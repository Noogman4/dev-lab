# NetMon V4: eingefrorener Prüfstand nach Runde 9 und optionaler Z3-Korrektur

Die unabhängige Runde 9 beurteilt den V9-Stand als für eine ausdrücklich
freizugebende gezielte VM-Prüfung vorbereitet. Das ist keine Gesamtabnahme und
keine Produktiv- oder VM-Startfreigabe. Der dort als optional und nicht blockierend
benannte Restfall Z3 wurde anschließend klein korrigiert und gezielt geprüft.
Diese nachträgliche Änderung ist vom unabhängigen V9-Urteil zu unterscheiden.

```text
/dev-lab/projects/dev-lab/backups/netmon-unification-20261031/candidate
```

Branch: `integration/netmon-v4-common-20261031`.
Basis: `baecee92f83764ca7af73ee0c61cf0f29f4bff3d`.
Alle Änderungen bleiben uncommittet. Keine weitere Integrationskopie,
Installation, Commits oder Pushes. Keine produktiven GUI-, Firewall-, DNS-,
VPN- oder Mountänderungen und kein VM-Start. Beide Originalstände und der
wiederhergestellte Internetzugang bleiben erhalten. H1 wird nicht neu
privilegiert geprüft.

## Z3: Logging-Markierung verdeckte das Interface

UFW zeigt etwa `Anywhere on wg0 (log)` oder `(log-all)`. Die Interface-
Extraktion erwartete jedoch das Interface am Feldende. Dadurch ging seine
Bindung verloren: Eine geloggte tunnelgebundene 443-Regel wurde wieder als
global gewertet und konnte nach Mutationen in Recovery führen. Bei inaktiven
Profilen fehlte das Interface im Sperrplan, was vor der Mutation zum Fehler
führte. Geloggte globale DENYs wurden im Controller nicht als global erkannt;
die Root-Prüfung verweigerte sie weiterhin. Es gab kein falsches ON, und AUS
blieb exakt. Die drei ersten Parser-Nachstellungen bestätigen den Verlust
von Interface beziehungsweise globaler Sperrerkennung auf V9.

`parse_ufw_structured_rule()` entfernt jetzt nur eine abschließende bekannte
Logging-Markierung aus dem Ziel- oder Quellfeld, nachdem der Familienmarker
normalisiert wurde und bevor das Interface zerlegt wird. Beide Positionen,
`log`/`log-all` und IPv4/IPv6 sind berücksichtigt. Die übrige Parsing- und
Regelprüfungslogik wird nicht umgebaut.

Die Logging-Markierung bleibt in der angezeigten Regel erhalten, der ursprüngliche
Statustext im Feld `raw` unverändert. So bleiben schlichtes ALLOW, ALLOW log
und ALLOW log-all auch für die bestehende Identitäts-, Duplikat- und Auswahl-
logik unterscheidbar. Echte gleiche geloggte Duplikate werden weiterhin markiert;
Logging- und Nicht-Logging-Regeln werden nicht versehentlich zusammengefasst
oder bei der Auswahl gleichgesetzt. Das strukturierte Ergebnisschema bleibt
gleich; kein neuer Pflichtschlüssel wird eingeführt.

Ein AST-Vergleich bestätigt: Die einzige geänderte Produktfunktion gegenüber
V9 ist `parse_ufw_structured_rule` in `netmon/features/firewall_controller.py`.
`netmon/core/ufw_snapshot.py` ist bytegleich zum unabhängig geprüften Stand.
Root-RPC-Protokoll bleibt **9**. Snapshotformat, Originalautorität, ACK,
Schreib-/DNS-/Konfliktgates, Z1-/Z2-/Y2-Prüfung bleiben bestehen.

## Aktuelle gezielte Nachweise

Die normale betroffene Auswahl besteht mit **529 Erfolgen**. Sie prüft auch
Parser-Verbraucher, Logging-Anzeigen, beide Feldpositionen/Familien, globale
Sperrerkennung sowie die getrennte Identität und präzise Auswahl der Logmodi.
Syntax, Black, Ruff und `git diff --check` bestehen für drei geänderte Pythondateien.

Die neue native Datei enthält 14 Fälle: geloggte vollständige und dienstbezogene
Freigaben auf aktivem Tunnel und inaktivem Katalogprofil mit EIN, Boolean,
Klassifikation, Resync und exaktem AUS; globale geloggte DENYs in IN/OUT mit
unveränderten Dateien/Laufzeit und null Kernel-Commits; `eth0` mit geloggter
443-Regel ebenfalls vor Mutation verweigert. Zwei frühere Z1- und eine Y2-
Kontrolle ergänzen die Auswahl. Die native Auswahl besteht mit **17 Erfolgen** (14 neue Fälle und drei frühere
Kontrollen). Die exakten Ergebnisse und IDs stehen
in `../../review-response-v10-20261101/test-results-v10.json`.

Die ersten drei fehlgeschlagenen Parser-Nachstellungen bleiben als solche
archiviert und sind keine Abnahmeergebnisse. Alle abschließenden Prüfungen
verwenden denselben unveränderten Produktcode und dieselben finalen Daten.
Tatsächliche App-Deskriptoren, Profilinventar/Resolver/Endpoint-Parser und private
reale Profile bleiben aktiv; nur externe I/O-, Link- und UI-Grenzen sind ersetzt.
Echter UFW-Code/ufw-init laufen in privaten Datei-/Netz-/PID-Namensräumen ohne
Capabilities mit festen Kernel-Stubs. Kein tatsächlicher Paketfluss oder realer
Tk-/NetworkManager-/Tunnelabbruch wird behauptet.

## Unabhängige Evidenz auf V9

Die externe Runde 9 bestätigte 176/176 Fälle in der vollständigen nativen Suite,
26 native und 512 normale gezielte Fälle. Die normale V9-Gesamtsuite ergab
5.016 Erfolge, dieselben 14 Fehler-IDs wie V5 und 327 Skips: kein vollständig
grüner Lauf. Konsolen und JUnit-Dateien sind zusätzlich archiviert; Fallzahlen,
Fehlerfreiheit der nativen Suite und die 14 normalen IDs wurden kontrolliert.
Das ist V9-Evidenz, keine vollständige V10-Prüfung.

Der externe Sweep prüfte laut Review 72 plausible Regelformen mit und ohne
Tunnel: 138 erfolgreiche komplette Zyklen, fünf korrekte vorzeitige Ablehnungen
und einen Post-Mutationsfall Z3. Das deckt nicht alle Kombinationen ab und ist
keine Freigabe des gesamten gemeinsamen Kandidaten. Die Rohdaten des v9-
Reviewverzeichnisses bleiben erhalten.

## Gesicherter Stand und nächste Entscheidung

`../../review-response-v10-20261101/` enthält eine strukturierte, ausdrücklich
nicht bytegleiche Archivnotiz zum inline übergebenen Review, das vollständige
externe v9-Verzeichnis, zusätzliche JUnit-/Konsolennachweise, den unveränderten
V9-Vorherstand, gezielten und vollständigen Patch, aktuelle Test-/Qualitätsbelege,
Manifest, Prüfsummen, `handoff-v10.json` und einen optionalen Z3-Prüfauftrag.
Der vollständige Originalreview bleibt im Chat. Frühere Übergaben bleiben
unverändert; die vorbestehende `d.py` wurde nicht ausgeführt und ältere `.pyc`
bleiben außerhalb der Quellmanifeste. Die HTML-Vorschau ist kein Produktcode.

Eine zusätzliche externe Z3-Stichprobe kann die nachträgliche kleine Änderung
prüfen; Z3 war laut unabhängigem Urteil keine VM-Voraussetzung. Der positive
V9-Befund darf trotzdem nicht als bereits erfolgte unabhängige Prüfung des
geänderten V10-Manifests ausgegeben werden. Es folgt daraus kein automatischer
VM-Start. Nächste gemeinsame Entscheidung ist die ausdrücklich freizugebende
gezielte VM-Prüfung am konkret eingefrorenen Stand.

Echte nft-/legacy-Semantik, installierter Helfer/sudo, tatsächliche Tk-/
NetworkManager-Abläufe, SIGKILL/Stromausfall und dpkg bleiben VM-Aufgaben.
INPUT-/FORWARD-Scope bleibt unverändert, keine Router-Isolation behauptet.
H1 und der vollständige damalige Systemzustand bleiben ungeprüft. Keine
Produktivfreigabe oder unabhängige Selbstabnahme.


## V11: Echter VPN-AUS-Pfad, VM-P2-1 (2026-11-01)

Dieser Abschnitt ersetzt den früheren V10-Übergabestatus; die vorherigen Abschnitte
bleiben historische Nachweise. Der Nutzer hat die Wegwerf-VM und anschließend die
gezielte Korrektur freigegeben. Die Originale und die produktiven Dienste werden
weiterhin nicht verändert.

Die echte V10-App reproduzierte mit `allow out on wg0 log ... 443/tcp` nach VPN AUS
zweimal Root=`on`, Boolean=False, Klassifikation=`unknown` und fehlenden Hinweis.
Der Parser behielt das Interface korrekt. Es fehlte der Offline-Abgleich nach
`cleanup_wireguard_interfaces`; erst dieser setzt die erforderlichen führenden
Interface-Sperren. Der `vpn_off`-Funktionskörper war gegenüber HEAD unverändert;
der erste Zeitpunkt des gesamten wechselwirkenden Fehlers ist damit nicht bestimmt.

`vpn_off` verwendet nun den geschützten Root-Zustand, gleicht nach dem Tunnelabbau
nur eine bereits aktive geschützte Transaktion ab und behandelt dessen Fehler
explizit. Die neue `require_active`-Bedingung in `SnapshotStore.begin` wird innerhalb
des bestehenden Root-UFW-Locks vor der ersten Mutation geprüft. OFF/reviewed/
recovery/applying/fehlende Sicherung können dadurch keine frische Aktivierung
erhalten. Der Client verweigert ältere Helfer über RPC-Protokoll **10**. Es gibt
keinen neuen RPC-Endpunkt und kein neues Format der geschützten Sicherung.

Während des verwalteten VPN-AUS-Ablaufs bleibt ein sitzungsbezogenes Flag für den
DNS-Abschluss gesetzt. Bei einem Fehler bleibt es gesetzt und der Aufruf liefert
False mit einer eindeutigen Meldung. Verifizierter Killswitch-Abgleich oder explizites
verifiziertes AUS löschen es. Bereits eingeplante DNS-Abschlüsse prüfen dieses Flag.
Unbekannte/recovery-Root-Zustände erhalten keine neue Schreibautorität. Ein inzwischen
erfolgtes explizites AUS gewinnt; es gibt keinen Wiederholungsversuch als frisches EIN.
Das Flag ist kein Ersatz für die persistente Root-Rollback-/Recovery-Autorität.

Die strenge globale Portprüfung, Benutzerregeln, Snapshot-Originale, IPv4/IPv6- und
Konfliktgates bleiben erhalten. Es gibt kein pauschales UFW-Deaktivieren und kein
Verschieben bestehender Regeln. Die Tests prüfen auch den unveränderten Original-
Datensatz bei fehlgeschlagenem Offline-Preflight und die exakte Wiederherstellung.

Auf dem Produktstand bestehen 419 gezielte normale und 46 neue native Fälle. Die
normale Gesamtsuite hat 5.063 Erfolge, genau die bereits archivierten 14 Fehler-IDs
und 329 Skips. Der zunächst am ersten bestehenden Fehler angehaltene Rohlauf bleibt
als Zwischenlauf erhalten. Eine neue native Gesamtsuite wird nicht behauptet.

Die echte V11-VM-Stichprobe verwendet legacy-Netfilter, sudo, geschützten
installierten Helfer, wirkliche Tk-Ereignisschleife im Gast-Xvfb und eigene echte
WireGuard-Links/Gegenstelle. Boolean, Klassifikation und Root stimmen nach VPN AUS
sofort und nach Wartezeit mit `on` überein; das tatsächliche Hinweisfenster erscheint.
Der anschließende reale wg-quick-Wechsel auf wg1 transportiert inneres IPv4/IPv6,
auch ein zweites VPN AUS bleibt korrekt. Kontrolliert fehlgeschlagener Offline-
Preflight pausiert den DNS-Abschluss und verändert weder Dateien/Laufzeit noch
Root-Datensatz. In beiden Fällen stellt explizites AUS exakt den jeweiligen
Benutzer-Ausgangszustand wieder her. Active-only-OFF-Gate und echter alter
Protokoll-9-Helfer sind separat am installierten Client geprüft. Das ist keine
vollständige DNS-/NetworkManager-/nft-VM-Abnahme und keine unabhängige Selbstprüfung.

V10 ist vollständig in `../../review-response-v11-20261101/before-sources.tar.gz`
mit seinem ursprünglichen Manifest archiviert; VM-Rotbelege liegen getrennt unter
`../../vm-lab-v10-20261101/phase2/`. V11-Belege bleiben in dessen `v11/`-Nachbarordner.
Die VM-Abnahme wird erst nach unabhängiger Nachprüfung des neuen V11-Manifests
fortgesetzt. Host-H1, SIGKILL/Stromausfall und weitere offene VM-Fälle bleiben offen.


## V12: Hostname-only-Fortsetzung und verzögerter DNS-Abschluss (2026-11-01)

Dieser Abschnitt ist der aktuelle Stand; V11 und frühere Abschnitte bleiben
historische Nachweise. Grundlage ist Claudes unveränderter V11-Bericht unter
`../../review-v11-independent-20261101/`. Der Nutzer hat die gezielte Korrektur
von F1/F2 und die Wegwerf-VM-Läufe freigegeben. F3/F4 bleiben separat offen.

**F1:** Nach dem Abbau des einzigen Tunnels hat ein Profil mit Hostname-Endpoint
keinen aufgelösten IP-Endpoint im Plan. V11 verweigerte diesen leeren Plan und
seine lokale Verifikation, obwohl der Root-Killswitch weiterhin geschlossen war.
`SnapshotStore.begin` erlaubt ihn nun nur mit `require_active=True`, bestehendem
aktiven geschützten Datensatz und erfolgreicher Verifikation des bisherigen Plans.
Ein frisches leeres EIN und unmarkierte alte leere Pläne erhalten diese Autorität
nicht. Der optionale boolesche Root-Datensatzwert `closed` ist nur für einen leeren
Interface-/Endpoint-Plan zulässig. Der Helfer bestätigt ihn im Status ausschließlich
nach vollständiger Datei- und Laufzeitprüfung. Controller-Boolean und Klassifikation
verwenden für leere Pläne diese Root-Bestätigung; unbekannte oder fehlerhafte
Antworten genügen nicht. Nachsynchronisation mit konkretem Plan entfernt das Merkmal.
Globale Sperren, Benutzerregeln, IPv4/IPv6-Prüfungen und Restore-Konfliktgates bleiben
wirksam. Das RPC-Protokoll steigt auf **11**, Datensatzversion bleibt 1 mit optionalem
validiertem Feld. Es wird keine DNS-Ausnahme zum Auflösen von Hostnamen geöffnet.

**F2:** V11 löschte nach erfolgreicher Wiederherstellung lediglich das Pause-Flag.
Eine zuvor abgebrochene DNS-Vorbereitung bzw. Abschlussplanung blieb verloren.
Die App merkt nun den aufgeschobenen Abschluss und stellt nach Freigabe der äußeren
Netzoperation genau einen Rückruf zu. Dieser prüft seine Generation, Pause,
Netzkoordinator und Root-Recovery erneut, führt die vorhandene Vorbereitung unter
eigener Netzoperation aus und plant den vorhandenen Abschluss. Neue VPN-Übergänge
und neue Vorbereitungen entwerten alte Rückrufe. Der Monitor darf dabei die
Vorbereitung nicht überspringen. Bei weiter bestehender Recovery wird nicht endlos
neu geplant. Ein unerwarteter Vorbereitungsfehler wird protokolliert; es folgt keine
unbegrenzte Wiederholung. DNS-Guard-Beobachtung bleibt möglich, automatische
Reparatur und `enforce_dns_clean` verändern während der Pause keine DNS-Konfiguration.
Die vorhandene Verweigerung automatischer ISP-DNS-Freigabe bleibt unverändert; die
Review-Hypothese eines tatsächlichen ISP-DNS-Ausfalls ist kein nachgewiesener Befund.

Lokale Nachweise auf dem Endstand: 439 gezielte normale Tests, 7 gezielte native
Fälle; normale Gesamtsuite 5.083 bestanden, 14 Fehler, 330 übersprungen. Die 14 IDs
sind identisch zum archivierten V11-Lauf, keine neuen Fehler-IDs; die Gesamtsuite ist
weiter rot. Keine neue vollständige native Suite. Syntax, Black, Ruff und Diff-Check
sind separat protokolliert. Fehlgeschlagene und erfolgreiche Zwischenläufe bleiben
mit ihrer Einordnung erhalten, einschließlich der korrigierten Testverfügbarkeit
von UFW und des SimpleNamespace-Kompatibilitätsfalls.

Echte legacy-VM: Die installierte Tk-App verwendet ein ausgewähltes Profil mit
Hostname-Endpoint ohne zusätzliche ausgewählte IP. EIN, VPN AUS, Root=`on,closed`,
Boolean/Klassifikation, tatsächlicher Hinweis, wg-quick-Wiederverbindung, zweites
VPN AUS und exaktes Killswitch AUS bestehen. Die kontrollierte Gast-Hosts-Auflösung
ist kein allgemeiner Hostname-DNS- oder Tunnel-Paketflussbeweis. Beim provozierten
Offline-Preflight-Fehler bleibt DNS pausiert; nach explizitem AUS laufen genau eine
Vorbereitung und ein ungepauster Abschluss nach Freigabe des UFW-Locks und der
äußeren Netzoperation. Das ist kein Nachweis einer automatischen ISP-DNS-Freigabe.
Frisches Active-only bei OFF und echter älterer Protokoll-10-Helfer werden ohne
Mutation verweigert. Nach echtem Gast-Neustart bleibt der neue geschlossene Plan
inklusive Regelsatz exakt; explizites AUS stellt die Sicherung exakt wieder her.
Ein erster SSH-Versuch während des Boots lief in einen Timeout; der zweite war
erfolgreich, ohne Recovery-Eingriff. Alle 118 installierten Python-Dateien sind
inhaltlich und hinsichtlich Root-Eigentum/Schreibschutz geprüft.

Paket: `1.1.21~v4dnstest20261101.1201`. Ein vorheriger echter App-Lauf endete wegen
nicht deaktivierter Gast-Startdialoge im Timeout; seine funktionalen Belege und
Diagnose bleiben separat erhalten. Nach Seed-Korrektur bestehen beide Endläufe.
Die Dialogkorrektur ist ausschließlich Testvorbereitung, keine Produktänderung.
Der VM-Datenträger bleibt nach sauberem Shutdown mit Snapshot gesichert.
V11 ist vor der Änderung vollständig mit Manifest und Tar-Archiv gesichert.
V12-Unterlagen liegen unter `../../review-response-v12-20261101/`.

Unabhängige Nachprüfung ausstehend. Keine Gesamtabnahme oder Produktivfreigabe.
F3/F4, V12-nft, vollständiger NetworkManager-/DNS-Guard-Pfad, SIGKILL/Stromausfall,
weitere Paket-Lebenszyklusfälle und Host-H1 bleiben offen. Beide Originalstände,
produktive Firewall/DNS/VPN und Git-Index/HEAD werden nicht verändert. Externe
Änderungen an FETCH_HEAD/Git-Objekten begründen keine unbelegte Akteurszuordnung;
eine bytegleiche Unverändertheit des gesamten .git-Verzeichnisses wird nicht behauptet.


## V13: Begrenzte F3-Korrektur (2026-11-01)

Auf ausdrücklichen Auftrag wird ausschließlich F3 korrigiert. V12 einschließlich
992-Dateien-Manifest wurde vor der ersten Änderung vollständig archiviert;
`../../review-response-v13-20261101/before-sources.tar.gz` enthält den Vorherstand.
F4 bleibt zurückgestellt, kein pauschaler weiterer Review-/Refactoring-Auftrag.

Die vorherige Analyse unter `../../analysis-f3-f4-v12-20261101/` reproduzierte F3
auf V12: Nach externem Verlust oder fehlgeschlagenem Wechsel blieb Root `on`, aber
Boolean `False` und lokale Klassifikation `unknown`. Die zentrale App-Anzeige war
weiter ON; beide OUTPUT-Policies blieben DROP. Netzwerkreset und Internet-AN wurden
in der Analyse nur gelesen, nicht als komplette echte Abläufe ausgeführt.

`vpn_controller.sync_killswitch_after_tunnel_change` führt jetzt den bereits im
VPN-AUS-Pfad vorhandenen Root-Abgleich gemeinsam aus. Es zählt der geschützte
Root-Zustand, nicht das Boolean nach dem Abbau. Nur Root ON führt zu einem
`require_active`-Abgleich; der Helfer prüft diese Voraussetzung unter seinem Lock.
Ein neueres explizites OFF gewinnt; absent/reviewed/off erzeugen kein neues EIN,
unknown/recovery pausieren DNS und verändern nicht eigenmächtig die Firewall.
Der fehlgeschlagene Start ruft die Recovery nun ebenfalls auf; das unvollständige
Cleanup nutzt die korrigierte Recovery-Methode. Bei Teilabbau bleiben laufende
andere Tunnel geplant. Die übrigen erfolgreichen Wechselpfade bleiben erhalten.

Der externe Verlust pausiert DNS und merkt einen ausstehenden Abgleich. Die App
startet hierfür einen Hintergrundauftrag unter ihrer vorhandenen Netzkoordination,
keine privilegierte Mutation im Tk-Monitor. Belegte Netzoperationen verschieben ihn;
Ende-Hook und Monitor können ihn erneut anstoßen. Ein unter der Koordination erneut
geprüftes Pending-Flag verhindert doppelten Abgleich. Der Auftrag liest immer die
aktuellen Interfaces und den aktuellen Root-Zustand, auch wenn inzwischen ein neuer
Tunnel besteht oder AUS ausgeführt wurde. Bei einem abgelehnten Abgleich bleibt
DNS pausiert; die ausstehende Aktion wird nicht endlos automatisch wiederholt.
Nach Erfolg läuft die V12-DNS-Vorbereitung und Abschlussplanung nach Freigabe der
Netzoperation weiter. Der externe Verlust erhält eine Logmeldung; es wird kein
Tk-Dialog direkt aus dem neuen Worker aufgerufen.

Root-Helfer und Firewall-Controller sind bytegleich zu V12, Protokoll bleibt 11.
Der AST-Vergleich begrenzt Produktänderungen auf neun vorgesehene Funktionen in
App und VPN-Controller. Keine neue Abhängigkeit, keine Änderungen an Benutzerregeln,
keine DNS-Freigabe und kein pauschales UFW-Deaktivieren. Ein älterer Unit-Test wurde
von Boolean-Autorität auf explizite Root-Autorität umgestellt; ein als False
vorgegebenes Boolean darf nun die aktive geschützte Fortsetzung nicht verhindern.

Endstand: 588 gezielte normale Tests und 12 native Fälle bestanden. Native neue
Fälle: externer Verlust mit IPv4-/IPv6-Logregeln, IP und Hostname, fehlgeschlagener
Wechsel, Teil-Cleanup bei weiter laufendem zweitem Tunnel, verweigerter Offline-
Preflight mit unverändertem Zustand und DNS-Pause sowie verzögert bearbeiteter Verlust
nach explizitem AUS ohne Reaktivierung. V11-/V12-Kontrollen bleiben grün. Normale
Tests prüfen außerdem beide Netzkoordinator-Varianten, Verschachtelung/Belegung,
DNS-Reihenfolge, unbekannte Root-Zustände und unerwartete Worker-Fehler. Ein erster
neuer Test griff auf ein absichtlich gelöschtes Attribut zu; korrigiert wurde nur
dieser Testzugriff auf `dict.get`. Rohbelege bleiben erhalten. Syntax, Black, Ruff
und Diff-Check sind grün. Keine neue normale oder native Gesamtsuite; die bisherigen
14 bekannten Gesamtsuite-Fehler bleiben V12-Historie, keine neue Gesamtfreigabe.

Paket `1.1.21~v4dnstest20261101.1301` wurde isoliert gebaut, 118 Python-Dateien
inhaltlich und syntaktisch gegen die Quellen geprüft; reguläre Paketdateien sind
Root-eigen und nicht gruppen-/weltbeschreibbar. Maintainer-Skripte wurden nur auf
Syntax geprüft, nicht ausgeführt. Der erste Build hatte wegen des schreibgeschützten
/dev/null Warnungen und bleibt separat erhalten. Der finale Build verwendet ein
privates /dev und ist ohne diese Warnungen abgeschlossen. Keine Host-Installation.
V13 wurde noch nicht in der VM installiert oder ausgeführt; V12-VM-Belege bleiben
historisch. Nächster vereinbarter Schritt ist ein begrenzter Paket-/Alltagstest nach
Einordnung der ausstehenden unabhängigen F1/F2-Rückmeldung, keine automatische neue
breite Review-Schleife. F4 und die bekannten VM-/Host-H1-Grenzen bleiben offen.
Beide Originale bleiben unverändert; keine Commits, Pushes oder Produktivfreigabe.


## V14: Nur G1/G2, sichere Killswitch-Erhaltung und DNS-Wiederanlauf (2026-11-02)

Der Nutzer hat nach Einordnung des V12-Reviews ausschließlich die Korrektur von
G1/G2 freigegeben. G3/G4 und F4 bleiben zurückgestellt. Originalreview und statischer
V13-Abgleich: `../../review-v12-independent-20261102/`. V13 wurde vor der ersten
Änderung vollständig mit 994-Dateien-Manifest archiviert. Vier eigene isolierte
Charakterisierungsläufe bestätigen die Fehler auf V13: Internet AN endet nach dem
automatischen AUS mit OUTPUT ACCEPT in beiden Familien; der vollständige vereinfachte
Spielmodus-Start und -Rollback endet ebenfalls OFF; der DNS-Wiederanlauf führt bei
stehendem Tunnel die Vorbereitung mit Resolver-Neustart aus. Dort ist die DNS-
Transportfunktion gestubbt; die echte DNS-Auswirkung und Paketfluss sind nicht gemessen.
Die V13-Probe ersetzt die alte DNS-Linkbereinigung durch einen aufgezeichneten Revert;
der Resolver-Neustart stammt aus der tatsächlichen Vorbereitung. Der V14-Nachtest
verwendet auch die echte Linkbereinigung mit einer privaten resolvectl-Statusantwort.

**G1:** Internet AN entfernt die temporäre Killswitch-Deaktivierung und den frischen
EIN-Versuch. Ein bestehender verifizierter geschlossener Plan bleibt erhalten. Falls
Boolean und Firewall nach einem Restore-Abbruch nicht übereinstimmen, wird nur der
vorhandene aktive Root-Zustand über den V13-Helfer abgeglichen; kein frisches leeres
EIN, keine Rücknahme eines ausdrücklichen OFF. Eine nicht vollständige Wiederherstellung
liefert nun False anstelle eines bloßen Loghinweises mit True. Die Spielmodus-
Aktivierung verweigert ein Profil mit verlangter Killswitch-Pause vor der ersten
Änderung, solange der Killswitch aktiv ist. Ausdrückliches AUS oder ein anderes Profil
bleiben Benutzerentscheidungen. Nach bewusstem AUS sind die optionalen Spielfreigaben
weiter testbar; ihre bestehenden Unit-Fixtures bilden nun diesen Ausgangszustand ab.
Es wird kein neuer Wiederaufnahme-/Sicherungsmechanismus mit weiterer Root-Autorität
eingeführt und die Sperre gegen frische leere Pläne nicht gelockert.

**G2:** Ein zusätzliches sitzungsbezogenes Merkmal kennzeichnet fehlende Vorbereitung.
Es wird durch die Firewall-bedingte Pause gesetzt und durch eine neue tatsächliche
Vorbereitung gelöscht. Das bloße Pausieren des Finalizers wegen einer anderen
Netzoperation setzt es nicht. Im vorhandenen Rückruf unter der Netzkoordination
wird nur bei tatsächlich fehlender Vorbereitung und strikt bestätigtem Fehlen
laufender WireGuard-Interfaces vorbereitet. Ein neuer oder nicht entfernbarer Tunnel
überspringt diese alte Vorbereitung; eine neue Abfrage-/Resolver-Bereinigung über den
laufenden Tunnel entfällt. Bei unbekannter Interface-Lage wird keine Vorbereitung
autorisiert. Dazu erhält get_wg_interfaces einen optionalen strict-Modus; bestehende
Aufrufer behalten ihr bisheriges Verhalten. Anschließend wird ausschließlich der
vorhandene Finalizer mit Generationsprüfung geplant, ohne Rekursions-/Doppellauf.
Die normale Vorbereitung vor einem beabsichtigten Profilwechsel bleibt erhalten.
Die automatische ISP-DNS-Freigabe wird weiterhin blockiert. G3-Pausenmeldung und
G4-Slot-Reconcile werden ausdrücklich nicht als behoben dargestellt.

Produktänderungen sind auf sieben Funktionen in App und VPN-Controller begrenzt.
Root-Helfer und Firewall-Controller sind bytegleich zu V13; RPC bleibt 11, keine
neuen Abhängigkeiten. Endkontrollen: 778 gezielte normale Tests. Die native Auswahl
hat 17 Erfolge (neue G1/G2-Fälle und gezielte V11/V12/V13-Kontrollen). Ruff wies danach
auf zwei durch den G1-Umbau überflüssige lokale vpn_restore_ok-Zuweisungen hin. Nur
diese wurden entfernt; der vollständige AST ohne diese Zuweisungen bleibt gleich.
Der Zwischenstand ist als pre-lint-app.py archiviert. Danach wurden die 778 normalen
und die zwei direkt betroffenen nativen G1-Fälle erneut auf dem Endstand ausgeführt.
Alle grün; Syntax, Black, Ruff und Diff-Check ebenfalls grün. Keine neue normale oder
native Gesamtsuite; 5.083/14/330 bleiben V12-Historie, keine grüne Gesamtbehauptung.

Paket `1.1.21~v4dnstest20261102.1401` wird aus dem endgültigen Quellstand isoliert
gebaut und gegen alle 118 enthaltenen Python-Dateien geprüft. Reguläre Paketdateien
sind Root-eigen und nicht gruppen-/weltbeschreibbar. Maintainer-Skripte sind nur auf
Syntax geprüft. Der erste Build vor der reinen Lint-Bereinigung bleibt gesondert
erhalten. V14 wurde nicht installiert oder in der VM ausgeführt. Echte V12-VM-Belege
werden nicht als V14-Abnahme ausgegeben. Für künftige Reviews wird zusätzlich ein
vollständiges eingefrorenes V14-Quellarchiv mit Manifest gesichert; kein paralleles
Weiterentwickeln des geprüften Ordners. Keine automatische neue breite Prüfrunde.
Nächster Schritt bleibt der begrenzte Paket-/Alltagstest in der Wegwerf-VM; Host-H1,
weitere VM-Abnahmegrenzen, G3/G4 und F4 bleiben offen. Keine Commits/Pushes, keine
produktiven Firewall-, DNS-, VPN-, Mount- oder Diensteingriffe, keine Produktivfreigabe.
