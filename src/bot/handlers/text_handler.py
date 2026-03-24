from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from src.llm.client import ask_claude


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processa mensagens de texto recebidas pelo bot.
    Envia a mensagem ao Claude e retorna a resposta formatada.
    """
    user = update.effective_user
    user_message = update.message.text

    logger.info(f"[TEXT] user_id={user.id} | user=@{user.username} | msg='{user_message[:60]}'")

    await update.message.chat.send_action("typing")

    try:
        reply = await ask_claude(
            user_id=user.id,
            user_message=user_message,
            voice_mode=False,
        )
        await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception as exc:
        logger.error(f"[TEXT] Erro ao processar mensagem de user_id={user.id}: {exc}")
        await update.message.reply_text(
            "Desculpe, ocorreu um erro ao processar sua mensagem. "
            "Por favor, tente novamente em instantes."
        )
