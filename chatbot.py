from __future__ import annotations

from bot_core import get_or_create_bot

if __name__ == "__main__":
    bot, db_path, did_bootstrap = get_or_create_bot()
    if did_bootstrap:
        print(f"[init] Trained new model with seed data. DB: {db_path}")
    else:
        print(f"[init] Loaded existing model. DB: {db_path}")

    print("Type something to begin (press Ctrl+C to exit)...")
    while True:
        try:
            user_input = input("You: ")
            response = bot.get_response(user_input)
            print("Bot:", getattr(response, "text", str(response)))
        except (KeyboardInterrupt, EOFError, SystemExit):
            break
