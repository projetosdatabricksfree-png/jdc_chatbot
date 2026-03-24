import os
import shutil
import tempfile
from pathlib import Path

from loguru import logger

from src.config import settings

# Carregamento lazy do modelo Whisper
_whisper_model = None

# Caminhos candidatos para o ffmpeg no Windows (winget e instalações manuais comuns)
_FFMPEG_SEARCH_PATHS = [
    # winget (Gyan.FFmpeg)
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/Links",
    # busca pelo padrão winget de pacotes descompactados
    *sorted(
        (Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/Packages").glob(
            "Gyan.FFmpeg_*/ffmpeg-*-full_build/bin"
        ),
        reverse=True,  # usa a versão mais recente
    ),
    # instalações manuais comuns
    Path("C:/ffmpeg/bin"),
    Path("C:/Program Files/ffmpeg/bin"),
]


def _ensure_ffmpeg_in_path() -> None:
    """
    Garante que o executável ffmpeg está acessível neste processo Python.
    Resolve o problema de PATH não atualizado após instalação via winget
    com o processo já em execução.
    """
    if shutil.which("ffmpeg"):
        return  # já está no PATH

    for candidate in _FFMPEG_SEARCH_PATHS:
        ffmpeg_exe = candidate / "ffmpeg.exe"
        if ffmpeg_exe.exists():
            bin_dir = str(candidate)
            os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
            logger.info(f"ffmpeg encontrado e adicionado ao PATH: {bin_dir}")
            return

    logger.warning(
        "ffmpeg não encontrado. Transcrição de áudio pode falhar. "
        "Instale com: winget install Gyan.FFmpeg"
    )


def _get_model():
    global _whisper_model
    if _whisper_model is None:
        import whisper

        _ensure_ffmpeg_in_path()
        logger.info(f"Carregando modelo Whisper '{settings.whisper_model}'...")
        _whisper_model = whisper.load_model(settings.whisper_model)
        logger.info("Modelo Whisper pronto.")
    return _whisper_model


def transcribe_audio(audio_bytes: bytes, file_extension: str = "ogg") -> str:
    """
    Transcreve um arquivo de áudio para texto usando o modelo Whisper local.

    Args:
        audio_bytes: Conteúdo binário do arquivo de áudio.
        file_extension: Extensão do arquivo recebido do Telegram (padrão: 'ogg').

    Returns:
        Texto transcrito do áudio.

    Raises:
        RuntimeError: Se a transcrição falhar.
    """
    _ensure_ffmpeg_in_path()

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

        if not transcript:
            raise RuntimeError("Transcrição retornou texto vazio.")

        logger.info(f"Transcrição concluída: '{transcript[:80]}'")
        return transcript

    except RuntimeError:
        raise
    except Exception as exc:
        logger.error(f"Falha na transcrição do áudio: {exc}")
        raise RuntimeError(f"Não foi possível transcrever o áudio: {exc}") from exc
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
