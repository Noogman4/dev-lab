# Radio Visualizer GPU Plan

## Ziel
Den aktuellen Tk-Canvas-Visualizer von der Audioerfassung zu entkoppeln und
spaeter einen fluessigeren GPU-faehigen Renderer anzubinden.

## Aktueller Stand
- Audio-Capture und Pegelberechnung laufen im Radio-Controller.
- Der aktive Renderer ist `Tk Canvas`.
- Ein GPU-Pfad `PySide6 OpenGL` ist im Code vorbereitet, aber noch nicht
  implementiert.

## Geplante Architektur
1. `Capture Worker`
   Liefert fortlaufend Pegel/Frequenzbaender, unabhaengig vom Renderer.
2. `Renderer Backend`
   Zeigt diese Pegel an.
   - `tk_canvas`: aktueller eingebauter CPU-Renderer
   - `pyside_opengl`: spaeterer Sidecar-/Vollbild-Renderer mit GPU
3. `UI Host`
   NetMon/Tk bleibt die Hauptanwendung und steuert Start, Stop, Diagnose und
   Quellenwahl.

## Warum Sidecar statt hartem Embedding
Ein direktes Qt-in-Tk-Embedding ist fehleranfaellig. Fuer einen spaeteren
GPU-Visualizer ist deshalb ein separater Renderer-Fensterpfad sinnvoller:
- eingebettete Vorschau kann bei Tk bleiben
- Vollbild kann spaeter an `PySide6 + QOpenGLWidget` uebergeben werden

## Naechste sinnvolle Schritte
1. Pegeldaten in ein klares Backend-Updateformat kapseln
2. `PySide6` optional als Installer-/Preflight-Komponente aufnehmen
3. ersten Sidecar-Vollbild-Renderer mit `QOpenGLWidget` oder `QQuickWidget`
   aufbauen
4. Vollbild von `Tk Canvas` auf GPU-Backend umschalten
