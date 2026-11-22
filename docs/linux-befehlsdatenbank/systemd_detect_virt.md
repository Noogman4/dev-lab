---
id: "systemd_detect_virt"
name: "systemd-detect-virt"
command: "systemd-detect-virt"
category: "Systemd & Dienste"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systemd & Dienste", "systemd-detect-virt"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 572
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; Umgebungsdetektion nicht getestet"
---

# systemd-detect-virt – Virtualisierungserkennung richtig interpretieren

## 1. Kurzbeschreibung

systemd-detect-virt versucht die eigene virtualisierte Laufumgebung zu erkennen.

## 2. Was macht der Befehl?

VM-Erkennung und Containererkennung sind verschiedene Fragen. Standardmäßig wird bei Verschachtelung üblicherweise die innerste erkannte Umgebung gemeldet. Eine Erkennung ist kein Nachweis der Sicherheitsisolation und keine vollständige Hardwareinventur. Das Programm ist vorhanden, die Umgebung wurde für diese Dokumentation nicht abgefragt.

Quelle, am 2026-11-13 gelesen: [Systemd: systemd-detect-virt-Handbuch](https://man7.org/linux/man-pages/man1/systemd-detect-virt.1.html); lokale Hilfe gelesen

## 3. Syntax

```text
systemd-detect-virt [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --container | Nur Containererkennung. |
| --vm | Nur vollständige Maschinenvirtualisierung. |
| --chroot | Chroot-Umgebung prüfen. |
| --private-users | User-Namespace prüfen. |
| --quiet | Keine Typausgabe; Status auswerten. |
| --list | Bekannte Erkennungstypen, nicht vorhandene Instanzen auflisten. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
systemd-detect-virt --container --quiet
```

Das Muster würde eine reale Umgebungsabfrage ohne Textausgabe ausführen. Status 0 würde eine Erkennung bedeuten; Nichtnull wäre kein positiver Sicherheitsbefund. Das Muster bleibt unausgeführt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Installationsbedingungen verstehen; Container und VM begrifflich trennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Heuristische Erkennung kann begrenzt sein. Aus einem Nichttreffer keine Bare-Metal- oder Vertrauenszusage ableiten. Keine Host- oder Gerätekennungen gesammelt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Keine Ausgabe | --quiet unterdrückt sie absichtlich. |
| Unterschiedliche Ergebnisse | Filter und Verschachtelung berücksichtigen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; Umgebungsdetektion nicht getestet. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| uname | Kernelinformationen. |
| machinectl | Registrierte Maschinen verwalten. |
| hostnamectl | Systembeschreibung, gesonderter Zugriff. |

Ausgangsdatensatz 572 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
