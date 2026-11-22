---
id: "hostname"
name: "hostname"
command: "hostname"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "caution"
tags: ["hostname", "grundlagen & hilfe"]
status: "Keine Namensänderung oder Auflösungsabfrage ausgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 358
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale hostname-Manpage gelesen"
---

# hostname – Rechnernamen abfragen und Änderungsformen erkennen

## 1. Kurzbeschreibung

`hostname` zeigt ohne Zielargument den aktuellen Rechnernamen. Andere Formen können Auflösungsinformationen abfragen oder den Namen ändern. **Für die Anzeige sind keine Root-Rechte nötig; Namensänderungen verlangen zusätzliche Rechte.**

## 2. Was macht der Befehl?

Die lokale Manpage unterscheidet den gesetzten Hostnamen von einem über Namensauflösung bestimmten vollständigen Namen. Ein FQDN hängt auch von der Resolverkonfiguration ab und ist nicht einfach immer ein angehängtes festes Suffix.

Ein Rechner kann mehrere Schnittstellen und Adressen haben. Deshalb ist die Ausgabe keine eindeutige allgemeine Antwort auf „Welche öffentliche IP habe ich?“.

## 3. Syntax

```bash
hostname
hostname --help
hostname --short
```

Ein zusätzliches gewöhnliches Namensargument kann dagegen eine Setzaktion bedeuten. Für reine Diagnose keinen neuen Namen anhängen.

## 4. Wichtige Optionen

| Option | Aufgabe | Grenze |
| --- | --- | --- |
| `--short` | Kurze Namensdarstellung. | Keine vollständige DNS-Prüfung. |
| `--fqdn` | Vollständigen aufgelösten Namen abfragen. | Hängt von der Namensauflösung ab. |
| `--all-ip-addresses` | Adressen der Maschine anzeigen. | Nicht automatisch öffentliche Außenadresse. |
| `--file DATEI` | Namen aus Datei setzen. | Verändernd, kein Dateibetrachter. |
| `--help` | Bedienung anzeigen. | Kein Aufruf zum Umbenennen. |

Optionen und Kurzformen sind implementierungsabhängig. Die lokale Variante ist maßgeblich.

## 5. Beispiel erklärt Schritt für Schritt

Geplanter lesender Einstieg:

```bash
hostname
```

Er würde den aktuellen Namen anzeigen. Dieser tatsächliche Rechnername wurde für das Dokument nicht erhoben. Ein fiktiver Wert wie `arbeitsplatz` beschreibt nur einen möglichen Ausgabetyp.

Soll ein Fehler bei vollständigen Namen untersucht werden, wäre eine gesonderte Resolverbetrachtung nötig. Ein anderer FQDN ist nicht automatisch ein unerlaubter Rechnerwechsel.

Eine direkte Namensänderung wirkt nach der beschriebenen klassischen Oberfläche zunächst auf die Laufzeit. Dauerhafte Verwaltung kann distributionsabhängig anders eingerichtet sein und wird hier nicht verändert.

## 6. Typische Anwendungsfälle

- Die eigene Maschine in einem Terminal zuordnen.
- Kurzen Namen und Namensauflösung auseinanderhalten.
- Einen Bericht um eine gezielt freigegebene Identitätsangabe ergänzen.
- Namensprobleme vor einer begründeten Verwaltungsänderung eingrenzen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein Rechnername kann eine Person oder interne Struktur verraten. Vor Weitergabe prüfen, ob er benötigt wird.

Setzformen können Anwendungen, Netzverwaltung und Protokollzuordnung beeinflussen. Eine Dateioption ist hier kein sicherer Weg zum bloßen Lesen einer Datei. Auflösungsformen können zusätzliche Namensdienstaktivität auslösen.

## 8. Häufige Fehler

- **Zusätzliches Wort als Beschreibung anhängen:** Könnte eine Setzaktion sein.
- **FQDN gleich fest gespeicherter Hostname:** Resolverkontext fehlt.
- **Lokale Adresse gleich öffentliche IP:** Andere Ebenen.
- **Laufzeit gleich dauerhafte Vorgabe:** Verwaltung und Neustartverhalten klären.

## 9. Sichere Varianten oder Tipps für Einsteiger

Für den Namen nur den einfachen lesenden Aufruf verwenden. Eine Umbenennung als eigenen Auftrag mit passenden distributionsbezogenen Werkzeugen planen.

Nicht als erste Reaktion DNS- oder Hostdateien ändern, wenn eine Namensabfrage unerwartet ausfällt. Zunächst konkrete Quelle und Fehlermeldung klären.

## 10. Verwandte Befehle

- `hostnamectl`: Hostnamensverwaltung und Status.
- `uname -n`: Systemknotenname.
- `ip address`: Schnittstellenadressen.
- `getent hosts`: Namensdienstabfrage.

**Prüfstand:** Lokale Manpage gelesen. Kein tatsächlicher Hostname veröffentlicht und keine System- oder DNS-Einstellung verändert.

Ausgangsdatensatz 358 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
