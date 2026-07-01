from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from memoria_vault.runtime.capabilities import (
    check_capability_index,
    import_capability,
    render_capability_index,
    write_capability_index,
)
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.operations import load_operation_policy
from memoria_vault.runtime.worker import enqueue_operation, run_next_job

ROOT = Path(__file__).resolve().parent.parent


def workspace(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "vault-template/capabilities", tmp_path / "capabilities")
    (tmp_path / "capabilities/_generated/capability-index.json").unlink(missing_ok=True)
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "capabilities@example.invalid")
    git(tmp_path, "config", "user.name", "Capabilities")
    return tmp_path


def git(vault: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=vault,
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.returncode:
        raise AssertionError(proc.stderr or proc.stdout)
    return proc.stdout.strip()


def test_capability_index_renderer_covers_shipped_operations() -> None:
    vault = ROOT / "vault-template"

    catalog = json.loads(render_capability_index(vault))
    rows = {row["id"]: row for row in catalog["capabilities"]}

    assert catalog["schema_version"] == 1
    assert (vault / "capabilities/_generated/capability-index.json").read_text(
        encoding="utf-8"
    ) == render_capability_index(vault)
    assert rows["compile-source-digest"]["allowed_tools"] == ["trusted_writer"]
    assert rows["enrich-source"]["allowed_network"] == [
        "https://api.crossref.org/",
        "https://api.openalex.org/",
        "https://api.unpaywall.org/",
    ]
    assert rows["compile-source-digest"]["trust"]["sha256"].startswith("sha256:")


def test_worker_operations_are_cataloged_and_policy_shaped() -> None:
    vault = ROOT / "vault-template"
    worker = (ROOT / "src/memoria_vault/runtime/worker.py").read_text(encoding="utf-8")
    worker_ids = set(re.findall(r'operation_id == "([^"]+)"', worker))
    for block in re.findall(r"operation_id in \{([^}]+)\}", worker):
        worker_ids.update(re.findall(r'"([^"]+)"', block))
    catalog = json.loads(render_capability_index(vault))
    catalog_ids = {row["id"] for row in catalog["capabilities"]}

    assert worker_ids <= catalog_ids
    for operation_id in sorted(catalog_ids):
        load_operation_policy(vault, operation_id)


def test_capability_index_projection_drift_check(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    result = write_capability_index(vault, commit=True, machine="test-machine")

    assert result["changed"] is True
    assert check_capability_index(vault)
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {
        "capabilities/_generated/capability-index.json",
        "journal/test-machine.jsonl",
    }

    (vault / "capabilities/_generated/capability-index.json").write_text("{}\n", encoding="utf-8")
    assert not check_capability_index(vault)


def test_worker_runs_capability_index_projection_operation_jobs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    queued = enqueue_operation(
        vault,
        "regenerate-capability-index",
        idempotency_key="capability-index",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["changed"] is True
    assert done["output"] == "capabilities/_generated/capability-index.json"
    assert check_capability_index(vault)
    committed = set(git(vault, "show", "--name-only", "--format=", done["commit"]).splitlines())
    assert committed == {
        "capabilities/_generated/capability-index.json",
        "journal/test-machine.jsonl",
    }


def test_directory_only_capability_manifest_fails_runtime_loader(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    asset_dir = vault / "capabilities/operations/directory-only"
    asset_dir.mkdir()
    (asset_dir / "prompt.md").write_text("# Prompt\n", encoding="utf-8")
    message = (
        "directory-only capability manifest is invalid: "
        "capabilities/operations/directory-only; "
        "expected sibling capabilities/operations/directory-only.md"
    )

    with pytest.raises(ValueError, match=re.escape(message)):
        render_capability_index(vault)
    with pytest.raises(ValueError, match=re.escape(message)):
        load_operation_policy(vault, "directory-only")


def test_same_stem_capability_asset_folder_is_allowed(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    asset_dir = vault / "capabilities/operations/analyze-gaps"
    asset_dir.mkdir()
    (asset_dir / "prompt.md").write_text("# Prompt\n", encoding="utf-8")

    rows = {row["id"] for row in json.loads(render_capability_index(vault))["capabilities"]}

    assert "analyze-gaps" in rows
    assert load_operation_policy(vault, "analyze-gaps")["operation_id"] == "analyze-gaps"


def test_unsigned_capability_import_is_quarantined_and_not_executable(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    incoming = tmp_path / "incoming/remote-danger.md"
    incoming.parent.mkdir()
    incoming.write_text(
        "---\n"
        "type: operation\n"
        "check_status: checked\n"
        "title: Remote danger\n"
        "description: Unsigned imported operation.\n"
        "operation_id: remote-danger\n"
        "allowed_tools: [shell]\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )

    result = import_capability(vault, incoming, machine="test-machine", commit=True)

    assert result["status"] == "quarantined"
    assert (vault / result["quarantine_path"]).is_file()
    assert not (vault / "capabilities/operations/remote-danger.md").exists()
    assert "remote-danger" not in {
        row["id"] for row in json.loads(render_capability_index(vault))["capabilities"]
    }
    event = list(iter_jsonl(vault / "journal/test-machine.jsonl"))[-1]
    assert event["check"] == "capability-import-trust"
    assert event["status"] == "failed"
    assert event["quarantined_id"] == result["quarantine_path"]
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {"journal/test-machine.jsonl"}
    try:
        load_operation_policy(vault, "remote-danger")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("unsigned imported operation should not be executable")
