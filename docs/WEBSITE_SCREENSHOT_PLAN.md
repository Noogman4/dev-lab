# NetMon Website Screenshot Plan

## Ziel

Die Website soll nicht nur Icons und Text zeigen, sondern mit wenigen belastbaren Screenshots beweisen, wie NetMon in der Praxis aussieht.

## Grundsatz

- Nicht moeglichst viele Screenshots.
- Lieber 3 bis 5 starke Motive.
- Jeder Screenshot braucht einen klaren Belegwert fuer eine Kernfunktion.

## Empfohlene Motive

### 1. DNS Guard / Resolver-Kontrolle

- Ziel: zeigen, dass NetMon DNS nicht nur nennt, sondern sichtbar bewertet und steuert.
- Inhalt:
  - DNS-Tab
  - DNS Guard Status
  - Resolver-/DoT-Status
  - moeglichst ein sauber lesbarer Ergebnisbereich
- Web-Nutzen: starker technischer Einstieg fuer Netzwerk-/Security-Nutzer.

### 2. Security / Firewall / Monitoring

- Ziel: den Security-Charakter der App belegen.
- Inhalt:
  - Security-Notebook
  - Firewall-/UFW-Status
  - Security-Events oder Guard-Bereich
  - moeglichst mehrere Security-Module im sichtbaren Rahmen
- Web-Nutzen: wichtigster Vertrauens-Screenshot fuer NetMon als Linux-Werkzeug.

### 3. Radio / Detached App / projectM

- Ziel: den eigenstaendigen Charakter der App zeigen.
- Inhalt:
  - Radio-Tab oder geloeste Radio-App
  - aktuelle Station
  - Player-/EQ-Elemente
  - falls stabil: projectM oder Visualizer-Hinweis
- Web-Nutzen: differenziert NetMon klar von reinem Netzwerk-Tooling.

### 4. Diagnose / Supportpaket

- Ziel: zeigen, dass Fehleranalyse und Support praktisch eingebaut sind.
- Inhalt:
  - Support-/Diagnose-Bereich
  - Button oder Export-Hinweis fuer Supportpaket
  - moeglichst klar erkennbare Diagnosefunktion
- Web-Nutzen: wichtig fuer Seriositaet und Wartbarkeit.

### 5. Gesamtansicht / Hauptnavigation

- Ziel: die Tab-Struktur und die Breite des Werkzeugs sichtbar machen.
- Inhalt:
  - Hauptfenster mit sichtbarer Navigation
  - mehrere Haupttabs oder verschachtelte Bereiche erkennbar
- Web-Nutzen: guter Ueberblick fuer Hero-Naehe oder Doku-Einstieg.

## Aufnahme-Regeln

- Desktop-Aufloesung bevorzugen, z. B. 1440x900 oder 1600x900.
- Keine ueberladenen Testdaten oder unlesbaren Logs.
- Wenn moeglich ein konsistentes Theme verwenden.
- Vor Aufnahme stoerende persoenliche Daten, Hostnamen, Tokens oder Pfade ausblenden.
- Lieber wenige, sauber gecroppte Bilder als ganze Monitordumps.

## Dateinamen-Vorschlag

- `netmon-dns-guard.png`
- `netmon-security-overview.png`
- `netmon-radio-detached.png`
- `netmon-support-diagnostics.png`
- `netmon-main-navigation.png`

## Repo-Zielort

Fuer Website-Screenshots:

```text
site/screenshots/
```

## Website-Reihenfolge

1. Hauptnavigation / Gesamtansicht
2. DNS Guard
3. Security
4. Radio
5. Diagnose / Support

## Minimaler erster Satz

Wenn du schnell online gehen willst, reichen zuerst:

- `netmon-security-overview.png`
- `netmon-dns-guard.png`
- `netmon-radio-detached.png`
