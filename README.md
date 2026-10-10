# Fluxary — Financial Assistant

English | [Português (Brasil)](README.pt-BR.md)

Fluxary is a Python Telegram bot for recording personal income and expenses,
automatically categorizing transactions with the Hugging Face Inference API,
and viewing financial summaries backed by SQLAlchemy.

## Features

- Record income and expenses from natural-language messages.
- Categorize transactions with Hugging Face AI and keyword-based fallbacks.
- Review current-month, weekly, monthly, and category-based reports.
- Persist transactions and account balances in PostgreSQL.

## Technology

Python 3.10+, `python-telegram-bot`, SQLAlchemy, PostgreSQL, Hugging Face
Inference API, and pytest.

## Project layout

| Path | Purpose |
| --- | --- |
| `main.py` | Application entry point |
| `src/ai/` | AI transaction categorization |
| `src/commands/` | Telegram commands and message handlers |
| `src/models/` | SQLAlchemy models and database setup |
| `src/services/` | Financial report generation |
| `src/utils/` | Parsing, formatting, and encryption helpers |
| `tests/` | Automated unit and integration-style tests |

## Setup

1. Install Python 3.10 or newer and PostgreSQL.
2. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install project dependencies:

   ```shell
   python -m pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and set your Telegram bot token, PostgreSQL
   connection string, and (optionally) Hugging Face API token. Keep `.env`
   private; it is excluded from Git.
5. Start the bot:

   ```shell
   python main.py
   ```

The bot requires a valid `BOT_TOKEN` and a reachable database to start. When
the Hugging Face token is missing or the API is unavailable, categorization
falls back to local keyword rules.

## Environment variables

Copy `.env.example` to `.env` and replace the example values with your own.
Never commit `.env` or share its secret values.

| Variable | Purpose | Requirement |
| --- | --- | --- |
| `BOT_TOKEN` | Telegram bot authentication token | Required |
| `DB_URI` | SQLAlchemy database connection URI | Required; defaults to local PostgreSQL |
| `HF_API_TOKEN` | Hugging Face Inference API token | Optional; keyword fallback is used without it |
| `ENCRYPTION_KEY` | Key for the encryption helper | Optional |
| `DEBUG` | Enables the project's debug configuration flag | Optional; defaults to `False` |
| `LOG_LEVEL` | Logging threshold: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` | Optional; defaults to `INFO` |

## Tests

Install the development and runtime dependencies with
`python -m pip install -r requirements.txt` (pytest is included), then run:

```shell
python -m pytest
```

The automated suite covers transaction categorization with a mocked Hugging
Face API (including timeouts and malformed responses), message parsing,
income/expense registration against in-memory SQLite, and the calculations
and formatting of weekly, monthly, and category reports. Tests do not require
Telegram or Hugging Face credentials, network access, or PostgreSQL.

## Demonstration

![Fluxary Telegram bot demonstration](contacerta.gif)
