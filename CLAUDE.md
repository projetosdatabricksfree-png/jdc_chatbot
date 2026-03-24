# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Visão Executiva do Projeto

O **JDC Chatbot** é um assistente conversacional de inteligência artificial desenvolvido para a **CAIXA Vida e Previdência (CVP)**, com foco operacional no suporte aos **Consultores Comerciais do segmento #VAREJO**. O sistema provê acesso imediato — via **Telegram** (e futuramente WhatsApp) — às regras, métricas, estrutura de pontuação e glossário do programa de performance **Jornada das Conquistas (JDC)**.

O objetivo estratégico é reduzir a dependência de supervisores para dúvidas operacionais de rotina, aumentar a produtividade dos consultores em campo e garantir uniformidade no acesso às informações do programa — 24 horas por dia, 7 dias por semana.

---

## Domínio de Negócio — Jornada das Conquistas (JDC)

### Estrutura de Pontuação

O JDC avalia o desempenho dos consultores por meio de **3 blocos mensais**:

| Bloco | Peso Mensal | Natureza |
|---|---|---|
| 🔵 Geração de Valor | 70 pontos | Base obrigatória |
| 🟦 Protagonismo | 30 pontos | Base obrigatória |
| 🟢 Mobilizador | até +10 pontos | Adicional / upgrade |

- **Meta anual:** 1.200 pontos → média de **100 pts/mês** (110 com Mobilizador)
- A pontuação mensal **não é zerada** no Acumulado — é progressiva ao longo do ano

### Bloco Geração de Valor (70 pts) — Sub Blocos

| Sub Bloco | Pontos | Status da Base |
|---|---|---|
| OKR | 34 pts | ⚠️ Pendente de conteúdo oficial |
| Acumulado | 20 pts | ✅ Documentado |
| Mensal | 16 pts | ✅ Documentado |
| Proteção à Vida | 7 pts | ⚠️ Pendente de conteúdo oficial |

### Bloco Protagonismo (30 pts) — Sub Blocos

| Sub Bloco | Pontos | Status da Base |
|---|---|---|
| Portabilidade (Port In/Out em UN e R$) | 15 pts | ⚠️ Pendente de conteúdo oficial |
| Protagonismo (Dispersão, ITDV) | 15 pts | ⚠️ Pendente de conteúdo oficial |

### Regra crítica de comportamento do LLM

O sistema **nunca deve inventar** métricas, metas ou regras que não estejam documentadas na base de conhecimento. Quando o conteúdo oficial de um sub bloco ainda não estiver disponível (ver seção Pendências abaixo), o LLM deve responder:

> *"Essa informação ainda não está na minha base de conhecimento. Consulte o material oficial do programa ou entre em contato com o seu gestor."*

---

## Arquitetura do Sistema

```
Consultor (campo — smartphone)
        │
        ├── Mensagem de Texto ──────────────────────────────────┐
        │                                                       │
        └── Mensagem de Voz (OGG/OPUS) ──► Whisper AI          │
                                          (Transcrição local)   │
                                                                ▼
                                               Telegram Bot API
                                                                │
                                                                ▼
                                           Orquestrador Python (async)
                                           python-telegram-bot v20
                                                                │
                                           ┌────────────────────┤
                                           │                    │
                                    Detecção de           Base de Conhecimento
                                    Modalidade            JORNADA_CONQUISTAS_
                                   (voz / texto)          LLM_BASE.md
                                           │                    │
                                           └─────────┬──────────┘
                                                     │
                                                     ▼
                                          Claude API — Anthropic
                                          (claude-sonnet-4-6)
                                          System Prompt adaptado
                                          por modalidade de entrada
                                                     │
                                                     ▼
                                          Resposta formatada
                                          entregue ao consultor
```

### Adaptação por modalidade de entrada

| Modalidade | Formato da resposta | Uso de tabelas | Tom |
|---|---|---|---|
| Texto | Completo, estruturado | Permitido | Profissional e direto |
| Voz (áudio transcrito) | Até 3 parágrafos curtos | Substituído por listas | Oral e acolhedor |

---

## Estrutura do Repositório

```
JDC_CHATBOT/
├── main.py                          # Ponto de entrada da aplicação
├── requirements.txt                 # Dependências Python
├── .env.example                     # Template de variáveis de ambiente
├── .env                             # Secrets locais (NÃO versionado)
├── .gitignore
├── CLAUDE.md                        # Este arquivo
├── JORNADA_CONQUISTAS_LLM_BASE.md   # Base de conhecimento do JDC
│
└── src/
    ├── config.py                    # Configurações centralizadas (pydantic-settings)
    ├── bot/
    │   ├── application.py           # Setup e inicialização do bot Telegram
    │   └── handlers/
    │       ├── commands.py          # Handlers de comandos (/start, /help)
    │       ├── text_handler.py      # Processamento de mensagens de texto
    │       └── voice_handler.py     # Processamento de mensagens de voz
    ├── llm/
    │   ├── client.py                # Cliente assíncrono da API Claude (Anthropic)
    │   └── prompts.py               # Construção de system prompts por modalidade
    ├── transcription/
    │   └── whisper_client.py        # Transcrição de áudio via Whisper (OpenAI)
    └── knowledge/
        └── loader.py                # Carregamento e cache da base de conhecimento
```

---

## Stack Tecnológica

| Componente | Tecnologia | Versão |
|---|---|---|
| Runtime | Python | 3.11+ |
| Telegram Bot | python-telegram-bot | 20.x (async) |
| LLM | Anthropic Claude | claude-sonnet-4-6 |
| Transcrição de voz | OpenAI Whisper | local (modelo `base`) |
| Configurações | pydantic-settings | 2.x |
| Conversão de áudio | pydub + ffmpeg | sistema |
| Logging | loguru | 0.7.x |

---

## Comandos de Desenvolvimento

### Instalação

```bash
# Criar e ativar ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# Instalar dependências
pip install -r requirements.txt
```

> **Pré-requisito:** `ffmpeg` deve estar instalado no sistema para conversão de áudio.
> Windows: `winget install ffmpeg` ou via [ffmpeg.org](https://ffmpeg.org)

### Configurar variáveis de ambiente

```bash
cp .env.example .env
# Editar .env com os tokens reais
```

### Executar o bot

```bash
python main.py
```

### Executar em background (produção)

```bash
nohup python main.py > logs/bot.log 2>&1 &
```

---

## Variáveis de Ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `TELEGRAM_TOKEN` | ✅ | Token do bot obtido via BotFather |
| `ANTHROPIC_API_KEY` | ✅ | Chave de API da Anthropic |
| `CLAUDE_MODEL` | Não | Modelo Claude a usar (default: `claude-sonnet-4-6`) |
| `WHISPER_MODEL` | Não | Tamanho do modelo Whisper: `tiny`, `base`, `small` (default: `base`) |
| `MAX_HISTORY_MESSAGES` | Não | Mensagens de histórico por usuário (default: `10`) |
| `LOG_LEVEL` | Não | Nível de log: `DEBUG`, `INFO`, `WARNING` (default: `INFO`) |

---

## Arquivo Central da Base de Conhecimento

`JORNADA_CONQUISTAS_LLM_BASE.md` é a **fonte da verdade** do sistema. Toda alteração nas regras, métricas ou glossário do JDC deve ser feita exclusivamente neste arquivo. O conteúdo é carregado em memória na inicialização e injetado no system prompt de cada interação com o Claude.

### Seções pendentes de conteúdo oficial

Os seguintes sub blocos ainda aguardam publicação oficial pela CVP e **não possuem detalhamento** na base de conhecimento atual:

- Sub bloco **OKR** (34 pts — maior peso do JDC)
- Sub bloco **Mobilizador / Escola de Negócios**
- Sub bloco **Portabilidade** (Port In / Port Out)
- Sub bloco **Protagonismo** (Dispersão, ITDV)
- Sub bloco **Proteção à Vida**
- Regras de ativação do Mobilizador
- Painéis de acompanhamento

---

## Histórico de Conversa

O sistema mantém histórico de contexto **por usuário** em memória (não persistido entre reinicializações). O limite padrão é de 10 mensagens por sessão, configurável via `MAX_HISTORY_MESSAGES`. Isso permite que o consultor faça perguntas de acompanhamento sem repetir o contexto.

---

## Fluxo de Processamento de Voz

1. Telegram entrega mensagem de voz no formato **OGG/OPUS**
2. O arquivo é baixado para um diretório temporário (`/tmp`)
3. O **Whisper** (modelo `base`, ~150MB, download único) transcreve o áudio para texto
4. O texto transcrito é enviado ao Claude com **system prompt no modo voz** (respostas curtas)
5. A resposta retorna ao consultor como **mensagem de texto** no Telegram

---

## Considerações de Segurança

- Tokens e chaves de API armazenados **exclusivamente no `.env`** local
- `.env` listado no `.gitignore` — **nunca versionado**
- Não há armazenamento de dados dos consultores em banco de dados
- Histórico de conversa mantido apenas em memória volátil
