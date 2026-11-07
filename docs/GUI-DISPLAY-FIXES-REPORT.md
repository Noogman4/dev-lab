# NetMon V4 – drei GUI-Anzeigefehler korrigiert

Stand: 30.10.2026, ausschließlich Arbeitskopie
`/dev-lab/projects/netmon-v4-dns-integration-test/`.
Keine Installation, kein DEB-Neubau, kein Commit oder Push.
Die bestehende installierte Anwendung und das vorhandene `.2`-DEB enthalten
weiterhin den vorherigen Code; beide wurden nicht verändert.

## 1. DNS-Kopfzeile

**Ursache:** `update_dns_header()` suchte `nm_get_dns_list` nur in
`self.__dict__`. Die Funktion ist eine Klassenmethode und wurde so übersprungen.
Der Fallback aggregiert aktive DNS-Server einschließlich globaler Resolver,
behielt aber die Beschriftung `NM DNS (Schnittstelle)` bei.

**Korrektur:** Die Methode wird über `getattr` gebunden und nur bei vorhandener
Schnittstelle aufgerufen. Echte NM-Linkdaten behalten ihre Schnittstellenangabe.
Fehlende/fehlgeschlagene Linkabfragen führen zur ausdrücklich aggregierten
Beschriftung `Resolver DNS`. An der DNS-Erkennung, Policy, Routingauswertung
oder einer Änderungsfunktion wurde nichts geändert.

**Regressionen:** Klassenmethode mit eigenem NM-Command-Fake, globaler DNS darf
nicht in ihre Linkanzeige gelangen; Fallback bei leerer Liste, NM-Fehler oder
fehlender Schnittstelle. Der bestehende Fallback-Test wurde auf die korrekte
Beschriftung angepasst. Im Settings-Reset-Test wurde die nun tatsächlich
aufgerufene, exakt bestimmte NM-Leseabfrage für `eth0` synthetisch beantwortet.
Zwei zusätzliche Negativfälle sichern ab, dass NM-Änderungen und die Abfrage
einer nicht freigegebenen Schnittstelle weiterhin am Hostzugriffs-Guard scheitern.
Der Guard selbst wurde nicht verändert.

**Grenze:** Ein aggregierter Fallback belegt keinen einzelnen aktiven Resolver
pro DNS-Anfrage. Eine Änderung des gesonderten Resolver-Statuslabels gehörte
nicht zu diesem Auftrag.

## 2. CPU-Modell

**Ursache:** `_read_cpu_model()` akzeptierte den ersten Schlüssel `processor`
gleichberechtigt mit `model name`/`hardware`. Auf x86 steht `processor: 0` vor
dem beschreibenden Modellnamen. Die Datenübergabe über `sysinfo_static` und
`_set_sysinfo_value("hw_cpu", ...)` war korrekt und bleibt unverändert.

**Korrektur:** Beschreibende Werte werden gesammelt; `model name` hat Vorrang
vor `hardware` und einem nicht numerischen `processor`-Text. Numerische
Prozessorindizes werden verworfen. Der vorhandene `lscpu`-Fallback bleibt
bestehen; sind keine Informationen verfügbar, erscheint `-`.
Keine CPU-Bezeichnung wird im Produktcode hardcodiert.

**Regressionen:** x86-Zeilenreihenfolge, Modellname vor Hardware-Fallback,
ARM-Hardware und beschreibender Processor-Text; rein numerische Indizes,
leere/fehlende cpuinfo und nicht verfügbare lscpu-Daten.

**Grenze:** Unbekannte oder nicht lesbare Hardwaredaten bleiben als `-`
gekennzeichnet; es wird keine Modellbezeichnung geraten.

## 3. About und optionale Dokumentation

**Ursache:** About nutzte ausschließlich `NETMON_APP_VERSION` (`1.1.21`).
Dokumentationshinweise und der Öffnen-Button waren unabhängig vom Vorhandensein
aktiv; der Dateinamen-Fallback akzeptierte auch Verzeichnisse/defekte Links mit
passender Endung.

**Korrektur:** `_get_about_display_version()` liest nur beim bekannten
installierten Programmpfad `/usr/lib/netmon/netmon/app.py` über den absoluten
Befehl `/usr/bin/dpkg-query --admindir=/var/lib/dpkg` Status und Version des
Pakets `netmon`. Erforderlich sind ein erfolgreicher Aufruf, exakt
`install ok installed` und ein einzelner plausibler Debian-Versionswert.
Die Abfrage hat drei Sekunden Zeitlimit; Fehler/ungeeignete Daten führen zur
Quellversion zurück. Eine Quellkopie übernimmt keine Version einer parallel
installierten Anwendung. Der Paketdatenbankpfad ist fest; es gibt keine
Abfrage aus Benutzereinstellungen und keine Installation.

Für ein tatsächlich installiertes Testpaket kann About damit beispielsweise
`1.1.21~v4dnstest20261030.2` zeigen. Dieselbe Ermittlung gilt im grafischen und
im Text-Fallback. Konstanten, Release-/Updatevergleich und Paketierung bleiben
unverändert. Die verwendete CLI-Abfrage wurde zusätzlich lesend gegen die
bestehende Paketdatenbank geprüft; sie liefert den erwarteten Status und die
Version `.2`.

Dokumentation wird nur anhand existierender Dateien angeboten. Fehlt sie,
erscheint ein ausdrücklicher Hinweis auf fehlende optionale PDF-/HTML-Dateien;
der Öffnen-Button ist deaktiviert und die Behauptung enthaltener
Troubleshooting-Dokumentation entfällt. Deutsch und Englisch sind ergänzt.

**Regressionen:** gültige Test-/Debian-Version mit Epoch, fehlende/halb
konfigurierte Pakete, ungültige/mehrzeilige/leere Metadaten, Quellkopie ohne
Übernahme einer installierten Version; Verzeichnis, defekter Link und echte
Dokumentdatei. Echte Tk-Dialogtests prüfen Paketversionsanzeige und
Dokumentverfügbarkeit jeweils in Deutsch/Englisch.

**Grenzen:** In dieser Arbeitskopie ist die sichtbare Quellversion weiterhin
`1.1.21`. Für die korrigierte installierte Oberfläche ist später ein gesondert
beauftragter Paketbau samt Installation erforderlich. Die Metadatenabfrage
ist auf den bestehenden Debian-Installationspfad begrenzt. Optionale
Dokumentation wurde nicht nachgeneriert.

## Tests und bestehende Gesamtprobleme

| Lauf | Bestanden | Fehlgeschlagen | Fehler | Übersprungen |
| --- | ---: | ---: | ---: | ---: |
| Gezielte Anzeige-/About-/DNS-/GUI-/Startup-Tests | 239 | 0 | 0 | 0 |
| Settings-Fixture einschließlich negativer Guard-Fälle | 39 | 0 | 0 | 0 |
| Vollständiger V4-Starter, sechs Phasen | 1041 Ausführungen / 1017 verschiedene IDs | 0 | 0 | 0 |
| Gesamte Testsammlung, abschließender Lauf | 4497 | 15 | 0 | 319 |
| Vorherstand in derselben Isolation, Vergleichslauf | 4465 | 15 | 0 | 319 |

Alle **30 neuen direkten Finding-Regressionsfälle** sowie die **zwei zusätzlichen
negativen Guard-Fälle** bestehen. Im großen Lauf sind genau dieselben 15
Fehler wie im Vorherstand vorhanden; kein zusätzlicher Fehler bleibt zurück.
Die 319 Skips betreffen 314 PHP-CLI-Fälle, einen chown-Fall, drei Fälle mit
zweiter UID und einen Fall mit root-eigenem /tmp. Sie sind keine bestandenen Fälle.

Die gezielte rote Reproduktion vor der Produktänderung ergab 15 fehlgeschlagene
und 26 bestandene Fälle; zwei zusätzliche Versionsanzeige-GUI-Fälle wurden danach
ergänzt. Black für alle betroffenen Python-Dateien und Ruff bestehen. Die
Suitegruppen überlappen und dürfen nicht zu verschiedenen IDs addiert werden.

Die 15 Fehler des großen Gesamtlaufs sind mit derselben Isolationsumgebung
auch im unveränderten Vorherstand nachgewiesen. Dazu wurden ausschließlich
Vorher-Dateien im privaten Bubblewrap-Namespace read-only eingeblendet;
die Arbeitskopie wurde nicht zurückgesetzt. Der Vergleichslauf blendet auch
die vorherigen Testfassungen ein und lässt ausschließlich die neue
Regressionstestdatei aus. Er ist ein Ursachenvergleich, kein grüner
abschließender Regressionstest.

Die vorhandenen Fehler verteilen sich auf:

- Zwei historische Sicherheitstests benötigen `git show` auf alte Commits;
  diese eigenständige Arbeitskopie enthält absichtlich keine Git-Historie.
- Zwölf Repository-Guard-Fälle erwarten keine Flatpak-Abfragefehler; das
  verfügbare Flatpak-Programm findet in der privaten Testumgebung keine
  passende Systemumgebung. Die Fixtures isolieren diese zusätzliche Quelle
  nicht vollständig.
- Ein Performance-/Supportpakettest erwartet `file_count=1`, erhält aber 0.
  Das ist ebenfalls im unveränderten Vorherstand reproduziert; die
  Supportpaketimplementierung wurde in diesem Auftrag nicht geändert.

Die große Sammlung ist deshalb **nicht vollständig grün**. Diese Befunde
werden nicht durch Änderungen außerhalb der drei GUI-Findings verdeckt.
Übersprungene Fälle und ihre Gründe stehen vollständig im JUnit/Console-Log.

Alle Läufe nutzen den unveränderten privaten Netz-/PID-/IPC-Namespace,
read-only Projekt, privates Home und Xvfb ohne Host-Dienstsockets. Reale
Netzwerk-/Firewallaktionen und Host-GUI-Starts wurden nicht durchgeführt.
Der erste große Lauf deckte eine fehlende NM-Leseattrappe in der Settings-
Fixture auf; der Hostzugriffs-Guard blockierte diese Abfrage. Nach Ergänzung
des exakten Fakes entfällt der Fixture-Fehler im abschließenden Lauf.

## Änderungserhalt und Prüfnachweise

Produktänderungen: sechs abgegrenzte App-Methoden einschließlich einer neuen
About-Hilfsmethode, plus ein neuer Übersetzungsschlüssel je Sprache.
Alle anderen App-Methoden sind auch als Quelltext identisch. Insbesondere
F1-/F6-Entscheidungen, Guardverhalten, privilegierte Helfer,
HDD-Methoden/-Module und Paketierung wurden nicht geändert. Alle anderen
zuvor gebundenen Quellen sind hashgleich; die 48 übernommenen DNS-Fälle
bleiben unverändert.

Installierte `app.py`, vorhandenes Test-DEB, Original-`app.py` und Original-
Git-Index wurden vor/nach per SHA-256 verglichen und bleiben identisch.
Keine Schreibbefehle im Original und kein KS48-Runnerstart. Der vorhandene
DEB-Hash bleibt
`0e39f579a9ecc63ade9f4234f1a4a7dca002f37995ab4b01fb6f3a0bede2b226`.

Nachweise: `integration-evidence/gui-display-fixes-20261030/` mit Vorherständen,
Diff, Erhaltungsprüfung, Test-/JUnit-Logs und dem ausschließlich für den
Vorhervergleich verwendeten Overlay-Runner. Die bestehende
`INTEGRATION-SHA256SUMS.txt` wird um den korrigierten Quellstand und die
Nachweise ergänzt; der vorherige Stand bleibt archiviert.

Reproduzierbare Aufrufe ohne Hostaktionen:

```sh
cd /dev-lab/projects/netmon-v4-dns-integration-test
python3 -B scripts/test_dns_integration.py all
python3 -B tests/run_isolated_suite.py -q -rs --tb=short \
  tests/test_gui_display_findings.py tests/test_netmon_about.py \
  tests/test_about_release_metadata.py tests/test_netmon_dns_consistency.py \
  tests/test_dns_integration_smoke.py tests/test_netmon_startup_instance.py \
  tests/test_netmon_settings_tab.py
python3 -B tests/run_isolated_suite.py -q -rs --tb=short --maxfail=0 tests
```

Die letzten Aufrufe erzeugen frische temporäre Nachweise. Der große Lauf
enthält die oben getrennt dokumentierten vorbestehenden Fehler. Keine
Werkzeuge wurden installiert. Nach Abschluss dieses Korrekturauftrags stoppen.
