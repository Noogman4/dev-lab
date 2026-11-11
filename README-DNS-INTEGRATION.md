> **Historischer DNS-Testbericht:** Der aktuelle Arbeitsstand ist der lokale Teststand 1.1.22 auf `release/netmon-1.1.22-test`; siehe [Teststand und Grenzen](docs/NETMON-1.1.22-TEST.md). Alte absolute Pfade und `d.py` sind keine aktuellen Startanweisungen. Die Legacy-Datei bleibt ausschließlich im eingefrorenen Kandidaten erhalten.

# NetMon V4 – eigenständige DNS-Testkopie

Zielpfad: `/dev-lab/projects/netmon-v4-dns-integration-test/`.
Entwicklungsstand für isolierte Tests: F1-Fehlklassifikation korrigiert,
DHCP-/ISP-DNS-Freigaben zur Absicherung von F6 vorläufig gesperrt.
Kein Livebetrieb; statische manuelle Profile bleiben erhalten.

## Wiederholbare Tests

Vorhandene Werkzeuge: Python 3.12, die kopierte `.venv`, Bubblewrap, Xvfb.
Es wurde nichts installiert. Die Launcher der kopierten `.venv` sind auf
den neuen Zielpfad angepasst. Die folgenden Befehle benötigen weder das
Originalrepository noch irgendeinen KS48-Runner oder dessen Autorisierung:

```sh
cd /dev-lab/projects/netmon-v4-dns-integration-test
python3 -B tests/run_isolated_suite.py --probe
python3 -B scripts/test_dns_integration.py all
```

Einzelne Phasen: `unit`, `dns-unit`, `integration`, `48`, `regressions`, `gui`.
Beispielsweise:

```sh
python3 -B scripts/test_dns_integration.py 48
python3 -B scripts/test_dns_integration.py gui
```

Jeder Aufruf erhält eine frische temporäre Ausgabeablage mit `console.log`
und `junit.xml`. Es gibt keine Einmalstart-Sperre und keine Gate-Dateien.
Tests laufen nicht-root mit privatem Netz-/PID-/IPC-Namespace, read-only
Projekt, privatem Home und ohne Host-Dienstsockets. Der vorhandene
Hostzugriffs-Guard bleibt aktiv. Der GUI-Test benutzt echte Tk-Widgets und
ausdrücklich simulierte Statusleser; er startet keine echte DNS-Reparatur.

## Ergebnis und offene Arbeit

63 Import-/Modulfälle, 23 gezielte DNS-Unit-Fälle, 258 DNS-Integrationsfälle,
48 unverändert übernommene KS48-Fälle, 626 angrenzende Regressionen und
23 GUI-/Startup-Fälle bestehen in den abschließenden gezielten Läufen.
Die Gruppen überlappen; die Zahlen dürfen nicht als Anzahl verschiedener
Tests addiert werden. Der vollständige Starter besteht mit 1041 Ausführungen und 1017
unterschiedlichen IDs. Bestehende unsichere Split-Konfigurationen werden
als Problem angezeigt und nicht pauschal umgeschrieben. System-DHCP-Auswahl
und automatische ISP-Restores einschließlich statischer Fallbacks werden
verweigert; eine sichere Wiederfreigabe ist noch nicht implementiert.

Reale DNS-/NetworkManager-/resolved-/Firewalltests: **NOT RUN**.
Der normale unisolierte Anwendungsstart ist kein sicherer Testeingang.
Für reale Funktionstests sind ein wegwerfbares privates Testsystem, private
Resolver und eine gesonderte ausdrückliche Freigabe erforderlich.

[Aktueller F1-/F6-Abschlussbericht und Einschränkungen](docs/DNS-F1-F6-REPORT.md).
[Historische Integration und Fehlversuche](docs/DNS-INTEGRATION-REPORT.md).
[Quell- und Testerhaltungsnachweise](integration-evidence/).
Historische Patches und relevante Quellen liegen in `archive/dns-development/`;
die übrigen Originalartefakte bleiben unverändert an ihren bisherigen Pfaden.
