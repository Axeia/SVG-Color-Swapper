from PySide6.QtWidgets import QStyledItemDelegate, QStyle, QApplication
from PySide6.QtCore import QRect, Qt
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
from PySide6.QtGui import QBrush, QColor, QPainter, QFont
from PySide6.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem, QItemDelegate, QStyledItemDelegate, QHeaderView, QStyleOptionHeader, QStyle
from PySide6.QtCore import Qt, QRect
from ColorCalc import ColorCalc
from enum import Enum

class ColIndex(Enum):
    OLDCOLOR    = 0
    OLDHEX      = 1
    OLDCONTRAST = 2
    NEWCONTRAST = 3
    NEWHEX      = 4
    NEWCOLOR    = 5

    def NewColumns():
        return (
            ColIndex.NEWCONTRAST.value,
            ColIndex.NEWHEX.value, ColIndex.NEWCOLOR.value
        )

class ColorTreeWidget(QTreeWidget):
    COLORCOLUMNWIDTH = 40

    def __init__(self, parent, showContrast: bool):
        super().__init__(parent)
        self.showContrast = showContrast
        # Needed to propogate to the mouseMoveEvent (and leaveEvent?) overwrite
        self.setMouseTracking(True)
        #self.setAlternatingRowColors(True)
        self.showContrastColumns(showContrast)
        # self.setRootIsDecorated(False)
        self.setIndentation(0)

        self.setHeaderLabels(
            ('Old', 'Hex', '◩ Contrast', 'Contrast ◩', 'Hex', 'New', ))
        self.setItemDelegateForColumn(ColIndex.NEWCONTRAST.value, IconOnTheRightDelegate(self))
        self.showContrastColumns(showContrast)

        fixedCols = [ColIndex.OLDCOLOR, ColIndex.NEWCOLOR]
        for fixedCol in fixedCols:
            self.header().setSectionResizeMode(fixedCol.value, QHeaderView.Fixed)

        stretchCols = [ColIndex.OLDHEX, ColIndex.OLDCONTRAST,
                       ColIndex.NEWCONTRAST, ColIndex.NEWHEX]
        for stretchCol in stretchCols:
            self.header().setSectionResizeMode(stretchCol.value, QHeaderView.Stretch)

        self.header().setStretchLastSection(False)
        self.header().setSectionsMovable(False)

        self.setColumnWidth(ColIndex.OLDCOLOR.value, self.COLORCOLUMNWIDTH)
        self.setColumnWidth(ColIndex.NEWCOLOR.value, self.COLORCOLUMNWIDTH)

        self.setInputHalfBackground('#000000')
        self.setOutputHalfBackground('#FFFFFF')

    def addColors(self, colors: set, oldBackground: str, newBackground: str):
        colorsSet = set(colors)

        oldBackground = QColor(oldBackground)
        newBackground = QColor(oldBackground)
        for color in colorsSet:
            treeItem = ColorTreeItem(self, color, oldBackground, newBackground)

    def showContrastColumns(self, show: bool):
        contrastColumns = [
            ColIndex.OLDCONTRAST.value, ColIndex.NEWCONTRAST.value,
        ]
        for contrastColumn in contrastColumns:
            if show:
                self.showColumn(contrastColumn)
            else:
                self.hideColumn(contrastColumn)

    def mouseMoveEvent(self, event):
        index = self.indexAt(event.pos())

        if not index.parent().isValid() \
                and index.column() in ColIndex.NewColumns():
            QApplication.setOverrideCursor(Qt.PointingHandCursor)
        elif event.pos().y() < self.header().height() \
                or event.pos().y() > self.visualItemRect(self.topLevelItem(self.topLevelItemCount() - 1)).bottom():
            self.actuallyRestoreCursor()
        elif index.isValid():
            self.actuallyRestoreCursor()

        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.actuallyRestoreCursor()
        super().leaveEvent(event)

    def actuallyRestoreCursor(self):
        while QApplication.overrideCursor() is not None:
            QApplication.restoreOverrideCursor()

    def setInputHalfBackground(self, hex: str):
        self.leftHalfBgColor = QColor(hex)
        contrastingColor = ColorCalc.GoodContrastColorForBackground(self.leftHalfBgColor)
        for i in range(0, self.topLevelItemCount()):
            colorTreeItem: ColorTreeItem = self.topLevelItem(i)
            colorTreeItem.setOldBackground(self.leftHalfBgColor)
            colorTreeItem.setForeground(ColIndex.OLDHEX.value, contrastingColor)
            colorTreeItem.setForeground(ColIndex.OLDCONTRAST.value, contrastingColor)
            
        self.fakeUpdate()

    def setOutputHalfBackground(self, hex: str):
        self.rightHalfBgColor = QColor(hex)
        contrastingColor = ColorCalc.GoodContrastColorForBackground(self.rightHalfBgColor)
        for i in range(0, self.topLevelItemCount()):
            colorTreeItem: ColorTreeItem = self.topLevelItem(i)
            colorTreeItem.setNewBackground(self.rightHalfBgColor)
            colorTreeItem.setForeground(ColIndex.NEWCONTRAST.value, contrastingColor)
            colorTreeItem.setForeground(ColIndex.NEWHEX.value, contrastingColor)

        self.fakeUpdate()

    # FIXME
    # For some reason .repaint() isn't enough to trigger a proper repaint.
    # For some other reason .update() requires a parameter and I'm not sure what
    # Adding and removing an item triggers an update
    def fakeUpdate(self):
        self.addTopLevelItem(QTreeWidgetItem())
        self.takeTopLevelItem(self.topLevelItemCount() - 1)

    def paintEvent(self, event):
      painter = QPainter(self.viewport())
      rect = event.rect()
      leftRect = QRect(rect.left(), rect.top(),
                       rect.width() / 2, rect.height())
      rightRect = QRect(rect.width() / 2, rect.top(),
                        rect.width() / 2, rect.height())
      painter.fillRect(leftRect, self.leftHalfBgColor)
      painter.fillRect(rightRect, self.rightHalfBgColor)
      super().paintEvent(event)



class ColorTreeItem(QTreeWidgetItem):
    def __init__(self, parent, hex: str, oldBackground: QColor, newBackground: QColor):
        super().__init__(parent)
        hexFont =  QFont('DejaVu Mono, Consolas, Courier, monospace')
        oldColor = QColor(hex)
        newColor = QColor(hex)

        self.oldBackground = oldBackground
        self.newBackground = newBackground

        oldContrast = ColorCalc.ContrastRatio(oldBackground, oldColor)
        newContrast = ColorCalc.ContrastRatio(newBackground, newColor)

        oldRatio = ColorCalc.ContrastRatioToString(oldContrast)
        newRatio = ColorCalc.ContrastRatioToString(newContrast)

        oldRatingIcon = ColorCalc.ContrastRatioToIcon(oldContrast)
        newRatingIcon = ColorCalc.ContrastRatioToIcon(newContrast)

        self.setBackground(ColIndex.OLDCOLOR.value, oldColor)
        self.setText(ColIndex.OLDHEX.value, hex)
        self.setFont(ColIndex.OLDHEX.value, hexFont)
        self.setIcon(ColIndex.OLDCONTRAST.value, oldRatingIcon)
        self.setText(ColIndex.OLDCONTRAST.value, oldRatio)
        
        self.setText(ColIndex.NEWCONTRAST.value, newRatio)
        self.setIcon(ColIndex.NEWCONTRAST.value, newRatingIcon)
        self.setText(ColIndex.NEWHEX.value, 'Change')
        self.setFont(ColIndex.NEWHEX.value, hexFont)
        self.setBackground(ColIndex.NEWCOLOR.value, QBrush(QColor(hex)))

        #self.setForeground(ColIndex.OLDHEX.value, QBrush(QColor("#FFFFFF")))
        #self.setForeground(ColIndex.OLDCONTRAST.value, QBrush(QColor("#FFFFFF")))

        
        #self.setForeground(ColIndex.NEWHEX.value, QBrush(QColor("#000000")))
        #self.setForeground(ColIndex.NEWCONTRAST.value, QBrush(QColor("#000000")))

    def setOldBackground(self, oldBackground: QColor):
        self.oldBackground = oldBackground
        self.updateOldColumns()


    def setNewBackground(self, newBackground: QColor):
        self.newBackground = newBackground
        self.updateNewColumns()

    # Call after setting new hex text or self.newBackground 
    # Will update new contrast, contrast rating and background color
    def updateNewColumns(self):
        newColor = self.background(ColIndex.OLDCOLOR.value).color()

        if self.text(ColIndex.NEWHEX.value) != 'Change':
            newColor = QColor(self.text(ColIndex.NEWHEX.value))

        newRatio = ColorCalc.ContrastRatio(newColor, self.newBackground)

        newIcon = ColorCalc.ContrastRatioToIcon(newRatio)
        self.setIcon(ColIndex.NEWCONTRAST.value, newIcon)
        
        newContrast = ColorCalc.ContrastRatioToString(newRatio)
        self.setText(ColIndex.NEWCONTRAST.value, newContrast)

        self.setBackground(ColIndex.NEWCOLOR.value, newColor)

    def updateOldColumns(self):
        oldColor = QColor(self.text(ColIndex.OLDHEX.value))
        oldRatio = ColorCalc.ContrastRatio(oldColor, self.oldBackground)

        oldIcon = ColorCalc.ContrastRatioToIcon(oldRatio)
        self.setIcon(ColIndex.NEWCONTRAST.value, oldIcon)
        
        oldContrast = ColorCalc.ContrastRatioToString(oldRatio)
        self.setText(ColIndex.NEWCONTRAST.value, oldContrast)

        self.setBackground(ColIndex.NEWCOLOR.value, oldColor)

    def getColorMapping(self) -> {}:
        newColor = self.data(ColIndex.NEWHEX.value, Qt.DisplayRole)
        if newColor == 'Change':
            return {}
        else:
            return {self.data(ColIndex.OLDHEX.value, Qt.DisplayRole): newColor}


class IconOnTheRightDelegate(QStyledItemDelegate):
    def initStyleOption(self, option: QStyleOptionViewItem, index):
        super().initStyleOption(option, index)
        option.decorationPosition = QStyleOptionViewItem.Right
        option.displayAlignment = Qt.AlignRight
