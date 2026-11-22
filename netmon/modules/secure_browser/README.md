# Secure Browser

Platzhalter-Modul für die spätere NetMon-Integration des Secure Browser Managers.

## Zweck

Dieses Modul bereitet die Architektur für getrennte, gehärtete Browser-Container
innerhalb von NetMon vor. Aktuell stellt es Datenmodell, Service-Skeleton,
Manager-Skeleton und einen lesenden GUI-Tab für die Inventur bestehender
Container bereit. Der Einstieg prüft per read-only Preflight, ob Builder,
Konfiguration, Firefox-Quelle und Menüpfade für die spätere Nutzung
vorhanden sind.

## Sicherheitsprinzipien

- Dry-Run zuerst
- Backup vor Änderung
- keine externen Profile löschen
- keine Container überschreiben
- keine Änderungen ohne spätere explizite Freigabe
- Zugangsdaten bleiben getrennt pro Container speicherbar

## Aktueller Stand

- Rein lesende Inventur bestehender Secure-Browser-Container
- Read-only Preflight für Builder-Skript, Konfiguration, Firefox-Quelle und Menüpfad
- Auswahl erkannter Container im Tab
- Detailansicht für Pfad, Binary, Profil, Menüeintrag und Domains
- Markdown-Export der aktuell gefilterten Inventuransicht in die Zwischenablage
- Read-only-Verifikation für ausgewählten Container
- Strukturierte Prüfung von `launcher.desktop` und Menüeintrag
- Vorschau von `start.sh` und `launcher.desktop` für den ausgewählten Container
- Explizite read-only Aktion `Launcher prüfen`
- Mehrbereichs-Viewer für `Übersicht`, `Launcher` und `Artefakte`
- Kennzahlen zur Statusverteilung der letzten Inventur
- Kompakter Risiko-Block pro ausgewähltem Container
- Schnellfilter für `Nur Risiken` und `Nur externe Profile`
- Erweiterte Kennzahlen für externe Profile, fehlende Launcher und fehlende Menüeinträge
- Erster Dry-Run-Entwurf für `Neuer Browser` mit Name, Startseite und Domains
- Erweiterter Dry-Run-Entwurf mit Vorlage, Menüname, Neue-Tab-URL und Icon-Modus
- Validierter Erstellplan im Dry-Run mit Zielordner, Builder-Vorschau und Warnhinweisen
- Interner Builder-Dry-Run ohne CLI-Dateiausgaben und ohne `--apply`
- Apply-Vorbereitung mit explizitem Bestätigungscode, weiterhin ohne Schreibpfad
- Separater `Apply ausführen`-Pfad über den bestehenden Builder mit Rückgabe von `stdout` und `stderr`
- Keine zusätzliche Paketinstallation durch NetMon für den Preflight erforderlich
- Keine automatische Erstellung oder Entfernung ohne explizite Benutzeraktion im Tab

## Geplante Funktionen

- Inventur
- Erstellen
- Registrieren bestehender Container
- Startmenü-Integration
- Favicon-Icons
- Deinstallation/Cleanup
- Update/Verify

## Getesteter Ansatz für den NetMon-Webbrowser

Am 21.11.2026 lief die vorhandene Firefox-ESR-Basis (140.12.0) in einer
Wegwerf-QEMU-VM ohne externe Netzwerkkarte und ohne Host-Freigaben. Der
Browser lud eine Testseite über Loopback. Am laufenden `firefox-bin` war
der von Bubblewrap erzeugte Mount-Namensraum des Hauptprozesses sichtbar.
Bei einem Firefox-Inhaltsprozess war zusätzlich der interne Seccomp-Filter
aktiv. Das Profil und ein separater Downloadordner waren schreibbar. Eine
Zugriffsprobe mit denselben Sandbox-Freigaben konnte drei künstliche Dateien
für NetMon-Konfiguration, normales Firefox-Profil und SSH weder lesen noch
ändern. Ein zusätzlicher Unix-Socket des Gasts war in der Sandbox unsichtbar.

Mozilla hat für spätere ESR-Ausgaben weitere [Sicherheitskorrekturen](https://www.mozilla.org/en-US/security/known-vulnerabilities/firefox-esr/)
veröffentlicht. Die vorhandene Basis 140.12.0 diente daher als Offline-Testmaterial.
Für einen zweiten Lauf wurde ESR 153.7.0 aus Mozillas Archiv separat bereitgestellt.
Die Signatur der Prüfsummenliste und der SHA-256-Wert des Archivs wurden geprüft.

Mit ESR 153.7.0 bestand der Prototyp auch unter virtuellem Weston/Wayland. Der
Hauptprozess lief im Bubblewrap-Mount-Namensraum und bei einem Inhaltsprozess war
Seccomp aktiv. Die Testdateien waren auch aus dem Dateisystem des laufenden
Hauptprozesses nicht sichtbar. Der zweite Link landete nachweislich im bereits
laufenden NetMon-Profil, während ein separates Firefox-Profil parallel lief.
Dazu wurde ein eigener D-Bus für die Testbrowser verwendet. Ein echter
Testdownload wurde im vorgesehenen Downloadordner gespeichert.

Der Test betraf den Start- und Zugriffsprototyp mit ausschließlich lokalem
Testverkehr. Für die NetMon-Anbindung sind noch Portale und Zwischenablage auf
dem Zorin-/Mint-Desktop, der tatsächliche DNS-/VPN-Weg sowie das Updateverfahren
für bestehende Profile zu prüfen.

## Startcode mit getrenntem Netzwerk

`sandbox.run_link()` startet die separat bereitgestellte Firefox-Binärdatei mit
Bubblewrap unter Wayland. Es bindet ein eigenes Profil und einen Downloadordner
ein. Der Aufrufer stellt die geprüfte Firefox-Basis und den privaten D-Bus bereit.
Bubblewrap, `slirp4netns`, `nsenter` und ein für den Benutzer zugängliches
TUN-Gerät müssen vorhanden sein. Firefox startet erst, wenn das isolierte
IPv4-Netzwerk bereit ist. Fehler gehen an den Aufrufer zurück.

Der geschützte Start benötigt einen Wayland-Socket. In einer reinen X11-Sitzung
meldet NetMon den fehlenden Wayland-Zugang. Wenn **Eigenen Browser aktivieren**
ausgeschaltet ist, öffnet NetMon Weblinks weiterhin im System-Standardbrowser.

Bubblewrap richtet die Benutzerzuordnung für Firefox vor dem Start der
Binärdatei ein. Der Netzwerkhelfer benutzt für seine eigene Sandbox den
Benutzer-Namensraum, dem der Browser-Netzwerk-Namensraum gehört. Beide
Namensräume werden dem Netzwerkhelfer über offene Dateideskriptoren übergeben.
Damit entfällt der zusätzliche `unshare`-Aufruf im AppArmor-Profil des
Browserprozesses.

Auf dem Zorin-Kernel mit aktivem AppArmor-Profil lud der neue Startweg eine
lokale Testseite in einem isolierten Testnetz mit separatem Wayland-Display.
Bei einem Firefox-Inhaltsprozess war Seccomp aktiv. Der Test nutzte ein
temporäres Profil und ein vom Desktop getrenntes Netzwerk.

Im QEMU-Gast ohne externe Netzwerkkarte und Host-Freigaben wurden mit Firefox
ESR 153.7.0 die getrennten Mount- und Netzwerk-Namensräume, ein Hauptprozess
ohne Linux-Capabilities und der interne Seccomp-Filter eines Inhaltsprozesses
geprüft. Die lokale Testseite war per DNS erreichbar. Der zweite Link kam im
laufenden Profil an, erkennbar am bereits gesetzten Cookie. Firefox speicherte
eine Testdatei im eigenen Downloadordner. Eine separate TCP-Probe aus dem
Browser-Namensraum erreichte den Test-Webserver, während der Zugriff über das
Gateway auf den Loopback-Testdienst des Gasts scheiterte.

Der DNS-Proxy von `slirp4netns` benutzt den Resolver des Systems. Die Sperre
gilt für die Gateway-Adresse. LAN-Zugriffe und den tatsächlichen DNS-/VPN-Weg
auf dem Desktop gilt es gesondert zu prüfen.
[Netzwerkoptionen von slirp4netns](https://github.com/rootless-containers/slirp4netns/blob/v1.2.1/slirp4netns.1.md#filtering-connections)

## Sandbox für Secure Browser

Neue Browser aus dem Secure-Browser-Tab verwenden dieselbe Bubblewrap-Sandbox
und zentral verwaltete Firefox-Basis wie der NetmonRoots Browser. Jeder Browser
hat sein eigenes Profil, einen eigenen Downloadordner und seine eigenen
Richtlinien. Die Auswahl im Tab bestimmt weiterhin, ob der Domainfilter aktiv
ist. Bei einem Startfehler bleibt der Browser geschlossen. Eine Aktualisierung
des Starters übernimmt den bereits gewählten Sandbox-Startmodus.

Das NetMon-DEB verlangt `bubblewrap`, `slirp4netns`, `dbus-daemon`, `dbus-bin`
und `util-linux`. Das separate `netmon-web-browser-runtime` wird empfohlen und
liefert die verwaltete Firefox-Basis für die unterstützte Architektur. Bei
lokalen DEBs kann APT beide Pakete gemeinsam installieren, wenn beide Dateien
angegeben werden. Der Tab prüft vor dem Anlegen die Firefox-Basis, die Wayland-
Sitzung und die Sandbox-Werkzeuge einschließlich TUN-Zugriff.

`tools/secure_browser_manager/containers.sandbox-pilot.json` enthält einen
Testbrowser für die NetMonRoots-Website. Die Sandbox benötigt eine Wayland-Sitzung
und die installierte Firefox-Basis unter `/opt/netmon-web-browser/firefox`.
In einer QEMU-VM öffneten zwei Testbrowser mit den Befehlen aus ihren
Desktop-Einträgen parallel ihre jeweils freigegebene lokale Seite. Eine
Weiterleitung auf eine gesperrte Domain wurde abgefangen. Der erste Browser
speicherte eine Testdatei im eigenen Downloadordner. Die Testdatei im
Home-Verzeichnis des Gasts lag außerhalb seines sichtbaren Dateisystems.

Vor der Umstellung eines Bestandsprofils prüfen wir auf dem Desktop insbesondere
Dateiauswahl, Anmeldungen, Domain-Freigaben und den DNS-/VPN-Weg.

### Einen bestehenden Secure Browser umstellen

Firefox für den ausgewählten Container schließen. Aus dem NetMon-Projektordner
startet dieser Aufruf eine Vorschau für genau den angegebenen Container.

```bash
python3 -EsB -m netmon.modules.secure_browser.container_migration "/absoluter/Pfad/zum/Container"
```

Mit `--apply` sichert das Werkzeug das interne Profil und die bisherigen
Startdateien als privates Archiv im `backups/`-Ordner des Containers. Erst
nach erfolgreicher Sicherung ersetzt es `start.sh`. Die Umstellung prüft die
Firefox-Profilsperre, die Firefox-Version und die Übereinstimmung der beiden
Policy-Dateien. Änderungen der Startdatei während der Sicherung brechen den
Vorgang ab. Der bestehende Desktop-Eintrag verweist weiter auf `start.sh`.
Das Archiv enthält die bisherige Startdatei und den Profilstand vor dem Wechsel.

## Anbindung an NetMon

Unter **Einstellungen → Allgemein → Start & System** steht direkt unter dem
Klickton die Option **Eigenen Browser aktivieren**. Sie ist standardmäßig aus
und wird beim Umschalten gespeichert. Aktiviert steuert sie externe Weblinks
aus NetMon, den Link-Slots, der Linux-Hilfe und Radio. Bei einem Startfehler
zeigt NetMon eine Meldung und der Link bleibt geschlossen.

NetMon startet pro Browserinstanz einen eigenen D-Bus und hält das Profil in
`web-browser/profile` unter `XDG_STATE_HOME/netmon` offen. Bei fehlendem
`XDG_STATE_HOME` liegt es unter `~/.local/state/netmon`. Der Downloadordner
`web-browser/downloads` liegt daneben. NetMon und eigenständiges Radio geben
Weblinks über einen privaten Unix-Socket an den Prozess weiter, der das Profil
gerade hält. Der Socket prüft die Linux-Benutzer-ID und nimmt nur HTTP(S)-Links
an. Die Bestätigung folgt auf die Linkübergabe an Firefox. Schließt der erste
Prozess, kann der andere beim nächsten Klick dasselbe Profil öffnen.

Im Menü **Lesezeichen** ist die Projektwebsite als **NetMonRoots** hinterlegt.

Über den Browser-Tabs erscheint links das NetMon-Symbol neben der Beschriftung
**NetmonRoots Browser**. Das Symbol ist 48 Pixel groß. Rechts zeigt Firefox
die eigenen Knöpfe zum Minimieren, Maximieren beziehungsweise Wiederherstellen
und Schließen. In der Wayland-VM waren alle drei auch bei einem GTK-Layout
sichtbar, das ursprünglich nur den Schließen-Knopf anzeigte. NetMon bindet das
Stylesheet und das Symbol für diesen Browser schreibgeschützt ein.

Der Secure-Browser-Builder erzeugt die Richtlinien für die dedizierte
Instanz. Firefox-Telemetrie, Studien und der Passwortmanager sind deaktiviert.
DNS-over-HTTPS ist deaktiviert, damit der Browser den vorgesehenen System-DNS
über den Netzwerkhelfer nutzt. HTTPS-Only ist standardmäßig eingeschaltet und
kann in Firefox umgestellt werden. Der Tracking-Schutz steht auf „Streng“ mit
fest aktivierten Firefox-Kompatibilitätsausnahmen. DNS-Vorabfragen sind abgeschaltet.
Die Datei wird nur in der Browser-Sandbox unter
`/etc/firefox/policies/policies.json` eingebunden.
[Firefox-Richtlinien unter Linux](https://firefox-admin-docs.mozilla.org/guides/policies-configuration/)

In der abgeschotteten QEMU-VM legte die Sitzungsverwaltung den eigenen D-Bus
an. Firefox bekam die Richtliniendatei eingebunden, öffnete weitere Links im
laufenden Profil und speicherte die Testdatei im eigenen Downloadordner. Beim
Beenden räumte NetMon den privaten Socket auf. Der Socket des separaten
Test-Busses blieb bestehen.

Im nächsten VM-Lauf übergab ein zweiter Prozess den Weblink an das bereits
laufende Profil. Der Testserver sah beim zweiten Link das zuvor gesetzte Cookie
und Firefox behielt dieselbe Prozess-ID. Nach dem Beenden startete der nächste
Prozess mit demselben Profil und öffnete eine weitere Testseite.

Zur Nutzung muss eine separat bereitgestellte und gepflegte Firefox-ESR-Basis
unter `/opt/netmon-web-browser/firefox` liegen. Die Dateien und ihre
Verzeichnisse müssen root gehören und vor Schreibzugriffen anderer Benutzer
geschützt sein. Der Startweg braucht zusätzlich `dbus-daemon`, `dbus-send` und
`setpriv`. Der Inhalt eines lokalen amd64-Entwicklungspakets aus dem signierten
deutschen Firefox-ESR-153.7.0-Archiv lief in der VM am vorgesehenen `/opt`-Pfad.
Die Systeminstallation, das Updateverfahren und die Abnahme auf dem realen
Desktop stehen noch aus.
