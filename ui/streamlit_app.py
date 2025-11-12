from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from bot_core import get_or_create_bot, DB_ENV_VAR, READ_ONLY_ENV_VAR

st.set_page_config(page_title="SupportBot", page_icon="💬", layout="centered")

st.title("💬 SupportBot")

# Initialize bot (and bootstrap if DB is new)
bot, db_path, did_bootstrap = get_or_create_bot()

# Sidebar controls
with st.sidebar:
    st.header("Settings")
    st.caption("Environment variables")
    st.code(
        f"{DB_ENV_VAR}={db_path}\n{READ_ONLY_ENV_VAR}={os.getenv(READ_ONLY_ENV_VAR) or 'false'}",
        language="bash",
    )

    if st.button("Clear conversation", type="secondary"):
        st.session_state.pop("messages", None)
        st.rerun()

    if st.button("Reset training (delete DB)", type="secondary"):
        try:
            p = Path(db_path)
            if p.exists():
                p.unlink()
            st.session_state.pop("messages", None)
            st.success("Database deleted. Restart the app to re-bootstrap.")
        except Exception as e:
            st.error(f"Failed to delete DB: {e}")

# Init chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Show init status
if did_bootstrap:
    st.info(f"New knowledge base created at {db_path} and bootstrapped with seed data.")
else:
    st.caption(f"Using database: {db_path}")

# Display history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask me anything"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get bot response
    response = bot.get_response(prompt)
    bot_text = getattr(response, "text", str(response))

    with st.chat_message("assistant"):
        st.markdown(bot_text)
    st.session_state["messages"].append({"role": "assistant", "content": bot_text})

# Simple teaching tool
with st.expander("Teach the bot a new Q/A pair"):
    q = st.text_input("User says")
    a = st.text_input("Bot should reply")
    col1, col2 = st.columns([1, 4])
    with col1:
        do_train = st.button("Train", disabled=not (q and a))
    if do_train:
        try:
            # Train a single pair
            bot.train_pairs([(q, a)])
            st.success("Trained on your example.")
        except Exception as e:
            st.error(f"Training failed: {e}")
