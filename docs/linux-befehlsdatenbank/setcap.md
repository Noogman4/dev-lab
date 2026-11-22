---
id: "setcap"
name: "setcap"
command: "setcap"
category: "Benutzer & Rechte"
language: "de"
root_required: true
risk_level: "danger"
tags: ["benutzer", "rechte", "capabilities", "sicherheit"]
status: "Ausgearbeitet; Quellen geprüft; Beispiel im Benutzer-Namensraum geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 117
reviewed_at: "2026-11-13"
locally_checked_version: "libcap2-bin 1:2.66-5ubuntu2.4"
---

# setcap – Datei-Capabilities setzen oder entfernen

## 1. Kurzbeschreibung

`setcap` versieht eine Programmdatei mit **Datei-Capabilities**. Das sind einzelne Teilrechte von Root, etwa `cap_net_bind_service` (Ports unter 1024 öffnen) oder `cap_net_raw` (Raw-Sockets). Startet jemand das Programm, erhält es diese Teilrechte – ohne setuid-Bit und ohne volle Root-Rechte.

**Für wirksame Capabilities im System sind Root-Rechte nötig** (genauer: die Capability `CAP_SETFCAP`). Als normaler Benutzer meldet `setcap` `unable to set CAP_SETFCAP effective capability: Operation not permitted`.

## 2. Was macht der Befehl?

`setcap` schreibt das erweiterte Attribut `security.capability` einer **regulären Datei**. Symbolische Links werden abgelehnt. Die Capability-Angabe folgt der Textform aus [cap_from_text(3)](https://manpages.debian.org/trixie/libcap-dev/cap_from_text.3.en.html):

```text
NAME[,NAME...]OPERATOR FLAGS
```

- `NAME`: zum Beispiel `cap_net_bind_service`.
- `OPERATOR`: `=` (genau setzen), `+` (hinzufügen), `-` (entfernen).
- `FLAGS`: `p` (permitted), `e` (effective), `i` (inheritable).

Für normale Programme ist `+ep` üblich: erlaubt und sofort aktiv. Was jede Capability gestattet, beschreibt [capabilities(7)](https://manpages.debian.org/trixie/manpages/capabilities.7.en.html).

Die Optionen folgen der [Debian-Manpage zu setcap](https://manpages.debian.org/trixie/libcap2-bin/setcap.8.en.html) und der lokalen Kurzhilfe von libcap 2.66.

### Wann Capabilities verschwinden

- Beim **Kopieren** ohne Erhalt erweiterter Attribute: Im Test hatte eine mit `cp` erstellte Kopie keine Capabilities mehr.
- Bei einem **Besitzerwechsel** mit `chown` (siehe [chown(2)](https://manpages.debian.org/trixie/manpages-dev/chown.2.en.html)).
- Bei **Paketaktualisierungen**, die die Datei ersetzen; Pakete setzen ihre Capabilities dann selbst neu.

## 3. Syntax

```text
setcap [-q] [-v] [-n ROOTID] CAPABILITIES DATEI [CAPABILITIES2 DATEI2 ...]
setcap -r DATEI
```

```bash
sudo setcap cap_net_bind_service+ep /usr/local/bin/meinserver
getcap /usr/local/bin/meinserver
sudo setcap -r /usr/local/bin/meinserver
```

Das bisherige NetMon-Beispiel `setcap --help` funktioniert nicht als Hilfe: libcap 2.66 meldet `fatal error: Invalid argument` und zeigt danach die Kurzhilfe. Vorgesehen ist `setcap -h`. Der Platzhalter `setcap [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-r` | Capabilities der Datei entfernen. | Anders als ein leerer Satz `=`; siehe Abschnitt 7. |
| `-v` | Nur prüfen, ob die Datei genau diese Capabilities hat. | Ändert nichts; Rückgabe `0` bei Übereinstimmung, sonst `1`. |
| `-q` | Weniger Ausgaben. | – |
| `-n ROOTID` | Capability nur für einen Benutzer-Namensraum mit dieser Root-ID schreiben. | Für Container-Abbilder. |
| `-` | Capability-Text von der Standardeingabe lesen. | Ende mit Leerzeile. |
| `-f` | Ausführung erzwingen. | Laut Manpage auch bei als ungültig angesehenen Operationen; meiden. |
| `-h` | Kurzhilfe. | Rückgabe `0`. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Einem selbst entwickelten Webserver erlauben, Port 80 zu öffnen, ohne ihn als Root zu starten. Das Setzen im echten System braucht Root und ist hier ein **Beispielszenario**. Danach folgt die tatsächlich geprüfte, ungefährliche Variante.

### Beispielszenario mit Root (nicht ausgeführt)

```bash
sudo setcap cap_net_bind_service+ep /usr/local/bin/meinserver
getcap /usr/local/bin/meinserver
```

Erwartet: `/usr/local/bin/meinserver cap_net_bind_service=ep`. Die Datei sollte Root gehören und nicht für andere beschreibbar sein, sonst könnte jemand den Inhalt austauschen.

### Geprüfte Variante: Benutzer-Namensraum mit eigener Datei

```bash
uebung="$(mktemp -d -t netmon-setcap-XXXXXX)" || exit 1
cd "$uebung" || exit 1
cp /bin/true prog
unshare -r setcap cap_net_bind_service+ep prog
getcap -n prog
```

`unshare -r` startet `setcap` in einem eigenen Benutzer-Namensraum, in dem dein Konto als Root gilt. Die Capability wird dadurch **namensraumgebunden** geschrieben. `getcap -n` zeigt `prog cap_net_bind_service=ep [rootid=1000]`: Sie wirkt nur in Namensräumen, deren Root deiner UID 1000 entspricht, und gibt im normalen System **keine** Zusatzrechte.

### Prüfen und entfernen

```bash
unshare -r setcap -v cap_net_bind_service+ep prog
unshare -r setcap -r prog
getcap -v prog
```

`-v` meldet `prog: OK`. Nach `-r` zeigt `getcap -v` nur noch den Dateinamen.

## 6. Typische Anwendungsfälle

| Aufgabe | Capability |
| --- | --- |
| Dienst auf Port unter 1024 ohne Root | `cap_net_bind_service+ep` |
| Netzwerkdiagnose mit Raw-Sockets (`ping`, `mtr`) | `cap_net_raw+ep` |
| Paketmitschnitt (`dumpcap` von Wireshark) | `cap_net_raw,cap_net_admin+ep` |
| Gezielte Rechteentziehung | leerer Satz `=` |

Auf dem geprüften System tragen `ping`, `mtr-packet` und `dumpcap` bereits solche Capabilities; Pakete setzen sie bei der Installation.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Warum „danger“

Jede Capability ist ein Stück Root. Manche sind **praktisch vollständige Root-Rechte**, zum Beispiel `cap_sys_admin`, `cap_setuid`, `cap_dac_override` oder `cap_sys_ptrace`. Setzt man sie auf ein Programm, das beliebige Befehle oder Dateien verarbeitet (eine Shell, `python3`, einen Editor), kann jeder lokale Benutzer damit Root werden. Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ wurde deshalb auf `danger` angehoben.

### Weitere Punkte

- **Beschreibbare Dateien:** Kann ein normaler Benutzer die Datei ändern, kann er eigenen Code mit den Capabilities ausstatten lassen. Programme mit Capabilities gehören Root und haben höchstens `755`.
- **Leerer Satz `=` gegenüber `-r`:** Laut Manpage ist ein leerer Satz nicht dasselbe wie das Entfernen. Ein leerer Satz verhindert gezielt, dass Ambient- oder Inheritable-Capabilities beim Start wirken.
- **Unsichtbarkeit:** `ls -l` zeigt Capabilities nicht an. Sie fallen nur mit `getcap` auf. Sicherheitsprüfungen sollten `getcap -r` einschließen.
- **Dateisysteme:** Ohne Unterstützung erweiterter Attribute (manche Netz- oder FAT-Dateisysteme) schlägt `setcap` fehl.

## 8. Häufige Fehler

| Meldung | Ursache | Vorgehen |
| --- | --- | --- |
| `unable to set CAP_SETFCAP effective capability: Operation not permitted` | Ohne Root aufgerufen. | Nur nach Prüfung mit Verwaltungsrechten. |
| `Invalid file '...' for capability operation` | Symbolischer Link oder keine reguläre Datei. | Echten Pfad mit `readlink -f` ermitteln. |
| `fatal error: Invalid argument` mit Kurzhilfe | Unbekannter Capability-Name oder falsche Textform. | Schreibweise gegen `capabilities(7)` prüfen. |
| `... differs in [pe]` | `-v` fand andere Capabilities. | Mit `getcap` den Ist-Zustand prüfen. |
| Programm verliert Rechte nach Update | Datei wurde ersetzt. | Capability neu setzen oder Paketmechanismus nutzen. |

`setcap` endet laut Manpage mit `0` bei Erfolg und `1` bei Fehlern; das bestätigten die Tests.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Nur die kleinste nötige Capability** vergeben, meist `cap_net_bind_service` oder `cap_net_raw`.
2. **Niemals auf Interpreter, Shells oder Editoren.**
3. **Datei vorher absichern:** Eigentümer Root, keine Schreibrechte für andere.
4. **Mit `setcap -v` und `getcap` kontrollieren.**
5. **Zum Üben einen Benutzer-Namensraum verwenden** wie im geprüften Beispiel.
6. **Alternative prüfen:** Bei systemd-Diensten lässt sich eine Capability oft in der Dienstdefinition vergeben, statt die Datei dauerhaft zu verändern.

### Prüfstand

- **Geprüfte Version:** libcap 2.66 (Paket libcap2-bin 1:2.66-5ubuntu2.4).
- **Tatsächlich ausgeführt** an einer Kopie von `/bin/true` im eigenen Testordner: Ablehnung ohne Root (Rückgabe 1), `-v` mit Abweichung, Setzen in `unshare -r` (namensraumgebunden, `rootid=1000`), `-v` mit `OK`, Verlust bei `cp`, Entfernen mit `-r`, Ablehnung eines Symlinks, ungültiger Name, `-h`.
- **Nicht geprüft:** Setzen mit echten Root-Rechten, Wirkung beim Programmstart, leerer Satz `=`, `-n`, `-f`, Dateisysteme ohne erweiterte Attribute.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `getcap` | Zeigt Datei-Capabilities; auch rekursiv. |
| `capsh` | Untersucht Capabilities und hilft mit `--suggest` bei der Auswahl. |
| `getpcaps` | Zeigt Capabilities laufender Prozesse. |
| `chmod u+s` | Klassisches setuid; gibt volle Rechte des Eigentümers. |
| `unshare -r` | Startet einen Benutzer-Namensraum für gefahrlose Übungen. |

Ausgangseintrag: Datensatz 117 in `index.json` (`setcap`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Die Root-Angabe wurde auf „erforderlich“ und die Risikostufe auf „Gefahr“ korrigiert. Das nicht funktionierende Beispiel `setcap --help` wurde durch `setcap -h`, die Capability-Schreibweise und einen geprüften Ablauf ersetzt.
