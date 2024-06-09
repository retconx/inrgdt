from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QLabel
)
from PySide6.QtGui import Qt, QDesktopServices

class UeberInrGdt(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Über InrGDT")
        self.setFixedWidth(400)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.accepted.connect(self.accept) # type: ignore

        dialogLayoutV = QVBoxLayout()
        labelBeschreibung = QLabel("<span style='font-weight:bold'>Programmbeschreibung:</span><br>InrGDT ist eine eigenständig plattformunabhängig lauffähige Software zur elektronischen Dokumentation des INR-Wertes sowie der Phenprocoumon-/ Warfarin-Dosierung via GDT-Schnittstelle in ein beliebiges Praxisverwaltungssystem.")
        labelBeschreibung.setAlignment(Qt.AlignmentFlag.AlignJustify)
        labelBeschreibung.setWordWrap(True)
        labelBeschreibung.setTextFormat(Qt.TextFormat.RichText)
        labelEntwickelsVon = QLabel("<span style='font-weight:bold'>Entwickelt von:</span><br>Fabian Treusch<br><a href='https://gdttools.de'>gdttools.de</a>")
        labelEntwickelsVon.setTextFormat(Qt.TextFormat.RichText)
        labelEntwickelsVon.linkActivated.connect(self.gdtToolsLinkGeklickt)
        labelHilfe = QLabel("<span style='font-weight:bold'>Hilfe:</span><br><a href='https://github.com/retconx/inrgdt/wiki'>InrGDT Wiki</a>")
        labelHilfe.setTextFormat(Qt.TextFormat.RichText)
        labelHilfe.linkActivated.connect(self.githubWikiLinkGeklickt)

        dialogLayoutV.addWidget(labelBeschreibung)
        dialogLayoutV.addWidget(labelEntwickelsVon)
        dialogLayoutV.addWidget(labelHilfe)
        dialogLayoutV.addWidget(self.buttonBox)
        self.setLayout(dialogLayoutV)

    def gdtToolsLinkGeklickt(self, link):
        QDesktopServices.openUrl(link)

    def githubWikiLinkGeklickt(self, link):
        QDesktopServices.openUrl(link)