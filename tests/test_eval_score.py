"""vault-eval scoring (ADR-11): the deterministic scorer turns the results
reported on eval cards into machine metrics — recall@k, support-rate, FAMA —
appends them to system/metrics/eval/runs.jsonl, and never fakes a score: a
task with no result block stays `unscored`."""

import datetime
import json
import sys
from pathlib import Path

import pytest

from memoria_vault.runtime.subsystems.telemetry.eval import eval_dispatch, eval_score


def _vault(tmp_path: Path) -> Path:
    """A minimal vault: two gold tasks, a small catalog, one superseded note."""
    ev = tmp_path / "system/eval"
    ev.mkdir(parents=True)
    (ev / "find-x.md").write_text(
        "---\ntype: eval-task\ntitle: Find X\nlifecycle: current\n"
        "workflow: find\neval_role: catalog\nreferences:\n  - vaswani2017attention\n---\n"
        "## Input\nQ\n## Expected behavior\nE\n## Scoring rubric\nR\n",
        encoding="utf-8",
    )
    (ev / "verify-y.md").write_text(
        "---\ntype: eval-task\ntitle: Verify Y\nlifecycle: current\n"
        "workflow: verify\neval_role: verify\nreferences:\n  - devlin2019bert\n---\n"
        "## Input\nQ\n## Expected behavior\nE\n## Scoring rubric\nR\n",
        encoding="utf-8",
    )
    sources = tmp_path / "catalog/sources"
    (sources / "vaswani2017attention").mkdir(parents=True)
    (sources / "vaswani2017attention/source.md").write_text(
        "---\ntype: source\ncheck_status: checked\ntitle: Attention\n"
        "description: Fixture source.\nsource_id: vaswani2017attention\n"
        "citekey: vaswani2017attention\n---\n",
        encoding="utf-8",
    )
    # a renamed record that still resolves via its `citekey:` frontmatter
    (sources / "bert-paper").mkdir(parents=True)
    (sources / "bert-paper/source.md").write_text(
        "---\ntype: source\ncheck_status: checked\ntitle: BERT\n"
        "description: Fixture source.\nsource_id: bert-paper\ncitekey: devlin2019bert\n---\n",
        encoding="utf-8",
    )
    notes = tmp_path / "knowledge/notes"
    notes.mkdir(parents=True)
    (notes / "old-claim.md").write_text(
        "---\ntype: note\ncheck_status: checked\ntitle: Old\nstatus: superseded\n"
        "source_id: catalog/sources/x2020\n---\nold\n",
        encoding="utf-8",
    )
    (notes / "replaced-claim.md").write_text(
        "---\ntype: note\ncheck_status: checked\ntitle: Replaced\n"
        "superseded_by: new-claim\nsource_id: catalog/sources/x2020\n---\nreplaced\n",
        encoding="utf-8",
    )
    (notes / "good-claim.md").write_text(
        "---\ntype: note\ncheck_status: checked\ntitle: Good\n"
        "source_id: catalog/sources/x2020\n---\ngood\n",
        encoding="utf-8",
    )
    return tmp_path


def _result_card(task: str, quarter: str, **fields) -> dict:
    block = json.dumps({"vault_eval": "result", "task": task, "quarter": quarter, **fields})
    return {
        "request_id": f"card-{task}",
        "status": "done",
        "runs": [{"summary": f"Report.\n\n```json\n{block}\n```\n"}],
    }


def test_catalog_resolves_by_stem_and_by_frontmatter_citekey(tmp_path):
    v = _vault(tmp_path)
    keys = eval_score.catalog_citekeys(v)
    assert {"vaswani2017attention", "devlin2019bert", "bert-paper"} <= keys


def test_superseded_claims_classification(tmp_path):
    v = _vault(tmp_path)
    assert eval_score.superseded_claims(v) == {"old-claim", "replaced-claim"}


def test_superseded_classification_matches_the_linter_detector(tmp_path):
    """eval_score mirrors fama_exposure's superseded test — parity guarded here
    (same pattern as the eval-role assignee mirror in test_eval.py)."""
    from memoria_vault.runtime.subsystems.integrity.linter import detectors

    v = _vault(tmp_path)
    # a downstream source citing every note: the detector flags exactly the superseded set
    src = v / "catalog/sources/uses"
    src.mkdir(parents=True)
    (src / "source.md").write_text(
        "---\ntype: source\ncheck_status: checked\ntitle: Uses\n"
        "description: Fixture source.\nsource_id: uses\n---\n"
        "[[old-claim]] [[replaced-claim]] [[good-claim]]\n",
        encoding="utf-8",
    )
    flagged = {f.message.split("[[")[1].split("]]")[0] for f in detectors.fama_exposure(v)}
    assert flagged == eval_score.superseded_claims(v)


def test_recall_at_k_hit_miss_and_window(tmp_path):
    v = _vault(tmp_path)
    catalog = eval_score.catalog_citekeys(v)
    task = {"references": ["vaswani2017attention"]}
    hit = eval_score.score_task(task, {"retrieved": ["a", "vaswani2017attention"]}, catalog, set())
    assert hit["recall_at_k"] == 1.0
    outside = eval_score.score_task(
        task, {"retrieved": ["a", "b", "c", "vaswani2017attention"]}, catalog, set()
    )
    assert outside["recall_at_k"] == 0.0  # rank 4 is outside the k=3 window
    k1 = eval_score.score_task(
        task, {"retrieved": ["a", "vaswani2017attention"]}, catalog, set(), k=1
    )
    assert k1["recall_at_k"] == 0.0


def test_recall_at_k_fraction_over_multiple_gold_citekeys(tmp_path):
    v = _vault(tmp_path)
    task = {"references": ["a2020", "b2021"]}
    m = eval_score.score_task(
        task, {"retrieved": ["a2020", "x", "y"]}, eval_score.catalog_citekeys(v), set()
    )
    assert m["recall_at_k"] == 0.5


def test_support_rate_fraction_of_resolving_citations(tmp_path):
    v = _vault(tmp_path)
    m = eval_score.score_task(
        {"references": []},
        {"cited": ["vaswani2017attention", "devlin2019bert", "ghost2099fake"]},
        eval_score.catalog_citekeys(v),
        set(),
    )
    assert m["support_rate"] == pytest.approx(0.667)
    assert "recall_at_k" not in m  # no gold references -> not computed


def test_fama_clean_and_exposure(tmp_path):
    v = _vault(tmp_path)
    sup = eval_score.superseded_claims(v)
    catalog = eval_score.catalog_citekeys(v)
    dirty = eval_score.score_task(
        {"references": []}, {"claims": ["good-claim", "old-claim"]}, catalog, sup
    )
    assert dirty["fama_clean"] == 0.0
    assert dirty["fama_exposed"] == ["old-claim"]
    clean = eval_score.score_task({"references": []}, {"claims": ["good-claim"]}, catalog, sup)
    assert clean["fama_clean"] == 1.0 and "fama_exposed" not in clean
    none_used = eval_score.score_task({"references": []}, {"claims": []}, catalog, sup)
    assert none_used["fama_clean"] == 1.0  # [] asserts "no claims used" -> clean


def test_no_inputs_means_no_metrics_not_fake_ones(tmp_path):
    v = _vault(tmp_path)
    m = eval_score.score_task(
        {"references": ["a"]}, {"self_score": 1.0}, eval_score.catalog_citekeys(v), set()
    )
    assert m == {}


def test_extract_results_filters_by_quarter_and_marker():
    cards = [
        _result_card("find-x", "2026-Q2", retrieved=["a"]),
        _result_card("find-x", "2026-Q1", retrieved=["stale"]),  # other quarter
        {"request_id": "noise", "runs": [{"summary": '```json\n{"foo": 1}\n```'}]},
        {"request_id": "broken", "runs": [{"summary": "```json\n{not json\n```"}]},
    ]
    out = eval_score.extract_results(cards, "2026-Q2")
    assert set(out) == {"find-x"} and out["find-x"]["retrieved"] == ["a"]


def test_extract_results_newest_block_wins_and_reads_all_summary_fields():
    card = {
        "request_id": "c1",
        "runs": [
            {
                "summary": "```json\n"
                + json.dumps(
                    {
                        "vault_eval": "result",
                        "task": "find-x",
                        "quarter": "2026-Q2",
                        "retrieved": ["first"],
                    }
                )
                + "\n```"
            }
        ],
        "metadata": json.dumps(
            {
                "summary": "```json\n"
                + json.dumps(
                    {
                        "vault_eval": "result",
                        "task": "find-x",
                        "quarter": "2026-Q2",
                        "retrieved": ["second"],
                    }
                )
                + "\n```"
            }
        ),
        "summary": "```json\n"
        + json.dumps(
            {
                "vault_eval": "result",
                "task": "verify-y",
                "quarter": "2026-Q2",
                "cited": ["devlin2019bert"],
            }
        )
        + "\n```",
    }
    out = eval_score.extract_results([card], "2026-Q2")
    assert out["find-x"]["retrieved"] == ["second"]  # later field supersedes
    assert out["verify-y"]["cited"] == ["devlin2019bert"]


def test_score_run_per_task_statuses_and_aggregate(tmp_path):
    v = _vault(tmp_path)
    cards = [
        _result_card(
            "find-x",
            "2026-Q2",
            retrieved=["vaswani2017attention"],
            cited=["vaswani2017attention"],
            claims=[],
            self_score=1.0,
        ),
        # verify-y reports nothing computable -> "reported", never faked
        _result_card("verify-y", "2026-Q2", self_score=0.5),
    ]
    run = eval_score.score_run(v, cards, "2026-Q2")
    rows = {t["task"]: t for t in run["tasks"]}
    assert rows["find-x"]["status"] == "scored"
    assert rows["find-x"]["metrics"] == {"recall_at_k": 1.0, "support_rate": 1.0, "fama_clean": 1.0}
    assert rows["find-x"]["self_score"] == 1.0
    assert rows["verify-y"]["status"] == "reported"
    assert "metrics" not in rows["verify-y"] and rows["verify-y"]["self_score"] == 0.5
    agg = run["aggregate"]
    assert agg["recall_at_k"] == {"mean": 1.0, "n": 1}
    assert (
        agg["tasks_total"],
        agg["tasks_scored"],
        agg["tasks_reported"],
        agg["tasks_unscored"],
    ) == (2, 1, 1, 0)
    assert run["quarter"] == "2026-Q2" and run["k"] == 3 and run["timestamp"]


def test_missing_results_stay_unscored(tmp_path):
    v = _vault(tmp_path)
    run = eval_score.score_run(v, [], "2026-Q2")
    assert all(t["status"] == "unscored" for t in run["tasks"])
    assert run["aggregate"]["tasks_unscored"] == 2
    assert "recall_at_k" not in run["aggregate"]  # nothing scored -> no metric means


def test_append_run_is_one_jsonl_line_per_run(tmp_path):
    v = _vault(tmp_path)
    run = eval_score.score_run(
        v, [_result_card("find-x", "2026-Q2", retrieved=["vaswani2017attention"])], "2026-Q2"
    )
    out = eval_score.append_run(v, run)
    eval_score.append_run(v, run)
    assert out == v / "system/metrics/eval/runs.jsonl"
    lines = out.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2 and json.loads(lines[0])["quarter"] == "2026-Q2"


def test_cli_skips_the_log_when_no_results_exist(tmp_path, monkeypatch, capsys):
    v = _vault(tmp_path)
    cards_file = tmp_path / "cards.json"
    cards_file.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "eval_score.py",
            "--vault",
            str(v),
            "--quarter",
            "2026-Q2",
            "--from-json",
            str(cards_file),
        ],
    )
    eval_score.main()
    assert "nothing scored, log untouched" in capsys.readouterr().out
    assert not (v / "system/metrics/eval/runs.jsonl").exists()


def test_cli_scores_and_appends_from_json(tmp_path, monkeypatch, capsys):
    v = _vault(tmp_path)
    cards_file = tmp_path / "cards.json"
    cards_file.write_text(
        json.dumps([_result_card("find-x", "2026-Q2", retrieved=["vaswani2017attention"])]),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "eval_score.py",
            "--vault",
            str(v),
            "--quarter",
            "2026-Q2",
            "--from-json",
            str(cards_file),
        ],
    )
    eval_score.main()
    assert "1 scored" in capsys.readouterr().out
    line = json.loads((v / "system/metrics/eval/runs.jsonl").read_text(encoding="utf-8").strip())
    assert line["aggregate"]["tasks_scored"] == 1


def test_resolve_quarter():
    today = datetime.date(2026, 6, 12)
    assert eval_score.resolve_quarter("current", today) == "2026-Q2"
    assert eval_score.resolve_quarter("previous", today) == "2026-Q1"
    assert eval_score.resolve_quarter("previous", datetime.date(2026, 2, 1)) == "2025-Q4"
    assert eval_score.resolve_quarter("2025-Q3", today) == "2025-Q3"
    with pytest.raises(SystemExit):
        eval_score.resolve_quarter("Q3", today)


def test_card_body_instructs_the_result_block(tmp_path):
    """The dispatcher tells the eval role exactly what the scorer will read."""
    v = _vault(tmp_path)
    task = eval_dispatch.load_gold_tasks(v)[0]
    card = eval_dispatch.card_for(task, "2026-Q2")
    assert '"vault_eval": "result"' in card["body"]
    assert f'"task": "{task["id"]}"' in card["body"]
    assert '"quarter": "2026-Q2"' in card["body"]
    # the non-committing contract still leads the card
    assert "Do NOT write to the vault" in card["body"]


def test_load_gold_tasks_carries_references(tmp_path):
    v = _vault(tmp_path)
    by_id = {t["id"]: t for t in eval_dispatch.load_gold_tasks(v)}
    assert by_id["find-x"]["references"] == ["vaswani2017attention"]
