---
id: "apparmor_status"
name: "apparmor_status"
command: "apparmor_status"
category: "Firewall & Sicherheit"
language: "de"
root_required: true
risk_level: "safe"
tags: ["apparmor_status", "firewall & sicherheit"]
status: "Lokale Programmzuordnung und Handbuch geprüft; keine erneute Systeminventur"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 306
reviewed_at: "2026-11-13"
locally_checked_version: "AppArmor 4.0.1really4.0.1-0ubuntu0.24.04.9; Alias und Hilfe geprüft"
---

# apparmor_status – den alternativen AppArmor-Statusnamen verstehen

## 1. Kurzbeschreibung

`apparmor_status` zeigt den Zustand von AppArmor an. Auf dem hier geprüften System verweist der Name auf dieselbe Datei wie `aa-status`. Es handelt sich dort um einen alternativen Aufrufnamen, nicht um einen zweiten unabhängigen Prüfer.

**Für die Hilfe sind keine Root-Rechte nötig.** Eine vollständige Statusansicht benötigt Zugriff auf geschützte AppArmor-Informationen; dafür können administrative Rechte erforderlich sein. Die Abfrage selbst lädt, entfernt oder verändert keine Profile.

## 2. Was macht der Befehl?

AppArmor beschränkt Programme mithilfe von Profilen. Ein Statusbericht kann geladene Profile, deren Modi und zugehörige Prozesse sichtbar machen. Ein Profil im Enforce-Modus setzt seine Regeln durch; Complain dient überwiegend der Beobachtung von Regelverletzungen. Explizite Verbote können auch dort weiter wirken.

Drei Fragen sind auseinanderzuhalten: Existiert eine Profildatei? Ist diese Definition im Kernel geladen? Läuft das betreffende Programm tatsächlich unter dem Profil? Eine einzelne Gesamtzahl beantwortet diese Fragen nicht vollständig.

Die [Debian-Manpage zu apparmor_status](https://manpages.debian.org/trixie/apparmor/apparmor_status.8.en.html) beschreibt den Statusaufruf. Zusätzlich wurden die lokal installierten Handbücher und Hilfetexte betrachtet. Die Dateizuordnung wurde mit `os.path.samefile` geprüft: Beide Namen bezeichnen hier dieselbe ausführbare Datei. Andere Distributionen können abweichende Paketaufteilungen haben.

## 3. Syntax

```text
apparmor_status [OPTION]
apparmor_status --help
apparmor_status --json
```

Ohne Option wird eine Statusausgabe angefordert. `--help` ist deshalb die passende erste Aktion, wenn nur die Bedienung gesucht wird. `--json` führt eine echte Abfrage durch und ist keine Beispieldatei.

Der Unterstrich im Namen gehört zum Programm. `apparmor-status` mit Bindestrich ist nicht automatisch derselbe verfügbare Aufruf.

## 4. Wichtige Optionen

| Option | Zweck | Beim Lesen beachten |
| --- | --- | --- |
| `--help` | Lokale Bedienung anzeigen. | Unterstützung der eigenen Version feststellen. |
| `--enabled` | Aktivierung über Rückgabestatus prüfen. | Fehlerursachen nicht pauschal als deaktiviert auslegen. |
| `--verbose` | Ausführliche Darstellung wählen. | Ein Bericht ist eine zeitliche Momentaufnahme. |
| `--json` | Strukturierte Statusdaten liefern. | Daten und Rückgabestatus getrennt prüfen. |
| `--pretty-json` | JSON mit lesbarer Einrückung ausgeben. | Derselbe Informationsbereich wie bei JSON. |
| `--show=profiles` | Profilansicht auswählen. | Neuere Option; lokale Hilfe entscheidet. |
| `--show=processes` | Prozessansicht auswählen. | Rechte und Prozesssicht können begrenzt sein. |

Zähl- und Filteroptionen haben sich weiterentwickelt. Beispiele aus unterschiedlichen AppArmor-Versionen deshalb nicht blind kombinieren. Eine Versionsoption wird hier nicht vorausgesetzt; die lokale Paketversion wurde über Paketmetadaten ermittelt.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Bedienung statt Schutzstatus abrufen

```bash
apparmor_status --help
```

Dieser Hilfsaufruf wurde lokal erfolgreich ausgeführt. Es wurden für diesen Eintrag keine tatsächlichen Profile, Prozessnamen oder Schutzmodi erneut ausgelesen.

### Schritt 2: Die Namensgleichheit richtig einordnen

Auf diesem System führt der Aufruf über `aa-status` zur gleichen Implementierung. Lieferten beide später denselben Bericht, wären das zwei Aufrufe derselben Informationsquelle. Das ist keine unabhängige Bestätigung durch ein anderes Sicherheitsprodukt.

### Schritt 3: Ein fiktives Ergebnis bewerten

Angenommen, eine geplante Abfrage meldet zwölf Profile und drei eingeschränkte Prozesse. Daraus folgt weder, dass die übrigen neun Profile kaputt sind, noch, dass alle anderen Anwendungen geschützt wären. Profile können geladen sein, obwohl gerade kein passender Prozess läuft.

Für die Frage nach einem bestimmten Programm wären dessen Prozessbindung, Profilmodus und Regeln relevant. Dieses Beispiel nennt bewusst keine tatsächlichen Programme des Rechners.

## 6. Typische Anwendungsfälle

### Unterschiedliche Anleitungen zusammenführen

Eine ältere Anleitung verwendet `apparmor_status`, eine andere `aa-status`. Zunächst die lokale Zuordnung klären, bevor vermeintlich widersprüchliche Ergebnisse als zwei verschiedene Schutzsysteme behandelt werden.

### Statusdaten für eine autorisierte Fehleranalyse sammeln

Ein lesender Bericht kann helfen, einen erwarteten Profilmodus einzuordnen. Zeitpunkt, Version und Rechte mitnotieren. In Containern oder eingeschränkten Umgebungen kann die Ansicht unvollständig sein.

### Skripte auf den vorhandenen Namen abstimmen

Ein Programmname kann fehlen, obwohl AppArmor vorhanden ist. Das ist zuerst eine Frage der Installation und Benennung, nicht automatisch eine Sicherheitsstörung.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Abfrage ändert keine Policy. Ihre Ausgabe kann jedoch Prozessnamen und Sicherheitsstruktur offenlegen. Solche Daten vor einer Weitergabe auf persönliche oder interne Angaben prüfen.

Ein Lesefehler beweist keine Deaktivierung. Fehlende Kontrollschnittstellen, unzureichende Rechte und ein tatsächlich nicht aktives Schutzsystem sind verschiedene Situationen. Den konkreten Rückgabestatus nach dem passenden lokalen Handbuch deuten.

Zwei identische Ausgaben unter Aliasnamen erhöhen nicht die Unabhängigkeit einer Prüfung. Ebenso ist ein erfolgreich geladener Profilsatz kein Nachweis, dass seine Regeln fachlich ausreichend sind.

## 8. Häufige Fehler

- **„Befehl nicht gefunden“:** Verfügbarkeit von `aa-status` und installiertem Paket prüfen; nicht vorschnell AppArmor umkonfigurieren.
- **JSON unbrauchbar:** Standardfehler nicht mit dem Datenstrom vermischen. Vor Verarbeitung Gültigkeit und Erfolg kontrollieren.
- **„Permission denied“:** Zugriffsgrenze feststellen. Nicht deshalb Profile abschalten.
- **Andere Profilzahl als erwartet:** Zeitpunkt, Namespace und Auswahloptionen vergleichen.
- **Option unbekannt:** Die lokale Hilfe ist für den installierten Aufruf maßgeblich.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit der Hilfe beginnen. Nur wenn ein tatsächlicher Statusbericht gebraucht wird, den passenden lesenden Aufruf wählen. Ein vorbereitender Hilfsaufruf benötigt keine automatische Rechteerhöhung.

Den Bericht zuerst beschreiben: Was wurde beobachtet, zu welchem Zeitpunkt, unter welchen Rechten? Erst danach eine begründete Schlussfolgerung ziehen. Bei Unsicherheit bleibt die Profilwirkung ein Prüfpunkt; der Name des Werkzeugs allein löst ihn nicht.

## 10. Verwandte Befehle

- `aa-status`: Auf diesem System derselbe Statusprüfer unter anderem Namen.
- `aa-complain`: Ändert den Profilmodus; keine reine Statusfunktion.
- `aa-enforce`: Schaltet ein Profil in durchsetzenden Modus.
- `apparmor_parser`: Lädt und verarbeitet Profildefinitionen.
- `journalctl`: Kann passende Meldungen anzeigen; Zugriff und Auswahl sind separat zu betrachten.

**Prüfstand:** Alternative Namen und Hilfe lokal geprüft. Vorhandene AppArmor-Policies und Dienste blieben unverändert. Laufende Prozesse wurden für diesen Eintrag nicht inventarisiert.

Ausgangsdatensatz 306 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
