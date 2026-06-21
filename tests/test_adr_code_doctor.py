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
    (root / "memoria/runtime/policy/decision.py").unlink()
    adr55 = root / "docs/adr/55-src-scaffold-populate-golden-copy.md"
    adr55.write_text(
        adr55.read_text(encoding="utf-8")
        + "\nThe golden-copy update path is resolved by the three-way reconcile in "
        "`golden_restore.py upgrade --source SRC --apply`.\n",
        encoding="utf-8",
    )

    errors = _m.check(root)

    assert any(
        "ADR-76" in error and "memoria/runtime/policy/decision.py" in error for error in errors
    )
    assert any(
        "ADR-55" in error and "golden_restore.py upgrade --source" in error for error in errors
    )
