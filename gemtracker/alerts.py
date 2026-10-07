"""Send alerts to Telegram and/or Discord (whichever is configured)."""
from __future__ import annotations

import html

from . import config, net


def enabled() -> bool:
    return bool((config.env("TELEGRAM_BOT_TOKEN") and config.env("TELEGRAM_CHAT_ID"))
                or config.env("DISCORD_WEBHOOK_URL"))


def send(lines: list, log=print) -> None:
    """`lines` is a list of (text, url or None); rendered with links per channel."""
    token, chat = config.env("TELEGRAM_BOT_TOKEN"), config.env("TELEGRAM_CHAT_ID")
    if token and chat:
        text = "\n".join(f'<a href="{html.escape(url)}">{html.escape(t)}</a>' if url else html.escape(t)
                         for t, url in lines)
        try:
            net.post_json(f"https://api.telegram.org/bot{token}/sendMessage",
                          {"chat_id": chat, "text": text, "parse_mode": "HTML",
                           "disable_web_page_preview": True})
        except Exception as exc:
            log(f"   Telegram alert failed: {exc}")
    hook = config.env("DISCORD_WEBHOOK_URL")
    if hook:
        text = "\n".join(f"[{t}](<{url}>)" if url else t for t, url in lines)
        try:
            net.post_json(hook, {"content": text[:1900]}, as_json=False)
        except Exception as exc:
            log(f"   Discord alert failed: {exc}")
