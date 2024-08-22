import configparser, os, re, sys
from PySide6.QtGui import QFont
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

        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)

        #config.ini lesen
        configIni = configparser.ConfigParser()
        configIni.read(os.path.join(configPath, "config.ini"))
        self.einrichtungsname = configIni["Allgemein"]["einrichtungsname"]
        self.archivierungspfad = configIni["Allgemein"]["archivierungspfad"]
        self.vorherigeDokuLaden = configIni["Allgemein"]["vorherigedokuladen"]
        self.wochentageAnzeigen = configIni["Allgemein"]["wochentageanzeigen"] == "True"
        self.leerzeichenVor = configIni["Allgemein"]["lzvor"]
        self.leerzeichenNach = configIni["Allgemein"]["lznach"]
        self.autoupdate = configIni["Allgemein"]["autoupdate"] == "True"
        self.updaterpfad = configIni["Allgemein"]["updaterpfad"]

        self.setWindowTitle("Allgemeine Einstellungen")
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type:ignore
        self.buttonBox.rejected.connect(self.reject) # type:ignore

        dialogLayoutV = QVBoxLayout()
        # Groupbox Wochentagsübertragung
        groupboxLayoutWochentagsUebertragungG = QGridLayout()
        groupBoxWochentagsUebertragung = QGroupBox("Wochentagsübertragung")
        groupBoxWochentagsUebertragung.setFont(self.fontBold)
        self.checkBoxWochentagsuebertragungAktivieren = QCheckBox("Aktivieren")
        self.checkBoxWochentagsuebertragungAktivieren.setFont(self.fontNormal)
        self.checkBoxWochentagsuebertragungAktivieren.setChecked(self.wochentageAnzeigen)
        self.checkBoxWochentagsuebertragungAktivieren.stateChanged.connect(self.checkBoxWochentagsuebertragungAktivierenChanged)
        labelLeerzeichen = QLabel("Zeilenkonfiguration:")
        labelLeerzeichen.setFont(self.fontNormal)
        labelLeerzeichenVor = QLabel("Anzahl Leerzeichen Vor:")
        labelLeerzeichenVor.setFont(self.fontNormal)
        self.lineEditLeerzeichenVor = QLineEdit(self.leerzeichenVor)
        self.lineEditLeerzeichenVor.setFont(self.fontNormal)
        self.lineEditLeerzeichenVor.setEnabled(self.wochentageAnzeigen)
        labelLeerzeichenNach = QLabel("Anzahl Leerzeichen Nach:")
        labelLeerzeichenNach.setFont(self.fontNormal)
        self.lineEditLeerzeichenNach = QLineEdit(self.leerzeichenNach)
        self.lineEditLeerzeichenNach.setFont(self.fontNormal)
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
        groupboxEinrichtung.setFont(self.fontBold)
        labelEinrichtungsname = QLabel("Name:")
        labelEinrichtungsname.setFont(self.fontNormal)
        self.lineEditEinrichtungsname = QLineEdit(self.einrichtungsname)
        self.lineEditEinrichtungsname.setFont(self.fontNormal)
        groupboxLayoutEinrichtungG.addWidget(labelEinrichtungsname, 0, 0)
        groupboxLayoutEinrichtungG.addWidget(self.lineEditEinrichtungsname, 0, 1)
        groupboxEinrichtung.setLayout(groupboxLayoutEinrichtungG)
        # Groupbox Archivierung
        groupboxLayoutArchivierungG = QGridLayout()
        groupboxArchivierung = QGroupBox("Archivierung")
        groupboxArchivierung.setFont(self.fontBold)
        labelArchivierungsverzeichnis= QLabel("Archivierungsverzeichnis:")
        labelArchivierungsverzeichnis.setFont(self.fontNormal)
        self.lineEditArchivierungsverzeichnis = QLineEdit(self.archivierungspfad)
        self.lineEditArchivierungsverzeichnis.setFont(self.fontNormal)
        self.lineEditArchivierungsverzeichnis.setToolTip(self.archivierungspfad)
        buttonDurchsuchenArchivierungsverzeichnis= QPushButton("...")
        buttonDurchsuchenArchivierungsverzeichnis.setFont(self.fontNormal)
        buttonDurchsuchenArchivierungsverzeichnis.clicked.connect(self.durchsuchenArchivierungsverzeichnis)
        self.checkBoxVorherigeDokuLaden = QCheckBox("Vorherige Dokumentation beim Programmstart laden")
        self.checkBoxVorherigeDokuLaden.setFont(self.fontNormal)
        self.checkBoxVorherigeDokuLaden.setChecked(self.vorherigeDokuLaden == "True")
        groupboxLayoutArchivierungG.addWidget(labelArchivierungsverzeichnis, 0, 0, 1, 2)
        groupboxLayoutArchivierungG.addWidget(self.lineEditArchivierungsverzeichnis, 1, 0)
        groupboxLayoutArchivierungG.addWidget(buttonDurchsuchenArchivierungsverzeichnis, 1, 1)
        groupboxLayoutArchivierungG.addWidget(self.checkBoxVorherigeDokuLaden, 2, 0, 1, 2)
        groupboxArchivierung.setLayout(groupboxLayoutArchivierungG)

        # GroupBox Updates
        groupBoxUpdatesLayoutG = QGridLayout()
        groupBoxUpdates = QGroupBox("Updates")
        groupBoxUpdates.setFont(self.fontBold)
        labelUpdaterPfad = QLabel("Updater-Pfad")
        labelUpdaterPfad.setFont(self.fontNormal)
        self.lineEditUpdaterPfad= QLineEdit(self.updaterpfad)
        self.lineEditUpdaterPfad.setFont(self.fontNormal)
        self.lineEditUpdaterPfad.setToolTip(self.updaterpfad)
        if not os.path.exists(self.updaterpfad):
            self.lineEditUpdaterPfad.setStyleSheet("background:rgb(255,200,200)")
        self.pushButtonUpdaterPfad = QPushButton("...")
        self.pushButtonUpdaterPfad.setFont(self.fontNormal)
        self.pushButtonUpdaterPfad.clicked.connect(self.pushButtonUpdaterPfadClicked)
        self.checkBoxAutoUpdate = QCheckBox("Automatisch auf Update prüfen")
        self.checkBoxAutoUpdate.setFont(self.fontNormal)
        self.checkBoxAutoUpdate.setChecked(self.autoupdate)

        groupBoxUpdatesLayoutG.addWidget(labelUpdaterPfad, 0, 0)
        groupBoxUpdatesLayoutG.addWidget(self.lineEditUpdaterPfad, 0, 1)
        groupBoxUpdatesLayoutG.addWidget(self.pushButtonUpdaterPfad, 0, 2)
        groupBoxUpdatesLayoutG.addWidget(self.checkBoxAutoUpdate, 1, 0)
        groupBoxUpdates.setLayout(groupBoxUpdatesLayoutG)

        dialogLayoutV.addWidget(groupBoxWochentagsUebertragung)
        dialogLayoutV.addWidget(groupboxEinrichtung)
        dialogLayoutV.addWidget(groupboxArchivierung)
        dialogLayoutV.addWidget(groupBoxUpdates)
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
            self.lineEditArchivierungsverzeichnis.setText(os.path.abspath(fd.directory().path()))
            self.lineEditArchivierungsverzeichnis.setToolTip(os.path.abspath(fd.directory().path()))

    def pushButtonUpdaterPfadClicked(self):
        fd = QFileDialog(self)
        fd.setFileMode(QFileDialog.FileMode.ExistingFile)
        if os.path.exists(self.lineEditUpdaterPfad.text()):
            fd.setDirectory(os.path.dirname(self.lineEditUpdaterPfad.text()))
        fd.setWindowTitle("Updater-Pfad auswählen")
        fd.setModal(True)
        if "win32" in sys.platform:
            fd.setNameFilters(["exe-Dateien (*.exe)"])
        elif "darwin" in sys.platform:
            fd.setNameFilters(["app-Bundles (*.app)"])
        fd.setLabelText(QFileDialog.DialogLabel.Accept, "Auswählen")
        fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
        if fd.exec() == 1:
            self.lineEditUpdaterPfad.setText(os.path.abspath(fd.selectedFiles()[0]))
            self.lineEditUpdaterPfad.setToolTip(os.path.abspath(fd.selectedFiles()[0]))
            self.lineEditUpdaterPfad.setStyleSheet("background:rgb(255,255,255)")
    
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