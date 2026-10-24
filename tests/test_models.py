import pytest
from pydantic import ValidationError

from smart_control_voice.models import Action, MediaType, Target, VoiceIntent


def test_valid_play_intent() -> None:
    intent = VoiceIntent.model_validate(
        {
            "action": "play_channel",
            "target": "caracol",
            "media_type": "live_stream",
            "parameters": {"query": "señal en vivo"},
        }
    )

    assert intent.action == Action.PLAY_CHANNEL
    assert intent.target == Target.CARACOL


def test_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        VoiceIntent.model_validate(
            {
                "action": "stop",
                "target": "caracol",
                "media_type": "local_file",
                "unexpected": True,
            }
        )


def test_volume_requires_bounded_value() -> None:
    with pytest.raises(ValidationError):
        VoiceIntent(
            action=Action.SET_VOLUME,
            target=Target.CARACOL,
            media_type=MediaType.LIVE_STREAM,
        )

    intent = VoiceIntent(
        action=Action.SET_VOLUME,
        target=Target.CARACOL,
        media_type=MediaType.LIVE_STREAM,
        parameters={"volume": 40},
    )
    assert intent.parameters.volume == 40