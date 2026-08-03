"""The shared fixture builders must reach what they claim to reach."""

from __future__ import annotations

from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.vocabulary.edges import CONCEPT_ROOTS
from tests import helpers

pytestmark = pytest.mark.runtime


def test_sync_file_verdicts_reaches_every_concept_root(tmp_path: Path) -> None:
    """fulltexts/ is a real concept root; the old hand-typed roster spelled it
    'fulltext' and the exists-continue swallowed the miss silently."""
    rels = [root.rstrip("/") + "/probe.md" for root in CONCEPT_ROOTS]
    for rel in rels:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\ntype: note\ntitle: probe\ncheck_status: checked\n---\nbody\n",
            encoding="utf-8",
        )

    helpers.sync_file_verdicts(tmp_path)

    for rel in rels:
        assert state.concept_check_status(tmp_path, rel) == "checked", rel
