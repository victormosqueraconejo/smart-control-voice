"""Application entry point."""

import logging
from pathlib import Path

from .config import get_settings


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    settings = get_settings()
    Path(settings.work_directory).mkdir(parents=True, exist_ok=True)
    from .application import VoiceApplication
    from .models import Target
    from .services.kodi import KodiClient
    from .services.llm import GroqIntentClient
    from .services.streams import MediaSource, SourceKind, StreamResolver
    from .services.transcription import WhisperTranscriber
    from .telegram_bot import TelegramBot

    source_values = {
        Target.CARACOL: settings.source_caracol_url,
        Target.RCN: settings.source_rcn_url,
        Target.TELEPACIFICO: settings.source_telepacifico_url,
        Target.NOTICIAS: settings.source_noticias_url,
        Target.PELICULAS_INVESTIGACION: settings.source_peliculas_investigacion_url,
    }
    sources: dict[Target, tuple[MediaSource, ...]] = {
        target: (MediaSource(SourceKind.URL, url),)
        for target, url in source_values.items()
        if url
    }

    voice_application = VoiceApplication(
        transcriber=WhisperTranscriber(
            settings.whisper_model,
            settings.whisper_device,
            settings.whisper_compute_type,
        ),
        intent_client=GroqIntentClient(settings.groq_api_key, settings.groq_model, settings.request_timeout_seconds),
        resolver=StreamResolver(sources),
        kodi=KodiClient(settings.kodi_url, settings.request_timeout_seconds),
    )
    TelegramBot(settings, voice_application).build().run_polling()


if __name__ == "__main__":
    main()