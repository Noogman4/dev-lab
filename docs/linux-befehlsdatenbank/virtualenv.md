---
id: "virtualenv"
name: "virtualenv"
command: "virtualenv"
category: "Python & Daten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Python & Daten", "virtualenv"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 526
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; virtualenv-Erzeugung offen"
---

# virtualenv – Python-Umgebungen mit virtualenv erzeugen

## 1. Kurzbeschreibung

virtualenv ist ein zusätzliches Werkzeug zur Erzeugung virtueller Python-Umgebungen.

## 2. Was macht der Befehl?

Es ist vom Standardbibliotheksmodul venv zu unterscheiden. Interpreterauswahl, Seeder und Downloadverhalten hängen von Version und Konfiguration ab. Eine virtuelle Umgebung isoliert Pakete, nicht Benutzerrechte oder Netzwerk. virtualenv fehlt lokal; es wurde nicht installiert.

Quelle, am 2026-11-13 gelesen: [virtualenv: offizielle CLI-Referenz](https://virtualenv.pypa.io/en/stable/reference/cli.html)

## 3. Syntax

```text
virtualenv [OPTIONEN] NEUES_ZIEL
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -p INTERPRETER | Gewünschten Python-Interpreter auswählen. |
| --no-seed | Keine Seedpakete installieren. |
| --no-download | Keinen Download aktueller Seedpakete aus PyPI erlauben. |
| --app-data PFAD | Werkzeugeigene Daten und Cachepfade auswählen. |
| --system-site-packages | Basispakete sichtbar machen; keine volle Pakettrennung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
virtualenv --no-seed --no-download --app-data EIGENER_CACHE NEUES_EIGENES_ZIEL
```

Dies ist ein nicht ausgeführtes Erzeugungsmuster für eine neue eigene Umgebung. Vor einem echten Lauf müssten die lokale Version und mögliche Konfigurationsvorgaben geprüft werden. --no-download allein ist keine allgemeine Netzwerksandbox.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Eine bewusst ausgewählte Python-Umgebung vorbereiten; alternative Interpreter unterstützen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Zielverzeichnis und Cache werden beschrieben. Bestehende Umgebungen und Benutzerkonfiguration nicht überschreiben. Keine Python-Umgebung macht fremden Code vertrauenswürdig.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Command not found | Separates Werkzeug fehlt; nicht mit venv-Verfügbarkeit verwechseln. |
| Interpreter nicht gefunden | Expliziten Interpreterpfad und Version prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; virtualenv-Erzeugung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| venv | Standardbibliotheksalternative. |
| python3 | Interpreter. |
| pip | Paketinstallation in ausgewählter Umgebung. |

Ausgangsdatensatz 526 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
