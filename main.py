import sys, configparser, os, datetime, shutil, logger, re
import gdt, gdtzeile, gdttoolsL
import dialogUeberInrGdt, dialogEinstellungenGdt, dialogEinstellungenBenutzer, dialogEinstellungenLanrLizenzschluessel, dialogEinstellungenImportExport, dialogEinstellungenDosierung
from PySide6.QtCore import Qt, QSize, QDate, QTime, QTranslator, QLibraryInfo
from PySide6.QtGui import QFont, QAction, QKeySequence, QIcon, QDesktopServices, QPalette, QColor
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QGroupBox,
    QPushButton,
    QHBoxLayout,
    QGridLayout,
    QWidget,
    QLabel, 
    QDateEdit,
    QComboBox,
    QMessageBox, 
    QCheckBox,
    QLineEdit,
    QTextEdit
)
import requests

basedir = os.path.dirname(__file__)
reInr = r"^\d([.,]\d)*$"

def versionVeraltet(versionAktuell:str, versionVergleich:str):
    """
    Vergleicht zwei Versionen im Format x.x.x
    Parameter:
        versionAktuell:str
        versionVergleich:str
    Rückgabe:
        True, wenn versionAktuell veraltet
    """
    versionVeraltet= False
    hunderterBase = int(versionVergleich.split(".")[0])
    zehnerBase = int(versionVergleich.split(".")[1])
    einserBase = int(versionVergleich.split(".")[2])
    hunderter = int(versionAktuell.split(".")[0])
    zehner = int(versionAktuell.split(".")[1])
    einser = int(versionAktuell.split(".")[2])
    if hunderterBase > hunderter:
        versionVeraltet = True
    elif hunderterBase == hunderter:
        if zehnerBase >zehner:
            versionVeraltet = True
        elif zehnerBase == zehner:
            if einserBase > einser:
                versionVeraltet = True
    return versionVeraltet

# Sicherstellen, dass Icon in Windows angezeigt wird
try:
    from ctypes import windll # type: ignore
    mayappid = "gdttools.inrgdt"
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(mayappid)
except ImportError:
    pass

class MainWindow(QMainWindow):

    # Mainwindow zentrieren
    def resizeEvent(self, e):
        mainwindowBreite = e.size().width()
        mainwindowHoehe = e.size().height()
        ag = self.screen().availableGeometry()
        screenBreite = ag.size().width()
        screenHoehe = ag.size().height()
        left = screenBreite / 2 - mainwindowBreite / 2
        top = screenHoehe / 2 - mainwindowHoehe / 2
        self.setGeometry(left, top, mainwindowBreite, mainwindowHoehe)

    def __init__(self):
        super().__init__()

        # config.ini lesen
        ersterStart = False
        updateSafePath = ""
        if sys.platform == "win32":
            logger.logger.info("Plattform: win32")
            updateSafePath = os.path.expanduser("~\\appdata\\local\\inrgdt")
        else:
            logger.logger.info("Plattform: nicht win32")
            updateSafePath = os.path.expanduser("~/.config/inrgdt")
        self.configPath = updateSafePath
        self.configIni = configparser.ConfigParser()
        if os.path.exists(os.path.join(updateSafePath, "config.ini")):
            logger.logger.info("config.ini in " + updateSafePath + " exisitert")
            self.configPath = updateSafePath
        elif os.path.exists(os.path.join(basedir, "config.ini")):
            logger.logger.info("config.ini in " + updateSafePath + " exisitert nicht")
            try:
                if (not os.path.exists(updateSafePath)):
                    logger.logger.info(updateSafePath + " exisitert nicht")
                    os.makedirs(updateSafePath, 0o777)
                    logger.logger.info(updateSafePath + "erzeugt")
                shutil.copy(os.path.join(basedir, "config.ini"), updateSafePath)
                logger.logger.info("config.ini von " + basedir + " nach " + updateSafePath + " kopiert")
                self.configPath = updateSafePath
                ersterStart = True
            except:
                logger.logger.error("Problem beim Kopieren der config.ini von " + basedir + " nach " + updateSafePath)
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InrGDT", "Problem beim Kopieren der Konfigurationsdatei. InrGDT wird mit Standardeinstellungen gestartet.", QMessageBox.StandardButton.Ok)
                mb.exec()
                self.configPath = basedir
        else:
            logger.logger.critical("config.ini fehlt")
            mb = QMessageBox(QMessageBox.Icon.Critical, "Hinweis von InrGDT", "Die Konfigurationsdatei config.ini fehlt. InrGDT kann nicht gestartet werden.", QMessageBox.StandardButton.Ok)
            mb.exec()
            sys.exit()
        self.configIni.read(os.path.join(self.configPath, "config.ini"))
        self.version = self.configIni["Allgemein"]["version"]
        self.immerextern = self.configIni["Allgemein"]["immerextern"] == "True"
        self.gdtImportVerzeichnis = self.configIni["GDT"]["gdtimportverzeichnis"]
        self.gdtExportVerzeichnis = self.configIni["GDT"]["gdtexportverzeichnis"]
        self.kuerzelinrgdt = self.configIni["GDT"]["kuerzelinrgdt"]
        self.kuerzelpraxisedv = self.configIni["GDT"]["kuerzelpraxisedv"]
        self.benutzernamenListe = self.configIni["Benutzer"]["namen"].split("::")
        self.benutzerkuerzelListe = self.configIni["Benutzer"]["kuerzel"].split("::")
        self.aktuelleBenuztzernummer = int(self.configIni["Benutzer"]["letzter"])
        self.dosen = self.configIni["Marcumar"]["dosen"].split("::")

        # Nachträglich hinzufefügte Options
        # 3.10.0
        # self.benutzeruebernehmen = False
        # if self.configIni.has_option("Allgemein", "benutzeruebernehmen"):
        #     self.benutzeruebernehmen = (self.configIni["Allgemein"]["benutzeruebernehmen"] == "1")
        # /Nachträglich hinzufefügte Options

        z = self.configIni["GDT"]["zeichensatz"]
        self.zeichensatz = gdt.GdtZeichensatz.IBM_CP437
        if z == "1":
            self.zeichensatz = gdt.GdtZeichensatz.BIT_7
        elif z == "3":
            self.zeichensatz = gdt.GdtZeichensatz.ANSI_CP1252
        self.lanr = self.configIni["Erweiterungen"]["lanr"]
        self.lizenzschluessel = self.configIni["Erweiterungen"]["lizenzschluessel"]

        # Prüfen, ob Lizenzschlüssel unverschlüsselt
        if len(self.lizenzschluessel) == 29:
            logger.logger.info("Lizenzschlüssel unverschlüsselt")
            self.configIni["Erweiterungen"]["lizenzschluessel"] = gdttoolsL.GdtToolsLizenzschluessel.krypt(self.lizenzschluessel)
            with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                    self.configIni.write(configfile)
        else:
            self.lizenzschluessel = gdttoolsL.GdtToolsLizenzschluessel.dekrypt(self.lizenzschluessel)

        # Grundeinstellungen bei erstem Start
        if ersterStart:
            logger.logger.info("Erster Start")
            mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von InrGDT", "Vermutlich starten Sie InrGDT das erste Mal auf diesem PC.\nMöchten Sie jetzt die Grundeinstellungen vornehmen?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.setDefaultButton(QMessageBox.StandardButton.Yes)
            if mb.exec() == QMessageBox.StandardButton.Yes:
                self.einstellungenLanrLizenzschluessel(False)
                self.einstellungenGdt(False)
                self.einstellungenBenutzer(False)
                self.einstellungenDosierung(False, True)

        # Version vergleichen und gegebenenfalls aktualisieren
        configIniBase = configparser.ConfigParser()
        try:
            configIniBase.read(os.path.join(basedir, "config.ini"))
            if versionVeraltet(self.version, configIniBase["Allgemein"]["version"]):
                # Version aktualisieren
                self.configIni["Allgemein"]["version"] = configIniBase["Allgemein"]["version"]
                self.configIni["Allgemein"]["releasedatum"] = configIniBase["Allgemein"]["releasedatum"] 
                # config.ini aktualisieren
                # 3.9.0 -> 3.10.0: ["Allgemein"]["benutzeruebernehmen"], ["Allgemein"]["einrichtunguebernehmen"] und ["Benutzer"]["einrichtung"] hinzufügen
                # if not self.configIni.has_option("Allgemein", "benutzeruebernehmen"):
                #     self.configIni["Allgemein"]["benutzeruebernehmen"] = "0"
                # /config.ini aktualisieren

                with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                    self.configIni.write(configfile)
                self.version = self.configIni["Allgemein"]["version"]
                logger.logger.info("Version auf " + self.version + " aktualisiert")
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InrGDT", "InrGDT wurde erfolgreich auf Version " + self.version + " aktualisiert.<br />Falls InrGDT Ihren Praxisalltag erleichtert, würde ich mich über eine kleine Anerkennung freuen. Unter <a href='https://gdttools.de/inrgdt.php#spende'>gdtools.de</a> finden Sie Informationen über die Möglichkeit einer Spende. Dankeschön! &#x1f609;", QMessageBox.StandardButton.Ok)
                mb.setTextFormat(Qt.TextFormat.RichText)
                mb.exec()
        except:
            logger.logger.error("Problem beim Aktualisieren auf Version " + configIniBase["Allgemein"]["version"])
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InrGDT", "Problem beim Aktualisieren auf Version " + configIniBase["Allgemein"]["version"], QMessageBox.StandardButton.Ok)
            mb.exec()

        # Add-Ons freigeschaltet?
        self.addOnsFreigeschaltet = gdttoolsL.GdtToolsLizenzschluessel.lizenzErteilt(self.lizenzschluessel, self.lanr, gdttoolsL.SoftwareId.INRGDT)
        
        jahr = datetime.datetime.now().year
        copyrightJahre = "2024"
        if jahr > 2024:
            copyrightJahre = "2024-" + str(jahr)
        self.setWindowTitle("InrGDT V" + self.version + " (\u00a9 Fabian Treusch - GDT-Tools " + copyrightJahre + ")")
        self.setFixedWidth(600)
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)
        self.fontBoldGross = QFont()
        self.fontBoldGross.setBold(True)
        self.fontBoldGross.setPixelSize(16)
        self.fontGross = QFont()
        self.fontGross.setPixelSize(16)

        # GDT-Datei laden
        gd = gdt.GdtDatei()
        self.patId = "-"
        self.name = "-"
        self.geburtsdatum = "-"
        mbErg = QMessageBox.StandardButton.Yes
        try:
            # Prüfen, ob PVS-GDT-ID eingetragen
            senderId = self.configIni["GDT"]["idpraxisedv"]
            if senderId == "":
                senderId = None
            gd.laden(self.gdtImportVerzeichnis + "/" + self.kuerzelinrgdt + self.kuerzelpraxisedv + ".gdt", self.zeichensatz, senderId)
            self.patId = str(gd.getInhalt("3000"))
            self.name = str(gd.getInhalt("3102")) + " " + str(gd.getInhalt("3101"))
            logger.logger.info("PatientIn " + self.name + " (ID: " + self.patId + ") geladen")
            self.geburtsdatum = str(gd.getInhalt("3103"))[0:2] + "." + str(gd.getInhalt("3103"))[2:4] + "." + str(gd.getInhalt("3103"))[4:8]
        except (IOError, gdtzeile.GdtFehlerException) as e:
            logger.logger.warning("Fehler beim Laden der GDT-Datei: " + str(e))
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InrGDT", "Fehler beim Laden der GDT-Datei:\n" + str(e) + "\n\nSoll InrGDT dennoch geöffnet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
            mb.button(QMessageBox.StandardButton.No).setText("Nein")
            mb.setDefaultButton(QMessageBox.StandardButton.No)
            mbErg = mb.exec()
        if mbErg == QMessageBox.StandardButton.Yes:
            self.widget = QWidget()
            self.widget.installEventFilter(self)

            # Formularaufbau
            wochentage = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
            mainLayoutV = QVBoxLayout()
            kopfLayoutG = QGridLayout()
            labelName = QLabel("Name")
            self.lineEditName = QLineEdit(self.name)
            self.lineEditName.setReadOnly(True)
            labelPatId = QLabel("ID")
            self.lineEditPatid = QLineEdit(self.patId)
            self.lineEditPatid.setReadOnly(True)
            labelGeburtsdatum = QLabel("Geburtsdatum")
            self.lineEditGeburtsdatum = QLineEdit(self.geburtsdatum)
            self.lineEditGeburtsdatum.setReadOnly(True)
            labelInr = QLabel("INR")
            labelInr.setFont(self.fontGross)
            self.lineEditInr = QLineEdit()
            self.lineEditInr.setFont(self.fontGross)
            self.lineEditInr.textEdited.connect(self.lineEditInrEdited)
            self.checkBoxExtern = QCheckBox("Extern bestimmter Wert")
            self.checkBoxExtern.setFont(self.fontGross)
            self.checkBoxExtern.setChecked(self.immerextern)
            self.checkBoxImmer= QCheckBox("Immer extern bestimmt")
            self.checkBoxImmer.setFont(self.fontGross)
            self.checkBoxImmer.setChecked(self.immerextern)
            self.checkBoxImmer.clicked.connect(self.checkBoxImmerClicked)
            kopfLayoutG.addWidget(labelName, 0, 0)
            kopfLayoutG.addWidget(self.lineEditName, 0, 1)
            kopfLayoutG.addWidget(labelPatId, 0, 2)
            kopfLayoutG.addWidget(self.lineEditPatid, 0, 3)
            kopfLayoutG.addWidget(labelGeburtsdatum, 0, 4)
            kopfLayoutG.addWidget(self.lineEditGeburtsdatum, 0, 5)
            kopfLayoutG.addWidget(labelInr, 1, 0)
            kopfLayoutG.addWidget(self.lineEditInr, 1, 1)
            kopfLayoutG.addWidget(self.checkBoxExtern, 1, 2, 1, 2)
            kopfLayoutG.addWidget(self.checkBoxImmer, 1, 4, 1, 2)
            
            inrLayoutG = QGridLayout()
            labelWochentage = []
            self.pushButtonDosen = []
            pushButtonDosenTemp = []
            self.pushButtonDosenAlle = []
            for wt in range(7):
                labelWochentage.append(QLabel(wochentage[wt]))
                labelWochentage[wt].setFont(self.fontGross)
                inrLayoutG.addWidget(labelWochentage[wt], 0, wt, 1, 1, Qt.AlignmentFlag.AlignCenter)
            labelAlle = QLabel("Alle")
            labelAlle.setFont(self.fontBoldGross)
            inrLayoutG.addWidget(labelAlle, 0, 7, 1, 1, Qt.AlignmentFlag.AlignCenter)
            
            # Buttons aufbauen
            for dosis in range(len(self.dosen)):
                pushButtonDosenTemp.clear()
                buttonText = str(self.dosen[dosis])
                if buttonText != "0":
                    buttonText = buttonText.replace(".25", "\u00bc").replace(".5", "\u00bd").replace(".75", "\u00be").replace(".", "").replace("0", "")
                for wt in range(7):
                    pushButtonDosenTemp.append(QPushButton(buttonText))
                    pushButtonDosenTemp[wt].setCheckable(True)
                    pushButtonDosenTemp[wt].setFont(self.fontGross)
                    pushButtonDosenTemp[wt].setAutoFillBackground(True)
                    pushButtonDosenTemp[wt].clicked.connect(lambda dosiszeile=dosis, wochentagspalte=wt: self.pushButtonDosisClicked(dosiszeile, wochentagspalte))
                    inrLayoutG.addWidget(pushButtonDosenTemp[wt], dosis + 1, wt)
                self.pushButtonDosenAlle.append(QPushButton(buttonText))
                self.pushButtonDosenAlle[dosis].setFont(self.fontBoldGross)
                self.pushButtonDosenAlle[dosis].clicked.connect(lambda checked=False, dosiszeile=dosis: self.pushButtonAlleClicked(checked, dosiszeile))
                inrLayoutG.addWidget(self.pushButtonDosenAlle[dosis])
                self.pushButtonDosen.append(pushButtonDosenTemp.copy())
            
            # Bemerkungsfeld
            labelBemerkungen = QLabel("Bemerkungen")
            self.textEditBemerkungen = QTextEdit()
            self.textEditBemerkungen.setFixedHeight(40)

            # Untersuchungsdatum und Benutzer
            untdatBenutzerLayoutG = QGridLayout()
            labelUntersuchungsdatum = QLabel("Untersuchungsdatum")
            self.untersuchungsdatum = QDate().currentDate()
            self.dateEditUntersuchungsdatum = QDateEdit()
            self.dateEditUntersuchungsdatum.setDate(self.untersuchungsdatum)
            self.dateEditUntersuchungsdatum.setDisplayFormat("dd.MM.yyyy")
            self.dateEditUntersuchungsdatum.setCalendarPopup(True)
            self.dateEditUntersuchungsdatum.userDateChanged.connect(self.dateEditUntersuchungsdatumChanged) # type: ignore
            untdatBenutzerLayoutG.addWidget(labelUntersuchungsdatum, 0, 0)
            untdatBenutzerLayoutG.addWidget(self.dateEditUntersuchungsdatum, 1, 0)
            labelBenutzer = QLabel("Benutzer")
            self.comboBoxBenutzer = QComboBox()
            self.comboBoxBenutzer.addItems(self.benutzernamenListe)
            aktBenNum = 0
            if self.aktuelleBenuztzernummer < len(self.benutzernamenListe):
                aktBenNum = self.aktuelleBenuztzernummer
            self.comboBoxBenutzer.setCurrentIndex(aktBenNum)
            untdatBenutzerLayoutG.addWidget(labelBenutzer, 0, 1)
            untdatBenutzerLayoutG.addWidget(self.comboBoxBenutzer, 1, 1)

            # Senden-Button
            self.pushButtonSenden = QPushButton("Daten senden")
            self.pushButtonSenden.setStyleSheet("background:rgb(200,255,200);border-color:rgb(0,0,0);font-size:18px")
            self.pushButtonSenden.setFixedHeight(60)
            self.pushButtonSenden.setEnabled(self.addOnsFreigeschaltet)
            self.pushButtonSenden.clicked.connect(self.pushButtonSendenClicked)

            mainLayoutV.addLayout(kopfLayoutG)
            mainLayoutV.addLayout(inrLayoutG)
            mainLayoutV.addWidget(labelBemerkungen)
            mainLayoutV.addWidget(self.textEditBemerkungen)
            mainLayoutV.addLayout(untdatBenutzerLayoutG)
            mainLayoutV.addWidget(self.pushButtonSenden)
            self.widget.setLayout(mainLayoutV)

            self.setCentralWidget(self.widget)
            self.lineEditInr.setFocus()

            # Menü
            menubar = self.menuBar()
            anwendungMenu = menubar.addMenu("")
            aboutAction = QAction(self)
            aboutAction.setMenuRole(QAction.MenuRole.AboutRole)
            aboutAction.triggered.connect(self.ueberInrGdt) # type: ignore
            updateAction = QAction("Auf Update prüfen", self)
            updateAction.setMenuRole(QAction.MenuRole.ApplicationSpecificRole)
            updateAction.triggered.connect(self.updatePruefung) # type: ignore
            einstellungenMenu = menubar.addMenu("Einstellungen")
            einstellungenGdtAction = QAction("GDT-Einstellungen", self)
            einstellungenGdtAction.triggered.connect(lambda checked=False, neustartfrage=True: self.einstellungenGdt(checked, True)) # type: ignore
            einstellungenBenutzerAction = QAction("BenutzerInnen verwalten", self)
            einstellungenBenutzerAction.triggered.connect(lambda checked=False, neustartfrage=True: self.einstellungenBenutzer(checked, True)) # type: ignore
            einstellungenDosierungAction = QAction("Dosierungen verwalten", self)
            einstellungenDosierungAction.triggered.connect(lambda checked=False, neustartfrage=True: self.einstellungenDosierung(checked, True)) # type: ignore

            einstellungenErweiterungenAction = QAction("LANR/Lizenzschlüssel", self)
            einstellungenErweiterungenAction.triggered.connect(lambda checked=False, neustartfrage=True: self.einstellungenLanrLizenzschluessel(checked, True)) # type: ignore
            einstellungenImportExportAction = QAction("Im- /Exportieren", self)
            einstellungenImportExportAction.triggered.connect(self.einstellungenImportExport) # type: ignore
            einstellungenImportExportAction.setMenuRole(QAction.MenuRole.NoRole)
            hilfeMenu = menubar.addMenu("Hilfe")
            hilfeWikiAction = QAction("InrGDT Wiki", self)
            hilfeWikiAction.triggered.connect(self.inrgdtWiki) # type: ignore
            hilfeUpdateAction = QAction("Auf Update prüfen", self)
            hilfeUpdateAction.triggered.connect(self.updatePruefung) # type: ignore
            hilfeUeberAction = QAction("Über InrGDT", self)
            hilfeUeberAction.setMenuRole(QAction.MenuRole.NoRole)
            hilfeUeberAction.triggered.connect(self.ueberInrGdt) # type: ignore
            hilfeLogExportieren = QAction("Log-Verzeichnis exportieren", self)
            hilfeLogExportieren.triggered.connect(self.logExportieren) # type: ignore
            
            anwendungMenu.addAction(aboutAction)
            anwendungMenu.addAction(updateAction)
            einstellungenMenu.addAction(einstellungenGdtAction)
            einstellungenMenu.addAction(einstellungenBenutzerAction)
            einstellungenMenu.addAction(einstellungenDosierungAction)
            einstellungenMenu.addAction(einstellungenErweiterungenAction)
            einstellungenMenu.addAction(einstellungenImportExportAction)
            hilfeMenu.addAction(hilfeWikiAction)
            hilfeMenu.addSeparator()
            hilfeMenu.addAction(hilfeUpdateAction)
            hilfeMenu.addSeparator()
            hilfeMenu.addAction(hilfeUeberAction)
            hilfeMenu.addSeparator()
            hilfeMenu.addAction(hilfeLogExportieren)
            
            # Updateprüfung auf Github
            try:
                self.updatePruefung(meldungNurWennUpdateVerfuegbar=True)
            except Exception as e:
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InrGDT", "Updateprüfung nicht möglich.\nBitte überprüfen Sie Ihre Internetverbindung.", QMessageBox.StandardButton.Ok)
                mb.exec()
                logger.logger.warning("Updateprüfung nicht möglich: " + str(e))
        else:
            sys.exit()

    def updatePruefung(self, meldungNurWennUpdateVerfuegbar = False):
        response = requests.get("https://api.github.com/repos/retconx/inrgdt/releases/latest")
        githubRelaseTag = response.json()["tag_name"]
        latestVersion = githubRelaseTag[1:] # ohne v
        if versionVeraltet(self.version, latestVersion):
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InrGDT", "Die aktuellere InrGDT-Version " + latestVersion + " ist auf <a href='https://www.github.com/retconx/inrgdt/releases'>Github</a> verfügbar.", QMessageBox.StandardButton.Ok)
            mb.setTextFormat(Qt.TextFormat.RichText)
            mb.exec()
        elif not meldungNurWennUpdateVerfuegbar:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InrGDT", "Sie nutzen die aktuelle InrGDT-Version.", QMessageBox.StandardButton.Ok)
            mb.exec()

    def ueberInrGdt(self):
        de = dialogUeberInrGdt.UeberInrGdt()
        de.exec()

    def logExportieren(self):
        if (os.path.exists(os.path.join(basedir, "log"))):
            downloadPath = ""
            if sys.platform == "win32":
                downloadPath = os.path.expanduser("~\\Downloads")
            else:
                downloadPath = os.path.expanduser("~/Downloads")
            try:
                if shutil.copytree(os.path.join(basedir, "log"), os.path.join(downloadPath, "Log_InrGDT"), dirs_exist_ok=True):
                    shutil.make_archive(os.path.join(downloadPath, "Log_InrGDT"), "zip", root_dir=os.path.join(downloadPath, "Log_InrGDT"))
                    shutil.rmtree(os.path.join(downloadPath, "Log_InrGDT"))
                    mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InrGDT", "Das Log-Verzeichnis wurde in den Ordner " + downloadPath + " kopiert.", QMessageBox.StandardButton.Ok)
                    mb.exec()
            except Exception as e:
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InrGDT", "Problem beim Download des Log-Verzeichnisses: " + str(e), QMessageBox.StandardButton.Ok)
                mb.exec()
        else:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InrGDT", "Das Log-Verzeichnis wurde nicht gefunden.", QMessageBox.StandardButton.Ok)
            mb.exec() 

    def einstellungenGdt(self, checked, neustartfrage = False):
        de = dialogEinstellungenGdt.EinstellungenGdt(self.configPath)
        if de.exec() == 1:
            self.configIni["GDT"]["idinrgdt"] = de.lineEditInrGdtId.text()
            self.configIni["GDT"]["idpraxisedv"] = de.lineEditPraxisEdvId.text()
            self.configIni["GDT"]["gdtimportverzeichnis"] = de.lineEditImport.text()
            self.configIni["GDT"]["gdtexportverzeichnis"] = de.lineEditExport.text()
            self.configIni["GDT"]["kuerzelinrgdt"] = de.lineEditInrGdtKuerzel.text()
            self.configIni["GDT"]["kuerzelpraxisedv"] = de.lineEditPraxisEdvKuerzel.text()
            self.configIni["GDT"]["zeichensatz"] = str(de.aktuelleZeichensatznummer + 1)
            with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                self.configIni.write(configfile)
            if neustartfrage:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von InrGDT", "Damit die Einstellungsänderungen wirksam werden, sollte InrGDT neu gestartet werden.\nSoll InrGDT jetzt neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    os.execl(sys.executable, __file__, *sys.argv)

    def einstellungenBenutzer(self, checked, neustartfrage = False):
        de = dialogEinstellungenBenutzer.EinstellungenBenutzer(self.configPath)
        if de.exec() == 1:
            namen = []
            kuerzel = []
            for i in range(5):
                if de.lineEditNamen[i].text() != "":
                    namen.append(de.lineEditNamen[i].text())
                    kuerzel.append(de.lineEditKuerzel[i].text())
            self.configIni["Benutzer"]["namen"] = "::".join(namen)
            self.configIni["Benutzer"]["kuerzel"] = "::".join(kuerzel)
            with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                self.configIni.write(configfile)
            if neustartfrage:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von InrGDT", "Damit die Einstellungsänderungen wirksam werden, sollte InrGDT neu gestartet werden.\nSoll InrGDT jetzt neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    os.execl(sys.executable, __file__, *sys.argv)

    def einstellungenDosierung(self, checked, neustartfrage = False):
        de = dialogEinstellungenDosierung.EinstellungenDosierung(self.configPath)
        if de.exec() == 1:
            self.dosen.clear()
            self.dosen.append("0")
            for zeile in range(3):
                for spalte in range(4):
                    if de.checkBoxDosierungen[zeile][spalte].isChecked():
                        self.dosen.append(de.dosierungen[zeile][spalte])
            self.configIni["Marcumar"]["dosen"] = "::".join(self.dosen)
            with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                self.configIni.write(configfile)
            if neustartfrage:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von InrGDT", "Damit die Einstellungsänderungen wirksam werden, sollte InrGDT neu gestartet werden.\nSoll InrGDT jetzt neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    os.execl(sys.executable, __file__, *sys.argv)

    def einstellungenLanrLizenzschluessel(self, checked, neustartfrage = False):
        de = dialogEinstellungenLanrLizenzschluessel.EinstellungenProgrammerweiterungen(self.configPath)
        if de.exec() == 1:
            self.configIni["Erweiterungen"]["lanr"] = de.lineEditLanr.text()
            self.configIni["Erweiterungen"]["lizenzschluessel"] = gdttoolsL.GdtToolsLizenzschluessel.krypt(de.lineEditLizenzschluessel.text())
            with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                self.configIni.write(configfile)
            if neustartfrage:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von InrGDT", "Damit die Einstellungsänderungen wirksam werden, sollte InrGDT neu gestartet werden.\nSoll InrGDT jetzt neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    os.execl(sys.executable, __file__, *sys.argv)

    def einstellungenImportExport(self):
        de = dialogEinstellungenImportExport.EinstellungenImportExport(self.configPath)
        if de.exec() == 1:
            pass
    
    def inrgdtWiki(self, link):
        QDesktopServices.openUrl("https://www.github.com/retconx/inrgdt/wiki")

    def lineEditInrEdited(self):
        if re.match(reInr, self.lineEditInr.text()) == None:
            self.lineEditInr.setStyleSheet("background:rgb(255,200,200)")
            self.pushButtonSenden.setEnabled(False)
        else:
            self.lineEditInr.setStyleSheet("background:rgb(255,255,255)")
            self.pushButtonSenden.setEnabled(True)

    def checkBoxImmerClicked(self):
        if self.checkBoxImmer.isChecked():
            self.checkBoxExtern.setChecked(True)

    def pushButtonDosisClicked(self, dosiszeile, wochentagspalte):
        for zeile in range(len(self.dosen)):
            if zeile != dosiszeile:
                self.pushButtonDosen[zeile][wochentagspalte].setChecked(False)

    def pushButtonAlleClicked(self, checked, dosiszeile):
        for zeile in range(len(self.dosen)):
            for wt in range(7):
                self.pushButtonDosen[zeile][wt].setChecked(False)
        for wt in range(7):
            for pushButton in self.pushButtonDosen[dosiszeile]:
                pushButton.setChecked(True)

    def dateEditUntersuchungsdatumChanged(self, datum):
        self.untersuchungsdatum = datum
                
    def pushButtonSendenClicked(self):
        logger.logger.info("Daten senden geklickt")
        if self.patId != "" and re.match(reInr, self.lineEditInr.text()):
            # GDT-Datei erzeugen
            sh = gdt.SatzHeader(gdt.Satzart.DATEN_EINER_UNTERSUCHUNG_UEBERMITTELN_6310, self.configIni["GDT"]["idpraxisedv"], self.configIni["GDT"]["idinrgdt"], self.zeichensatz, "2.10", "Fabian Treusch - GDT-Tools", "InrGDT", self.version, self.patId)
            gd = gdt.GdtDatei()
            logger.logger.info("GdtDatei-Instanz erzeugt")
            gd.erzeugeGdtDatei(sh.getSatzheader())
            logger.logger.info("Satzheader 6310 erzeugt")
            self.datum = "{:>02}".format(str(self.dateEditUntersuchungsdatum.date().day())) + "{:>02}".format(str(self.dateEditUntersuchungsdatum.date().month())) + str(self.dateEditUntersuchungsdatum.date().year())
            jetzt = QTime().currentTime()
            uhrzeit = "{:>02}".format(str(jetzt.hour())) + "{:>02}".format(str(jetzt.minute())) + str(jetzt.second())
            logger.logger.info("Untersuchungsdatum/ -uhrzeit festgelegt")
            gd.addZeile("6200", self.datum)
            gd.addZeile("6201", uhrzeit)
            gd.addZeile("8402", "ALLG00")

            # Befund
            befundzeile = "{:.1f}".format(float(self.lineEditInr.text().replace(",", "."))).replace(".", ",")
            befundzeile += "    "
            wochendosis = 0
            wochendosen = []
            for wt in range(7):
                for dosis in range(len(self.dosen)):
                    if self.pushButtonDosen[dosis][wt].isChecked():
                        wochendosen.append("{:.2f}".format(float(self.dosen[dosis])).replace(".", ","))
                        wochendosis += float(self.dosen[dosis])
            befundzeile += "  -  ".join(wochendosen)
            externBenutzer = self.benutzerkuerzelListe[self.aktuelleBenuztzernummer]
            if self.checkBoxExtern.isChecked():
                externBenutzer = "extern/" + externBenutzer
            befundzeile += "  WD: " + "{:.2f}".format(wochendosis).replace(".", ",") + " (" + externBenutzer + ")"
            gd.addZeile("6220", befundzeile)

            # Benutzer
            gd.addZeile("6227", self.textEditBemerkungen.toPlainText())
            logger.logger.info("Befund und Kommentar erzeugt")
                
            # GDT-Datei exportieren
            if not gd.speichern(self.gdtExportVerzeichnis + "/" + self.kuerzelpraxisedv + self.kuerzelinrgdt + ".gdt", self.zeichensatz):
                logger.logger.error("Fehler bei GDT-Dateiexport nach " + self.gdtExportVerzeichnis + "/" + self.kuerzelpraxisedv + self.kuerzelinrgdt + ".gdt")
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InrGDT", "GDT-Export nicht möglich.\nBitte überprüfen Sie die Angabe des Exportverzeichnisses.", QMessageBox.StandardButton.Ok)
                mb.exec()
            self.configIni["Allgemein"]["immerextern"] = str(self.checkBoxImmer.isChecked())
            try:
                with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                    self.configIni.write(configfile)
                    logger.logger.info("Allgemein/immerextern in config.ini auf " + str(self.checkBoxImmer.isChecked()) + " gesetzt")
            except:
                logger.logger.error("Fehler beim Speichern von Allgemein/immerextern in config.ini")
            sys.exit()
        elif self.patId != "":
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InrGDT", "INR-Eingabe unzulässig", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditInr.selectAll()
            self.lineEditInr.setFocus()
        else:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InrGDT", "GDT-Export nicht möglich, da kein Patient von PVS übermittelt.", QMessageBox.StandardButton.Ok)
            mb.exec()
    
    def gdtToolsLinkGeklickt(self, link):
        QDesktopServices.openUrl(link)
    
app = QApplication(sys.argv)
qt = QTranslator()
filename = "qtbase_de"
directory = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
qt.load(filename, directory)
app.installTranslator(qt)
app.setWindowIcon(QIcon(os.path.join(basedir, "icons/program.png")))
window = MainWindow()
window.show()

app.exec()