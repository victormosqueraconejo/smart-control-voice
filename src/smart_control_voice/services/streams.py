"""Configured media resolution with yt-dlp and static fallbacks."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import urlparse

from ..models import Target, VoiceIntent


class StreamResolutionError(RuntimeError):
    """Raised when no configured playable source can be resolved."""


class SourceKind(StrEnum):
    URL = "url"
    YOUTUBE_SEARCH = "youtube_search"


@dataclass(frozen=True)
class MediaSource:
    kind: SourceKind
    value: str


class StreamResolver:
    def __init__(
        self,
        sources: dict[Target, tuple[MediaSource, ...]],
        extractor: Callable[[str], str] | None = None,
    ) -> None:
        self._sources = sources
        self._extractor = extractor

    def resolve_static(self, intent: VoiceIntent) -> str | None:
        for source in self._sources.get(intent.target, ()):
            if source.kind == SourceKind.URL and self._is_http_url(source.value):
                return source.value
        return None

    @staticmethod
    def _is_http_url(value: str) -> bool:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    def resolve(self, intent: VoiceIntent) -> str:
        sources = self._sources.get(intent.target, ())
        static_url = self.resolve_static(intent)
        if static_url is not None and intent.media_type.value == "live_stream":
            return static_url

        query = intent.parameters.query or next(
            (source.value for source in sources if source.kind == SourceKind.YOUTUBE_SEARCH),
            None,
        )
        if not query:
            raise StreamResolutionError(f"no source configured for {intent.target.value}")
        if self._extractor is not None:
            url = self._extractor(query)
            if not self._is_http_url(url):
                raise StreamResolutionError("resolved source is not a valid HTTP URL")
            return url
        try:
            import yt_dlp  # type: ignore[import-untyped]

            with yt_dlp.YoutubeDL({"quiet": True, "format": "best", "noplaylist": True}) as downloader:
                info = downloader.extract_info(f"ytsearch1:{query}", download=False)
            url = info["entries"][0].get("url") if info.get("entries") else info.get("url")
        except Exception as error:
            raise StreamResolutionError("yt-dlp could not resolve the requested source") from error
        if not isinstance(url, str) or not self._is_http_url(url):
            raise StreamResolutionError("resolved source is not a valid HTTP URL")
        return url