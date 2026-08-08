"""
Explicit, deterministic resolution of the .env file's location -- and a
safe way to add/update/remove a single KEY=value line in it without
disturbing anything else already in the file (comments, ordering, other
keys).

Deliberately NOT relying on python-dotenv's own auto-discovery. Tested
directly against this repo during dev and it found nothing at all (no
.env exists here yet, and find_dotenv()'s search came up empty even
from the repo root) -- too easy to get wrong silently, especially now
that this module also *writes* to the file, not just reads it. Anchored
to a real, explicit path instead, same "don't trust ambient discovery"
reasoning as session.py's DB path.

Resolution mirrors how DATABASE_URL already works for the packaged app:
- ENV_FILE_PATH env var, if set (AppRun sets this to the writable data
  dir for the packaged app, since the AppImage's own tree is read-only
  and can't be written back into)
- otherwise, the repo root next to the backend/ package (dev default,
  where .env / .env.example already live)
"""
import os
import re
from pathlib import Path


def _resolve_env_file() -> Path:
    return Path(os.environ.get("ENV_FILE_PATH") or (Path(__file__).resolve().parent.parent.parent / ".env"))


# Snapshotted once, for main.py's one-time load_dotenv() call at process
# startup -- that's supposed to stay fixed for the process's lifetime.
ENV_FILE = _resolve_env_file()


def upsert_key(key: str, value: str | None) -> None:
    """Set KEY=value in the .env file, or remove that line entirely if
    value is empty/None. Every other line is left untouched -- this
    reads the whole file, replaces or drops just the one matching line,
    and writes it back, rather than a blind append (which would leave
    stale duplicate lines behind on every update).

    Also updates os.environ directly, so the change is live immediately
    for the running process -- no restart needed, same as how .env is
    only ever read once at startup otherwise.

    Re-resolves the env file path fresh on every call (unlike ENV_FILE
    above) rather than using the startup snapshot -- this is also what
    lets tests point ENV_FILE_PATH at a throwaway temp file via
    monkeypatch without needing to reload/reimport anything, so nothing
    here can ever touch the real repo .env during a test run.
    """
    env_file = _resolve_env_file()
    lines = env_file.read_text().splitlines() if env_file.exists() else []
    pattern = re.compile(rf"^{re.escape(key)}=")
    kept_lines = [line for line in lines if not pattern.match(line)]

    value = (value or "").strip()
    if value:
        kept_lines.append(f"{key}={value}")
        os.environ[key] = value
    else:
        os.environ.pop(key, None)

    env_file.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(kept_lines)
    env_file.write_text(content + "\n" if content else "")
