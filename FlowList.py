from PySide6.QtWidgets import QListView, QStyledItemDelegate, QStyle, QAbstractItemView, QListWidgetItem
from PySide6.QtCore import Qt, QRect, QSize, QAbstractListModel, QModelIndex
from PySide6.QtGui import QColor, QDesktopServices, QIcon
from SvgFile import SvgFile
from ColorCalc import ColorCalc
import os


"""
    A custom widget for displaying a list that sorts out its own grid,
    items will be added to a row until it runs out of space at which point the
    next item will be placed on the next row.

    The look is supposed to mimic what you would find in a typical file explorer
    providing a preview of the icon and the name of the file.
"""
class FlowList(QListView):

    """
    A custom QStyledItemDelegate that's to be used exclusively with the FlowList
    class. 

    It uses a custom sizeHint() to allow the icons to be drawn in a consistent 
    manner. It adds two methods to define how the icons are rendered.
    """
    class IconTextDelegate(QStyledItemDelegate):
        def __init__(self, size: int, contrastingColor: QColor = None):
            super().__init__()
            self.contrastingColor = contrastingColor
            self.styleAsDisabled = False
            self.size = size

        def paint(self, painter, option, index):
            # Handle selection
            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())

            # Draw the pixmap
            svgFile: SvgFile = index.data(Qt.DecorationRole)
            pixmap = svgFile.getPixmapScaledTo(self.size)
            if self.styleAsDisabled:
                icon = QIcon(pixmap)
                pixmap = icon.pixmap(pixmap.size(), QIcon.Disabled, QIcon.On)

            # Calculate the space needed for the text
            text = index.data(Qt.DisplayRole)
            fontMetrics = painter.fontMetrics()
            textHeight = fontMetrics.height()

            # Set the height of pixmapRect
            pixmapRect = QRect(option.rect)
            pixmapRect.setHeight(option.rect.height() - textHeight)

            x = pixmapRect.left() + (pixmapRect.width() - pixmap.width()) / 2
            y = pixmapRect.top() + (pixmapRect.height() - pixmap.height()) / 2
            painter.drawPixmap(x, y, pixmap)

            # Draw the text
            if self.contrastingColor != None:
                painter.setPen(self.contrastingColor)
            text = index.data(Qt.DisplayRole)
            fontMetrics = painter.fontMetrics()
            textHeight = fontMetrics.height()
            textRect = QRect(option.rect)
            textRect.setTop(textRect.bottom() - textHeight - 8)
            painter.drawText(textRect, Qt.AlignCenter, text)

        def sizeHint(self, option, index) -> QSize:
            return QSize(160, 160)
        
        """
            Args:
                styleAsDisabled (bool) True if the disabled styling should be used
        """
        def setDisabledStyling(self, styleAsDisabled: bool):
            self.styleAsDisabled = styleAsDisabled

        """
            Args:
                size (int) the size the icon will be rendered at.
                It should be smaller than the sizeHint and leave enough room for
                text to be added.
        """
        def setSize(self, size: int):
            self.size = size

    """
    QListView is a very flexible class so this init mostly just sets options 
    available in its parent class.

    In addition it sets the item delegate to IconTextDelegate.
    """
    def __init__(self, size):
        super().__init__()
        self.contrastingColor = None
        self.size = size
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setGridSize(QSize(160, 160))
        self.setSpacing(240 - size)
        self.setFlow(QListView.Flow.LeftToRight)
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setUniformItemSizes(False)
        self.setItemDelegate(FlowList.IconTextDelegate(self.size, self.contrastingColor))
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.doubleClicked.connect(self.openFile)

    def setDisabledStyling(self, styleAsDisabled: bool):
        iconTextDelegate: iconTextDelegate = self.itemDelegate()
        iconTextDelegate.setDisabledStyling(styleAsDisabled)
        self.repaint()

    def setIconSize(self, size: int) -> None:
        iconTextDelegate : iconTextDelegate = self.itemDelegate()
        iconTextDelegate.setSize(size)
        self.repaint()

    def clear(self):
        for action in self.actions():
            self.removeAction(action)

    def openFile(self, listItem: QListWidgetItem):
        print(QDesktopServices.openUrl(listItem.data(3)))

    def setFontColorToContrastWith(self, color: QColor):
        self.contrastingColor = ColorCalc.GoodContrastColorForBackground(color)
        self.setItemDelegate(FlowList.IconTextDelegate(self.size, self.contrastingColor))

class IconModel(QAbstractListModel):
    def __init__(self, icons, parent=None):
        super().__init__(parent)
        self.icons = icons

    def rowCount(self, parent=QModelIndex()):
        return len(self.icons)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        svgFile: SvgFile = self.icons[index.row()]
        if role == Qt.DisplayRole:
            return os.path.basename(svgFile.filePath)
        elif role == Qt.DecorationRole:
            return svgFile
        elif role == Qt.ToolTipRole:
            return svgFile.filePath