> **Historischer Integrationsbericht:** Der eingefrorene V52-Kandidat bleibt unter dem unten genannten Sicherungspfad erhalten. Der aktuelle Arbeitsstand wurde für den lokalen Teststand 1.1.22 in den Branch `release/netmon-1.1.22-test` überführt. Siehe [Teststand und Grenzen](docs/NETMON-1.1.22-TEST.md).

# NetMon V4 gemeinsamer Prüfstand

Für die weitere unabhängige Prüfung gilt ausschließlich diese Arbeitskopie:

```text
/dev-lab/projects/dev-lab/backups/netmon-unification-20261031/candidate
```

Sie vereinigt die bisherigen DNS-/HDD-/GUI-Tests und die lokalen
WireGuard-/Killswitch-Incident-Korrekturen. Branch:
`integration/netmon-v4-common-20261031`, Basis `baecee92`.
Änderungen einschließlich neuer Hilfsmodule und Tests sind uncommittet.

[Herkunft, Entscheidungen, Testergebnisse und Prüfgrenzen](docs/NETMON-UNIFICATION-20261031.md)
stehen im ursprünglichen Integrationsbericht.
[Aktueller Korrekturstand nach Claudes Prüfung](docs/NETMON-KILLSWITCH-REVIEW-FIXES-20261031.md)
und `../review-response-v14-20261102/handoff-v14.json` sind für die erneute Prüfung maßgeblich.
Beide Originalstände bleiben erhalten.
Der ältere `README-DNS-INTEGRATION.md` und die übernommenen Paketberichte sind
historische Nachweise; ihre absoluten Pfade sind keine aktuellen Arbeitsaufträge.

Gezielte vorhandene DNS-Prüfung:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py --probe
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/test_dns_integration.py all
```

Gesamtsuite im privaten Test-Namensraum, mit weiterhin aktiven Hostaktions-Guards:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_isolated_suite.py \
  --netmon-audit-continue -q -rs --tb=short tests \
  tools/secure_browser_manager/tests/test_browser_container_builder.py
```

Zusätzliche native UFW-Prüfung ausschließlich über den eigenen isolierten Starter:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B tests/run_native_ufw_suite.py \
  -q --tb=short tests/native_ufw
```

Aktueller Übergabestand: **V14**, ausschließlich G1/G2 auf der zusammengeführten
V13-Basis. V13 ist vollständig vor der Änderung archiviert. Root-Helfer und
Firewall-Controller sind unverändert, Protokoll bleibt **11**.

G1: Internet AN schaltet einen zuvor aktiven Killswitch nicht mehr vorübergehend
aus. Bei nötigem Abgleich wird ausschließlich bestehende geschützte Autorität
fortgesetzt; ein explizites AUS gewinnt. Eine unvollständige Wiederherstellung
liefert False. Spielprofile, die eine Killswitch-Pause verlangen, werden bei aktivem
Killswitch vor Änderungen abgelehnt. Der Nutzer kann bewusst AUS wählen oder ein
Spielprofil ohne Pause nutzen; eine automatische ungeschützte Lücke entfällt.

G2: Aufgeschobener DNS-Abschluss und fehlende Vorbereitung werden unterschieden.
Vorbereitung wird nur nachgeholt, wenn sie ausdrücklich aussteht und eine strikte
WireGuard-Abfrage keine laufenden Interfaces bestätigt. Bei laufendem Tunnel wird
nur der Abschluss geplant; eine fehlgeschlagene Abfrage erlaubt keine Bereinigung.
Eine Pause nur wegen einer anderen Netzoperation wiederholt die Vorbereitung nicht.
Vorhandene Generations-, Netzkoordinator- und ISP-DNS-Freigabesperren bleiben erhalten.

Nachweis: Die beiden Fehler wurden vor der Korrektur auf V13 in vier isolierten
Charakterisierungsfällen reproduziert. Danach 778 gezielte normale und 17 native
Fälle bestanden; nach Entfernung zweier ungenutzter lokaler Zuweisungen wurden die
778 normalen und die zwei betroffenen nativen G1-Fälle auf dem Endstand wiederholt.
Syntax, Black, Ruff und Diff-Check bestanden. Native Tests verwenden echten UFW-Code
mit Kernel-Stub, keinen echten Paketfluss. Keine neue Gesamtsuite; die V12-Zahlen
5.083/14/330 bleiben Historie und begründen keine V14-Gesamtfreigabe.

Paket: `1.1.21~v4dnstest20261102.1401`, unter
`../review-response-v14-20261102/package/dist/`. Alle 118 Python-Dateien entsprechen
den Quellen; Paketbesitzrechte und Syntax sind geprüft. Noch keine Installation
oder VM-Ausführung von V14. Die bisherigen echten VM-Belege gehören zu V12.

V14-Stand, Vorherarchiv, gezielter Patch, Paket und Belege:
`../review-response-v14-20261102/`. Für künftige unabhängige Prüfungen wird ein
vollständiges V14-Quellarchiv mit Manifest bereitgestellt; der aktive Arbeitsordner
wird während einer solchen Prüfung nicht weiterentwickelt. Keine automatische neue
breite Prüfrunde. Nächster vereinbarter Schritt ist der begrenzte Paket-/Alltagstest
in der Wegwerf-VM; keine automatische Installation auf dem produktiven Host.
G3/G4/F4 bleiben zurückgestellt. Beide Originale und produktive Firewall/DNS/VPN
bleiben erhalten; keine Commits oder Pushes. Keine Gesamt- oder Produktivfreigabe.
V14-nft, vollständige NetworkManager-/DNS-Guard-Integration, SIGKILL/Stromausfall,
Paketlebenszyklus und Host-H1 bleiben offen.
