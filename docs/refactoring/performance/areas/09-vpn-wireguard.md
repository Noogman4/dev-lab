# 09 VPN und WireGuard Performance

## Messbedingungen

- Bereich: `netmon/features/vpn_controller.py`
- Commit vorher: `3d4b232e`
- Operation: direkter Aufruf von `internal_ipv4_profile_candidates`
- Messuhr: `time.perf_counter()`
- Langes Profil, kurzes Profil und leerer Wert
- 100 Wiederholungen pro Operation
- Keine WireGuard-Profile gelesen, geschrieben, gestartet oder geloescht
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Median |
| --- | ---: |
| `vpn_internal_ipv4_profile_candidates` | 0.003 ms |

## Ergebnisse Nachher

| Operation | Median |
| --- | ---: |
| `vpn_internal_ipv4_profile_candidates` | 0.004 ms |

## Bewertung

- Die Kandidatenbildung bleibt deutlich unter 1 ms.
- Die Differenz von 0.001 ms liegt im Messrauschen.
- Keine Datei-, Netzwerk-, Root- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waeren spaeter echte Profil-I/O- und `wg`-Aufrufe, die in diesem Schritt bewusst nicht beruehrt wurden.

## Aussagekraft

- Die Messung prueft reine Namenslogik mit synthetischen Profilwerten.
- Reale VPN-Laufzeit haengt von WireGuard, NetworkManager, UFW und Dateisystemzugriffen ab.
