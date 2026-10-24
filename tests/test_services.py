import json
from types import SimpleNamespace

import httpx
import pytest

from smart_control_voice.models import Target, VoiceIntent
from smart_control_voice.services.kodi import KodiClient, KodiError
from smart_control_voice.services.llm import GroqIntentClient, IntentExtractionError
from smart_control_voice.services.streams import MediaSource, SourceKind, StreamResolver


def play_intent() -> VoiceIntent:
    return VoiceIntent.model_validate(
        {
            "action": "play_channel",
            "target": "caracol",
            "media_type": "youtube_search",
            "parameters": {"query": "Caracol TV en vivo"},
        }
    )


def test_resolver_uses_configured_youtube_source() -> None:
    queries: list[str] = []

    def extract(query: str) -> str:
        queries.append(query)
        return "https://cdn.example.test/live.m3u8"

    resolver = StreamResolver(
        {Target.CARACOL: (MediaSource(SourceKind.YOUTUBE_SEARCH, "Caracol oficial"),)},
        extractor=extract,
    )

    assert resolver.resolve(play_intent()) == "https://cdn.example.test/live.m3u8"
    assert queries == ["Caracol TV en vivo"]


@pytest.mark.asyncio
async def test_kodi_client_sends_json_rpc_request() -> None:
    requests: list[dict[str, object]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": "smart-control-voice", "result": "OK"})

    client = KodiClient("http://kodi.test/jsonrpc", transport=httpx.MockTransport(handler))

    await client.open("https://cdn.example.test/live.m3u8")

    assert requests[0]["method"] == "Player.Open"
    assert requests[0]["params"] == {"item": {"file": "https://cdn.example.test/live.m3u8"}}


@pytest.mark.asyncio
async def test_kodi_client_rejects_json_rpc_errors() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": "smart-control-voice", "error": {"code": -1}})

    client = KodiClient("http://kodi.test/jsonrpc", transport=httpx.MockTransport(handler))

    with pytest.raises(KodiError):
        await client.stop()


@pytest.mark.asyncio
async def test_groq_client_validates_response() -> None:
    class FakeCompletions:
        async def create(self, **kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content='{"action":"play_channel","target":"caracol","media_type":"live_stream","parameters":{}}'
                        )
                    )
                ]
            )

    client = GroqIntentClient("test-key", "llama3-8b-8192", client=SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions())))

    intent = await client.extract("reproduce caracol")

    assert intent.target == Target.CARACOL


@pytest.mark.asyncio
async def test_groq_client_wraps_invalid_json() -> None:
    class FakeCompletions:
        async def create(self, **kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="not-json"))])

    client = GroqIntentClient("test-key", "llama3-8b-8192", client=SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions())))

    with pytest.raises(IntentExtractionError):
        await client.extract("reproduce caracol")