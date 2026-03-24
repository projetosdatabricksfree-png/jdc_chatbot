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


# Mapeamento de emojis → expressões em português para TTS.
#
# Princípio: apenas emojis que adicionam informação NOVA ao texto
# recebem uma expressão. Todos os outros são removidos silenciosamente,
# pois o modelo Claude já escreve a emoção em palavras e usa o emoji
# como decoração visual — evitando duplicações como "Ótimo! Ótimo!".
#
# Emojis que adicionam informação nova:
#   ⚠️  → "Atenção:" (sinaliza alerta antes de uma frase)
#   ❌  → "Não." (negação explícita, reforça o sentido)
#
_EMOJI_TO_EXPRESSION: dict[str, str] = {
    "⚠": "Atenção:",    # U+26A0 — núcleo de ⚠️ (com variation selector \uFE0F)
    "🚨": "Importante:",
    "❗": "Atenção!",
    "❌": "Não.",
    "😔": "Infelizmente,",
    "😕": "Infelizmente,",
}

# Regex universal que captura qualquer emoji Unicode
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"   # Misc symbols, pictographs, emoticons, transport
    "\U00002702-\U000027B0"   # Dingbats
    "\U000024C2-\U0001F251"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\u2600-\u26FF"           # Misc symbols (☀ ⚠ ✅ ❌ ❓ ℹ️ ...)
    "\u2700-\u27BF"
    "\uFE00-\uFE0F"           # Variation selectors (parte de emojis compostos)
    "\U0001F1E0-\U0001F1FF"   # Flags
    "]+",
    flags=re.UNICODE,
)


def _replace_emoji(match: re.Match) -> str:
    """Substitui emoji por expressão mapeada ou string vazia."""
    emoji = match.group(0)
    # Tenta cada caractere do match individualmente (emojis compostos)
    for char in emoji:
        if char in _EMOJI_TO_EXPRESSION:
            expr = _EMOJI_TO_EXPRESSION[char]
            return f" {expr} " if expr else " "
    return " "


def prepare_for_tts(text: str) -> str:
    """
    Prepara o texto para síntese de voz:
    1. Remove formatação Markdown
    2. Substitui emojis reativos por expressões em português
    3. Remove emojis decorativos silenciosamente
    4. Normaliza espaços e pontuação
    """
    # Remove Markdown
    text = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"_{1,2}(.+?)_{1,2}", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"`{1,3}[^`]*`{1,3}", "", text)
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)

    # Substitui emojis (mapeados → expressão | não mapeados → vazio)
    text = _EMOJI_RE.sub(_replace_emoji, text)

    # Remove duplicatas consecutivas geradas quando modelo escreve
    # tanto o emoji quanto a palavra (ex: "Atenção: Atenção:")
    _EXPRESSION_WORDS = r"(Aten[çc][aã]o[:]?|Importante[:]?|N[aã]o[.]?|Infelizmente[,]?)"
    text = re.sub(
        rf"{_EXPRESSION_WORDS}\s+{_EXPRESSION_WORDS}",
        r"\1",
        text,
        flags=re.IGNORECASE,
    )

    # Remove espaços antes de pontuação (gerados quando emoji precede ".")
    text = re.sub(r" +([.,!?:;])", r"\1", text)
    # Normaliza espaços e remove linhas em branco excessivas
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

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
    clean_text = prepare_for_tts(text)
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
