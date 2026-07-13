from __future__ import annotations

import base64
import json
from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.operations import load_operation_policy
from memoria_vault.runtime.worker import enqueue_operation, run_next_job
from tests.helpers import copy_memoria_dirs, git, init_git


def workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas", "config")
    init_git(tmp_path, "worker@example.invalid", "Alpha Worker")
    git(tmp_path, "add", ".memoria/schemas", ".memoria/config")
    git(tmp_path, "commit", "-m", "seed worker workspace")
    return tmp_path


def test_worker_runs_capture_source_operation_jobs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    queued = enqueue_operation(
        vault,
        "capture-source",
        payload={
            "work_id": "source-alpha",
            "title": "Alpha Source",
            "description": "A fixture source.",
            "content_text": "Extracted alpha text.",
            "raw_text": "raw alpha bytes",
            "raw_filename": "alpha.txt",
            "resource": "https://example.test/alpha",
            "citekey": "alpha2026",
            "run_id": "capture-alpha",
        },
        idempotency_key="capture-alpha",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["work_id"] == "source-alpha"
    assert done["check_status"] == "unchecked"
    assert done["content_path"] == ".memoria/blobs/source-content/source-alpha/content.txt"
    assert done["raw_path"] == ".memoria/blobs/source-content/source-alpha/raw/alpha.txt"
    assert not (vault / "catalog/sources/source-alpha/source.md").exists()
    source = state.catalog_source(vault, "source-alpha")
    assert source is not None
    assert source["check_status"] == "unchecked"
    assert source["resource"] == "https://example.test/alpha"
    assert (vault / done["content_path"]).read_text(encoding="utf-8") == "Extracted alpha text.\n"
    assert (vault / done["raw_path"]).read_text(encoding="utf-8") == "raw alpha bytes"
    committed = set(git(vault, "show", "--name-only", "--format=", done["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL}


def test_worker_runs_capture_pdf_source_operation_jobs(tmp_path: Path, monkeypatch) -> None:
    vault = workspace(tmp_path)
    monkeypatch.setattr(
        "memoria_vault.runtime.capture._extract_pdf_pages",
        lambda _raw: [
            {
                "page": 2,
                "text": "A PDF block with anchored evidence.",
            }
        ],
    )

    queued = enqueue_operation(
        vault,
        "capture-pdf-source",
        payload={
            "work_id": "pdf-source",
            "title": "PDF Source",
            "description": "A fixture PDF source.",
            "raw_pdf_base64": base64.b64encode(b"%PDF fixture\n").decode(),
            "raw_filename": "paper.pdf",
            "run_id": "capture-pdf",
        },
        idempotency_key="capture-pdf",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["work_id"] == "pdf-source"
    assert done["check_status"] == "unchecked"
    assert done["content_path"] == ".memoria/blobs/source-content/pdf-source/content.txt"
    assert done["raw_path"] == ".memoria/blobs/source-content/pdf-source/raw/paper.pdf"
    assert not (vault / "catalog/sources/pdf-source/source.md").exists()
    assert "anchored evidence" in (vault / done["content_path"]).read_text(encoding="utf-8")


def test_worker_capture_pdf_source_fails_before_partial_write(tmp_path: Path, monkeypatch) -> None:
    vault = workspace(tmp_path)
    monkeypatch.setattr(
        "memoria_vault.runtime.capture._extract_pdf_pages",
        lambda _raw: [{"page": 2, "text": "\ufffd\ufffd !!! ???", "blocks": []}],
    )

    enqueue_operation(
        vault,
        "capture-pdf-source",
        payload={
            "work_id": "pdf-missing-selector",
            "title": "PDF Missing Selector",
            "description": "A fixture PDF source.",
            "raw_pdf_base64": base64.b64encode(b"%PDF fixture\n").decode(),
            "raw_filename": "paper.pdf",
            "run_id": "capture-pdf-missing-selector",
        },
        idempotency_key="capture-pdf-missing-selector",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done is not None
    assert done["status"] == "failed"
    assert "coherence check" in done["error"]
    assert not (vault / "catalog/sources/pdf-missing-selector").exists()
    assert not (vault / ".memoria/journal").exists()


def test_worker_runs_capture_bibtex_source_operation_jobs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    bibtex = """@article{harness2026,
      title = {Harnessed Workflows for Durable Research},
      author = {Ada, River and Morgan Lin},
      year = {2026},
      journal = {Journal of Testable Systems},
      doi = {10.1000/harness.2026},
      abstract = {A fixture paper for the Memoria test environment harness.}
    }"""

    queued = enqueue_operation(
        vault,
        "capture-bibtex-source",
        payload={"bibtex": bibtex, "run_id": "capture-bibtex-harness"},
        idempotency_key="capture-bibtex-harness",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["work_id"] == "doi-10.1000_harness.2026"
    assert done["check_status"] == "unchecked"
    assert done["raw_path"].endswith("/raw/harness2026.bib")
    assert (
        (vault / done["raw_path"]).read_text(encoding="utf-8").startswith("@article{harness2026,")
    )
    assert not (vault / "catalog/sources/doi-10.1000_harness.2026/source.md").exists()
    assert not (vault / "bibliography.bib").exists()
    with state.connect(vault) as conn:
        source = conn.execute(
            "SELECT citekey, check_status, identifiers_json FROM catalog_sources WHERE work_id = ?",
            ("doi-10.1000_harness.2026",),
        ).fetchone()
        enrich = conn.execute(
            "SELECT status, operation_id, actor FROM operation_requests WHERE request_id = ?",
            ("enrich-doi-10.1000_harness.2026",),
        ).fetchone()
    assert source["citekey"] == "harness2026"
    assert source["check_status"] == "unchecked"
    assert json.loads(source["identifiers_json"]) == {"doi": "10.1000/harness.2026"}
    assert tuple(enrich) == ("pending", "enrich-source", "operation")
    assert done["enrichment_job"]["job_id"] == "enrich-doi-10.1000_harness.2026"
    committed = set(git(vault, "show", "--name-only", "--format=", done["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL}


def test_worker_runs_capture_url_source_operation_jobs(tmp_path: Path, monkeypatch) -> None:
    vault = workspace(tmp_path)

    def fake_read(url: str, timeout: float) -> bytes:
        assert url == "https://example.test/path/page"
        assert timeout == 2.0
        return b"<html><head><title>Worker URL</title></head><body>Worker page text.</body></html>"

    monkeypatch.setattr("memoria_vault.runtime.capture._read_url_bytes", fake_read)

    queued = enqueue_operation(
        vault,
        "capture-url-source",
        payload={
            "url": "https://example.test/path/page",
            "timeout": 2,
            "run_id": "capture-url",
        },
        idempotency_key="capture-url",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["work_id"] == "url-example.test-path-page"
    assert done["check_status"] == "unchecked"
    assert not (vault / "catalog/sources/url-example.test-path-page/source.md").exists()
    source = state.catalog_source(vault, "url-example.test-path-page")
    assert source is not None
    assert source["title"] == "Worker URL"
    assert source["resource"] == "https://example.test/path/page"
    assert "Worker page text." in (vault / done["content_path"]).read_text(encoding="utf-8")


def test_worker_rejects_capture_url_source_outside_allowed_network(
    tmp_path: Path, monkeypatch
) -> None:
    vault = workspace(tmp_path)
    policy = {
        **load_operation_policy(vault, "capture-url-source"),
        "allowed_network": ["https://allowed.test/"],
    }
    monkeypatch.setattr(
        "memoria_vault.runtime.operations.load_operation_policy",
        lambda _vault, _operation_id: policy,
    )

    def forbidden_fetch(_url: str, _timeout: float) -> bytes:
        raise AssertionError("network policy should block before URL fetch")

    monkeypatch.setattr("memoria_vault.runtime.capture._read_url_bytes", forbidden_fetch)
    enqueue_operation(
        vault,
        "capture-url-source",
        payload={"url": "http://blocked.test/source", "run_id": "capture-blocked-url"},
        idempotency_key="capture-blocked-url",
        actor="pi",
    )

    done = run_next_job(vault, machine="test-machine")

    assert done is not None
    assert done["status"] == "failed"
    assert "cannot access http://blocked.test/source" in done["error"]
    assert not (vault / "catalog/sources/url-blocked.test-source").exists()
