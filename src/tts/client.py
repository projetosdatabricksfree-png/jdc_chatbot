import io
import re
import tempfile
import os

import edge_tts
from pydub import AudioSegment
from loguru import logger

from src.transcription.whisper_client import _ensure_ffmpeg_in_path

# Voz neural pt-BR da Microsoft (opções: FranciscaNeural / AntonioNeural)
_VOICE = "pt-BR-FranciscaNeural"


def _strip_markdown(text: str) -> str:
    """
    Remove formatação Markdown do texto antes de enviar para TTS.
    Evita que o modelo leia símbolos como *, _, #, etc. em voz alta.
    """
    # Remove bold/italic: **texto**, *texto*, __texto__, _texto_
    text = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", text)
    text = re.sub(r"_{1,2}(.+?)_{1,2}", r"\1", text)
    # Remove headers: ## Título
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove inline code: `código`
    text = re.sub(r"`(.+?)`", r"\1", text)
    # Remove links: [texto](url)
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
    # Remove emojis e caracteres especiais que soam estranho em TTS
    text = re.sub(r"[🔵🟢🟦📊📌🎯🗺️⚙️❓⚠️✅🗑️🎙️📩👋]", "", text)
    # Limpa espaços duplos resultantes
    text = re.sub(r" {2,}", " ", text).strip()
    return text


async def text_to_voice_ogg(text: str) -> bytes:
    """
    Converte texto para áudio OGG/OPUS pronto para enviar como
    mensagem de voz no Telegram.

    Args:
        text: Texto a ser convertido (pode conter Markdown — será limpo automaticamente).

    Returns:
        Bytes do arquivo OGG/OPUS.

    Raises:
        RuntimeError: Se a conversão falhar.
    """
    _ensure_ffmpeg_in_path()
    clean_text = _strip_markdown(text)
    logger.debug(f"[TTS] Convertendo texto ({len(clean_text)} chars) para áudio...")

    # Gera MP3 via edge-tts em arquivo temporário
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_mp3:
        mp3_path = tmp_mp3.name

    try:
        communicate = edge_tts.Communicate(clean_text, _VOICE)
        await communicate.save(mp3_path)

        # Converte MP3 → OGG OPUS (formato de voz do Telegram)
        audio = AudioSegment.from_mp3(mp3_path)
        ogg_buffer = io.BytesIO()
        audio.export(ogg_buffer, format="ogg", codec="libopus", bitrate="64k")
        ogg_bytes = ogg_buffer.getvalue()

        logger.info(f"[TTS] Áudio gerado: {len(ogg_bytes) / 1024:.1f} KB")
        return ogg_bytes

    except Exception as exc:
        logger.error(f"[TTS] Falha na geração de áudio: {exc}")
        raise RuntimeError(f"Não foi possível gerar o áudio: {exc}") from exc
    finally:
        try:
            os.remove(mp3_path)
        except OSError:
            pass
