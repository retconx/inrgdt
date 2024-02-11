import configparser, os, re
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
    QCheckBox,
    QMessageBox
)

zeichensatz = ["7Bit", "IBM (Standard) CP 437", "ISO8859-1 (ANSI) CP 1252"]

class EinstellungenAllgemein(QDialog):
    def __init__(self, configPath):
        super().__init__()

        #config.ini lesen
        configIni = configparser.ConfigParser()
        configIni.read(os.path.join(configPath, "config.ini"))
        self.einrichtungsname = configIni["Allgemein"]["einrichtungsname"]
        self.archivierungspfad = configIni["Allgemein"]["archivierungspfad"]
        self.vorherigeDokuLaden = configIni["Allgemein"]["vorherigedokuladen"]
        self.wochentageAnzeigen = configIni["Allgemein"]["wochentageanzeigen"] == "True"
        self.leerzeichenVor = configIni["Allgemein"]["lzvor"]
        self.leerzeichenNach = configIni["Allgemein"]["lznach"]

        self.setWindowTitle("Allgemeine Einstellungen")
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type:ignore
        self.buttonBox.rejected.connect(self.reject) # type:ignore

        dialogLayoutV = QVBoxLayout()
        # Groupbox Wochentagsübertragung
        groupboxLayoutWochentagsUebertragungG = QGridLayout()
        groupBoxWochentagsUebertragung = QGroupBox("Wochentagsübertragung")
        groupBoxWochentagsUebertragung.setStyleSheet("font-weight:bold")
        self.checkBoxWochentagsuebertragungAktivieren = QCheckBox("Aktivieren")
        self.checkBoxWochentagsuebertragungAktivieren.setStyleSheet("font-weight:normal")
        self.checkBoxWochentagsuebertragungAktivieren.setChecked(self.wochentageAnzeigen)
        self.checkBoxWochentagsuebertragungAktivieren.stateChanged.connect(self.checkBoxWochentagsuebertragungAktivierenChanged)
        labelLeerzeichen = QLabel("Zeilenkonfiguration:")
        labelLeerzeichen.setStyleSheet("font-weight:normal")
        labelLeerzeichenVor = QLabel("Anzahl Leerzeichen Vor:")
        labelLeerzeichenVor.setStyleSheet("font-weight:normal")
        self.lineEditLeerzeichenVor = QLineEdit(self.leerzeichenVor)
        self.lineEditLeerzeichenVor.setStyleSheet("font-weight:normal")
        self.lineEditLeerzeichenVor.setEnabled(self.wochentageAnzeigen)
        labelLeerzeichenNach = QLabel("Anzahl Leerzeichen Nach:")
        labelLeerzeichenNach.setStyleSheet("font-weight:normal")
        self.lineEditLeerzeichenNach = QLineEdit(self.leerzeichenNach)
        self.lineEditLeerzeichenNach.setStyleSheet("font-weight:normal")
        self.lineEditLeerzeichenNach.setEnabled(self.wochentageAnzeigen)
        labelWochentagLegende = QLabel("INR[Leerzeichen Vor]Mo[Leerzeichen Nach][Leerzeichen Vor]Di[Leerzeichen Nach]...[Leerzeichen Vor]So[Leerzeichen Nach]")
        labelWochentagLegende.setStyleSheet("font-weight:normal;font-style:italic")
        groupboxLayoutWochentagsUebertragungG.addWidget(self.checkBoxWochentagsuebertragungAktivieren, 0, 0, 1, 4)
        groupboxLayoutWochentagsUebertragungG.addWidget(labelLeerzeichen, 1, 0, 1, 4)
        groupboxLayoutWochentagsUebertragungG.addWidget(labelLeerzeichenVor, 2, 0, 1, 1)
        groupboxLayoutWochentagsUebertragungG.addWidget(self.lineEditLeerzeichenVor, 2, 1, 1, 1)
        groupboxLayoutWochentagsUebertragungG.addWidget(labelLeerzeichenNach, 2, 2, 1, 1)
        groupboxLayoutWochentagsUebertragungG.addWidget(self.lineEditLeerzeichenNach, 2, 3, 1, 1)
        groupboxLayoutWochentagsUebertragungG.addWidget(labelWochentagLegende, 3, 0, 1, 4)
        groupBoxWochentagsUebertragung.setLayout(groupboxLayoutWochentagsUebertragungG)

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
        dialogLayoutV.addWidget(groupBoxWochentagsUebertragung)
        dialogLayoutV.addWidget(groupboxEinrichtung)
        dialogLayoutV.addWidget(groupboxArchivierung)
        dialogLayoutV.addWidget(self.buttonBox)
        self.setLayout(dialogLayoutV)

    def checkBoxWochentagsuebertragungAktivierenChanged(self):
        self.lineEditLeerzeichenVor.setEnabled(self.checkBoxWochentagsuebertragungAktivieren.isChecked())
        self.lineEditLeerzeichenNach.setEnabled(self.checkBoxWochentagsuebertragungAktivieren.isChecked())

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
    
    def accept(self):
        patternZahl = r"^\d+$"
        if re.match(patternZahl, self.lineEditLeerzeichenVor.text()) == None:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InrGDT", "Leerzeichenanzahl Vor ungültig", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditLeerzeichenVor.setFocus()
            self.lineEditLeerzeichenVor.selectAll()
        elif re.match(patternZahl, self.lineEditLeerzeichenNach.text()) == None:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InrGDT", "Leerzeichenanzahl Nach ungültig", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditLeerzeichenNach.setFocus()
            self.lineEditLeerzeichenNach.selectAll()
        else:
            self.done(1)