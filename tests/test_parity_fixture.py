"""User-facing parity fixture."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_vault.cli import main
from memoria_vault.runtime import state
from memoria_vault.runtime.capabilities import render_capability_index
from memoria_vault.runtime.vaultio import read_frontmatter
from tests.cli_test_helpers import cli_command_surface
from tests.helpers import set_concept_verdict

pytestmark = pytest.mark.contract

ADAPTER_ENV_VARS = (
    "OBSIDIAN_API_KEY",
    "OBSIDIAN_MCP_PORT",
    "OBSIDIAN_MCP_SSL_VERIFY",
    "ZOTERO_API_KEY",
    "HERMES_HOME",
)


def test_palette_actions_have_standalone_cli_parity(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in ADAPTER_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    _write_attention_fixture(workspace)
    _write_project_argument_fixture(workspace)

    assert (
        main(
            [
                "new",
                "note",
                "Palette note",
                "--workspace",
                str(workspace),
                "--body",
                "Captured without an adapter.",
                "--json",
            ]
        )
        == 0
    )
    note = json.loads(capsys.readouterr().out)
    assert "check_status" not in read_frontmatter(workspace / note["path"])
    assert state.concept_check_status(workspace, note["path"]) == "unchecked"

    assert main(["attention", "list", "--workspace", str(workspace), "--json"]) == 0
    attention = json.loads(capsys.readouterr().out)
    assert [row["path"] for row in attention["attention"]] == [
        "inbox/dismiss-card.md",
        "inbox/resolve-card.md",
    ]

    assert (
        main(
            [
                "project",
                "trace",
                "--workspace",
                str(workspace),
                "project-alpha",
                "--json",
                "--idempotency-key",
                "palette-trace",
            ]
        )
        == 0
    )
    trace = json.loads(capsys.readouterr().out)
    assert trace["result"]["project_path"] == "projects/project-alpha/project.md"
    assert trace["result"]["relation_count"] == 1

    assert (
        main(
            [
                "attention",
                "resolve",
                "--workspace",
                str(workspace),
                "inbox/resolve-card.md",
                "--apply",
                "--json",
                "--idempotency-key",
                "palette-resolve",
            ]
        )
        == 0
    )
    resolved = json.loads(capsys.readouterr().out)
    assert resolved["result"]["resolution"]["outcome"] == "apply"
    assert resolved["result"]["resolution"]["routing_class"] == "ask"

    assert (
        main(
            [
                "attention",
                "resolve",
                "--workspace",
                str(workspace),
                "inbox/dismiss-card.md",
                "--reject",
                "--json",
                "--idempotency-key",
                "palette-reject",
            ]
        )
        == 0
    )
    rejected = json.loads(capsys.readouterr().out)
    assert rejected["result"]["resolution"]["outcome"] == "reject"
    assert rejected["result"]["resolution"]["routing_class"] == "ask"

    with state.connect(workspace) as conn:
        rows = conn.execute(
            """
            SELECT request_id, operation_id
            FROM operation_requests
            WHERE request_id IN ('palette-trace', 'palette-resolve', 'palette-reject')
            ORDER BY request_id
            """
        ).fetchall()
    assert [(row["request_id"], row["operation_id"]) for row in rows] == [
        ("palette-reject", "resolve-attention"),
        ("palette-resolve", "resolve-attention"),
        ("palette-trace", "analyze-project-argument"),
    ]


def test_startup_shell_restore_is_adapter_only_not_core_cli() -> None:
    surface = cli_command_surface()

    assert "memoria restore shell" not in surface
    assert "memoria workspace run" in surface
    assert "memoria workspace scan" in surface


def _dispatchable_operation_ids() -> list[str]:
    """Collection-time operation roster from the package's own manifests.

    1733: the dispatch sweep is parametrized per operation so xdist spreads
    ~60 dispatches across workers instead of serializing them in one 128s
    test. The roster comes from `render_capability_index()` with no
    workspace, which is safe at collection time; the parity test below
    pins it against a real workspace's manifests so the two sources cannot
    silently diverge.
    """
    rows = json.loads(render_capability_index())["capabilities"]
    return sorted(
        str(fm.get("operation_id") or fm["id"]) for fm in rows if fm.get("type") == "operation"
    )


@pytest.fixture(scope="module")
def parity_workspace(tmp_path_factory: pytest.TempPathFactory) -> Path:
    workspace = tmp_path_factory.mktemp("parity") / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--quiet"]) == 0
    return workspace


def test_operation_parity_is_manifest_derived(
    parity_workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    manifests = _operation_manifest_rows(parity_workspace)
    manifest_ids = {row["operation_id"] for row in manifests}
    assert manifest_ids
    assert [row for row in manifests if row["adapter_only"] or row["dropped"]] == []

    assert main(["operation", "list", "--workspace", str(parity_workspace), "--json"]) == 0
    listed = json.loads(capsys.readouterr().out)
    listed_ids = {row["operation_id"] for row in listed["operations"]}
    assert listed_ids == manifest_ids
    # The parametrized dispatch sweep below draws its roster from the package
    # index at collection time; this equality is what keeps that roster honest.
    assert set(_dispatchable_operation_ids()) == manifest_ids


@pytest.mark.parametrize("operation_id", _dispatchable_operation_ids())
def test_operation_is_dispatchable(
    parity_workspace: Path, capsys: pytest.CaptureFixture[str], operation_id: str
) -> None:
    rc = main(
        [
            "operation",
            "run",
            "--workspace",
            str(parity_workspace),
            operation_id,
            "--payload-json",
            "{}",
            "--json",
            "--idempotency-key",
            f"parity-{operation_id}",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    error = str((output.get("result") or {}).get("error") or output.get("error") or "")
    assert not (rc != 0 and "unsupported operation" in error), error


def _operation_manifest_rows(workspace: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for frontmatter in json.loads(render_capability_index(workspace))["capabilities"]:
        if frontmatter.get("type") != "operation":
            continue
        rows.append(
            {
                "operation_id": str(frontmatter.get("operation_id") or frontmatter["id"]),
                "adapter_only": bool(frontmatter.get("adapter_only")),
                "dropped": bool(frontmatter.get("dropped")),
                "drop_reason": str(frontmatter.get("drop_reason") or ""),
            }
        )
    return rows


def _write_attention_fixture(workspace: Path) -> None:
    inbox = workspace / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    for name, title in (
        ("dismiss-card", "Dismiss card"),
        ("resolve-card", "Resolve card"),
    ):
        (inbox / f"{name}.md").write_text(
            "---\n"
            f"title: {title}\n"
            "projection: attention\n"
            "attention_kind: flag\n"
            "attention_status: open\n"
            "routing_class: ask\n"
            "target: notes/palette.md\n"
            "---\n"
            "# Attention\n\nPalette parity fixture.\n",
            encoding="utf-8",
        )


def _write_project_argument_fixture(workspace: Path) -> None:
    project = workspace / "projects/project-alpha/project.md"
    project.parent.mkdir(parents=True, exist_ok=True)
    project.write_text(
        "---\n"
        "type: project\n"
        "title: Alpha project\n"
        "tags: []\n"
        "links: {}\n"
        "thesis: notes/thesis.md\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    set_concept_verdict(workspace, "projects/project-alpha/project.md", "project")
    thesis = workspace / "notes/thesis.md"
    support = workspace / "notes/support.md"
    thesis.parent.mkdir(parents=True, exist_ok=True)
    thesis.write_text(
        "---\ntype: note\ntitle: Thesis\ntags: []\nlinks: {}\nstatus: accepted\n---\nThesis.\n",
        encoding="utf-8",
    )
    set_concept_verdict(workspace, "notes/thesis.md", "note")
    support.write_text(
        "---\n"
        "type: note\n"
        "title: Support\n"
        "tags: []\n"
        "status: accepted\n"
        "links:\n"
        "  supports:\n"
        "    - notes/thesis.md\n"
        "---\n"
        "Support.\n",
        encoding="utf-8",
    )
    set_concept_verdict(workspace, "notes/support.md", "note")
