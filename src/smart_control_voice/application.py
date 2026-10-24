"""Application use case coordinating transcription, intent and Kodi."""

import asyncio
from pathlib import Path
from typing import Protocol

from .models import Action, VoiceIntent


class Transcriber(Protocol):
    def transcribe(self, audio_path: Path) -> str: ...


class IntentClient(Protocol):
    async def extract(self, text: str) -> VoiceIntent: ...


class Resolver(Protocol):
    def resolve(self, intent: VoiceIntent) -> str: ...


class Kodi(Protocol):
    async def open(self, media_url: str) -> object: ...
    async def stop(self) -> object: ...
    async def set_volume(self, volume: int) -> object: ...


class VoiceApplication:
    def __init__(self, transcriber: Transcriber, intent_client: IntentClient, resolver: Resolver, kodi: Kodi) -> None:
        self._transcriber = transcriber
        self._intent_client = intent_client
        self._resolver = resolver
        self._kodi = kodi
        self._locks: dict[int, asyncio.Lock] = {}

    async def process(self, chat_id: int, audio_path: Path) -> VoiceIntent:
        lock = self._locks.setdefault(chat_id, asyncio.Lock())
        async with lock:
            transcript = await asyncio.to_thread(self._transcriber.transcribe, audio_path)
            intent = await self._intent_client.extract(transcript)
            if intent.action == Action.STOP:
                await self._kodi.stop()
            elif intent.action == Action.SET_VOLUME:
                assert intent.parameters.volume is not None
                await self._kodi.set_volume(intent.parameters.volume)
            else:
                media_url = await asyncio.to_thread(self._resolver.resolve, intent)
                await self._kodi.open(media_url)
            return intent