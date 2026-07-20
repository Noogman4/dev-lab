# Kernel Sysctl Baseline

## Ziel

Dieses Dokument beschreibt die fuer NetMon relevante Sysctl-Baseline als
technisch pruefbare Referenz fuer Desktop-, Entwicklungs- und bei Bedarf auch
Server-Systeme. Die Angaben sind absichtlich profilbezogen und nicht als
blinde "mehr ist immer besser"-Regel zu verstehen.

## Lade-Reihenfolge und Prioritaet

Sysctl-Werte koennen aus mehreren Quellen geladen werden:

```text
/usr/lib/sysctl.d/
/run/sysctl.d/
/etc/sysctl.d/
/etc/sysctl.conf
```

Wichtige Praxisregel:

- Spaetere bzw. hoeher priorisierte Dateien koennen fruehere Werte
  ueberschreiben.
- Gleiche Parameternamen muessen deshalb immer inklusive ihrer finalen
  Herkunftsdatei bewertet werden.

Praxisbeispiel:

- `/usr/lib/sysctl.d/99-protect-links.conf`
- `/etc/sysctl.d/99-zz-netmon-hardening.conf`

Wenn beide Dateien denselben Parameter setzen, ueberschreibt die spaeter
bewertete lokale Konfiguration unter `/etc/sysctl.d/` typischerweise den
Distributionsstandard. Eine rein dateibezogene Sicht ohne Wertabgleich fuehrt
hier leicht zu Fehlinterpretationen.

## NetMon Apply-Stufe

Ab Sonntag, 19. Juli 2026, besitzt NetMon fuer die Sysctl-Baseline eine erste
explizite Apply-Stufe.

Rahmen:

- nur nach ausdruecklicher Bestaetigung
- nur mit vorhandenen Administratorrechten
- nur ueber eine dedizierte Drop-in-Datei
- kein blindes Ueberschreiben beliebiger Sysctl-Quellen

Aktueller Zielpfad:

- `/etc/sysctl.d/99-zz-netmon-hardening.conf`

Rollback-Grundsatz:

- Vor einer Aenderung wird der vorherige Zustand der Drop-in-Datei gelesen
- bei Fehlern stellt NetMon den vorherigen Stand wieder her oder entfernt die
  neu angelegte Datei
- anschliessend wird `sysctl --system` erneut geladen

Wichtig:

- Diese Apply-Stufe ist absichtlich auf Sysctl begrenzt
- PAM, Bootloader, Firewall-Regeln und Shadow-bezogene Aenderungen bleiben
  deutlich sensibler und werden nicht im selben Automatisierungsgrad behandelt

## Referenzparameter

### kernel.kptr_restrict

Parameter:
kernel.kptr_restrict

Erwarteter Wert:
2

Nutzen:
Schraenkt die Offenlegung von Kernelzeigern stark ein und erschwert
Informationsgewinn fuer lokale Angriffe.

Moegliche Nebenwirkungen:
Kernel-Debugging und einzelne Diagnosewerkzeuge koennen eingeschraenkt sein.

Eignung fuer Desktop:
Geeignet

Eignung fuer Entwicklung:
Geeignet, ausser bei speziellen Kernel-Debugging-Anforderungen

Eignung fuer Server:
Geeignet

Moegliche Ausnahmen:
Temporare Debug-Sessions mit dokumentierter Begruendung

Pruefbefehl:
`sysctl kernel.kptr_restrict`

Empfohlene Konfigurationsdatei:
`/etc/sysctl.d/99-zz-netmon-hardening.conf`

### kernel.sysrq

Parameter:
kernel.sysrq

Erwarteter Wert:
0

Nutzen:
Deaktiviert Magic-SysRq-Sonderfunktionen und reduziert Missbrauchsmoeglichkeiten
an lokal erreichbaren Konsolen.

Moegliche Nebenwirkungen:
Administratorische Notfallfunktionen stehen ohne temporare Umschaltung nicht zur
Verfuegung.

Eignung fuer Desktop:
Geeignet

Eignung fuer Entwicklung:
Geeignet

Eignung fuer Server:
Geeignet, sofern kein operativer Bedarf an SysRq besteht

Moegliche Ausnahmen:
Fehlersuche auf physisch kontrollierten Testsystemen

Pruefbefehl:
`sysctl kernel.sysrq`

Empfohlene Konfigurationsdatei:
`/etc/sysctl.d/99-zz-netmon-hardening.conf`

### kernel.perf_event_paranoid

Parameter:
kernel.perf_event_paranoid

Erwarteter Wert:
3

Nutzen:
Begrenzt unprivilegierten Zugriff auf Performance-Metriken und reduziert
moegliche Seitenkanalinformationen.

Moegliche Nebenwirkungen:
Bestimmte Profiling- oder Performance-Analyse-Workflows fuer Entwickler koennen
zusaetzliche Rechte benoetigen.

Eignung fuer Desktop:
Geeignet

Eignung fuer Entwicklung:
Geeignet mit moeglicher Ausnahme fuer Low-Level-Profiling

Eignung fuer Server:
Geeignet

Moegliche Ausnahmen:
Dedizierte Performance-Labors mit dokumentierter Risikoabwaegung

Pruefbefehl:
`sysctl kernel.perf_event_paranoid`

Empfohlene Konfigurationsdatei:
`/etc/sysctl.d/99-zz-netmon-hardening.conf`

### kernel.unprivileged_bpf_disabled

Parameter:
kernel.unprivileged_bpf_disabled

Erwarteter Wert:
1

Nutzen:
Verhindert unprivilegierte BPF-Nutzung und reduziert Angriffsoberflaeche in
einem sicherheitsrelevanten Kernel-Bereich.

Moegliche Nebenwirkungen:
Einzelne Entwickler- oder Observability-Werkzeuge koennen ohne Root nicht mehr
wie gewohnt arbeiten.

Eignung fuer Desktop:
Geeignet

Eignung fuer Entwicklung:
Geeignet mit Ausnahmen fuer spezielle eBPF-Workflows

Eignung fuer Server:
Geeignet

Moegliche Ausnahmen:
Dedizierte eBPF-Entwicklungs- oder Monitoring-Systeme

Pruefbefehl:
`sysctl kernel.unprivileged_bpf_disabled`

Empfohlene Konfigurationsdatei:
`/etc/sysctl.d/99-zz-netmon-hardening.conf`

### fs.protected_fifos

Parameter:
fs.protected_fifos

Erwarteter Wert:
2

Nutzen:
Erschwert Missbrauch von FIFOs in gemeinsam beschreibbaren Bereichen und
reduziert Race- oder Link-basierte Angriffe.

Moegliche Nebenwirkungen:
Seltene Altsoftware mit unsauberem FIFO-Handling kann betroffen sein.

Eignung fuer Desktop:
Geeignet

Eignung fuer Entwicklung:
Geeignet

Eignung fuer Server:
Geeignet

Moegliche Ausnahmen:
Legacy-Anwendungen mit dokumentiertem Kompatibilitaetsbedarf

Pruefbefehl:
`sysctl fs.protected_fifos`

Empfohlene Konfigurationsdatei:
`/etc/sysctl.d/99-zz-netmon-hardening.conf`

### net.ipv4.conf.all.log_martians

Parameter:
net.ipv4.conf.all.log_martians

Erwarteter Wert:
1

Nutzen:
Protokolliert verdaechtige oder ungueltige Pakete und verbessert die
Nachvollziehbarkeit von Netzwerkauffaelligkeiten.

Moegliche Nebenwirkungen:
Mehr Logeintraege bei stoerungsreichen oder stark exponierten Netzen.

Eignung fuer Desktop:
Geeignet

Eignung fuer Entwicklung:
Geeignet

Eignung fuer Server:
Geeignet

Moegliche Ausnahmen:
Systeme mit bewusst minimierter Protokollierung oder knappen Logbudgets

Pruefbefehl:
`sysctl net.ipv4.conf.all.log_martians`

Empfohlene Konfigurationsdatei:
`/etc/sysctl.d/99-zz-netmon-hardening.conf`

### net.ipv4.conf.default.log_martians

Parameter:
net.ipv4.conf.default.log_martians

Erwarteter Wert:
1

Nutzen:
Aktiviert dieselbe Martian-Logging-Strategie auch fuer neu erzeugte Interfaces.

Moegliche Nebenwirkungen:
Zusaetzliche Logmenge bei dynamischen Interface-Szenarien.

Eignung fuer Desktop:
Geeignet

Eignung fuer Entwicklung:
Geeignet

Eignung fuer Server:
Geeignet

Moegliche Ausnahmen:
Systeme mit bewusst abweichender Logging-Strategie

Pruefbefehl:
`sysctl net.ipv4.conf.default.log_martians`

Empfohlene Konfigurationsdatei:
`/etc/sysctl.d/99-zz-netmon-hardening.conf`

### net.ipv4.conf.default.accept_source_route

Parameter:
net.ipv4.conf.default.accept_source_route

Erwarteter Wert:
0

Nutzen:
Verhindert die Akzeptanz von Source-Routed-Paketen und reduziert alte, heute
meist unerwuenschte Routing-Angriffsvektoren.

Moegliche Nebenwirkungen:
Praktisch selten relevant; Spezialumgebungen mit historischen Netzfeatures
koennen betroffen sein.

Eignung fuer Desktop:
Geeignet

Eignung fuer Entwicklung:
Geeignet

Eignung fuer Server:
Geeignet

Moegliche Ausnahmen:
Sehr spezielle Labor- oder Legacy-Netze

Pruefbefehl:
`sysctl net.ipv4.conf.default.accept_source_route`

Empfohlene Konfigurationsdatei:
`/etc/sysctl.d/99-zz-netmon-hardening.conf`

### net.ipv4.conf.all.rp_filter

Parameter:
net.ipv4.conf.all.rp_filter

Erwarteter Wert:
2

Nutzen:
Aktiviert Reverse-Path-Filterung im loseren Modus und bietet Schutz gegen
offensichtliche Spoofing-Faelle bei gleichzeitig besserer Kompatibilitaet fuer
komplexere Routing-Szenarien.

Moegliche Nebenwirkungen:
Weniger restriktiv als Wert `1`, dafuer in VPN-, WireGuard- und
Multi-Interface-Umgebungen meist alltagstauglicher.

Eignung fuer Desktop:
Geeignet

Eignung fuer Entwicklung:
Geeignet

Eignung fuer Server:
Abhaengig von Routing-Topologie; haeufig ebenfalls geeignet

Moegliche Ausnahmen:
Einfaches Single-Interface-System mit bewusst gewuenschtem Strict-Mode `1`

Pruefbefehl:
`sysctl net.ipv4.conf.all.rp_filter`

Empfohlene Konfigurationsdatei:
`/etc/sysctl.d/99-zz-netmon-hardening.conf`

### net.ipv4.conf.default.rp_filter

Parameter:
net.ipv4.conf.default.rp_filter

Erwarteter Wert:
2

Nutzen:
Uebernimmt die profilgerechte RP-Filter-Grundeinstellung auch fuer neue
Interfaces.

Moegliche Nebenwirkungen:
Wie bei `net.ipv4.conf.all.rp_filter`: geringere Strenge als Wert `1`, dafuer
hoehere Praxistauglichkeit in komplexeren Netzaufbauten.

Eignung fuer Desktop:
Geeignet

Eignung fuer Entwicklung:
Geeignet

Eignung fuer Server:
Abhaengig von der Routing-Topologie

Moegliche Ausnahmen:
Single-Interface-Server mit bewusstem Strict-Mode

Pruefbefehl:
`sysctl net.ipv4.conf.default.rp_filter`

Empfohlene Konfigurationsdatei:
`/etc/sysctl.d/99-zz-netmon-hardening.conf`

## Bewusst nicht erzwungener Parameter

### kernel.modules_disabled

Parameter:
kernel.modules_disabled

Erwarteter Wert:
nicht als allgemeine Pflichtvorgabe gesetzt

Nutzen:
Wuerde das Nachladen von Kernelmodulen dauerhaft unterbinden.

Moegliche Nebenwirkungen:
Massive Funktionseinschraenkungen fuer Treiber, Hardwarewechsel, VPN,
Virtualisierung, Entwicklungswerkzeuge und Diagnosefaelle.

Eignung fuer Desktop:
Im Regelfall ungeeignet

Eignung fuer Entwicklung:
Hauefig ungeeignet

Eignung fuer Server:
Nur fuer stark spezialisierte, statische Umgebungen denkbar

Moegliche Ausnahmen:
Minimalistische, streng kontrollierte Appliances

Pruefbefehl:
`sysctl kernel.modules_disabled`

Empfohlene Konfigurationsdatei:
keine generelle Empfehlung fuer dieses Profil
