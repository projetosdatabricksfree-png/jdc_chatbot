from collections import defaultdict, deque
from typing import Deque

import anthropic
from loguru import logger

from src.config import settings
from src.llm.prompts import build_system_prompt

# Histórico de conversa por user_id (em memória, não persistido)
_conversation_history: dict[int, Deque[dict]] = defaultdict(
    lambda: deque(maxlen=settings.max_history_messages)
)

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _get_history(user_id: int) -> list[dict]:
    return list(_conversation_history[user_id])


def _append_to_history(user_id: int, role: str, content: str) -> None:
    _conversation_history[user_id].append({"role": role, "content": content})


def clear_history(user_id: int) -> None:
    _conversation_history[user_id].clear()
    logger.debug(f"Histórico limpo para user_id={user_id}")


async def ask_claude(
    user_id: int,
    user_message: str,
    voice_mode: bool = False,
) -> str:
    """
    Envia uma mensagem ao Claude mantendo o histórico de conversa do usuário.

    Args:
        user_id: Identificador único do usuário no Telegram.
        user_message: Texto da pergunta do consultor.
        voice_mode: True quando a mensagem originou de um áudio transcrito.

    Returns:
        Texto da resposta gerada pelo Claude.
    """
    _append_to_history(user_id, "user", user_message)

    messages = _get_history(user_id)
    system_prompt = build_system_prompt(voice_mode=voice_mode)

    logger.info(
        f"[LLM] user_id={user_id} | mode={'voice' if voice_mode else 'text'} "
        f"| history_len={len(messages)}"
    )

    response = _client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
    )

    reply = response.content[0].text
    _append_to_history(user_id, "assistant", reply)

    logger.debug(f"[LLM] Resposta gerada ({len(reply)} chars)")
    return reply
