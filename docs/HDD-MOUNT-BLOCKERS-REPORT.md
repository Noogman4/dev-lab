# NetMon V4 – Swapfile-fstab-Blockade und lesende Busy-Diagnose

Stand: 31.10.2026. Ausschließlich Arbeitskopie
`/dev-lab/projects/netmon-v4-dns-integration-test/` geändert.

Die unabhängig bestätigte Swapfile-Blockade ist gezielt korrigiert und mit
synthetischen Geräten getestet. **Eine vollständige Mount-Freigabe auf dem
Rechner ist weiterhin nicht nachgewiesen:** Ein weiterer fstab-Quellpfad ist
in der aktuellen Prozesssicht nicht auflösbar. Der Schutz verweigert dort
weiterhin. Es wurde weder tatsächlich gemountet/ausgehängt/entsperrt noch
`/etc/fstab` geändert. Kein Paketbau, keine Installation, keine Commits/Pushes.

## Ursache und Sicherheitsargument

`_check_system_fstab()` leitete jede nicht ausdrücklich virtuelle Quelle an
`_fstab_block_source()` weiter. Diese Funktion verlangt bewusst ein verifiziertes
Blockgerät. Ein regulärer `/swapfile none swap ...`-Eintrag scheiterte deshalb
mit `System fstab source is not a block device.` und blockierte auch andere
Geräte. Die neue positive Regression scheiterte vor der Korrektur genau dort.

Die Blockgeräteprüfung bleibt unverändert. Ausschließlich eine reguläre Datei
mit `fstype=swap` erhält eine eigene Beweiskette:

1. Der bereits größenbegrenzt, root-eigen, unveränderlich gelesene fstab-Inhalt
   muss zur findmnt-Zeile passen: identische dekodierte Quelle, Ziel `none`, Typ
   `swap`, Dump-/Pass-Werte nur `0`. Zugelassene Optionen: `sw`, `defaults`,
   `nofail`, `noauto`, `discard`, `discard=once`, `discard=pages`, `pri=<Ganzzahl>`.
   Doppelte Optionsschlüssel und doppelte Swapfile-Zeilen werden verweigert.
2. Absoluter kanonischer Pfad ohne `.`/`..`, leere Komponenten, Steuerzeichen
   oder `/dev`-Namensraum. Komponentenweises `O_PATH|O_NOFOLLOW`, für Eltern
   zusätzlich `O_DIRECTORY`, jeweils relativ zum noch geöffneten Eltern-FD.
   Alle Komponenten root-eigen, kein Gruppen-/Fremdschreibrecht. Die letzte
   Komponente muss regulär, nur für root zugänglich, mindestens 4096 Bytes groß
   und einfach verlinkt sein. Es werden keine Swap-Inhalte geöffnet/gelesen.
3. Die feste Kerneldatei `/proc/swaps` muss genau diesen Pfad eindeutig als
   aktiven Typ `file` mit plausibler Größe bestätigen. Ein beliebiger als
   `swap` deklarierter Dateipfad reicht ausdrücklich nicht.
4. `st_dev` wird gegen das aktuelle lsblk-Inventar und die bestehende vollständige
   Blockgeräteprüfung gebunden. Unklare/fehlende UUIDs, Widersprüche und
   unzulässige Gerätevorfahren bleiben gesperrt. Das Trägergerät darf weder
   Gerätenummer noch UUID der ausgewählten Dateisystemquelle haben.
5. Datei-Metadaten, Aktivierungsidentität und Trägergerät werden gegen ein
   frisches Inventar erneut geprüft; anschließend unveränderte fstab und die
   bisherige Geräte-Revalidierung unmittelbar vor dem UDisks-Aufruf.
   Der veränderliche Swap-Zähler `Used` gehört nicht zur Identität.

Damit ist die zugelassene Quelle eine bestätigte Datei auf einem anderen
Dateisystem, kein möglicher Alias des ausgewählten Blockgeräts. Root-geschützte
Pfadkomponenten verhindern das Umhängen durch den unprivilegierten Aufrufer.
Die bisherige Vertrauensgrenze – vertrauenswürdiger Kernel, Systemwerkzeuge und
root-administrierte Systemkonfiguration – bleibt bestehen. Das ist keine
atomare Transaktion gegenüber gleichzeitig handelnden Administratoren.
Sichere Optionen bleiben `nodev,nosuid,noexec`; kein Root-Mount-Fallback,
keine zusätzlichen Privilegien oder benutzerbestimmten Mount-Optionen.

**Bewusste Grenzen:** Inaktive Swapdateien erhalten keine Ausnahme; insbesondere
wird kein Swap aktiviert und kein privilegierter Header-Leser ergänzt.
Symlinks/Hardlinks, benutzerbeschreibbare Vorfahren, großzügigere Dateirechte,
unbekannte Optionen und nicht eindeutig auf ein Blockgerät abbildbare
Dateisysteme bleiben gesperrt. Das betrifft beispielsweise nicht beweisbar
zuordenbare anonyme/mehrteilige Dateisysteme. Alle übrigen fstab-Quellen müssen
weiterhin die bisherige Prüfung bestehen.

Grundlagen: [`/proc/swaps` beschreibt aktive Swapbereiche](https://man7.org/linux/man-pages/man5/proc_swaps.5.html);
[`O_PATH` ermöglicht Metadatenzugriff ohne Lesen des Dateiinhalts](https://man7.org/linux/man-pages/man2/open.2.html).

## Lesender Vergleich am Rechner

Prüfung als UID 1000, ohne sudo: `/swapfile` ist root-eigen, Modus 0600,
ein Hardlink, aktiver Kerneltyp `file`, Größe 8388604 KiB, Trägergerät `259:2`.
Die separate neue Swapfile-Unterprüfung besteht für Slot 2 und Slot 3 mit den
echten Metadaten. Der Ablauf sperrt Mount/Unlock ausdrücklich und erlaubt nur
die zwei festen lsblk-/findmnt-Leseabfragen.

Die vollständige Prüfung verweigert beide Slots dagegen weiterhin wegen
`/dev/disk/by-uuid/8f6bf0dc-a7cb-41b7-a8be-293a345da986` (`FileNotFoundError`).
Das UUID-Aliasverzeichnis selbst ist sichtbar. Ob der betreffende Datenträger
fehlt, ein fstab-Rest besteht oder die Prozesssicht eingeschränkt ist, wurde
nicht abschließend festgestellt. Keine automatische Korrektur, kein Entfernen
dieses Eintrags und kein Umgehen seiner Prüfung. Slot 1 bleibt ein geschlossenes
LUKS-Gerät ohne freigegebene Dateisystemquelle; kein Unlock wurde versucht.

## `target is busy`: kein nachgewiesener NetMon-Codefehler

Die vorhandenen historischen Logs dokumentieren eine tatsächliche
UDisks-`DeviceBusy`-Verweigerung. Ein geöffnetes Dateimanagerfenster ist laut
Nutzerhinweis eine plausible Ursache, durch diese Logs aber nicht bewiesen.
Der damalige verursachende Prozess lässt sich daraus nicht rückwirkend bestimmen.
Die Verweigerung selbst wird nicht als nachgewiesener NetMon-Codefehler bewertet.

Ergänzt wurde nur Diagnose nach einer fehlgeschlagenen Aktion mit Busy-Meldung:
lesbare `/proc/PID/cwd`- und FD-Verweise im gleichen Mount-Namensraum,
PID/Prozessname/Bezugstyp sowie abhängige Mounts anhand der Eltern-IDs in
`/proc/self/mountinfo`. Exakte Pfadgrenzen vermeiden Treffer auf ähnlich
benannten Nachbarverzeichnissen. Geräte-/Mountbindung wird davor/danach geprüft;
bei Wechsel werden Hinweise verworfen. Ergebnisse erscheinen im vorhandenen
Aktionsstatus und Log, deutsch/englisch übersetzt.

Es erfolgen keine zusätzlichen mutierenden Befehle, kein Prozesssignal, keine
Autorisierungserweiterung, kein Force-/Lazy-Unmount. Die bisherigen vier
Unmount-Versuche und der LUKS-Close-Ablauf bleiben unverändert. Nach Erfolg gibt
es keinen Prozessscan. Die Ergänzung macht ein belegtes Laufwerk nicht frei.

Die Anzeige bezeichnet Ergebnisse stets als unvollständige Momentaufnahme:
höchstens 2048 Prozesse, 512 FDs je Prozess, 20 Prozesshinweise, 64 abhängige
Mounts, 1 MiB Mounttabelle und ungefähr zwei Sekunden Prozesssuche. Das Zeitbudget
wird zwischen Leseoperationen geprüft und ist keine harte IO-Zeitgarantie.
Andere Namensräume, fehlende Leserechte, reine Speicherabbildungen, alternative
Bind-Mount-Pfade, Kernelbezüge und Prozesswechsel können Hinweise verbergen.
Keine Treffer bedeuten ausdrücklich nicht „Laufwerk unbenutzt“.
Die [Kernel-Dokumentation zu `/proc`](https://www.kernel.org/doc/html/latest/filesystems/proc.html)
beschreibt diese Prozess-/Mountinformationen und die Zugriffsgrenzen.

## Änderung und Tests

Produktdateien: `netmon/services/hdd_mount_service.py`,
`netmon/features/hdd_controller.py`, fünf zusätzliche Schlüssel je
`netmon/lang/de.json` und `en.json`. Bestehende Sprachdatei-Einträge einschließlich
vorhandener doppelter Schlüssel sind bytegetreu erhalten.

Neue Tests: `tests/test_hdd_swapfile_policy.py` (36 Fälle),
`tests/test_hdd_busy_diagnostics.py` (15 Fälle). Der bisherige Feedbacktest für
eine ungeschützte Schein-Swapdatei bleibt ablehnend; nur die erwartete spezifische
Fehlerbeschreibung wurde angepasst. Bestehende Gerätewechsel-/Unmount-/LUKS-Tests
bleiben unverändert.

| Abschließende Prüfung | Bestanden | Fehlgeschlagen/Fehler | Übersprungen |
| --- | ---: | ---: | ---: |
| HDD inkl. 51 neuer Fälle und frühere GUI-/About-Regressionen | 392 | 0 | 0 |
| V4 Import-/Modulfälle | 63 | 0 | 0 |
| V4 gezielte DNS-Unit-Fälle | 23 | 0 | 0 |
| V4 DNS-Integration | 258 | 0 | 0 |
| Übernommene DNS-Testfälle | 48 | 0 | 0 |
| V4 angrenzende Regressionen | 626 | 0 | 0 |
| V4 GUI/Startup | 23 | 0 | 0 |

V4 insgesamt **1041 Ausführungen / 1017 unterschiedliche Test-IDs**.
Alle Ausführungen über den unveränderten Bubblewrap-/Xvfb-Teststarter, private
Netz-/PID-/IPC-Umgebung und bestehende Hostaktions-Guards. Der bestehende DNS-
Unit-Filter wählt 66 Fälle ab; dies sind keine übersprungenen oder fehlgeschlagenen
Tests. Black, Ruff und Syntaxprüfung aller fünf betroffenen Python-Dateien
bestanden. Keine zusätzlichen Abhängigkeiten.

Historisch getrennt erhalten: erwartete rote Swapfile-Reproduktion (1 Fehler),
erster neuer Testlauf mit fehlendem Fixture-Import (241 bestanden, 6 Setupfehler),
danach 247 bestanden. Der Fixture-Import wurde korrigiert. Ein erster Ruff-Aufruf
scheiterte am schreibgeschützten Cachepfad; Prüfung ohne Cache bestanden. Diese
Zwischenstände sind keine Fehler im abschließenden Lauf.

**Nicht ausgeführt:** echte Mount-/Unmount-/Unlock-/Close-Aktionen, neue
Host-GUI-Starts, Änderungen an fstab/DNS/Firewall/VPN, Paketbau oder Installation.
Keine erneute vollständige Repository-Testmatrix außerhalb der genannten Auswahl.

## Integrität und Reproduktion

Alle 56024 aufgezeichneten Original-/Archiv-Einträge gegen die vorhandene
Referenz `integration-evidence/original-after.json` stimmen überein. Die aktuelle
Arbeitskopie wurde gegen 288 vor Beginn erfasste Quell-/Test-/Skriptdateien
geprüft: nur die fünf genannten bestehenden Dateien plus zwei neue Tests geändert.
Alle übrigen alten Funktions-/Klassendefinitionen im Service (15) und Controller
(60) sind AST-identisch, ausgenommen die ausdrücklich erweiterten
`_check_system_fstab()` und `hdd_unmount_async()`. Letztere enthält ausschließlich
die zusätzliche lesende Diagnose im bisherigen Fehlerzweig. F1/F6, die 48 Fälle,
Isolationsstarter, Paketierung, Original und KS48 bleiben unangetastet.

| Datei | SHA-256 nach Korrektur |
| --- | --- |
| `netmon/services/hdd_mount_service.py` | `e064db8d092c4636712e6123a1e3dbebeab47e613cb4c086fcf01364fbc36c6e` |
| `netmon/features/hdd_controller.py` | `da2cf8c97cc7a8b36f5ca3aea8197a63351c17b6389033de36728d6644242f3f` |
| Neues Swapfile-Testmodul | `3da731f20373e95a0c04166678887ad168000f6c2b9082ef571c09fba59da9c5` |
| Neues Busy-Testmodul | `27e83fbf819a22efd035c73d1b3a227d31d1889c0047e54eddefc83676e11ff0` |

Das bestehende `.2`-DEB bleibt bei SHA-256
`0e39f579a9ecc63ade9f4234f1a4a7dca002f37995ab4b01fb6f3a0bede2b226`.
Die installierte Service-Datei bleibt bei
`3523edc2c7cd3bc2988c88bef4d39570819089c9d781a296cb2cd0270a793da0`.
`/etc/fstab` bleibt bei
`d3a3efb8988b07d0011769a12cfa9132da9717f75830fdb6bf4f9a0ee3d6e081`.
Installierter Teststand und vorhandenes DEB enthalten diese Korrekturen nicht.

Nachweise: `integration-evidence/hdd-mount-blockers-20261031/` enthält
Vorherstände, Diff, JUnit, Test-/Qualitätsprotokolle, Hash-/AST-Prüfung,
Archiverhaltungsprüfung und den ausschließlich lesenden Host-Prüfablauf.
Die vorhandene `INTEGRATION-SHA256SUMS.txt` wird aktualisiert; es entsteht kein
Gate-/Freigabeverfahren. Temporäre Prüfpfade in den Nachweisskripten bei einer
erneuten Ausführung anpassen; Ausgabeordner müssen jeweils neu sein.

```sh
cd /dev-lab/projects/netmon-v4-dns-integration-test
python3 -B tests/run_isolated_suite.py -q -rs --tb=short \
  tests/test_hdd_swapfile_policy.py tests/test_hdd_busy_diagnostics.py \
  tests/test_hdd_action_feedback.py tests/test_netmon_hdd.py \
  tests/test_hdd_mount_security.py tests/test_hdd_review_regressions.py \
  tests/test_gui_display_findings.py tests/test_netmon_about.py
python3 -B scripts/test_dns_integration.py all
sha256sum -c INTEGRATION-SHA256SUMS.txt
```

Für den späteren realen Test: zunächst den weiteren nicht auflösbaren fstab-
Eintrag lesend klären; keine automatische Bereinigung. Danach separat einen
Stand mit dieser Korrektur bereitstellen und ein konkretes Testlaufwerk mit
unveränderlicher Identität ausdrücklich freigeben. Vor dem normalen Unmount
Dateimanagerfenster und andere bekannte Nutzer dieses Laufwerks regulär
schließen. Bei Busy Hinweise prüfen; fehlende Hinweise sind keine Freigabe.
Eine echte Mount-/Unmount-Erprobung und jede Paketänderung bleiben ausstehend.
