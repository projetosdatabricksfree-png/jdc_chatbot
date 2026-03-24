import sys
from loguru import logger

from src.config import settings
from src.knowledge.loader import load_knowledge_base
from src.bot.application import build_application


def configure_logging() -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        colorize=True,
    )
    logger.add(
        "logs/bot.log",
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} - {message}",
    )


def main() -> None:
    configure_logging()

    logger.info("=" * 60)
    logger.info("JDC Chatbot — CAIXA Vida e Previdência")
    logger.info(f"Modelo LLM: {settings.claude_model}")
    logger.info(f"Modelo Whisper: {settings.whisper_model}")
    logger.info("=" * 60)

    # Pré-carrega a base de conhecimento na inicialização
    load_knowledge_base()

    app = build_application()

    logger.info("Bot iniciado. Aguardando mensagens... (Ctrl+C para encerrar)")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
