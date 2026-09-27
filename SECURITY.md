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

- Minisign key ID: `54BF5F1867BDD004`
- Canonical key file: [`docs/security/netmonroots.minisign.pub`](docs/security/netmonroots.minisign.pub)
- Public key: `RWQE0L1nGF+/VDIfeLCEp4x2UutfhhdCmPKSMTZY05kXJprqXyXfzo9R`

The copy downloaded from `netmonroots.com` must match this exact public key.
`SHA256SUMS` alone provides an integrity check and is not proof of origin.

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
