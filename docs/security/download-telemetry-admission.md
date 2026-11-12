# Download-Statistik: Redirect wartet nicht auf den Statistik-Schreiber

## Nachtrag 12.11.2026

Finding: **Public download requests can exhaust PHP workers through
synchronous telemetry rewrites** (Scan `4852934e`, Finding 4, MEDIUM,
Revision `bac02d28`).

Bisher hat jeder anonyme Aufruf von `download.php` vor dem 302-Redirect den
globalen Statistik-Lock geholt. Danach hat er den ganzen JSON-Zustand gelesen,
neu geschrieben, per `fsync` gesichert und umbenannt. Wer den Lock nicht bekam,
hat bis zu 1 s gewartet. Gleichzeitige Aufrufe haben so PHP-Worker blockiert.

Neues Verhalten (`site/download-lib.php`):

- Der Redirect-Pfad wartet höchstens 50 ms auf den Statistik-Lock
  (`NETMON_DOWNLOAD_LOCK_WAIT_MS`). Bekommt er ihn, schreibt er wie bisher
  atomar und mit `fsync`.
- Bekommt er ihn nicht, hängt er den Treffer als eine JSON-Zeile an die
  begrenzte Warteschlange `<stats>.pending` an (höchstens 256 KiB, Zeilen
  höchstens 8 KiB). Ist die Warteschlange voll, wird der Treffer verworfen.
  Die Platte wächst also nicht unbegrenzt, und der Download funktioniert
  weiter.
- Der nächste Schreiber, der den Lock bekommt, übernimmt die Warteschlange
  per `rename` nach `<stats>.draining`. Dafür wartet er nur auf Anhänger, die
  gerade eine Zeile schreiben. Er prüft jede Zeile erneut: Pflichtfelder als
  Text, Längengrenzen, Datumsformat. Gültige Treffer zählt er in einem einzigen
  atomaren Schreibvorgang mit. Erst danach entfernt er die übernommene Datei.
  Ungültige oder nicht mehr anwendbare Zeilen fallen weg und blockieren die
  Statistik nicht dauerhaft.
- Scheitert dieses Schreiben, bleibt `<stats>.draining` liegen. Beim nächsten
  Mal wird es genau einmal angewendet.
- Die Statistikansicht mit Token übernimmt vor dem Lesen ebenfalls die
  Warteschlange.
- Die Warteschlange wird exklusiv angelegt (`x`, folgt keinem gepflanzten
  Symlink), hat Modus `0600` und dieselben Prüfungen wie der JSON-Zustand:
  reguläre Datei, genau ein Link, gleiche Identität nach dem Öffnen. Ein
  Anhänger schreibt nur, solange seine Datei noch `<stats>.pending` heißt.

Grenzen:

- Ein Rate-Limit pro Client gibt es im Repository nicht. Stock-Caddy bietet
  keines ohne Plugin. Ein Limit am Reverse-Proxy oder in PHP-FPM bleibt eine
  Betriebsaufgabe.
- Bei anhaltender Flut gehen Zählungen jenseits der Warteschlangengrenze
  verloren.

Validierung: 319 PHP-gestützte Tests (`tests/test_download_statistics*.py`)
mit PHP 8.3.6 CLI, isoliert in einem eigenen Netzwerk-Namespace
(`unshare -rn`, nur Loopback), dreimal hintereinander grün. Neu sind die Fälle
für den gehaltenen Lock (20 Treffer statt rund 20 s jetzt unter 2,5 s), die
volle Warteschlange, ungültige Zeilen, einen liegengebliebenen Stapel und einen
gepflanzten Symlink. Kein Zugriff auf die öffentliche Website.
