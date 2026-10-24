"""Domain models shared by the integrations."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Action(StrEnum):
    PLAY_CHANNEL = "play_channel"
    PLAY_CATEGORY = "play_category"
    STOP = "stop"
    SET_VOLUME = "set_volume"


class Target(StrEnum):
    CARACOL = "caracol"
    RCN = "rcn"
    TELEPACIFICO = "telepacifico"
    NOTICIAS = "noticias"
    PELICULAS_INVESTIGACION = "peliculas_investigacion"


class MediaType(StrEnum):
    LIVE_STREAM = "live_stream"
    YOUTUBE_SEARCH = "youtube_search"
    LOCAL_FILE = "local_file"


class IntentParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str | None = None
    volume: int | None = Field(default=None, ge=0, le=100)


class VoiceIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Action
    target: Target
    media_type: MediaType
    parameters: IntentParameters = Field(default_factory=IntentParameters)

    @model_validator(mode="after")
    def validate_parameters(self) -> "VoiceIntent":
        if self.action == Action.SET_VOLUME and self.parameters.volume is None:
            raise ValueError("set_volume requires parameters.volume")
        if self.action == Action.STOP and self.media_type != MediaType.LOCAL_FILE:
            raise ValueError("stop must use local_file as media_type")
        if self.action in (Action.PLAY_CHANNEL, Action.PLAY_CATEGORY) and self.media_type == MediaType.LOCAL_FILE:
            raise ValueError("play actions cannot use local_file")
        return self