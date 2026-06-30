"""Optional OpenAI API client for NetMon's Chad analysis tab."""

from __future__ import annotations

import base64
import mimetypes
import os
import json
import urllib.error
import urllib.request
from pathlib import Path

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
            raise ValueError("Image path must be inside the user home directory.") from exc

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

    def _format_api_error(self, response_text: str) -> str:
        text = (response_text or "").strip()
        if not text:
            return "Fehler: Unbekannter API-Fehler"

        try:
            data = json.loads(text)
        except Exception:
            return "Fehler: Unbekannter API-Fehler"

        error_data = data.get("error")
        if isinstance(error_data, dict):
            message = str(error_data.get("message") or "").strip()
            if message:
                return f"Fehler: {message}"

        message = str(data.get("message") or "").strip()
        if message:
            return f"Fehler: {message}"

        return "Fehler: Unbekannter API-Fehler"

    def _analysis_max_output_tokens(self, prompt: str, files: list[dict] | None = None) -> int:
        prompt_length = len(str(prompt or ""))
        has_files = bool(files)
        if prompt_length >= 80000:
            return 3200
        if prompt_length >= 40000:
            return 2600
        if prompt_length >= 15000:
            return 2000
        if has_files:
            return 1200
        return 1400

    def _analysis_timeout_seconds(self, prompt: str, files: list[dict] | None = None) -> int:
        prompt_length = len(str(prompt or ""))
        has_files = bool(files)
        if prompt_length >= 80000 or has_files:
            return 90
        if prompt_length >= 40000:
            return 75
        if prompt_length >= 15000:
            return 60
        return 30

    def analyze(self, prompt: str, files: list[dict] | None = None) -> tuple[bool, str]:
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

            status_code, response_text = self._post_json(
                url,
                headers,
                payload,
                timeout=timeout_seconds,
            )

            if status_code != 200:
                return False, self._format_api_error(response_text)

            data = json.loads(response_text)
            self._update_usage_from_response(data)
            if data.get("output_text"):
                return True, str(data.get("output_text", "")).strip()

            output = data.get("output", [])
            text_parts = []

            for item in output:
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        text_parts.append(content.get("text", ""))

            result_text = "\n".join(text_parts).strip()

            if not result_text:
                return False, "Empty response from API."

            return True, result_text

        except Exception as exc:
            return False, f"Error during online analysis: {exc}"

    def chat(
        self, messages: list[dict], files: list[dict] | None = None
    ) -> tuple[bool, str]:
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
                "max_output_tokens": 900,
            }

            status_code, response_text = self._post_json(
                url,
                headers,
                payload,
                timeout=30,
            )

            if status_code != 200:
                return False, self._format_api_error(response_text)

            data = json.loads(response_text)
            self._update_usage_from_response(data)
            if data.get("output_text"):
                result_text = str(data.get("output_text", "")).strip()
                if result_text:
                    return True, result_text

            output = data.get("output", [])
            text_parts = []

            for item in output:
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        text_parts.append(content.get("text", ""))

            result_text = "\n".join(text_parts).strip()

            if not result_text:
                return False, "Empty response from API."

            return True, result_text

        except Exception as exc:
            return False, f"Error in chat: {exc}"


__all__ = ["AiOnlineService"]
