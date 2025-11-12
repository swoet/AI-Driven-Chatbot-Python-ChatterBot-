# AI-Driven Chatbot (Python + ChatterBot)

This project provides a minimal ChatterBot-based assistant with:
- Persistent SQLite storage (no data loss across runs)
- A simple CLI
- A clean Flask web UI with chat history, reset, and on-the-fly teaching

## Quick start

1) Create a virtual environment (recommended)

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# or CMD
.\.venv\Scripts\activate.bat
```

2) Install dependencies

```bash
pip install -r requirements.txt
```

3) Run the CLI

```bash
python chatbot.py
```

4) Run the web UI

```bash
python webapp/app.py
# then open http://127.0.0.1:8000
```

The first run will create a local SQLite database (default: `database.sqlite3`). The CLI and UI will then share the same knowledge base.

## Configuration

You can set these environment variables:

- `CHATBOT_DB_PATH` – Path to the SQLite database file (default: `./database.sqlite3`).
- `CHATBOT_READ_ONLY` – If `true`, disables training (default: `false`).

Example (PowerShell):

```powershell
$env:CHATBOT_DB_PATH = "C:\\path\\to\\mydb.sqlite3"
$env:CHATBOT_READ_ONLY = "true"
```

## Notes on ChatterBot versions

ChatterBot’s older releases have compatibility constraints with SQLAlchemy. This project pins `SQLAlchemy<1.4` for safety. If you already have a working combination, you can adjust `requirements.txt` accordingly.

## UI/UX

- Flask chat interface with clean layout and styles
- Conversation history (per browser session)
- Controls to clear chat and reset training (deletes DB)
- Simple “Teach the bot” panel for quick Q/A fine-tuning

## Project structure

- `chatbot.py` – CLI entrypoint
- `bot_core.py` – Bot configuration and bootstrap training (SQLite + difflib)
- `webapp/app.py` – Flask web UI
- `webapp/templates/` and `webapp/static/` – UI templates and styles

## Roadmap ideas

- Add corpus-based training flows
- Export/import knowledge base snapshots
- Unit tests, linting (ruff), and pre-commit hooks
- Optional FastAPI + HTMX web UI for production deployment
- Optional Streamlit UI (add back `streamlit` to requirements if your Python supports prebuilt `pyarrow` wheels)
