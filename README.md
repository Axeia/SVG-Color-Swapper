
# SVG Color Swapper

SVG color swapper is a utility made to change over SVG icons from one color palette to another to quickly port a bunch of icons from a set of colors over to another set of colors.

1. Select an input directory (it has to have SVGs in it)
2. Select an output directory (SVGs will be created [or overwritten] here)
3. Swap colors around (previewed as you do)
4. Hit save

![ss](https://i.imgur.com/2dfpUza.gif)

## Features
* Preview your icons at common icon sizes: 16, 32, 48, 64, 128. Accessible under the shortcuts <kbd>alt</kbd>+<kbd>1</kbd> to <kbd>5</kbd>
* Live preview of the color swap and contrast as you select the color
* Calculates the contrast based on the [Web Accessibility Iniative's Contrast Article](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html).
	* 👍 If the contrast is higher than 4.5:1 it gets a (green) thumb up icon*
	* 👌 If the contrast is lower than 4.5:1 but higher than 3:1 it gets an (orange) Ok icon*
	* 👎 If the contrast is lower than 3:1 it gets a (red) thumbs down icon*
* (Almost?) all UI settings are saved as you use them and will restore themselves when you restart the application
* The color widget on the side can be be positioned by dragging it (it can be on the left or right, or undocked [floating]).
* Different backgrounds for the icon lists? Different background colors for the color tree widget (for easy visual identification)
	* Background colors are customizable - you can add your own
* Cross platform compatible - written in Python using Qt/PySide6
	* Style icons as disabled to see what they would look like in Qt in the disabled state (if you want disabled icons to actually look disabled - avoid gray as a color!)

>**Note**
>  This application relies on [Qt's SVGRenderer](https://doc.qt.io/qtforpython-6/PySide6/QtSvg/QSvgRenderer.html), including it's limitation of only supporting up up to [SVG Tiny 1.2](https://www.w3.org/TR/SVGTiny12/). 
>	This means a lot of things don't work (like for example ), if you're writing a Qt based app this is however a pro not a con. If it works in this it should work with any Qt app! 

  
If the save button is grayed out there should be a description next to it to warn you why icons cannot be saved yet.

  
*The icons are color coded in the app but not here, they actually use the same emoticon but color shifted for easier recognition of what is good or bad (or just ok).

# How to run
Make sure you python, pip and PySide6 installed. 
`pip install PySide6`
Download this project and just run main.py with:
`python main.py`

*It's been developed with Python 3.10.11, if it bugs out in other versions of Python feel free to submit an issue*

# License
MIT