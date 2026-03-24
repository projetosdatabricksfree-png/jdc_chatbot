from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)
from loguru import logger

from src.config import settings
from src.bot.handlers.commands import start, help_command, clear_command
from src.bot.handlers.text_handler import handle_text
from src.bot.handlers.voice_handler import handle_voice


def build_application() -> Application:
    """
    Constrói e configura a aplicação do bot Telegram com todos os handlers registrados.

    Returns:
        Application configurada e pronta para iniciar o polling.
    """
    app = Application.builder().token(settings.telegram_token).build()

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("limpar", clear_command))

    # Mensagens de texto (exclui comandos)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )

    # Mensagens de voz
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    logger.info("Handlers registrados: /start, /help, /limpar, text, voice")
    return app
