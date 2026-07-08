# NetMon Minisign Releases

## Zweck

NetMon kann Release-Dateien nicht nur per `SHA256SUMS`, sondern zusaetzlich mit `minisign` absichern.

Das Ziel:

- Nutzer pruefen zuerst die Hashes
- danach koennen sie die Hash-Datei selbst kryptografisch verifizieren
- dadurch ist nicht nur die Datei-Integritaet, sondern auch die Herkunft der Hash-Datei abgesichert

## Voraussetzungen

- `minisign` ist lokal installiert
- der geheime Signaturschluessel liegt ausserhalb des Repos
- der oeffentliche Schluessel kann spaeter mit ausgeliefert werden

## Schluessel erzeugen

```bash
mkdir -p ~/.config/netmonroots/minisign
minisign -G \
  -p ~/.config/netmonroots/minisign/netmonroots.minisign.pub \
  -s ~/.config/netmonroots/minisign/netmonroots.minisign.key
```

Hinweise:

- den Secret Key niemals ins Repository legen
- den Public Key darfst du mit der Website ausliefern
- beim Generieren vergibt `minisign` eine Passphrase fuer den Secret Key

## Signierten Website-Build erzeugen

```bash
NETMON_MINISIGN_SECRET_KEY=~/.config/netmonroots/minisign/netmonroots.minisign.key \
NETMON_MINISIGN_PUBKEY=~/.config/netmonroots/minisign/netmonroots.minisign.pub \
make site-build
```

Wenn alles vorhanden ist, erzeugt der Build zusaetzlich:

- `dist/site-build/public_html/dist/SHA256SUMS.minisig`
- `dist/site-build/public_html/verify/netmonroots.minisign.pub`
- `dist/site-build/public_html/verify/verify_netmon_signature.sh`
- `dist/site-build/public_html/latest-version.json` bleibt Teil des Upload-Bundles und sollte zum veroeffentlichten Paketstand passen

## Signiertes Release-Update ohne kompletten Website-Build

Wenn nur Paket, Doku, `SHA256SUMS` und Signatur aktualisiert werden muessen:

```bash
NETMON_MINISIGN_SECRET_KEY=~/.config/netmonroots/minisign/netmonroots.minisign.key \
NETMON_MINISIGN_PUBKEY=~/.config/netmonroots/minisign/netmonroots.minisign.pub \
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

Hash pruefen:

```bash
sha256sum -c SHA256SUMS
```

Signatur pruefen:

```bash
bash verify_netmon_signature.sh \
  netmonroots.minisign.pub \
  SHA256SUMS.minisig \
  SHA256SUMS
```

## Aktueller Repo-Status

- der Website-Build unterstuetzt signierte Releases bereits
- ohne installiertes `minisign` oder ohne gesetzte Key-Variablen wird nur unsigniert gebaut
- das ist fuer Test-Builds in Ordnung, aber fuer produktive Releases ist Signatur empfehlenswert
