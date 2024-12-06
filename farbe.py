from enum import Enum
from PySide6.QtGui import QPalette, QColor

class farben(Enum):
    NORMAL = {}
    GRUEN = {"hell" : (240, 255, 240), "dunkel" : (50, 100, 50)}
    ROT = {"hell" : (255, 240, 240), "dunkel" : (100, 50, 50)}

@staticmethod
def getTextPalette(farbe:farben, aktuellePalette:QPalette):
    if farbe == farben.NORMAL:
        return QPalette()
    modus = "hell"
    if aktuellePalette.color(QPalette.Base).value() < 150:
        modus = "dunkel"
    r, g, b = farbe.value[modus]
    palette = QPalette()
    palette.setColor(QPalette.Base, QColor(r, g, b))
    return palette