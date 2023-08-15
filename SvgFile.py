from PySide6.QtCore import QFile, QRegularExpression, QRegularExpressionMatch, QSize, QByteArray
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import QFile, Qt
from PySide6.QtSvg import QSvgRenderer

import re

class SvgFile:
    def __init__(self, filePath: str):
        self.colors = {}
        self.content = ''
        self.filePath = filePath
        self.colorMap = {}

        file = QFile(filePath)
        if file.open(QFile.ReadOnly | QFile.Text):
            self.content = str(file.readAll(), encoding='utf-8')

            regEx = QRegularExpression('(#[[:xdigit:]]{3,6})(?:;|\s)')
            matches = regEx.globalMatch(self.content)
            while matches.hasNext():
                match: QRegularExpressionMatch = matches.next()

                colorHex = match.captured(1).capitalize()
                if colorHex in self.colors:
                    self.colors[colorHex] += 1
                else:
                    self.colors[colorHex] = 1

    def setColorMap(self, colorMap: {}):
        self.colorMap = colorMap

    def getPixmapScaledTo(self, size: int) -> QPixmap:
        svgRenderer = QSvgRenderer(QByteArray(self.getColorMappedContent()))

        pixmap = QPixmap(QSize(size, size))
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        svgRenderer.render(painter)
        painter.end()

        return pixmap
    
    def getColorMappedContent(self) -> str:
        svgAsString = self.content

        if self.colorMap:
            # create a regular expression pattern that matches all the substrings
            pattern = '|'.join(map(re.escape, self.colorMap.keys()))
            # define a callback function to perform the replacement

            def replace(match):
                return self.colorMap[match.group(0)]
            # use the sub method to perform the replacement
            svgAsString = re.sub(pattern, replace, self.content)

        return svgAsString

