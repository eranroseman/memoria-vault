import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from memoria_vault.runtime.subsystems.lib import worklists


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
    assert prompt_fm["target"] == "system/worklists/transformer-screening/"
    assert "lane" not in prompt_fm
    assert "task_id" not in prompt_fm


def test_emit_worklist_neutralizes_report_derived_text(tmp_path):
    result = worklists.emit_worklist(
        tmp_path,
        "![Batch](http://beacon.example/batch.png)",
        [
            {
                "title": "![Work](http://beacon.example/work.png)",
                "item_ref": "https://beacon.example/ref",
                "reason": '<img src="http://beacon.example/reason.png">',
            }
        ],
    )

    [item] = result["items"]
    rendered = item.read_text(encoding="utf-8")
    prompt = result["prompt"].read_text(encoding="utf-8")
    assert "![" not in rendered + prompt
    assert "<img" not in rendered
    for url in (
        "http://beacon.example/batch.png",
        "http://beacon.example/work.png",
        "http://beacon.example/reason.png",
    ):
        assert f"`{url}`" in rendered + prompt


def test_emit_worklist_renders_composed_title_and_reference_inert(tmp_path):
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("Pandoc is optional")
    result = worklists.emit_worklist(
        tmp_path,
        "Security review",
        [
            {
                "title": '```\n<img src="https://evil.example/item-title">\n```',
                "item_ref": 'ref ` <img src="https://evil.example/item-ref"> `',
            }
        ],
    )

    [item] = result["items"]
    rendered = subprocess.run(
        [pandoc, "-f", "commonmark", "-t", "html"],
        input=item.read_text(encoding="utf-8"),
        text=True,
        capture_output=True,
        check=True,
    ).stdout

    assert "<img" not in rendered


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
