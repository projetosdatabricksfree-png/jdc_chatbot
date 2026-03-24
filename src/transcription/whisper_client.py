import os
import tempfile
from pathlib import Path

from loguru import logger

from src.config import settings

# Carregamento lazy do modelo Whisper (download único ~150MB para modelo 'base')
_whisper_model = None


def _get_model():
    global _whisper_model
    if _whisper_model is None:
        import whisper  # import lazy para não bloquear a inicialização do bot

        logger.info(f"Carregando modelo Whisper '{settings.whisper_model}'...")
        _whisper_model = whisper.load_model(settings.whisper_model)
        logger.info("Modelo Whisper pronto.")
    return _whisper_model


def transcribe_audio(audio_bytes: bytes, file_extension: str = "ogg") -> str:
    """
    Transcreve um arquivo de áudio para texto usando o modelo Whisper local.

    Args:
        audio_bytes: Conteúdo binário do arquivo de áudio.
        file_extension: Extensão do arquivo (ex: 'ogg', 'mp3', 'wav').

    Returns:
        Texto transcrito do áudio.

    Raises:
        RuntimeError: Se a transcrição falhar.
    """
    with tempfile.NamedTemporaryFile(
        suffix=f".{file_extension}", delete=False
    ) as tmp_file:
        tmp_path = tmp_file.name
        tmp_file.write(audio_bytes)

    try:
        logger.debug(f"Transcrevendo áudio: {tmp_path}")
        model = _get_model()
        result = model.transcribe(tmp_path, language="pt", fp16=False)
        transcript = result["text"].strip()
        logger.info(f"Transcrição concluída: '{transcript[:80]}...'")
        return transcript
    except Exception as exc:
        logger.error(f"Falha na transcrição do áudio: {exc}")
        raise RuntimeError(f"Não foi possível transcrever o áudio: {exc}") from exc
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
