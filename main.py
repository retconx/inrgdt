import sys, configparser, os, datetime, shutil, logger, re, atexit, subprocess
import gdt, gdtzeile, farbe
## Nur mit Lizenz
import gdttoolsL
## /Nur mit Lizenz
import dialogUeberInrGdt, dialogEinstellungenAllgemein, dialogEinstellungenGdt, dialogEinstellungenBenutzer, dialogEinstellungenLanrLizenzschluessel, dialogEinstellungenImportExport, dialogEinstellungenDosierung, inrPdf, dialogEula
from PySide6.QtCore import Qt, QDate, QTime, QTranslator, QLibraryInfo
from PySide6.QtGui import QFont, QAction, QIcon, QDesktopServices, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
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
    QTextEdit,
    QGroupBox
)
import requests

basedir = os.path.dirname(__file__)
reInr = r"^\d([.,]\d)*\d?$"

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
        self.maxBenutzerzahl = 20
        self.standardpalette = self.palette()

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

        ## Nachträglich hinzufefügte Options
        # 1.1.0
        self.archivierungspfad = ""
        if self.configIni.has_option("Allgemein", "archivierungspfad"):
            self.archivierungspfad = self.configIni["Allgemein"]["archivierungspfad"]
        self.vorherigedokuladen = False
        if self.configIni.has_option("Allgemein", "vorherigedokuladen"):
            self.vorherigedokuladen = self.configIni["Allgemein"]["vorherigedokuladen"] == "True"
        # 1.2.0
        self.einrichtungsname = ""
        if self.configIni.has_option("Allgemein", "einrichtungsname"):
            self.einrichtungsname = self.configIni["Allgemein"]["einrichtungsname"]
        # 1.2.1
        self.immerpdf = False
        if self.configIni.has_option("Allgemein", "immerpdf"):
            self.immerpdf = self.configIni["Allgemein"]["immerpdf"] == "True"
        # 1.2.2
        self.eulagelesen = False
        if self.configIni.has_option("Allgemein", "eulagelesen"):
            self.eulagelesen = self.configIni["Allgemein"]["eulagelesen"] == "True"
        # 1.3.0
        self.wochentageAnzeigen = False
        self.lzVor = "0"
        self.lzNach = "0"
        if self.configIni.has_option("Allgemein", "wochentageanzeigen"):
            self.wochentageAnzeigen = self.configIni["Allgemein"]["wochentageanzeigen"] == "True"
            self.lzVor = self.configIni["Allgemein"]["lzvor"]
            self.lzNach = self.configIni["Allgemein"]["lznach"]
        # 1.4.0
        self.autoupdate = True
        self.updaterpfad = ""
        if self.configIni.has_option("Allgemein", "autoupdate"):
            self.autoupdate = self.configIni["Allgemein"]["autoupdate"] == "True"
        if self.configIni.has_option("Allgemein", "updaterpfad"):
            self.updaterpfad = self.configIni["Allgemein"]["updaterpfad"]
        # 1.5.0
        self.bemerkungenAufPdf = False
        if self.configIni.has_option("Allgemein", "bemerkungenaufpdf"):
            self.bemerkungenAufPdf = self.configIni["Allgemein"]["bemerkungenaufpdf"] == "True"
        # 1.9.0
        self.halbstatt05 = False
        if self.configIni.has_option("Allgemein", "halbstatt05"):
            self.halbstatt05 = self.configIni["Allgemein"]["halbstatt05"] == "True"
        ## /Nachträglich hinzufefügte Options

        z = self.configIni["GDT"]["zeichensatz"]
        self.zeichensatz = gdt.GdtZeichensatz.IBM_CP437
        if z == "1":
            self.zeichensatz = gdt.GdtZeichensatz.BIT_7
        elif z == "3":
            self.zeichensatz = gdt.GdtZeichensatz.ANSI_CP1252
        self.lanr = self.configIni["Erweiterungen"]["lanr"]
        self.lizenzschluessel = self.configIni["Erweiterungen"]["lizenzschluessel"]

        ## Nur mit Lizenz
        # Prüfen, ob Lizenzschlüssel unverschlüsselt
        if len(self.lizenzschluessel) == 29:
            logger.logger.info("Lizenzschlüssel unverschlüsselt")
            self.configIni["Erweiterungen"]["lizenzschluessel"] = gdttoolsL.GdtToolsLizenzschluessel.krypt(self.lizenzschluessel)
            with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                    self.configIni.write(configfile)
        else:
            self.lizenzschluessel = gdttoolsL.GdtToolsLizenzschluessel.dekrypt(self.lizenzschluessel)
        ## /Nur mit Lizenz

        # Prüfen, ob EULA gelesen
        if not self.eulagelesen:
            de = dialogEula.Eula()
            de.exec()
            if de.checkBoxZustimmung.isChecked():
                self.eulagelesen = True
                self.configIni["Allgemein"]["eulagelesen"] = "True"
                with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                    self.configIni.write(configfile)
                logger.logger.info("EULA zugestimmt")
            else:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InrGDT", "Ohne Zustimmung der Lizenzvereinbarung kann InrGDT nicht gestartet werden.", QMessageBox.StandardButton.Ok)
                mb.exec()
                sys.exit()

        # Grundeinstellungen bei erstem Start
        if ersterStart:
            logger.logger.info("Erster Start")
            mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von InrGDT", "Vermutlich starten Sie InrGDT das erste Mal auf diesem PC.\nMöchten Sie jetzt die Grundeinstellungen vornehmen?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.setDefaultButton(QMessageBox.StandardButton.Yes)
            if mb.exec() == QMessageBox.StandardButton.Yes:
                ## Nur mit Lizenz
                self.einstellungenLanrLizenzschluessel(False, False)
                ## /Nur mit Lizenz
                self.einstellungenGdt(False, False)
                self.einstellungenBenutzer(False, False)
                self.einstellungenDosierung(False, False)
                self.einstellungenAllgemein(False, False)
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InrGDT", "Die Ersteinrichtung ist abgeschlossen. InrGDT wird beendet.", QMessageBox.StandardButton.Ok)
                mb.exec()
                sys.exit()

        # Version vergleichen und gegebenenfalls aktualisieren
        configIniBase = configparser.ConfigParser()
        try:
            configIniBase.read(os.path.join(basedir, "config.ini"))
            if versionVeraltet(self.version, configIniBase["Allgemein"]["version"]):
                # Version aktualisieren
                self.configIni["Allgemein"]["version"] = configIniBase["Allgemein"]["version"]
                self.configIni["Allgemein"]["releasedatum"] = configIniBase["Allgemein"]["releasedatum"] 
                ## config.ini aktualisieren
                # 1.0.2 -> 1.1.0: ["Allgemein"]["archivierungspfad"] und ["Allgemein"]["vorherigedokuladen"] hinzufügen
                if not self.configIni.has_option("Allgemein", "archivierungspfad"):
                    self.configIni["Allgemein"]["archivierungspfad"] = ""
                if not self.configIni.has_option("Allgemein", "vorherigedokuladen"):
                    self.configIni["Allgemein"]["vorherigedokuladen"] = "False"
                # 1.1.6 -> 1.2.0 ["Allgemein"]["einrichtungsname"] hinzufügen
                if not self.configIni.has_option("Allgemein", "einrichtungsname"):
                    self.configIni["Allgemein"]["einrichtungsname"] = ""
                # 1.2.0 -> 1.2.1 ["Allgemein"]["immerpdf"] hinzufügen
                if not self.configIni.has_option("Allgemein", "immerpdf"):
                    self.configIni["Allgemein"]["immerpdf"] = "False"
                # 1.2.2 -> 1.3.0 ["Allgemein"]["wochentageanzeigen"], ["Allgemein"]["lzvor"] und ["Allgemein"]["lznach"] hinzufügen
                if not self.configIni.has_option("Allgemein", "wochentageanzeigen"):
                    self.configIni["Allgemein"]["wochentageanzeigen"] = "False"
                    self.configIni["Allgemein"]["lzvor"] = self.lzVor
                    self.configIni["Allgemein"]["lznach"] = self.lzNach
                # 1.3.7 -> 1.4.0 ["Allgemein"]["autoupdate"] und ["Allgemein"]["updaterpfad"] hinzufügen
                if not self.configIni.has_option("Allgemein", "autoupdate"):
                    self.configIni["Allgemein"]["autoupdate"] = "True"
                if not self.configIni.has_option("Allgemein", "updaterpfad"):
                    self.configIni["Allgemein"]["updaterpfad"] = ""
                # 1.5.0 -> 1.6.0 ["Allgemein"]["bemerkungenaufpdf"] hinzufügen
                if not self.configIni.has_option("Allgemein", "bemerkungenaufpdf"):
                    self.configIni["Allgemein"]["bemerkungenaufpdf"] = "False"
                # 1.8.2 -> 1.9.0 ["Allgemein"]["halbstatt05"] hinzufügen
                if not self.configIni.has_option("Allgemein", "halbstatt05"):
                    self.configIni["Allgemein"]["halbstatt05"] = "False"
                ## /config.ini aktualisieren

                with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                    self.configIni.write(configfile)
                self.version = self.configIni["Allgemein"]["version"]
                logger.logger.info("Version auf " + self.version + " aktualisiert")
                # Prüfen, ob EULA gelesen
                de = dialogEula.Eula(self.version)
                de.exec()
                self.eulagelesen = de.checkBoxZustimmung.isChecked()
                self.configIni["Allgemein"]["eulagelesen"] = str(self.eulagelesen)
                with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                    self.configIni.write(configfile)
                if self.eulagelesen:
                    logger.logger.info("EULA zugestimmt")
                else:
                    logger.logger.info("EULA nicht zugestimmt")
                    mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InrGDT", "Ohne  Zustimmung zur Lizenzvereinbarung kann InrGDT nicht gestartet werden.", QMessageBox.StandardButton.Ok)
                    mb.exec()
                    sys.exit()
        except SystemExit:
            sys.exit()
        except:
            logger.logger.error("Problem beim Aktualisieren auf Version " + configIniBase["Allgemein"]["version"])
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InrGDT", "Problem beim Aktualisieren auf Version " + configIniBase["Allgemein"]["version"], QMessageBox.StandardButton.Ok)
            mb.exec()

        self.addOnsFreigeschaltet = True

        ## Nur mit Lizenz
        # Pseudo-Lizenz?
        self.pseudoLizenzId = ""
        rePatId = r"^patid\d+$"
        for arg in sys.argv:
            if re.match(rePatId, arg) != None:
                logger.logger.info("Pseudo-Lizenz mit id " + arg[5:])
                self.pseudoLizenzId = arg[5:]

        # Add-Ons freigeschaltet?
        self.addOnsFreigeschaltet = gdttoolsL.GdtToolsLizenzschluessel.lizenzErteilt(self.lizenzschluessel, self.lanr, gdttoolsL.SoftwareId.INRGDT) or gdttoolsL.GdtToolsLizenzschluessel.lizenzErteilt(self.lizenzschluessel, self.lanr, gdttoolsL.SoftwareId.INRGDTPSEUDO) and self.pseudoLizenzId != ""
        if self.lizenzschluessel != "" and gdttoolsL.GdtToolsLizenzschluessel.getSoftwareId(self.lizenzschluessel) == gdttoolsL.SoftwareId.INRGDTPSEUDO and self.pseudoLizenzId == "":
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InrGDT", "Bei Verwendung einer Pseudolizenz muss InrGDT mit einer Patienten-Id als Startargument im Format \"patid<Pat.-Id>\" ausgeführt werden.", QMessageBox.StandardButton.Ok)
            mb.exec() 
        ## /Nur mit Lizenz
        
        jahr = datetime.datetime.now().year
        copyrightJahre = "2024"
        if jahr > 2024:
            copyrightJahre = "2024-" + str(jahr)
        self.setWindowTitle("InrGDT V" + self.version + " (\u00a9 Fabian Treusch - GDT-Tools " + copyrightJahre + ")")
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)
        self.fontBoldGross = QFont()
        self.fontBoldGross.setBold(True)
        self.fontBoldGross.setPixelSize(16)
        self.fontGross = QFont()
        self.fontGross.setBold(False)
        self.fontGross.setPixelSize(16)
        self.fontGrossStrikeOut = QFont()
        self.fontGrossStrikeOut.setPixelSize(16)
        self.fontGrossStrikeOut.setStrikeOut(True)

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
            gd.laden(os.path.join(self.gdtImportVerzeichnis, self.kuerzelinrgdt + self.kuerzelpraxisedv + ".gdt"), self.zeichensatz, senderId)
            self.patId = str(gd.getInhalt("3000"))
            self.name = str(gd.getInhalt("3102")) + " " + str(gd.getInhalt("3101"))
            logger.logger.info("PatientIn " + self.name + " (ID: " + self.patId + ") geladen")
            ## Nur mit Lizenz
            if self.pseudoLizenzId != "":
                self.patId = self.pseudoLizenzId
                logger.logger.info("PatId wegen Pseudolizenz auf " + self.pseudoLizenzId + " gesetzt")
            ## /Nur mit Lizenz
            self.geburtsdatum = str(gd.getInhalt("3103"))[0:2] + "." + str(gd.getInhalt("3103"))[2:4] + "." + str(gd.getInhalt("3103"))[4:8]
        except (IOError, gdtzeile.GdtFehlerException) as e:
            logger.logger.warning("Fehler beim Laden der GDT-Datei: " + str(e))
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InrGDT", "Fehler beim Laden der GDT-Datei:\n" + str(e) + "\n\nDieser Fehler hat in der Regel eine der folgenden Ursachen:\n- Die im PVS und in InrGDT konfigurierten GDT-Austauschverzeichnisse stimmen nicht überein.\n- InrGDT wurde nicht aus dem PVS heraus gestartet, so dass keine vom PVS erzeugte GDT-Datei gefunden werden konnte.\n\nSoll InrGDT dennoch geöffnet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
            mb.button(QMessageBox.StandardButton.No).setText("Nein")
            mb.setDefaultButton(QMessageBox.StandardButton.No)
            mbErg = mb.exec()
        if mbErg == QMessageBox.StandardButton.Yes:
            self.widget = QWidget()
            self.widget.installEventFilter(self)

            # Formularaufbau
            self.wochentage = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
            self.wochentageLang = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
            mainLayoutV = QVBoxLayout()
            kopfLayoutG = QGridLayout()
            inrLayoutH = QHBoxLayout()
            self.labelPseudolizenz = QLabel("+++ Pseudolizenz für Test-/ Präsentationszwecke +++")
            self.labelPseudolizenz.setStyleSheet("color:rgb(255,50,50)")
            labelName = QLabel("Name: " + self.name)
            labelName.setFont(self.fontGross)
            labelPatId = QLabel("ID: " + self.patId)
            labelPatId.setFont(self.fontGross)
            labelGeburtsdatum = QLabel("Geburtsdatum: " + self.geburtsdatum)
            labelGeburtsdatum.setFont(self.fontGross)
            labelDokumentationVom = QLabel("Zuletzt dokumentiert:")
            labelDokumentationVom.setFont(self.fontGross)
            self.labelArchivdatum = QLabel("--.--.----")
            self.labelArchivdatum.setFont(self.fontGross)
            self.pushButtonArchivierungLaden = QPushButton("\U0001f504")
            self.pushButtonArchivierungLaden.setFont(self.fontGross)
            self.pushButtonArchivierungLaden.setEnabled(False)
            self.pushButtonArchivierungLaden.clicked.connect(self.pushButtonArchivierungLadenClicked)
            kopfLayoutG.addWidget(labelName, 0, 0)
            kopfLayoutG.addWidget(labelPatId, 0, 1)
            kopfLayoutG.addWidget(labelGeburtsdatum, 0, 2)
            kopfLayoutG.addWidget(labelDokumentationVom, 1, 0)
            kopfLayoutG.addWidget(self.labelArchivdatum, 1, 1)
            kopfLayoutG.addWidget(self.pushButtonArchivierungLaden, 1, 2, alignment=Qt.AlignmentFlag.AlignLeft)
            # GroupBox INR-Messwert
            groupBoxInrMesswert = QGroupBox("INR-Messwert")
            groupBoxInrMesswert.setFont(self.fontBoldGross)
            groupBoxInrMesswertLayout = QHBoxLayout()
            self.lineEditInr = QLineEdit()
            self.lineEditInr.setFont(self.fontGross)
            self.lineEditInr.textEdited.connect(self.lineEditInrEdited)
            self.checkBoxExtern = QCheckBox("Extern bestimmter Wert")
            self.checkBoxExtern.setFont(self.fontGross)
            self.checkBoxExtern.setChecked(self.immerextern)
            groupBoxInrMesswertLayout.addWidget(self.lineEditInr)
            groupBoxInrMesswertLayout.addWidget(self.checkBoxExtern)
            groupBoxInrMesswert.setLayout(groupBoxInrMesswertLayout)
            # GroupBox INR-Zielbereich
            groupBoxInrZielbereich = QGroupBox("INR-Zielbereich")
            groupBoxInrZielbereich.setFont(self.fontBoldGross)
            groupBoxInrZielbereichLayout = QHBoxLayout()
            self.lineEditInrzielVon = QLineEdit()
            self.lineEditInrzielVon.setFont(self.fontGross)
            self.lineEditInrzielVon.textEdited.connect(lambda text="", lineEdit=self.lineEditInrzielVon: self.lineEditInrzielEdited(text, lineEdit))
            labelBis = QLabel("-")
            labelBis.setFont(self.fontBoldGross)
            self.lineEditInrzielBis = QLineEdit()
            self.lineEditInrzielBis.setFont(self.fontGross)
            self.lineEditInrzielBis.textEdited.connect(lambda text="", lineEdit=self.lineEditInrzielBis: self.lineEditInrzielEdited(text, lineEdit))
            groupBoxInrZielbereich.setLayout(groupBoxInrZielbereichLayout)
            groupBoxInrZielbereichLayout.addWidget(self.lineEditInrzielVon)
            groupBoxInrZielbereichLayout.addWidget(labelBis)
            groupBoxInrZielbereichLayout.addWidget(self.lineEditInrzielBis)
            inrLayoutH.addWidget(groupBoxInrMesswert)
            inrLayoutH.addWidget(groupBoxInrZielbereich)

            inrLayoutG = QGridLayout()
            labelWochentage = []
            self.pushButtonDosen = []
            pushButtonDosenTemp = []
            self.pushButtonDosenAlle = []
            for wt in range(7):
                labelWochentage.append(QLabel(self.wochentage[wt]))
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
                    pushButtonDosenTemp[wt].clicked.connect(lambda checked=False, dosiszeile=dosis, wochentagspalte=wt: self.pushButtonDosisClicked(checked, dosiszeile, wochentagspalte))
                    inrLayoutG.addWidget(pushButtonDosenTemp[wt], dosis + 1, wt)
                self.pushButtonDosenAlle.append(QPushButton(buttonText))
                self.pushButtonDosenAlle[dosis].setFont(self.fontBoldGross)
                self.pushButtonDosenAlle[dosis].clicked.connect(lambda checked=False, dosiszeile=dosis: self.pushButtonAlleClicked(checked, dosiszeile))
                inrLayoutG.addWidget(self.pushButtonDosenAlle[dosis])
                self.pushButtonDosen.append(pushButtonDosenTemp.copy())

            # Folgewoche
            groupBoxFolgewoche = QGroupBox("Folgewoche")
            groupBoxFolgewoche.setFont(self.fontGross)
            groupBoxFolgewocheLayoutG = QGridLayout()
            self.pushButtonFolgewocheAktivieren = QPushButton("Aktivieren")
            self.pushButtonFolgewocheAktivieren.setCheckable(True)
            self.pushButtonFolgewocheAktivieren.setAutoFillBackground(True)
            self.pushButtonFolgewocheAktivieren.clicked.connect(self.pushButtonFolgewocheAktivierenClicked)
            groupBoxFolgewocheLayoutG.addWidget(self.pushButtonFolgewocheAktivieren, 0, 0, 1, 8)
            self.comboBoxFolgewoche = []
            for wt in range(7):
                self.comboBoxFolgewoche.append(QComboBox())
                self.comboBoxFolgewoche[wt].setFont(self.fontGross)
                self.comboBoxFolgewoche[wt].setEnabled(False)
                self.comboBoxFolgewoche[wt].setFixedHeight(30)
                for dosis in self.dosen:
                    if dosis == "0":
                        self.comboBoxFolgewoche[wt].addItem("0")
                    else:
                        self.comboBoxFolgewoche[wt].addItem(dosis.replace(".25", "\u00bc").replace(".5", "\u00bd").replace(".75", "\u00be").replace(".", "").replace("0", ""))
                groupBoxFolgewocheLayoutG.addWidget(self.comboBoxFolgewoche[wt], len(self.dosen) + 2, wt)
            self.pushButtonFolgewocheZuruecksetzen = QPushButton("\U0001f504")
            self.pushButtonFolgewocheZuruecksetzen.setToolTip("Zurücksetzen")
            self.pushButtonFolgewocheZuruecksetzen.setFont(self.fontGross)
            self.pushButtonFolgewocheZuruecksetzen.setEnabled(False)
            self.pushButtonFolgewocheZuruecksetzen.clicked.connect(self.pushButtonFolgewocheZuruecksetzenClicked)
            groupBoxFolgewocheLayoutG.addWidget(self.pushButtonFolgewocheZuruecksetzen, len(self.dosen) + 2, 7)
            groupBoxFolgewoche.setLayout(groupBoxFolgewocheLayoutG)
            
            # Bemerkungsfeld
            bemerkungenLayoutH = QHBoxLayout()
            labelBemerkungen = QLabel("Bemerkungen:")
            labelBemerkungen.setFont(self.fontGross)
            self.textEditBemerkungen = QTextEdit()
            self.textEditBemerkungen.setFixedHeight(50)
            self.textEditBemerkungen.setFont(self.fontGross)
            self.checkBoxBemerkungenAufPdf = QCheckBox("Bemerkungen auf PDF-Plan übernehmen")
            self.checkBoxBemerkungenAufPdf.setFont(self.fontGross)
            self.checkBoxBemerkungenAufPdf.setEnabled(self.immerpdf)
            self.checkBoxBemerkungenAufPdf.setChecked(self.bemerkungenAufPdf)
            self.checkBoxBemerkungenAufPdf.clicked.connect(self.checkBoxBemerkungenAufPdfClicked)
            bemerkungenLayoutH.addWidget(labelBemerkungen)
            bemerkungenLayoutH.addWidget(self.checkBoxBemerkungenAufPdf)

            # Untersuchungsdatum und Benutzer
            untdatBenutzerLayoutG = QGridLayout()
            labelUntersuchungsdatum = QLabel("Untersucht am:")
            labelUntersuchungsdatum.setFont(self.fontGross)
            self.untersuchungsdatum = QDate().currentDate()
            self.dateEditUntersuchungsdatum = QDateEdit()
            self.dateEditUntersuchungsdatum.setFont(self.fontGross)
            self.dateEditUntersuchungsdatum.setDate(self.untersuchungsdatum)
            self.dateEditUntersuchungsdatum.setDisplayFormat("dd.MM.yyyy")
            self.dateEditUntersuchungsdatum.setCalendarPopup(True)
            self.dateEditUntersuchungsdatum.userDateChanged.connect(self.dateEditUntersuchungsdatumChanged)
            untdatBenutzerLayoutG.addWidget(labelUntersuchungsdatum, 0, 0)
            untdatBenutzerLayoutG.addWidget(self.dateEditUntersuchungsdatum, 1, 0)
            labelBenutzer = QLabel("Dokumentiert von:")
            labelBenutzer.setFont(self.fontGross)
            self.comboBoxBenutzer = QComboBox()
            self.comboBoxBenutzer.setFont(self.fontGross)
            self.comboBoxBenutzer.addItems(self.benutzernamenListe)
            self.comboBoxBenutzer.currentIndexChanged.connect(self.comboBoxBenutzerIndexChanged)
            aktBenNum = 0
            if self.aktuelleBenuztzernummer < len(self.benutzernamenListe):
                aktBenNum = self.aktuelleBenuztzernummer
            self.comboBoxBenutzer.setCurrentIndex(aktBenNum)
            untdatBenutzerLayoutG.addWidget(labelBenutzer, 0, 1)
            untdatBenutzerLayoutG.addWidget(self.comboBoxBenutzer, 1, 1)
            labelNaechsteKontrolle = QLabel("Nächste Kontrolle:")
            labelNaechsteKontrolle.setFont(self.fontGross)
            self.naechsteKontrolle = QDate().currentDate()
            self.dateEditNaechsteKontrolle = QDateEdit()
            self.dateEditNaechsteKontrolle.setFont(self.fontGross)
            self.dateEditNaechsteKontrolle.setDate(self.naechsteKontrolle)
            self.dateEditNaechsteKontrolle.setDisplayFormat("dd.MM.yyyy")
            self.dateEditNaechsteKontrolle.setCalendarPopup(True)
            self.dateEditNaechsteKontrolle.setEnabled(self.immerpdf)
            self.dateEditNaechsteKontrolle.userDateChanged.connect(self.dateEditNaechsteKontrolleChanged)
            untdatBenutzerLayoutG.addWidget(labelNaechsteKontrolle, 0, 2, 1, 2)
            untdatBenutzerLayoutG.addWidget(self.dateEditNaechsteKontrolle, 1, 2)
            self.checkBoxPdfErstellen = QCheckBox("PDF-Plan erstellen")
            self.checkBoxPdfErstellen.setFont(self.fontGross)
            self.checkBoxPdfErstellen.setChecked(self.immerpdf)
            self.checkBoxPdfErstellen.clicked.connect(self.checkBoxPdfErstellenClicked)
            untdatBenutzerLayoutG.addWidget(self.checkBoxPdfErstellen, 1, 3)

            # Senden-Button
            self.pushButtonSenden = QPushButton("Daten senden")
            self.pushButtonSenden.setFont(self.fontBoldGross)
            self.pushButtonSenden.setAutoFillBackground(True)
            self.pushButtonSenden.setFixedHeight(60)
            self.pushButtonSenden.setEnabled(False)
            self.pushButtonSenden.clicked.connect(self.pushButtonSendenClicked)

            ## Nur mit Lizenz
            if self.addOnsFreigeschaltet and gdttoolsL.GdtToolsLizenzschluessel.getSoftwareId(self.lizenzschluessel) == gdttoolsL.SoftwareId.INRGDTPSEUDO:
                mainLayoutV.addWidget(self.labelPseudolizenz, alignment=Qt.AlignmentFlag.AlignCenter)
            ## /Nur mit Lizenz
            mainLayoutV.addLayout(kopfLayoutG)
            mainLayoutV.addSpacing(10)
            mainLayoutV.addLayout(inrLayoutH)
            mainLayoutV.addLayout(inrLayoutG)
            mainLayoutV.addWidget(groupBoxFolgewoche)
            mainLayoutV.addLayout(bemerkungenLayoutH)
            mainLayoutV.addWidget(self.textEditBemerkungen)
            mainLayoutV.addLayout(untdatBenutzerLayoutG)
            mainLayoutV.addWidget(self.pushButtonSenden)
            mainLayoutV.addSpacing(10)
            ## Nur mit Lizenz
            if self.addOnsFreigeschaltet:
                gueltigeLizenztage = gdttoolsL.GdtToolsLizenzschluessel.nochTageGueltig(self.lizenzschluessel)
                if gueltigeLizenztage  > 0 and gueltigeLizenztage <= 30:
                    labelLizenzLaeuftAus = QLabel("Die genutzte Lizenz ist noch " + str(gueltigeLizenztage) + " Tage gültig.")
                    labelLizenzLaeuftAus.setStyleSheet("color:rgb(255,50,50)")
                    mainLayoutV.addWidget(labelLizenzLaeuftAus, alignment=Qt.AlignmentFlag.AlignCenter)
            else:
                self.pushButtonSenden.setEnabled(False)
                self.pushButtonSenden.setText("Keine gültige Lizenz")
            ## /Nur mit Lizenz
            self.widget.setLayout(mainLayoutV)
            self.setCentralWidget(self.widget)
            self.lineEditInr.setFocus()

            # Menü
            menubar = self.menuBar()
            anwendungMenu = menubar.addMenu("")
            aboutAction = QAction(self)
            aboutAction.setMenuRole(QAction.MenuRole.AboutRole)
            aboutAction.triggered.connect(self.ueberInrGdt) 
            updateAction = QAction("Auf Update prüfen", self)
            updateAction.setMenuRole(QAction.MenuRole.ApplicationSpecificRole)
            updateAction.triggered.connect(self.updatePruefung) 
            hilfeAutoUpdateAction = QAction("Automatisch auf Update prüfen", self)
            hilfeAutoUpdateAction.setCheckable(True)
            hilfeAutoUpdateAction.setChecked(self.autoupdate)
            hilfeAutoUpdateAction.triggered.connect(self.autoUpdatePruefung)
            einstellungenMenu = menubar.addMenu("Einstellungen")
            einstellungenAllgemeinAction = QAction("Allgemeine Einstellungen", self)
            einstellungenAllgemeinAction.triggered.connect(lambda checked = False, neustartfrage = True: self.einstellungenAllgemein(checked, neustartfrage))
            einstellungenGdtAction = QAction("GDT-Einstellungen", self)
            einstellungenGdtAction.triggered.connect(lambda checked = False, neustartfrage = True: self.einstellungenGdt(checked, neustartfrage))
            einstellungenBenutzerAction = QAction("BenutzerInnen verwalten", self)
            einstellungenBenutzerAction.triggered.connect(lambda checked = False, neustartfrage = True: self.einstellungenBenutzer(checked, neustartfrage)) 
            einstellungenDosierungAction = QAction("Dosierungen verwalten", self)
            einstellungenDosierungAction.triggered.connect(lambda checked = False, neustartfrage = True: self.einstellungenDosierung(checked, neustartfrage)) 
            ## Nur mit Lizenz
            einstellungenErweiterungenAction = QAction("LANR/Lizenzschlüssel", self)
            einstellungenErweiterungenAction.triggered.connect(lambda checked = False, neustartfrage = True: self.einstellungenLanrLizenzschluessel(checked, neustartfrage)) 
            einstellungenImportExportAction = QAction("Im- /Exportieren", self)
            einstellungenImportExportAction.triggered.connect(self.einstellungenImportExport) 
            einstellungenImportExportAction.setMenuRole(QAction.MenuRole.NoRole)
            ## /Nur mit Lizenz
            hilfeMenu = menubar.addMenu("Hilfe")
            hilfeWikiAction = QAction("InrGDT Wiki", self)
            hilfeWikiAction.triggered.connect(self.inrgdtWiki)
            hilfeUpdateAction = QAction("Auf Update prüfen", self)
            hilfeUpdateAction.triggered.connect(self.updatePruefung)
            hilfeUeberAction = QAction("Über InrGDT", self)
            hilfeUeberAction.setMenuRole(QAction.MenuRole.NoRole)
            hilfeUeberAction.triggered.connect(self.ueberInrGdt)
            hilfeEulaAction = QAction("Lizenzvereinbarung (EULA)", self)
            hilfeEulaAction.triggered.connect(self.eula) 
            hilfeLogExportieren = QAction("Log-Verzeichnis exportieren", self)
            hilfeLogExportieren.triggered.connect(self.logExportieren) 
            
            anwendungMenu.addAction(aboutAction)
            anwendungMenu.addAction(updateAction)
            einstellungenMenu.addAction(einstellungenAllgemeinAction)
            einstellungenMenu.addAction(einstellungenGdtAction)
            einstellungenMenu.addAction(einstellungenBenutzerAction)
            einstellungenMenu.addAction(einstellungenDosierungAction)
            ## Nur mit Lizenz
            einstellungenMenu.addAction(einstellungenErweiterungenAction)
            einstellungenMenu.addAction(einstellungenImportExportAction)
            ## /Nur mit Lizenz
            hilfeMenu.addAction(hilfeWikiAction)
            hilfeMenu.addSeparator()
            hilfeMenu.addAction(hilfeUpdateAction)
            hilfeMenu.addAction(hilfeAutoUpdateAction)
            hilfeMenu.addSeparator()
            hilfeMenu.addAction(hilfeUeberAction)
            hilfeMenu.addAction(hilfeEulaAction)
            hilfeMenu.addSeparator()
            hilfeMenu.addAction(hilfeLogExportieren)
            
            # Updateprüfung auf Github
            if self.autoupdate:
                try:
                    self.updatePruefung(meldungNurWennUpdateVerfuegbar=True)
                except Exception as e:
                    mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InrGDT", "Updateprüfung nicht möglich.\nBitte überprüfen Sie Ihre Internetverbindung.", QMessageBox.StandardButton.Ok)
                    mb.exec()
                    logger.logger.warning("Updateprüfung nicht möglich: " + str(e))
            
            # Gegebenenfalls vorherige Doku laden
            if self.vorherigedokuladen:
                self.mitVorherigerUntersuchungAusfuellen()
                self.pushButtonFolgewocheZuruecksetzenClicked()
        else:
            sys.exit()

    def mitVorherigerUntersuchungAusfuellen(self):
        for dosis in range(len(self.dosen)):
            for wt in range(7):
                self.pushButtonDosen[dosis][wt].setChecked(False)
        pfad = os.path.join(self.archivierungspfad, self.patId)
        doku = ""
        if os.path.exists(self.archivierungspfad):
            if os.path.exists(pfad) and len(os.listdir(pfad)) > 0:
                dokus = [d for d in os.listdir(pfad) if os.path.isfile(os.path.join(pfad, d))]
                dokus.sort()
                try:
                    with open(os.path.join(pfad, dokus[len(dokus) - 1]), "r") as d:
                        doku = d.read().strip()
                except Exception as e:
                    mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InrGDT", "Fehler beim Lesen der vorherigen Dokumentation: " + str(e) + "\nSoll InrGDT neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                    mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                    mb.button(QMessageBox.StandardButton.No).setText("Nein")
                    if mb.exec() == QMessageBox.StandardButton.Yes:
                        os.execl(sys.executable, __file__, *sys.argv)
        else:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InrGDT", "Das Archivierungsverzeichnis " + self.archivierungspfad + "  ist nicht erreichbar. Vorherige Assessments können daher nicht geladen werden.\nFalls es sich um eine Netzwerkfreigabe handeln sollte, stellen Sie die entsprechende Verbindung sicher und starten InrGDT neu.\nSoll InrGDT neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.setDefaultButton(QMessageBox.StandardButton.Yes)
            mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
            mb.button(QMessageBox.StandardButton.No).setText("Nein")
            if mb.exec() == QMessageBox.StandardButton.Yes:
                os.execl(sys.executable, __file__, *sys.argv)  
        
        dokuLesbar = True
        zielInrVon = ""
        zielInrBis = ""
        if doku == "" or len(doku) < 50:
            dokuLesbar = False
        elif len(doku) > 50:
            zielbereich = doku.split("::")[len(doku.split("::")) - 1]
            if not "-" in zielbereich and len(zielbereich.split("-")) != 2:
                dokuLesbar = False
            else:
                zielInrVon = zielbereich.split("-")[0]
                zielInrBis = zielbereich.split("-")[1]
        if not dokuLesbar:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InrGDT", "Die vorherige Dokumentation von ist nicht lesbar.", QMessageBox.StandardButton.Ok)
            mb.exec()
            doku = ""
        if doku != "" and self.addOnsFreigeschaltet:
            # Untersuchungsdatum
            zurVerfuegungStehendeDosenFloat = []
            for dosis in self.dosen:
                zurVerfuegungStehendeDosenFloat.append(float(dosis))
            self.archivierungsUntersuchungsdatum = doku[:2] + "." + doku[2:4] + "." + doku[4:8]
            archivierungsdosen = doku.split("::")
            nichtGefundeneArchivdosen = []
            for wt in range(7):
                if float(archivierungsdosen[wt + 1].replace(",", ".")) in zurVerfuegungStehendeDosenFloat:
                    dosisIndex = zurVerfuegungStehendeDosenFloat.index(float(archivierungsdosen[wt + 1].replace(",", ".")))
                    self.pushButtonDosen[dosisIndex][wt].setChecked(True)
                else:
                    nichtGefundeneArchivdosen.append(self.wochentage[wt] + ": " + archivierungsdosen[wt + 1].replace(",25", "\u00bc").replace(",5", "\u00bd").replace(",75", "\u00be").replace(",", "").replace("0", ""))
            self.labelArchivdatum.setText(self.archivierungsUntersuchungsdatum)
            self.pushButtonArchivierungLaden.setToolTip("Dokumentation vom " + self.archivierungsUntersuchungsdatum + " wiederherstellen")
            self.pushButtonArchivierungLaden.setEnabled(True)
            if len(nichtGefundeneArchivdosen) > 0:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InrGDT", "Nicht alle archivierten Tagesdosen können wegen fehlender Dosisbuttons wiederhergestellt werden:\n" + "\n".join(nichtGefundeneArchivdosen), QMessageBox.StandardButton.Ok)
                mb.exec()
            # Zielbereich
            self.lineEditInrzielVon.setText(zielInrVon)
            self.lineEditInrzielBis.setText(zielInrBis)

    def pushButtonArchivierungLadenClicked(self):
        self.mitVorherigerUntersuchungAusfuellen()
        self.labelArchivdatum.setText(self.archivierungsUntersuchungsdatum)
        self.labelArchivdatum.setFont(self.fontGross)

    def updatePruefung(self, meldungNurWennUpdateVerfuegbar = False):
        logger.logger.info("Updateprüfung")
        response = requests.get("https://api.github.com/repos/retconx/inrgdt/releases/latest")
        githubRelaseTag = response.json()["tag_name"]
        latestVersion = githubRelaseTag[1:] # ohne v
        if versionVeraltet(self.version, latestVersion):
            logger.logger.info("Bisher: " + self.version + ", neu: " + latestVersion)
            if os.path.exists(self.updaterpfad):
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von InrGDT", "Die aktuellere InrGDT-Version " + latestVersion + " ist auf Github verfügbar.\nSoll der GDT-Tools Updater geladen werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    logger.logger.info("Updater wird geladen")
                    atexit.register(self.updaterLaden)
                    sys.exit()
            else:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InrGDT", "Die aktuellere InrGDT-Version " + latestVersion + " ist auf <a href='https://github.com/retconx/inrgdt/releases'>Github</a> verfügbar.<br />Bitte beachten Sie auch die Möglichkeit, den Updateprozess mit dem <a href='https://github.com/retconx/gdttoolsupdater/wiki'>GDT-Tools Updater</a> zu automatisieren.", QMessageBox.StandardButton.Ok)
                mb.setTextFormat(Qt.TextFormat.RichText)
                mb.exec()
        elif not meldungNurWennUpdateVerfuegbar:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InrGDT", "Sie nutzen die aktuelle InrGDT-Version.", QMessageBox.StandardButton.Ok)
            mb.exec()

    def updaterLaden(self):
        sex = sys.executable
        programmverzeichnis = ""
        logger.logger.info("sys.executable: " + sex)
        if "win32" in sys.platform:
            programmverzeichnis = sex[:sex.rfind("inrgdt.exe")]
        elif "darwin" in sys.platform:
            programmverzeichnis = sex[:sex.find("InrGDT.app")]
        elif "linux" in sys.platform:
            programmverzeichnis = sex[:sex.rfind("inrgdt")]
        logger.logger.info("Programmverzeichnis: " + programmverzeichnis)
        try:
            if "win32" in sys.platform:
                subprocess.Popen([self.updaterpfad, "inrgdt", self.version, programmverzeichnis], creationflags=subprocess.DETACHED_PROCESS) # type: ignore
            elif "darwin" in sys.platform:
                subprocess.Popen(["open", "-a", self.updaterpfad, "--args", "inrgdt", self.version, programmverzeichnis])
            elif "linux" in sys.platform:
                subprocess.Popen([self.updaterpfad, "inrgdt", self.version, programmverzeichnis])
        except Exception as e:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InrGDT", "Der GDT-Tools Updater konnte nicht gestartet werden", QMessageBox.StandardButton.Ok)
            logger.logger.error("Fehler beim Starten des GDT-Tools Updaters: " + str(e))
            mb.exec()

    def autoUpdatePruefung(self, checked):
        self.autoupdate = checked
        self.configIni["Allgemein"]["autoupdate"] = str(checked)
        with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
            self.configIni.write(configfile)

    def ueberInrGdt(self):
        de = dialogUeberInrGdt.UeberInrGdt()
        de.exec()

    def eula(self):
        QDesktopServices.openUrl("https://gdttools.de/Lizenzvereinbarung_InrGDT.pdf")

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

    def einstellungenAllgemein(self, checked, neustartfrage):
        de = dialogEinstellungenAllgemein.EinstellungenAllgemein(self.configPath)
        if de.exec() == 1:
            self.configIni["Allgemein"]["wochentageanzeigen"] = str(de.checkBoxWochentagsuebertragungAktivieren.isChecked())
            self.configIni["Allgemein"]["lzvor"] = de.lineEditLeerzeichenVor.text()
            self.configIni["Allgemein"]["lznach"] = de.lineEditLeerzeichenNach.text()
            self.configIni["Allgemein"]["einrichtungsname"] = de.lineEditEinrichtungsname.text()
            self.configIni["Allgemein"]["archivierungspfad"] = de.lineEditArchivierungsverzeichnis.text()
            self.configIni["Allgemein"]["vorherigedokuladen"] = str(de.checkBoxVorherigeDokuLaden.isChecked())
            self.configIni["Allgemein"]["updaterpfad"] = de.lineEditUpdaterPfad.text()
            self.configIni["Allgemein"]["autoupdate"] = str(de.checkBoxAutoUpdate.isChecked())
            self.configIni["Allgemein"]["halbstatt05"] = str(de.checkboxHalbStatt05.isChecked())
            with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                self.configIni.write(configfile)
            if neustartfrage:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von InrGDT", "Damit die Einstellungsänderungen wirksam werden, sollte InrGDT neu gestartet werden.\nSoll InrGDT jetzt neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    os.execl(sys.executable, __file__, *sys.argv)

    def einstellungenGdt(self, checked, neustartfrage):
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

    def einstellungenBenutzer(self, checked, neustartfrage):
        de = dialogEinstellungenBenutzer.EinstellungenBenutzer(self.configPath)
        if de.exec() == 1:
            namen = []
            kuerzel = []
            for i in range(self.maxBenutzerzahl):
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

    def einstellungenDosierung(self, checked, neustartfrage):
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

    ## Nur mit Lizenz
    def einstellungenLanrLizenzschluessel(self, checked, neustartfrage):
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
    ## /Nur mit Lizenz
    
    def inrgdtWiki(self, link):
        QDesktopServices.openUrl("https://github.com/retconx/inrgdt/wiki")

    def lineEditInrEdited(self):
        if re.match(reInr, self.lineEditInr.text()) == None:
            self.lineEditInr.setPalette(farbe.getBasePalette(farbe.farben.ROT, self.palette()))
            self.pushButtonSenden.setEnabled(False)
        elif self.addOnsFreigeschaltet:
            self.lineEditInr.setPalette(farbe.getBasePalette(farbe.farben.NORMAL, self.palette()))
            self.pushButtonSenden.setEnabled(True)

    def lineEditInrzielEdited(self, text, lineEdit):
        if lineEdit.text() != "" and re.match(reInr, lineEdit.text()) == None:
            lineEdit.setPalette(farbe.getBasePalette(farbe.farben.ROT, self.palette()))
            self.pushButtonSenden.setEnabled(False)
        elif self.addOnsFreigeschaltet:
            lineEdit.setPalette(farbe.getBasePalette(farbe.farben.NORMAL, self.palette()))
            if re.match(reInr, self.lineEditInr.text()) != None:
                self.pushButtonSenden.setEnabled(True)

    def pushButtonDosisClicked(self, checked, dosiszeile, wochentagspalte):
        if self.labelArchivdatum.text() != "--.--.----":
            self.labelArchivdatum.setFont(self.fontGrossStrikeOut)
        for zeile in range(len(self.dosen)):
            if zeile != dosiszeile:
                self.pushButtonDosen[zeile][wochentagspalte].setChecked(False)

    def pushButtonAlleClicked(self, checked, dosiszeile):
        if self.labelArchivdatum.text() != "--.--.----":
            self.labelArchivdatum.setFont(self.fontGrossStrikeOut)
        for zeile in range(len(self.dosen)):
            for wt in range(7):
                self.pushButtonDosen[zeile][wt].setChecked(False)
        for wt in range(7):
            for pushButton in self.pushButtonDosen[dosiszeile]:
                pushButton.setChecked(True)

    def pushButtonFolgewocheAktivierenClicked(self, checked):
        for wt in range(7):
            self.comboBoxFolgewoche[wt].setEnabled(checked)
        self.pushButtonFolgewocheZuruecksetzen.setEnabled(checked)
        if checked:
            # self.pushButtonFolgewocheZuruecksetzenClicked()
            self.pushButtonFolgewocheAktivieren.setText("Deaktivieren")
        else:
            self.pushButtonFolgewocheAktivieren.setText("Aktivieren")

    def pushButtonFolgewocheZuruecksetzenClicked(self):
        for wt in range(7):
            dosisFestgelegt = False
            for zeile in range(len(self.dosen)):
                if self.pushButtonDosen[zeile][wt].isChecked():
                    dosisFestgelegt = True
                    self.comboBoxFolgewoche[wt].setCurrentText(self.pushButtonDosen[zeile][wt].text())
            if not dosisFestgelegt:
                self.comboBoxFolgewoche[wt].setCurrentText("0")

    def dateEditUntersuchungsdatumChanged(self, datum):
        self.untersuchungsdatum = datum

    def comboBoxBenutzerIndexChanged(self, index):
        self.aktuelleBenuztzernummer = index
    
    def dateEditNaechsteKontrolleChanged(self, datum):
        self.naechsteKontrolle = datum

    def checkBoxPdfErstellenClicked(self, checked):
        self.checkBoxBemerkungenAufPdf.setEnabled(checked)
        self.dateEditNaechsteKontrolle.setEnabled(checked)

    def checkBoxBemerkungenAufPdfClicked(self, checked):
        self.bemerkungenAufPdf = checked
                
    def pushButtonSendenClicked(self):
        logger.logger.info("Daten senden geklickt")
        if self.patId != "" and re.match(reInr, self.lineEditInr.text()):
            # GDT-Datei erzeugen
            sh = gdt.SatzHeader(gdt.Satzart.DATEN_EINER_UNTERSUCHUNG_UEBERMITTELN_6310, self.configIni["GDT"]["idpraxisedv"], self.configIni["GDT"]["idinrgdt"], self.zeichensatz, "2.10", "Fabian Treusch - GDT-Tools", "InrGDT", self.version, self.patId)
            gd = gdt.GdtDatei()
            logger.logger.info("GdtDatei-Instanz erzeugt")
            gd.erzeugeGdtDatei(sh.getSatzheader())
            logger.logger.info("Satzheader 6310 erzeugt")
            untersuchungsdatum = "{:>02}".format(str(self.dateEditUntersuchungsdatum.date().day())) + "{:>02}".format(str(self.dateEditUntersuchungsdatum.date().month())) + str(self.dateEditUntersuchungsdatum.date().year())
            jetzt = QTime().currentTime()
            uhrzeit = "{:>02}".format(str(jetzt.hour())) + "{:>02}".format(str(jetzt.minute())) + str(jetzt.second())
            logger.logger.info("Untersuchungsdatum/ -uhrzeit festgelegt")
            gd.addZeile("6200", untersuchungsdatum)
            gd.addZeile("6201", uhrzeit)
            gd.addZeile("8402", "ALLG00")
            # PDF hinzufügen
            if self.checkBoxPdfErstellen.isChecked():
                gd.addZeile("6302", "inr")
                gd.addZeile("6303", "pdf")
                gd.addZeile("6304", "Marcumar-Dosierungsplan")
                gd.addZeile("6305", os.path.join(basedir, "pdf/inr_temp.pdf"))

            # Wochentagsübertragung
            wochentagszeile = ""
            if self.wochentageAnzeigen:
                lzVor = ""
                for i in range(int(self.lzVor)):
                    lzVor += " "
                lzNach = ""
                for i in range(int(self.lzNach)):
                    lzNach += " "
                wochentagszeile = "INR"
                if not self.halbstatt05:
                    for wt in self.wochentage:
                        wochentagszeile += lzVor + wt + lzNach
                gd.addZeile("6220", wochentagszeile)
            
            untWt = self.untersuchungsdatum.dayOfWeek() # Montag = 1, Sonntag = 7
            montagDerUntersuchungswoche = self.untersuchungsdatum.addDays(1 - untWt)
            sonntagDerUntersuchungswoche = self.untersuchungsdatum.addDays(7 - untWt)
            montagDerFolgewoche = sonntagDerUntersuchungswoche.addDays(1)
            vonDatum = "{:>02}".format(str(montagDerUntersuchungswoche.day())) + "." + "{:>02}".format(str(montagDerUntersuchungswoche.month())) + "." + str(montagDerUntersuchungswoche.year())
            bisDatum = "{:>02}".format(str(sonntagDerUntersuchungswoche.day())) + "." + "{:>02}".format(str(sonntagDerUntersuchungswoche.month())) + "." + str(sonntagDerUntersuchungswoche.year())
            moFolgeDatum = "{:>02}".format(str(montagDerFolgewoche.day())) + "." + "{:>02}".format(str(montagDerFolgewoche.month())) + "." + str(montagDerFolgewoche.year())
            
            # Befund
            inrNachkommastellen = 0
            if len(self.lineEditInr.text().replace(".", ",").split(",")) > 1:
                inrNachkommastellen = len(self.lineEditInr.text().replace(".", ",").split(",")[1])
            befundzeile = ""
            if inrNachkommastellen <= 1:
                befundzeile = "{:.1f}".format(float(self.lineEditInr.text().replace(",", "."))).replace(".", ",")
            elif inrNachkommastellen == 2:
                befundzeile = "{:.2f}".format(float(self.lineEditInr.text().replace(",", "."))).replace(".", ",")
            befundzeile += "     "
            wochendosis = 0
            wochendosen = []
            nichtAlleWochentage = False
            for wt in range(7):
                for dosis in range(len(self.dosen)):
                    if self.pushButtonDosen[dosis][wt].isChecked():
                        wochendosen.append("{:.2f}".format(float(self.dosen[dosis])).replace(".", ","))
                        wochendosis += float(self.dosen[dosis])
                if len(wochendosen) != wt + 1:
                    nichtAlleWochentage = True
                    wochendosen.append("0,00")
            wochendosenFormatiert = wochendosen.copy()
            wochendosisFormatiert = "{:.2f}".format(wochendosis).replace(".", ",")
            if self.halbstatt05:
                for i in range(len(wochendosen)):
                    wochendosenFormatiert[i] = wochendosen[i].replace(",25", "\u00bc").replace(",50", "\u00bd").replace(",75", "\u00be").replace("0", "").replace(",", "")
                wochendosisFormatiert = wochendosisFormatiert.replace(",25", "\u00bc").replace(",50", "\u00bd").replace(",75", "\u00be").replace("0", "").replace(",", "")
            befundzeile += "  -  ".join(wochendosenFormatiert)
            externBenutzer = self.benutzerkuerzelListe[self.aktuelleBenuztzernummer]
            if self.checkBoxExtern.isChecked():
                externBenutzer = "extern/" + externBenutzer
            befundzeile += "  WD: " + wochendosisFormatiert + " (" + externBenutzer + ")"
            if self.pushButtonFolgewocheAktivieren.isChecked():
                gd.addZeile("6220", vonDatum + " - " + bisDatum + ":")
            gd.addZeile("6220", befundzeile)
            wochendosenFolgewoche = []
            wochendosisFolgewoche = 0
            if self.pushButtonFolgewocheAktivieren.isChecked():
                gd.addZeile("6220", "Ab " + moFolgeDatum + ":")
                gd.addZeile("6220", wochentagszeile)
                if inrNachkommastellen == 1:
                    befundzeile = "{:.1f}".format(float(self.lineEditInr.text().replace(",", "."))).replace(".", ",")
                elif inrNachkommastellen == 2:
                    befundzeile = "{:.2f}".format(float(self.lineEditInr.text().replace(",", "."))).replace(".", ",")
                befundzeile += "     "
                for wt in range(7):
                    wochendosenFolgewoche.append("{:.2f}".format(float(self.dosen[self.comboBoxFolgewoche[wt].currentIndex()])).replace(".", ","))
                    wochendosisFolgewoche += float(self.dosen[self.comboBoxFolgewoche[wt].currentIndex()])
                befundzeile += "  -  ".join(wochendosenFolgewoche)
                befundzeile += "  WD: " + "{:.2f}".format(wochendosisFolgewoche).replace(".", ",") + " (" + externBenutzer + ")"
                gd.addZeile("6220", befundzeile)
            
            # Benutzer
            gd.addZeile("6227", self.textEditBemerkungen.toPlainText())
            logger.logger.info("Befund und Kommentar erzeugt")
            datenSendenOk = True
            if nichtAlleWochentage:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von InrGDT", "Nicht für jeden Wochentag wurde eine Dosis angegeben.\nSollen die Daten dennoch übertragen werden? In diesem Fall wird die Dosis an den betroffenen Wochentagen auf 0 gesetzt.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.No)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.No:
                        datenSendenOk = False
            if datenSendenOk and self.dateEditUntersuchungsdatum.date().daysTo(self.dateEditNaechsteKontrolle.date()) < 0:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InrGDT", "Das Datum für die nächste Kontrolle muss nach dem Untersuchungsdatum liegen.", QMessageBox.StandardButton.Ok)
                mb.exec()
                datenSendenOk = False
                self.dateEditNaechsteKontrolle.selectAll()
            zielbereichEingetragen = self.lineEditInrzielVon.text() != "" and self.lineEditInrzielBis.text() != "" and float(self.lineEditInrzielVon.text().replace(",", ".")) < float(self.lineEditInrzielBis.text().replace(",", "."))
            if datenSendenOk and not zielbereichEingetragen:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InrGDT", "Die obere INR-Zielbereichsgrenze muss größer als die untere sein.", QMessageBox.StandardButton.Ok)
                mb.exec()
                datenSendenOk = False
                self.lineEditInrzielVon.setFocus()
                self.lineEditInrzielVon.selectAll()
            if datenSendenOk:
                # PDF erzeugen
                if self.checkBoxPdfErstellen.isChecked():
                    logger.logger.info("PDF-Erstellung aktiviert")
                    pdf = inrPdf.geriasspdf ("P", "mm", "A4")
                    logger.logger.info("FPDF-Instanz erzeugt")
                    pdf.add_page()
                    pdf.set_font("helvetica", "", 14)
                    pdf.cell(0, 10, "für " + self.name + " (* " + self.geburtsdatum + ")", align="C", new_x="LMARGIN", new_y="NEXT")
                    if self.einrichtungsname != "":
                        pdf.cell(0, 10, "erstellt von: " + self.einrichtungsname, align="C", new_x="LMARGIN", new_y="NEXT")
                    pdf.cell(0, 10, new_x="LMARGIN", new_y="NEXT")
                    pdf.set_font("helvetica", "", 16)
                    untdat = "{:>02}".format(str(self.dateEditUntersuchungsdatum.date().day())) + "." + "{:>02}".format(str(self.dateEditUntersuchungsdatum.date().month())) + "." + str(self.dateEditUntersuchungsdatum.date().year())
                    nkDat = ""
                    if self.naechsteKontrolle != QDate().currentDate():
                        nkDat = self.wochentageLang[self.dateEditNaechsteKontrolle.date().dayOfWeek() - 1] + ", " + "{:>02}".format(str(self.dateEditNaechsteKontrolle.date().day())) + "." + "{:>02}".format(str(self.dateEditNaechsteKontrolle.date().month())) + "." + str(self.dateEditNaechsteKontrolle.date().year())
                    if inrNachkommastellen <= 1:
                        pdf.cell(0, 5, "Aktueller INR-Wert: " + "{:.1f}".format(float(self.lineEditInr.text().replace(",", "."))).replace(".", ",") +  " (" + untdat + ")", align="C", new_x="LMARGIN", new_y="NEXT")
                    elif inrNachkommastellen == 2:
                        pdf.cell(0, 5, "Aktueller INR-Wert: " + "{:.2f}".format(float(self.lineEditInr.text().replace(",", "."))).replace(".", ",") +  " (" + untdat + ")", align="C", new_x="LMARGIN", new_y="NEXT")
                    # Ggf. Zielbereich
                    if zielbereichEingetragen:
                        pdf.set_font("helvetica", "", 12)
                        pdf.leerzeile(2)
                        pdf.cell(0, 4, "INR-Zielbereich: " + self.lineEditInrzielVon.text().replace(".", ",") + " - " + self.lineEditInrzielBis.text().replace(".", ","), align="C", new_x="LMARGIN", new_y="NEXT")
                    pdf.leerzeile(10)
                    if self.pushButtonFolgewocheAktivieren.isChecked():
                        x = 10
                    else:
                        x = 35
                    pdf.set_x(x)
                    pdf.set_font("helvetica", "B", 16)
                    if self.pushButtonFolgewocheAktivieren.isChecked():
                        pdf.cell(50, 16, "Zeitraum", border=1, align="C")

                    for wt in range(7):
                        if wt < 6:
                            pdf.cell(20, 16, self.wochentage[wt], border=1, align="C")
                        else:
                            pdf.cell(20, 16, self.wochentage[wt], border=1, align="C", new_x="LMARGIN", new_y="NEXT")
                    pdf.set_x(x)
                    pdf.set_font("helvetica", "", 16)
                    if self.pushButtonFolgewocheAktivieren.isChecked():
                        pdf.cell(50, 7, " " + vonDatum + " -", border="TLR", new_y="NEXT",)
                        pdf.set_x(x)
                        pdf.cell(50, 7, " " + bisDatum, border="BLR")
                        pdf.set_y(pdf.get_y() - 7)
                        pdf.set_x(x + 50)
                    for wt in range(7):
                        if wt < 6:
                            if wochendosen[wt] != "0,00":
                                pdf.cell(20, 14, wochendosen[wt].replace(",25", "\u00bc").replace(",50", "\u00bd").replace(",75", "\u00be").replace(",", "").replace("0", ""), border=1, align="C")
                            else:
                                pdf.cell(20, 14, "0", border=1, align="C")
                        else:
                            if wochendosen[wt] != "0,00":
                                pdf.cell(20, 14, wochendosen[wt].replace(",25", "\u00bc").replace(",50", "\u00bd").replace(",75", "\u00be").replace(",", "").replace("0", ""), border=1, align="C", new_x="LMARGIN", new_y="NEXT")
                            else:
                                pdf.cell(20, 14, "0", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
                    if self.pushButtonFolgewocheAktivieren.isChecked():
                        pdf.set_x(x)
                        pdf.cell(50, 14, " Ab " + moFolgeDatum, border=1)
                        for wt in range(7):
                            pdf.cell(20, 14, self.comboBoxFolgewoche[wt].currentText(), border=1, align="C")
                        pdf.cell(0, 10, new_x="LMARGIN", new_y="NEXT")

                    # Ggf. Bemerkungen
                    if self.bemerkungenAufPdf and self.textEditBemerkungen.toPlainText() != "":
                        pdf.cell(0, 10, new_x="LMARGIN", new_y="NEXT")
                        pdf.set_font("helvetica", "", 14)
                        pdf.cell(0, 0, "Bemerkungen:", new_x="LMARGIN", new_y="NEXT")
                        pdf.set_font("helvetica", "", 14)
                        pdf.cell(0, 10, self.textEditBemerkungen.toPlainText())    

                    # Ggf. nächste Kontrolle
                    if nkDat != "":
                        pdf.cell(0, 10, new_x="LMARGIN", new_y="NEXT")
                        pdf.set_font("helvetica", "", 14)
                        pdf.cell(0, 14, "Nächste Kontrolle: " + nkDat)
                    pdf.set_y(-30)
                    pdf.set_font("helvetica", "I", 10)
                    pdf.cell(0, 10, "Generiert von InrGDT V" + self.version + " (\u00a9 GDT-Tools " + str(datetime.date.today().year) + ")", align="R")
                    logger.logger.info("PDF-Seite aufgebaut")
                    try:
                        pdf.output(os.path.join(basedir, "pdf/inr_temp.pdf"))
                        logger.logger.info("PDF-Output nach " + os.path.join(basedir, "pdf/inr_temp.pdf") + " erfolgreich")
                    except:
                        logger.logger.error("Fehler bei PDF-Output nach " + os.path.join(basedir, "pdf/inr_temp.pdf"))

                # GDT-Datei exportieren
                if not gd.speichern(os.path.join(self.gdtExportVerzeichnis, self.kuerzelpraxisedv + self.kuerzelinrgdt + ".gdt"), self.zeichensatz):
                    logger.logger.error("Fehler bei GDT-Dateiexport nach " + self.gdtExportVerzeichnis + "/" + self.kuerzelpraxisedv + self.kuerzelinrgdt + ".gdt")
                    mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InrGDT", "GDT-Export nicht möglich.\nBitte überprüfen Sie die Angabe des Exportverzeichnisses.", QMessageBox.StandardButton.Ok)
                    mb.exec()
                self.configIni["Allgemein"]["immerextern"] = str(self.checkBoxExtern.isChecked())
                self.configIni["Allgemein"]["immerpdf"] = str(self.checkBoxPdfErstellen.isChecked())
                self.configIni["Allgemein"]["bemerkungenaufpdf"] = str(self.checkBoxBemerkungenAufPdf.isChecked())
                self.configIni["Benutzer"]["letzter"] = str(self.aktuelleBenuztzernummer)
                try:
                    with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                        self.configIni.write(configfile)
                        logger.logger.info("Allgemein/immerextern in config.ini auf " + str(self.checkBoxExtern.isChecked()) + " gesetzt")
                        logger.logger.info("Allgemein/immerpdf in config.ini auf " + str(self.checkBoxPdfErstellen.isChecked()) + " gesetzt")
                    # Archivieren
                    zusammenfassung = untersuchungsdatum + "::" + "::".join(wochendosen)
                    if self.pushButtonFolgewocheAktivieren.isChecked():
                        folgewochendosen = []
                        for wt in range(7):
                            folgewochendosen.append("{:.2f}".format(float(self.dosen[self.comboBoxFolgewoche[wt].currentIndex()])).replace(".", ","))
                        zusammenfassung = untersuchungsdatum + "::" + "::".join(folgewochendosen)
                    # Ggf. Zielbereich
                    if zielbereichEingetragen:
                        zusammenfassung += "::" + self.lineEditInrzielVon.text().replace(".", ",") + "-" + self.lineEditInrzielBis.text().replace(".", ",")
                    if self.archivierungspfad != "":
                        if os.path.exists(self.archivierungspfad):
                            speicherdatum = str(self.dateEditUntersuchungsdatum.date().year()) + "{:>02}".format(str(self.dateEditUntersuchungsdatum.date().month())) + "{:>02}".format(str(self.dateEditUntersuchungsdatum.date().day()))
                            try:
                                if not os.path.exists(self.archivierungspfad + "/" + self.patId):
                                    os.mkdir(self.archivierungspfad + "/" + self.patId, 0o777)
                                    logger.logger.info("Archivierungsverzeichnis für PatId " + self.patId + " erstellt")
                                with open(self.archivierungspfad + "/" + self.patId + "/" + speicherdatum + "_" + self.patId + ".ina", "w") as zf:
                                    zf.write(zusammenfassung)
                                    logger.logger.info("Doku für PatId " + self.patId + " archiviert")
                            except IOError as e:
                                logger.logger.error("IO-Fehler beim Speichern der Doku von PatId " + self.patId + ": " + str(e))
                                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InrGDT", "Fehler beim Speichern der Dokumentation\n" + str(e), QMessageBox.StandardButton.Ok)
                                mb.exec()
                            except:
                                logger.logger.error("Nicht-IO-Fehler beim Speichern der Doku von PatId " + self.patId)
                                raise
                        else:
                            logger.logger.warning("Dokuverzeichnis existiert nicht")
                            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InrGDT", "Speichern der Dokumentation nicht möglich\nBitte überprüfen Sie die Angabe des Dokumentations-Speicherverzeichnisses.", QMessageBox.StandardButton.Ok)
                            mb.exec()
                    else:
                        logger.logger.info("Nicht archiviert, da Archivierungspfad nicht festgelegt")
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
app.setWindowIcon(QIcon(os.path.join(basedir, "icons", "program.png")))
window = MainWindow()
window.show()
app.exec()