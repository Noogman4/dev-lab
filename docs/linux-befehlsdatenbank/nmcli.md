---
id: "nmcli"
name: "nmcli"
command: "nmcli"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "nmcli"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 437
reviewed_at: "2026-11-13"
locally_checked_version: "nmcli 1.46.0"
---

# nmcli – Ein Profil ausschließlich als Text erzeugen

## 1. Kurzbeschreibung

nmcli steuert NetworkManager und zeigt dessen Zustand. Im ausdrücklich gewählten Offline-Modus lassen sich Profiltexte ohne Daemonzugriff erzeugen. Ohne diesen Modus ist connection add eine echte Profiländerung.

## 2. Was macht der Befehl?

Profil, aktives Profil und Gerät sind unterschiedliche Objekte. Namen können mehrdeutig sein; UUIDs identifizieren Profile genauer. Die Übung erzeugt nur ein eigenes Ethernet-Keyfile als Text. Sie importiert oder aktiviert es nicht. Der Offline-Modus ist laut lokaler Manpage für add/modify vorgesehen, kein allgemeiner Schutzschalter für beliebige Unterbefehle.

Quelle, am 2026-11-13 gelesen: [NetworkManager: nmcli-Handbuch](https://networkmanager.dev/docs/api/latest/nmcli.html) und lokale nmcli-Manpage

## 3. Syntax

```text
nmcli [OPTIONEN] OBJEKT KOMMANDO [ARGUMENTE]
nmcli --offline connection add type TYP con-name NAME ifname LINK
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--offline` | add/modify verarbeiten Profiltext ohne Daemon. |
| `connection show` | Gespeicherte und gegebenenfalls aktive Profildaten. |
| `device status` | Gerätezustand aus Managersicht. |
| `connection up/down` | Verbindung aktivieren/deaktivieren. |
| `-f`, `-g`, `-t` | Felder beziehungsweise Werte und kompakte Ausgabe wählen. |
| `--show-secrets` | Kann Passwörter offenlegen; hier nicht verwendet. |
| `--wait 0` | Nicht auf Abschluss warten; Erfolg beweist keine abgeschlossene Aktivierung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigenen Ordner anlegen

Voraussetzungen: Bash, NetworkManager/nmcli mit dokumentiertem Offline-Modus und rg. Alle Schritte gehören in dieselbe Shell. Der Interface-Name ist erfunden.

### Schritt 2: Text erzeugen und Felder lesen

```bash
uebung="$(mktemp -d -t netmon-nmcli-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
nmcli --version
nmcli --offline connection add type ethernet con-name Lernprofil ifname eth-lernen > profil.nmconnection
rg '^(id=Lernprofil|interface-name=eth-lernen|type=ethernet)$' profil.nmconnection
```

### Schritt 3: Ergebnis bewerten

Die Datei enthält id=Lernprofil, type=ethernet und interface-name=eth-lernen. Eine erzeugte UUID kann zwischen Läufen wechseln. Die Datei bleibt im Testordner. Es wurde kein Profil dem Dienst hinzugefügt und keine Schnittstelle aktiviert. Das ist ein Format-/Erzeugungstest, kein Verbindungstest.

## 6. Typische Anwendungsfälle

**Profilsyntax lernen:** Eigenschaften an eigenem Text verstehen. **Automatisierung vorbereiten:** Explizite Objekte, Felder und eindeutige Identifikatoren verwenden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Weglassen von --offline würde aus derselben add-Form einen echten Verwaltungsauftrag machen. Änderungen an DNS, Routing, Funk und Verbindungen können Sitzungen trennen. Profildateien können Geheimnisse enthalten; diese Übung enthält keine. Das Textprofil darf nicht ungeprüft importiert werden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Unbekanntes --offline | Version oder Paketvariante unterstützt den Modus nicht; stoppen. |
| Profilname mehrdeutig | Bei echten Abfragen UUID verwenden. |
| Erfolg bei --wait 0 | Nur angenommene Anfrage, keine bestätigte Fertigstellung. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Das Offline-Schlüsselwort immer direkt im geprüften Aufruf belassen. Dateiinhalt und Status kontrollieren; keine Folgeaktivierung aus dem erfolgreichen Textexport ableiten.

**Prüfstand am 2026-11-13:** nmcli 1.46.0. Praktisch geprüft: Offline-Erzeugung eines eigenen Profiltexts und drei Felder praktisch geprüft. Nicht geprüft: Daemon, Import, Aktivierung, Geräte, DHCP, DNS, Rechte- und Geheimnisfälle. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `nmtui` | Interaktive Manageroberfläche. |
| `nm-connection-editor` | Grafische Profilbearbeitung. |
| `ip` | Kernelobjekte statt Profilverwaltung. |

Ausgangsdatensatz 437 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
