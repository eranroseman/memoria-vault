"""L1 component tests for the inbox archival sweep (#338).

A resolved inbox card (lifecycle current + `resolved:` stamp) older
than N days flips to lifecycle: archived in place; everything else is left
alone — so the inbox demonstrably converges to empty when cards are handled.
"""

import datetime

from operations.cleanup import archive_inbox as m


def _card(vault, name, body, folder="inbox"):
    d = vault / folder
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text(body, encoding="utf-8")
    return p


def _days_ago(n):
    return (datetime.date.today() - datetime.timedelta(days=n)).isoformat()


def test_old_resolved_card_archived(tmp_path):
    p = _card(
        tmp_path,
        "flag-a.md",
        "---\ntype: flag\nlifecycle: current\n"
        f"resolved: {_days_ago(45)}\ncertainty: likely\n---\nBody stays.\n",
    )
    out = m.sweep(tmp_path, days=30)
    assert out["archived"] == ["inbox/flag-a.md"]
    text = p.read_text(encoding="utf-8")
    assert "lifecycle: archived" in text
    # every other byte preserved — frontmatter fields and body untouched
    assert f"resolved: {_days_ago(45)}" in text
    assert "certainty: likely" in text
    assert text.endswith("Body stays.\n")


def test_invalid_retracted_lifecycle_is_not_archived(tmp_path):
    _card(
        tmp_path,
        "cand-r.md",
        f"---\ntype: candidate\nlifecycle: retracted\nresolved: {_days_ago(31)}\n---\n",
    )
    out = m.sweep(tmp_path, days=30)
    assert out["archived"] == [] and out["skipped_unresolved"] == 1


def test_fresh_resolved_card_untouched(tmp_path):
    p = _card(
        tmp_path,
        "flag-fresh.md",
        f"---\ntype: flag\nlifecycle: current\nresolved: {_days_ago(3)}\n---\n",
    )
    out = m.sweep(tmp_path, days=30)
    assert out["archived"] == [] and out["skipped_fresh"] == 1
    assert "lifecycle: current" in p.read_text(encoding="utf-8")


def test_unresolved_card_untouched(tmp_path):
    # proposed (awaiting the PI) and resolved-without-a-stamp: never touched
    p1 = _card(tmp_path, "proposed.md", "---\ntype: gap\nlifecycle: proposed\n---\n")
    p2 = _card(tmp_path, "no-stamp.md", "---\ntype: flag\nlifecycle: current\n---\n")
    out = m.sweep(tmp_path, days=0)
    assert out["archived"] == [] and out["skipped_unresolved"] == 2
    assert "lifecycle: proposed" in p1.read_text(encoding="utf-8")
    assert "lifecycle: current" in p2.read_text(encoding="utf-8")


def test_malformed_card_skipped_with_warning(tmp_path, capsys):
    p = _card(tmp_path, "broken.md", "---\nlifecycle: current\nresolved: [unclosed\n")
    out = m.sweep(tmp_path, days=0)
    assert out["archived"] == [] and out["skipped_malformed"] == 1
    assert "skip inbox/broken.md" in capsys.readouterr().err
    assert p.read_text(encoding="utf-8").startswith("---\nlifecycle: current")


def test_n_read_from_calibration_yaml(tmp_path):
    f = tmp_path / ".memoria" / "schemas"
    f.mkdir(parents=True)
    (f / "calibration.yaml").write_text("inbox:\n  archive_after_days: 7\n", encoding="utf-8")
    assert m.archive_after_days(tmp_path) == 7


def test_default_n_when_config_absent(tmp_path, capsys):
    m._warned_calibration = False
    assert m.archive_after_days(tmp_path) == m.DEFAULT_ARCHIVE_AFTER_DAYS == 30
    assert "WARNING" in capsys.readouterr().err  # loud, not silent


def test_idempotent_rerun(tmp_path):
    _card(
        tmp_path,
        "flag-a.md",
        f"---\ntype: flag\nlifecycle: current\nresolved: {_days_ago(40)}\n---\nbody\n",
    )
    first = m.sweep(tmp_path, days=30)
    second = m.sweep(tmp_path, days=30)
    assert first["archived"] == ["inbox/flag-a.md"]
    assert second["archived"] == [] and second["skipped_already_archived"] == 1


def test_dry_run_writes_nothing(tmp_path):
    p = _card(
        tmp_path,
        "flag-a.md",
        f"---\ntype: flag\nlifecycle: current\nresolved: {_days_ago(40)}\n---\n",
    )
    out = m.sweep(tmp_path, days=30, dry_run=True)
    assert out["archived"] == ["inbox/flag-a.md"] and out["dry_run"] is True
    assert "lifecycle: current" in p.read_text(encoding="utf-8")


def test_inbox_converges_to_empty(tmp_path):
    """Acceptance: handled cards drain; nothing active remains after the sweep."""
    import yaml

    for i in range(3):
        _card(
            tmp_path,
            f"done-{i}.md",
            f"---\ntype: flag\nlifecycle: current\nresolved: {_days_ago(31 + i)}\n---\n",
        )
    m.sweep(tmp_path, days=30)
    states = [
        yaml.safe_load(p.read_text(encoding="utf-8").split("---")[1])["lifecycle"]
        for p in sorted((tmp_path / "inbox").glob("*.md"))
    ]
    assert states == ["archived"] * 3
