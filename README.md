# Philosopher — Telegram Bot

A Telegram bot that helps users make decisions through structured philosophical thinking. It applies a 4-layer framework (existentialism, pragmatism, stoicism, real-world context) to any life problem and delivers clear, actionable guidance — not abstract philosophy.

## How It Works

1. User sends `/start` and picks a predefined problem or types their own.
2. The bot immediately generates a structured response using OpenAI (GPT-4o-mini).
3. The conversation continues — the bot deepens its analysis with each follow-up.

Every response follows a strict format:

| Block | Lens |
|---|---|
| 🧠 СМЫСЛ | Existentialism — values, choice, inner conflict |
| ⚙️ РЕЗУЛЬТАТ | Pragmatism — consequences, growth, benefit |
| 🧱 КОНТРОЛЬ | Stoicism — what you control vs. what you don't |
| 🌍 КОНТЕКСТ | Reality — constraints, environment, obligations |
| 💥 ВЫВОД | Clear recommendation or 2–3 options |
| 👉 СЛЕДУЮЩИЙ ШАГ | One concrete action to take right now |

## Bot Commands

| Command | Description |
|---|---|
| `/start` | Start a new conversation |
| `/reset` | Start over |
| `/clear` | Clear conversation history |
| `/existentialism` | Full reference text on existentialism |
| `/notifications` | Set up daily reminders |
| `/stats` | Analytics (admin only) |

## Project Structure

```
main.py                    — Bot logic, handlers, state management
texts.py                   — All user-facing strings and predefined problems
prompts.py                 — System prompt and framework for the LLM
llm.py                     — OpenAI API client (GPT-4o-mini)
existentialism_full_text.py — Long-form existentialism reference text
requirements.txt           — Python dependencies
```

## Setup

### Prerequisites

- Python 3.9+
- A Telegram bot token (from [@BotFather](https://t.me/BotFather))
- An OpenAI API key

### Installation

```bash
git clone <repo-url>
cd philosophy-tg-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

```
BOT_TOKEN=your-telegram-bot-token-here
OPENAI_API_KEY=your-openai-api-key-here
ADMIN_USER_ID=your-telegram-user-id-here
```

### Run

```bash
python3 main.py
```

## Features

- **Structured philosophical framework** — every answer follows a consistent 4-layer analysis
- **Predefined problem topics** — quick-start buttons for common life situations (career, burnout, relationships, motivation, etc.)
- **Free-text input** — users can describe any problem in their own words
- **Conversation memory** — the bot tracks context across multiple turns (up to 5 messages)
- **Conversation phases** — challenge → reflection → closure → help, adapting tone and depth
- **Help mode** — activates when the user is stuck or explicitly asks for help
- **Daily notifications** — configurable reminders with timezone support
- **Rate limiting** — per-user daily limits and minimum interval between messages
- **Admin analytics** — `/stats` command for usage metrics

## Tech Stack

- [aiogram 3](https://docs.aiogram.dev/) — async Telegram bot framework
- [OpenAI API](https://platform.openai.com/) — GPT-4o-mini for response generation
- Python 3.9+ with asyncio
