---
id: "edquota"
name: "edquota"
command: "edquota"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "edquota"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 217
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; edquota fehlt"
---

# edquota – Speicher- und Inodequoten bearbeiten

## 1. Kurzbeschreibung

`edquota` öffnet einen Editor für Benutzer-, Gruppen- oder Projektquoten. Das Speichern kann reale Kontingente ändern. Die Dokumentation setzt hierfür administrative Rechte voraus; es ist kein gewöhnlicher Textdateieditor für beliebige Dateien.

## 2. Was macht der Befehl?

Belegung und Grenzen sind getrennt: Aktuell verbrauchter Platz ist eine Information, keine frei korrigierbare Sollzahl. Softlimits dürfen für eine Karenzzeit überschritten werden; Hardlimits bilden die unmittelbare Grenze. Eine Grenze von 0 bedeutet hier keine auferlegte Quote, nicht null erlaubte Bytes. Platzwerte werden standardmäßig in KiB interpretiert; Inodewerte zählen Objekte.

Quelle, am 2026-11-13 gelesen: [edquota-Handbuch der quota-tools](https://manpages.debian.org/trixie/quota/edquota.8.en.html)

## 3. Syntax

```text
edquota [-u | -g | -P] [-f DATEISYSTEM] NAME ...
edquota [-u | -g | -P] -t
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-u`, `-g`, `-P` | Benutzer-, Gruppen- oder Projektquoten auswählen; Benutzer ist Vorgabe. |
| `-f DATEISYSTEM` | Wirkung auf ein Dateisystem begrenzen; sonst mehrere möglich. |
| `-p VORBILD` | Grenzen vom Vorbild übernehmen; kein bloßes Anzeigen. |
| `-t` | Allgemeine Karenzzeiten bearbeiten. |
| `-T NAME` | Individuellen Zeitpunkt der Softlimit-Durchsetzung bearbeiten. |
| `-r` | Auch entfernte Quoten per RPC bearbeiten; reale Netz-/Serverwirkung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Erfundene Lernwerte:
Platz: Belegung 600 KiB; soft 800 KiB; hard 1000 KiB
Inodes: Belegung 10; soft 20; hard 30
```

Ein weiteres kleines Objekt kann an der Inodegrenze scheitern, obwohl Platz frei ist. Nach Überschreiten von 800 KiB wäre die Karenz relevant, oberhalb der Hardgrenze soll keine weitere entsprechende Belegung erlaubt werden. Die Werte sind nur ein Schema, keine tatsächlich im Editor gelesenen Kontendaten. Der Editor wird nicht gestartet.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Kontingente planen:** Datenmenge und Anzahl kleiner Dateien getrennt begrenzen. **Vorlagen verwalten:** Gleichartige Grenzen bewusst auf ausgewählte Kennungen übertragen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Zu enge Grenzen können Schreibvorgänge von Anwendungen verhindern. EDITOR/VISUAL bestimmt ausführbaren Editorcode. Kein fremdes Konto, keine echte Quota-Datei und keine RPC-Verbindung werden hier verändert. Das Aufrufen mit einem Benutzernamen ist bereits ein Verwaltungsauftrag.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Speicher frei, trotzdem Schreiben abgelehnt | Quota oder Inodegrenze kann greifen; nicht nur df ansehen. |
| Zahl wird anders interpretiert | KiB gegen Inodeanzahl beziehungsweise numerische UID unterscheiden. |
| Keine Quoten verfügbar | Unterstützung/Aktivierung fehlt; nicht zur Übung aktivieren. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; edquota fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `quota` | Eigene Quotenauskunft. |
| `repquota` | Gesammelte Berichte. |
| `setquota` | Nichtinteraktive Änderung mit denselben administrativen Risiken. |

Ausgangsdatensatz 217 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
