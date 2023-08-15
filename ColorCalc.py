from PyQt5.QtCore import QSize, Qt, QRect
from PySide6.QtGui import QColor
from PySide6.QtGui import QPixmap, QPainter, QFont, QIcon
from PySide6.QtCore import QSize, QRect, Qt
from typing import Union

"""
A big thanks to w3.org for sharing the formula for calculating contrast
https://www.w3.org/TR/WCAG20-TECHS/G17.html

This class calculates the contrast ratio between 2 colors as well assigning a 
rating based on the WAI guidelines. 
"""
class ColorCalc:
    GOODRATIOTHRESHOLD = 4.5
    OKRATIOTHRESHOLD = 3
    COLOROPTIONS = (QColor('#FFFFFF'), QColor('#000000'))

    @staticmethod
    def RelativeLuminance(color: QColor) -> float:
        rgb = [color.redF(), color.greenF(), color.blueF()]
        for i in range(3):
            if rgb[i] <= 0.03928:
                rgb[i] /= 12.92
            else:
                rgb[i] = ((rgb[i] + 0.055) / 1.055) ** 2.4
        return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]

    @staticmethod
    def ContrastRatio(background: QColor, foreground: QColor) -> float:
        l1 = ColorCalc.RelativeLuminance(background)
        l2 = ColorCalc.RelativeLuminance(foreground)
        if l1 < l2:
            l1, l2 = l2, l1
        return (l1 + 0.05) / (l2 + 0.05)

    @staticmethod
    def ContrastRatioString(background: QColor, foreground: QColor):
        return ColorCalc.ContrastRatioToString(
            round(ColorCalc.ContrastRatio(background, foreground))
        )

    @staticmethod
    def ContrastRatioToString(contrastRatio: float) -> str:
        return f'{round(contrastRatio, 1)}:1'
    
    """
    Given a contrast ratio calcualted by ContrastRatio it will rate good it is
    in the form of an icon.

    Note: The icons are based on unicode emojis and thus might differ significantly accross font-families.
    What you see below in your editors font might not represent what it will look like in the application.
    """
    @staticmethod
    def ContrastRatioToIcon(contrastRatio: float) -> QIcon:
        if contrastRatio >= ColorCalc.GOODRATIOTHRESHOLD:
            return ColorCalc.EmoticonToIcon('👍', QSize(48, 48), QColor(0, 255, 0, 128))
        elif contrastRatio >= ColorCalc.OKRATIOTHRESHOLD:
            return ColorCalc.EmoticonToIcon('👌', QSize(48, 48), QColor(155, 100, 50, 128))
        else:
            return ColorCalc.EmoticonToIcon('👎', QSize(48, 48), QColor(255, 0, 0, 128))

    """
    Converts the given character(s) to a QIcon.

    Args:
        emoticon (str): The text to convert to a QIcon.
        size (QSize, optional): The size of the icon to create. Defaults to QSize(48, 48).
        hue (QColor, optional): The icon can be 'tinted' to a certain hue by providing a color.

    Returns:
        QIcon: The created QIcon.
    """
    @staticmethod
    def EmoticonToIcon(emoticon: str, size: QSize = QSize(48, 48), hue: QColor = None) -> QIcon:
        # Create a pixmap to draw the emoticon
        pixmap = QPixmap(size * 2)
        pixmap.fill(Qt.transparent)  # Filling with transparent color
        painter = QPainter(pixmap)

        # Set font and draw the emoticon
        font = QFont()
        font.setPixelSize(min(size.width(), size.height()))
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, emoticon)
        painter.end()

        # Crop the pixmap to non-transparent pixels
        image = pixmap.toImage()
        left = image.width()
        right = 0
        top = image.height()
        bottom = 0

        for x in range(image.width()):
            for y in range(image.height()):
                if image.pixelColor(x, y).alpha() != 0:
                    left = min(left, x)
                    right = max(right, x)
                    top = min(top, y)
                    bottom = max(bottom, y)

        croppedPixmap = pixmap.copy(
            QRect(left, top, right - left + 1, bottom - top + 1))
        croppedPixmap = croppedPixmap.scaled(size)

        # Apply hue if specified
        if hue is not None:
            croppedPixmap = ColorCalc.ApplyHue(croppedPixmap, hue)

        return QIcon(croppedPixmap)

    """
    Calculates the contrast between the colors defined in ColorCalc.COLOROPTIONS and the given color. 
    Then returns the color with the highest contrast from ColorCalc.COLOROPTIONs

    args:
        color (QColor|str) 

    Returns:
        QColor: The color with the highest contrast to be used as the background for the given color
    """
    @staticmethod
    def GoodContrastColorForBackground(color: Union[QColor, str]) -> QColor: 
        if isinstance(color, str):
            color = QColor(color)
        elif not isinstance(color, QColor):
            raise TypeError("color must be either a QColor object or a string")
        
        contrastRatios = {}
        for colorOption in ColorCalc.COLOROPTIONS:
            contrastRatios[ColorCalc.ContrastRatio(color, colorOption)] = colorOption

        return contrastRatios[max(contrastRatios)]

    """
    Apply a hue tint to a given QPixmap.

    This method takes a source QPixmap and applies a hue tint to it, creating a new QPixmap with the
    specified hue. The method returns the modified QPixmap.

    Args:
        pixmap (QPixmap): The source QPixmap to apply the hue tint to.
        hue (QColor): The QColor representing the hue to apply to the QPixmap.

    Returns:
        QPixmap: A new QPixmap with the hue tint applied.
    """
    @staticmethod
    def ApplyHue(pixmap: QPixmap, hue: QColor) -> QPixmap:
        # Create a mask from the transparent pixels in the source pixmap
        mask = pixmap.createMaskFromColor(QColor(0, 0, 0, 0), Qt.MaskInColor)

        # Create a new pixmap filled with the specified hue
        huePixmap = QPixmap(pixmap.size())
        huePixmap.fill(hue)
        huePixmap.setMask(mask)

        # Draw the hue pixmap onto the source pixmap using the mask
        painter = QPainter(pixmap)
        painter.drawPixmap(0, 0, huePixmap)
        painter.end()

        return pixmap