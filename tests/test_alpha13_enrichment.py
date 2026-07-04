from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.capture import render_references_bib
from memoria_vault.runtime.enrichment import (
    _optional_providers,
    _provider_endpoint,
    load_provider_config,
    provider_allowlist_issues,
    replay_enrichment_run,
)
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.operations import load_operation_policy
from memoria_vault.runtime.worker import enqueue_operation, run_next_job

ROOT = Path(__file__).resolve().parent.parent


def sha_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def workspace(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "vault-template/.memoria/schemas", tmp_path / ".memoria/schemas")
    shutil.copytree(ROOT / "vault-template/.memoria/config", tmp_path / ".memoria/config")
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "alpha13@example.invalid")
    git(tmp_path, "config", "user.name", "Alpha13")
    git(tmp_path, "add", ".memoria/schemas", ".memoria/config")
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


def allow_example_full_text(monkeypatch) -> None:
    original = load_operation_policy
    policy = {
        **original(Path(), "enrich-source"),
        "allowed_network": [
            *original(Path(), "enrich-source")["allowed_network"],
            "https://example.test/",
        ],
    }

    def load_policy(vault: Path, operation_id: str) -> dict:
        if operation_id == "enrich-source":
            return policy
        return original(vault, operation_id)

    monkeypatch.setattr("memoria_vault.runtime.operations.load_operation_policy", load_policy)


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


def provider_payloads(
    *, title: str = "Alpha Source", retracted: bool = False, full_text: str = ""
) -> dict:
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
                "relation": {"is-retracted-by": [{"id": "10.1000/retraction", "id-type": "doi"}]}
                if retracted
                else {"is-preprint-of": [{"id": "10.1000/preprint", "id-type": "doi"}]},
                "reference": [
                    {
                        "DOI": "10.1000/beta",
                        "article-title": "Beta Reference",
                    }
                ],
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
            "referenced_works": ["https://openalex.org/W999"],
            "related_works": ["https://openalex.org/W888"],
            "primary_topic": {
                "id": "https://openalex.org/T321",
                "display_name": "Knowledge management",
                "subfield": {"display_name": "Information systems"},
                "field": {"display_name": "Computer science"},
                "domain": {"display_name": "Physical sciences"},
                "score": 0.91,
            },
            "topics": [{"id": "https://openalex.org/T123", "display_name": "Research workflows"}],
            "concepts": [
                {
                    "id": "https://openalex.org/C123",
                    "display_name": "Information retrieval",
                    "score": 0.82,
                }
            ],
            "keywords": [{"id": "https://openalex.org/K123", "display_name": "research workflow"}],
            "mesh": [
                {
                    "descriptor_ui": "D012345",
                    "descriptor_name": "Bibliometrics",
                    "qualifier_name": "methods",
                    "is_major_topic": True,
                }
            ],
            "sustainable_development_goals": [
                {
                    "id": "https://metadata.un.org/sdg/4",
                    "display_name": "Quality Education",
                    "score": 0.71,
                }
            ],
        },
        "unpaywall": {
            "doi": "10.1000/alpha",
            "is_oa": True,
            "oa_status": "gold",
            "best_oa_location": {
                "url_for_pdf": "https://example.test/alpha.pdf",
                "license": "cc-by",
                **({"full_text": full_text} if full_text else {}),
            },
        },
    }


def semantic_scholar_payload() -> dict:
    return {
        "paperId": "S2-ALPHA",
        "title": "Alpha Source",
        "tldr": {"text": "Semantic Scholar TLDR for Alpha."},
        "references": [
            {
                "paperId": "S2-DELTA",
                "title": "Delta Semantic Reference",
                "externalIds": {"DOI": "10.1000/delta"},
            }
        ],
        "citations": [
            {
                "paperId": "S2-GAMMA",
                "title": "Gamma Semantic Citation",
                "externalIds": {"DOI": "10.1000/gamma"},
            }
        ],
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
    assert done["text_status"] == "full-text"
    assert done["content_path"].startswith(".memoria/blobs/source-content/source-alpha/")
    assert not (vault / "catalog/sources/source-alpha/source.md").exists()
    assert not (vault / "references.bib").exists()
    with state.connect(vault) as conn:
        row = conn.execute(
            "SELECT title, doi, check_status, text_status, content_path FROM catalog_sources"
        ).fetchone()
    assert tuple(row) == (
        "Alpha Source",
        "10.1000/alpha",
        "unchecked",
        "full-text",
        done["content_path"],
    )


def test_enrich_source_manifest_and_provider_allowlist_agree() -> None:
    vault = ROOT / "vault-template"

    policy = load_operation_policy(vault, "enrich-source")
    config = load_provider_config(vault)

    assert policy["operation_id"] == "enrich-source"
    assert provider_allowlist_issues(config, policy) == []


def test_provider_allowlist_rejects_host_prefix_bypass() -> None:
    policy = {
        "operation_id": "enrich-source",
        "allowed_network": ["https://api.openalex.org/"],
    }
    config = {
        "providers": {
            "openalex": {
                "enabled": True,
                "base_url": "https://api.openalex.org.evil/",
            }
        }
    }

    assert provider_allowlist_issues(config, policy) == [
        "openalex base_url not allowed: https://api.openalex.org.evil/"
    ]


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


def test_semantic_scholar_optional_provider_is_default_on_only_when_keyed(
    monkeypatch,
) -> None:
    config = load_provider_config(ROOT / "vault-template")

    monkeypatch.delenv("SEMANTIC_SCHOLAR_API_KEY", raising=False)
    assert _optional_providers(config, "doi", {}) == []
    assert _optional_providers(config, "doi", {"semanticscholar": {}}) == ["semanticscholar"]

    monkeypatch.setenv("SEMANTIC_SCHOLAR_API_KEY", "semantic-key")
    assert _optional_providers(config, "doi", {}) == ["semanticscholar"]


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
        state.JOURNAL_HEAD_REL,
    }


def test_enrich_source_replays_optional_semantic_scholar_payload(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    enqueue_operation(
        vault, "capture-source", payload=doi_payload(), idempotency_key="capture-alpha"
    )
    run_next_job(vault, machine="test-machine")
    payloads = {**provider_payloads(), "semanticscholar": semantic_scholar_payload()}

    enqueue_operation(
        vault,
        "enrich-source",
        payload={"source_id": "source-alpha", "provider_payloads": payloads},
        idempotency_key="enrich-alpha",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done is not None
    assert done["status"] == "done"
    assert done["optional_provider_failures"] == []
    with state.connect(vault) as conn:
        providers = [
            row["provider"]
            for row in conn.execute("SELECT provider FROM provider_payloads ORDER BY provider")
        ]
        semantic_id = conn.execute(
            """
            SELECT value FROM external_ids
            WHERE namespace = 'semanticscholar' AND owner_id = 'source-alpha'
            """
        ).fetchone()
        semantic_edges = [
            tuple(row)
            for row in conn.execute(
                """
                SELECT relation_type, target_id, target_title FROM work_graph_edges
                WHERE source_provider = 'semanticscholar'
                ORDER BY relation_type, target_id
                """
            )
        ]
    assert providers == ["crossref", "openalex", "semanticscholar", "unpaywall"]
    assert semantic_id["value"] == "S2-ALPHA"
    assert semantic_edges == [
        ("references", "doi:10.1000/delta", "Delta Semantic Reference"),
        ("related", "doi:10.1000/gamma", "Gamma Semantic Citation"),
    ]


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
            "SELECT check_status, provider_coverage, csl_json FROM catalog_sources"
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
        graph_edges = conn.execute(
            "SELECT relation_type, target_id FROM work_graph_edges ORDER BY relation_type, target_id"
        ).fetchall()
        mesh_sdg_edges = conn.execute(
            """
            SELECT target_id, target_title
            FROM work_graph_edges
            WHERE target_id IN ('mesh:D012345', 'https://metadata.un.org/sdg/4')
            ORDER BY target_id
            """
        ).fetchall()
        discovered = conn.execute(
            "SELECT check_status FROM catalog_sources WHERE source_id IN ('W888', 'W999')"
        ).fetchall()

    assert source["check_status"] == "checked"
    assert source["provider_coverage"] == "full"
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
    assert [tuple(row) for row in graph_edges] == [
        ("authorship", "https://openalex.org/A123"),
        ("institution", "https://ror.org/03yrm5c26"),
        ("keyword", "https://openalex.org/K123"),
        ("references", "doi:10.1000/beta"),
        ("references", "https://openalex.org/W999"),
        ("related", "doi:10.1000/preprint"),
        ("related", "https://openalex.org/W888"),
        ("source", "1234-5678"),
        ("topic", "https://metadata.un.org/sdg/4"),
        ("topic", "https://openalex.org/C123"),
        ("topic", "https://openalex.org/T123"),
        ("topic", "https://openalex.org/T321"),
        ("topic", "mesh:D012345"),
    ]
    assert [tuple(row) for row in mesh_sdg_edges] == [
        ("https://metadata.un.org/sdg/4", "Quality Education"),
        ("mesh:D012345", "Bibliometrics / methods"),
    ]
    assert discovered == []
    assert len(done["discovery_candidate_paths"]) == 4
    for rel in done["discovery_candidate_paths"]:
        text = (vault / rel).read_text(encoding="utf-8")
        assert "projection: attention" in text
        assert "attention_kind: candidate" in text
    committed = set(git(vault, "show", "--name-only", "--format=", done["commit"]).splitlines())
    assert committed == {
        *done["discovery_candidate_paths"],
        state.JOURNAL_HEAD_REL,
        "references.bib",
    }


def test_enrich_source_replays_provider_payload_blobs(tmp_path: Path) -> None:
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

    replay = replay_enrichment_run(vault, done["run_id"])

    with state.connect(vault) as conn:
        source = conn.execute("SELECT csl_json FROM catalog_sources").fetchone()
        normalized = conn.execute(
            "SELECT provider, normalized_json FROM provider_payloads ORDER BY provider"
        ).fetchall()
        projection = conn.execute(
            "SELECT output_sha256 FROM outputs WHERE output_id = 'references.bib'"
        ).fetchone()
        [payload_row] = conn.execute(
            "SELECT raw_path FROM provider_payloads WHERE provider = 'openalex'"
        ).fetchall()

    assert replay["canonical"]["csl_json"] == json.loads(source["csl_json"])
    assert replay["normalized"] == {
        row["provider"]: json.loads(row["normalized_json"]) for row in normalized
    }
    assert projection["output_sha256"] == sha_text(render_references_bib(vault))

    (vault / payload_row["raw_path"]).unlink()
    with pytest.raises(RuntimeError, match="provider payload blob missing"):
        replay_enrichment_run(vault, done["run_id"])


def test_enrich_source_conflict_degrades_without_human_checked_bypass(tmp_path: Path) -> None:
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
            "provider_payloads": provider_payloads(title="Crossref Disagreement"),
        },
        idempotency_key="enrich-alpha",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done["enrichment_status"] == "needs_human"
    assert done["attention_path"] == "inbox/flag-enrichment-source-alpha-source-enrichment.md"
    with state.connect(vault) as conn:
        row = conn.execute(
            "SELECT check_status, provider_coverage FROM catalog_sources WHERE source_id = ?",
            ("source-alpha",),
        ).fetchone()
        title_provenance = conn.execute(
            """
            SELECT evidence_payload_id, alternatives_json, conflict_status
            FROM field_provenance
            WHERE source_id = ? AND field_path = 'title'
            """,
            ("source-alpha",),
        ).fetchone()
        payload_hashes = {
            row["provider"]: row["raw_hash"]
            for row in conn.execute("SELECT provider, raw_hash FROM provider_payloads")
        }
    assert tuple(row) == ("unchecked", "degraded")
    assert title_provenance["evidence_payload_id"] == payload_hashes["crossref"]
    assert title_provenance["conflict_status"] == "conflict"
    assert json.loads(title_provenance["alternatives_json"]) == [
        {
            "provider": "openalex",
            "value": "Alpha Source",
            "evidence_payload_id": payload_hashes["openalex"],
        }
    ]
    attention_text = (vault / done["attention_path"]).read_text(encoding="utf-8")
    assert payload_hashes["crossref"] in attention_text
    assert payload_hashes["openalex"] in attention_text

    enqueue_operation(
        vault,
        "update-work",
        payload={
            "source_id": "source-alpha",
            "provider_coverage": "degraded",
            "check_status": "checked",
        },
        idempotency_key="accept-degraded-alpha",
    )
    failed = run_next_job(vault, machine="test-machine")

    assert failed["status"] == "failed"
    assert "degraded provider coverage cannot set checked" in failed["error"]


def test_enrich_source_blocks_abstract_only_text_without_acquired_full_text(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    payload = {
        **doi_payload(),
        "content_text": "Only the abstract.",
        "text_status": "abstract-only",
    }
    enqueue_operation(vault, "capture-source", payload=payload, idempotency_key="capture-alpha")
    run_next_job(vault, machine="test-machine")
    enqueue_operation(
        vault,
        "enrich-source",
        payload={"source_id": "source-alpha", "provider_payloads": provider_payloads()},
        idempotency_key="enrich-alpha",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done["enrichment_status"] == "needs_human"
    assert "source-full-text" in done["attention_path"]
    assert "full-text acquisition failed" in done["finding"]["reason"]
    with state.connect(vault) as conn:
        row = conn.execute(
            "SELECT check_status, text_status FROM catalog_sources WHERE source_id = 'source-alpha'"
        ).fetchone()
    assert tuple(row) == ("unchecked", "abstract-only")
    assert not (vault / "references.bib").exists()
    assert not (vault / "knowledge/works/source-alpha.md").exists()


def test_enrich_source_acquires_replayed_full_text(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    payload = {
        **doi_payload(),
        "content_text": "Only the abstract.",
        "text_status": "abstract-only",
    }
    enqueue_operation(vault, "capture-source", payload=payload, idempotency_key="capture-alpha")
    run_next_job(vault, machine="test-machine")
    full_text = "Acquired alpha full text about framing, methods, outcomes, gaps, and impact."

    enqueue_operation(
        vault,
        "enrich-source",
        payload={
            "source_id": "source-alpha",
            "provider_payloads": provider_payloads(full_text=full_text),
        },
        idempotency_key="enrich-alpha",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done is not None
    assert done["enrichment_status"] == "enriched"
    assert done["text_status"] == "full-text"
    assert (vault / done["content_path"]).read_text(encoding="utf-8") == full_text + "\n"
    with state.connect(vault) as conn:
        row = conn.execute(
            "SELECT check_status, text_status, content_path FROM catalog_sources "
            "WHERE source_id = 'source-alpha'"
        ).fetchone()
    assert tuple(row) == ("checked", "full-text", done["content_path"])


def test_enrich_source_fetches_allowed_open_access_text(tmp_path: Path, monkeypatch) -> None:
    vault = workspace(tmp_path)
    allow_example_full_text(monkeypatch)
    payload = {
        **doi_payload(),
        "content_text": "Only the abstract.",
        "text_status": "abstract-only",
    }
    enqueue_operation(vault, "capture-source", payload=payload, idempotency_key="capture-alpha")
    run_next_job(vault, machine="test-machine")
    html = (
        "<html><body><article>Fetched open access full text about framing, "
        "methods, outcomes, gaps, and impact.</article></body></html>"
    )

    class Response:
        def __init__(self):
            self.headers = {"Content-Type": "text/html; charset=utf-8"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return html.encode()

    def fake_urlopen(req, timeout):
        assert req.full_url == "https://example.test/alpha.pdf"
        assert timeout == 20
        return Response()

    monkeypatch.setattr("memoria_vault.runtime.enrichment.request.urlopen", fake_urlopen)

    enqueue_operation(
        vault,
        "enrich-source",
        payload={"source_id": "source-alpha", "provider_payloads": provider_payloads()},
        idempotency_key="enrich-alpha",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done is not None
    assert done["enrichment_status"] == "enriched"
    content = (vault / done["content_path"]).read_text(encoding="utf-8")
    assert "Fetched open access full text" in content


def test_enrich_source_tries_next_open_access_text_url(tmp_path: Path, monkeypatch) -> None:
    vault = workspace(tmp_path)
    allow_example_full_text(monkeypatch)
    payload = {
        **doi_payload(),
        "content_text": "Only the abstract.",
        "text_status": "abstract-only",
    }
    enqueue_operation(vault, "capture-source", payload=payload, idempotency_key="capture-alpha")
    run_next_job(vault, machine="test-machine")
    providers = provider_payloads()
    providers["unpaywall"]["best_oa_location"] = {
        "url_for_pdf": "https://example.test/empty.txt",
        "url_for_landing_page": "https://example.test/full.html",
    }
    calls = []

    class Response:
        def __init__(self, body: str):
            self.body = body
            self.headers = {"Content-Type": "text/html; charset=utf-8"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return self.body.encode()

    def fake_urlopen(req, timeout):
        calls.append(req.full_url)
        assert timeout == 20
        if req.full_url.endswith("/empty.txt"):
            return Response("")
        return Response("<html><body>Fallback open access full text.</body></html>")

    monkeypatch.setattr("memoria_vault.runtime.enrichment.request.urlopen", fake_urlopen)

    enqueue_operation(
        vault,
        "enrich-source",
        payload={"source_id": "source-alpha", "provider_payloads": providers},
        idempotency_key="enrich-alpha",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done["enrichment_status"] == "enriched"
    assert calls == ["https://example.test/empty.txt", "https://example.test/full.html"]
    assert "Fallback open access full text" in (vault / done["content_path"]).read_text(
        encoding="utf-8"
    )


def test_enrich_source_fetches_open_access_locations_list(tmp_path: Path, monkeypatch) -> None:
    vault = workspace(tmp_path)
    allow_example_full_text(monkeypatch)
    payload = {
        **doi_payload(),
        "content_text": "Only the abstract.",
        "text_status": "abstract-only",
    }
    enqueue_operation(vault, "capture-source", payload=payload, idempotency_key="capture-alpha")
    run_next_job(vault, machine="test-machine")
    providers = provider_payloads()
    providers["unpaywall"]["best_oa_location"] = {
        "url_for_fulltext": "https://blocked.test/full.html",
    }
    providers["unpaywall"]["oa_locations"] = [
        {"url_for_fulltext": "https://blocked.test/full.html"},
        {"url_for_landing_page": "https://example.test/list.html"},
    ]
    calls = []

    class Response:
        def __init__(self):
            self.headers = {"Content-Type": "text/html; charset=utf-8"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b"<html><body>Listed open access full text.</body></html>"

    def fake_urlopen(req, timeout):
        calls.append(req.full_url)
        assert timeout == 20
        return Response()

    monkeypatch.setattr("memoria_vault.runtime.enrichment.request.urlopen", fake_urlopen)

    enqueue_operation(
        vault,
        "enrich-source",
        payload={"source_id": "source-alpha", "provider_payloads": providers},
        idempotency_key="enrich-alpha",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done["enrichment_status"] == "enriched"
    assert calls == ["https://example.test/list.html"]
    assert "Listed open access full text" in (vault / done["content_path"]).read_text(
        encoding="utf-8"
    )


def test_enrich_source_fetches_openalex_open_access_location(tmp_path: Path, monkeypatch) -> None:
    vault = workspace(tmp_path)
    allow_example_full_text(monkeypatch)
    payload = {
        **doi_payload(),
        "content_text": "Only the abstract.",
        "text_status": "abstract-only",
    }
    enqueue_operation(vault, "capture-source", payload=payload, idempotency_key="capture-alpha")
    run_next_job(vault, machine="test-machine")
    providers = provider_payloads()
    providers["unpaywall"]["best_oa_location"] = {
        "url_for_fulltext": "https://blocked.test/full.html",
    }
    providers["openalex"]["open_access"] = {
        "is_oa": True,
        "oa_url": "https://blocked.test/openalex.html",
    }
    providers["openalex"]["primary_location"] = {
        "is_oa": False,
        "pdf_url": "https://example.test/closed.pdf",
    }
    providers["openalex"]["locations"] = [
        {
            "is_oa": True,
            "landing_page_url": "https://example.test/openalex.html",
        }
    ]
    calls = []

    class Response:
        def __init__(self):
            self.headers = {"Content-Type": "text/html; charset=utf-8"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b"<html><body>OpenAlex discovered full text.</body></html>"

    def fake_urlopen(req, timeout):
        calls.append(req.full_url)
        assert timeout == 20
        return Response()

    monkeypatch.setattr("memoria_vault.runtime.enrichment.request.urlopen", fake_urlopen)

    enqueue_operation(
        vault,
        "enrich-source",
        payload={"source_id": "source-alpha", "provider_payloads": providers},
        idempotency_key="enrich-alpha",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done["enrichment_status"] == "enriched"
    assert calls == ["https://example.test/openalex.html"]
    assert "OpenAlex discovered full text" in (vault / done["content_path"]).read_text(
        encoding="utf-8"
    )


def test_enrich_source_fetches_crossref_full_text_link(tmp_path: Path, monkeypatch) -> None:
    vault = workspace(tmp_path)
    allow_example_full_text(monkeypatch)
    payload = {
        **doi_payload(),
        "content_text": "Only the abstract.",
        "text_status": "abstract-only",
    }
    enqueue_operation(vault, "capture-source", payload=payload, idempotency_key="capture-alpha")
    run_next_job(vault, machine="test-machine")
    providers = provider_payloads()
    providers["unpaywall"]["best_oa_location"] = {
        "url_for_fulltext": "https://blocked.test/full.html",
    }
    providers["openalex"]["open_access"] = {}
    providers["openalex"]["primary_location"] = {"is_oa": False}
    providers["openalex"]["locations"] = []
    providers["crossref"]["message"]["link"] = [
        {
            "URL": "https://example.test/crossref.html",
            "content-type": "text/html",
            "intended-application": "text-mining",
        }
    ]
    calls = []

    class Response:
        def __init__(self):
            self.headers = {"Content-Type": "text/html; charset=utf-8"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b"<html><body>Crossref full text link body.</body></html>"

    def fake_urlopen(req, timeout):
        calls.append(req.full_url)
        assert timeout == 20
        return Response()

    monkeypatch.setattr("memoria_vault.runtime.enrichment.request.urlopen", fake_urlopen)

    enqueue_operation(
        vault,
        "enrich-source",
        payload={"source_id": "source-alpha", "provider_payloads": providers},
        idempotency_key="enrich-alpha",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done["enrichment_status"] == "enriched"
    assert calls == ["https://example.test/crossref.html"]
    assert "Crossref full text link body" in (vault / done["content_path"]).read_text(
        encoding="utf-8"
    )


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
            "SELECT check_status, provider_coverage FROM catalog_sources WHERE source_id = 'source-alpha'"
        ).fetchone()
    assert tuple(row) == ("unchecked", "full")
    events = list(iter_jsonl(vault / "journal/test-machine.jsonl"))
    assert events[-1]["event"] == "check-fired"
    assert events[-1]["check"] == "source-retraction"
    assert done["attention_path"] == "inbox/flag-enrichment-source-alpha-source-retraction.md"
    assert (vault / done["attention_path"]).is_file()
    committed = set(git(vault, "show", "--name-only", "--format=", done["commit"]).splitlines())
    assert committed == {
        "inbox/flag-enrichment-source-alpha-source-retraction.md",
        state.JOURNAL_HEAD_REL,
    }
