# Lab Workflow

## Ziel

Dieses Dokument beschreibt den empfohlenen Workflow fuer das externe NetMon-Testlabor auf `sdc1`.

Ausgangspunkt:

- Entwicklung und Git bleiben auf dem internen Zorin-System.
- Das externe Laufwerk unter `/media/happy/Work2/netmon-lab` dient fuer Distros, Testdaten, Logs, Screenshots, Exporte und Vergleichsstaende.

## Grundprinzip

- Ein fuehrendes NetMon-Repository auf Zorin.
- Keine zweite primaere Repo-Kopie auf dem externen Datentraeger.
- Testlaeufe liefern Artefakte nach `netmon-lab`.
- Auswertung, Fixes und Commits passieren wieder im Haupt-Repo.

## Empfohlene Verzeichnisstruktur

```text
/media/happy/Work2/netmon-lab/
  isos/
  vms/
  images/
  distros/
    zorin/
      notes/
    ubuntu/
      notes/
    debian/
      notes/
    fedora/
      notes/
    mint/
      notes/
    arch/
      notes/
  runs/
  artifacts/
  screenshots/
  shared/
    netmon-testdata/
  notes/
```

## Teststrategie

### 1. Entwicklung auf Zorin

- Code in `/dev-lab/projects/dev-lab` aendern.
- Lokal `ruff`, `black --check`, `pytest` und passende Smoke-Checks ausfuehren.
- Vor einem Testlauf committen oder mindestens den Git-Stand notieren.

### 2. Testumgebung auf externem Labor

- VMs oder native Distros auf der externen Platte bereitstellen.
- Pro Distro Notizen und Besonderheiten unter `distros/<name>/notes/` pflegen.
- Testdaten, Supportpakete und Screenshots nicht ins Repo, sondern ins Labor schreiben.

### 3. Testlauf pro Szenario

Fuer jeden Lauf einen separaten Run-Ordner erzeugen, z. B.:

```text
runs/2026-07-08-zorin-smoke/
  env/
  logs/
  screenshots/
  exports/
  captures/
  artifacts/
  notes.md
  run.env
```

Empfohlene Szenarien:

- `smoke`
- `gui`
- `headless`
- `packaging`
- `security`
- `vpn`
- `radio`
- `repo-guard`

### 4. Rueckfluss ins Haupt-Repo

- Fehler und Beobachtungen im Run-Ordner sammeln.
- Fixes ausschliesslich im Haupt-Repo umsetzen.
- Danach erneut testen und die Ergebnisse vergleichen.

## Run-Skript

Das Repository bringt ein kleines Hilfsskript mit:

```bash
scripts/lab/init_test_run.sh --distro zorin --scenario smoke
```

Beispiel mit Notiz:

```bash
scripts/lab/init_test_run.sh \
  --distro fedora \
  --scenario gui \
  --note "Fedora 42 GNOME, erster GUI-Smoke fuer NetMon 1.1.17"
```

Nur Pfade aufloesen, ohne etwas anzulegen:

```bash
scripts/lab/init_test_run.sh --distro ubuntu --scenario packaging --print-only
```

## Was pro Testlauf gesammelt werden sollte

- Distro, Version, Kernel
- Desktop oder Window Manager
- Python-Version
- Paketlage optionaler NetMon-Abhaengigkeiten
- Ergebnis von `python -m netmon --headless`
- Ergebnis von GUI-Smokes
- exportierte Diagnose- oder Supportpakete
- Screenshots
- relevante Logs
- manuelle Beobachtungen und Workarounds

## Minimaler NetMon-Testablauf

1. Git-Stand notieren.
2. Run-Ordner anlegen.
3. Headless-Start pruefen.
4. GUI-Start pruefen.
5. Kernbereiche testen:
   - DNS
   - Firewall
   - Security
   - Radio
   - Export-/Diagnosepfade
6. Artefakte in den Run-Ordner schreiben.
7. Ergebnisse im Haupt-Repo auswerten und Fixes committen.

## Hinweise

- Native Distro-Installationen auf der externen Platte sind fuer harte Integrationsfaelle sinnvoll.
- Fuer den Alltag sind VMs meist schneller, reproduzierbarer und risikoaermer.
- Fremde Preset-/Asset-Sammlungen sollten getrennt von regulaeren NetMon-Testartefakten behandelt werden.
