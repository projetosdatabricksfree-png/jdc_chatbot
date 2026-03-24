from telegram import Update
from telegram.ext import ContextTypes

from src.llm.client import clear_history


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para o comando /start."""
    user = update.effective_user
    await update.message.reply_text(
        f"Olá, {user.first_name}! 👋\n\n"
        "Sou o assistente oficial do programa *Jornada das Conquistas (JDC)* — CAIXA Vida e Previdência.\n\n"
        "Estou disponível para todas as gerências da CVP e posso te ajudar com:\n\n"
        "📊 *Pontuação e blocos* — Geração de Valor, Protagonismo, Mobilizador\n"
        "🎯 *Metas* — mensais, acumuladas e anuais\n"
        "🧮 *Fórmulas e métricas* — como cada indicador é calculado\n"
        "📖 *Glossário* — Prestamista, ITDV, Port In/Out e mais\n"
        "❓ *FAQ* — as dúvidas mais comuns do programa\n\n"
        "Pode enviar sua dúvida por *texto* ou *áudio* 🎙️\n\n"
        "⚠️ Para dúvidas fora do JDC, a área *COTAT* da CVP pode te ajudar.\n\n"
        "_Use /help para ver todos os comandos disponíveis._",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para o comando /help."""
    await update.message.reply_text(
        "*Comandos disponíveis:*\n\n"
        "/start — Apresentação do assistente\n"
        "/help — Esta mensagem de ajuda\n"
        "/limpar — Limpa o histórico da sua conversa\n\n"
        "*Como usar:*\n"
        "Envie sua dúvida sobre o JDC por texto ou áudio.\n"
        "Para perguntas em campo, prefira o áudio — as respostas serão mais curtas e diretas.",
        parse_mode="Markdown",
    )


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para o comando /limpar — reseta o histórico do usuário."""
    user_id = update.effective_user.id
    clear_history(user_id)
    await update.message.reply_text(
        "Histórico limpo! Pode começar uma nova conversa. ✅"
    )
