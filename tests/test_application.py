from pathlib import Path

import pytest

from smart_control_voice.application import VoiceApplication
from smart_control_voice.models import VoiceIntent


class FakeTranscriber:
    def transcribe(self, audio_path: Path) -> str:
        return "reproduce caracol"


class FakeIntentClient:
    async def extract(self, text: str) -> VoiceIntent:
        return VoiceIntent.model_validate(
            {
                "action": "play_channel",
                "target": "caracol",
                "media_type": "live_stream",
            }
        )


class FakeResolver:
    def resolve(self, intent: VoiceIntent) -> str:
        return "https://example.test/caracol.m3u8"


class FakeKodi:
    def __init__(self) -> None:
        self.opened: list[str] = []

    async def open(self, media_url: str) -> object:
        self.opened.append(media_url)
        return "OK"

    async def stop(self) -> object:
        return "OK"

    async def set_volume(self, volume: int) -> object:
        return "OK"


@pytest.mark.asyncio
async def test_processes_voice_command_without_external_services(tmp_path: Path) -> None:
    kodi = FakeKodi()
    application = VoiceApplication(FakeTranscriber(), FakeIntentClient(), FakeResolver(), kodi)

    intent = await application.process(42, tmp_path / "voice.ogg")

    assert intent.target.value == "caracol"
    assert kodi.opened == ["https://example.test/caracol.m3u8"]