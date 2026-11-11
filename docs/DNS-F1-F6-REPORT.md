# NetMon V4 – F1/F6: Korrektur und sichere Verweigerung

30.10.2026, Europe/Berlin. Ausschließlich Arbeitskopie
`/dev-lab/projects/netmon-v4-dns-integration-test/`.

## Ergebnis

- **F1: falsche Entwarnung korrigiert.** Physische Default-DNS-Routen und
  globale Fallbackresolver bleiben auch bei einem Split-only-VPN sichtbar.
  Ein bestehender unsicherer Split-/Default-Konflikt wird weiterhin nicht
  pauschal umgeschrieben; Erkennung ist keine reale Leak-Sanierung.
- **F6: riskante Freigaben vorläufig gesperrt**, entsprechend der ausdrücklichen
  Entscheidung der Projektverantwortlichen in diesem Auftrag. DHCP-/ISP-DNS
  wird durch diese Wege nicht mehr freigegeben. Die sichere Wiederaufnahme
  dieser Funktion bleibt **BLOCKED**: die vorhandene synchrone NM-Schnittstelle
  koordiniert laufende Änderungen nicht atomar mit externen VPN-Übergängen.
- Der beauftragte vollständige Starter besteht: **1041 Testausführungen,
  1017 unterschiedliche Test-IDs, keine Fehler oder Skips**. Die 48 übernommenen
  Fälle sowie GUI-/Startup- und angrenzende Regressionen bestehen weiterhin.

Es wurde kein Freigabe-, Owner-, Gate- oder neues Prüfverfahren entwickelt.
Der vorhandene Teststarter und seine Isolation sind unverändert.
Reale DNS-/Firewall-/NetworkManager-/Resolvereingriffe: **NOT RUN**.

## F1 – Ursache, Auswirkung und Korrektur

Die vollständige unabhängige Befundbeschreibung wurde aus
`archive/dns-development/V3-INDEPENDENT-REVIEW.md` gelesen und anhand der
vorhandenen simulierten Gegenbeispiele reproduziert: sowohl physisch als
auch global lieferte die ursprüngliche Policy `conflict=False`, `leak=False`
und `only_vpn_dns=True` trotz zusätzlicher Default-/Fallbackquelle.

**Ursache:** `DNSControlService.vpn_dns_routing()` übersprang Resolverquellen,
sobald `split_only` für die VPN-Links galt. Bei spezifischen fremden Domains
wurde dadurch auch ein physisches `DefaultRoute=yes` übersprungen. Die
globale Resolverquelle wurde mit derselben Ausnahme ausgeblendet.
`evaluate_dns_snapshot()` übernahm die falsche Klassifikation; die bestehende
App-Guard-Auswertung konnte deshalb `ok` melden.

**Änderung in `netmon/services/dns_control_service.py`:** Die
`split_only`-Ausnahmen sind entfernt. Spezifische Domains und allgemeine
Default-/Fallbacknutzung werden getrennt ausgewertet. Globale Resolver
werden ohne überlagernde VPN-Rootroute berücksichtigt; ein physischer Link
wird bei bestätigtem `DefaultRoute=no` weiterhin als reine Split-Quelle
erhalten. Die Ausnahme für eine tatsächlich vorhandene VPN-Rootroute
(`~.`) bleibt bestehen. DNS-Adressen und Domains werden nicht verändert.

Die zugrunde gelegte Routingregel wurde anhand der offiziellen
[systemd-resolved-Dokumentation, Version 255](https://www.freedesktop.org/software/systemd/man/255/systemd-resolved.service.html#Protocols%20and%20Routing)
geprüft: Bei nicht passenden Routing-Domains werden DefaultRoute-Links und
globale Resolver berücksichtigt. Die Reproduktion verwendet lokale
Statusfixtures und stellt keine echten DNS-Anfragen.

**Regression:** Die zwei bisherigen False-Negative-Gegenbeispiele verlangen
jetzt Konflikt/Leak-Anzeige und verweigerte automatische Reparatur. Zwölf
neue Parameterfälle prüfen physisch/global × IPv4/IPv6 × DefaultRoute
yes/no/fehlend, einschließlich des tatsächlichen App-Guard-Zustands.
Die frühere Erwartung „legitimes Split-DNS“ bei gleichzeitigem physischem
DefaultRoute=yes und Split-only-VPN ist korrigiert; sichere Split- und
VPN-Rootroutenkontrollen bleiben erhalten.

**Grenze:** Die bestehende sichere Zurückhaltung bei Split-Profilen bleibt.
Ein exponierter Resolver verschwindet nicht durch eine Warnung. Fehlende
gezielte Routingkorrektur und tatsächliche Paket-/Resolverwirkung werden
nicht als erledigt bezeichnet.

## F6 – Ursache, Auswirkung und gewählte Korrektur

Die ursprünglichen vier Fälle wurden reproduziert: VPN wird während
`nmcli con mod` beziehungsweise `nmcli con up` aktiv oder unbekannt.
In allen Fällen wurden beide `ignore-auto-dns=no`-Eigenschaften geschrieben
und die Verbindung aktiviert, bevor der Controller den Wechsel bemerkte.

**Ursache:** Der Controller prüfte vor und nach dem vollständigen synchronen
Serviceaufruf. Der Service revalidierte Profilidentität und Eigenschaften,
aber diese NM-Prüfungen stellten keine atomare Bindung an den VPN-Zustand
her. Der gemeinsame DNS-Lock serialisiert kooperierende DNS-Writer;
ein externer VPN-Akteur und ein bereits laufender NM-Befehl werden dadurch
nicht gesperrt. Weitere Rechecks könnten die nächste Aktion stoppen,
aber keine schon erfolgte Freigabe rückwirkend verhindern.

Die Projektverantwortliche hat deshalb ausdrücklich gewählt:
**„DHCP-/ISP-Freigaben vorläufig sperren; sichere Verweigerung bevorzugen“.**
Es wird kein Ersatzbeweis durch nachträgliche Prüfung oder unbestätigte
Kompensation behauptet.

| Modul | Konkrete Änderung |
|---|---|
| `netmon/services/dns_control_service.py` | Öffentlicher und privater NM-Schreibpfad verweigern `ignore_auto_dns` ungleich exakt True vor NM-Aktionen. Der erlaubte restriktive Pfad erzeugt ausschließlich `ignore-auto-dns=yes`. |
| `netmon/features/dns_controller.py` | `System (DHCP/auto)` wird vor NM-/Drop-in-/Resolveraktionen mit sichtbarem Grund abgelehnt. Der nicht mehr erlaubte DHCP-Folgezweig entfällt. Statische manuelle Profile verwenden weiterhin den restriktiven Pfad. |
| `netmon/app.py` | `_apply_automatic_dns_restore_choice()` verweigert auch statische automatische ISP-Fallbacks unter dem bestehenden Lock. `on_vpn_disconnected()` entfernt nach einer verweigerten Freigabe weder Drop-in noch startet es resolved neu. |

Der sichtbare Grund lautet:
„DHCP-/ISP-DNS-Freigabe vorläufig gesperrt; sichere Koordination mit
VPN-Wechseln fehlt.“ Die API meldet False beziehungsweise `success=False`,
keinen angenommenen Erfolg. Es gibt keinen neuen Schalter oder Gatezustand,
mit dem die Sperre automatisch umgangen wird.

**Regression:** Die vier ursprünglichen Interleaving-Fälle verlangen jetzt
unveränderte IPv4-/IPv6-Eigenschaften und keinerlei Schreibauftrag. Dazu
kommen zwei direkte Service-Einstiege, vier automatische Restorefälle
(DHCP/statischer Fallback × Übergang ja/nein) und ein echter Disconnect-
Workerpfad mit synchronem Threadfake. Dieser prüft zusätzlich den erhaltenen
Drop-in und das Ausbleiben eines Resolver-Neustarts. Insgesamt 11 F6-Fälle
bestehen. Vier Bestandsfälle, die noch erfolgreiche Freigaben verlangten,
prüfen nun die gewählte Verweigerung; die Auswahlpräferenz wird weiterhin
separat geprüft. Kein Test wurde übersprungen oder mit xfail versehen.

**Funktionale Einschränkung:** System-DHCP-Auswahl und automatische ISP-
Restores einschließlich öffentlicher statischer Fallbacks sind nicht
verfügbar. Nach VPN-Ende kann die bisherige DNS-Konfiguration erhalten und
nicht mehr erreichbar sein. Manuelle statische Profile bleiben möglich,
soweit deren bestehende VPN-/Übergangsprüfungen sie zulassen. Die Sperre
verhindert keinen bereits vorhandenen Leak und keine Änderung durch fremde
Systemakteure. Sie verhindert die von diesen NetMon-Pfaden ausgehende
unsichere Freigabe; sie ist keine allgemeine Kernel-Egressgarantie.

## Tatsächliche Prüfergebnisse

Alle Rohbelege liegen unter `integration-evidence/f1-f6-20261030/`.

| Lauf | Ergebnis |
|---|---|
| Ursprüngliche F1/F6-Charakterisierungen | 7 PASS; sie reproduzieren ausdrücklich die unsicheren Abläufe, keine Sicherheits-PASS. |
| Neue F1-Sicherheitsassertion vor Codefix | FAIL: physische Defaultquelle wurde nicht als Konflikt erkannt. |
| F1-Nachlauf, vollständige betroffene DNS-Untermenge | 251 PASS. |
| Neue F6-Sicherheitsassertion vor Codefix | FAIL: tatsächliche NM-Änderung/Aktivierung statt Verweigerung. |
| Gezielter F6-Nachlauf | 11 PASS. |
| Erster F6-Kompatibilitätslauf | 254 PASS, 4 FAIL durch bisherige Erfolgsoracles für jetzt gesperrte Freigaben. |
| Erster Anpassungsnachlauf | 252 PASS, 1 FAIL; eine Cloudflare-Erfolgsassertion war noch nicht vollständig umgestellt. |
| Vollständige betroffene Suite nach vollständiger Anpassung | 258 PASS. |
| Beauftragter Starter `python3 -B scripts/test_dns_integration.py all` | Alle sechs Phasen PASS; Einzelzahlen unten. |
| Syntax, black, ruff der sieben geänderten Pythondateien | PASS. |
| Reale DNS-/Firewall-/NM-/Resolvertests; unisolierter GUI-Dauerbetrieb | **NOT RUN**. |

| Phase des abschließenden Starters | PASS | Fehler / Skip |
|---|---:|---:|
| Imports, Module und Writer-Sicherheit | 63 | 0 / 0 |
| Gezielte DNS-Units | 23 | 0 / 0 |
| DNS-Integration einschließlich neuer Regressionen | 258 | 0 / 0 |
| Übernommene 48 Fälle | 48 | 0 / 0 |
| Angrenzende Regressionen | 626 | 0 / 0 |
| GUI-/Startup-Fälle | 23 | 0 / 0 |

Die Gruppen überschneiden sich: 1041 Ausführungen entsprechen 1017
unterschiedlichen IDs. Die 19 zusätzlichen Parameterfälle sind zwölf
F1- und sieben zusätzliche F6-Fälle; bestehende Gegenbeispiele werden jetzt
als Sicherheitsregressionen weitergeführt. Die GUI wurde mit echten Widgets
und den bereits vorhandenen Statusfakes geprüft, keine echten Dienste.
Frühere Fehlläufe bleiben erhalten.

## Erhaltung und Vorbereitung des praktischen Tests

Die vollständige Datei `tests/test_netmon_killswitch.py` und damit alle
48 IDs bleiben bytegleich. Die KS-P1-Startupkorrektur ist bytegleich.
In App wurden ausschließlich die beiden oben bezeichneten Methoden
geändert. Originalprojekt, bestehendes Archiv, Isolationsrunner und
Teststarter sind unverändert. Es gab keine Installation, Hoständerung,
Commits oder Pushes. Vorstände, finaler Diff, Hashes und Erhaltungsnachweis
liegen im Nachweisverzeichnis; das bestehende Integrationsmanifest wird
auf die neuen Dateien aktualisiert. Historische Berichte bleiben als
frühere Prüfstände erkennbar.

Für einen praktischen Anwendungstest ist die Kopie mit den genannten
Einschränkungen vorbereitet. Der nächste reale Test braucht weiterhin einen
gesondert freigegebenen, wegwerfbaren privaten Zielrechner mit privaten
Resolvern, begrenzten Schreibrechten und einem unabhängigen Restore.
DHCP-/ISP-Freigabe ist dabei nicht als funktionierender Testpfad einzuplanen.
Ein späteres sicheres Wiederzulassen dieser Funktion erfordert eine eigene
technisch belegte Lösung; es ist mit diesem Auftrag nicht implementiert.
