from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

from flask import Flask, render_template, request, redirect, url_for, session, flash

# Ensure project root on sys.path for local runs (python webapp/app.py)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bot_core import get_or_create_bot

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

# Initialize bot
bot, db_path, did_bootstrap = get_or_create_bot()


@app.context_processor
def inject_globals():
    return {
        "db_path": db_path,
        "did_bootstrap": did_bootstrap,
    }


@app.route("/", methods=["GET"])
def index():
    messages: List[Dict[str, Any]] = session.get("messages", [])
    return render_template("index.html", messages=messages)


@app.route("/send", methods=["POST"])
def send():
    global bot
    text = (request.form.get("message") or "").strip()
    if not text:
        return redirect(url_for("index"))

    messages: List[Dict[str, Any]] = session.get("messages", [])
    messages.append({"role": "user", "content": text})

    response = bot.get_response(text)
    reply = getattr(response, "text", str(response))
    messages.append({"role": "assistant", "content": reply})

    session["messages"] = messages
    return redirect(url_for("index"))


@app.route("/clear", methods=["POST"])
def clear():
    session.pop("messages", None)
    return redirect(url_for("index"))


@app.route("/teach", methods=["POST"])
def teach():
    global bot
    q = (request.form.get("teach_q") or "").strip()
    a = (request.form.get("teach_a") or "").strip()
    if q and a:
        try:
            bot.train_pairs([(q, a)])
            flash("Trained on your example.", "success")
        except Exception as e:
            flash(f"Training failed: {e}", "error")
    return redirect(url_for("index"))


@app.route("/reset-db", methods=["POST"])
def reset_db():
    global bot, db_path, did_bootstrap
    try:
        p = Path(db_path)
        if p.exists():
            p.unlink()
        # Recreate bot, which will bootstrap with seed data
        bot, db_path, did_bootstrap = get_or_create_bot()
        session.pop("messages", None)
        flash("Database reset. Bot re-initialized with seed data.", "success")
    except Exception as e:
        flash(f"Failed to reset DB: {e}", "error")
    return redirect(url_for("index"))


if __name__ == "__main__":
    # Run development server
    app.run(host="127.0.0.1", port=8000, debug=False)
