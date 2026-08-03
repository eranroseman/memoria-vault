"""Reader for `.memoria/config/attention.yaml` (I1 spec §6): ordering and throttles.

One config file carries both PI-owned knobs over the attention queue: `order_by:`
reorders or drops the ranking factors vault-wide, and `producers:` throttles a
single producer to `quiet` or `paused`. Both are PI acts on an inspectable file --
nothing in the runtime writes this file, and no automatic throttle exists (the
`attention-throttle` decision rule *recommends* only).

Every read fails safe. A missing file, unreadable YAML, a mapping where a list
belongs, or an unknown factor or mode all resolve to the shipped default rather
than raising: a config typo must not be able to take the queue down, and the
default is the behaviour the spec ratified.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ATTENTION_CONFIG = ".memoria/config/attention.yaml"

# The default factor order (I1 spec §6.2). The `block` pin is deliberately absent:
# it is not a factor, so it can be neither reordered nor dropped, and
# `engine.api._order_key` applies it outside this tuple.
DEFAULT_ORDER_BY: tuple[str, ...] = ("priority", "loudness", "impact", "staleness", "age")
ORDER_FACTORS = frozenset(DEFAULT_ORDER_BY)
PRODUCER_MODES = frozenset({"active", "quiet", "paused"})


def attention_order_by(vault: Path) -> tuple[str, ...]:
    """The configured factor order, or the default when unset or unusable."""
    return normalize_order_by(_load(vault).get("order_by") or ())


def normalize_order_by(factors: Any) -> tuple[str, ...]:
    """Keep the known factors in the given order; fall back to the default if none survive.

    The one normalizer for both fronts -- the config file and the per-invocation
    `--order-by` flag -- so a factor name the file may drop cannot mean something
    different when the flag spells it.

    A sequence or nothing: `order_by:` written as a scalar, a mapping, or a
    number is a config mistake, not a one-element order, and reading it as one
    would silently rank on whatever the value happened to iterate into.
    """
    if not isinstance(factors, (list, tuple)):
        return DEFAULT_ORDER_BY
    picked = tuple(
        factor for factor in factors if isinstance(factor, str) and factor in ORDER_FACTORS
    )
    return picked or DEFAULT_ORDER_BY


def producer_mode(vault: Path, raised_by: str) -> str:
    """`active | quiet | paused` for one producer. Absent or unknown reads as active."""
    producers = _load(vault).get("producers")
    mode = producers.get(raised_by) if isinstance(producers, dict) else None
    return mode if mode in PRODUCER_MODES else "active"


def _load(vault: Path) -> dict[str, Any]:
    path = Path(vault) / ATTENTION_CONFIG
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}
