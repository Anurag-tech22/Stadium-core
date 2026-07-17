"""Input sanitization. Runs before ANY user text touches the context
engine or the LLM. This is the first stop for the injection-resistance
guarantee documented in the README."""

from __future__ import annotations

import bleach

MAX_LEN = 500


def sanitize_text(raw: str) -> str:
    cleaned = bleach.clean(raw, tags=[], attributes={}, strip=True)
    # Mitigate potential SQL comment injections and query chaining
    cleaned = cleaned.replace(";", "").replace("--", "")
    # Mitigate command injection escape and piping characters
    cleaned = cleaned.replace("|", "").replace("&", "").replace("$", "").replace("`", "")
    cleaned = " ".join(cleaned.split())  # collapse whitespace
    return cleaned[:MAX_LEN]
