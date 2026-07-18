# NetMon – Internet AN/AUS Refactoring

## Überblick

Die Buttons **Internet AUS** und **Internet AN** wurden grundlegend überarbeitet, um sauber mit der bestehenden UFW-/Killswitch-/VPN-Logik zusammenzuspielen. Das System speichert nun den Zustand vor dem Abschalten und versucht, diesen intelligent wiederherzustellen.

---

## 1. Vorzustand-Speicherung

### Initialisierung (Constructor)

```python
self.internet_suspend_state = {
    "ufw_was_active": False,           # War UFW aktiv?
    "killswitch_was_active": False,    # War Killswitch aktiv?
    "vpn_was_active": False,           # War ein VPN aktiv?
    "vpn_profile": "",                 # Profil-Name (z.B. "proton", "ch")
    "vpn_interface": "",               # WireGuard Interface (z.B. "wg0")
}
```

**Ort:** Constructor (__init__) nach dem Privacy-Config-Setup (Zeile ~653)

### Speicherlogik in `internet_disable()`

Beim Klick auf **Internet AUS** wird der aktuelle Zustand so abgefragt:

```python
self.internet_suspend_state = {
    "ufw_was_active": self.check_ufw_active(),      # UFW Status abfragen
    "killswitch_was_active": self.killswitch_is_on(), # Killswitch Status
    "vpn_was_active": bool(self.get_wg_iface()),    # Aktive WG-Interfaces?
    "vpn_profile": self.active_wg_profile() or "",  # Aktuelles VPN-Profil
    "vpn_interface": self.get_wg_iface() or "",     # Aktuelles Interface
}
```

**Methoden-Reuse:**
- `check_ufw_active()` – Prüft UFW-Status via `ufw status`
- `killswitch_is_on()` – Prüft UFW Default Policy (deny outgoing = Killswitch an)
- `active_wg_profile()` – Gibt Profil-Namen zurück
- `get_wg_iface()` – Gibt aktives WireGuard-Interface zurück

---

## 2. Internet AUS – Reihenfolge & Logik

### A. Vorzustand speichern
```python
self.log("Internet AUS: Vorzustand gespeichert.")
```
Der Zustand wird wie oben beschrieben erfasst.

### B. Killswitch kontrolliert deaktivieren
Falls der Killswitch aktiv war:
```python
if self.internet_suspend_state["killswitch_was_active"]:
    self.log("Killswitch vorübergehend deaktiviert.")
    self.killswitch_off(async_mode=False, ensure_sudo=False, refresh_ui=False)
```

**Wichtig:**
- Der Killswitch wird **synchron** deaktiviert (`async_mode=False`)
- Das geschieht **BEVOR** das Netzwerk abgeschaltet wird
- `ensure_sudo=False`, da `internet_disable()` bereits `ensure_sudo_session()` aufgerufen hat
- `refresh_ui=False`, um UI-Refresh zu sparen

**Grund:** 
Wenn der Killswitch noch aktiv ist, wenn das Netz wieder kommt, blockiert er den Traffic sofort. Deshalb muss er zuerst weg.

### C. Internet systemweit deaktivieren
```python
rc, out = run_cmd(["sudo", "-n", "nmcli", "networking", "off"], timeout=10)
if rc == 0:
    self.log("Internet systemweit deaktiviert.")
    return True
```

### D. Fehlerbehandlung
Falls `nmcli networking off` fehlschlägt:
- Fehler-Log wird ausgegeben
- MessageBox zeigt Fehler an
- **Zustandsspeicher wird invalidiert** (auf Defaults zurückgesetzt), damit Auto-Restore nicht versucht wird

```python
if rc != 0:
    # Zustand löschen -> kein Auto-Restore bei nächstem AN
    self.internet_suspend_state = {
        "ufw_was_active": False,
        "killswitch_was_active": False,
        "vpn_was_active": False,
        "vpn_profile": "",
        "vpn_interface": "",
    }
    return False
```

---

## 3. Internet AN – Reihenfolge & Logik

### Methoden-Struktur

- `internet_enable()` – Öffentliche/UI-Methode, delegiert async an `_internet_on_sync()`
- `_internet_on_sync()` – Synchrone Implementierung mit komplexer Logik

Diese Trennung erlaubt:
- Nicht im UI zu blocken (async via `self.run_async()`)
- Aber saubere synchrone Kontrolllogik ohne Race-Conditions

### A. Internet systemweit aktivieren
```python
rc, out = run_cmd(["sudo", "-n", "nmcli", "networking", "on"], timeout=10)
if rc == 0:
    self.after(0, lambda: self.log("Internet systemweit aktiviert."))
else:
    # Fehler behandelt, Return
    return False
```

### B. Kurz warten für Netzwerk-Refresh
```python
time.sleep(1)  # 1 Sekunde warten, damit Interfaces/Verbindungen wieder hochkommen
```

Diese Pause ist notwendig, damit:
- NetworkManager Zeit hat, Interfaces zu reaktivieren
- `get_wg_iface()` und andere Status-Abfragen später valide Werte liefern

### C. VPN nur dann auto-wiederherstellen, wenn es vorher aktiv war

```python
vpn_restore_ok = False
if self.internet_suspend_state.get("vpn_was_active"):
    profile_to_restore = self.internet_suspend_state.get("vpn_profile", "").strip()
    
    if profile_to_restore:
        self.after(0, lambda: self.log(
            f"VPN-Wiederherstellung gestartet (Profil: {profile_to_restore})."
        ))
        
        # vpn_switch() mit ensure_sudo=False (bereits checked)
        vpn_ok = self.vpn_switch(
            profile_to_restore, 
            ensure_sudo=False, 
            refresh_ui=False
        )
        
        if vpn_ok:
            vpn_restore_ok = True
            self.after(0, lambda: self.log("VPN erfolgreich wiederhergestellt."))
        else:
            self.after(0, lambda: self.log("VPN-Wiederherstellung fehlgeschlagen."))
else:
    # VPN war nicht aktiv -> nicht wieder aktivieren
    vpn_restore_ok = True  # Kein Fehler
```

**Methoden-Reuse:**
- `vpn_switch(profile_name, ensure_sudo, refresh_ui)` – Existierende VPN-Aktivierungsmethode

**Logik:**
- Nutzer hatte VPN an? → Versuch, das gleiche Profil wieder zu aktivieren
- Nutzer hatte VPN aus? → Nicht automatisch einschalten
- `vpn_restore_ok` wird `True` gesetzt, wenn VPN erfolgreich ist ODER gar nicht aktiv war

---

## 4. Killswitch – Wann wird er wieder aktiviert?

### Die kritische Regel

> **Der Killswitch wird NUR reaktiviert, wenn BEIDE Bedingungen erfüllt sind:**
> 1. Er war vor `Internet AUS` aktiv (`killswitch_was_active == True`)
> 2. Nach `Internet AN` ist ein VPN-Tunnel wirklich aktiv (`get_wg_iface()` ist nicht None)

### Implementierung

```python
if self.internet_suspend_state.get("killswitch_was_active"):
    if vpn_restore_ok and self.get_wg_iface():
        # Beide Bedingungen erfüllt -> Killswitch wieder an
        self.after(0, lambda: self.log("Killswitch wieder aktiviert."))
        self.killswitch_on(
            async_mode=True,      # Async, nicht blockierend
            ensure_sudo=False,    # Bereits geprüft
            refresh_ui=False      # Manueller Refresh am Ende
        )
    else:
        # VPN-Reconnect fehlgeschlagen -> Killswitch bleibt aus
        self.after(0, lambda: self.log(
            "Internet aktiviert, Killswitch bleibt aus, da kein aktiver "
            "VPN-Tunnel wiederhergestellt werden konnte."
        ))
```

**Methoden-Reuse:**
- `killswitch_on(async_mode, ensure_sudo, refresh_ui)` – Existierende Killswitch-Aktivierung

---

## 5. VPN-Rekonstruktion fehlgeschlagen – Was passiert?

### Szenario: `vpn_switch()` gibt `False` zurück

```
1. Internet AN wird geklickt
2. nmcli networking on erfolgreich
3. VPN-Wiederherstellung gestartet
4. VPN-Profil konnte nicht aktiv werden
   ↓
   vpn_ok = False
   vpn_restore_ok bleibt False
   ↓
5. Killswitch-Reaktivierung übersprungen
   ↓
6. Nutzer hat dennoch Internetzugang
```

### Log-Ausgaben

```
Internet systemweit aktiviert.
VPN-Wiederherstellung gestartet (Profil: proton).
VPN-Wiederherstellung fehlgeschlagen.
Internet aktiviert, Killswitch bleibt aus, da kein aktiver VPN-Tunnel wiederhergestellt werden konnte.
```

### Benutzer bleibt nicht ausgesperrt

Der Nutzer hat normalen Internetzugang, weil:
- Netzwerk ist an
- Killswitch bleibt deaktiviert
- UFW bleibt in seinem bisherigen Zustand

Der Nutzer kann dann manuell VPN wieder aktivieren, wenn gewünscht.

---

## 6. Architektur – Wie wird der Nutzer nicht ausgesperrt?

Die Schutzlogik besteht aus mehreren Ebenen:

### 1. **Killswitch ist ein „Kill"-Schalter für leicht reachable VPN**
   - Ohne VPN? → Killswitch muss aus sein, sonst blockiert er Internet

### 2. **Internet AUS deaktiviert Killswitch ZUERST**
   - Dann Netz ab → keine Zeit für "Netz an + Killswitch noch aktiv = blockiert"

### 3. **Internet AN reaktiviert Killswitch nur, wenn VPN wirklich aktiv ist**
   - Nicht nach dem Versuch, sondern nach der Verifizierung
   - `get_wg_iface()` ist der Proof, dass WireGuard läuft

### 4. **Fehlgeschlagener VPN-Reconnect → Killswitch bleibt aus**
   - Expliziter Log: `"...Killswitch bleibt aus, da kein aktiver VPN-Tunnel wiederhergestellt werden konnte."`
   - Nutzer sieht die Meldung und weiß, warum er noch Netz hat

### 5. **Zustandsreset nach erfolgreicher Wiederherstellung**
   - Nach `Internet AN` wird `internet_suspend_state` gelösch, damit keine Altdaten hängen bleiben

---

## 7. UFW-Behandlung

### Vorzustand wird NICHT blind zerstört

```python
# UFW-Zustand: merken, nicht blind zerstören
# Der Killswitch remanagt UFW intern. Wenn Killswitch wieder an ist, wird
# UFW gerade durch killswitch_on() rekonfiguriert.
# Falls Killswitch nicht wieder angeht, bleibt UFW im bestehenden Zustand.
```

**Logik:**
- Wenn Killswitch wieder aktiviert wird → `killswitch_on()` remanagt UFW-Rules
- Wenn Killswitch ausbleibt → UFW bleibt in seinem Zustand (wahrscheinlich `allow outgoing` nach `killswitch_off()`)

---

## 8. Bestehende Methoden – Wiederverwendung

### Abgestimmte Methoden-Nutzung

| Funktion | Genutzte Methode | Quelle |
|----------|------------------|--------|
| UFW-Status abfragen | `check_ufw_active()` | Zeile 7330 |
| Killswitch-Status | `killswitch_is_on()` | Zeile 7376 |
| Killswitch an | `killswitch_on()` | Zeile 7992 |
| Killswitch aus | `killswitch_off()` | Zeile 8066 |
| VPN aktivieren | `vpn_switch(target)` | Zeile 7809 |
| VPN-Profil erfragen | `active_wg_profile()` | Zeile 6911 |
| VPN-Interface erfragen | `get_wg_iface()` | Zeile 6921 |

### Keine Duplikation
- Firewall-Logik delegiert an `fw_enable()` / `fw_disable()`
- Killswitch-Logik delegiert an `killswitch_on()` / `killswitch_off()`
- VPN-Logik delegiert an `vpn_switch()` / `vpn_off()`
- Keine Duplizierung von Shell-Commands oder UFW-Rules

---

## 9. Fehlerbehandlung Summary

### Internet AUS fehlgeschlagen
```
✗ nmcli networking off schlägt fehl
→ Internet-Zustand wird invalidiert
→ Kein Auto-Restore beim nächsten AN
→ Nutzer wird benachrichtigt (MessageBox + Log)
```

### Internet AN fehlgeschlagen
```
✗ nmcli networking on schlägt fehl
→ Prozess abbricht
→ Nutzer wird benachrichtigt
→ internet_suspend_state bleibt wie ist (für evtl. nächster Versuch)
```

### VPN-Reconnect fehlgeschlagen
```
✓ nmcli networking on erfolgreich
✗ vpn_switch() gibt False zurück
→ Killswitch bleibt aus
→ Nutzer hat Internet, aber ohne VPN/Killswitch
→ Expliziter Log über warum
```

### Killswitch-Reaktivierung fehlgeschlagen
```
✓ nmcli networking on erfolgreich
✓ vpn_switch() erfolgreich
✗ killswitch_on() fehlgeschlagen
→ Nutzer hat Internet + VPN, aber Killswitch möglicherweise nicht richtig an
→ Log zeigt das an, Nutzer kann manuell überprüfen
```

---

## 10. Use Case Beispiele

### Szenario 1: Standard – Killswitch + VPN
```
Vorzustand:
  - UFW: aktiv
  - Killswitch: AN
  - VPN: aktiv (proton)

Internet AUS:
  1. Zustand speichern
  2. killswitch_off() (synchron)
  3. nmcli networking off
  
Logs: 
  Internet AUS: Vorzustand gespeichert.
  Killswitch vorübergehend deaktiviert.
  Internet systemweit deaktiviert.

Internet AN:
  1. nmcli networking on
  2. sleep(1)
  3. vpn_switch("proton")
  4. killswitch_on() (async)
  5. Zustand leeren

Logs:
  Internet systemweit aktiviert.
  VPN-Wiederherstellung gestartet (Profil: proton).
  VPN erfolgreich wiederhergestellt.
  Killswitch wieder aktiviert.
```

### Szenario 2: Nur Firewall, kein VPN/Killswitch
```
Vorzustand:
  - UFW: aktiv
  - Killswitch: AUS
  - VPN: inaktiv

Internet AUS:
  1. Zustand speichern (alles False)
  2. (Killswitch bleibt aus, war ja nicht an)
  3. nmcli networking off

Logs:
  Internet AUS: Vorzustand gespeichert.
  Internet systemweit deaktiviert.

Internet AN:
  1. nmcli networking on
  2. sleep(1)
  3. (VPN nicht aktivieren, war nicht an)
  4. (Killswitch nicht aktivieren, war nicht an)
  5. Zustand leeren

Logs:
  Internet systemweit aktiviert.
```

### Szenario 3: VPN-Reconnect fehlgeschlagen
```
Vorzustand:
  - UFW: aktiv
  - Killswitch: AN
  - VPN: aktiv (ch)

Internet AUS:
  → Zustand gespeichert, Killswitch aus, Netz ab

Internet AN:
  1. nmcli networking on ✓
  2. sleep(1)
  3. vpn_switch("ch") ✗ FEHLGESCHLAGEN
     (z.B. Netzwerk zu schlecht für Tunnel-Aufbau)
  4. Killswitch bleibt AUS (weil VPN nicht aktiv)
  5. Zustand leeren

Logs:
  Internet systemweit aktiviert.
  VPN-Wiederherstellung gestartet (Profil: ch).
  VPN-Wiederherstellung fehlgeschlagen.
  Internet aktiviert, Killswitch bleibt aus, da kein aktiver VPN-Tunnel 
  wiederhergestellt werden konnte.

Nutzer hat Internetzugang, aber ohne VPN-Schutz.
```

---

## 11. Code-Einträge

### Neue Methoden
- **`_internet_on_sync()`** – Zeile 6977
  - Private Methode mit komplexer Zustandswiederherstellung
  - Dokumentiert in docstring

### Modifizierte Methoden
- **`internet_disable()`** – Zeile 6940
  - Vorzustand-Speicherung
  - Killswitch-Deaktivierung
  - Fehlerbehandlung mit State-Reset

- **`internet_enable()`** – Zeile 6994
  - Delegiert an `_internet_on_sync()` via `self.run_async()`
  - Bleibt return-schnell, um nicht zu blocken

### Constructor-Änderung
- **`App.__init__()`** – Zeile ~653
  - `self.internet_suspend_state` Initialisierung

---

## 12. Testing & Validierung

### Code-Qualität
✓ Python Syntax valide  
✓ Black formatted (line-length=88)  
✓ Ruff checks erfolgreich  

### Bestehende Tests
- 52/57 Tests bestehen
- 5 Tests schlagen fehl (pre-existing in `vpn_switch()` und `delete_selected_vpn_profile()`)
- Keine Tests für `internet_disable()`/`internet_enable()` existierten vorher

---

## 13. Zusammenfassung

Die Umsetzung folgt dem Prinzip der **definierten Zustandslogik**:

1. **Speichern** – Vorzustand vor Abschalten erfassen
2. **Demontieren** – Killswitch zuerst aus (verhindert Blockade)
3. **Abschalten** – Netz jetzt sicher aus
4. **Aktivieren** – Netz wieder an
5. **Wiederaufbau** – VPN wenn nötig, Killswitch wenn sicher
6. **Verifikation** – Nur reaktivieren wenn bewährt
7. **Reset** – Zustand leeren nach erfolgreicher Wiederherstellung

**Sicherheit:** Der Nutzer kann nach `Internet AN` nicht in einem blockierten Zustand steckenbleiben, weil der Killswitch nur reaktiviert wird, wenn der VPN-Tunnel wirklich läuft.

