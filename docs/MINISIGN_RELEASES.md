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
- der passende oeffentliche Schluessel liegt ausserhalb des Repos bereit
- die Public-Key-Zeile ist unabhaengig von `netmonroots.com` in `SECURITY.md`
  und unter `docs/security/netmonroots.minisign.pub` gepinnt

Aktueller Release-Key:

- Key-ID: `54BF5F1867BDD004`
- Public Key: `RWQE0L1nGF+/VDIfeLCEp4x2UutfhhdCmPKSMTZY05kXJprqXyXfzo9R`

## Schluessel erzeugen

```bash
mkdir -p ~/.config/netmonroots/minisign
minisign -G \
  -p ~/.config/netmonroots/minisign/netmonroots.minisign.pub \
  -s ~/.config/netmonroots/minisign/netmonroots.minisign.key
```

Hinweise:

- den Secret Key niemals ins Repository legen
- den Public Key mit der Website ausliefern und zusaetzlich unabhaengig pinnen
- beim Generieren vergibt `minisign` eine Passphrase fuer den Secret Key

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

Der Public Key muss vor dieser Pruefung mit der unabhaengig veroeffentlichten
Public-Key-Zeile verglichen werden. Der Verifier kann diesen Pin zusaetzlich
erzwingen:

```bash
NETMON_EXPECTED_MINISIGN_PUBKEY='RWQE0L1nGF+/VDIfeLCEp4x2UutfhhdCmPKSMTZY05kXJprqXyXfzo9R' \
bash verify_netmon_signature.sh \
  netmonroots.minisign.pub \
  SHA256SUMS.minisig \
  SHA256SUMS
```

Die Key-Zeile stammt aus dem bereits kontrolliert erzeugten Release-Key und
wird nicht automatisch aus der Download-Origin uebernommen.

## Aktueller Repo-Status

- Website- und Release-Update-Build erzwingen signierte Releases
- Signatur und bereitgestellter Public Key werden im Build direkt verifiziert
- unsignierte lokale Test-Builds benoetigen `NETMON_ALLOW_UNSIGNED_BUILD=1`
- der echte Public Key ist in `SECURITY.md` und als kanonische Datei im
  Repository gepinnt
