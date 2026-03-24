import io

from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from src.llm.client import ask_claude
from src.transcription.whisper_client import transcribe_audio
from src.tts.client import text_to_voice_ogg


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processa mensagens de voz recebidas pelo bot.

    Fluxo completo:
    1. Baixa o OGG/OPUS do Telegram
    2. Transcreve via Whisper (pt-BR)
    3. Envia texto ao Claude em modo voz (resposta curta)
    4. Converte resposta para áudio via edge-tts
    5. Envia resposta como mensagem de voz
    """
    user = update.effective_user
    voice = update.message.voice

    logger.info(
        f"[VOICE] user_id={user.id} | user=@{user.username} "
        f"| duration={voice.duration}s"
    )

    await update.message.chat.send_action("typing")

    processing_msg = await update.message.reply_text(
        "🎙️ Recebi seu áudio, transcrevendo..."
    )

    try:
        # 1. Download do arquivo de voz
        voice_file = await voice.get_file()
        buffer = io.BytesIO()
        await voice_file.download_to_memory(buffer)
        audio_bytes = buffer.getvalue()

        # 2. Transcrição
        transcript = transcribe_audio(audio_bytes, file_extension="ogg")
        logger.info(f"[VOICE] Transcrição: '{transcript[:80]}'")

        await processing_msg.edit_text(
            f"🎙️ *Você perguntou:* _{transcript}_\n\n⏳ Gerando resposta...",
            parse_mode="Markdown",
        )

        await update.message.chat.send_action("record_voice")

        # 3. Resposta do Claude (modo voz = resposta curta e direta)
        reply_text = await ask_claude(
            user_id=user.id,
            user_message=transcript,
            voice_mode=True,
        )

        # 4. Converte resposta para áudio OGG
        voice_bytes = await text_to_voice_ogg(reply_text)

        # 5. Envia como mensagem de voz
        await update.message.reply_voice(
            voice=io.BytesIO(voice_bytes),
            caption=f"_{reply_text[:900]}_" if len(reply_text) <= 900 else None,
            parse_mode="Markdown" if len(reply_text) <= 900 else None,
        )

        # Remove a mensagem de status intermediária
        await processing_msg.delete()

    except RuntimeError as exc:
        logger.error(f"[VOICE] Falha para user_id={user.id}: {exc}")
        await processing_msg.edit_text(
            "⚠️ Não consegui processar seu áudio.\n"
            "Por favor, envie sua dúvida por *texto*.",
            parse_mode="Markdown",
        )
    except Exception as exc:
        logger.error(f"[VOICE] Erro inesperado para user_id={user.id}: {exc}")
        await processing_msg.edit_text(
            "⚠️ Ocorreu um erro inesperado. Tente novamente ou envie sua dúvida por texto."
        )
