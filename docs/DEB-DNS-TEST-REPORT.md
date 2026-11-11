# NetMon V4 – DEB-Testpaket, 30.10.2026

## Ergebnis

Gebaut, statisch geprüft und als entpackter Payload isoliert getestet.
Keine Installation, Produktfreigabe, Commits oder Pushes.

| Merkmal | Wert |
| --- | --- |
| Paketdatei | `/dev-lab/projects/netmon-v4-dns-integration-test/dist/netmon_1.1.21~v4dnstest20261030.2_all.deb` |
| Paketname | `netmon` |
| Version | `1.1.21~v4dnstest20261030.2` |
| Architektur | `all` |
| Größe | 201854234 Bytes, rund 193 MiB |
| SHA-256 | `0e39f579a9ecc63ade9f4234f1a4a7dca002f37995ab4b01fb6f3a0bede2b226` |

Desktopname **NetMon V4 DNS Test**, Control-Description, Changelog und
`TEST-BUILD.md` kennzeichnen den Teststand. Die interne Anwendungsversion
bleibt `1.1.21`. Gleiche Paketidentität und Installationspfade bedeuten:
**keine parallele Installation neben dem Produktpaket**. Die Testversion
sortiert durch `~` unter `1.1.21`, mit `dpkg --compare-versions` geprüft.
Es gibt keine Freigabesignatur.

## Gezielte Änderungen

Der bestehende Builder `scripts/build_netmon_deb.sh` verwendet weiterhin
`dpkg-deb --root-owner-group`; keine neue Build-Infrastruktur.

1. Optionaler Testmodus `--test-version 1.1.21~v4dnstestYYYYMMDD.N`, passende
   Testkennzeichnung und Verweigerung beim Überschreiben existierender Pakete.
2. Kritischer bisheriger Nebenpfad: `postinst`/`prerm` konnten aus
   `/var/lib/netmon/install-dns-nm.state` NM-Profile verändern/reaktivieren,
   einschließlich DHCP-DNS-Freigaben. Diese Wiederherstellung entfällt;
   der Legacy-Zustand wird weder gelesen noch entfernt. Vorher rot reproduziert.
3. Kritischer Deinstaller-Nebenpfad: `reset_netmon_dns_changes()` konnte
   `ignore-auto-dns no` setzen, Profile reaktivieren, den DoT-Drop-in löschen und
   Resolver/NM neu starten. Die Funktion verweigert jetzt mit Rückgabecode 1.
   Die auswählbare DNS-Reset-Frage entfällt; die Zusammenfassung zeigt ihn als
   deaktiviert. Vorher mit privater Datei und Befehlsattrappen rot reproduziert.
4. Testmodus: nur Python-Laufzeit zwingend; Netzwerk-/Firewall-/Feature-Werkzeuge
   einschließlich `udisks2`, `cryptsetup`, `sudo` in `Suggests`, ohne `Recommends`.
   Das Paket fordert keine automatische Installation solcher Dienste an.
   Der Standardmodus behält die bisherigen Feature-Abhängigkeiten; Python wird
   passend zum Quelltext auf >= 3.11 begrenzt.
5. Fehlendes `tools/__init__.py` eingebunden. doc-base-Registrierung nur bei
   tatsächlich vorhandener optionaler HTML- und PDF-Dokumentation.

Implementierung geändert: Builder und `scripts/netmon_uninstall_menu.sh`.
Regressionen geändert: `tests/test_deb_postinst_security.py`,
`tests/test_netmon_deb_packaging.py`, `tests/test_netmon_uninstaller.py`.
Vorherstände und vollständiger Diff: `integration-evidence/deb-test-20261030/`.

F1-/F6-Produktcode, privilegierte Helfer, Teststarter, Isolation/Guards und alle
48 Fälle bleiben bytegleich zum Auftragsbeginn. Original und DNS-/KS48-Archive:
56024 Einträge gegen vorhandene Referenz unverändert, einschließlich Original-
Index SHA-256 `8d318f997b4dfe5ae97cd51e1eeed455ed53891afaca7655004201c775098ef3`.
Kein Git-Befehl oder KS48-Runnerstart wurde benötigt.

Zwischenbuild `.1` ist wegen des danach gefundenen Deinstaller-Nebenpfads
**verworfen**, unter `dist/superseded-deb-test-20261030/` aufbewahrt und kein
Installationskandidat. Historischer SHA-256:
`0de1ca09161e2fab1b61e6db52fef600c8f8a15419fd83d1049fe1f6b6547f3a`.

## Paketprüfung

`Depends: python3 (>= 3.11), python3-tk, python3-psutil, python3-pil,
python3-pil.imagetk`. Keine virtuelle Umgebung/Entwicklungsabhängigkeiten im DEB.
Keine nativen ELF-Dateien. Alle verpackten Python-Dateien bestehen die
3.11-Grammatikprüfung; Laufzeittests mit Python 3.12.3, keine vollständige
3.11-Laufzeitmatrix.

Tatsächlicher Control-/Data-Tar geprüft: **204 Einträge, 167 Dateien**, alle
`root:root`, Verzeichnisse 0755, Dateien 0644 oder ausdrücklich ausführbar 0755.
Keine Setuid-/Setgid-Bits, Gruppen-/Fremdschreibrechte, Links/Spezialdateien,
Git-/Cache-/Credential-Verzeichnisse, Bytecode, `.venv`, sudoers, Polkit-Regeln
oder Dienstunits. `md5sums`: alle 167 Dateien vollständig und korrekt.

Python: `/usr/lib/netmon`; Starter/Deinstaller: `/usr/bin`; Ressourcen/Desktop/
Icons: `/usr/share`; Dokumentation: `/usr/share/doc/netmon`.
Starter: `/usr/bin/python3 -m netmon` mit `/usr/lib/netmon` im Suchpfad.
Desktop- und Shell-Syntaxprüfungen bestanden. Zwei Desktop-Hinweise zu mehreren
Hauptkategorien können doppelte Menüeinträge bedeuten.
Lintian: Exit 0, keine Fehler, eine Warnung `maintainer-script-empty [prerm]`
für das absichtlich wirkungslose Entfernungsskript.

DNS-Module/Ressourcen im echten Paket gegen 121 Quelldateien sowie 9 zusätzliche
Launcher-/Tool-/Asset-Dateien gehasht; Deinstaller ebenfalls quellengleich.
Bestehende Ausnahmen: `netmon/dark_test.py` ist ein Entwicklungsstarter;
`netmon/linux-befehle.csv` wird aus der umfangreicheren kanonischen Tool-CSV
installiert; Entwickler-README/Testdateien entfallen. Vorhandene Log-Bilder und
Code-the-Classics-Ressourcen bleiben enthalten und erklären den Großteil der
Paketgröße. Generierte optionale PDF-/HTML-Dokumentation liegt hier nicht vor.

| Maintainer-Skript | Verhalten |
| --- | --- |
| `preinst` | Nicht vorhanden |
| `postinst` | Optional Desktop-Datenbank aktualisieren; Log-Bilder nach `/etc/skel/.../NetMon/Log-Pics` kopieren, ohne vorhandene Dateien zu ersetzen |
| `prerm` | Wirkungsloser erfolgreicher Abschluss; keine DNS-Rücksetzung |
| `postrm` | Nicht vorhanden |

Keine Änderungen an DNS-, Resolver-, Firewall- oder Netzwerkkonfiguration durch
diese Skripte. Der vorhandene `/etc/skel`-Seiteneffekt bleibt bestehen.
Legacy-DNS-Zustand und bestehende DNS-Einstellungen bleiben auch bei Entfernung
erhalten; eine manuelle Bereinigung benötigt eine separate Entscheidung.

Privilegierte Helfer: normale root-eigene Dateien ohne Setuid/neue Rechtefreigabe;
Bootstrap-, Eigentümer-, Pfad- und Payload-Prüfungen unverändert. Positive
Root-Ausführung nicht getestet. Anwendung/Deinstaller haben weiterhin explizite
administrative Funktionen, etwa Firewall-/VPN-Aktionen nach Auswahl. Diese wurden
nicht unisoliert gestartet; sie sind kein passiver Paket-Lebenszyklus.

## Testergebnisse

| Abschließender Lauf | Bestanden | Fehler | Übersprungen |
| --- | ---: | ---: | ---: |
| Import-/Modulfälle | 63 | 0 | 0 |
| Gezielte DNS-Unit-Fälle | 23 | 0 | 0 |
| DNS-Integration | 258 | 0 | 0 |
| Übernommene DNS-Fälle | 48 | 0 | 0 |
| Angrenzende Regressionen | 626 | 0 | 0 |
| GUI/Startup | 23 | 0 | 0 |
| Paketierung/Deinstallation zusätzlich | 57 | 0 | 0 |

Angeforderter unveränderter Starter: **1041 Ausführungen / 1017 verschiedene IDs**.
Mit den 57 zusätzlichen, nicht überlappenden Paketierungsfällen:
**1098 Ausführungen / 1074 verschiedene IDs**. Die bestehende DNS-Unit-Auswahl
wählt 66 Fälle per Filter ab; diese sind keine übersprungenen/fehlgeschlagenen Tests.

Getrennt archivierte erwartete rote Reproduktionen vor Korrektur:
`legacy-before` und `uninstaller-before`, je 1 fehlgeschlagen.
Ein Wiederholungsaufruf in eine bereits belegte Ausgabeablage wurde vor Tests
verweigert; die vorhandene rote Aufzeichnung blieb erhalten. Keine dieser
historischen Aufzeichnungen ist ein Fehler im abschließenden Lauf.

Entpackter Payload zusätzlich nicht-root mit privatem Bubblewrap-Netz-/PID-/IPC-
Namespace ohne Host-Dienstsockets geprüft: Paketimporte/CLI-Hilfe, F1 mit physischem/
globalem DNS, F6 an öffentlicher/privater Service-Methode, Controller und
Auto-Restore sowie Verweigerung des tatsächlich verpackten Deinstaller-DNS-Resets
mit erhaltener privater DNS-Datei. Python-Probe verbietet Netzwerk-/Unterprozess-
Aktionen. Der privilegierte Helfer verweigert erwartungsgemäß nicht-root.

**Dies ist keine Installation**, sondern eine Prüfung nach `dpkg-deb --raw-extract`.
Native Debian-Abhängigkeiten psutil/Pillow/ImageTk fehlen auf dem Host. Die Probe
nutzt nur lesend bestehende kopierte `.venv`-Site-Packages als Abhängigkeitssurrogat;
Anwendungsmodule kommen nachweislich aus dem Paket. Kein vollständig installiertes
Gast-Debian/Ubuntu mit eigener Paketdatenbank und nativen Abhängigkeiten verwendet.

**Nicht ausgeführt:** Hostinstallation, tatsächliche Installation/Upgrade/Remove/
Purge, Abhängigkeitsinstallation, positiver installierter Root-Helfer-Test, reale
DNS-/Firewall-/VPN-/Resolvertests, unisolierter Anwendungsstart.

Qualität: Bash-Syntax bestanden; Builder-Shellcheck ohne Befund. Deinstaller:
dieselben 7 vorbestehenden SC2034/SC2059-Befunde, keine zusätzlichen.
Black-Einzeldateiprüfungen und Ruff der drei betroffenen Python-Testdateien bestanden.
Hängende Black-Mehrdateiprüfungen wurden gezielt beendet und durch erfolgreiche
Einzeldateiprüfungen ersetzt; andere Prozesse blieben unangetastet.

## Reproduktion und Nachweise

```sh
cd /dev-lab/projects/netmon-v4-dns-integration-test
python3 -B scripts/test_dns_integration.py all
python3 -B tests/run_isolated_suite.py -q -rs --tb=short \
  tests/test_netmon_deb_packaging.py tests/test_deb_postinst_security.py \
  tests/test_netmon_uninstaller.py
dpkg-deb --info dist/netmon_1.1.21~v4dnstest20261030.2_all.deb
dpkg-deb --contents dist/netmon_1.1.21~v4dnstest20261030.2_all.deb
sha256sum dist/netmon_1.1.21~v4dnstest20261030.2_all.deb
```

Build: `DPKG_DEB_THREADS_MAX=2 bash scripts/build_netmon_deb.sh --test-version
1.1.21~v4dnstest20261030.2`. Erneuter Build verweigert die existierende Datei;
für einen weiteren Build eine neue Testnummer verwenden. Zeitstempel in Paket/
Changelog verhindern die Zusage byteidentischer Neubauten. Der Hash bindet das
hier tatsächlich geprüfte Artefakt.

`integration-evidence/deb-test-20261030/`: Build-/Test-/Lintian-Logs, JUnit,
Inventar, Hashbindungen, Vorherstände/Diff und verwendete Prüfskripte. Für einen
anderen temporären Prüfpfad deren Konstanten `WORK`, `ROOT`, `DEB`/`EXTRACTED`
anpassen. Proben benötigen die vorhandene dokumentierte Bubblewrap-/Xvfb-
Testumgebung. Die bestehende `INTEGRATION-SHA256SUMS.txt` wird ergänzt;
keine neue Freigabe oder Gate-Datei.

## Späterer kontrollierter Installationstest

1. Erst nach ausdrücklicher Projektentscheidung: wegwerfbare Debian-/Ubuntu-VM
   mit Snapshot/eigener Paketdatenbank, keine Host-Dienstsockets oder produktiven
   Netzadapter, private Resolver/VPN-Gegenstelle vorbereiten.
2. SHA prüfen, vorhandene Paketversion/Konfiguration erfassen. Eine frische VM
   ohne NetMon bevorzugen: Alte Maintainer-Skripte eines bereits installierten
   Pakets können beim Upgrade laufen und werden durch dieses DEB nicht rückwirkend
   sicher. Gleicher Paketname bedeutet Ersatz statt paralleler Installation.
3. Paketmanager-Auflösung zunächst simulieren; Python-Abhängigkeiten gezielt im
   Gast bereitstellen. Optionale Dienste separat entscheiden, nicht pauschal alle
   `Suggests` installieren.
4. Installation, Desktopstart als normaler Benutzer, Helper-Eigentümer sowie
   Entfernung/Purge im Gast prüfen. Netzwerkzustand vorher/nachher vergleichen;
   Lebenszyklus muss ohne DNS-/Firewalländerung bleiben. `/etc/skel`-Bilder und
   bewusst erhaltenen Legacy-Zustand erfassen.
5. DHCP-/ISP-Freigaben und automatische ISP-Restores müssen verweigern. Echte
   manuelle DNS-/VPN-/Firewallaktionen sind ein nachgelagerter praktischer Test
   mit eigener Freigabe und Snapshot-Rückkehrmöglichkeit.

Nach Paketbau und Prüfung stoppen. Installation bleibt ausstehend.
