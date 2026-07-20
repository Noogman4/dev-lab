# NetMon Performance Baseline

## Stand

- Datum: 2026-07-20T22:36:00+02:00
- Branch: `refactor/safe-stepwise-20260720-222422`
- Commit: `204e6daa refactor: separate support bundle file selection`
- NetMon-Version: `1.1.20`
- Python: `.venv/bin/python`, `Python 3.12.3`
- Betriebssystem: `Linux proglab 7.0.0-28-generic #28~24.04.1-Ubuntu SMP PREEMPT_DYNAMIC Wed Jul  1 15:50:57 UTC 2 x86_64`
- Messuhr: `time.perf_counter()`

## Messbedingungen

- Keine Codeaenderung vor dieser Baseline.
- GUI-Startmessung per `bash scripts/run_netmon_gui_smoke.sh` ausserhalb der Sandbox, weil Tk/xvfb innerhalb der Sandbox schon als instabil dokumentiert ist.
- Funktionsmessungen liefen in der Sandbox.
- Wiederholte Messungen wurden nur fuer ungefaehrliche Operationen ausgefuehrt.
- Keine realen Root-Aktionen, keine Paketinstallationen, keine sicherheitskritischen Systemaenderungen.

## Gestartete Bereiche

- Headless-GUI-Smoke mit bestehenden Smoke-Patches.
- Core-Pfadhelfer aus `netmon.core.state`.
- Support-Bundle-Dateiauswahl und Manifestbau.
- Kleine Core-Testgruppe und fokussierter Ruff-Check.

## Ergebnisse

| Bereich | Operation | Runs | Median |
| --- | --- | ---: | ---: |
| startup | `headless_gui_smoke_startup` | 3 | 4925.237 ms |
| core | `state_path_helpers` | 10 | 0.069 ms |
| diagnostics | `support_bundle_inputs` | 10 | 0.643 ms |
| diagnostics | `support_manifest_build` | 10 | 0.112 ms |
| tests | `pytest_core_perf_seed` | 3 | 188.424 ms |
| tests | `ruff_check` | 3 | 21.081 ms |

## Bekannte Hintergrundprozesse

- Headless-GUI-Smoke nutzt `xvfb-run`.
- NetMon GUI-Smoke meldet DNS-Statusaktualisierung und Radio-Theme-Diagnostik im Startauszug.
- Die Smoke-Patches deaktivieren bekannte schwere Startup-Aktionen.

## Messabweichungen

- GUI-Smoke enthält Prozessstart, xvfb-Start, Python-Importe, App-Aufbau und Shutdown. Er ist daher eine Start-Surrogatmessung, keine reine Tab-Aufbaumessung.
- `support_manifest_build` zeigt einen ersten Aufruf mit 2.991 ms und danach Werte um 0.1 ms; Median ist deshalb aussagekraeftiger als Mittelwert.
- Sehr kurze Operationen unter 1 ms sind empfindlich gegen Scheduler- und I/O-Rauschen.

## Bewertung

- Auffaelligster Wert ist der Headless-GUI-Smoke mit Median 4925.237 ms. Das ist fuer vollstaendigen Prozess- und GUI-Aufbau plausibel, aber als Start-Baseline relevant.
- Die bereits refaktorierten Core-Helfer liegen im Sub-Millisekundenbereich.
- Keine Optimierung wurde vorgenommen; diese Baseline dient nur dem Vergleich fuer kommende Bereiche.
