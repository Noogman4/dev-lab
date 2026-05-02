"""Local prompt builder for optional NetMon analysis workflows."""

from __future__ import annotations

import re


class AiAnalysisService:
    def sanitize_content(self, content: str) -> str:
        text = (content or "").strip()
        if not text:
            return ""

        replacements = [
            (
                r"(?i)\b(authorization\s*:\s*bearer)\s+[A-Za-z0-9._~+/=-]+",
                r"\1 [REDACTED]",
            ),
            (
                r"(?i)\b(api[_-]?key|token|secret|password|passwd|pwd)\s*[:=]\s*"
                r"['\"]?[^'\"\s;]+",
                r"\1=[REDACTED]",
            ),
            (
                r"(?i)\b(private[_-]?key|client[_-]?secret|access[_-]?token)\s*[:=]\s*"
                r"['\"]?[^'\"\s;]+",
                r"\1=[REDACTED]",
            ),
            (
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
                "[EMAIL_REDACTED]",
            ),
            (
                r"(?<![A-Za-z0-9])/(home|Users)/[A-Za-z0-9._-]+",
                r"/\1/[USER_REDACTED]",
            ),
            (
                r"(?i)\b(passphrase|psk)\s*[:=]\s*['\"]?[^'\"\s;]+",
                r"\1=[REDACTED]",
            ),
        ]
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text)

        return text

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

Daten:
{content}
""".strip()


__all__ = ["AiAnalysisService"]
