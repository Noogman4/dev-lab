---
id: "ss_tulpen"
name: "ss -tulpen"
command: "ss -tulpen"
category: "Aufgabenorientierte Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["aufgabenorientierte hilfe", "ss_tulpen"]
status: "Ausgearbeitet; Quellen und lokale Hilfe geprüft; Socketabfrage offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 59
reviewed_at: "2026-11-13"
locally_checked_version: "ss aus iproute2 6.1.0; Hilfe und Version geprüft"
---

# ss -tulpen – Lokale TCP-/UDP-Bindungen und Prozesszuordnung lesen

## 1. Kurzbeschreibung

`ss -tulpen` zeigt ausgewählte lokale TCP- und UDP-Sockets mit numerischen Adressen, erweiterten Angaben und soweit erlaubt einer Prozesszuordnung. Die Buchstaben sind kombinierte Optionen des Programms `ss`.

**Für eine normale Socketübersicht sind keine Root-Rechte nötig.** Prozessdetails anderer Konten können fehlen. Der dokumentierte Aufruf öffnet keinen Testdienst und beendet keine Verbindung.

## 2. Was macht der Befehl?

Ss liest Socketinformationen aus dem aktuellen Systemkontext. TCP-Listener und UDP-Bindungen sind fachlich unterschiedlich: UDP benötigt keinen TCP-Verbindungsaufbau und kann in der Anzeige etwa als `UNCONN` erscheinen.

Die Ausgabe beschreibt lokale Bindungen im sichtbaren Netzwerk-Namespace. Sie ist kein externer Portscan. Ob ein Dienst von einem anderen Rechner erreichbar ist, hängt zusätzlich unter anderem von Routing, Firewall und Geräteumgebung ab.

Grundlage: [Distributions-Manpage zu ss](https://manpages.debian.org/trixie/iproute2/ss.8.en.html) und lokale Hilfe sowie Version von iproute2 6.1.0. Es wurde keine reale Socketliste dieses Rechners für die Dokumentation abgefragt.

## 3. Syntax

```text
ss -tulpen [FILTER]
```

Die Kombination lässt sich verständlicher zerlegen:

```bash
ss --tcp --udp --listening --processes --extended --numeric
```

Die Kurzform und die lange Form sollen dieselbe Auswahl ausdrücken. Kein Ergebnis ist nicht automatisch ein Fehler; im betrachteten Kontext können keine passenden Sockets sichtbar sein.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-t`, `--tcp` | TCP auswählen. | Nicht mit vollständiger UDP-Ansicht verwechseln. |
| `-u`, `--udp` | UDP auswählen. | Connectionless-Bindungen anders interpretieren. |
| `-l`, `--listening` | Auf lauschende beziehungsweise entsprechend gebundene Auswahl begrenzen. | Keine Übersicht aller aktiven Verbindungen. |
| `-p`, `--processes` | Prozesszuordnung anzeigen. | Kann wegen Berechtigungen unvollständig sein. |
| `-e`, `--extended` | Zusatzangaben wie UID und Inode. | Technische Identifikatoren, keine Vertrauensbewertung. |
| `-n`, `--numeric` | Numerische Port-/Adressdarstellung. | Verhindert Verwechslung durch Servicenamen. |
| `-4`, `-6` | Adressfamilie begrenzen. | Andere Familie wird nicht mitgeprüft. |
| `-a`, `--all` | Auch nicht lauschende Auswahl einbeziehen. | Anderer Berichtsumfang als der ursprüngliche Listenerauftrag. |
| `-H`, `--no-header` | Kopfzeile ausblenden. | Macht Text nicht automatisch zu einer stabilen strukturierten Schnittstelle. |
| `-O`, `--oneline` | Einzeilige Darstellung je Socket. | Sonderzeichen und Versionsunterschiede weiter beachten. |
| `-r`, `--resolve` | Namen auflösen. | Kann Namensauflösung auslösen; für rein numerische Ansicht nicht nötig. |
| `-K`, `--kill` | Bestimmte Sockets zwangsweise schließen. | Ausdrücklich andere, verändernde Aufgabe; hier nicht verwenden. |

Filter können die Auswahl auf einen lokalen Port begrenzen. Ein Portwert allein ist kein sicherer Prozess- oder Dienstidentifikator.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Lokale Funktionen prüfen

```bash
ss --version
ss --help
```

Diese beiden Aufrufe wurden ausgeführt. Die folgenden Listenaufrufe bleiben dokumentierte praktische Schritte.

### Schritt 2: Übersicht lesen

```bash
ss -tulpen
```

Protokoll, Zustand, lokale Adresse und Prozessangaben getrennt betrachten. Ein leerer Prozessbereich kann an fehlendem Zugriff liegen und bedeutet nicht, dass kein Prozess verantwortlich ist.

### Schritt 3: TCP allein eingrenzen

```bash
ss -ltnp
```

Die vereinfachte Ansicht konzentriert sich auf TCP-Listener. IPv4 und IPv6 können unterschiedliche Einträge liefern. Ein lokaler Wildcard-Listener beweist noch keine externe Erreichbarkeit.

### Schritt 4: Einen Beispielport auswählen

```bash
ss -ltn 'sport = :8080'
```

Die Zahl 8080 ist hier nur ein Beispiel. Der Filter wird zitiert, damit die Shell den Ausdruck nicht zerlegt. Keine Zeile ist ein plausibles Ergebnis, wenn an diesem Port kein passender Listener sichtbar ist.

### Schritt 5: Bindungsadresse einordnen

`127.0.0.1` ist Loopback im betreffenden Namespace. `0.0.0.0` bezeichnet eine IPv4-Wildcard-Bindung. Eine IPv6-Wildcard ist nicht ohne Prüfung der Socketkonfiguration gleichbedeutend mit garantierter IPv4-Mitbedienung. Fernzugriff müsste separat und ausdrücklich geprüft werden.

## 6. Typische Anwendungsfälle

**Portkonflikt eingrenzen:** Lokale Bindung und soweit erlaubt zugehörigen Prozess lesen, bevor ein Dienst umkonfiguriert wird.

**Falsche Bindungsadresse erkennen:** Loopback, konkrete Adresse und Wildcard unterscheiden, wenn ein eigener Dienst anders erreichbar ist als erwartet.

**Anwendungsstart kontrollieren:** Prüfen, ob ein erwarteter Listener im richtigen Namespace erscheint. Das bestätigt nicht dessen Anwendungsprotokoll oder sichere Konfiguration.

**Protokolltrennung:** TCP-Listener und UDP-Bindungen getrennt analysieren, statt alle Statuswerte gleich zu behandeln.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Lokale Liste ist kein externer Sicherheitsnachweis

Ein gebundener Port kann durch eine Firewall blockiert sein. Umgekehrt kann ein Dienst über andere Adressen, Namespaces oder Weiterleitungen erreichbar sein. Keine pauschale Aussage „von außen offen“ oder „sicher geschlossen“ allein aus dieser Liste ableiten.

### Rechte und sichtbarer Kontext

Prozessangaben hängen von Berechtigungen und der Prozess-/Namespace-Sicht ab. Höhere Rechte nicht reflexartig einsetzen. Bei einer gezielten späteren Diagnose den benötigten Umfang begründen.

### Fremde und vertrauliche Daten

Prozessnamen, Adressen und Ports können interne Struktur zeigen. Berichte vor dem Teilen prüfen. Prozessbezeichnungen allein beweisen weder legitime noch verdächtige Aktivität.

### Andere Optionen können eingreifen

`-K` beendet passende Sockets; das ist keine reine Filterverbesserung. Vor Änderungen zuerst den tatsächlichen Prozess, Zweck und betroffenen Dienst bestimmen. Die Dokumentation führt keine solche Aktion aus.

**Root-Rechte sind für die normale eingeschränkte Ansicht nicht erforderlich.** Vollständige fremde Prozesszuordnung und reale Erreichbarkeitsprüfung bleiben separate Fragen.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Kein Prozessname | Berechtigung oder Sichtbereich eingeschränkt. | Einschränkung nennen, nicht „kein Prozess“ behaupten. |
| Kein erwarteter Listener | Andere Adresse, Familie, Namespace oder nicht gestartet. | Kontext gezielt prüfen. |
| UDP zeigt UNCONN | Für die Bindung plausibler connectionless-Zustand. | Nicht als TCP-Verbindungsfehler behandeln. |
| Wildcard, aber fern nicht erreichbar | Firewall, Routing oder Dienstkontext. | Nächste Ebene getrennt untersuchen. |
| Servicename statt Zahl | Numerische Darstellung fehlt. | `-n` bewusst verwenden. |
| Kernelzugriff verweigert | Ausführungsumgebung eingeschränkt. | Praktische Sicht als unvollständig markieren. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Mit numerischen lesenden Listen beginnen.
2. Protokoll und Adressfamilie bewusst wählen.
3. Fehlende Prozessinformationen als Grenze benennen.
4. Listener und externe Erreichbarkeit unterscheiden.
5. Keine Kill-Option zur Diagnose ergänzen.
6. Berichte nicht allein nach Prozessnamen bewerten.

**Prüfstand:** Ss-Version iproute2 6.1.0 und lokale Hilfe wurden gelesen; das offizielle Distributionshandbuch wurde geprüft. Keine echten Sockets wurden aufgelistet, geöffnet, geschlossen oder verändert. Prozesssicht, Portfilter und reale Dienstbindungen bleiben praktische Prüfpunkte.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ip addr`, `ip route` | Adress- und Routingkontext. |
| `lsof` | Dateideskriptor-/Prozessansicht mit anderer Zugriffsgrenze. |
| `systemctl status` | Zustand eines konkret benannten Diensts. |
| `nft` | Firewallregeln; Änderungen wären ein eigener Auftrag. |

Ausgangseintrag: Datensatz 59 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
