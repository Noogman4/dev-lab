from __future__ import annotations

import json
import os


class LangService:
    def __init__(self, base_path: str):
        self.base_path = base_path

    def load(self, lang_code: str) -> dict:
        path = os.path.join(self.base_path, f"{lang_code}.json")

        if not os.path.isfile(path):
            return {}

        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            return {}

        return data if isinstance(data, dict) else {}
