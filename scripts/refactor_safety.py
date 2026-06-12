#!/usr/bin/env python3
"""
refactor_safety.py — Sicherheitsprüfungen für God-Object-Extraktion in app.py

Verwendung:
  python3 scripts/refactor_safety.py check   <methoden_name>
  python3 scripts/refactor_safety.py status
  python3 scripts/refactor_safety.py proxies  [--delete-safe]

Subkommandos:
  check   <name>   Prüfe ob Methode sicher gelöscht/extrahiert werden kann
  status           Zeige aktuellen Stand (Proxies / echte Logik / Trivial)
  proxies          Liste alle Proxy-Methoden mit Caller-Anzahl
"""

import ast
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
APP_PY = ROOT / "netmon" / "app.py"
FEATURES_DIR = ROOT / "netmon" / "features"


# ---------------------------------------------------------------------------
# AST-Helpers
# ---------------------------------------------------------------------------

def load_app_class():
    src = APP_PY.read_text()
    tree = ast.parse(src)
    cls = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "App")
    return src, cls


def classify_methods(cls):
    """Klassifiziert alle App-Methoden in proxy / empty / real."""
    proxies, empty, real = [], [], []
    for node in cls.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        name = node.name
        body_src = ast.unparse(node)
        lines = node.end_lineno - node.lineno + 1
        stmts = [s for s in node.body
                 if not isinstance(s, ast.Expr) or not isinstance(s.value, ast.Constant)]
        is_proxy = (
            len(stmts) <= 2
            and any("controller" in ast.unparse(s).lower() for s in stmts)
        )
        if is_proxy:
            proxies.append((name, node.lineno, node.end_lineno))
        elif lines <= 3:
            empty.append((name, node.lineno, node.end_lineno))
        else:
            real.append((name, node.lineno, node.end_lineno))
    return proxies, empty, real


# ---------------------------------------------------------------------------
# Caller-Check
# ---------------------------------------------------------------------------

def find_callers(method_name: str) -> list[tuple[str, int, str]]:
    """
    Sucht alle Aufrufer von `method_name` im gesamten Codebase.
    Gibt Liste von (datei, zeile, kontext) zurück.
    Ignoriert die Definitions-Zeile selbst (def method_name).
    """
    pattern = rf"\b{re.escape(method_name)}\s*\("
    callers = []
    for py_file in ROOT.rglob("*.py"):
        if "venv" in py_file.parts or "__pycache__" in py_file.parts:
            continue
        try:
            lines = py_file.read_text().splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, start=1):
            if re.search(pattern, line) and not re.search(rf"^\s*def\s+{re.escape(method_name)}\s*\(", line):
                callers.append((str(py_file.relative_to(ROOT)), i, line.strip()))
    return callers


# ---------------------------------------------------------------------------
# Controller-Gegenstück prüfen
# ---------------------------------------------------------------------------

def find_controller_counterpart(method_name: str) -> list[str]:
    """Sucht ob method_name als freie Funktion in einem Controller existiert."""
    pattern = rf"^def {re.escape(method_name)}\s*\("
    found = []
    for py_file in FEATURES_DIR.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        try:
            lines = py_file.read_text().splitlines()
        except Exception:
            continue
        for line in lines:
            if re.search(pattern, line):
                found.append(str(py_file.relative_to(ROOT)))
    return found


# ---------------------------------------------------------------------------
# Syntax-Verifikation
# ---------------------------------------------------------------------------

def verify_syntax(path: pathlib.Path) -> tuple[bool, str]:
    try:
        ast.parse(path.read_text())
        return True, ""
    except SyntaxError as e:
        return False, f"{e.msg} (Zeile {e.lineno})"


# ---------------------------------------------------------------------------
# Subkommandos
# ---------------------------------------------------------------------------

def cmd_check(method_name: str):
    print(f"\n{'='*55}")
    print(f"Prüfe: {method_name}")
    print(f"{'='*55}")

    _, cls = load_app_class()
    proxies, empty, real = classify_methods(cls)

    proxy_names = {n for n, *_ in proxies}
    empty_names = {n for n, *_ in empty}
    real_names  = {n for n, *_ in real}

    if method_name in proxy_names:
        print("Typ:    Proxy-Methode (delegiert an Controller)")
    elif method_name in empty_names:
        print("Typ:    Triviale/leere Methode")
    elif method_name in real_names:
        print("Typ:    ECHTE LOGIK — erst extrahieren, dann löschen!")
    else:
        print(f"WARNUNG: '{method_name}' nicht in App-Klasse gefunden")
        return

    callers = find_callers(method_name)
    callers_in_app = [c for c in callers if c[0] == "netmon/app.py"]
    callers_outside = [c for c in callers if c[0] != "netmon/app.py"]

    print(f"\nAufrufer außerhalb app.py: {len(callers_outside)}")
    for path, line, ctx in callers_outside[:10]:
        print(f"  {path}:{line}  {ctx[:70]}")
    if len(callers_outside) > 10:
        print(f"  ... +{len(callers_outside)-10} weitere")

    counterparts = find_controller_counterpart(method_name)
    print(f"\nController-Gegenstück: {'JA' if counterparts else 'NEIN'}")
    for c in counterparts:
        print(f"  {c}")

    print()
    if method_name in (proxy_names | empty_names) and not callers_outside:
        print("✓ SICHER ZU LÖSCHEN")
    elif method_name in (proxy_names | empty_names) and callers_outside:
        print(f"! Erst {len(callers_outside)} Aufrufer updaten, dann löschen")
    elif method_name in real_names:
        if counterparts:
            print("→ Controller-Gegenstück existiert bereits — Aufrufer updaten, dann Proxy löschen")
        else:
            print("→ Noch extrahieren: Funktion in Controller kopieren, dann Proxy anlegen")


def cmd_status():
    _, cls = load_app_class()
    proxies, empty, real = classify_methods(cls)

    print(f"\napp.py — aktueller Refactoring-Stand")
    print(f"{'─'*45}")
    proxy_lines = sum(e - s + 1 for _, s, e in proxies)
    empty_lines = sum(e - s + 1 for _, s, e in empty)
    real_lines  = sum(e - s + 1 for _, s, e in real)
    total = len(proxies) + len(empty) + len(real)

    print(f"Proxy-Methoden (löschbar):   {len(proxies):4d}  ({proxy_lines:6d} Zeilen)")
    print(f"Triviale Methoden:           {len(empty):4d}  ({empty_lines:6d} Zeilen)")
    print(f"Echte Logik (extrahieren):   {len(real):4d}  ({real_lines:6d} Zeilen)")
    print(f"{'─'*45}")
    print(f"Gesamt:                      {total:4d}  ({proxy_lines+empty_lines+real_lines:6d} Zeilen)")
    print()
    total_ok = len(proxies) + len(empty)
    pct = 100 * total_ok / total if total else 0
    print(f"Fortschritt (löschbar ohne Extraktion): {total_ok}/{total} = {pct:.0f}%")


def cmd_proxies(delete_safe: bool = False):
    src, cls = load_app_class()
    proxies, _, _ = classify_methods(cls)
    print(f"\n{'Methode':<45} {'Aufrufer außerhalb':>18}  {'Controller'}")
    print("─" * 90)
    safe = []
    for name, start, end in sorted(proxies, key=lambda x: x[0]):
        callers_outside = [c for c in find_callers(name) if c[0] != "netmon/app.py"]
        counterparts = find_controller_counterpart(name)
        marker = "✓" if not callers_outside and counterparts else " "
        print(f"{marker} {name:<44} {len(callers_outside):>18}  {', '.join(counterparts)[:40]}")
        if marker == "✓":
            safe.append(name)
    print(f"\n✓ = sicher löschbar: {len(safe)} von {len(proxies)}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "check" and len(sys.argv) >= 3:
        cmd_check(sys.argv[2])
    elif cmd == "status":
        cmd_status()
    elif cmd == "proxies":
        cmd_proxies("--delete-safe" in sys.argv)
    else:
        print(__doc__)
        sys.exit(1)
