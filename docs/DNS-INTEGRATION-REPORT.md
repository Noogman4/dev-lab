# NetMon V4 – DNS-Integration und wiederholbare Entwicklungstests

> Historischer Integrationsstand vor der F1-/F6-Korrektur. Aktueller Stand:
> [F1-/F6-Abschlussbericht](DNS-F1-F6-REPORT.md). Die folgenden Laufzahlen
> und damaligen offenen Befunde werden als historische Nachweise erhalten.

30.10.2026, Europe/Berlin. Arbeitskopie:
`/dev-lab/projects/netmon-v4-dns-integration-test/`.

## Ergebnis

Die Kopie enthält die vorhandenen Produktfunktionen, den zuvor nicht
integrierten V1–V3-DNS-Patchbestand, die erforderlichen vorhandenen
Schreibsicherheitskorrekturen und normale isolierte pytest-Eingänge.
Die 48 bisherigen KS48-Fälle sind vollständig und bytegleich erhalten.
Kein KS48-Einmalrunner, Gate oder Autorisierungszustand ist Laufzeitabhängigkeit.

**Die Projektverantwortliche hat die Übernahme von V3 einschließlich seiner
bekannten Lücken ausschließlich in diese isolierte Kopie zur Fehlerreproduktion
ausdrücklich gewählt.** F1 und F6 sind deshalb keine behobenen Findings.
Dieser Bericht macht keinen Schutzclaim für reales DNS oder Kernelpakete.

Die Kopie wurde unter `/tmp/netmon-v4-dns-integration-test/` vorbereitet und
geprüft und anschließend an den gewünschten Zielpfad übertragen.
Produkt-/Testquellen und Ressourcen sind echte Kopien, keine Hardlinks zum
Original. `.venv` wurde kopiert und ihre Textlauncher auf den Zielpfad
umgestellt; keine Paketinstallation. Python und GUI-/Isolationstools bleiben
die vorhandenen Systemwerkzeuge. Gitmetadaten, Backups/Buildablagen,
Credentialverzeichnisse, Bytecodecaches und alte KS48-Zustände wurden nicht
als aktive Bestandteile übernommen. Das ursprüngliche Repository und alle
bisherigen KS48-/DNS-Artefakte bleiben an Ort und Stelle erhalten.

## Integrationsübersicht

| Bestand | Kategorie | Behandlung |
|---|---|---|
| DNSControlService, DNS-/DoT-Controller, DNS-Tab, DNSSEC/Guard-Grundfunktionen | BEREITS INTEGRIERT | Vorhandenen Produktbaum kopiert; keine zweite Grundimplementierung. |
| KS-P1: Killswitch beim Start nicht automatisch abschalten | BEREITS INTEGRIERT | Exaktes aktuelles Methodensegment erhalten; V3 darf diese Korrektur nicht zurücknehmen. |
| KP-R01 und 48 aktuelle Killswitch-/DNS-/VPN-Tests | BEREITS INTEGRIERT | Originaldatei und alle 48 IDs bytegleich übernommen. |
| Aktuelle WireGuard-Interfaceprüfungen und übrige Produktkorrekturen | BEREITS INTEGRIERT | Aktuelle Quellen im Dreiwegevergleich erhalten; keine alten V3-Fixtures darüberkopiert. |
| V1 Feedback-/Repair-Unterdrückung, V2 F1–F8-Erweiterungen, V3 F1/F6/F7-Nachbesserungen | ZU INTEGRIEREN → übernommen | V3 enthält V1/V2 bereits; nur einmal als kumulativer Stand integriert. |
| Atomarer Konfigurationswriter und stdin-Unterstützung aus der V3-Basis | ZU INTEGRIEREN → übernommen | Im aktuellen Produkt fehlende Abhängigkeit ergänzt, keine Installation des privilegierten Helpers. |
| V3-Startup-Abschaltlogik gegen neueren KS-P1-Vertrag | KONFLIKT → gelöst | Neuere strikte Retention gewinnt; keine automatische Off-Kante wiedereingeführt. |
| DNS-Service-Imports und DoT-Backup-/Schreibpfad aus unterschiedlichen Basisständen | KONFLIKT → gelöst | Neue Parser-/Lock-Abhängigkeiten und vorhandene atomare Writer-/Rollbackkorrektur zusammengeführt. |
| Historische Killswitch-/Interface-Fixtures gegen aktuelle Sicherheitsassertions | KONFLIKT → gelöst | Die 48 aktuelle Tests bleiben unverändert; ältere Teständerungen werden dort nicht angewendet. |
| F1/F6 aus unabhängiger V3-Prüfung | KONFLIKT / OFFEN | Bewusst nur für isolierte Fehlerreproduktion übernommen; keine Livequalifikation. |
| PoC V5.1, P0 Fix2 und Stage1 Fix1 | NICHT BENÖTIGT für diesen Produkttestpfad | Modelle/Fakes und unvollständige reale Adapter bleiben archiviert, keine ungeprüfte Verdrahtung an DNS-/Firewallaktionen. |
| KS48-Runner V1–V9-B01, Gate-/Owner-/Assessmentkette und G02-Reparatur | NICHT BENÖTIGT | Keine Weiterentwicklung, keine Übernahme als Testabhängigkeit; Originale unverändert aufbewahrt. |

## Patchbasis, Abhängigkeiten und Erhaltung

Historische Basis von V1/V2/V3 laut Lieferberichten:
`066c13705e3105dbbf23d25e1451829a65e3b899`.
Dieser Stand wurde aus der vorhandenen Dateiablage
`netmon-dns-v2/baseline` verwendet; das Original wurde nicht ausgecheckt.
Der kumulative V3-Patch wurde zunächst auf einer getrennten Referenz unter
`/tmp/netmon-v3-reference` mit `patch --batch --forward` vollständig angewendet.
Er wurde **nicht** blind auf das heutige Produkt angewendet. Der Dreiwegevergleich
erhält aktuelle Änderungen gegenüber der gemeinsamen historischen Basis.

| Patch | SHA-256 |
|---|---|
| V1 | `8d0db180fbe1420a7fc55633509e96aae343b1d7db82a4d5af3a9ff4718119a1` |
| V2 | `4a96f8b3ee053a4516bd3f0e757fad3d8e53acfe268f54a62eec8cbac3ec2db3` |
| V3 | `542f62236fbd9dbf6cc2953b7f695494cc8ade92f78d3b691ba90b6574249629` |

Alle drei Werte wurden gegen die vorhandenen Originaldateien geprüft.
`integration-evidence/input-hashes.json`, `merge-decisions.json` und
`integration.diff` liefern genaue Eingaben, Entscheidungen und den finalen
Diff gegenüber dem heutigen Original. Die beiden übernommenen V3-Testdateien
für Feedback/F1–F8 und die unabhängigen Gegenbeispiele sind getrennt erkennbar.

Abhängigkeiten: DNS-Tab → App-/DNS-/DoT-Controller → DNSControlService →
Commandrunner beziehungsweise atomarer Konfigurationswriter. VPN-Inventare
bleiben an den vorhandenen VPN-/Interfacepfad angebunden. Tests ersetzen
NM-, resolved-, UFW- und WG-Aufträge mit eng begrenzten Fakes; die äußere
Sandbox und `tests/conftest.py` bleiben die Hostschutzgrenze.
Ein Anwendungscode-/Testimport benötigt keinen PoC, passiven Validator oder
KS48-Vertrag. `48-test-migration.json` belegt die Auswahlbindung
`a961dface53bcfa063896ff849f9347002aa0802b8b7ed7fdd66610aa8403c5d`
und Testdateibindung
`32969dee1d25935831afa7dc7947f5d60e0013602c095a2adf1309c8d01485dd`.
Die Tests selbst importieren keinen KS48-Runner. Ihre bestehenden Fakes
bleiben erhalten; sie benötigen die alte Einmalstartkette nicht.

## Tests in der beauftragten Reihenfolge

| Schritt | Tatsächliches Ergebnis | Nachweis unter integration-evidence |
|---|---|---|
| Syntax vor Imports | 209 vorhandene Pythondateien bestanden; finale Syntaxprüfung ergänzt die neuen Dateien | syntax.json / final-quality.json |
| Imports / Module / vorhandene DNS-Schreibsicherheit | 63 PASS | 01-imports-unit/junit.xml |
| Gezielte DNS-Units | 23 PASS, 66 gezielt nicht ausgewählt | 02-dns-unit/junit.xml |
| Isolierte DNS-Integration | 239 PASS | 03-dns-integration/console.log und junit.xml |
| Übernommene KS48-Fälle | 48/48 PASS, keine Skips oder xfail | 04-migrated-48/console.log und junit.xml |
| Relevante Regressionen | 626 PASS | 05-regressions-retry/console.log und junit.xml |
| GUI / Timer / Startup | 23 PASS | 06-gui-final-4/console.log und junit.xml |
| Reale DNS-Funktion, NM/resolved, UFW/VPN, Paketwirkung | **NOT RUN** | benötigt gesonderte Freigabe und eigenes privates Testsystem |
| Gesamte übrige Produktsuite, P0-/Kernelmodelle, echte manuelle Workerpfade | **NOT RUN** | nicht Teil dieser gezielten Testausführung |

Die Gruppen überschneiden sich. Grüne 14 adversariale Charakterisierungen
innerhalb der 239 Fälle bestätigen zum Teil absichtlich unsicheres Verhalten.
Sie sind weder 14 behobene Findings noch ein unabhängiger aktueller Review.
Historische Testzahlen in übernommenen Dokumenten sind keine neuen Läufe.

Der fertige Starter wurde zusätzlich mit `all` vollständig wiederholt:
alle sechs Phasen bestanden erneut, zusammen 1022 Testausführungen mit
998 unterschiedlichen Test-IDs, ohne Fehler oder Skips. Dies bestätigt den
wiederholbaren Entwicklungsweg; es erweitert den fachlichen Sicherheitsclaim
nicht. Rohbelege sind nach `integration-evidence/repeated/` übernommen,
Summen stehen in `repeat-summary.json`. Black und ruff bestehen für alle
18 geänderten/neuen aktiven Pythondateien sowie die zwei archivierten
Entwicklungsrezepte; `final-quality.json` enthält die Einzelprüfungen.

Der GUI-Test erzeugt die reale App mit echten Widgets, wählt den DNS-Reiter
aus und baut sie sauber ab. Der vorhandene Smoke-Modus deaktiviert schwere
Startupaktionen. Exakte zusätzliche Statusfakes melden fehlende Beobachtung
als Fehler/unknown; sie behaupten keinen aktiven DNS-/Firewallzustand.
Jeder nicht erwartete Befehl bleibt ein Testfehler. Für den DNS-Tab
unbeteiligte Hardwareabfrage und echte OS-Threads sind in dieser Fixture
ausdrücklich ersetzt. Ein normaler unisolierter GUI-Dauerbetrieb wurde nicht
gestartet und ist **NOT RUN**.

## Reproduzierte Fehler und gezielte Korrekturen

1. **Historische Git-Abhängigkeit:** Der erste angrenzende Regressionslauf
   endete mit 258 PASS und einem Fehler: ein Baseline-Test nutzte `git show`
   in der absichtlich gitfreien Kopie. Er liest jetzt eine lokale Fixture
   des exakten historischen Commitpfads. Quelle einmalig mit
   `git --no-optional-locks --no-pager ... show --no-ext-diff --no-textconv`
   unter schreibgeschütztem Original-Gitverzeichnis gelesen; kein Status,
   Checkout oder Indexrefresh. Fixture-SHA-256:
   `9f6fb318fcd53f9513e0e5203d0ff1255dac18e6e187a0f5dd8e896e6e92b54e`.
   Sicherheitsassertions unverändert; Nachlauf 626 PASS.
2. **GUI-Testgrenze:** Der erste GUI-Lauf wurde vom bestehenden Hostguard
   wegen Statusaufrufen gestoppt. Spätere Versuche benannten zusätzlich die
   Hardwareabfrage und WG-Fallbacks. Die Fixture simuliert diese eng; der
   Guard wurde nicht gelockert. Alle Fehlversuche bleiben erhalten.
3. **Tk-Abbaufehler:** `_cancel_pending_after_callbacks` löschte auch von
   Unterwidgets registrierte Tcl-Kommandos über das Hauptfenster. Beim
   Unterwidget-Abbau folgte `TclError: can't delete Tcl command`. Der neue
   Minimaltest reproduziert den Fehler im Vorlauf `06-timer-before`.
   Der Helfer in `netmon/main.py` cancelt jetzt am registrierenden Widget.
   Timerregression und echter App-Abbau bestehen. Kein DNS-Sicherheitsverhalten
   wurde hierfür verändert.
4. **Tk-Test-Lebenszyklus:** Eine erste rohe Tcl-Fensterzerstörung ließ den
   Python-Default-Root veraltet zurück. Die Fixture verwendet nun reguläres
   `root.destroy()`; dies ist eine Testkorrektur, kein weiterer Produktpatch.

Kein Fehlversuch wurde überschrieben oder als Erfolg umetikettiert.
Die zusätzliche finale Wrapperausführung und eine Prüfung nach Übertragung
werden separat protokolliert, statt frühere Läufe umzuschreiben.

## Offene Fehler und nächster realer Test

- **F1 weiterhin offen:** Split-only-VPN kann eine unabhängige physische oder
  globale Default-DNS-Quelle falsch als konfliktfrei melden. Andere Fälle
  werden nur als ungelöst erkannt; sie sind nicht automatisch saniert.
- **F6 weiterhin offen:** VPN-Wechsel während eines bereits laufenden
  NM-Schritts kann DHCP-DNS-Teiländerungen und Aktivierung zulassen. Ein
  nachträglicher Recheck verhindert keine rückwirkende Leak-Zeitspanne.
- V4-PoC-Schutzstatus ist keine echte Egressgarantie. Gemeinsamer realer
  Transition-Owner, Kernel-Egressschutz, vollständiger Rollback und
  Boot-/Crashqualifikation sind nicht durch diese Übernahme umgesetzt.
- Der übernommene atomare Writer verweigert privilegierte Nutzung aus
  ungeschütztem Quellcode. Sein installierter Root-Helper wurde hier nicht
  installiert; echte DNS-Schreibfähigkeit ist deshalb nicht nachgewiesen.
- Sechs ältere, intern bisher nicht verwendete DNS-Modusforwarder haben
  weiterhin keine Controllerziele. Die getesteten normalen DNS-Tab-Aktionen
  verwenden andere Pfade; diese Legacy-Schnittstellen sind nicht repariert.

Vor einem realen Funktionstest: F1/F6 gezielt entscheiden/beheben; ein
wegwerfbares privates Testsystem mit privaten IPv4-/IPv6-Resolvern und ohne
Hostdienstdurchreichung auswählen; genaue erlaubte Profil-/Resolveraktionen,
Readback und unabhängigen Restore festlegen. Erst danach gesonderte
ausdrückliche Freigabe für Einrichtung und tatsächliche Mutationen einholen.
Hier wurden weder Einstellungen des Hosts verändert noch Pakete installiert.

## Weiterverwenden, archivieren, später bereinigen

| Behandlung | Dateien / Verzeichnisse |
|---|---|
| Weiter benötigt | Produktmodule, DNS-/DoT-/UI-Tests, die 48 Bestandsfälle, neue Timer-/Writerregressionen, vorhandener Isolationsrunner, kleiner Testauswahlstarter, lokale historische Fixture. |
| Nur archivieren | V1/V2/V3-Patches, unabhängige V3-Prüfung, vollständige ursprüngliche Writer-Testquelle unter archive/dns-development; alle bisherigen KS48-Versionen, Assessments, Owner-/Gateablagen an ihren unveränderten Originalpfaden; PoC/P0/Stage1-Entwicklung als Referenz. |
| Später möglicherweise löschen | Nach eigener Entscheidung der Projektverantwortlichen: alte temporäre Runner-/Ergebnisablagen, duplizierte Entwicklungs-/Reviewkopien und nicht benötigte große Radio-Presetressourcen dieser Testkopie. Noch nichts davon gelöscht. |

`original-before.json` und `original-after.json` erfassen die unveränderten
Originalquellen einschließlich Gitmetadaten sowie die gesamten bisherigen
DNS-V4-/Reviewartefakte. Ein Vergleichsprotokoll und das finale Manifest
liegen in `integration-evidence`. Es gab keine Commits, Pushes, neuen KS48-
Versionen, Gate-/Ownerpublikationen oder automatischen Freigaben.

## Prüfung am endgültigen Zielpfad

Nach Übertragung bestand die Isolationsprobe erneut. Der normale Starter
wurde direkt aus `/dev-lab/projects/netmon-v4-dns-integration-test/` mit
`48` und `gui` ausgeführt: erneut **48/48 PASS** und **23/23 PASS**.
Die Importprüfung bestätigt die Modulpfade innerhalb genau dieser Kopie.
Logs und JUnit liegen zusätzlich unter `integration-evidence/relocated/`.

Der erste vollständige Dateitransfer meldete am Ende einen Fehler, weil ein
temporärer Writer-Sicherheitstest absichtlich eine FIFO-Fixture angelegt
hatte, die `copytree` nicht als reguläre Datei kopiert. Die kopierten Quellen
waren vollständig: alle damals 316 Manifestpositionen wurden am Ziel exakt
verifiziert. Temporäre private Fixture-/Home-/Cacheablagen gehören nicht
zum benötigten Lieferumfang; die abschließende Kopierprüfung nimmt sie aus
und löscht weder die ursprünglichen Nachweise noch bereits kopierte Dateien.
Dieser Transferfehler war kein Produkt- oder Testfehler.

Das abschließende `INTEGRATION-SHA256SUMS.txt` bindet Produkt-/Test-/Script-
Pythonquellen, neue Integrationsdokumente, Patcharchive, historische Fixture
und ausgewählte JSON-/JUnit-/Log-/Diff-Nachweise. Es bindet nicht jedes große
Radioressourcenfile oder jedes Paket der kopierten `.venv` und ist keine
neue Laufzeit-Freigabesperre. Die Übertragung dieser übrigen regulären Dateien
wird zusätzlich gegen die vorbereitete Kopie geprüft. Keine Installation,
keine Änderung an Host-DNS/Firewall und keine reale DNS-Funktionsprobe.
