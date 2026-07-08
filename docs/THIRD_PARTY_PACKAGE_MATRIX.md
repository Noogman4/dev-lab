# Third-Party Package Matrix

Diese Matrix trennt fuer NetMon zwischen:

- direkt im `.deb` enthalten
- nur als Paketabhaengigkeit / Systemtool erwartet
- rechtlich meist unkritisch
- vor Release nochmals pruefen

Grundlage dieser Einordnung:

- Paket-Skript: [scripts/build_netmon_deb.sh](/dev-lab/projects/dev-lab/scripts/build_netmon_deb.sh:1)
- aktuelle Hinweise: [THIRD_PARTY_NOTICES.md](/dev-lab/projects/dev-lab/THIRD_PARTY_NOTICES.md:1)

## 1. Direkt im `.deb` enthalten

Diese Inhalte werden vom Build-Skript aktiv in das Debian-Paket kopiert.

| Komponente | Im Paket | Typ | Einschätzung | Hinweis |
| --- | --- | --- | --- | --- |
| NetMon eigener Python-Code | Ja | Eigenes Werk | unkritisch | Eigene Projektlizenz maßgeblich |
| `netmon/lang/*.json` | Ja | Eigenes Werk | unkritisch | Teil des Projekts |
| `netmon/config/*.json` | Ja | Eigenes Werk / Konfig | unkritisch | Teil des Projekts |
| `linux-befehle.csv` | Ja | Projektdaten | prüfen bei Fremdinhalten | Wenn vollständig selbst erstellt: unkritisch |
| `tools/netmon.png` und weitere NetMon-Bilder | Ja | Assets | prüfen bei Fremdursprung | Wenn selbst erstellt: unkritisch |
| `tools/mdpresets/...` | Ja | Fremd-/Asset-Sammlung | prüfen | projectM-/Preset-Herkunft sauber dokumentieren |
| `tools/MD2 Presets Edited for projectM 4.x` | Ja | Fremd-/Asset-Sammlung | prüfen | Herkunft und Rechte prüfen |
| `tools/Log-Pics` | Ja | Bildsammlung | prüfen | Nur unkritisch, wenn eigene oder klar freigegebene Bilder |
| Doku-PDF / Doku-HTML aus `dist/docs` | Ja | Eigene Dokumentation | meist unkritisch | Fremdbilder oder Fremdtexte in der Doku separat prüfen |
| `Code-the-Classics.zip` | Ja | gebündelter Fremdinhalt | zulässig mit Beilage | BSD-2-Clause-Hinweis muss in den Begleitunterlagen mitgeliefert werden |

## 2. Nicht im `.deb` enthalten, aber als Abhängigkeit erwartet

Diese Programme oder Bibliotheken werden nach aktuellem Build-Skript nicht in
das Paket kopiert, sondern nur als Laufzeitumgebung vorausgesetzt oder empfohlen.

| Komponente | Im Paket | Einbindung | Einschätzung | Hinweis |
| --- | --- | --- | --- | --- |
| `python3-psutil` | Nein | `Depends` | meist unkritisch | Systempaket, nicht von NetMon relicensiert |
| `python3-pil`, `python3-pil.imagetk` | Nein | `Depends` | meist unkritisch | Systempaket |
| `python3-pypdf2` | Nein | `Suggests` | meist unkritisch | Systempaket |
| `python3-pygame` | Nein | `Suggests` | meist unkritisch | Systempaket |
| `python3-pgzero` | Nein | `Suggests` | meist unkritisch | Systempaket |
| `network-manager`, `dnsutils`, `wireguard-tools`, `ufw` | Nein | `Recommends` | meist unkritisch | Nur referenziert / aufgerufen |
| `traceroute`, `mtr`, `nmap`, `iftop`, `htop` | Nein | `Recommends` | meist unkritisch | Nur referenziert / aufgerufen |
| `lynis`, `rkhunter`, `clamav`, `clamav-freshclam` | Nein | `Recommends` | meist unkritisch | Nur referenziert / aufgerufen |
| `speedtest-cli` | Nein | `Recommends` | meist unkritisch | Nur referenziert / aufgerufen |
| `mpv` | Nein | `Recommends` | meist unkritisch | Nur referenziert / aufgerufen |
| `cryptsetup`, `udisks2` | Nein | `Depends` | meist unkritisch | Fuer installierten LUKS-/Mount-Pfad erforderlich |
| `whois` | Nein | `Recommends` | meist unkritisch | Nur referenziert / aufgerufen |
| `wireshark`, `tshark`, `projectm`, `projectm-pulseaudio` | Nein | `Suggests` | meist unkritisch | Nur optional referenziert |

## 3. Rechtlich meist unkritisch

Diese Fälle sind normalerweise gut vertretbar, sofern die Paketstruktur so
bleibt wie aktuell:

- Systemprogramme werden nur aufgerufen, aber nicht selbst in das `.deb` gepackt.
- Python-Bibliotheken kommen als Distribution-/APT-Abhängigkeit vom System.
- Eigene Projektdateien, eigene Texte und eigene UI-Dateien werden mitgeliefert.
- `LICENSE` und `THIRD_PARTY_NOTICES.md` sind im Projekt vorhanden und im Release sauber referenziert.

## 4. Vor Release nochmals prüfen

Diese Punkte sollten nicht nur mit Bauchgefühl freigegeben werden:

- `Code-the-Classics.zip`
  Grund: bei Änderungen am gebündelten Archiv sollte die Upstream-Lizenzlage erneut mit dem echten Inhaltsstand abgeglichen werden.

- `tools/mdpresets/...`
  Grund: Preset-Sammlungen und bearbeitete Presets können eigene Urheber- und Lizenzlagen haben.

- `tools/MD2 Presets Edited for projectM 4.x`
  Grund: bearbeitete Fremd-Presets brauchen nachvollziehbare Herkunft und Freigabe.

- `tools/Log-Pics`
  Grund: Bildrechte immer einzeln prüfen, wenn nicht sicher selbst erstellt.

- alle Logos, Banner oder Splash-Bilder
  Grund: nur dann unkritisch, wenn eindeutig Eigenmaterial oder klar freigegeben.

- Doku-Artefakte
  Grund: eingebettete Screenshots, Logos, Fremdzitate oder Assets können eigene Rechte auslösen.

## 5. Praktische Schlussfolgerung

Wenn die Drittprogramme nur optionale Nachinstallationen oder normale
Systemabhaengigkeiten bleiben, ist das nach heutigem Stand in der Regel
vertretbar.

Nicht automatisch abgedeckt sind aber gebündelte Fremdarchive und fremde
Asset-Sammlungen, die physisch im `.deb` landen. Dort braucht ihr saubere
Begleitunterlagen und nachvollziehbare Herkunft.

## 6. Empfehlung

Vor einem finalen oeffentlichen Release:

1. Den BSD-2-Clause-Hinweis fuer `Code-the-Classics.zip` im Paket und in den Begleitunterlagen mitliefern.
2. Preset- und Bildsammlungen auf Herkunft und Freigabe pruefen.
3. `LICENSE`, `THIRD_PARTY_NOTICES.md`, `CODE_THE_CLASSICS_LICENSE.txt` und `site/legal.html` gegen den echten Paketinhalt final abgleichen.
