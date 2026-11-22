---
id: "mount"
name: "mount"
command: "mount"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "caution"
tags: ["Datentraeger & Dateisysteme", "mount"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 234
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine lokale Programmversion ermittelt"
---

# mount – Dateisysteme in den Verzeichnisbaum einhängen

## 1. Kurzbeschreibung

`mount` verbindet ein Dateisystem oder eine andere Dateisicht mit einem Pfad. Das verändert den Mountzustand. Üblicherweise sind administrative Rechte nötig; ausdrücklich erlaubte Benutzermounts, FUSE oder Namespaces haben eigene Regeln.

## 2. Was macht der Befehl?

Der bisherige Inhalt des Zielverzeichnisses wird während des Mounts verdeckt, nicht automatisch gelöscht. Ein bloßer Verzeichnisname kann einen fstab-Auftrag auswählen. `--bind` zeigt vorhandene Inhalte an einem weiteren Ort; es erstellt keine unabhängige Kopie. Quelle, Ziel, Dateisystemtyp und Optionen sind getrennte Angaben.

Quelle, am 2026-11-13 gelesen: [mount-Projekthandbuch](https://manpages.debian.org/trixie/mount/mount.8.en.html)

## 3. Syntax

```text
mount [-t TYP] [-o OPTIONEN] QUELLE ZIEL
mount --bind ALTPFAD NEUPFAD
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-t TYP` | Dateisystemtreiber wählen; falsche Wahl repariert keine Signatur. |
| `-o ro` | Lesende Mountsicht anfordern; je Dateisystem kann etwa Journalwiedergabe dennoch schreiben. |
| `-o noexec,nodev,nosuid` | Bestimmte Nutzungsmöglichkeiten begrenzen; keine vollständige Sandbox. |
| `--bind`, `--rbind` | Vorhandenen Baum zusätzlich sichtbar machen, rekursiv auch Untermounts. |
| `-o remount,...` | Optionen bestehender Mounts verändern; eigener Zustandswechsel. |
| `-a` | Viele konfigurierte Mounts ausführen; kein isoliertes Beispiel. |
| `--fake` | Versionsabhängiger Planungsmodus; nicht als universelle Nebenwirkungsfreiheit voraussetzen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Planungsmuster:
Quelle: DATEISYSTEM
Ziel: LEERER_ZIELORDNER
Angeforderte Sicht: ro
```

Vor echtem Mounten wären alle drei Angaben zu prüfen. Der Quelltyp kann ein Gerät, Netzwerkdienst oder virtuelles Dateisystem sein. Das Ziel ist der Einhängepfad. `ro` bedeutet weder vollständige Datenrettungsisolation noch Schutz gegen Änderungen über andere Pfade. Hier wird kein Zielordner gemountet.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Datenzugriff planen:** Einen zusätzlichen Datenträger in die Hierarchie einordnen. **Bind-Sichten verstehen:** Mehrere Zugriffspfade zu denselben Inhalten von Kopien unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Echte Mounts können Geräteschreibzugriffe, Netzwerkverkehr, Helperprogramme und systemweite Sichtänderungen verursachen. Fremde Dateisysteme können präparierte Inhalte enthalten. Kein sudo-Mount, keine fstab-Änderung und kein Fake-Mounttest ausgeführt. Ein Label oder UUID kann auf geklonten Medien doppelt vorkommen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Dateien im Ziel verschwunden | Vorhandener Inhalt wird vom Mount verdeckt; nicht blind löschen. |
| Permission denied | Berechtigung oder erlaubte Benutzerregel fehlt; keine pauschale Eskalation. |
| Falscher filesystem type | Quelle, Typ, Features und Version getrennt prüfen. |
| Bind-Sicht verändert Original | Beide Wege zeigen dieselben Daten; kein Backup. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `umount` | Löst Einhängungen. |
| `findmnt` | Zeigt Mountbeziehungen. |
| `mountpoint` | Prüft einen Einhängepunkt. |

Ausgangsdatensatz 234 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
