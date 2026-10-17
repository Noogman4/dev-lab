# NetMon Minisign Releases

## Zweck

NetMon sichert Release-Dateien mit signierten `SHA256SUMS` und `minisign` ab.

Das Ziel:

- Nutzer verifizieren zuerst die Signatur von `SHA256SUMS` mit dem fest gepinnten NetMon-Key
- nur bei erfolgreicher Signaturpruefung pruefen sie die Hashes der Release-Dateien
- dadurch ist nicht nur die Datei-Integritaet, sondern auch die Herkunft der Hash-Datei abgesichert

## Voraussetzungen

- `minisign` ist lokal installiert
- der geheime Signaturschluessel liegt ausserhalb des Repos
- der kanonische oeffentliche Schluessel liegt unter `docs/security/netmonroots.minisign.pub`
- die Public-Key-Zeile ist unabhaengig von `netmonroots.com` in `SECURITY.md`
  und unter `docs/security/netmonroots.minisign.pub` gepinnt

Aktueller Release-Key:

- Key-ID: `54BF5F1867BDD004`
- Public Key: `RWQE0L1nGF+/VDIfeLCEp4x2UutfhhdCmPKSMTZY05kXJprqXyXfzo9R`

Der Verifier enthaelt diesen Key als feste Konstante. Er prueft die komplette
Public-Key-Datei vor dem Start von Minisign und uebergibt Minisign ausschliesslich
die Konstante. Fehlende, nicht lesbare, beschaedigte oder abweichende
Schluesseldateien fuehren zum Abbruch. `NETMON_EXPECTED_MINISIGN_PUBKEY` ist
wirkungslos; auch andere Umgebungsvariablen koennen den Pin nicht aendern oder
deaktivieren. Es gibt keinen alternativen Schluessel und keinen Testmodus im
produktiven Verifier.

## Bestehenden Release-Schluessel verwenden

Fuer Releases wird ausschliesslich der vorhandene Release-Schluessel verwendet.
Den Secret Key ausserhalb des Repositorys aufbewahren und niemals einchecken.
Diese Haertung erzeugt keinen neuen Release-Schluessel und rotiert keinen Key.

## Signierten Website-Build erzeugen

```bash
NETMON_MINISIGN_SECRET_KEY=~/.config/netmonroots/minisign/netmonroots.minisign.key \
make site-build
```

Ohne `NETMON_MINISIGN_PUBKEY` verwendet der Build automatisch den im
Repository gepinnten Public Key. Ein abweichender expliziter Public Key wird
abgelehnt.

Wenn alles vorhanden ist, erzeugt der Build zusaetzlich:

- `dist/site-build/public_html/dist/SHA256SUMS.minisig`
- `dist/site-build/public_html/verify/netmonroots.minisign.pub`
- `dist/site-build/public_html/verify/verify_netmon_signature.sh`
- `dist/site-build/public_html/latest-version.json` bleibt Teil des Upload-Bundles und sollte zum veroeffentlichten Paketstand passen

Ohne `minisign`, lesbaren Secret Key oder passenden Public Key bricht jeder
Produktions-Build ab. `NETMON_ALLOW_UNSIGNED_BUILD` wird nicht mehr ausgewertet;
auch `=1` kann Signierung und Verifikation nicht umgehen.

Beide Builds arbeiten zunaechst privat unter `dist/.release-work/`. Erst nach
Signaturpruefung, ZIP-Freigabepruefung und erneuter Hash-/Signaturpruefung des
Upload-Ordners erscheint das Ergebnis am Produktionspfad. Ein vorhandener
Ausgabeordner wird zu Beginn unter `dist/.release-history/` aufbewahrt und ist
kein Ergebnis des neuen Laufs. Bei Fehlern wird der private Arbeitsordner entfernt;
es gibt keinen neuen Produktionsordner und keine neue Upload-ZIP. Parallele Builds
desselben Typs werden ueber `flock` ausgeschlossen. Alte Artefakte in der Historie
nicht als aktuelle Ausgabe hochladen. Nur bei Exit-Code 0 und neuer erfolgreicher
Freigabepruefung fortfahren.

## Separater unsignierter lokaler Test

```bash
make unsigned-test-bundle
```

Dieser Einstieg verpackt die lokal vorhandenen Paket-/Dokudateien ausschliesslich
fuer Tests unter `unsigned-test-builds/test-*/netmon-UNSIGNED-TEST-ONLY.zip`.
Er ruft keines der Produktionsskripte auf, hat keine Signieroption und schreibt
weder `dist/site-build/` noch `dist/site-release-update/`. Im ZIP liegen eine
`UNSIGNED-TEST-ONLY/`-Wurzel, ein dauerhafter Marker, eine Testidentitaet mit
`production_release: false` und umbenannte Testdateien. Es gibt keine
`public_html`-Uploadstruktur, `latest-version.json`, Produktions-Summendatei oder
Release-Signatur. **Nicht veroeffentlichen und nicht als Release installieren.**
Fuer eine lokale Website-Vorschau weiterhin `make site-serve` verwenden.

## Signiertes Release-Update ohne kompletten Website-Build

Wenn nur Paket, Doku, `SHA256SUMS` und Signatur aktualisiert werden muessen:

```bash
NETMON_MINISIGN_SECRET_KEY=~/.config/netmonroots/minisign/netmonroots.minisign.key \
make site-release-update
```

Dabei entsteht ein kleines Upload-Bundle unter:

- `dist/site-release-update/public_html/`
- `dist/site-release-update/netmonroots_release_update.zip`

Das Update-Bundle enthaelt nur die Release-relevanten Dateien und ist fuer Routine-
Updates des Downloadbereichs gedacht.

## Upload und lokale Freigabepruefung

Im Repository existiert kein automatisierter CI-, GitHub-Release-, SCP-/Rsync-
oder cPanel-Publikationsjob. Die Auslieferung erfolgt manuell. Die folgende
Pruefung ist eine lokale Schranke, keine behauptete serverseitige CI-Garantie.

Unmittelbar vor einem Upload aus einem unabhaengig geprueften Checkout ausfuehren:

```bash
python3 scripts/verify_netmon_release_bundle.py \
  dist/site-build/netmonroots_public_html.zip --kind site
# oder fuer das kleine Update-Bundle:
python3 scripts/verify_netmon_release_bundle.py \
  dist/site-release-update/netmonroots_release_update.zip --kind update
```

Nur die erfolgreich gepruefte ZIP hochladen und deren ausgegebenen SHA-256-Wert
beibehalten. Nach Aenderungen erneut pruefen. Die Pruefung verwendet ausschliesslich
den Repository-Verifier mit dessen festem H-01-Pin, niemals das Skript aus der ZIP.
Auch die mitgelieferten Verifikationsskripte muessen bytegleich mit diesem
Checkout sein; ein altes oder manipuliertes Verifikationsskript wird abgelehnt.
Sie prueft Signatur und exakte Payload-Hashes, Produktionsnamen, Version, benoetigte
Dateien/Struktur und das Fehlen von `UNSIGNED-TEST-ONLY` in Pfaden und Dateiinhalten.
Ein umbenanntes oder in den Produktionsbereich kopiertes Test-ZIP wird abgelehnt.
Symlinks, Sonderdateien, doppelte/unsichere Pfade und widerspruechliche ZIP-Metadaten
sind ebenfalls unzulaessig. Die Pruefung benoetigt keine Netzwerkverbindung.

Mit hochgeladen werden muessen insbesondere:

- `public_html/dist/SHA256SUMS` und `SHA256SUMS.minisig`
- alle drei in den signierten Summen aufgefuehrten Paket-/Dokudateien
- `public_html/verify/netmonroots.minisign.pub`
- `public_html/verify/verify_netmon_signature.sh`
- `public_html/latest-version.json`

Die Minisign-Signatur authentifiziert die drei Payload-Hashes, nicht jede
Website-Datei und nicht den ZIP-Container als Ganzes. Die ZIP-Pruefung liefert
zusaetzliche Struktur-/Integritaetskontrollen. Details, Ressourcenlimits und
Betriebsannahmen: [M-04](security/M-04.md).

## Verifikation fuer Nutzer

Den Verifier aus einem unabhaengig bezogenen, geprueften Checkout des
[Projekt-Repositorys](https://github.com/Noogman4/dev-lab) mit H-01-Fix verwenden.
Den absoluten Pfad unten anpassen. Der Checkout einschliesslich Verifier und
eingebautem Pin muss vertrauenswuerdig sein. Ein Skript, das gemeinsam mit
Schluessel, Signatur und Artefakten vom moeglicherweise kompromittierten
Downloadserver kommt, kann diesen Vertrauensanker nicht ersetzen.

Im Downloadverzeichnis mit `SHA256SUMS`, `SHA256SUMS.minisig`, der gelieferten
`netmonroots.minisign.pub` und allen in `SHA256SUMS` aufgefuehrten Dateien:

```bash
NETMON_REPO=/absoluter/pfad/zum/vertrauten/dev-lab
bash "$NETMON_REPO/scripts/verify_netmon_signature.sh" \
  netmonroots.minisign.pub \
  SHA256SUMS.minisig \
  SHA256SUMS &&
sha256sum -c SHA256SUMS
```

Der feste Pin wird immer automatisch geprueft; eine Umgebungsvariable ist nicht
erforderlich. Bei einem Fehler abbrechen und nicht installieren. Erst wenn
Signatur und alle Dateihashes gueltig sind, ist die Pruefung erfolgreich.
Der gesamte Pruefschritt funktioniert ohne Netzwerkverbindung. Ein alleiniger
SHA-256-Vergleich belegt keine Herkunft.

## Aktueller Repo-Status

- Website- und Release-Update-Build erzwingen signierte Releases
- Signatur und bereitgestellter Public Key werden im Build direkt verifiziert
- unsignierte Testpakete entstehen ausschliesslich ueber `make unsigned-test-bundle`
- `NETMON_ALLOW_UNSIGNED_BUILD` hat keinerlei Freigabewirkung
- der echte Public Key ist in `SECURITY.md` und als kanonische Datei im
  Repository gepinnt
- der ausgelieferte Verifier erzwingt denselben Key ohne Opt-in und ohne Override
- lokale Regressionstests verwenden eine bereits signierte NetMon-1.1.21-Fixture
  sowie temporaere Angreifer-Keys und fuehren den produktiven Verifier ohne
  Testmodus oder Austausch des eingebauten Pins aus
