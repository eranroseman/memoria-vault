from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.enrichment import (
    _provider_endpoint,
    load_provider_config,
    provider_allowlist_issues,
)
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.operations import load_operation_policy
from memoria_vault.runtime.worker import enqueue_operation, run_next_job

ROOT = Path(__file__).resolve().parent.parent


def workspace(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "vault-template/.memoria/schemas", tmp_path / ".memoria/schemas")
    shutil.copytree(ROOT / "vault-template/.memoria/enrichment", tmp_path / ".memoria/enrichment")
    shutil.copytree(ROOT / "vault-template/capabilities", tmp_path / "capabilities")
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "alpha13@example.invalid")
    git(tmp_path, "config", "user.name", "Alpha13")
    git(tmp_path, "add", ".memoria/schemas", ".memoria/enrichment", "capabilities")
    git(tmp_path, "commit", "-m", "seed alpha13 workspace")
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


def doi_payload() -> dict:
    return {
        "source_id": "source-alpha",
        "title": "Alpha Source",
        "description": "A fixture DOI source.",
        "content_text": "Extracted alpha text.",
        "raw_text": "raw alpha bytes",
        "raw_filename": "alpha.txt",
        "resource": "https://doi.org/10.1000/alpha",
        "identifiers": {"doi": "10.1000/alpha"},
        "citekey": "alpha2026",
        "run_id": "capture-alpha",
    }


def provider_payloads(*, title: str = "Alpha Source", retracted: bool = False) -> dict:
    return {
        "crossref": {
            "message": {
                "DOI": "10.1000/alpha",
                "URL": "https://doi.org/10.1000/alpha",
                "type": "journal-article",
                "title": [title],
                "container-title": ["Journal of Testable Systems"],
                "author": [
                    {
                        "given": "Ada",
                        "family": "River",
                        "ORCID": "https://orcid.org/0000-0002-1825-0097",
                    }
                ],
                "issued": {"date-parts": [[2026]]},
                "relation": {"is-retracted-by": [{"id": "10.1000/retraction"}]}
                if retracted
                else {},
            }
        },
        "openalex": {
            "id": "https://openalex.org/W123",
            "doi": "https://doi.org/10.1000/alpha",
            "title": "Alpha Source",
            "authorships": [
                {
                    "author": {
                        "id": "https://openalex.org/A123",
                        "display_name": "Ada River",
                        "orcid": "https://orcid.org/0000-0002-1825-0097",
                    },
                    "institutions": [
                        {
                            "id": "https://ror.org/03yrm5c26",
                            "ror": "https://ror.org/03yrm5c26",
                            "display_name": "Example University",
                        }
                    ],
                }
            ],
            "primary_location": {
                "source": {
                    "display_name": "Journal of Testable Systems",
                    "issn_l": "1234-5678",
                }
            },
            "topics": [{"display_name": "Research workflows"}],
        },
        "unpaywall": {
            "doi": "10.1000/alpha",
            "is_oa": True,
            "oa_status": "gold",
            "best_oa_location": {
                "url_for_pdf": "https://example.test/alpha.pdf",
                "license": "cc-by",
            },
        },
    }


def test_capture_source_stages_doi_unchecked_without_references(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    enqueue_operation(
        vault, "capture-source", payload=doi_payload(), idempotency_key="capture-alpha"
    )
    done = run_next_job(vault, machine="test-machine")

    assert done is not None
    assert done["status"] == "done"
    assert done["check_status"] == "unchecked"
    assert done["source_id"] == "source-alpha"
    assert done["content_path"].startswith(".memoria/blobs/source-content/source-alpha/")
    assert not (vault / "catalog/sources/source-alpha/source.md").exists()
    assert not (vault / "references.bib").exists()
    with state.connect(vault) as conn:
        row = conn.execute(
            "SELECT title, doi, check_status, content_path FROM catalog_sources"
        ).fetchone()
    assert tuple(row) == ("Alpha Source", "10.1000/alpha", "unchecked", done["content_path"])


def test_enrich_source_manifest_and_provider_allowlist_agree() -> None:
    vault = ROOT / "vault-template"

    policy = load_operation_policy(vault, "enrich-source")
    config = load_provider_config(vault)

    assert policy["operation_id"] == "enrich-source"
    assert provider_allowlist_issues(config, policy) == []


def test_provider_endpoint_uses_configured_env_query_params(monkeypatch) -> None:
    config = load_provider_config(ROOT / "vault-template")
    monkeypatch.setenv("NCBI_EMAIL", "pi@example.test")
    monkeypatch.setenv("OPENALEX_API_KEY", "openalex-key")

    crossref_endpoint = _provider_endpoint(config, "crossref", "10.1000/alpha")
    openalex_endpoint = _provider_endpoint(config, "openalex", "10.1000/alpha")
    unpaywall_endpoint = _provider_endpoint(config, "unpaywall", "10.1000/alpha")

    assert crossref_endpoint.endswith("?mailto=pi%40example.test")
    assert "api_key=openalex-key" in openalex_endpoint
    assert "mailto=pi%40example.test" in openalex_endpoint
    assert unpaywall_endpoint.endswith("?email=pi%40example.test")


def test_enrich_source_requires_all_doi_providers(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    enqueue_operation(
        vault, "capture-source", payload=doi_payload(), idempotency_key="capture-alpha"
    )
    run_next_job(vault, machine="test-machine")

    enqueue_operation(
        vault,
        "enrich-source",
        payload={
            "source_id": "source-alpha",
            "provider_payloads": {
                key: value for key, value in provider_payloads().items() if key != "unpaywall"
            },
        },
        idempotency_key="enrich-alpha",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done is not None
    assert done["status"] == "done"
    assert done["enrichment_status"] == "needs_human"
    with state.connect(vault) as conn:
        row = conn.execute(
            "SELECT check_status FROM catalog_sources WHERE source_id = 'source-alpha'"
        ).fetchone()
    assert row["check_status"] == "unchecked"
    events = list(iter_jsonl(vault / "journal/test-machine.jsonl"))
    assert events[-1]["event"] == "check-fired"
    assert "missing required provider: unpaywall" in events[-1]["reason"]
    assert done["attention_path"].startswith("inbox/flag-enrichment-source-alpha-")
    attention = vault / done["attention_path"]
    assert attention.is_file()
    assert "Required DOI provider payloads did not all resolve." in attention.read_text(
        encoding="utf-8"
    )
    committed = set(git(vault, "show", "--name-only", "--format=", done["commit"]).splitlines())
    assert committed == {
        "inbox/flag-enrichment-source-alpha-source-enrichment.md",
        "journal/test-machine.jsonl",
    }


def test_enrich_source_writes_payloads_provenance_and_references(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    enqueue_operation(
        vault, "capture-source", payload=doi_payload(), idempotency_key="capture-alpha"
    )
    run_next_job(vault, machine="test-machine")

    enqueue_operation(
        vault,
        "enrich-source",
        payload={"source_id": "source-alpha", "provider_payloads": provider_payloads()},
        idempotency_key="enrich-alpha",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done is not None
    assert done["status"] == "done"
    assert done["enrichment_status"] == "enriched"
    assert done["references_path"] == "references.bib"
    assert "@article{alpha2026," in (vault / "references.bib").read_text(encoding="utf-8")
    with state.connect(vault) as conn:
        source = conn.execute(
            "SELECT check_status, metadata_status, csl_json FROM catalog_sources"
        ).fetchone()
        payload_rows = conn.execute(
            "SELECT provider, raw_hash, raw_path FROM provider_payloads ORDER BY provider"
        ).fetchall()
        provenance = conn.execute(
            "SELECT field_path, winning_provider FROM field_provenance ORDER BY field_path"
        ).fetchall()
        external_ids = conn.execute(
            "SELECT namespace, value FROM external_ids ORDER BY namespace, value"
        ).fetchall()
        materialization = conn.execute(
            "SELECT materialization_status FROM outputs WHERE output_id = 'references.bib'"
        ).fetchone()

    assert source["check_status"] == "checked"
    assert source["metadata_status"] == "verified"
    assert json.loads(source["csl_json"])["title"] == "Alpha Source"
    assert [(row["provider"], row["raw_hash"].startswith("sha256:")) for row in payload_rows] == [
        ("crossref", True),
        ("openalex", True),
        ("unpaywall", True),
    ]
    for row in payload_rows:
        assert (vault / row["raw_path"]).is_file()
    assert ("title", "crossref") in [tuple(row) for row in provenance]
    assert ("doi", "10.1000/alpha") in [tuple(row) for row in external_ids]
    assert materialization["materialization_status"] == "materialized"
    committed = set(git(vault, "show", "--name-only", "--format=", done["commit"]).splitlines())
    assert committed == {"journal/test-machine.jsonl", "references.bib"}


def test_enrich_source_blocks_retracted_doi(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    enqueue_operation(
        vault, "capture-source", payload=doi_payload(), idempotency_key="capture-alpha"
    )
    run_next_job(vault, machine="test-machine")

    enqueue_operation(
        vault,
        "enrich-source",
        payload={
            "source_id": "source-alpha",
            "provider_payloads": provider_payloads(retracted=True),
        },
        idempotency_key="enrich-alpha",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done is not None
    assert done["status"] == "done"
    assert done["enrichment_status"] == "contested"
    with state.connect(vault) as conn:
        row = conn.execute(
            "SELECT check_status, metadata_status FROM catalog_sources WHERE source_id = 'source-alpha'"
        ).fetchone()
    assert tuple(row) == ("unchecked", "unverified")
    events = list(iter_jsonl(vault / "journal/test-machine.jsonl"))
    assert events[-1]["event"] == "check-fired"
    assert events[-1]["check"] == "source-retraction"
    assert done["attention_path"] == "inbox/flag-enrichment-source-alpha-source-retraction.md"
    assert (vault / done["attention_path"]).is_file()
    committed = set(git(vault, "show", "--name-only", "--format=", done["commit"]).splitlines())
    assert committed == {
        "inbox/flag-enrichment-source-alpha-source-retraction.md",
        "journal/test-machine.jsonl",
    }
