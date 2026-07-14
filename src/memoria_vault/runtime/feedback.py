"""Shadow-first discipline flag for I1 feedback instrumentation."""

from __future__ import annotations

from pathlib import Path

import yaml

FEEDBACK_CONFIG = ".memoria/config/feedback.yaml"


def feedback_production_enabled(vault: Path) -> bool:
    """Return True only when feedback.yaml explicitly sets production_enabled: true.

    Gates *acting* on the signal, never recording. Fails safe to False on an
    absent, unreadable, malformed, or key-missing config.
    """
    path = Path(vault) / FEEDBACK_CONFIG
    if not path.is_file():
        return False
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return False
    if not isinstance(data, dict):
        return False
    return data.get("production_enabled") is True
