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


def test_emit_worklist_passes_raised_by_and_loudness_through(tmp_path):
    # `alert`, not `quiet`: `quiet` is the shipped default since I1 A.5, so
    # passing it would prove the default rather than the pass-through.
    worklists.emit_worklist(
        tmp_path,
        "Bulk import batch",
        [{"title": "One", "item_ref": "doi-10.1234/x"}],
        raised_by="import",
        loudness="alert",
    )

    [prompt] = list((tmp_path / "inbox").glob("work-prompt-*.md"))
    frontmatter = _frontmatter(prompt)
    assert frontmatter["raised_by"] == "import"
    assert frontmatter["loudness"] == "alert"


def test_emit_import_worklist_ranks_duplicates_first_with_honest_denominators(tmp_path):
    result = worklists.emit_import_worklist(
        tmp_path,
        run_id="20260717-a1b2",
        rows=[
            {"title": "Unmappable entry type", "item_ref": "misc-1", "group": "unmapped"},
            {"title": "Malformed entry", "citekey": "broken2024", "group": "failed"},
            {
                "title": "Enrichment-surfaced retraction",
                "item_ref": "doi-10.1234/z",
                "group": "retraction",
            },
            {
                "title": "Cross-identifier duplicate",
                "item_ref": "doi-10.1234/y",
                "group": "duplicate",
                "reason": "arXiv id matches admitted work doi-10.1234/q",
            },
            {"title": "Parse error at entry 7", "item_ref": "entry-7", "group": "failed"},
        ],
        entries_total=10,
        admitted=6,
    )

    assert result is not None
    assert result["worklist"] == "import-20260717-a1b2"
    by_rank = {}
    for path in result["items"]:
        frontmatter = _frontmatter(path)
        by_rank[frontmatter["rank"]] = (frontmatter["group"], frontmatter["item_ref"])
    assert by_rank == {
        1: ("duplicate", "doi-10.1234/y"),
        2: ("retraction", "doi-10.1234/z"),
        3: ("failed", "broken2024"),
        4: ("failed", "entry-7"),
        5: ("unmapped", "misc-1"),
    }
    [prompt] = list((tmp_path / "inbox").glob("work-prompt-*.md"))
    frontmatter = _frontmatter(prompt)
    assert frontmatter["raised_by"] == "import"
    assert frontmatter["loudness"] == "quiet"
    for denominator in ("10 entries", "6 admitted", "5 need judgment"):
        assert denominator in frontmatter["title"]


def test_emit_import_worklist_empty_judgment_set_mints_nothing(tmp_path):
    result = worklists.emit_import_worklist(
        tmp_path, run_id="20260717-c3d4", rows=[], entries_total=4, admitted=4
    )

    assert result is None
    assert not (tmp_path / "system" / "worklists").exists()
    assert not (tmp_path / "inbox").exists()
