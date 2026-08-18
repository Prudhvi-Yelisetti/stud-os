"""
Replaces Obsidian-style template placeholders in a template chapter's
title/content when it's used to create a new chapter (see
routers/notes.py's create_chapter_from_template and
routers/daily_notes.py).
"""
from datetime import datetime

PLACEHOLDERS = {
    "{{date}}": lambda now: now.strftime("%Y-%m-%d"),
    "{{time}}": lambda now: now.strftime("%H:%M"),
    "{{datetime}}": lambda now: now.strftime("%Y-%m-%d %H:%M"),
}


def interpolate(text: str, now: datetime | None = None) -> str:
    now = now or datetime.now()
    for placeholder, render in PLACEHOLDERS.items():
        if placeholder in text:
            text = text.replace(placeholder, render(now))
    return text
