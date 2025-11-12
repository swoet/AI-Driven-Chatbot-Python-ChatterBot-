from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root on sys.path for `uvicorn fastapi_app.main:app`
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from bot_core import get_or_create_bot

app = FastAPI()

# Static and templates
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Initialize bot (shared single instance)
bot, db_path, did_bootstrap = get_or_create_bot()


@app.get("/healthz")
def healthz():
    return PlainTextResponse("ok")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "db_path": db_path,
            "did_bootstrap": did_bootstrap,
        },
    )


@app.post("/send", response_class=HTMLResponse)
def send(message: str = Form(...)):
    # Return an HTML snippet that HTMX appends to the chat
    user_html = (
        f'<div class="msg user"><div class="role">You</div>'
        f'<div class="bubble">{escape_html(message)}</div></div>'
    )
    reply_obj = bot.get_response(message)
    reply = getattr(reply_obj, "text", str(reply_obj))
    bot_html = (
        f'<div class="msg assistant"><div class="role">Bot</div>'
        f'<div class="bubble">{escape_html(reply)}</div></div>'
    )
    return HTMLResponse(user_html + bot_html)


@app.post("/teach", response_class=HTMLResponse)
def teach(teach_q: str = Form(""), teach_a: str = Form("")):
    if teach_q and teach_a:
        try:
            bot.train_pairs([(teach_q, teach_a)])
            return HTMLResponse('<li class="success">Trained on your example.</li>')
        except Exception as e:
            return HTMLResponse(f'<li class="error">Training failed: {escape_html(str(e))}</li>')
    return HTMLResponse('<li class="error">Both fields are required.</li>')


@app.post("/reset-db", response_class=HTMLResponse)
def reset_db():
    global bot, db_path, did_bootstrap
    try:
        p = Path(db_path)
        if p.exists():
            p.unlink()
        bot, db_path, did_bootstrap = get_or_create_bot()
        return HTMLResponse('<li class="success">Database reset. Bot re-initialized with seed data.</li>')
    except Exception as e:
        return HTMLResponse(f'<li class="error">Failed to reset DB: {escape_html(str(e))}</li>')


@app.post("/clear", response_class=HTMLResponse)
def clear():
    # Signal the client to clear chat; we return empty content
    return HTMLResponse("")


# Utilities

def escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
