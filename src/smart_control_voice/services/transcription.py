"""Local speech-to-text adapter."""

from pathlib import Path
from typing import Any


class TranscriptionError(RuntimeError):
    """Raised when local transcription cannot complete."""


class WhisperTranscriber:
    def __init__(self, model: str, device: str, compute_type: str, language: str = "es") -> None:
        self._model_name = model
        self._device = device
        self._compute_type = compute_type
        self._language = language
        self._model: Any = None

    def _get_model(self) -> Any:
        if self._model is None:
            try:
                from faster_whisper import WhisperModel  # type: ignore[import-untyped]
            except ImportError as error:
                raise TranscriptionError("faster-whisper is not installed") from error
            self._model = WhisperModel(
                self._model_name,
                device=self._device,
                compute_type=self._compute_type,
            )
        return self._model

    def transcribe(self, audio_path: Path) -> str:
        try:
            segments, _ = self._get_model().transcribe(str(audio_path), language=self._language)
            text = " ".join(segment.text.strip() for segment in segments).strip()
        except Exception as error:
            raise TranscriptionError("audio transcription failed") from error
        if not text:
            raise TranscriptionError("audio did not contain recognizable speech")
        return text