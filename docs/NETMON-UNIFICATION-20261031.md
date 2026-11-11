# NetMon V4 Zusammenführung vom 31.10.2026

Dieser Bericht beschreibt den gesicherten Stand vor der unabhängigen Prüfung.
Der [anschließende Korrekturbericht](NETMON-KILLSWITCH-REVIEW-FIXES-20261031.md)
beschreibt die aktuelle Prüfkopie.

Der gemeinsame Prüfstand enthält die DNS-, HDD- und GUI-Änderungen der bisherigen
Testkopie sowie die WireGuard-Pfad- und Killswitch-Incident-Korrekturen des
Produktarbeitsverzeichnisses. Er ist eine unabhängige lokale Git-Kopie mit
uncommitteten Änderungen. Beide Ausgangsstände bleiben unverändert erhalten.
Dieser Stand ist zur unabhängigen Prüfung vorbereitet; er ist nicht installiert.

## Verbindlicher Prüfstand und Herkunft

Arbeitsverzeichnis für die anschließende gemeinsame Prüfung:

```text
/dev-lab/projects/dev-lab/backups/netmon-unification-20261031/candidate
```

Branch: `integration/netmon-v4-common-20261031`.
Git-Basis: `baecee92f83764ca7af73ee0c61cf0f29f4bff3d`.
`git diff` allein zeigt die neuen, ungetrackten Hilfsmodule und Tests nicht;
`git status --short` und der vollständige Review-Patch gehören zur Prüfung.

| Eingang | Übernommener Inhalt |
| --- | --- |
| A: `/dev-lab/projects/dev-lab` auf `security/hdd-b01-b02-cloud-review` | Git-Basis einschließlich HDD-/WireGuard-Härtung; alle lokalen NetMon-/Teständerungen einschließlich Killswitch-Snapshot, Journal und WireGuard-Pfadbehandlung |
| B: `/dev-lab/projects/netmon-v4-dns-integration-test`, ohne `.git` | DNS V1–V3 mit F1-Korrektur und F6-Verweigerung, atomarer privilegierter Konfigurationsschreiber und stdin-Unterstützung; HDD-/GUI-/Paketierungsänderungen mit Regressionstests |

B wurde laut seinen Integrationsnachweisen bereits auf dem Produktzweig von A
aufgebaut. Deshalb erfolgte eine dateiweise Dreiwegezusammenführung mit dem
genannten Commit als gemeinsamer Basis. Fehlende IDE-/Containerdateien in B
wurden nicht als Löschauftrag interpretiert. Vorhandene Benutzerkonfigurationen,
Profile, Firewallregeln oder installierte Dateien wurden nicht übertragen.

Die im ursprünglichen Repository gespeicherte Referenz `origin/main` steht auf
`066c13705e3105dbbf23d25e1451829a65e3b899`. Sie ist keine Fortsetzung des aktuellen
Arbeitszweigs: gemeinsame Git-Basis ist `2eb1ed8f4ba96b98c5db5c50964631bd29aa3c4f`,
danach gibt es drei Commits nur im Arbeitszweig und 16 nur auf diesem Main-Stand.
Diese 16 Commits wurden nicht pauschal zusätzlich integriert. B enthält bereits
ausgewählte DNS-Abhängigkeiten dieses historischen Main-Stands. Die genaue Liste
steht in `../main-not-in-input-basis.txt`. Dieser Prüfstand vereinigt A und B;
ein vollständiger zusätzlicher Main-Abgleich bleibt eine eigene Entscheidung.
Maßgeblich sind die Commit-IDs, da die neue Kopie das lokale Repository als
Remote hat und dessen lokale Branch-Namen abbildet.

## Integrationsentscheidungen

Der einzige Textkonflikt lag in `App.repair_orphaned_killswitch_on_startup()`.
Die zusätzliche Journalprüfung aus A bleibt erhalten. Bei offenem oder
unlesbarem Wiederherstellungszustand findet keine automatische Firewalländerung
statt; auch ein erkannter aktiver Killswitch wird beim Start nicht automatisch
abgeschaltet. Die strengere VPN-Statusbeobachtung aus B bleibt ebenfalls erhalten.

Ein neuer Integrationstest belegte einen weiteren semantischen Konflikt:
Der DNS-Pfad aus B ruft bei aktivem VPN direkt `apply_vpn_dns_policy()` auf und
umging damit die Wiederherstellungssperre in `enforce_dns_clean()` aus A.
Vor der Korrektur führte der simulierte Guard trotz gesetztem
`killswitch_recovery_required` zwei DNS-Änderungsbefehle aus. Nun prüft
`run_dns_guard_check_once()` vor der automatischen Reparatur dieselbe Sperre,
setzt einen ausdrücklichen ungeklärten Status und führt keine Reparatur aus.
15 Regressionen prüfen Speicherzustand, persistierte Journalphasen einschließlich
Neustart/unlesbarem Journal und geschützte Zustände `recovery`/`unknown`, jeweils
mit und ohne VPN; eine Positivkontrolle erhält die normale Reparatur.

DNS F6 bleibt absichtlich gesperrt: keine DHCP-/ISP-DNS-Freigabe, auch nicht
durch automatische statische Fallbacks. Die DNS-Korrekturen sind damit keine
vollständige Lösung für beliebige externe VPN-Wechsel. Die HDD-Ausnahmen für
Swapdateien und fehlende fremde fstab-UUID-Aliase behalten ihre jeweiligen
Nachweispflichten; Gerätebindung und sichere Mountoptionen bleiben erhalten.

Die ausgetauschten Testfunktionen sind in `../removed-symbols.json` einzeln
aufgeführt. Alte Erwartungen an pauschale UFW-Bereinigung, Aktivierung von UFW
beim Abschalten, ungeprüfte Profilmigration und automatische ISP-DNS-Freigabe
werden durch die strengeren Snapshot-/Pfad-/F6-Tests ersetzt. Der historisch
`48` genannte Testschritt enthält deshalb jetzt 46 Fälle; sein Name ist keine
aktuelle Fallzahl und er ist kein separater KS48-Abnahmelauf.

## Validierung

Alle Laufzeittests liefen als unprivilegierter Benutzer über den vorhandenen
Bubblewrap-/Xvfb-Starter: privates Netz ohne Hostrouten, privater PID-Namensraum,
schreibgeschütztes Projekt, keine Host-Heimatverzeichnisse oder Dienstsockets.
Die Isolationsprobe bestand. Die vorhandene virtuelle Umgebung wurde kopiert;
es wurden keine Abhängigkeiten installiert.

| Prüfung | Ergebnis |
| --- | --- |
| Gesamtsuite einschließlich Secure-Browser-Builder | 4.925 bestanden, 14 fehlgeschlagen, 319 übersprungen |
| Gegenprüfung ausschließlich der 14 Fehler an Original A | Alle 14 identischen Test-IDs fehlgeschlagen |
| Gegenprüfung ausschließlich der 14 Fehler an Original B | Alle 14 identischen Test-IDs fehlgeschlagen |
| Killswitch/Snapshot/Journal/WireGuard und angrenzende Regressionen | 756 bestanden |
| HDD/GUI/About/Einstellungen/Paketierung/Deinstaller | 592 bestanden |
| Neue DNS-/Firewall-Grenzfälle | 15 bestanden; erste Reproduktion vor Korrektur erwartungsgemäß fehlgeschlagen |
| DNS-Starter, alle sechs Phasen | 1.039 Ausführungen bestanden; 66 bewusste Filterabwahlen im gezielten Unit-Schritt |
| Ruff, Black und Python-3.11-Grammatik der 46 betroffenen Python-Dateien | Bestanden |
| Shellsyntax der übernommenen Build-/Deinstallationsskripte, `git diff --check` | Bestanden |

Die Auswahlen überlappen; ihre Zahlen dürfen nicht addiert werden.
Die 14 bestehenden Fehler betreffen zwölf Repository-Guard-Tests mit einer
fehlgeschlagenen Flatpak-Systemabfrage im Namespace, einen Supportpaket-Test
mit abweichender Dateizahl und eine Secure-Browser-Launcher-Erwartung mit festem
Heimatverzeichnis. Sie wurden hier nicht geändert. Die übersprungenen Fälle
betreffen überwiegend fehlendes PHP sowie benötigte zweite UID/Dateirechte.
Die Gesamtsuite ist somit ausdrücklich nicht vollständig grün.

## Nachweise und nächste Prüfung

Der Elternordner enthält private Quellarchive beider Eingänge, ein verifiziertes
Git-Bundle mit allen ursprünglichen Referenzen, `inputs.json` mit SHA-256 und
Modi, Integrationsentscheidungen, vollständigen Review-Patch, finale Prüfsummen,
JUnit-/Konsolennachweise, Qualitätsprüfung und Originalvergleich.
Vorhandene historische Berichte in `docs/` beziehen sich weiterhin auf ihre
damaligen Kopien und Paketversionen; für diesen Prüfstand gilt dieser Bericht.

Die unabhängige Prüfung muss genau diese Kopie einschließlich neuer Dateien
untersuchen, insbesondere die privilegierten Snapshot-/Restore-Grenzen,
IPv4-/IPv6-Teilzustände und das Zusammenspiel mit DNS Guard/VPN-Steuerung.
Die Kernel-Tabellen beider Adressfamilien werden getrennt angewendet; eine
globale Atomarität über IPv4 und IPv6 wird nicht behauptet. Native positive
Root-Helfer-/Kernel-Tests und Neustart-/Abbruch-Abnahme gehören anschließend
in eine wegwerfbare VM mit Benutzerregeln und Dual-Stack-Szenarien.

Es gab keine Commits, Pushes, Paketinstallation, produktiven App-Starts oder
Firewall-/DNS-/VPN-/Mountänderungen. Die Auswahl des dauerhaft führenden
Arbeitsverzeichnisses und die Übernahme in dieses folgen nach der Prüfung.
