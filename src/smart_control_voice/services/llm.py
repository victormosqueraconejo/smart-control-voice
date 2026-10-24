"""Groq intent extraction adapter."""

import json
from typing import Any

from groq import AsyncGroq

from ..models import VoiceIntent


class IntentExtractionError(RuntimeError):
    """Raised when Groq returns an unusable intent."""


SYSTEM_PROMPT = """Eres un clasificador de comandos multimedia en español.
Devuelve únicamente JSON válido, sin markdown, comentarios ni texto adicional.
Usa exactamente estas claves: action, target, media_type, parameters.
parameters puede contener query y, para set_volume, volume entre 0 y 100.
Valores permitidos:
action: play_channel, play_category, stop, set_volume
target: caracol, rcn, telepacifico, noticias, peliculas_investigacion
media_type: live_stream, youtube_search, local_file
"""


class GroqIntentClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: float = 30.0,
        client: Any | None = None,
    ) -> None:
        self._client = client or AsyncGroq(api_key=api_key, timeout=timeout)
        self._model = model

    async def extract(self, text: str) -> VoiceIntent:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            raw = response.choices[0].message.content
            if not isinstance(raw, str):
                raise TypeError("Groq response content is not text")
            return VoiceIntent.model_validate(json.loads(raw))
        except Exception as error:
            raise IntentExtractionError("Groq returned an invalid or unavailable intent") from error