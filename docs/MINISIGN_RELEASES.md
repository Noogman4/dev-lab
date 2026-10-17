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

Ohne `minisign`, Secret Key oder Public Key bricht ein Release-Build ab. Fuer
einen bewusst unsignierten lokalen Test-Build ist ein explizites Opt-out
erforderlich:

```bash
NETMON_ALLOW_UNSIGNED_BUILD=1 make site-build
```

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

## Upload

Bei signierten Releases muessen diese Dateien mit hochgeladen werden:

- `public_html/dist/SHA256SUMS.minisig`
- `public_html/verify/netmonroots.minisign.pub`
- `public_html/verify/verify_netmon_signature.sh`
- `public_html/latest-version.json`

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
- unsignierte lokale Test-Builds benoetigen `NETMON_ALLOW_UNSIGNED_BUILD=1`
- der echte Public Key ist in `SECURITY.md` und als kanonische Datei im
  Repository gepinnt
- der ausgelieferte Verifier erzwingt denselben Key ohne Opt-in und ohne Override
- lokale Regressionstests verwenden eine bereits signierte NetMon-1.1.21-Fixture
  sowie temporaere Angreifer-Keys und fuehren den produktiven Verifier ohne
  Testmodus oder Austausch des eingebauten Pins aus
