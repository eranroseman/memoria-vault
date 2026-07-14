from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

import pytest

from memoria_vault.runtime import capabilities as capability_module
from memoria_vault.runtime import state
from memoria_vault.runtime.capabilities import (
    CAPABILITY_INDEX_PATH,
    DEFAULT_RUNNER_POLICY,
    check_capability_index,
    iter_capability_manifests,
    render_capability_index,
)
from memoria_vault.runtime.capabilities import (
    write_capability_index as _write_capability_index,
)
from memoria_vault.runtime.operations import load_operation_policy
from memoria_vault.runtime.worker import enqueue_operation, run_next_job
from tests.helpers import ROOT, call_with_context, git, init_git


def write_capability_index(vault: Path, *args, **kwargs):
    return call_with_context(_write_capability_index, vault, *args, **kwargs)


def workspace(tmp_path: Path) -> Path:
    init_git(tmp_path, "capabilities@example.invalid", "Capabilities")
    return tmp_path


def test_capability_index_renderer_covers_shipped_operations() -> None:
    catalog = json.loads(render_capability_index())
    rows = {row["id"]: row for row in catalog["capabilities"]}

    assert catalog["schema_version"] == 1
    assert rows["compile-source-digest"]["allowed_tools"] == ["trusted_writer"]
    assert rows["enrich-source"]["allowed_network"] == [
        "https://api.crossref.org/",
        "https://api.openalex.org/",
        "https://api.unpaywall.org/",
        "https://api.semanticscholar.org/",
    ]
    assert rows["compile-source-digest"]["trust"]["source"] == "product"
    assert rows["compile-source-digest"]["trust"]["sha256"].startswith("sha256:")
    assert rows["compile-source-digest"]["path"].startswith("product/capabilities/operations/")
    assert rows["compile-source-digest"]["runner"] == DEFAULT_RUNNER_POLICY
    assert "check_status" not in rows["compile-source-digest"]

    operations = ROOT / "src/memoria_vault/product/capabilities/operations"
    assert not any(
        re.search(r"^runner:", path.read_text(encoding="utf-8"), re.M)
        for path in operations.glob("*.md")
    )


def test_worker_operations_are_cataloged_and_policy_shaped() -> None:
    worker = (ROOT / "src/memoria_vault/runtime/worker.py").read_text(encoding="utf-8")
    worker_ids = set(re.findall(r'operation_id == "([^"]+)"', worker))
    for block in re.findall(r"operation_id in \{([^}]+)\}", worker):
        worker_ids.update(re.findall(r'"([^"]+)"', block))
    # Some checks dispatch through a module-level dict (`operation_id in SOME_DICT`)
    # instead of a literal set; pull its keys too so the dispatch dict doesn't
    # have to be spelled out twice just to keep this scan honest.
    for dict_name in re.findall(r"operation_id in (\w+)", worker):
        dict_block = re.search(rf"^{dict_name} = \{{(.*?)^\}}", worker, re.M | re.S)
        if dict_block:
            worker_ids.update(re.findall(r'"([^"]+)":', dict_block.group(1)))
    catalog = json.loads(render_capability_index())
    catalog_ids = {row["id"] for row in catalog["capabilities"]}

    assert worker_ids <= catalog_ids
    assert catalog_ids <= worker_ids
    for operation_id in sorted(catalog_ids):
        load_operation_policy(Path(), operation_id)


def test_capability_index_projection_drift_check(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    result = write_capability_index(vault, machine="test-machine")

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
        actor="pi",
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


def test_only_operation_capabilities_are_supported() -> None:
    with pytest.raises(ValueError, match="unsupported capability type: adapter"):
        iter_capability_manifests("adapter")


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
