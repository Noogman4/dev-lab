---
id: "venv"
name: "venv"
command: "python3 -m venv"
category: "Python & Daten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Python & Daten", "venv"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 525
reviewed_at: "2026-11-13"
locally_checked_version: "Python 3.12.3"
---

# venv – Virtuelle Python-Umgebung anlegen

## 1. Kurzbeschreibung

venv ist ein Modul der Python-Standardbibliothek; der übliche Aufruf lautet python3 -m venv.

## 2. Was macht der Befehl?

Die Umgebung trennt Python-Pakete vom Basisinterpreter. Sie ist keine Betriebssystem-Sandbox: ausgeführter Code behält Benutzerrechte und Netzwerkzugriff. Aktivierung ändert vor allem die Shell-Suchpfade und ist für den direkten Aufruf des Umgebungsinterpreters nicht erforderlich. Umgebungen werden am Ziel neu erzeugt, nicht als portable Installation kopiert.

Quelle, am 2026-11-13 gelesen: [Python: venv-Handbuch](https://docs.python.org/3/library/venv.html); lokale Hilfe Python 3.12 gelesen

## 3. Syntax

```text
python3 -m venv [OPTIONEN] ZIELVERZEICHNIS
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --without-pip | Keine pip-Bootstrapinstallation. |
| --system-site-packages | Pakete der Basisumgebung sichtbar machen; Isolation reduzieren. |
| --copies | Interpreterdateien kopieren statt üblicher Links. |
| --clear | Vorhandenen Zielinhalt löschen; hier nicht verwenden. |
| --upgrade-deps | Abhängigkeiten aktualisieren; kann Netzwerkzugriff auslösen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Neuen privaten Ort wählen

Die Übung läuft in einer eigenen Shell; Python 3 mit venv muss vorhanden sein.

### Schritt 2: Ohne Paketinstallation erzeugen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
python3 -m venv --without-pip env
env/bin/python -c 'import sys; assert sys.prefix != sys.base_prefix; print("Eigene venv aktiv im Interpreter")'
```

### Schritt 3: Ergebnis lesen

Der Interpreter erkennt einen anderen Umgebungspfad als seinen Basispfad. Es wurde weder die Benutzershell aktiviert noch ein Paket installiert. Die eigene Umgebung bleibt zur Prüfung erhalten.

## 6. Typische Anwendungsfälle

Projektabhängigkeiten in einer eigenen Umgebung verwalten; Interpreterzuordnung prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Vorhandene Umgebungen nicht mit --clear bearbeiten. Fremder Python-Code bleibt ausführbarer Benutzer-Code. Keine systemweiten Pakete und keine globalen Suchpfade ändern.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| venv: command not found | Modul über python3 -m venv aufrufen. |
| ensurepip fehlt | Distributionspaketierung prüfen; der hier getestete Modus benötigt kein pip. |
| Falsches pip | Interpreter und Paketwerkzeug derselben Umgebung zuordnen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Direkt env/bin/python verwenden, wenn keine Aktivierung nötig ist. Neue Umgebungen nicht in Git aufnehmen und keine Projektdateien in ihre internen Verzeichnisse legen.

**Prüfstand am 2026-11-13:** Python 3.12.3. Praktisch geprüft: Neue eigene Umgebung ohne pip geprüft; Aktivierung, Paketinstallation und andere Python-Versionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| virtualenv | Separates Umgebungswerkzeug. |
| python3 | Basisinterpreter. |
| pip | Pakete für einen bestimmten Interpreter. |

Ausgangsdatensatz 525 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
