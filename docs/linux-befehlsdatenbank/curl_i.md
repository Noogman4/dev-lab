---
id: "curl_i"
name: "curl -I"
command: "curl -I"
category: "Aufgabenorientierte Hilfe"
language: "de"
root_required: false
risk_level: "caution"
tags: ["aufgabenorientierte hilfe", "curl_i"]
status: "Ausgearbeitet; Quellen und lokale Hilfe geprüft; HTTP-Test offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 51
reviewed_at: "2026-11-13"
locally_checked_version: "curl 8.5.0, Ubuntu-Paket mit Sicherheitskorrekturen; Hilfe geprüft"
---

# curl -I – HTTP-Header mit einer bewussten HEAD-Anfrage lesen

## 1. Kurzbeschreibung

`curl -I` fordert bei HTTP(S) normalerweise nur die Header einer Ressource mit der Methode HEAD an. Das eignet sich zur Prüfung von Status, Weiterleitung und bestimmten Serverangaben, ohne den normalen Antwortkörper abzurufen.

**Root-Rechte sind dafür nicht nötig.** Die Anfrage verbindet sich mit einem Server und kann dort protokolliert werden. „Nur Header“ bedeutet nicht offline und nicht ohne jede Außenwirkung. Hier wurde keine Testanfrage an einen fremden Dienst gesendet.

## 2. Was macht der Befehl?

Curl löst die Adresse auf, stellt eine Verbindung her und führt gegebenenfalls eine TLS-Verhandlung aus. Dann sendet es die Anfrage und zeigt empfangene Header. HEAD soll Metadaten entsprechend einer passenden GET-Anfrage liefern, der Server kann diese Methode aber ablehnen oder anders implementieren.

Ein `Content-Length`-Header kann die Länge eines möglichen GET-Inhalts beschreiben; er bedeutet nicht, dass diese Daten bei HEAD heruntergeladen wurden. Ein Statuscode wie 200 beweist außerdem weder die inhaltliche Qualität einer Webseite noch eine vertrauenswürdige Downloadquelle.

Grundlage ist die [offizielle curl-Manpage](https://curl.se/docs/manpage.html), abgeglichen mit lokaler HTTP-Hilfe und curl 8.5.0. Neuere Online-Optionen werden nicht ohne lokale Prüfung vorausgesetzt.

## 3. Syntax

```text
curl -I [OPTIONEN] URL
```

```bash
curl -q -I --proto '=https' --connect-timeout 5 --max-time 15 'https://example.com/'
```

Dies ist ein dokumentierter externer Anfrageaufruf und wurde hier nicht ausgeführt. `-q` steht zuerst und überspringt die normale curl-Konfigurationsdatei. Es entfernt nicht automatisch Proxy- oder andere Umgebungsbedingungen. Eine konkrete URL bewusst prüfen und vollständig zitieren.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-I`, `--head` | Bei HTTP(S) HEAD statt normalen Inhaltsabruf verwenden. | Nicht gleichbedeutend mit `-i`. |
| `-i` | Header zusätzlich zum normalen Antwortinhalt zeigen. | Kann weiterhin den Inhalt herunterladen. |
| `-L`, `--location` | Weiterleitungen folgen. | Kann weitere Server ansprechen. |
| `--max-redirs N` | Zahl gefolgter Redirects begrenzen. | Keine Prüfung, ob alle Ziele fachlich erwünscht sind. |
| `--proto '=https'` | Zugelassene Protokolle beschränken. | Prüft keine allgemeine Host-Allowlist oder öffentliche IP-Zugehörigkeit. |
| `--proto-redir '=https'` | Protokolle für Redirects beschränken. | Bei bewusst gewähltem `-L` zusätzlich verwenden. |
| `--connect-timeout SEK` | Verbindungsaufbau begrenzen. | Andere Grenze als die gesamte Laufzeit. |
| `--max-time SEK` | Gesamten Transfer zeitlich begrenzen. | Sinnvoll für begrenzte Diagnose. |
| `-sS` | Fortschritt ausblenden, Fehler weiterhin zeigen. | HTTP-Fehlerstatus und Prozessfehler getrennt beurteilen. |
| `--fail` | Viele HTTP-Fehler als curl-Fehler behandeln. | Nicht jede Authentifizierungsbesonderheit pauschal abdecken. |
| `-D DATEI` | Empfangene Header speichern. | Schreibt eine eigene Datei. |
| `-v` | Verbindungsdiagnose. | Kann sensible Anfrageangaben offenlegen. |
| `-k`, `--insecure` | TLS-Verifikation abschwächen. | Für normale Prüfung nicht verwenden. |

`-X HEAD` setzt vor allem einen Methodentext und ist kein gleichwertiger Ersatz für die vollständige Arbeitsweise von `-I`. Für die hier gewünschte Headeranfrage die passende Option verwenden.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Lokale Fähigkeiten prüfen

```bash
curl --version
curl --help http
```

Diese lokalen Abfragen wurden ausgeführt. Unterstützte Protokolle und tatsächlichen Build beachten.

### Schritt 2: Gewünschtes Ziel bewusst auswählen

Eine bekannte HTTPS-Adresse für einen eigenen Diagnosezweck wählen. Keine vertraulichen Tokens in eine öffentlich geteilte URL kopieren. Die Beispieladresse ist kein Auftrag, sie während der Dokumentation aufzurufen.

### Schritt 3: Begrenzte HEAD-Anfrage planen

```bash
curl -q -I --proto '=https' --connect-timeout 5 --max-time 15 'https://example.com/'
```

Der Aufruf würde eine Verbindung aufbauen. Ohne `-L` wird ein Redirect zunächst nur sichtbar gemacht. Das ist für eine erste Kontrolle übersichtlicher als automatisch die ganze Kette zu verfolgen.

### Schritt 4: Antwort einordnen

Statuszeile, `Location`, `Content-Type` und gegebenenfalls Größen-/Cacheangaben lesen. Mehrere Headerblöcke können etwa durch Zwischenantworten, Proxyverbindungen oder bewusst gefolgte Redirects entstehen. Nicht blind die erste Textzeile als endgültiges Zielergebnis verwenden.

### Schritt 5: HTTP- und Prozessstatus trennen

Curl kann ohne `--fail` einen technisch erfolgreichen Transfer melden, obwohl die Antwort HTTP 404 oder einen anderen Fehlerstatus trägt. Für einen automatisierten Ablauf ausdrücklich definieren, welche HTTP-Antworten akzeptiert werden und wie Prozessfehler behandelt werden.

## 6. Typische Anwendungsfälle

**Weiterleitung ansehen:** Ein `Location`-Ziel lesen, bevor es bewusst verfolgt wird. Ein Headerwert ist fremde Eingabe, kein automatisch auszuführender Befehl.

**Servermetadaten prüfen:** Content-Type, Cacheangaben oder angebotene Größe untersuchen. Nicht alle Server liefern bei HEAD identische Angaben zum späteren GET.

**Verbindungsfehler eingrenzen:** DNS, TLS, Verbindung und HTTP-Status als unterschiedliche Ebenen betrachten.

**Begrenzte Diagnose vorbereiten:** Kurze Zeitlimits und einen einzigen bekannten Endpunkt verwenden, statt viele unbekannte Ziele gleichzeitig abzufragen.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Anfrage ist Außenwirkung

IP-Adresse, Zeit, URL und Header können serverseitig protokolliert werden. Auch ein eigentlich nur lesendes HTTP-Verfahren kann auf einem fehlerhaft gestalteten Dienst unerwartete Aktionen auslösen. Ein unbekannter Link ist nicht allein wegen `-I` folgenlos.

### Weiterleitungen und Zielprüfung

`-L` erweitert den tatsächlichen Verbindungsumfang. Eine Protokollbeschränkung verhindert nicht automatisch unerwünschte lokale, private oder fremde Hosts. Für sicherheitskritische Anwendungen braucht es eine eigene saubere Zielvalidierung; dieses CLI-Beispiel bildet sie nicht ab.

### TLS und vertrauliche Daten

`-k` schwächt die Serverprüfung. Ein Zertifikatsfehler sollte Anlass zur Ursachenklärung sein. Header, Cookies, Zugangsdaten und verbose Berichte können Geheimnisse enthalten. Nicht ungeprüft veröffentlichen oder an fremde Hosts weiterreichen.

### Umleitungen und Grenzen

`-D` beziehungsweise Shell-Umleitungen schreiben Dateien und können vorhandene Ziele ersetzen. Zeitlimits begrenzen den Versuch, beweisen aber keine Serverqualität. HEAD-Ablehnung ist kein allgemeiner Nachweis, dass eine normale Webseite nicht erreichbar ist.

**Root-Rechte sind für die Anfrage nicht erforderlich.** Lokale Hilfeprüfung und tatsächlicher Netzwerkzugriff bleiben getrennte Handlungen.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| HTTP 405 | Dienst unterstützt HEAD nicht wie erwartet. | Methodengrenze berücksichtigen. |
| Curl-Status 0 trotz HTTP-Fehler | Standard bewertet erfolgreichen Transfer. | HTTP-Status ausdrücklich prüfen beziehungsweise geeignete Fail-Option verwenden. |
| Zertifikatsfehler | Zertifikat, Zeit, Vertrauenskette oder Proxyproblem. | Ursache prüfen statt `-k` ergänzen. |
| Redirect angezeigt | Ressource liegt an anderem Ort. | Ziel zuerst lesen und bewusst entscheiden. |
| Timeout | DNS, Verbindung oder Serverantwort zu langsam. | Betroffene Phase und Limits getrennt prüfen. |
| Headerliste unerwartet | Proxy, Zwischenantwort oder Redirectkette. | Antwortblöcke richtig zuordnen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Bekannte HTTPS-Adresse bewusst auswählen.
2. Mit `-I` und kurzen Zeitlimits beginnen.
3. Redirects zunächst ansehen, nicht automatisch verfolgen.
4. Zertifikatsprüfung eingeschaltet lassen.
5. HTTP-Status und curl-Abschlussstatus getrennt beurteilen.
6. Berichte auf Zugangsdaten und private Angaben prüfen.

**Prüfstand:** Curl-Version 8.5.0 und lokale HTTP-Hilfe wurden gelesen; die offizielle Referenz wurde geprüft. Es wurde keine HTTP-Anfrage für diesen Eintrag ausgeführt und kein Server oder Proxy getestet. HEAD-Verhalten, Redirects, TLS und reale Statusauswertung bleiben praktische Prüfpunkte.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `curl` | Allgemeiner Transferclient mit deutlich weiterem Funktionsumfang. |
| `wget` | Anderer Transferclient mit eigener Optionssemantik. |
| `openssl s_client` | Spezialisierte TLS-Diagnose, kein identischer HTTP-Test. |
| `getent` | Lokale Namensauflösung lesen; keine vollständige HTTPS-Prüfung. |

Ausgangseintrag: Datensatz 51 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
