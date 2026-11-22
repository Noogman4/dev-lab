---
id: "arp_scan"
name: "arp-scan"
command: "arp-scan"
category: "NetMon Spezial / Diagnoseideen"
language: "de"
root_required: true
risk_level: "caution"
tags: ["arp_scan", "netmon spezial / diagnoseideen"]
status: "Manpage geprüft; kein Paket gesendet und kein Netzscan ausgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 400
reviewed_at: "2026-11-13"
locally_checked_version: "arp-scan lokal nicht installiert"
---

# arp-scan – aktive ARP-Abfragen im ausdrücklich freigegebenen lokalen Netz planen

## 1. Kurzbeschreibung

`arp-scan` sendet ARP-Anfragen und zeigt Antworten aus dem lokalen Netz. Es ist ein aktiver Netzwerkzugriff, keine bloße Anzeige vorhandener Nachbartabellen. **Unter Linux sind passende Raw-Socket-Rechte nötig, beispielsweise `CAP_NET_RAW`; Root ist eine mögliche, aber nicht die einzige Berechtigungsform.**

## 2. Was macht der Befehl?

Die [arp-scan-Manpage bei Debian](https://manpages.debian.org/trixie/arp-scan/arp-scan.1.en.html) beschreibt Ziele, Schnittstelle und Antworten. ARP betrifft die lokale IPv4-Nachbarschaft und wird nicht wie normaler IP-Verkehr durch Router weitergeleitet.

Eine Antwort ist eine Beobachtung zum Abfragezeitpunkt. Herstellerzuordnungen beruhen auf Adressdatenbanken und bestätigen weder den tatsächlichen Gerätetyp noch eine vertrauenswürdige Identität.

## 3. Syntax

```text
arp-scan --help
arp-scan --interface=LABOR_SCHNITTSTELLE EINZELNES_FREIGEGEBENES_ZIEL
```

Die Platzhalter sind ein Plan, kein sofort ausführbarer Hostauftrag. Schnittstelle und Ziel müssen zum ausdrücklich freigegebenen eigenen Labor gehören. Hier wird kein tatsächliches Netz adressiert.

## 4. Wichtige Optionen

| Option | Zweck | Reichweite |
| --- | --- | --- |
| `--interface=NAME` | Ausgangsschnittstelle wählen. | Verhindert keine falsche fachliche Zielwahl. |
| `--localnet` | Ziele aus Schnittstellenkonfiguration bilden. | Kann deutlich breiter als ein Einzelziel sein. |
| `--file=DATEI` | Zielliste lesen. | Vollständigen Umfang vorher prüfen. |
| `--numeric` | Numerische Ziele verlangen. | Keine Garantie gegen aktive Netzlast. |
| `--retry=ANZAHL` | Anzahl Versuche pro Ziel. | Mehr Versuche erzeugen mehr Verkehr. |
| `--bandwidth=WERT` | Sendeumfang begrenzen. | Trotzdem aktive Anfragen. |
| `--help` | Bedienung anzeigen. | Kein Scan notwendig. |

Keine dauerhaften Capabilities oder SUID-Einstellungen allein für eine Dokumentationsübung setzen.

## 5. Beispiel erklärt Schritt für Schritt

Zuerst eine konkrete eigene Laborschnittstelle und genau ein freigegebenes Ziel festlegen. Ein automatisches `--localnet` würde einen anderen, breiteren Auftrag erzeugen.

Danach die geplante Anfrage in Worten beschreiben: Von welcher Schnittstelle an welches Ziel, in welchem Netz und mit welchem erwarteten Umfang? Erst ein tatsächlicher separater Diagnoseauftrag dürfte diesen Plan ausführen.

Hier wurde kein Aufruf gestartet, weil `arp-scan` lokal nicht installiert ist und die Datenbankerstellung keinen Netzscan erfordert. Es wurden keine MAC-Adressen, Geräte oder Antworten erhoben.

## 6. Typische Anwendungsfälle

- Einen ausdrücklich freigegebenen lokalen IPv4-Laborbestand aktiv untersuchen.
- Aktive Erreichbarkeitsbeobachtung von vorhandenen Nachbardaten unterscheiden.
- Eine Schnittstellen- oder Zielauswahl vor einem Scan nachvollziehbar planen.
- Grenzen einer einfachen Gerätezuordnung erklären.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der Aufruf erzeugt Netzverkehr und kann Überwachungs- oder Betriebsabläufe auslösen. Große Zielmengen und hohe Raten sind für eine kleine Diagnose unnötig. Keine automatische Ausweitung auf unbekannte Netze.

Keine Antwort beweist nicht sicher, dass ein Gerät fehlt: Segmentierung, Funkisolation, Zeitpunkt oder Paketverlust können eine Rolle spielen. Eine Antwort beweist umgekehrt keine gesicherte Geräteidentität.

## 8. Häufige Fehler

- **Passiver Blick erwartet:** Es werden Pakete gesendet.
- **Falsche Schnittstelle:** Anderes lokales Netz betroffen.
- **IPv6-Geräte erwartet:** ARP ist nicht IPv6-Nachbarerkennung.
- **Herstellername als Identitätsbeweis:** Datenbankzuordnung bleibt begrenzt.
- **Keine Antwort gleich ausgeschaltet:** Weitere Ursachen möglich.

## 9. Sichere Varianten oder Tipps für Einsteiger

Für eine reine vorhandene Nachbaransicht zunächst `ip neigh` betrachten. Das ersetzt keinen aktiven Test, benötigt aber keinen selbst gestarteten ARP-Scan.

Einen aktiven Auftrag klein und ausdrücklich begrenzen. Ergebnis, Zeitpunkt und tatsächliche Schnittstelle dokumentieren, ohne daraus eine vollständige Netzinventur zu behaupten.

## 10. Verwandte Befehle

- `ip neigh`: Vorhandene Nachbarinformationen.
- `ip address`: Eigene Schnittstellenadressen.
- `arping`: Einzelzielbezogene ARP-Funktionen mit eigener Wirkung.
- `nmap`: Andere aktive Untersuchungen; Umfang separat festlegen.

**Prüfstand:** Handbuch gelesen. Kein Paket gesendet, keine Raw-Socket-Freigabe eingerichtet und kein Netzscan ausgeführt. Datensatz 400 beendet den vereinbarten Arbeitsbereich.

Ausgangsdatensatz 400 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
