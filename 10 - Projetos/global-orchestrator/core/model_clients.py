from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request


class ModelClientError(RuntimeError):
    """Raised when the configured model client cannot produce a usable response."""


class GeminiModelClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gemini-2.5-flash",
        timeout: int = 30,
        api_base: str = "https://generativelanguage.googleapis.com/v1beta/models",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.api_base = api_base.rstrip("/")

    def _build_url(self) -> str:
        encoded_key = urllib.parse.quote(self.api_key, safe="")
        return f"{self.api_base}/{self.model}:generateContent?key={encoded_key}"

    def complete(self, *, prompt: str, message: str) -> str:
        payload = {
            "system_instruction": {
                "parts": [{"text": prompt}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": message}],
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 400,
                "responseMimeType": "application/json",
            },
        }

        request = urllib.request.Request(
            self._build_url(),
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
            parsed = json.loads(raw)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise ModelClientError(f"Gemini HTTP {exc.code}: {body[:500]}") from exc
        except Exception as exc:
            raise ModelClientError(f"Erro ao chamar Gemini: {exc}") from exc

        try:
            return parsed["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelClientError(f"Resposta Gemini sem texto utilizavel: {json.dumps(parsed)[:500]}") from exc
