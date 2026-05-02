"""Optional OpenAI API client for NetMon's Chad analysis tab."""

from __future__ import annotations

import base64
import mimetypes
import os
import json
import urllib.error
import urllib.request

try:
    import requests
except Exception:  # pragma: no cover - depends on optional runtime dependency.
    requests = None


class AiOnlineService:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "").strip()

    def is_available(self):
        return bool(self.api_key)

    def image_to_data_url(self, path: str) -> str:
        mime, _ = mimetypes.guess_type(path)
        if not mime:
            mime = "image/png"

        with open(path, "rb") as f:
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

    def analyze(self, prompt: str, files: list[dict] | None = None) -> tuple[bool, str]:
        if not self.api_key:
            return False, "Kein API-Key gesetzt (OPENAI_API_KEY)."

        try:
            url = "https://api.openai.com/v1/responses"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            files = files or []
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
                    "model": "gpt-4.1-mini",
                    "input": [{"role": "user", "content": content_items}],
                    "max_output_tokens": 800,
                }
            else:
                payload = {
                    "model": "gpt-4.1-mini",
                    "input": prompt,
                    "max_output_tokens": 800,
                }

            status_code, response_text = self._post_json(
                url,
                headers,
                payload,
                timeout=20,
            )

            if status_code != 200:
                return False, f"API Fehler: {status_code} - {response_text}"

            data = json.loads(response_text)
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
                return False, "Leere Antwort von API."

            return True, result_text

        except Exception as exc:
            return False, f"Fehler bei Online-Analyse: {exc}"

    def chat(
        self, messages: list[dict], files: list[dict] | None = None
    ) -> tuple[bool, str]:
        if not self.api_key:
            return False, "Kein API-Key gesetzt."

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
                "model": "gpt-4.1-mini",
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
                return False, f"API Fehler: {status_code} - {response_text}"

            data = json.loads(response_text)
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
                return False, "Leere Antwort von API."

            return True, result_text

        except Exception as exc:
            return False, f"Fehler im Chat: {exc}"


__all__ = ["AiOnlineService"]
