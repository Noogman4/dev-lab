# Security Policy

## Supported Versions

The current supported public release line is:

| Version | Supported |
| --- | --- |
| `1.1.21` | Yes |
| `1.1.20` and older | No |

Security fixes are prepared against the current maintained release line first.
Repository development snapshots are not separate supported release lines.

## Release Authenticity

Production release bundles must include a Minisign signature and public key.
The build fails when either key material or `minisign` is missing. The public
key is pinned in this repository so users can compare it independently from
the download server.

Both production bundle scripts always sign and verify before success.
`NETMON_ALLOW_UNSIGNED_BUILD` cannot bypass either check. Builds use private
staging; older outputs are retained outside the current output path in
`dist/.release-history/`, and failed staging is removed. The final ZIP is checked
by `scripts/verify_netmon_release_bundle.py` with the repository verifier.
A separate signed `verify/RELEASE-SHA256SUMS` binds every bundled file except
itself and its own signature. Exact membership is required; old bundles without
this manifest are rejected. The staged upload directory must also match the
authenticated ZIP before promotion. Download checksum verification is unchanged.
Unsigned local payload tests use only `make unsigned-test-bundle`, with separate
`unsigned-test-builds/` output, different names, an `UNSIGNED-TEST-ONLY` marker
and no production upload structure. Never publish these test artifacts.

There is no automated publication job in this repository. Before manual upload,
run the [local publication gate](docs/MINISIGN_RELEASES.md#upload-und-lokale-freigabepruefung)
on the exact ZIP to upload. It rejects unsigned, invalid and relabelled test
bundles, checks both pinned signatures and every bundled file hash, and validates the
production structure. This is not a server-side enforcement guarantee.

- Minisign key ID: `54BF5F1867BDD004`
- Canonical key file: [`docs/security/netmonroots.minisign.pub`](docs/security/netmonroots.minisign.pub)
- Public key: `RWQE0L1nGF+/VDIfeLCEp4x2UutfhhdCmPKSMTZY05kXJprqXyXfzo9R`

`scripts/verify_netmon_signature.sh` embeds this exact key as a mandatory trust
anchor. It rejects missing, unreadable, malformed, and different key files before
running Minisign, then verifies the signature with the embedded key. Environment
variables, including the obsolete `NETMON_EXPECTED_MINISIGN_PUBKEY`, cannot
override or disable this check. There is no alternate-key or test-mode bypass.

Use the verifier from an independently obtained, reviewed checkout of this
repository containing the H-01 fix. A verifier downloaded together with the
release from `netmonroots.com` cannot establish trust if that server is
compromised: an attacker could replace the script as well as the key and files.
The downloaded key must match the script's built-in pin automatically.

Verify `SHA256SUMS.minisig` first, then run `sha256sum -c SHA256SUMS` only if
signature verification succeeds. Install only after both checks pass. Verification
is local and needs no network connection once the inputs and trusted verifier
are available. `SHA256SUMS` alone is not proof of origin. See the
[verification instructions](docs/MINISIGN_RELEASES.md#verifikation-fuer-nutzer).

## Reporting a Vulnerability

Please do **not** open a public GitHub issue for a suspected security problem.

Instead, report it privately to:

- `support@netmonroots.com`
- `info@netmonroots.com`

Please include, if possible:

- affected NetMon version
- operating system and version
- clear reproduction steps
- impact assessment
- logs, screenshots, or proof of concept if available

## Disclosure Process

- We review incoming reports and try to confirm the issue.
- If the issue is valid, we prepare a fix for the active supported release line.
- After a fix is available, we can disclose the issue publicly in a coordinated way.

## Scope

This policy covers:

- the NetMon application
- Debian release artifacts published for NetMon
- the public website content at `netmonroots.com` that belongs to NetMon distribution and release handling

## Additional Security Notes

For technical background, audit notes, operational risks, and internal hardening context, see:

- [docs/SECURITY.md](docs/SECURITY.md)
