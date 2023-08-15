from PySide6.QtWidgets import QComboBox
from FlowList import FlowList
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QLabel, QWidget
from PySide6.QtGui import QColor
from PySide6 import QtCore
from PySide6 import QtWidgets
from PySide6 import QtGui
from SvgFile import SvgFile
from ColorTree import ColorTreeWidget, ColorTreeItem, ColIndex
from FlowList import FlowList, IconModel
from enum import Enum
import glob
import sys

# Instead of writing the same string to both set and get settings names which is 
# error prone. Set it one place and just refer to it instead.
class SettingsVar(str, Enum):
    INPUT_FOLDER = 'InputFolder'
    OUTPUT_FOLDER = 'OutputFolder'
    PREVIEW_ICON_SIZE = 'PreviewIconSize'
    INPUT_BACKGROUND_COLOR = 'InputBackgroundColor'
    OUTPUT_BACKGROUND_COLOR = 'OutputBackgroundColor'
    SHOW_CONTRAST = 'ShowContrast'
    COLOR_SWAPS = 'ColorSwaps'
    CUSTOM_INPUT_COLORS = 'CustomInputColors'
    CUSTOM_OUTPUT_COLORS = 'CustomOutputColors'
    WINDOW_GEOMETRY = 'WindowGeometry'
    TREE_DOCK_POSITION = 'TreeDockPosition'
    STYLE_AS_DISABLED = 'StyleAsDisabled'


ORGANIZATION = 'SVG Color Swapper'
APPNAME = 'SVG Color Swapper'
SETTINGS = QtCore.QSettings(ORGANIZATION, APPNAME)
"""
    A custom ComboBox widget for selecting colors.

    This widget is designed to display a list of default colors, and  custom colors
    retrieved from SETTINGS. 

    Args:
        colorsSetting (SettingsVar): The setting key to retrieve custom colors.
        colorSetting (SettingsVar): The setting key to set the current selected color.

    Attributes:
        DefaultColors (list): A list of standard colors that cannot be added or removed.
    """
class ColorComboBox(QComboBox):
    # Standard colors that cannot be added or removed.
    DefaultColors = ['#000000', '#FFFFFF']

    # colorsSetting is used to retrieve custom colors
    # colorSetting is used to set the currentText
    def __init__(self, colorsSetting: SettingsVar, colorSetting: SettingsVar):
        super().__init__()
        self.colorsSetting = colorsSetting
        self.colorSetting = colorSetting
        self.rePopulate()

    """ 
    Populates (or repopulates) the combobox adding DefaultColors and any custom 
    colors the user might have added. Also retrieves the last select option and
    sets it once more.
    """
    def rePopulate(self):
        self.clear()

        colors = ColorComboBox.DefaultColors + SETTINGS.value(self.colorsSetting, [], list)
        default = '#FFFFFF'
        if self.colorsSetting == SettingsVar.OUTPUT_BACKGROUND_COLOR:
            default = '#000000'
        selectedColor = SETTINGS.value(self.colorSetting, default, str)
        
        for color in colors:
            qColor = QColor(color)
            pixmap = QPixmap(16, 16)
            pixmap.fill(qColor)
            self.addItem(pixmap, color)

            if color == selectedColor:
                self.setCurrentText(color)

class MainWindow(QMainWindow):

    listSvgFiles = []

    def __init__(self, appName: str):
        super().__init__()
        self.inputListSvgFiles = []
        self.outputListSvgFiles = []

        self.setWindowTitle('SVG Color Swapper')
        self.addBottomGui()         # Must be done BEFORE addCenterGui
        self.addCenterGui()
        self.addDockedColorWidget() # Must be done AFTER addCenterGui
        self.resize(1280, 800)
        self.setMouseTracking(True)

        if SETTINGS.contains(SettingsVar.INPUT_FOLDER):
            self.populateListSvgFiles()

        # Populate tree with any previously done colorswaps
        colorSwaps = SETTINGS.value(SettingsVar.COLOR_SWAPS, {})
        for colorToLookFor, colorToSet in colorSwaps.items():
            for i in range(self.tree.topLevelItemCount()):
                colorTreeItem: ColorTreeItem = self.tree.topLevelItem(i)
                if colorTreeItem.text(ColIndex.OLDHEX.value) == colorToLookFor:
                    colorTreeItem.setText(ColIndex.NEWHEX.value, colorToSet)
                    colorTreeItem.updateNewColumns()
            
        # All of the UI is set up. Start hooking up events.
        self.inputBackgroundColorComboBox.currentIndexChanged.connect(self.onChangeInputBackground)
        self.outputBackgroundColorComboBox.currentIndexChanged.connect(self.onChangeOutputBackground)
        self.inputBackgroundColorComboBox.setCurrentText(SETTINGS.value(SettingsVar.INPUT_BACKGROUND_COLOR, '#000000', str))  # Triggers currentIndexChanged
        self.inputBackgroundColorComboBox.currentIndexChanged.emit(self.inputBackgroundColorComboBox.currentIndex())
        self.outputBackgroundColorComboBox.setCurrentText(SETTINGS.value(SettingsVar.OUTPUT_BACKGROUND_COLOR, '#FFFFFF', str))
        self.outputBackgroundColorComboBox.currentIndexChanged.emit(self.outputBackgroundColorComboBox.currentIndex())

        self.buttonAddInputColor.pressed.connect(lambda: self.onPressedAddBackgroundColor(
            SettingsVar.CUSTOM_INPUT_COLORS, SettingsVar.INPUT_BACKGROUND_COLOR))
        self.buttonDeleteInputColor.pressed.connect(lambda: self.onPressedDeleteBackgroundColor(
            SettingsVar.CUSTOM_INPUT_COLORS, SettingsVar.INPUT_BACKGROUND_COLOR))
        self.buttonAddOutputColor.pressed.connect(lambda: self.onPressedAddBackgroundColor(
            SettingsVar.CUSTOM_OUTPUT_COLORS, SettingsVar.OUTPUT_BACKGROUND_COLOR))
        self.buttonDeleteOutputColor.pressed.connect(lambda: self.onPressedDeleteBackgroundColor(
            SettingsVar.CUSTOM_OUTPUT_COLORS, SettingsVar.OUTPUT_BACKGROUND_COLOR))

        self.checkboxDisabledStyling.setChecked(SETTINGS.value(SettingsVar.STYLE_AS_DISABLED, False, bool))

        self.comboBoxSizes.currentIndexChanged.connect(self.onChangeIconSIze)
        selectedSize = SETTINGS.value(SettingsVar.PREVIEW_ICON_SIZE, 64, int)
        self.comboBoxSizes.setCurrentText(str(selectedSize))

        
        # Restore the state of the dock widgets from SETTINGS
        self.restoreState(SETTINGS.value(SettingsVar.TREE_DOCK_POSITION, b''))
        # Restore the geometry of the window from SETTINGS
        self.restoreGeometry(SETTINGS.value(SettingsVar.WINDOW_GEOMETRY, b''))

        self.replaceOutputColorsWithTreeColors()

    def closeEvent(self, event):
        # Save the state of the dock widgets to SETTINGS
        SETTINGS.setValue(SettingsVar.TREE_DOCK_POSITION, self.saveState())

        # Save the geometry of the window to SETTINGS
        SETTINGS.setValue(SettingsVar.WINDOW_GEOMETRY, self.saveGeometry())
        super().closeEvent(event)

    def onPressedAddBackgroundColor(self, colors: SettingsVar, color: SettingsVar):
        QtWidgets.QColorDialog()

        colorDialog = QtWidgets.QColorDialog()
        result = colorDialog.exec()
        if result == QtWidgets.QDialog.Accepted:
            newColor = colorDialog.currentColor().name()
            customColors = SETTINGS.value(colors, [], list)
            customColors.append(newColor)
            SETTINGS.setValue(colors, customColors)
            SETTINGS.setValue(color, newColor)
            if colors == SettingsVar.CUSTOM_INPUT_COLORS:
                self.inputBackgroundColorComboBox.rePopulate()
                self.inputBackgroundColorComboBox.setCurrentText(newColor)
            else:
                self.outputBackgroundColorComboBox.rePopulate()
                self.outputBackgroundColorComboBox.setCurrentText(newColor)

    def onPressedDeleteBackgroundColor(self, colors: SettingsVar, color: SettingsVar):
        customColors: list = SETTINGS.value(colors, [], list)
        if(color == SettingsVar.INPUT_BACKGROUND_COLOR):
            customColors.remove(self.inputBackgroundColorComboBox.currentText())
            SETTINGS.setValue(colors, customColors)
            self.inputBackgroundColorComboBox.rePopulate()
        else:
            customColors.remove(self.outputBackgroundColorComboBox.currentText())
            SETTINGS.setValue(colors, customColors)
            self.outputBackgroundColorComboBox.rePopulate()


    def addBottomGui(self):
        widgetBottom = QWidget()
        layoutBottom = QtWidgets.QHBoxLayout(widgetBottom)

        layoutBottom.addWidget(QLabel('Icon styling: '))

        self.checkboxDisabledStyling = QtWidgets.QCheckBox('as disabled')
        layoutBottom.addWidget(self.checkboxDisabledStyling)
        self.checkboxDisabledStyling.stateChanged.connect(self.onDisabledStyleChange)

        iconControlsWidget = QtWidgets.QWidget()
        iconControlsLayout = QtWidgets.QHBoxLayout(iconControlsWidget)
        sizes = [16, 32, 48, 64, 128]
        iconPreviewLabel = QtWidgets.QLabel('size: ')
        iconPreviewLabel.setToolTip('Controls the size used for the icon previews <br/> <em>Shortcut: alt+1 to alt+5</em>')
        iconControlsLayout.addWidget(iconPreviewLabel)

        self.comboBoxSizes = QtWidgets.QComboBox()

        for i, size in enumerate(sizes):
            self.comboBoxSizes.addItem(str(size))
            action = QtGui.QAction(self)
            action.setShortcut('Alt+{}'.format(i+1))
            action.triggered[bool].connect(
                lambda checked, index=i: self.comboBoxSizes.setCurrentIndex(index)
            )

            self.addAction(action)

        iconControlsLayout.addWidget(self.comboBoxSizes)
        layoutBottom.addWidget(iconControlsWidget)

        spacer = QtWidgets.QSpacerItem(20, 1)
        layoutBottom.addItem(spacer)

        widgetSave = QtWidgets.QWidget()
        layoutSave = QtWidgets.QHBoxLayout(widgetSave)
        self.labelMessageIcon = QLabel()
        self.labelMessageIcon.setPixmap(self.labelMessageIcon.style().standardPixmap(QtWidgets.QStyle.SP_MessageBoxWarning))
        layoutSave.addWidget(self.labelMessageIcon)
        self.labelMessage = QLabel()
        layoutSave.addWidget(self.labelMessage)
        layoutSave.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.buttonSave = QtWidgets.QPushButton("&Save 'new' icons")
        self.buttonSave.setIcon(self.buttonSave.style().standardIcon(
            QtWidgets.QStyle.SP_DialogSaveButton))
        self.buttonSave.setDisabled(True)
        self.buttonSave.clicked.connect(self.createAndSaveIcons)
        layoutSave.addWidget(self.buttonSave)
        layoutBottom.addWidget(widgetSave)

        self.statusBar().addPermanentWidget(widgetBottom)
        self.statusBar().setSizeGripEnabled(False)


    @QtCore.Slot(int)
    def onDisabledStyleChange(self, state: int):
        styleIt = self.checkboxDisabledStyling.checkState() == QtCore.Qt.CheckState.Checked
        SETTINGS.setValue(SettingsVar.STYLE_AS_DISABLED, styleIt)
        self.flowListInput.setDisabledStyling(styleIt)
        self.flowListOutput.setDisabledStyling(styleIt)

    def selectedSize(self) -> int:
        return int(self.comboBoxSizes.currentText())


    @QtCore.Slot(int)
    def onChangeIconSIze(self, index: int):
        size = self.selectedSize()
        self.flowListInput.setIconSize(size)
        self.flowListOutput.setIconSize(size)
        self.flowListInput.repaint()
        SETTINGS.setValue(SettingsVar.PREVIEW_ICON_SIZE, size)


    def createAndSaveIcons(self):
        model = self.flowListOutput.model()
        fileWrittenCount = 0
        for row in range(model.rowCount()):
            index = model.index(row, 0)
            svgFile: SvgFile = model.data(index, QtCore.Qt.DecorationRole)
            newFilePath = svgFile.filePath.replace(
                self.lineEditInputFolder.text(),
                self.lineEditOutputFolder.text()
            )
            
            # Create directories if they don't exist
            QtCore.QDir().mkpath(QtCore.QFileInfo(newFilePath).path())

            # Create the file
            file = QtCore.QFile(newFilePath)
            if file.open(QtCore.QIODevice.WriteOnly | QtCore.QIODevice.Text):
                if file.write(svgFile.getColorMappedContent().encode('utf-8')) != -1:
                    fileWrittenCount += 1
                file.close()

        if fileWrittenCount > 0:
            self.statusBar().showMessage(
                "✅ Created {} .svg's in {}".format(
                    fileWrittenCount,
                    self.lineEditOutputFolder.text()
                )
            )
        else:
            self.statusBar().showMessage('❌ No files were created')
    
    #Populates self.inputListSvgFiles and self.outputListSvgFiles with the content
    #from the input folder. Also ensures the lists showing these are repainted.
    def populateListSvgFiles(self):
        colors = []
        
        #Filter down to just .svg's
        dir = QtCore.QDir(SETTINGS.value(SettingsVar.INPUT_FOLDER))
        dir.setNameFilters(['*.svg'])

        #
        it = QtCore.QDirIterator(dir)
        while it.hasNext():
            it.next()
            inputSvgFile = SvgFile(it.filePath())
            self.inputListSvgFiles.append(inputSvgFile)
            colors += inputSvgFile.colors.keys()

            self.outputListSvgFiles.append(SvgFile(it.filePath()))

        self.evaluateSaveButtonState()

        self.tree.addColors(
            set(colors),
            self.inputBackgroundColorComboBox.currentText(),
            self.outputBackgroundColorComboBox.currentText()
        )
        self.flowListInput.repaint()
        self.flowListOutput.repaint()

    # Evaluates if everything is in order to save files
    # Everything checks out? Enable saveButton
    # Something isn't right? Disable saveButton
    # 
    # self.labelMessage is used to indicate to the user what isn't right so they
    # can take steps to rectify that.
    def evaluateSaveButtonState(self):
        message = self.labelMessage
        icon = self.labelMessageIcon
        evaluationPassed = True

        # No input = No output. Disable
        if not SETTINGS.contains(SettingsVar.INPUT_FOLDER):
            message.setText('Set an input folder to proceed')
            icon.setPixmap(icon.style().standardPixmap(QtWidgets.QStyle.SP_MessageBoxInformation))
            evaluationPassed = False
        # No icons in the inputfolder? Disable 
        if len(self.inputListSvgFiles) < 1:
            message.setText('Input folder doesn\'t contain any SVGs')
            icon.setPixmap(icon.style().standardPixmap(QtWidgets.QStyle.SP_MessageBoxWarning))
            evaluationPassed = False
        # No place to save things to? Disable
        if not SETTINGS.contains(SettingsVar.OUTPUT_FOLDER):
            message.setText('Set an output folder to proceed')
            icon.setPixmap(icon.style().standardPixmap(QtWidgets.QStyle.SP_MessageBoxInformation))
            evaluationPassed = False
        
        # No write permissions on output folder? Disable
        fileInfo = QtCore.QFileInfo(SETTINGS.value(SettingsVar.OUTPUT_FOLDER))
        if not fileInfo.isWritable():
            message.setText('No write permissions on the output folder')
            icon.setPixmap(icon.style().standardPixmap(QtWidgets.QStyle.SP_MessageBoxCritical))
            evaluationPassed = False

        # Everything checks out.
        icon.setPixmap(icon.style().standardPixmap(QtWidgets.QStyle.SP_MessageBoxWarning))
        message.setText('This will overwrite any already existing files')
        self.buttonSave.setEnabled(evaluationPassed)

    def syncScrollBars(self, value):
        # If one is scrolled, programmatically scroll the other.
        if self.sender() == self.flowListInput.verticalScrollBar():
            self.flowListOutput.verticalScrollBar().setValue(value)
        else:
            self.flowListInput.verticalScrollBar().setValue(value)

    @QtCore.Slot(QtCore.QItemSelection, QtCore.QItemSelection)
    def syncSelections(self, selected, deselected):
        sender = self.sender()
        otherView = self.flowListInput if sender == self.flowListOutput.selectionModel() else self.flowListOutput
        # Update the selection of the other view
        otherView.selectionModel().select(selected, QtCore.QItemSelectionModel.Select)
        otherView.selectionModel().select(deselected, QtCore.QItemSelectionModel.Deselect)

    # Run addBottomGui before this. The bottom GUI contains the size selection
    # which is used for the icon sizes here
    def addCenterGui(self):
        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)
        self.setCentralWidget(scrollArea)

        mainCenterWidget = QtWidgets.QWidget()
        mainCenterLayout = QtWidgets.QHBoxLayout(mainCenterWidget)
        mainCenterLayout.setSpacing(0)
        mainCenterLayout.setContentsMargins(0, 0, 0, 0)

        # Create input panel
        inputPanel, self.flowListInput, self.lineEditInputFolder, self.inputBackgroundColorComboBox, \
        self.buttonAddInputColor, self.buttonDeleteInputColor = \
        self.createPanel(
            'Input',
            self.inputListSvgFiles,
            SettingsVar.INPUT_FOLDER,
            '/path/to/svg/filled/folder',
            self.onClickSetInputFolder,
            SettingsVar.CUSTOM_INPUT_COLORS,
            SettingsVar.INPUT_BACKGROUND_COLOR
        )

        # Create output panel
        outputPanel, self.flowListOutput, self.lineEditOutputFolder, self.outputBackgroundColorComboBox, \
        self.buttonAddOutputColor, self.buttonDeleteOutputColor = \
        self.createPanel(
            'Output',
            self.outputListSvgFiles,
            SettingsVar.OUTPUT_FOLDER,
            '/path/for/new/icons',
            self.onClickSetOutputFolder,
            SettingsVar.CUSTOM_OUTPUT_COLORS,
            SettingsVar.OUTPUT_BACKGROUND_COLOR
        )

        # Add panels to main layout
        mainCenterLayout.addWidget(inputPanel)
        mainCenterLayout.addWidget(outputPanel)

        scrollArea.setWidget(mainCenterWidget)

    def createPanel(self, label, svgFiles, settingsVar, defaultPath, setFolderFunc, colors: SettingsVar, color: SettingsVar):
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout(panel)

        listView = FlowList(self.selectedSize())
        model = IconModel(svgFiles)
        listView.setModel(model)

        # Make the scrollbars scroll at the same time.
        listView.verticalScrollBar().valueChanged.connect(self.syncScrollBars)
        # Select in one, select in the other
        listView.selectionModel().selectionChanged.connect(self.syncSelections)

        lbl = QLabel(label)
        lbl.setStyleSheet('font-size: 28px;')
        layout.addWidget(lbl, 0, 0, 1, 3)
        layout.addWidget(QtWidgets.QLabel('Folder'), 1, 0, 1, 2)
        folder = str(SETTINGS.value(settingsVar, defaultPath, str))
        lineEditFolder = QtWidgets.QLineEdit(folder)
        lineEditFolder.setReadOnly(True)
        layout.addWidget(lineEditFolder, 1, 1, 1, 2)
        dirButton = QtWidgets.QPushButton()
        dirButton.clicked.connect(setFolderFunc)
        dirButton.setIcon(dirButton.style().standardIcon(QtWidgets.QStyle.SP_DialogOpenButton))
        layout.addWidget(dirButton, 1, 3, 1, 1)
        layout.addWidget(QLabel('Background'), 2, 0, 1, 1)
        backgroundColorComboBox = ColorComboBox(colors, color)
        layout.addWidget(backgroundColorComboBox, 2, 1, 1, 1)
        buttonAddColor = QtWidgets.QPushButton()
        buttonAddColor.setToolTip('Add new color')
        buttonAddColor.setIcon(QtGui.QIcon('Add.svg'))
        layout.addWidget(buttonAddColor, 2, 2, 1, 1)
        buttonDeleteColor = QtWidgets.QPushButton()
        buttonDeleteColor.setToolTip('Delete selected color')
        buttonDeleteColor.setIcon(QtGui.QIcon('Delete.svg'))
        layout.addWidget(buttonDeleteColor, 2, 3, 1, 1)

        layout.addWidget(listView, 3, 0, 1, 4)
        layout.setColumnStretch(1, 1)

        return panel, listView, lineEditFolder, backgroundColorComboBox, buttonAddColor, buttonDeleteColor

    def onClickSetInputFolder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select input folder', SETTINGS.value(SettingsVar.INPUT_FOLDER, QtCore.QDir.homePath()))
        if folder != '':
            if folder == SETTINGS.value(SettingsVar.OUTPUT_FOLDER):
                self.triggerInputEqualsOutputErrorDialog()
                self.onClickSetInputFolder()
            else:
                SETTINGS.setValue(SettingsVar.INPUT_FOLDER, folder)
                self.lineEditInputFolder.setText(folder)
                self.evaluateSaveButtonState()

    def onClickSetOutputFolder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select outpput folder', SETTINGS.value(SettingsVar.OUTPUT_FOLDER, QtCore.QDir.homePath()))
        if folder != '':
            if folder == SETTINGS.value(SettingsVar.INPUT_FOLDER):
                self.triggerInputEqualsOutputErrorDialog()
                self.onClickSetOutputFolder()
            else:
                SETTINGS.setValue(SettingsVar.OUTPUT_FOLDER, folder)
                self.lineEditOutputFolder.setText(folder)
                self.evaluateSaveButtonState()

    def triggerInputEqualsOutputErrorDialog(self):
        QtWidgets.QMessageBox.critical(self, 'Input = Output', 'The output folder has to differ from the input folder')

    def getSvgFilePaths(self) -> list:
        folder = SETTINGS.value(SettingsVar.INPUT_FOLDER) + '/'
        return glob.glob(folder + '*.svg')

    def addDockedColorWidget(self):
        self.treeDockWidget = QtWidgets.QDockWidget('Colors', self)
        self.treeDockWidget.setObjectName('ColorDock')
        self.treeDockWidget.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable | 
            QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.treeDockWidget.setMouseTracking(True)

        treeAndControlsWidget = QtWidgets.QWidget()
        layoutTreeAndControls = QtWidgets.QVBoxLayout(treeAndControlsWidget)

        checkUnfoldAll = QtWidgets.QCheckBox('Show contrast')
        checkUnfoldAll.setToolTip('''
            <html>The web accessibility iniative recommends a contrast ratio of 4.5:1 for text and 3 for large text. 
            <br/>This application sticks to the same guideline for images/background color. 
            <br/><br/>https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html
        ''')
        checkUnfoldAll.setCheckable(True)
        checkUnfoldAll.toggled.connect(self.onToggleShowContrast)
        layoutTreeAndControls.addWidget(checkUnfoldAll)

        showContrast = SETTINGS.value(SettingsVar.SHOW_CONTRAST, False, bool)
        self.tree = ColorTreeWidget(self.treeDockWidget, showContrast)
        self.tree.currentItemChanged.connect(self.onItemChangeColorTreeSelectMatchingIcons)
        self.tree.itemPressed.connect(self.onPressedTreeColor)
        layoutTreeAndControls.addWidget(self.tree)
        self.treeDockWidget.setWidget(treeAndControlsWidget)
        
        showContrast = SETTINGS.value(SettingsVar.SHOW_CONTRAST, False, bool)
        checkUnfoldAll.setChecked(showContrast)
        self.onToggleShowContrast(showContrast)

        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.treeDockWidget)
        self.treeDockWidget.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        self.treeDockWidget.setAllowedAreas(QtCore.Qt.DockWidgetArea.RightDockWidgetArea | QtCore.Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setCorner(QtCore.Qt.Corner.BottomRightCorner, QtCore.Qt.DockWidgetArea.RightDockWidgetArea)

    def onChangeInputBackground(self):
        hex = self.inputBackgroundColorComboBox.currentText()
        SETTINGS.setValue(SettingsVar.INPUT_BACKGROUND_COLOR, hex)
        self.buttonDeleteInputColor.setEnabled(hex not in ColorComboBox.DefaultColors)
        self.tree.setInputHalfBackground(hex)
        self.flowListInput.setStyleSheet(f'background-color: {hex};')
        self.flowListInput.setFontColorToContrastWith(QColor(hex))

    def onChangeOutputBackground(self):
        hex = self.outputBackgroundColorComboBox.currentText()
        SETTINGS.setValue(SettingsVar.OUTPUT_BACKGROUND_COLOR,hex)
        self.buttonDeleteOutputColor.setEnabled(hex not in ColorComboBox.DefaultColors)
        self.tree.setOutputHalfBackground(hex)
        self.flowListOutput.setStyleSheet(f'background-color: {hex};')
        self.flowListOutput.setFontColorToContrastWith(QColor(hex))

    @QtCore.Slot(bool)
    def onToggleShowContrast(self, checked):
        SETTINGS.setValue(SettingsVar.SHOW_CONTRAST, checked)
        self.tree.showContrastColumns(checked)
        treeWidth = 240
        if checked:
            treeWidth = 350
        self.treeDockWidget.setMinimumWidth(treeWidth)
        self.treeDockWidget.setMaximumWidth(treeWidth)

    @QtCore.Slot(QtWidgets.QTreeWidgetItem, QtWidgets.QTreeWidgetItem)
    def onItemChangeColorTreeSelectMatchingIcons(self, itCur: QtWidgets.QTreeWidgetItem, itPrev: QtWidgets.QTreeWidgetItem):
        hexToSearchFor = itCur.text(ColIndex.OLDHEX.value)

        model = self.flowListInput.model()
        self.flowListInput.selectionModel().clear()
        for row in range(model.rowCount()):
            index = model.index(row, 0)
            svgFile: SvgFile = model.data(index, QtCore.Qt.DecorationRole)
            if hexToSearchFor in svgFile.colors:
                self.flowListInput.selectionModel().select(index, QtCore.QItemSelectionModel.Select)
    
    @QtCore.Slot(QtWidgets.QTreeWidgetItem, int)
    def onPressedTreeColor(self, it: ColorTreeItem, col):
        if (col in ColIndex.NewColumns()) and it.parent() == None:
            # Save the initial 
            startColorHex = it.text(ColIndex.OLDHEX.value)
            startColor = it.background(ColIndex.OLDCOLOR.value).color()
            restoreOldNew = False

            # Set the initial to the new color if there's one
            if it.text(ColIndex.NEWHEX.value) != 'Change':
                startColorHex = it.text(ColIndex.NEWHEX.value)
                startColor = it.background(ColIndex.NEWCOLOR.value).color()
                restoreOldNew = True
            
            colorDialog = QtWidgets.QColorDialog(startColor)
            colorDialog.currentonChangeColorTreeColor.connect(self.onChangeColorTreeColor)

            result = colorDialog.exec()

            # If the user cancels out, restore previous situation
            if result != QtWidgets.QDialog.Accepted:
                if restoreOldNew:
                    it.setText(ColIndex.NEWHEX.value, startColorHex)
                else: #Restore from plain old - old
                    it.setText(ColIndex.NEWHEX.value, 'Change')
                it.updateNewColumns()
                self.replaceOutputColorsWithTreeColors()
            else:
                # Save to settings
                colorSwaps = SETTINGS.value(SettingsVar.COLOR_SWAPS, {})
                colorSwaps[it.text(ColIndex.OLDHEX.value)] = it.text(ColIndex.NEWHEX.value)
                SETTINGS.setValue(SettingsVar.COLOR_SWAPS, colorSwaps)

    # Takes the old/new colors from the ColorTree and applies them to the output preview
    def replaceOutputColorsWithTreeColors(self):
        # Create the color mapping based on the color tree
        colorMapping = {}
        for i in range(0, self.tree.topLevelItemCount()):
            colorTreeItem: ColorTreeItem = self.tree.topLevelItem(i)
            colorMapping |= colorTreeItem.getColorMapping()

        # Apply the color mapping on the preview SvgFiles/list
        outputModel = self.flowListOutput.model()
        for i in range(outputModel.rowCount()):
            index = outputModel.index(i, 0)
            svgFile: SvgFile = outputModel.data(index, QtCore.Qt.DecorationRole)
            svgFile.setColorMap(colorMapping)
            outputModel.setData(index, svgFile, QtCore.Qt.DecorationRole)

    @QtCore.Slot(QColor)
    def onChangeColorTreeColor(self, color: QColor):
        self.tree.currentItem().setText(ColIndex.NEWHEX.value, color.name())
        self.tree.currentItem().updateNewColumns()

        self.replaceOutputColorsWithTreeColors()
        self.tree.fakeUpdate()

app = QApplication(sys.argv)
app.setWindowIcon(QtGui.QIcon('AppIcon.svg'))
window = MainWindow(APPNAME)
window.show()

app.exec()