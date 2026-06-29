from pathlib import Path

import yaml
from operations.lib import worklists


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text.split("---", 2)[1])


def test_emit_worklist_writes_projection_rows_and_one_prompt(tmp_path):
    result = worklists.emit_worklist(
        tmp_path,
        "Transformer screening",
        [
            {"title": "Attention Is All You Need", "item_ref": "@vaswani2017", "group": "seed"},
            {
                "title": "BERT",
                "item_ref": "@devlin2019",
                "group": "follow-up",
                "reason": "Cites transformer architecture.",
            },
        ],
        source_report="notes/fleeting/maps/transformer-report.md",
    )

    assert result["worklist"] == "transformer-screening"
    item_paths = sorted((tmp_path / "system" / "worklists" / result["worklist"]).glob("*.md"))
    assert len(item_paths) == 2
    for path in item_paths:
        fm = _frontmatter(path)
        assert fm["projection"] == "worklist-item"
        assert fm["attention_status"] == "open"
        assert "type" not in fm
        assert fm["decision"] == "proposed"
        assert fm["worklist"] == "transformer-screening"
        assert fm["source_report"] == "notes/fleeting/maps/transformer-report.md"

    prompts = list((tmp_path / "inbox").glob("work-prompt-*.md"))
    assert len(prompts) == 1
    prompt_fm = _frontmatter(prompts[0])
    assert prompt_fm["projection"] == "attention"
    assert prompt_fm["attention_kind"] == "work-prompt"
    assert prompt_fm["raised_by"] == "worklists"
    assert "system/worklists/worklists.base#By worklist" in prompt_fm["target"]


def test_emit_worklist_rejects_unknown_decision(tmp_path):
    try:
        worklists.emit_worklist(tmp_path, "Bad batch", [{"title": "x", "decision": "accept"}])
    except ValueError as exc:
        assert "decision must be" in str(exc)
    else:
        raise AssertionError("unknown decisions must fail")


def test_emit_report_reads_items_or_rows(tmp_path):
    report = tmp_path / "report.json"
    report.write_text(
        '{"title":"Coverage", "items":[{"title":"One", "item_ref":"notes/sources/one.md"}]}',
        encoding="utf-8",
    )
    result = worklists.emit_report(tmp_path, report)
    assert result["worklist"] == "coverage"
    assert len(result["items"]) == 1
