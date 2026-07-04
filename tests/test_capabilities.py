from __future__ import annotations

import json
import re
import subprocess
import uuid
from pathlib import Path

import pytest

from memoria_vault.runtime import capabilities as capability_module
from memoria_vault.runtime import state
from memoria_vault.runtime.capabilities import (
    CAPABILITY_INDEX_PATH,
    check_capability_index,
    import_capability,
    iter_capability_manifests,
    render_capability_index,
    write_capability_index,
)
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.operations import load_operation_policy
from memoria_vault.runtime.worker import enqueue_operation, run_next_job

ROOT = Path(__file__).resolve().parent.parent


def workspace(tmp_path: Path) -> Path:
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
    catalog = json.loads(render_capability_index())
    rows = {row["id"]: row for row in catalog["capabilities"]}

    assert catalog["schema_version"] == 1
    assert rows["compile-source-digest"]["allowed_tools"] == ["trusted_writer"]
    assert rows["enrich-source"]["allowed_network"] == [
        "https://api.crossref.org/",
        "https://api.openalex.org/",
        "https://api.unpaywall.org/",
    ]
    assert rows["compile-source-digest"]["trust"]["source"] == "product"
    assert rows["compile-source-digest"]["trust"]["sha256"].startswith("sha256:")
    assert rows["compile-source-digest"]["path"].startswith("product/capabilities/operations/")


def test_worker_operations_are_cataloged_and_policy_shaped() -> None:
    worker = (ROOT / "src/memoria_vault/runtime/worker.py").read_text(encoding="utf-8")
    worker_ids = set(re.findall(r'operation_id == "([^"]+)"', worker))
    for block in re.findall(r"operation_id in \{([^}]+)\}", worker):
        worker_ids.update(re.findall(r'"([^"]+)"', block))
    catalog = json.loads(render_capability_index())
    catalog_ids = {row["id"] for row in catalog["capabilities"]}

    assert worker_ids <= catalog_ids
    assert catalog_ids <= worker_ids
    for operation_id in sorted(catalog_ids):
        load_operation_policy(Path(), operation_id)


def test_capability_index_projection_drift_check(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    result = write_capability_index(vault, commit=True, machine="test-machine")

    assert result["changed"] is True
    assert check_capability_index(vault)
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert result["path"] == CAPABILITY_INDEX_PATH
    assert committed == {state.JOURNAL_HEAD_REL}

    (vault / CAPABILITY_INDEX_PATH).write_text("{}\n", encoding="utf-8")
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
    assert done["output"] == CAPABILITY_INDEX_PATH
    assert check_capability_index(vault)
    committed = set(git(vault, "show", "--name-only", "--format=", done["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL}


def test_directory_only_capability_manifest_fails_runtime_loader(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_capability_package(
        tmp_path,
        monkeypatch,
        "operation",
        {"directory-only/prompt.md": "# Prompt\n"},
    )
    message = (
        "directory-only capability manifest is invalid: "
        "product/capabilities/operations/directory-only; "
        "expected sibling product/capabilities/operations/directory-only.md"
    )

    with pytest.raises(ValueError, match=re.escape(message)):
        render_capability_index()
    with pytest.raises(ValueError, match=re.escape(message)):
        load_operation_policy(Path(), "directory-only")


def test_same_stem_capability_asset_folder_is_allowed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_capability_package(
        tmp_path,
        monkeypatch,
        "operation",
        {
            "analyze-gaps.md": (
                "---\n"
                "type: operation\n"
                "check_status: checked\n"
                "title: Analyze gaps\n"
                "description: Fixture.\n"
                "operation_id: analyze-gaps\n"
                "allowed_tools: [trusted_writer]\n"
                "allowed_paths: []\n"
                "allowed_network: []\n"
                "runner:\n"
                "  test: {provider: local, model: deterministic-fixture, temperature: 0}\n"
                "  live: {provider: gateway, model: deterministic-fixture, temperature: 0}\n"
                "prompt_version: fixture\n"
                "io_schema: {input: fixture, output: fixture}\n"
                "risk_class: low\n"
                "required_checks: []\n"
                "---\n"
                "Body.\n"
            ),
            "analyze-gaps/prompt.md": "# Prompt\n",
        },
    )

    rows = {row["id"] for row in json.loads(render_capability_index())["capabilities"]}

    assert "analyze-gaps" in rows
    assert load_operation_policy(Path(), "analyze-gaps")["operation_id"] == "analyze-gaps"


def test_only_operation_capabilities_are_supported(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    legacy = tmp_path / "legacy-mcp.md"
    legacy.write_text(
        "---\n"
        "type: mcp\n"
        "check_status: unchecked\n"
        "title: Legacy MCP\n"
        "description: Old capability type.\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsupported capability type: mcp"):
        import_capability(vault, legacy)
    with pytest.raises(ValueError, match="unsupported capability type: adapter"):
        iter_capability_manifests("adapter")


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
        row["id"] for row in json.loads(render_capability_index())["capabilities"]
    }
    event = list(iter_jsonl(vault / "journal/test-machine.jsonl"))[-1]
    assert event["check"] == "capability-import-trust"
    assert event["status"] == "failed"
    assert event["quarantined_id"] == result["quarantine_path"]
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL}
    try:
        load_operation_policy(vault, "remote-danger")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("unsigned imported operation should not be executable")


def _patch_capability_package(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capability_type: str,
    files: dict[str, str],
) -> None:
    assert capability_type == "operation"
    home = "operations"
    package_name = f"test_caps_{uuid.uuid4().hex}"
    package_root = tmp_path / "packages"
    package = package_root / package_name / home
    package.mkdir(parents=True)
    (package_root / package_name / "__init__.py").write_text("", encoding="utf-8")
    (package / "__init__.py").write_text("", encoding="utf-8")
    for rel, text in files.items():
        path = package / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    monkeypatch.syspath_prepend(str(package_root))
    monkeypatch.setattr(capability_module, "CAPABILITY_PACKAGE", f"{package_name}.{home}")
