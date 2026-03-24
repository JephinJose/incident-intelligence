import json
import logging
import time

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model

    async def generate(self, prompt: str, timeout: float = 120.0) -> str:
        start = time.monotonic()
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                r = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False},
                )
                r.raise_for_status()
            except httpx.ConnectError as e:
                raise RuntimeError(f"Cannot connect to Ollama at {self.base_url}: {e}") from e
            except httpx.HTTPStatusError as e:
                raise RuntimeError(f"Ollama returned {e.response.status_code}: {e.response.text}") from e

        elapsed_ms = int((time.monotonic() - start) * 1000)
        raw = r.json().get("response", "").strip()
        logger.debug("Ollama response in %dms: %s...", elapsed_ms, raw[:100])
        return raw

    async def generate_json(self, prompt: str, fallback: dict | None = None, timeout: float = 120.0) -> dict:
        raw = await self.generate(prompt, timeout=timeout)
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Failed to parse Ollama JSON response: %s", raw[:200])
            return fallback or {"raw": raw}

    async def health_check(self) -> bool:
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                r = await client.get(f"{self.base_url}/api/tags")
                return r.status_code == 200
            except httpx.ConnectError:
                return False


ollama = OllamaClient()
