"""Local prompt builder for optional NetMon analysis workflows."""

from __future__ import annotations

try:
    from netmon.core.log_redaction import redact_sensitive_text
except ModuleNotFoundError:  # pragma: no cover - legacy flat import layout
    from core.log_redaction import redact_sensitive_text

CHAD_COMMAND_GUIDANCE = """
Terminalbefehle Schritt für Schritt darstellen:
- Pro Schritt: zuerst Empfehlung und Zweck kurz erklären, dann den zugehörigen
  Terminalbefehl in einem eigenen Markdown-Codeblock mit Sprache bash zeigen,
  danach die Abarbeitung und Prüfung erklären: erwartetes Ergebnis und nächster Schritt.
- Genau einen zusammengehörigen Terminalbefehl pro Codeblock. Unabhängige Befehle
  niemals in einem Sammelblock oder mit Semikolon/&& zusammenfassen. Auch einen
  zusätzlichen Prüfbefehl in einem eigenen Codeblock mit Erklärung davor zeigen.
- In kopierbare Blöcke gehören nur Befehle, keine Shell-Prompts wie $ oder #,
  keine Erläuterungen, Kommentare oder Beispielausgaben. Erklärungen stehen außerhalb.
- Zusammengehörige Pipelines, Zeilenfortsetzungen, Schleifen und Here-Dokumente
  bleiben als ein vollständiger Befehl erhalten; niemals mechanisch pro Zeile trennen.
- Keine abschließende Zusammenfassung aller Befehle und kein Gesamtskript.
- Zuerst prüfen; notwendige Änderungen mit Wirkung und Risiken vorher erklären.
  Keine erfolgreiche Ausführung behaupten, bevor das Ergebnis vorliegt.
- Hängt der weitere Ablauf von einer noch unbekannten Ausgabe ab, nur den nächsten
  sinnvollen Prüfschritt zeigen und den Nutzer danach um das Ergebnis bitten.
""".strip()


class AiAnalysisService:
    def sanitize_content(self, content: str) -> str:
        """Redact text bound for an external AI with NetMon's shared filter.

        One redaction contract for logs, diagnostics and AI prompts: the
        shared filter covers option/value pairs, Basic/Bearer authorization,
        cookies, PEM keys, provider tokens, URL credentials, WireGuard keys,
        e-mail addresses and home directory names.
        """
        text = (content or "").strip()
        if not text:
            return ""
        return redact_sensitive_text(text).strip()

    def build_prompt(self, title: str, content: str) -> str:
        content = self.sanitize_content(content)

        if not content:
            return f"{title}: Keine Daten vorhanden."

        focus = ""
        if "security" in (title or "").lower():
            focus = """
Fokus:
- Sind die Events harmlos, auffällig oder kritisch?
- Gibt es Hinweise auf Portscan oder echte Angriffe?
- Welche Einträge sind normale Firewall-Hintergrundgeräusche?
- Welche konkreten nächsten Schritte sind sinnvoll?
""".strip()
        elif "dns" in (title or "").lower():
            focus = """
Fokus:
- Wenn VPN aktiv ist, ist VPN-DNS zu bevorzugen.
- Globales DNS-over-TLS mit Cloudflare/Google/Quad9 kann VPN-DNS überschreiben und DNS-Leaks verursachen.
- DNSSEC=allow-downgrade ist bei VPN oft sinnvoller als strict.
- Bewerte DoT und DNSSEC nicht pauschal als besser, sondern berücksichtige den VPN-Kontext.
- Wenn Leak erkannt: NEIN und ausschließlich VPN-DNS gelistet ist, bewerte das Risiko als niedrig.
- "mittel" ist nur korrekt, wenn mehrere DNS-Quellen oder öffentliche Resolver zusätzlich vorhanden sind.
""".strip()
        elif "startup guard" in (title or "").lower():
            focus = """
Fokus:
- Bewerte neue/geänderte Autostart- oder systemd-Einträge vorsichtig.
- Behaupte nicht, dass etwas Malware ist.
- Erkläre, was der Eintrag vermutlich macht.
- Achte auf verdächtige Pfade wie /tmp, /dev/shm, versteckte Dateien oder unbekannte Skripte.
- Gib konkrete Prüfschritte an.
""".strip()
        elif "path guard" in (title or "").lower():
            focus = """
Fokus:
- Prüfe PATH-Manipulationen vorsichtig.
- Erkläre, ob PATH-Einträge gefährlich, ungewöhnlich oder normal sind.
- Achte besonders auf /tmp, /var/tmp, /dev/shm, '.', $PWD und PATH-Erweiterungen in Shell-Profilen.
- Behaupte nicht, dass Malware sicher vorhanden ist.
- Gib konkrete sichere Prüfschritte.
""".strip()

        focus_block = f"\n\n{focus}" if focus else ""

        return f"""
Du bist ein Analyse-Assistent für NetMon.

Analysiere die folgenden Daten verständlich für einen Linux-Nutzer.
{focus_block}

Bitte liefere:
1. Kurzbewertung
2. Auffälligkeiten
3. Risiko (niedrig/mittel/hoch)
4. Konkrete nächste Schritte

{CHAD_COMMAND_GUIDANCE}

Daten:
{content}
""".strip()


__all__ = ["AiAnalysisService"]
