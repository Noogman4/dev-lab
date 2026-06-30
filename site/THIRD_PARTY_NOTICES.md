# Third-Party Notices

This file summarizes third-party software, libraries, and bundled components
used by NetMon.

NetMon itself is licensed under `GPL-3.0-or-later`.
All trademarks, copyrights, and license rights for third-party components
remain with their respective authors and projects.

For future updates and supplemental legal notes, see:

- `https://netmonroots.com`
- planned legal overview: `https://netmonroots.com/legal`

## 1. Python runtime dependencies used by NetMon

- `psutil`
  Version seen in local environment: `5.9.8`
  Author: Giampaolo Rodola
  License: `BSD-3-Clause`
  Project: `https://github.com/giampaolo/psutil`
  Purpose in NetMon: local system, process, memory, temperature, and uptime data
  Local verification note: package metadata and a local `LICENSE` file were found

- `Pillow`
  Version seen in local environment: `10.2.0`
  Author: Pillow contributors
  License: `HPND`
  Project: `https://python-pillow.org`
  Purpose in NetMon: image handling and `ImageTk` support for log and UI image workflows
  Local verification note: license classifier found in installed package metadata

- `PyPDF2`
  Version seen in local environment: `2.12.1`
  Author: PyPDF2 / pypdf contributors
  License: `BSD-style` according to installed package classifier
  Project: `https://pypdf2.readthedocs.io/`
  Purpose in NetMon: PDF reading helpers where optional document tooling is enabled
  Local verification note: BSD license classifier found in installed package metadata

- `keyring`
  Version seen in local environment: `24.3.1`
  Author: keyring contributors
  License: `MIT`
  Project: `https://github.com/jaraco/keyring`
  Purpose in NetMon: optional secure storage for API keys in the system keyring
  Local verification note: MIT license classifier found in installed package metadata

## 2. Optional Python components referenced by the project

- `PySide6`
  Version seen in local development environment: `6.11.0`
  Author: Qt for Python / The Qt Company and contributors
  License: `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only`
  Project: `https://doc.qt.io/qtforpython/`
  Purpose in NetMon: optional Qt-related project components or tools where applicable
  Local verification note: license string found in local wheel metadata under the project venv

- `reportlab`
  Author: ReportLab contributors
  License: upstream ReportLab license applies
  Project: `https://www.reportlab.com/`
  Purpose in project tooling: PDF generation used by local documentation build scripts
  Local verification note: referenced by build scripts, not installed in the current local Python runtime during this review

- `pygame`
  Version seen in local environment: `2.5.2`
  Author: pygame community project
  License: `LGPL`
  Project: `https://www.pygame.org`
  Purpose in NetMon: optional Fun runtime components
  Local verification note: LGPL classifier found in installed package metadata

- `pgzero`
  Version seen in local environment: `1.2`
  Author: Daniel Pope and contributors
  License: `LGPLv3` according to installed package classifier
  Project: `https://pypi.org/project/pgzero/`
  Purpose in NetMon: optional Fun runtime components
  Local verification note: LGPLv3 classifier found in installed package metadata

## 3. Bundled or redistributed content

- `Code-the-Classics.zip`
  Source reference found in bundled archive: `Code-the-Classics/README.md`
  Additional bundled reference: `Code-the-Classics/README (2).md`
  Upstream reference: `https://magazine.raspberrypi.com/books/code-the-classics-vol-I-2ed`
  Copyright: `Raspberry Pi Foundation`
  License: `BSD 2-Clause`
  Purpose in NetMon: optional import/archive for the Fun area
  Redistribution note: binary redistribution is permitted if the copyright
  notice, license conditions, and disclaimer are reproduced in the documentation
  and/or other materials provided with the distribution.
  Packaging note: NetMon ships a separate `CODE_THE_CLASSICS_LICENSE.txt`
  alongside package documentation to satisfy this notice requirement.

## 4. External system tools invoked by NetMon

NetMon can call installed system programs that are not shipped as part of the
main Python application. These tools remain under the licenses of their
respective upstream projects and Linux distribution packages.

Examples include:

- `ufw`
- `nmcli` / NetworkManager
- `wg` / `wireguard-tools`
- `curl`
- `dig` / `dnsutils`
- `traceroute`
- `mtr`
- `nmap`
- `iftop`
- `htop`
- `lynis`
- `rkhunter`
- `clamav` / `freshclam`
- `mpv`
- `speedtest` / `speedtest-cli`
- `cryptsetup`
- `whois`
- `xdg-open`

These programs are not relicensed by NetMon. Their original authors and
maintainers should be credited through their respective package metadata,
project pages, and distribution documentation.

## 5. Release follow-up before public distribution

The following items should be checked again before a final public package or
website release:

- Verify whether `Code-the-Classics.zip` may be redistributed in the exact form
  bundled by NetMon whenever the bundled archive content changes materially.
- If `PySide6` is actually shipped in a NetMon release path, confirm whether
  the corresponding Qt for Python license texts should be added to the package
  documentation.
- If `reportlab` is declared as a supported local build dependency for end
  users, consider adding its original license text or a more exact upstream
  reference.
- For Debian-style packages, consider also copying or referencing relevant
  upstream license texts in `/usr/share/doc/netmon/` if the packaged release
  redistributes those components directly.

## 6. Developer and attribution note

NetMon project lead:

- Happy

Technical assistance credited in the application:

- Chad
- Codi

This notice file is a practical attribution overview for the project. It does
not replace original upstream license texts, package copyright files, or
distribution-level legal documentation.
