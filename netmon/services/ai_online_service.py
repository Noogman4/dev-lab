"""Optional OpenAI API client for NetMon's Chad analysis tab."""

from __future__ import annotations

import base64
import mimetypes
import os
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

from .ai_analysis_service import CHAD_COMMAND_GUIDANCE

try:
    import requests
except Exception:  # pragma: no cover - depends on optional runtime dependency.
    requests = None


class AiOnlineService:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        self.default_model = "gpt-4.1-mini"
        self.last_usage = {}
        self.last_usage_text = ""
        self.last_response_incomplete = False

    def is_available(self):
        return bool(self.api_key)

    def image_to_data_url(self, path: str) -> str:
        resolved = Path(path).expanduser().resolve(strict=True)
        allowed_suffixes = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
        if resolved.suffix.lower() not in allowed_suffixes:
            raise ValueError("Unsupported image file type.")

        home_dir = Path.home().resolve()
        try:
            resolved.relative_to(home_dir)
        except ValueError as exc:
            raise ValueError(
                "Image path must be inside the user home directory."
            ) from exc

        mime, _ = mimetypes.guess_type(str(resolved))
        if not mime:
            mime = "image/png"

        with open(resolved, "rb") as f:
            data = base64.b64encode(f.read()).decode("ascii")

        return f"data:{mime};base64,{data}"

    def _post_json(self, url: str, headers: dict, payload: dict, timeout: int):
        if requests is not None:
            response = requests.post(
                url, headers=headers, json=payload, timeout=timeout
            )
            return response.status_code, response.text

        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.status, response.read().decode(
                    "utf-8", errors="replace"
                )
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8", errors="replace")

    def _update_usage_from_response(self, data: dict):
        usage = data.get("usage") or {}
        if not isinstance(usage, dict):
            self.last_usage = {}
            self.last_usage_text = ""
            return

        self.last_usage = dict(usage)
        input_tokens = int(usage.get("input_tokens") or 0)
        output_tokens = int(usage.get("output_tokens") or 0)
        total_tokens = int(
            usage.get("total_tokens") or (input_tokens + output_tokens) or 0
        )
        if total_tokens <= 0:
            self.last_usage_text = ""
            return
        self.last_usage_text = (
            f"Gesamt: {total_tokens} | Input: {input_tokens} | Output: {output_tokens}"
        )

    def _safe_error_text(self, text: str, *, limit: int | None = 1000) -> str:
        text = str(text)
        if self.api_key:
            text = text.replace(self.api_key, "[REDACTED]")
        text = re.sub(r"(?i)\bBearer\s+\S+", "Bearer [REDACTED]", text)
        text = re.sub(r"\bsk-[A-Za-z0-9_*.-]{4,}", "[REDACTED]", text)
        return text if limit is None else text[:limit]

    def _format_api_error(
        self, response_text: str, status_code: int | None = None
    ) -> str:
        try:
            data = json.loads(response_text)
        except (ValueError, TypeError):
            data = {}
        if not isinstance(data, dict):
            data = {}
        error = data.get("error")
        if not isinstance(error, dict):
            error = data
        message = error.get("message")
        if not isinstance(message, str) or not message.strip():
            message = "Unbekannter API-Fehler"
        parts = ["Fehler: " + self._safe_error_text(message.strip())]
        if type(status_code) is int and 100 <= status_code <= 599:
            parts.append(f"HTTP-Status: {status_code}")
        for key, label in (("code", "API-Code"), ("type", "API-Typ")):
            value = error.get(key)
            if isinstance(value, str):
                value = self._safe_error_text(value)
                if re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", value):
                    parts.append(f"{label}: {value}")
        if status_code == 401:
            parts.append(
                "Anmeldung abgelehnt: OpenAI-API-Key, Projektberechtigungen und gegebenenfalls IP-Freigabe prüfen. "
                "Speichern im Schlüsselbund bestätigt keine erfolgreiche API-Anmeldung."
            )
        return "\n".join(parts)

    def _analysis_max_output_tokens(
        self, prompt: str, files: list[dict] | None = None
    ) -> int:
        prompt_length = len(str(prompt or ""))
        if prompt_length >= 80000:
            return 6400
        if prompt_length >= 40000:
            return 5120
        return 4096

    def _analysis_timeout_seconds(
        self, prompt: str, files: list[dict] | None = None
    ) -> int:
        prompt_length = len(str(prompt or ""))
        has_files = bool(files)
        if prompt_length >= 80000 or has_files:
            return 90
        if prompt_length >= 40000:
            return 75
        if prompt_length >= 15000:
            return 60
        return 60

    def _read_response(self, data: dict) -> tuple[bool, str]:
        """Preserve partial output, but never report it as a completed answer."""
        self._update_usage_from_response(data)
        self.last_response_incomplete = data.get("status") == "incomplete"
        text = data.get("output_text")
        if not isinstance(text, str) or not text.strip():
            parts = []
            for item in data.get("output", []) or []:
                for content in item.get("content", []) or []:
                    if content.get("type") == "output_text":
                        parts.append(content.get("text", ""))
            text = "\n".join(parts)
        text = text.strip()
        if self.last_response_incomplete:
            details = data.get("incomplete_details")
            reason = details.get("reason") if isinstance(details, dict) else None
            if reason == "max_output_tokens":
                notice = "Antwort unvollständig: Ausgabelimit erreicht."
            elif reason == "content_filter":
                notice = (
                    "Antwort unvollständig: API-Inhaltsfilter hat die Ausgabe begrenzt."
                )
            else:
                notice = "Antwort unvollständig: Die API meldet einen Abbruch."
            notice += "\nDer folgende Text ist nur eine Teilantwort. Es erfolgt keine automatische Wiederholung."
            if text:
                notice += "\n\n" + self._safe_error_text(text, limit=None)
            return False, notice
        if data.get("status") in {"failed", "cancelled", "queued", "in_progress"}:
            return False, "Antwort nicht abgeschlossen.\n" + self._format_api_error(
                data.get("error") and json.dumps({"error": data["error"]}) or "{}"
            )
        if not text:
            return False, "Empty response from API."
        return True, text

    def analyze(self, prompt: str, files: list[dict] | None = None) -> tuple[bool, str]:
        self.last_response_incomplete = False
        if not self.api_key:
            return False, "No API key configured (OPENAI_API_KEY)."

        try:
            url = "https://api.openai.com/v1/responses"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            files = files or []
            max_output_tokens = self._analysis_max_output_tokens(prompt, files)
            timeout_seconds = self._analysis_timeout_seconds(prompt, files)
            if files:
                content_items = [{"type": "input_text", "text": prompt}]
                for file_item in files:
                    if file_item.get("type") == "image" and file_item.get("path"):
                        content_items.append(
                            {
                                "type": "input_image",
                                "image_url": self.image_to_data_url(file_item["path"]),
                                "detail": "auto",
                            }
                        )
                payload = {
                    "model": self.default_model,
                    "input": [{"role": "user", "content": content_items}],
                    "max_output_tokens": max_output_tokens,
                }
            else:
                payload = {
                    "model": self.default_model,
                    "input": prompt,
                    "max_output_tokens": max_output_tokens,
                }

            payload["instructions"] = CHAD_COMMAND_GUIDANCE
            status_code, response_text = self._post_json(
                url,
                headers,
                payload,
                timeout=timeout_seconds,
            )

            if status_code != 200:
                return False, self._format_api_error(response_text, status_code)

            data = json.loads(response_text)
            return self._read_response(data)

        except Exception as exc:
            return False, "Error during online analysis: " + self._safe_error_text(exc)

    def chat(
        self, messages: list[dict], files: list[dict] | None = None
    ) -> tuple[bool, str]:
        self.last_response_incomplete = False
        if not self.api_key:
            return False, "No API key configured."

        try:
            url = "https://api.openai.com/v1/responses"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            input_items = [
                {
                    "role": "developer",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Du bist Chad, der NetMon Analyse-Assistent. "
                                "Antworte auf Deutsch, verständlich, praktisch und "
                                "sicherheitsbewusst. Gib bei Netzwerk-, Firewall-, "
                                "DNS-, VPN- und Linux-Themen konkrete nächste Schritte. "
                                "Keine gefährlichen Befehle ohne Warnung."
                            ),
                        }
                    ],
                }
            ]

            recent_messages = (messages or [])[-12:]
            files = files or []
            last_user_index = -1
            for idx, msg in enumerate(recent_messages):
                if msg.get("role", "user") == "user":
                    last_user_index = idx

            for idx, msg in enumerate(recent_messages):
                role = msg.get("role", "user")
                text = (msg.get("content") or "").strip()
                if not text:
                    continue

                if role == "assistant":
                    input_items.append(
                        {
                            "role": "assistant",
                            "content": [{"type": "output_text", "text": text}],
                        }
                    )
                else:
                    if role not in ("user", "developer", "system"):
                        role = "user"

                    content_items = [{"type": "input_text", "text": text}]
                    if role == "user" and idx == last_user_index:
                        for file_item in files:
                            if file_item.get("type") == "image" and file_item.get(
                                "path"
                            ):
                                content_items.append(
                                    {
                                        "type": "input_image",
                                        "image_url": self.image_to_data_url(
                                            file_item["path"]
                                        ),
                                        "detail": "auto",
                                    }
                                )

                    input_items.append(
                        {
                            "role": role,
                            "content": content_items,
                        }
                    )

            payload = {
                "model": self.default_model,
                "input": input_items,
                "instructions": CHAD_COMMAND_GUIDANCE,
                "max_output_tokens": 900,
            }

            status_code, response_text = self._post_json(
                url,
                headers,
                payload,
                timeout=30,
            )

            if status_code != 200:
                return False, self._format_api_error(response_text, status_code)

            data = json.loads(response_text)
            return self._read_response(data)

        except Exception as exc:
            return False, "Error in chat: " + self._safe_error_text(exc)


__all__ = ["AiOnlineService"]
