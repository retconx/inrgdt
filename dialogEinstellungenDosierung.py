import configparser, os
from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QCheckBox,
    QMessageBox,
)

class EinstellungenDosierung(QDialog):
    def __init__(self, configPath):
        super().__init__()

        #config.ini lesen
        configIni = configparser.ConfigParser()
        configIni.read(os.path.join(configPath, "config.ini"))
        self.dosen = configIni["Marcumar"]["dosen"].split("::")
        self.setWindowTitle("Dosierungen verwalten")
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type: ignore
        self.buttonBox.rejected.connect(self.reject) # type: ignore

        self.dosierungen = {}
        self.dosierungen[0] = ["0.25", "0.5", "0.75", "1"]
        self.dosierungen[1] = ["1.25", "1.5", "1.75", "2"]
        self.dosierungen[2] = ["2.25", "2.5", "2.75", "3"]

        dialogLayoutV = QVBoxLayout()
        dialogLayoutG = QGridLayout()
        self.checkBoxDosierungen = []
        tempcheckBoxListe = []
        for zeile in range(3):
            tempcheckBoxListe.clear()
            for spalte in range(4):
                tempcheckBoxListe.append(QCheckBox(self.dosierungen[zeile][spalte].replace(".", ",")))
                tempcheckBoxListe[spalte].setChecked(self.dosierungen[zeile][spalte] in self.dosen)
                dialogLayoutG.addWidget(tempcheckBoxListe[spalte], zeile, spalte)
            self.checkBoxDosierungen.append(tempcheckBoxListe.copy())
        dialogLayoutG.setSpacing(20)
        dialogLayoutV.addLayout(dialogLayoutG)
        dialogLayoutV.addWidget(self.buttonBox)

        self.setLayout(dialogLayoutV)
        