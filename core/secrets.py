"""API keys live in the git-ignored .env file, never in app_config.json.

app_config.json is committed to a public repository, so every config
loader passes its dict through merge_secrets() to fill in the keys, and
every config writer passes it through strip_secrets() first, which moves
any key typed into the UI into .env and blanks it in the JSON.

.env accepts either format, one key per line:
    gemini_api_key=AIza...
    "gemini_api_key": "AIza...",
"""
import re
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

_LINE = re.compile(r'^\s*"?([A-Za-z0-9_]+)"?\s*[:=]\s*"?(.*?)"?\s*,?\s*$')


def _is_secret(key: str) -> bool:
    return key.endswith("_api_key")


def read_secrets() -> dict:
    secrets = {}
    try:
        text = ENV_PATH.read_text(encoding="utf-8")
    except Exception:
        return secrets
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = _LINE.match(line)
        if m:
            key, value = m.group(1).lower(), m.group(2).strip()
            if _is_secret(key) and value:
                secrets[key] = value
    return secrets


def merge_secrets(cfg: dict) -> dict:
    """Fill empty *_api_key fields in cfg from .env (in place; returns cfg)."""
    for key, value in read_secrets().items():
        if not (cfg.get(key) or "").strip():
            cfg[key] = value
    return cfg


def _write(secrets: dict):
    ENV_PATH.write_text(
        "".join(f"{k}={v}\n" for k, v in sorted(secrets.items())),
        encoding="utf-8",
    )


def strip_secrets(cfg: dict) -> dict:
    """Move non-empty keys from cfg into .env; return a copy safe to commit.

    An empty key in cfg never deletes anything from .env — a config loaded
    without its secrets must not wipe them on save. Use clear_secret().
    """
    clean = dict(cfg)
    secrets = read_secrets()
    changed = False
    for key in [k for k in cfg if _is_secret(k)]:
        value = (cfg.get(key) or "").strip()
        if value and secrets.get(key) != value:
            secrets[key] = value
            changed = True
        clean[key] = ""
    if changed:
        _write(secrets)
    return clean


def clear_secret(key: str):
    secrets = read_secrets()
    if secrets.pop(key, None) is not None:
        _write(secrets)
