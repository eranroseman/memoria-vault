"""Conversational-ask grounding-contract tests (U4 §4)."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from memoria_vault.product import copi_conversational_ask
from memoria_vault.product.copi_conversational_ask import (
    PRIORS_REFUSAL,
    conversational_ask_section,
)
from memoria_vault.runtime import retrieval_pipeline
from tests.helpers import ROOT


def _string_constants(path: Path) -> list[str]:
    """Every string constant a module carries, implicit concatenation already joined.

    Reading the parsed constants rather than the raw text is what makes the
    single-source scan below catch a copy-pasted multi-line assignment: the
    wrapped source lines never contain the joined sentence, but the parsed
    constant does.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]


def _flat(text: str) -> str:
    """Collapse the markdown's cosmetic line wrapping so sentence pins survive a reflow."""
    return " ".join(text.split())


def test_priors_refusal_is_defined_in_exactly_one_module_under_src() -> None:
    """Contract 7's single-source scan: retyping the refusal anywhere under `src/` fails.

    The needle is the imported constant, never a literal this file spells out,
    so the scan cannot pass by agreeing with itself. The expected carrier is the
    defining module's own `__file__`, so moving the constant moves the pin with it.
    """
    definer = Path(copi_conversational_ask.__file__).resolve()
    carriers = sorted(
        path.resolve()
        for path in (ROOT / "src").rglob("*.py")
        if any(PRIORS_REFUSAL in constant for constant in _string_constants(path))
    )

    assert carriers == [definer]


def test_section_scripts_the_priors_refusal_verbatim() -> None:
    """Strict, unflattened: the refusal must be quotable as the one blockquote line it is."""
    assert PRIORS_REFUSAL in conversational_ask_section()


def test_section_routes_retrieval_empty_to_the_payload_unknowns() -> None:
    text = _flat(conversational_ask_section())

    assert "say the payload's `unknowns[0]` string exactly as it arrived" in text
    assert "do not re-derive those numbers" in text


def test_section_carries_no_fillable_honest_empty_template() -> None:
    """The engine renders honest-empty per query; a quotable template invites invented counts."""
    stages = retrieval_pipeline.PipelineStages(40)
    stages.add_ranked(0)
    stages.add_returned(0)
    rendered = retrieval_pipeline.honest_empty(
        stages.rows(), retrieval_pipeline.excluded_strata(unchecked=12)
    )
    skeleton = [part for part in re.split(r"\d+", rendered) if len(part.strip()) > 8]
    assert skeleton, f"honest-empty wording has no count-free text to look for: {rendered!r}"

    text = _flat(conversational_ask_section())

    assert [part for part in skeleton if part.strip() in text] == []


def test_section_states_the_grounding_rules() -> None:
    section = conversational_ask_section()
    text = _flat(section)

    assert section.startswith("## Conversational ask — grounding contract")
    assert "`operation_run` with operation id `answer-query`" in text
    assert "Never answer a vault-content question from your own prior knowledge." in text
    assert "Rephrasing is allowed; additions are forbidden." in text
    assert "Every claim carries its source ref." in text
    assert "dropped, not voiced" in text
    assert "Citation-correct is not grounded, and grounded is not true." in text
