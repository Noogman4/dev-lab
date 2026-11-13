---
id: "apt_install"
name: "apt install"
command: "apt install"
category: "Aufgabenorientierte Hilfe"
language: "de"
root_required: true
risk_level: "caution"
tags: ["aufgabenorientierte hilfe", "apt_install"]
status: "Ausgearbeitet; Quellen und Hilfe geprüft; Installation nicht ausgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 46
reviewed_at: "2026-11-13"
locally_checked_version: "APT 2.8.4; lokale Hilfe und Version geprüft"
---

# apt install – Ein Paket mit geprüfter Änderungsvorschau installieren

## 1. Kurzbeschreibung

`apt install` installiert oder aktualisiert Pakete auf Debian-, Ubuntu- und verwandten Systemen. Der Datenbankname bezeichnet den Unterbefehl `install` des Programms `apt`, kein separates Programm namens „apt install“.

**Die normale systemweite Installation benötigt Root-Rechte.** Reine Informationsabfragen und eine geeignete Simulation benötigen sie gewöhnlich nicht. Eine Installation ist ausdrücklich keine nur lesende Aktion; die entsprechende pauschale Ausgangseinstufung wäre falsch.

## 2. Was macht der Befehl?

APT bestimmt aus den bekannten Paketquellen und Versionen einen Installationsplan einschließlich Abhängigkeiten. Es lädt benötigte Pakete und lässt sie über die Paketverwaltung entpacken und konfigurieren. Dabei können zusätzliche Pakete installiert, vorhandene aktualisiert und bei Konflikten weitere Änderungen vorgeschlagen werden.

Paketskripte können mit Systemrechten laufen und Dienste verändern. Ein scheinbar kleines Paket kann deshalb mehr bewirken als nur eine Datei in einen Programmordner zu kopieren. Paketname, Herkunft und vollständigen Plan vor der Bestätigung prüfen.

Grundlagen: [APT-Benutzerhandbuch](https://manpages.debian.org/trixie/apt/apt.8.en.html), [APT-Get-Referenz zu gemeinsamen Optionen](https://manpages.debian.org/trixie/apt/apt-get.8.en.html) und [APT-Vertrauensmodell](https://manpages.debian.org/trixie/apt/apt-secure.8.en.html). Lokal wurden nur Hilfe und Version von APT 2.8.4 gelesen.

## 3. Syntax

```text
sudo apt install PAKET [WEITERE_PAKETE ...]
apt -s install PAKET
```

`PAKET` ist ein genauer Paketname aus einer bewusst ausgewählten Quelle. Eine Versionsauswahl kann als `PAKET=VERSION` erfolgen, sofern verfügbar. Ein lokales DEB wird mit einem Pfad wie `./paket.deb` angegeben; das ist ein eigener Herkunfts- und Vertrauensfall.

## 4. Wichtige Optionen

| Option oder Zusatz | Wirkung | Konkreter Hinweis |
| --- | --- | --- |
| `-s`, `--simulate` | Geplante Schritte simulieren. | Kein vollständiger Lauf von Paket- oder Dienstskripten. |
| `--no-install-recommends` | Empfohlene Pakete nicht automatisch ergänzen. | Kann erwartete Zusatzfunktionen weglassen. |
| `--reinstall` | Vorhandenes Paket erneut installieren. | Keine Garantie für Reparatur privater oder veränderter Konfiguration. |
| `--download-only` | Pakete laden, ohne sie normal zu installieren. | Netzwerk- und Cache-Schreiboperation, kein reines Lesen. |
| `-y`, `--assume-yes` | Rückfragen weitgehend automatisch bejahen. | Für ersten manuellen Auftrag vermeiden. |
| `--no-remove` | Bei einer geplanten Entfernung abbrechen. | Zusätzliche Grenze, keine vollständige Risikoprüfung. |
| `PAKET=VERSION` | Bestimmte Version verlangen. | Verfügbarkeit, Abhängigkeiten und mögliche Rückstufung prüfen. |
| `-t RELEASE` | Zielrelease beeinflussen. | Kann die Auswahl weiterer Abhängigkeiten verändern. |

Keine Optionen zur Umgehung fehlender Authentifizierung oder unsicherer Quellen als normale Problemlösung verwenden. Eine Installation aus einem unbekannten lokalen DEB ist nicht allein wegen APT automatisch vertrauenswürdig.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Paketname und Details lesen

```bash
apt show htop
```

Das ist eine dokumentierte Abfrage eines Beispielpakets. Beschreibung, Version und Abhängigkeiten prüfen. Der Auftrag führt diese Abfrage nicht automatisch gegen den echten Paketbestand aus.

### Schritt 2: Plan simulieren

```bash
apt -s install htop
```

Die Simulation zeigt den geplanten Paketumfang anhand des aktuellen lokalen Index. Sie führt nicht alle echten Installationswirkungen aus und garantiert nicht, dass ein späterer Stand denselben Plan ergibt.

### Schritt 3: Herkunft und Änderungsumfang beurteilen

Vor einer Installation die konfigurierten Quellen, neue Abhängigkeiten, Aktualisierungen und etwaige Entfernungen prüfen. Eine Warnung nicht durch pauschales Abschalten von Signaturprüfungen umgehen.

### Schritt 4: Installation nur als eigener bewusster Systemauftrag

```bash
sudo apt install htop
```

Dieser Schritt würde das System verändern. Erst nach Prüfung und ausdrücklichem Installationswunsch durchführen. Die Zusammenfassung vor der Bestätigung erneut lesen; kein automatisches `-y` ergänzen.

### Schritt 5: Paketstand anschließend prüfen

```bash
dpkg-query -W htop
```

Ein vorhandener Paketstatus und eine tatsächlich funktionierende Anwendung sind unterschiedliche Prüfziele. Ein passender Starttest wäre ein weiterer eigener Schritt.

## 6. Typische Anwendungsfälle

**Ein benötigtes Programm ergänzen:** Paket aus der zur Distribution passenden vertrauenswürdigen Quelle wählen und vollständigen Plan lesen.

**Einzelnes Paket aktualisieren:** Ein Installationsauftrag kann eine vorhandene Version ersetzen. Auswirkungen auf Abhängigkeiten und Dienste beachten.

**Installation vorbereiten:** Informationsabfragen und Simulation erlauben eine erste Planung, ohne den echten Installationslauf mit Paketskripten durchzuführen.

**Eigenes lokales DEB installieren:** Quelle und Integrität unabhängig prüfen. Das `./` kennzeichnet einen Pfad; es ersetzt keine Authentizitätsprüfung des Pakets.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Systemänderungen und Skripte

Pakete können Programme, Bibliotheken, Konfiguration und Dienste verändern. Ihr Installationscode kann privilegiert laufen. Ein erfolgreiches Entpacken beweist keine für alle Arbeitsabläufe störungsfreie Integration.

### Abhängigkeiten und Quelle

Der Plan kann zusätzliche Änderungen enthalten. Quellen aus unterschiedlichen Releases oder unbekannte Fremdarchive können unerwünschte Versionen auswählen. Die APT-Authentifizierung schützt den vorgesehenen Archivweg und bedeutet keine allgemeine Harmlosigkeitsprüfung sämtlicher Software.

### Simulation ist begrenzt

Eine Simulation verändert den Paketbestand nicht, führt aber insbesondere nicht die echte Konfiguration jedes Pakets aus. Fehlende Rechte beim Lesen bestimmter Konfiguration oder ein später geänderter Index können den Plan beeinflussen. Vor dem echten Lauf erneut prüfen.

### Unterbrechung und Parallelbetrieb

Stromausfall, voller Datenträger oder ein Abbruch können eine unvollständige Konfiguration hinterlassen. Nicht parallel mehrere Paketmanager starten und keine Sperrdateien blind löschen.

**Root-Rechte sind für die systemweite Installation erforderlich, für passende Lese- und Simulationsschritte gewöhnlich nicht.** Diese Beschreibung ist keine Freigabe, Pakete auf dem Rechner zu installieren.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Paket nicht gefunden | Name falsch oder lokale Listen kennen es nicht. | Name und passende Quellen prüfen. |
| Abhängigkeiten nicht erfüllbar | Versions-, Release- oder Konfliktproblem. | Vollständigen Plan klären, nicht blind erzwingen. |
| Sperre belegt | Anderer Paketprozess arbeitet. | Legitimen Prozess abwarten beziehungsweise dessen Zustand prüfen. |
| Authentifizierungsfehler | Quelle, Schlüssel oder Archivinformationen passen nicht. | Ursache beheben statt Prüfung abschalten. |
| Kein Platz | Cache oder Dateisystem voll. | Platzbedarf und sichere Bereinigung separat planen. |
| Konfiguration unterbrochen | Frühere Installation nicht abgeschlossen. | Paketstatus und konkrete Meldung lesen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Erst Paketdetails und Herkunft prüfen.
2. Vor einem neuen Auftrag simulieren.
3. Den vollständigen Plan vor Bestätigung erneut lesen.
4. Kein pauschales `-y` oder Authentifizierungs-Bypass verwenden.
5. Nicht parallel mit mehreren Paketmanagern arbeiten.
6. Paketstatus und tatsächliche Funktion anschließend getrennt prüfen.

**Prüfstand:** APT-Version 2.8.4 und lokale Hilfe wurden gelesen; offizielle Handbücher wurden geprüft. Keine Paketlisten wurden geladen, keine Simulation gestartet, keine Pakete installiert und keine Dienste verändert. Sämtliche paketbezogenen Beispielschritte bleiben praktische Prüfpunkte.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `apt search`, `apt show` | Paketinformationen vor der Installation. |
| `apt update` | Lokale Paketlisten verändern und aktualisieren. |
| `apt-get` | Spezialisierte APT-Oberfläche, besonders für kontrollierte Skripte. |
| `apt-cache policy` | Versions- und Herkunftsauswahl betrachten. |
| `dpkg-query` | Installierten Paketstatus lesen. |

Ausgangseintrag: Datensatz 46 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
