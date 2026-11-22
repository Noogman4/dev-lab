# 🐧 Linux Mint – Komponenten einfach erklärt

**Ein Nachschlagewerk für System, Desktop, Netzwerk und Konfiguration**\
Stand: 21. November 2026 · Grundlage: Linux Mint mit Ubuntu-/Linux-Unterbau; LMDE-Abweichungen sind gekennzeichnet

---

> 💡 **Zur Einordnung:** Linux Mint besteht aus vielen Bausteinen. Dazu gehören Programme, Hintergrunddienste, Protokolle, Verzeichnisse und Konfigurationsdateien. Nur ein Teil davon sind technisch „Kernelmodule“.
>
> Diese Übersicht beschreibt wichtige Komponenten und mögliche Ergänzungen. Sie ist keine Bestandsaufnahme deines Computers: Welche davon installiert oder aktiv sind, hängt von Mint-Version, Edition, Hardware und Einrichtung ab.

> 🌿 **Mint-Editionen:** Die Übersicht berücksichtigt Cinnamon, MATE und Xfce. Linux Mint basiert üblicherweise auf Ubuntu; **LMDE** steht für „Linux Mint Debian Edition“ und verwendet Debian direkt. Einige Ubuntu-Werkzeuge sind dort nicht verfügbar.

## Inhaltsverzeichnis

1. [🔵 Systemkern und Startvorgang](#1-systemkern-und-startvorgang)
2. [🟣 Desktop, Fenster und Grafik](#2-desktop-fenster-und-grafik)
3. [🟢 Netzwerk und Internet](#3-netzwerk-und-internet)
4. [🟠 Laufwerke und Dateisysteme](#4-laufwerke-und-dateisysteme)
5. [🔴 Sicherheit und Berechtigungen](#5-sicherheit-und-berechtigungen)
6. [🟡 Ton, Drucker und Hintergrunddienste](#6-ton-drucker-und-hintergrunddienste)
7. [🔷 Programme und Softwareverwaltung](#7-programme-und-softwareverwaltung)
8. [📁 Wichtige Verzeichnisse](#8-wichtige-verzeichnisse)
9. [📝 Wichtige Konfigurationsdateien](#9-wichtige-konfigurationsdateien)
10. [🧭 Begriffe auf einen Blick](#10-begriffe-auf-einen-blick)
11. [🔎 Weiterführende Quellen](#11-weiterfuehrende-quellen)

> 🎨 **Darstellung:** Farbige Symbole kennzeichnen die Themenbereiche. Sie funktionieren ohne zusätzliche Erweiterungen. Schriftfarben und Hintergrundfarben lassen sich in Markdown nicht über alle Anzeigeprogramme hinweg zuverlässig festlegen.

---

<a id="1-systemkern-und-startvorgang"></a>
## 🔵 1. Systemkern und Startvorgang

*Die Grundlage: vom Einschalten bis zum laufenden Betriebssystem.*

| Name | Art | Funktion |
| :--- | :--- | :--- |
| **Linux-Kernel** | Systemkern | Verwaltet Prozessor, Arbeitsspeicher, Geräte und laufende Prozesse. |
| **Kernelmodule** | Kernel-Erweiterungen | Ergänzen den Kernel, beispielsweise um WLAN-Treiber oder Unterstützung für Dateisysteme. |
| **UEFI / BIOS** | Rechner-Firmware | Initialisiert die Hardware und leitet den Start des Betriebssystems ein. Gehört zum Computer, nicht zu Linux Mint selbst. |
| **GRUB** | Bootmanager | Ermöglicht die Auswahl des Betriebssystems oder einer anderen Kernelversion. |
| **initramfs** | Startumgebung | Lädt früh benötigte Treiber und bereitet den Zugriff auf das eigentliche System vor, etwa bei verschlüsselten Laufwerken. |
| **systemd** | Dienst- und Systemverwaltung | Startet und überwacht Dienste; organisiert unter anderem Neustart und Herunterfahren. |
| **udev** | Geräteverwaltung | Verarbeitet Geräteereignisse und verwaltet Geräteeinträge, beispielsweise beim Einstecken eines USB-Sticks. |

---

<a id="2-desktop-fenster-und-grafik"></a>
## 🟣 2. Desktop, Fenster und Grafik

*Diese Bausteine machen das System sichtbar und bedienbar.*

| Name | Art | Funktion |
| :--- | :--- | :--- |
| **Cinnamon** | Desktopumgebung | Liefert Menü, Panel, Fensterbedienung und Einstellungen der Cinnamon-Edition. |
| **MATE** | Desktopumgebung | Klassisch aufgebaute Alternative in der MATE-Edition. |
| **Xfce** | Desktopumgebung | Ressourcenschonende Alternative in der Xfce-Edition. |
| **Cinnamon-Systemeinstellungen** | Einstellungsprogramm | Verwaltet unter anderem Designs, Anzeige, Tastatur, Arbeitsflächen und Erweiterungen. |
| **Applets / Desklets / Erweiterungen** | Cinnamon-Ergänzungen | Applets ergänzen das Panel, Desklets den Desktop; Erweiterungen verändern das Verhalten der Oberfläche. |
| **Wayland** | Grafikprotokoll | Regelt den Austausch zwischen Anwendungen und dem Compositor. Unterstützung und Reife hängen von Desktop und Version ab. |
| **X11 / Xorg** | Grafikprotokoll / Displayserver | X11 ist das ältere Grafikprotokoll; Xorg ist eine verbreitete Umsetzung als Displayserver und wird in vielen Mint-Sitzungen verwendet. |
| **XWayland** | Kompatibilitätskomponente | Ermöglicht X11-Anwendungen, innerhalb einer unterstützten Wayland-Sitzung zu laufen. |
| **Muffin / libmuffin** | Fensterverwaltung | Liefert Cinnamon Funktionen zur Fensterverwaltung und Bildkomposition. Cinnamon verwendet die Bibliothek; ein eigener Muffin-Prozess muss dabei nicht laufen. |
| **Marco** | Fenstermanager | Verwaltet die Fenster der MATE-Oberfläche in einer typischen X11-Sitzung. |
| **Xfwm4** | Fenstermanager | Verwaltet die Fenster und deren Darstellung in einer typischen Xfce-Sitzung. |
| **LightDM** | Anmeldemanager | Verwaltet den grafischen Anmeldevorgang und startet die gewählte Desktopsitzung. |
| **Slick Greeter** | Anmeldeoberfläche | Stellt den sichtbaren Anmeldebildschirm für LightDM bereit. |
| **Mesa** | Grafikbibliotheken und Treiberkomponenten | Stellt unter anderem OpenGL- und Vulkan-Unterstützung für viele Grafikgeräte bereit. |
| **Nemo** | Dateimanager | Verwaltet Dateien und Ordner in der Cinnamon-Edition. |
| **Caja** | Dateimanager | Verwaltet Dateien und Ordner in der MATE-Edition. |
| **Thunar** | Dateimanager | Verwaltet Dateien und Ordner in der Xfce-Edition. |

> 💡 **Zusammenhang:** Cinnamon, MATE und Xfce sind alternative Desktopumgebungen. Ihre Fensterverwaltung und Dateimanager unterscheiden sich. Wayland und X11 sind die zugrunde liegenden Grafikprotokolle; sie sind nicht in jeder Edition gleich verfügbar.

---

<a id="3-netzwerk-und-internet"></a>
## 🟢 3. Netzwerk und Internet

*Verbindungen, Namensauflösung und Kommunikation mit anderen Geräten.*

| Name | Art | Funktion |
| :--- | :--- | :--- |
| **NetworkManager** | Netzwerkdienst | Verwaltet LAN, WLAN und unterstützte VPN-Verbindungen. |
| **systemd-resolved** | Dienst zur Namensauflösung | Kann Namensanfragen und einen DNS-Zwischenspeicher verwalten. Ob der Dienst eingesetzt wird, hängt von Mint-Version und Einrichtung ab. |
| **DNS** | Namenssystem | Übersetzt Namen wie `example.com` in IP-Adressen. |
| **DHCP** | Netzwerkprotokoll | Liefert automatisch Netzwerkeinstellungen wie IP-Adresse, Gateway und DNS-Server. |
| **Netplan** | Konfigurationssystem | Beschreibt Netzwerkeinstellungen in YAML-Dateien, sofern installiert und verwendet. Unter Mint nicht pauschal als aktive Standardverwaltung anzunehmen; LMDE kann abweichen. |
| **wpa_supplicant** | Authentifizierungsdienst | Übernimmt unter anderem die Anmeldung an geschützten WLAN-Netzen. |
| **WireGuard** | VPN-Technik | Erstellt verschlüsselte Netzwerkverbindungen; muss passend eingerichtet sein. |
| **Blueman** | Bluetooth-Verwaltung | Grafisches Werkzeug zum Koppeln und Verwalten von Bluetooth-Geräten; arbeitet mit BlueZ zusammen. |
| **BlueZ** | Bluetooth-System | Ermöglicht Bluetooth-Verbindungen, etwa mit Kopfhörern, Mäusen und Tastaturen. |
| **Avahi** | Lokale Diensterkennung | Erkennt Geräte und Dienste im lokalen Netzwerk, unter anderem über mDNS und Namen mit `.local`. |

> 💡 **Zusammenhang:** NetworkManager verwaltet die Verbindung. DHCP kann die Netzwerkeinstellungen liefern. DNS löst Namen auf. Netplan kann je nach Installation beteiligt sein; die grafische Mint-Netzwerkverwaltung arbeitet mit NetworkManager.

---

<a id="4-laufwerke-und-dateisysteme"></a>
## 🟠 4. Laufwerke und Dateisysteme

*Wie Linux Speicher organisiert und Dateien zugänglich macht.*

| Name | Art | Funktion |
| :--- | :--- | :--- |
| **ext4** | Dateisystem | Verbreitetes Linux-Dateisystem zum Speichern von Dateien und Verzeichnissen. |
| **Btrfs** | Dateisystem | Alternative mit Funktionen wie Prüfsummen und Snapshots; nicht auf jedem Mint-System eingerichtet. |
| **VFS** | Kernel-Schnittstelle | Bietet eine gemeinsame Schnittstelle zu unterschiedlichen Dateisystemen. |
| **mount / umount** | Befehle | Hängen ein Dateisystem in den Verzeichnisbaum ein beziehungsweise aus. |
| **UDisks2** | Laufwerksdienst | Unterstützt Desktopprogramme bei der Laufwerksverwaltung, beispielsweise beim Einbinden von USB-Laufwerken. |
| **LUKS / dm-crypt** | Verschlüsselungsformat / Kernel-Technik | LUKS verwaltet das Format für verschlüsselte Datenträger; dm-crypt übernimmt die eigentliche Blockgeräteverschlüsselung. |
| **LVM** | Speicherverwaltung | Verwaltet logische Speicherbereiche flexibel über physische Laufwerke hinweg. |
| **Timeshift** | Systemwiederherstellung | Erstellt System-Snapshots für die Rückkehr zu einem früheren Zustand. Persönliche Dateien sind standardmäßig ausgenommen; ersetzt keine Sicherung eigener Dokumente. |
| **mintbackup** | Datensicherungswerkzeug | Sichert persönliche Dateien und eine Liste installierter Software für eine spätere Wiederherstellung. |
| **mintstick** | USB-Werkzeuge | Schreibt ISO-Abbilder auf USB-Sticks und bietet ein Werkzeug zum Formatieren von USB-Sticks. |
| **Swap** | Auslagerungsspeicher | Ergänzt den Arbeitsspeicher. Kann bei geeigneter Konfiguration auch für den Ruhezustand verwendet werden. |

> 💡 **„Einhängen“ bedeutet:** Ein Dateisystem wird unter einem Verzeichnispfad zugänglich gemacht, beispielsweise ein USB-Stick unter `/media/...`.

---

<a id="5-sicherheit-und-berechtigungen"></a>
## 🔴 5. Sicherheit und Berechtigungen

*Wer darf was tun – und welche Zugriffe sind erlaubt?*

| Name | Art | Funktion |
| :--- | :--- | :--- |
| **root** | Administratorkonto | Besitzt umfassende Systemrechte. |
| **sudo** | Berechtigungswerkzeug | Führt erlaubte Befehle mit den Rechten eines anderen Kontos aus, meist als root. |
| **Polkit** | Berechtigungssystem | Prüft, ob ein Benutzer privilegierte Aktionen eines Systemdienstes ausführen darf, etwa aus einem grafischen Programm heraus. |
| **PAM** | Authentifizierungssystem | Stellt gemeinsame Bausteine für Anmeldung und Authentifizierungsprüfungen bereit. |
| **AppArmor** | Zugriffsschutz | Beschränkt anhand von Profilen, auf welche Ressourcen ein Programm zugreifen darf. |
| **UFW** | Firewall-Verwaltung | Vereinfacht das Einrichten und Verwalten von Firewall-Regeln. |
| **Netfilter** | Kernel-Funktionen | Verarbeitet und filtert Netzwerkpakete und ermöglicht unter anderem Firewall- und NAT-Funktionen. |
| **nftables / iptables** | Regel- und Verwaltungswerkzeuge | Konfigurieren die Paketfilterung des Kernels. Welche Schnittstelle verwendet wird, hängt vom System ab. |
| **Gufw** | Grafische Firewall-Verwaltung | Bedienoberfläche für UFW zum Anzeigen und Bearbeiten von Firewall-Regeln. |
| **GNOME Keyring** | Zugangsdatenverwaltung | Speichert Passwörter und andere Geheimnisse für unterstützende Anwendungen. |

---

<a id="6-ton-drucker-und-hintergrunddienste"></a>
## 🟡 6. Ton, Drucker und Hintergrunddienste

*Dienste, die meist unauffällig im Hintergrund arbeiten.*

| Name | Art | Funktion |
| :--- | :--- | :--- |
| **ALSA** | Audiosystem | Liefert grundlegende Linux-Audioschnittstellen und Treiber für Soundgeräte. |
| **PipeWire** | Multimedia-Dienst | Verarbeitet und verteilt Audio und bestimmte Videoströme, etwa bei Bildschirmfreigaben. |
| **WirePlumber** | PipeWire-Sitzungsverwaltung | Verwaltet Geräte, Verbindungen und Regeln für PipeWire. |
| **PulseAudio** | Audiodienst | Verwaltet Audioströme vor allem auf älteren Systemen. Bei PipeWire kann eine kompatible Schnittstelle diese Rolle übernehmen. |
| **CUPS** | Drucksystem | Verwaltet Drucker, Warteschlangen und Druckaufträge. |
| **D-Bus** | Nachrichtensystem | Ermöglicht den Austausch von Nachrichten zwischen Anwendungen und Systemdiensten. |
| **journald** | Protokolldienst | Sammelt System- und Dienstmeldungen; lesbar unter anderem mit `journalctl`. |
| **cron / systemd-Timer** | Zeitgesteuerte Aufgaben | Starten Aufgaben zu festgelegten Zeiten oder nach bestimmten Zeitabständen. |
| **UPower** | Energieinformationsdienst | Liefert Informationen über Akkus und Stromversorgung an Anwendungen und Desktopkomponenten. |

---

<a id="7-programme-und-softwareverwaltung"></a>
## 🔷 7. Programme und Softwareverwaltung

*Software installieren, aktualisieren und über Befehle bedienen.*

| Name | Art | Funktion |
| :--- | :--- | :--- |
| **APT** | Paketverwaltung | Installiert und aktualisiert Software aus Paketquellen einschließlich benötigter Abhängigkeiten. |
| **dpkg** | Paketwerkzeug | Installiert und verwaltet Debian-Pakete mit der Endung `.deb`. |
| **Flatpak** | Anwendungspaketsystem | Betreibt Anwendungen mit eigenen Laufzeitumgebungen und durch Berechtigungen begrenzten Zugriffen. |
| **Snap / snapd** | Optionales Paketsystem | In Mint standardmäßig nicht eingerichtet; die Installation von snapd wird üblicherweise durch eine APT-Regel blockiert. Eine Nutzung erfordert bewusste zusätzliche Einrichtung. |
| **mintinstall** | Anwendungsverwaltung | Sucht und installiert Programme aus Paketquellen und Flatpak-Angeboten. |
| **mintupdate** | Aktualisierungsverwaltung | Zeigt Software- und Sicherheitsupdates an und ermöglicht deren Installation. |
| **mintsources** | Paketquellenverwaltung | Verwaltet Softwarequellen, Spiegelserver und Wartungsaufgaben; Funktionen unterscheiden sich zwischen Ubuntu-Mint und LMDE. |
| **mintdrivers** | Treiberverwaltung | Hilft bei der Installation passender proprietärer Treiber. Verwendet Ubuntu-Komponenten und ist in LMDE nicht verfügbar. |
| **mintreport** | Systemberichte | Zeigt Systeminformationen und hilft bei der Erfassung von Abstürzen und Problemen. |
| **mintwelcome** | Willkommensprogramm | Bietet nach der Installation Orientierung und Zugang zu ersten Einrichtungsschritten. |
| **mintlocale** | Sprachverwaltung | Verwaltet Spracheinstellungen und Eingabemethoden. |
| **mintupgrade** | Versionsupgrade-Werkzeug | Unterstützt freigegebene Upgrades auf eine neue Hauptversion; Verfügbarkeit hängt vom vorgesehenen Upgradepfad ab. |
| **Aptkit** | Paketverwaltungsbibliothek | Stellt in neueren Mint-Versionen gemeinsame Funktionen für grafische Paketoperationen bereit. |
| **Captain** | Paketinstallationsprogramm | Öffnet und installiert in neueren Mint-Versionen unter anderem lokale DEB-Pakete; ersetzt dort GDebi und apturl. |
| **XApps** | Anwendungsfamilie | Gemeinsame Desktopprogramme, beispielsweise Xed zum Bearbeiten von Text, Xreader für Dokumente und Pix für Bilder. |
| **Bash** | Shell / Kommandointerpreter | Verarbeitet Befehle und Shellskripte. |
| **Terminal** | Bedienprogramm | Stellt ein Fenster bereit, in dem du mit einer Shell wie Bash arbeitest. |
| **glibc** | Programmbibliothek | Liefert grundlegende Funktionen, die viele Linux-Programme benötigen. |

> 💡 **Terminal und Bash:** Das Terminal ist das Bedienfenster. Bash ist ein darin laufender Kommandointerpreter.

---

<a id="8-wichtige-verzeichnisse"></a>
## 📁 8. Wichtige Verzeichnisse

*Linux ordnet Dateien und Geräte in einem gemeinsamen Verzeichnisbaum an.*

| Pfad | Bedeutung |
| :--- | :--- |
| **`/`** | Wurzel des gesamten Verzeichnisbaums. |
| **`/etc`** | Systemweite Konfigurationsdateien. Das Verzeichnis ist selbst kein Programm. |
| **`/home`** | Persönliche Verzeichnisse der Benutzer. |
| **`/root`** | Persönliches Verzeichnis des Administratorkontos root. |
| **`/boot`** | Dateien für den Systemstart, darunter Kernel und initramfs. |
| **`/usr`** | Großteil der installierten Programme, Bibliotheken und gemeinsam verwendeten Daten. |
| **`/var`** | Veränderliche Systemdaten, etwa Protokolle, Caches und Warteschlangen. |
| **`/dev`** | Geräteeinträge, über die Programme auf Geräte zugreifen können. |
| **`/proc`** | Virtuelles Dateisystem mit Informationen über Prozesse und den Kernel. |
| **`/sys`** | Virtuelles Dateisystem mit Informationen und Schnittstellen zu Geräten und Kernelfunktionen. |
| **`/run`** | Flüchtige Laufzeitdaten; werden beim Neustart neu angelegt. |
| **`/tmp`** | Temporäre Dateien; die Bereinigung richtet sich nach der Systemkonfiguration. |
| **`/media`** | Häufiger Einhängeort für automatisch eingebundene Wechselmedien. |
| **`/mnt`** | Üblicher Ort für vorübergehend manuell eingehängte Dateisysteme. |
| **`/opt`** | Zusätzliche Software mit eigenem Installationsbereich. |

> 💡 **Nicht verwechseln:** `/` ist die Wurzel des Dateibaums. `/root` ist das persönliche Verzeichnis des Benutzers root.

---

<a id="9-wichtige-konfigurationsdateien"></a>
## 📝 9. Wichtige Konfigurationsdateien

*Hier stehen Einstellungen, die Programme und Dienste auswerten.*

| Datei oder Verzeichnis | Funktion |
| :--- | :--- |
| **`/etc/fstab`** | Legt fest, welche Dateisysteme wo und mit welchen Optionen eingebunden werden sollen, häufig beim Start. |
| **`/etc/crypttab`** | Beschreibt verschlüsselte Datenträger und wie deren Entschlüsselung eingerichtet werden soll. |
| **`/etc/hostname`** | Enthält den Rechnernamen. |
| **`/etc/hosts`** | Ordnet Rechnernamen lokal IP-Adressen zu. |
| **`/etc/resolv.conf`** | Enthält Angaben zur DNS-Namensauflösung; wird häufig automatisch verwaltet oder ist eine symbolische Verknüpfung. |
| **`/etc/NetworkManager/`** | Konfiguration von NetworkManager; kann gespeicherte Verbindungsprofile enthalten. |
| **`/etc/netplan/`** | Netzwerkkonfiguration im YAML-Format, sofern Netplan installiert und verwendet wird. |
| **`/etc/passwd`** | Benutzerkonten mit Angaben wie Benutzer-ID, persönlichem Verzeichnis und Anmeldeshell. |
| **`/etc/shadow`** | Geschützte Passwortprüfwerte und Angaben zur Passwortgültigkeit. |
| **`/etc/group`** | Gruppen mit Gruppen-IDs und zusätzlichen Gruppenmitgliedschaften. |
| **`/etc/sudoers`** | Regeln dafür, wer welche Befehle über sudo ausführen darf. |
| **`/etc/default/grub`** | Einstellungen für die Erzeugung der GRUB-Konfiguration. |
| **`/etc/systemd/system/`** | Lokal eingerichtete Dienste, Timer und Anpassungen bestehender Dienste. |
| **`/etc/sysctl.conf`**, **`/etc/sysctl.d/`** | Einstellungen für veränderbare Kernelparameter, etwa zum Netzwerkverhalten. |
| **`/etc/apt/sources.list.d/`** | Softwarequellen für APT, beispielsweise in `.sources`- oder `.list`-Dateien. |
| **`/etc/lightdm/`** | Konfiguration des Anmeldemanagers LightDM, unter anderem über Dateien in `lightdm.conf.d/`. |
| **`/etc/lightdm/slick-greeter.conf`** | Lokale Anpassungen der sichtbaren Anmeldeoberfläche, sofern die Datei angelegt wurde. |
| **`/etc/linuxmint/info`** | Angaben zur installierten Mint-Version und Edition. |
| **`/etc/apt/preferences.d/nosnap.pref`** | APT-Regel, die auf üblichen Mint-Installationen die Installation von snapd blockiert. |
| **`~/.config/dconf/user`** | Binäre Datenbank mit vielen persönlichen Desktop-Einstellungen; wird über Einstellungsprogramme oder dconf-Werkzeuge verwaltet. |
| **`~/.local/share/cinnamon/`** | Persönliche Cinnamon-Ergänzungen und Daten, etwa heruntergeladene Applets, Desklets und Erweiterungen. |
| **`~/.config/`** | Persönliche Einstellungen vieler Anwendungen. |
| **`~/.bashrc`** | Persönliche Einstellungen für interaktive Bash-Sitzungen ohne Login. |

> 💡 **Pfad lesen:** In `/etc/fstab` ist `/etc` das Verzeichnis und `fstab` der Dateiname. Das Zeichen `~` steht für dein persönliches Benutzerverzeichnis, etwa `/home/sandra` – abhängig von deinem tatsächlichen Benutzernamen.

---

<a id="10-begriffe-auf-einen-blick"></a>
## 🧭 10. Begriffe auf einen Blick

| Begriff | Einfach erklärt | Beispiel |
| :--- | :--- | :--- |
| **Kernel** | Kern des Betriebssystems | Linux |
| **Kernelmodul** | Nachladbare Erweiterung des Kernels | Ein WLAN-Treiber |
| **Dienst / Daemon** | Hintergrundprogramm mit einer bestimmten Aufgabe | NetworkManager |
| **Protokoll** | Regeln für die Kommunikation | Wayland, DNS, DHCP |
| **Desktopumgebung** | Zusammengehörige Oberfläche und Desktopprogramme | Cinnamon, MATE, Xfce |
| **Bibliothek** | Gemeinsam verwendete Programmfunktionen | glibc |
| **Dateisystem** | Struktur zur Organisation gespeicherter Daten | ext4, Btrfs |
| **Verzeichnis** | Ordner im Dateibaum | `/etc` |
| **Konfigurationsdatei** | Gespeicherte Einstellungen | `/etc/fstab` |

**Deine drei Beispiele:**

| Name | Was ist es? | Wofür ist es da? |
| :--- | :--- | :--- |
| **Wayland** | Grafikprotokoll | Kommunikation zwischen grafischen Anwendungen und dem Compositor. |
| **`/etc`** | Verzeichnis | Enthält systemweite Konfiguration. |
| **`/etc/fstab`** | Konfigurationsdatei | Beschreibt die Einbindung von Dateisystemen. |

---

<a id="11-weiterfuehrende-quellen"></a>
## 🔎 11. Weiterführende Quellen

- [Linux Mint – Editionen auswählen](https://linuxmint-installation-guide.readthedocs.io/en/latest/choose.html): Cinnamon, MATE und Xfce.
- [Linux Mint – Cinnamon-Komponenten](https://linuxmint-developer-guide.readthedocs.io/en/latest/cinnamon.html): Cinnamon, Muffin und Nemo.
- [Linux Mint – eigene Werkzeuge](https://linuxmint-developer-guide.readthedocs.io/en/latest/mint-tools.html): Anwendungsverwaltung, Updates, Treiber und weitere Mint-Werkzeuge.
- [Linux Mint – Neuerungen in 22.1](https://www.linuxmint.com/rel_xia_cinnamon_whatsnew.php): Einführung von Aptkit und Captain; versionsabhängige Funktionen.
- [Linux Mint – System-Snapshots](https://linuxmint-installation-guide.readthedocs.io/en/latest/timeshift.html): Einrichtung der Systemwiederherstellung.
- [Linux Mint – Timeshift](https://github.com/linuxmint/timeshift): Funktionsweise und Abgrenzung zur Sicherung persönlicher Dateien.
- [Linux Mint – Snap Store](https://linuxmint-user-guide.readthedocs.io/en/latest/snap.html): Standardverhalten und optionale Einrichtung.
- [Linux Mint – LMDE](https://www.linuxmint.com/download_lmde.php): Debian-basierte Mint-Variante.

*Diese Übersicht dient als verständliches Nachschlagewerk. Sie enthält keine Änderungen an deinem System.*
