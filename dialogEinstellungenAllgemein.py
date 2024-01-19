import configparser, os
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QCheckBox
)

zeichensatz = ["7Bit", "IBM (Standard) CP 437", "ISO8859-1 (ANSI) CP 1252"]

class EinstellungenAllgemein(QDialog):
    def __init__(self, configPath):
        super().__init__()
        self.setFixedWidth(500)

        #config.ini lesen
        configIni = configparser.ConfigParser()
        configIni.read(os.path.join(configPath, "config.ini"))
        self.einrichtungsname = configIni["Allgemein"]["einrichtungsname"]
        self.archivierungspfad = configIni["Allgemein"]["archivierungspfad"]
        self.vorherigeDokuLaden = configIni["Allgemein"]["vorherigedokuladen"]

        self.setWindowTitle("Allgemeine Einstellungen")
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type:ignore
        self.buttonBox.rejected.connect(self.reject) # type:ignore

        dialogLayoutV = QVBoxLayout()
        # Groupbox Einrichtung
        groupboxLayoutEinrichtungG = QGridLayout()
        groupboxEinrichtung = QGroupBox("Einrichtung/Praxis")
        groupboxEinrichtung.setStyleSheet("font-weight:bold")
        labelEinrichtungsname = QLabel("Name:")
        labelEinrichtungsname.setStyleSheet("font-weight:normal")
        self.lineEditEinrichtungsname = QLineEdit(self.einrichtungsname)
        self.lineEditEinrichtungsname.setStyleSheet("font-weight:normal")
        groupboxLayoutEinrichtungG.addWidget(labelEinrichtungsname, 0, 0)
        groupboxLayoutEinrichtungG.addWidget(self.lineEditEinrichtungsname, 0, 1)
        groupboxEinrichtung.setLayout(groupboxLayoutEinrichtungG)
        # Groupbox Archivierung
        groupboxLayoutArchivierungG = QGridLayout()
        groupboxArchivierung = QGroupBox("Archivierung")
        groupboxArchivierung.setStyleSheet("font-weight:bold")
        labelArchivierungsverzeichnis= QLabel("Archivierungsverzeichnis:")
        labelArchivierungsverzeichnis.setStyleSheet("font-weight:normal")
        self.lineEditArchivierungsverzeichnis = QLineEdit(self.archivierungspfad)
        self.lineEditArchivierungsverzeichnis.setStyleSheet("font-weight:normal")
        self.lineEditArchivierungsverzeichnis.setToolTip(self.archivierungspfad)
        buttonDurchsuchenArchivierungsverzeichnis= QPushButton("Durchsuchen")
        buttonDurchsuchenArchivierungsverzeichnis.setStyleSheet("font-weight:normal")
        buttonDurchsuchenArchivierungsverzeichnis.clicked.connect(self.durchsuchenArchivierungsverzeichnis)
        self.checkBoxVorherigeDokuLaden = QCheckBox("Vorherige Dokumentation beim Programmstart laden")
        self.checkBoxVorherigeDokuLaden.setStyleSheet("font-weight:normal")
        self.checkBoxVorherigeDokuLaden.setChecked(self.vorherigeDokuLaden == "True")
        groupboxLayoutArchivierungG.addWidget(labelArchivierungsverzeichnis, 0, 0, 1, 2)
        groupboxLayoutArchivierungG.addWidget(self.lineEditArchivierungsverzeichnis, 1, 0)
        groupboxLayoutArchivierungG.addWidget(buttonDurchsuchenArchivierungsverzeichnis, 1, 1)
        groupboxLayoutArchivierungG.addWidget(self.checkBoxVorherigeDokuLaden, 2, 0, 1, 2)
        groupboxArchivierung.setLayout(groupboxLayoutArchivierungG)
        dialogLayoutV.addWidget(groupboxEinrichtung)
        dialogLayoutV.addWidget(groupboxArchivierung)
        dialogLayoutV.addWidget(self.buttonBox)
        self.setLayout(dialogLayoutV)

    def durchsuchenArchivierungsverzeichnis(self):
        fd = QFileDialog(self)
        fd.setFileMode(QFileDialog.FileMode.Directory)
        fd.setWindowTitle("Archivierungsverzeichnis")
        fd.setDirectory(self.archivierungspfad)
        fd.setModal(True)
        fd.setLabelText(QFileDialog.DialogLabel.Accept, "Ok")
        fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
        if fd.exec() == 1:
            self.archivierungspfad = fd.directory()
            self.lineEditArchivierungsverzeichnis.setText(fd.directory().path())