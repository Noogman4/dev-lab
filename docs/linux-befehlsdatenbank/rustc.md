---
id: "rustc"
name: "rustc"
command: "rustc"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "rustc"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 299
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; Programm fehlt"
---

# rustc – Rust-Quelltext mit festgelegter Edition übersetzen

## 1. Kurzbeschreibung

rustc ist der Rust-Compiler. Er übersetzt eine Crate und kann Programme, Bibliotheken oder Zwischenformate erzeugen. Cargo ist die darüberliegende Projekt-/Abhängigkeitsverwaltung und nicht mit rustc gleichzusetzen.

## 2. Was macht der Befehl?

Der normale Aufruf einer einfachen Binärcrate baut ein Programm; ein separater Aufruf startet es. Eine Edition legt Sprachregeln fest und ist weder Toolchainversion noch Zielplattform. Der direkte rustc-Default darf nicht aus dem Default eines neuen Cargo-Projekts abgeleitet werden. --emit begrenzt oder erweitert Artefakte. --emit=metadata ist kein allgemeiner Schutz gegen Compilezeitcode wie prozedurale Makros.

Quelle, am 2026-11-13 gelesen: [Rust-Projekt: rustc-Aufrufargumente](https://doc.rust-lang.org/rustc/command-line-arguments.html)

## 3. Syntax

```text
rustc [OPTIONEN] QUELLE.rs
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--edition=2021` | Sprachregeln ausdrücklich festlegen; passende Mindesttoolchain erforderlich. |
| `-o DATEI`, `--out-dir ORDNER` | Ausgabe wählen; -o hat Vorrang. |
| `--crate-type=bin/rlib/cdylib` | Artefaktart wählen; nicht beliebig austauschbar. |
| `-g`, `-C opt-level=0` | Debugdaten und Optimierungsstufe wählen. |
| `-O` | Entspricht opt-level=3, nicht einfach einem Lesemodus. |
| `--emit=metadata/obj/asm` | Metadaten, Objekt oder Assemblertext erzeugen. |
| `--extern NAME=PFAD` | Externe Crate ausdrücklich anbinden. |
| `--target TRIPEL` | Ziel wählen; installiert nicht dessen Bibliotheken/Linker. |
| `--explain E...`, `--version --verbose` | Diagnose erläutern beziehungsweise Compiler-/Hoststand lesen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

**Nicht praktisch ausgeführt; erklärendes Muster.** Die benötigte Umgebung fehlt oder die praktische Ausführung ist gesondert offen.

```bash
uebung="$(mktemp -d -t lernen-299-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
rustc --version --verbose
cat > lernen.rs <<'RUST'
fn main() {
    println!("Hallo Rust {}", 6 * 7);
}
RUST
rustc --edition=2021 -g -C opt-level=0 lernen.rs -o lernen
./lernen

```

### Schritt 3: Ergebnis auswerten

Eine geeignete installierte Toolchain würde ein eigenes Programm erzeugen und Hallo Rust 42 ausgeben. Externe Crates, Cargo-Buildskripte und prozedurale Fremdmakros sind nicht enthalten. rustc fehlt lokal, deshalb sind Übersetzung und Laufzeit praktisch offen; es wurde keine Toolchain nachinstalliert. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Einzeldateien verstehen: Compiler und Projektmanager unterscheiden. Plattformbau planen: Edition, Compilerstand und Target gesondert festhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Rust verhindert viele Speicherfehler in sicherem Code, macht Programme aber nicht frei von Datei-, Netzwerk- oder Logikrisiken. Prozedurale Makros und native Abhängigkeiten können bereits beim Kompilieren Code ausführen. Ein Targetwechsel erzeugt keine funktionierende Laufzeitumgebung. Keine Rustup-/Cargo-Installation oder Netzabfrage ist Teil des Beispiels. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Edition nicht unterstützt | Compilerstand prüfen; Edition ist kein automatischer Downloadauftrag. |
| Cannot find crate | Passende --extern-/Suchpfade und Targetartefakte prüfen. |
| Linker fehlt | Targettoolchain vollständig planen. |
| Borrow-checker-Fehler | Diagnose und --explain lesen; nicht blind unsafe einsetzen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `cargo` | Projekt-/Abhängigkeitsverwaltung mit Buildskripten. |
| `rustup` | Toolchainverwaltung mit Installationswirkungen. |
| `ld` | Mögliche Linkerstufe. |
| `readelf` | Erzeugtes ELF statisch untersuchen. |

Ausgangsdatensatz 299 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
