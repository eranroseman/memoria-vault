"""L1 component tests for adr_code_doctor."""

import adr_code_doctor as _m


def _write(root, rel, text="ok"):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _minimal_clean_root(tmp_path):
    for item in _m.CHECKS:
        _write(tmp_path, item.adr, "\n".join(item.required_text) + "\n")
        for rel in item.required_paths:
            _write(tmp_path, rel)
    return tmp_path


def test_check_accepts_current_mechanism_claims(tmp_path):
    root = _minimal_clean_root(tmp_path)

    assert _m.check(root) == []


def test_check_flags_missing_mechanism_and_stale_claim(tmp_path):
    root = _minimal_clean_root(tmp_path)
    (root / "src/memoria_vault/runtime/policy/decision.py").unlink()
    adr41 = root / "docs/adr/41-configurable-review-gate-mode.md"
    adr41.write_text(
        adr41.read_text(encoding="utf-8")
        + "\nThe old dispatch refuses to advance a card wording is stale.\n",
        encoding="utf-8",
    )

    errors = _m.check(root)

    assert any(
        "ADR-41" in error and "src/memoria_vault/runtime/policy/decision.py" in error
        for error in errors
    )
    assert any(
        "ADR-41" in error and "dispatch refuses to advance a card" in error for error in errors
    )
