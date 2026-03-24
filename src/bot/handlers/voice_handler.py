import io

from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from src.llm.client import ask_claude
from src.transcription.whisper_client import transcribe_audio


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processa mensagens de voz recebidas pelo bot.

    Fluxo:
    1. Baixa o arquivo OGG/OPUS do Telegram
    2. Transcreve o áudio via Whisper
    3. Envia o texto transcrito ao Claude em modo voz (resposta curta)
    4. Retorna a resposta ao consultor
    """
    user = update.effective_user
    voice = update.message.voice

    logger.info(
        f"[VOICE] user_id={user.id} | user=@{user.username} "
        f"| duration={voice.duration}s"
    )

    await update.message.chat.send_action("typing")

    # Feedback imediato enquanto processa
    processing_msg = await update.message.reply_text(
        "🎙️ Recebi seu áudio, transcrevendo..."
    )

    try:
        # Download do arquivo de voz
        voice_file = await voice.get_file()
        buffer = io.BytesIO()
        await voice_file.download_to_memory(buffer)
        audio_bytes = buffer.getvalue()

        # Transcrição
        transcript = transcribe_audio(audio_bytes, file_extension="ogg")
        logger.info(f"[VOICE] Transcrição: '{transcript[:80]}'")

        # Confirmação da transcrição para o usuário
        await processing_msg.edit_text(
            f"🎙️ *Você perguntou:* _{transcript}_",
            parse_mode="Markdown",
        )

        await update.message.chat.send_action("typing")

        # Resposta do Claude em modo voz (respostas curtas e diretas)
        reply = await ask_claude(
            user_id=user.id,
            user_message=transcript,
            voice_mode=True,
        )

        await update.message.reply_text(reply, parse_mode="Markdown")

    except RuntimeError as exc:
        logger.error(f"[VOICE] Falha na transcrição para user_id={user.id}: {exc}")
        await processing_msg.edit_text(
            "Não consegui transcrever seu áudio. "
            "Por favor, tente enviar sua dúvida por texto."
        )
    except Exception as exc:
        logger.error(f"[VOICE] Erro inesperado para user_id={user.id}: {exc}")
        await processing_msg.edit_text(
            "Ocorreu um erro ao processar seu áudio. "
            "Tente novamente ou envie sua dúvida por texto."
        )
