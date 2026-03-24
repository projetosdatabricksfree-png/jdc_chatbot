from functools import lru_cache
from pathlib import Path
from loguru import logger

from src.config import settings


@lru_cache(maxsize=1)
def load_knowledge_base() -> str:
    """
    Carrega e armazena em cache o conteúdo da base de conhecimento do JDC.
    O arquivo é lido apenas uma vez durante o ciclo de vida da aplicação.
    """
    path: Path = settings.knowledge_base_path

    if not path.exists():
        raise FileNotFoundError(
            f"Base de conhecimento não encontrada: {path.resolve()}"
        )

    content = path.read_text(encoding="utf-8")
    logger.info(f"Base de conhecimento carregada: {path.name} ({len(content)} chars)")
    return content
