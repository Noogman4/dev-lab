# Legal Release Checklist

Diese Checkliste ist fuer den finalen NetMon-Release gedacht, bevor eine `.deb`,
eine Website-Version oder ein oeffentliches Downloadpaket verteilt wird.

## 1. Projektlizenz

- `LICENSE` ist im Repo vorhanden und entspricht der gewollten Lizenz `GPL-3.0-or-later`.
- Der About-Dialog zeigt die Projektlizenz korrekt an.
- Die Paketierung kopiert `LICENSE` in die finale Release-Struktur oder verlinkt sauber auf die installierte Lizenzdatei.

## 2. Third-Party Notices

- `THIRD_PARTY_NOTICES.md` ist aktuell und beschreibt reale Runtime-Abhaengigkeiten.
- Optionale Komponenten sind klar von Pflicht-Abhaengigkeiten getrennt.
- Build-Only-Komponenten sind als solche gekennzeichnet.
- Externe Systemtools sind nur als verwendete Programme beschrieben, nicht als von NetMon mitlizenzierte Bestandteile.

## 3. Original-Lizenztexte

- Fuer redistribuierte Drittkomponenten ist geprueft, ob zusaetzliche Original-Lizenztexte mitgeliefert werden muessen.
- Falls ja, liegen diese Texte zusaetzlich im Paket oder in `/usr/share/doc/netmon/`.
- Fuer Debian-Pakete ist geprueft, ob ein Verweis auf Systemlizenzpfade ausreicht oder ob eigene Kopien notwendig sind.

## 4. Bundled Content

- `Code-the-Classics.zip` ist rechtlich zur Redistribution freigegeben.
- Fuer `Code-the-Classics.zip` sind Quelle, Autorenhinweis und Lizenzlage nachvollziehbar dokumentiert.
- Der BSD-2-Clause-Hinweis fuer `Code-the-Classics.zip` liegt dem Paket als Begleittext bei.
- Alle sonstigen Bilder, Icons, Fonts, PDFs oder ZIP-Dateien im Paket sind auf Herkunft und Nutzungsrechte geprueft.

## 5. Website / Public Legal Page

- `site/legal.html` ist vorhanden und konsistent mit `THIRD_PARTY_NOTICES.md`.
- Die Website nennt Projektlizenz, Credits, Drittanbieterhinweise und Kontaktadresse.
- Der Link `https://netmonroots.com/legal` ist vor Release wirklich erreichbar.
- Die Webtexte behaupten nichts, was lokal nicht geprueft oder dokumentiert ist.

## 6. Credits / Attribution

- Projektleitung ist korrekt genannt.
- Technische Assistenz / Credits sind konsistent zwischen App, Repo und Website.
- Drittprojekte werden nicht nur technisch, sondern auch namentlich nachvollziehbar erwaehnt, wenn das fuer Attribution sinnvoll ist.

## 7. Packaging Check

- Das Debian-Paket enthaelt oder referenziert:
  - `LICENSE`
  - `THIRD_PARTY_NOTICES.md`
  - ggf. weitere notwendige Upstream-Lizenztexte
- Die Installationspfade fuer diese Dateien sind im About-Dialog und in der Doku nachvollziehbar.
- Es gibt keinen mitgelieferten Fremdinhalt ohne gepruefte Lizenzlage.

## 8. Final Review

- Release-Stand von App, Doku und Website ist auf dieselbe Version abgestimmt.
- Alte Platzhalter (`planned`, `optional`, `spaeter`) sind fuer den oeffentlichen Release entfernt oder klar als Roadmap markiert.
- Ein letzter manueller Review von:
  - `LICENSE`
  - `THIRD_PARTY_NOTICES.md`
  - `site/legal.html`
  - About-Dialog
  - Debian-Paketinhalt
  wurde durchgefuehrt.
