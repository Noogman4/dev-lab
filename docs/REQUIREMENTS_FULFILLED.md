# Beantwortung aller geforderten Punkte

## 1. Wie der Vorzustand gespeichert wird

**Ort:** Constructor (`App.__init__`, Zeile ~653) und `internet_disable()` (Zeile 6960)

**Dictionary-Struktur:**
```python
self.internet_suspend_state = {
    "ufw_was_active": False,           # Boolean: check_ufw_active()
    "killswitch_was_active": False,    # Boolean: killswitch_is_on()
    "vpn_was_active": False,           # Boolean: bool(get_wg_iface())
    "vpn_profile": "",                 # String: active_wg_profile() oder ""
    "vpn_interface": "",               # String: get_wg_iface() oder ""
}
```

**Befüllung beim Internet AUS:**
```python
self.internet_suspend_state = {
    "ufw_was_active": self.check_ufw_active(),
    "killswitch_was_active": self.killswitch_is_on(),
    "vpn_was_active": bool(self.get_wg_iface()),
    "vpn_profile": self.active_wg_profile() or "",
    "vpn_interface": self.get_wg_iface() or "",
}
```

**Wiederverwendeter Code:** ✓
- `check_ufw_active()` – UFW Status aus `ufw status`
- `killswitch_is_on()` – Prüft UFW Default Policy
- `get_wg_iface()` – Gibt aktives WireGuard-Interface
- `active_wg_profile()` – Gibt Profil-Name

---

## 2. Reihenfolge bei Internet AUS

### Ablauf:
1. **Vorzustand speichern**
   ```python
   self.internet_suspend_state = {...}
   self.log("Internet AUS: Vorzustand gespeichert.")
   ```

2. **Killswitch kontrolliert deaktivieren**
   ```python
   if self.internet_suspend_state["killswitch_was_active"]:
       self.log("Killswitch vorübergehend deaktiviert.")
       self.killswitch_off(async_mode=False, ensure_sudo=False, refresh_ui=False)
   ```
   - **Wichtig:** Synchron (`async_mode=False`)
   - **Grund:** Muss fertig sein, bevor Netz abgeht
   - **Wiederverwendet:** `killswitch_off()` Methode

3. **Internet systemweit deaktivieren**
   ```python
   rc, out = run_cmd(["sudo", "-n", "nmcli", "networking", "off"], timeout=10)
   if rc == 0:
       self.log("Internet systemweit deaktiviert.")
       return True
   ```

4. **Fehlerbehandlung**
   ```python
   # Falls Schritt 3 fehlschlägt:
   self.internet_suspend_state = {...}  # State invalidieren
   return False                          # Abbruch, Nutzer benachrichtigt
   ```

### Log-Ausgaben:
```
Internet AUS: Vorzustand gespeichert.
Killswitch vorübergehend deaktiviert.
Internet systemweit deaktiviert.
```

---

## 3. Reihenfolge bei Internet AN

### Ablauf:

#### Phase 1: **Netz aktivieren**
```python
rc, out = run_cmd(["sudo", "-n", "nmcli", "networking", "on"], timeout=10)
if rc == 0:
    self.after(0, lambda: self.log("Internet systemweit aktiviert."))
else:
    return False  # Abbruch
```

#### Phase 2: **Netzwerk stabilisieren**
```python
time.sleep(1)  # 1 Sekunde warten auf NetworkManager-Refresh
```
- **Grund:** `get_wg_iface()` muss später valide Werte liefern

#### Phase 3: **VPN für Auto-Fehler**
```python
vpn_restore_ok = False
if self.internet_suspend_state.get("vpn_was_active"):
    profile_to_restore = self.internet_suspend_state.get("vpn_profile", "").strip()
    if profile_to_restore:
        vpn_ok = self.vpn_switch(
            profile_to_restore, ensure_sudo=False, refresh_ui=False
        )
        vpn_restore_ok = vpn_ok
else:
    vpn_restore_ok = True  # War nie aktiv = kein Fehler
```
- **Wiederverwendet:** `vpn_switch()` Methode
- **Logik:** Nur wenn `vpn_was_active` TRUE

#### Phase 4: **Killswitch BEDINGUNGSLOS reaktivieren**
```python
if self.internet_suspend_state.get("killswitch_was_active"):
    if vpn_restore_ok and self.get_wg_iface():
        self.after(0, lambda: self.log("Killswitch wieder aktiviert."))
        self.killswitch_on(async_mode=True, ensure_sudo=False, refresh_ui=False)
    else:
        self.after(0, lambda: self.log(
            "Internet aktiviert, Killswitch bleibt aus, da kein aktiver "
            "VPN-Tunnel wiederhergestellt werden konnte."
        ))
```
- **Wiederverwendet:** `killswitch_on()` Methode
- **Kritische Logik:** NUR wenn `vpn_restore_ok == True` UND `get_wg_iface()` aktiv

#### Phase 5: **Zustandsspeicher leeren**
```python
self.internet_suspend_state = {
    "ufw_was_active": False,
    "killswitch_was_active": False,
    "vpn_was_active": False,
    "vpn_profile": "",
    "vpn_interface": "",
}
self.after(0, self.refresh)
```

### Log-Ausgaben (Normal):
```
Internet systemweit aktiviert.
VPN-Wiederherstellung gestartet (Profil: proton).
VPN erfolgreich wiederhergestellt.
Killswitch wieder aktiviert.
```

---

## 4. Wann wird der Killswitch wieder aktiviert?

### Die Regel:

> **Killswitch wird wieder aktiviert ⟺ (killswitch_was_active ISTFALSE) ∧ (vpn_restore_ok ISTRUE) ∧ (get_wg_iface() ISTDEFINED)**

### Implementation:

```python
if self.internet_suspend_state.get("killswitch_was_active"):
    # Bedingung 1: Killswitch war aktiv
    
    if vpn_restore_ok and self.get_wg_iface():
        # Bedingung 2: VPN erfolgreich wiederhergestellt
        # Bedingung 3: WireGuard-Interface aktiv
        
        self.killswitch_on(async_mode=True, ensure_sudo=False, refresh_ui=False)
```

### Nicht reaktiviert wenn:
- ❌ Killswitch war nie aktiv
- ❌ VPN-Reconnect fehlgeschlagen
- ❌ `get_wg_iface()` gibt `None` zurück (WG nicht aktiv)
- ❌ Kombination der obigen

### Schutzbegründung:
- Wenn `get_wg_iface() == None` → WireGuard läuft NICHT
- Killswitch aktiviert + kein VPN = sofortiger Traffic-Block
- Deshalb: Erst prüfen, dann aktivieren

---

## 5. Was passiert, wenn VPN nicht wiederhergestellt werden kann?

### Szenario: `vpn_switch(profile)` gibt `False` zurück

```python
vpn_ok = self.vpn_switch("proton", ensure_sudo=False, refresh_ui=False)
if vpn_ok:
    vpn_restore_ok = True
    self.after(0, lambda: self.log("VPN erfolgreich wiederhergestellt."))
else:
    self.after(0, lambda: self.log("VPN-Wiederherstellung fehlgeschlagen."))
    # vpn_restore_ok bleibt False
```

### Konsequenzen:

1. **Killswitch bleibt deaktiviert**
   ```python
   if vpn_restore_ok and self.get_wg_iface():
       # Diese Bedingung ist jetzt FALSE
       self.killswitch_on(...)  # Wird NICHT aufgerufen
   else:
       self.log("Internet aktiviert, Killswitch bleibt aus...")
   ```

2. **Internet ist aber AKTIV**
   - `nmcli networking on` war erfolgreich
   - Nutzer hat normalen Internetzugang
   - Nur ohne VPN-Schutz

3. **Klare Meldung**
   ```
   VPN-Wiederherstellung gestartet (Profil: proton).
   VPN-Wiederherstellung fehlgeschlagen.
   Internet aktiviert, Killswitch bleibt aus, da kein aktiver VPN-Tunnel 
   wiederhergestellt werden konnte.
   ```

### Nutzer-Handlung:
- Sieht die Meldung
- Kann VPN manuell aktivieren
- Oder Internet weiter ohne VPN nutzen
- **Nicht ausgesperrt!**

---

## 6. Wie verhindert wird, dass Nutzer nach Internet AN ausgesperrt bleibt

### Problem (ohne diese Lösung):
```
1. Netzwerk an (nmcli on)
2. VPN-Reconnect versucht, fehlgeschlagen
3. Killswitch AUTOMATISCH wieder aktiviert
4. Nutzer: "Netz an, aber kein Traffic!" → Ausgesperrt
```

### Lösung in 5 Ebenen:

#### Ebene 1: **Killswitch ist nur für "VPN-Ready"-Systeme**
```
Killswitch AN + kein VPN = Traffic blockiert
→ Das ist per Design so, nicht-Test
```

#### Ebene 2: **Internet AUS deaktiviert Killswitch ZUERST**
```python
# BEVOR nmcli networking off:
self.killswitch_off(async_mode=False, ...)
# Dann networking off
```
- **Verhindert:** Netz kommt wieder online, Killswitch ist noch an

#### Ebene 3: **Internet AN wartet vor VPN-Versuch abwarten**
```python
time.sleep(1)  # Netzwerk stabilisieren
# DANN vpn_switch versuchen
```
- **Verhindert:** Race-condition zwischen `networking on` und VPN-Reconnect

#### Ebene 4: **Killswitch VERIFI nachdem VPN aktiv ist**
```python
vpn_ok = self.vpn_switch(profile, ...)
if vpn_ok:
    if self.get_wg_iface():  # Prüfung nach Aktivierung!
        killswitch_on()
```
- **Nicht blind reaktivieren nach Versuch**
- **Sondern nach Beweis** via `get_wg_iface()` != None

#### Ebene 5: **Killswitch bleibt EXPLIZIT aus bei Fehler**
```python
if vpn_restore_ok and self.get_wg_iface():
    killswitch_on()
else:
    # VPN fehlgeschlagen
    → Killswitch bleibt DEAKTIVIERT
    → Log: "...Killswitch bleibt aus..."
```

### Das Ergebnis:
- ✓ Internet funktioniert
- ✓ Nutzer sieht warum (Log)
- ✓ Nicht ausgesperrt
- ✓ Kann VPN manuell später aktivieren

---

## 7. Welche bestehenden Methoden wiederverwendet wurden

### UFW/Killswitch-Methoden:

| Was | Methode | Zeile | Zweck |
|-----|---------|-------|-------|
| UFW Status | `check_ufw_active()` | 7330 | Prüfe ob Firewall aktiv |
| Killswitch Status | `killswitch_is_on()` | 7376 | Prüfe ob Killswitch aktiv |
| Killswitch AN | `killswitch_on()` | 7992 | Aktiviere Killswitch |
| Killswitch AUS | `killswitch_off()` | 8066 | Deaktiviere Killswitch |

### VPN-Methoden:

| Was | Methode | Zeile | Zweck |
|-----|---------|-------|-------|
| VPN aktivieren | `vpn_switch()` | 7809 | Aktiviere ein Profil |
| VPN deofault Profil | `active_wg_profile()` | 6911 | Welches Profil ist aktiv |
| WG-Interface | `get_wg_iface()` | 6921 | Welches WG-Interface ist aktiv |

### Keine Duplikation:
- ❌ **NICHT** neu implementiert: UFW-Rules, Killswitch-Rules, VPN-Start-Logik
- ✓ **Delegiert an:** Bestehende, getestete Methoden
- ✓ **Vorteil:** Single Source of Truth, minimale Fehlerquellen

### Beispiel Killswitch-Deaktivierung:
```python
# NICHT so:
# run_cmd(["sudo", "-n", "ufw", "default", "allow", "outgoing"], ...)
# (Reimplementierung von killswitch_off Logik)

# SONDERN so:
self.killswitch_off(async_mode=False, ensure_sudo=False, refresh_ui=False)
# (Bestehende Methode nutzen)
```

---

## Summary

### Geforderte Punkte – Alle erfüllt:

| Punkt | Status | Details |
|-------|--------|---------|
| 1. Vorzustand speichern | ✓ | `internet_suspend_state` dict, befüllt mit `check_ufw_active()`, `killswitch_is_on()`, etc. |
| 2. Internet AUS Reihenfolge | ✓ | Speichern → Killswitch aus → Netz aus (synchron) |
| 3. Internet AN Reihenfolge | ✓ | Aktivieren → Warten → VPN → Killswitch (mit Verifizierung) |
| 4. Killswitch-Reaktivierung | ✓ | Nur wenn `vpn_was_active=True` UND `vpn_restore_ok=True` UND `get_wg_iface()` |
| 5. VPN-Fehler | ✓ | Killswitch bleibt aus, Nutzer hat Internet |
| 6. Schutz vor Sperrung | ✓ | 5-Ebenen Architektur, Verifizierung statt Blind-Aktivierung |
| 7. Methoden-Reuse | ✓ | `check_ufw_active()`, `killswitch_on/off()`, `vpn_switch()`, `active_wg_profile()`, `get_wg_iface()` |

### Code-Qualität:
- ✓ Python 3.11 Syntax OK
- ✓ Black formatiert
- ✓ Ruff passed
- ✓ Keine bestehenden Tests gebrochen

### Dokumentation:
- ✓ Inline-Kommentare im Code
- ✓ Docstring in `_internet_on_sync()`
- ✓ Ausführliches Design-Doc: [docs/NETMON_INTERNET_ON_OFF_REFACTORING.md](docs/NETMON_INTERNET_ON_OFF_REFACTORING.md)
- ✓ Summary: [docs/INTERNET_ONOFF_SUMMARY.md](docs/INTERNET_ONOFF_SUMMARY.md)

