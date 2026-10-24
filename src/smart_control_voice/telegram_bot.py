"""Telegram polling adapter."""

import logging
import tempfile
from datetime import timedelta
from pathlib import Path
from typing import Any

from telegram import Update
from telegram.ext import Application, ApplicationBuilder, ContextTypes, MessageHandler, filters

from .application import VoiceApplication
from .config import Settings

logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self, settings: Settings, voice_application: VoiceApplication) -> None:
        self._settings = settings
        self._voice_application = voice_application

    def build(self) -> Application[Any, Any, Any, Any, Any, Any]:
        application = ApplicationBuilder().token(self._settings.telegram_bot_token).build()
        application.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        return application

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.effective_message
        user = update.effective_user
        chat = update.effective_chat
        if message is None or user is None or chat is None or message.voice is None:
            return
        if user.id not in self._settings.telegram_allowed_ids and chat.id not in self._settings.telegram_allowed_ids:
            await message.reply_text("No tienes autorización para usar este bot.")
            return
        voice = message.voice
        if voice.file_size is not None and voice.file_size > self._settings.audio_max_bytes:
            await message.reply_text("El audio supera el tamaño máximo permitido.")
            return
        duration = voice.duration.total_seconds() if isinstance(voice.duration, timedelta) else voice.duration
        if duration > self._settings.audio_max_duration_seconds:
            await message.reply_text("El audio supera la duración máxima permitida.")
            return

        await message.reply_text("Procesando tu comando...")
        try:
            telegram_file = await context.bot.get_file(voice.file_id)
            with tempfile.TemporaryDirectory(dir=self._settings.work_directory) as directory:
                audio_path = Path(directory) / "voice.ogg"
                await telegram_file.download_to_drive(audio_path)
                intent = await self._voice_application.process(chat.id, audio_path)
            await message.reply_text(f"Listo: {intent.action.value} -> {intent.target.value}")
        except Exception:
            logger.exception("voice command failed", extra={"chat_id": chat.id, "update_id": update.update_id})
            await message.reply_text("No pude ejecutar el comando. Revisa el servicio y vuelve a intentar.")