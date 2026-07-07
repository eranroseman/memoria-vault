from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.capture import (
    capture_bibtex_source,
    capture_pdf_source,
    capture_source,
    capture_url_source,
    check_references_bib,
    render_references_bib,
    write_references_bib,
)
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.policy.audit import sha256_file
from tests.helpers import copy_memoria_dirs, git, init_git


def workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas")
    init_git(tmp_path, "capture@example.invalid", "Capture")
    return tmp_path


def test_capture_source_writes_catalog_db_row_and_blobs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    result = capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Extracted alpha text.\n",
        raw_bytes=b"raw alpha bytes",
        raw_filename="alpha.txt",
        resource="https://example.test/alpha",
        item_type="article",
        identifiers={"doi": "10.0000/alpha"},
        csl_json={"id": "alpha"},
        citekey="alpha2026",
        machine="test-machine",
        run_id="capture-alpha",
    )

    content = vault / ".memoria/blobs/source-content/source-alpha/content.txt"
    raw = vault / ".memoria/blobs/source-content/source-alpha/raw/alpha.txt"
    source = state.catalog_source(vault, "source-alpha")

    assert result["source_path"] == "catalog/sources/source-alpha"
    assert result["check_status"] == "checked"
    assert source is not None
    assert source["check_status"] == "checked"
    assert source["work_id"] == "source-alpha"
    assert source["item_type"] == "article"
    assert source["raw_path"] == ".memoria/blobs/source-content/source-alpha/raw/alpha.txt"
    assert source["content_path"] == ".memoria/blobs/source-content/source-alpha/content.txt"
    assert source["raw_text_sha256"] == sha256_file(raw)
    assert source["normalized_text_sha256"] == sha256_file(content)
    assert content.read_text(encoding="utf-8") == "Extracted alpha text.\n"
    assert raw.read_bytes() == b"raw alpha bytes"
    assert not (vault / "catalog/sources/source-alpha/source.md").exists()
    assert not (vault / "references.bib").exists()

    events = list(iter_jsonl(vault / "journal/test-machine.jsonl"))
    assert [event["event"] for event in events] == ["run", "run"]
    assert events[0]["status"] == "started"
    assert events[-1]["status"] == "done"
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL}


def test_capture_source_populates_work_aspect_read_model(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "# Paper\n\n## Method\n\nInterview coding.\n\n## Results\n\nCare pathways changed.\n",
        csl_json={
            "id": "alpha",
            "memoria": {
                "aspects": {
                    "key_idea": "Coordination work is visible in local traces.",
                    "projected_impact": "Excluded from the alpha.16 aspect model.",
                }
            },
        },
    )

    aspects = state.work_aspects(vault, "source-alpha")

    assert [(row["aspect_type"], row["aspect_text"]) for row in aspects] == [
        ("key_idea", "Coordination work is visible in local traces."),
        ("method", "Interview coding."),
        ("outcome", "Care pathways changed."),
    ]
    assert {row["check_status"] for row in aspects} == {"checked"}


def test_capture_source_rejects_removed_required_check_argument(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)

    with pytest.raises(TypeError, match="required_checks"):
        capture_source(
            vault,
            "source-alpha",
            "Alpha Source",
            "A fixture source.",
            "Extracted alpha text.",
            required_checks=["later-integrity"],
            machine="test-machine",
        )

    assert not (vault / "catalog/sources/source-alpha").exists()
    assert not (vault / "journal/test-machine.jsonl").exists()


def test_capture_source_refuses_to_replace_existing_raw(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Extracted alpha text.",
        raw_bytes=b"raw alpha bytes",
        machine="test-machine",
    )

    try:
        capture_source(
            vault,
            "source-alpha",
            "Alpha Source",
            "A fixture source.",
            "Extracted alpha text.",
            raw_bytes=b"different bytes",
            machine="test-machine",
        )
    except FileExistsError as exc:
        assert "source.txt" in str(exc)
    else:
        raise AssertionError("capture should not replace an existing raw blob")

    assert (
        vault / ".memoria/blobs/source-content/source-alpha/raw/source.txt"
    ).read_bytes() == b"raw alpha bytes"


def test_capture_pdf_source_derives_content(tmp_path: Path, monkeypatch) -> None:
    vault = workspace(tmp_path)

    monkeypatch.setattr(
        "memoria_vault.runtime.capture._extract_pdf_pages",
        lambda _raw: [
            {
                "page": 3,
                "text": "The PDF reports an anchored finding on page 3.",
            }
        ],
    )

    result = capture_pdf_source(
        vault,
        "pdf-source",
        "PDF Source",
        "A fixture PDF source.",
        b"%PDF-1.4 fixture bytes\n",
        raw_filename="paper.pdf",
        machine="test-machine",
    )

    assert result["content_path"] == ".memoria/blobs/source-content/pdf-source/content.txt"
    assert result["text_status"] == "full-text"
    assert "## Page 3" in (vault / result["content_path"]).read_text(encoding="utf-8")
    source = state.catalog_source(vault, result["work_id"])
    assert source is not None
    assert source["text_status"] == "full-text"
    assert source["raw_path"] == ".memoria/blobs/source-content/pdf-source/raw/paper.pdf"
    assert not (vault / "catalog/sources/pdf-source/source.md").exists()
    events = list(iter_jsonl(vault / "journal/test-machine.jsonl"))
    assert events[0]["workflow"] == "capture_pdf_source"
    assert events[-1]["workflow"] == "capture_pdf_source"


def test_capture_pdf_source_rejects_incoherent_parser_text(tmp_path: Path, monkeypatch) -> None:
    vault = workspace(tmp_path)

    monkeypatch.setattr(
        "memoria_vault.runtime.capture._extract_pdf_pages",
        lambda _raw: [{"page": 1, "text": "\ufffd\ufffd !!! ???", "blocks": []}],
    )

    try:
        capture_pdf_source(
            vault,
            "bad-pdf",
            "Bad PDF",
            "A broken PDF extraction.",
            b"%PDF-1.4 fixture bytes\n",
            machine="test-machine",
        )
    except ValueError as exc:
        assert "coherence check" in str(exc)
    else:
        raise AssertionError("incoherent PDF extraction should fail")

    assert not (vault / "journal").exists()
    assert not (vault / "catalog/sources/bad-pdf").exists()


def test_capture_source_validates_before_journaling(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    try:
        capture_source(vault, "bad", "Bad", "Missing content", "")
    except ValueError as exc:
        assert "content_text is required" in str(exc)
    else:
        raise AssertionError("empty content should fail")

    assert not (vault / "journal").exists()
    assert not (vault / "catalog/sources/bad").exists()


def test_capture_bibtex_source_maps_metadata_and_raw(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    bibtex = """@article{harness2026,
      title = {Harnessed Workflows for Durable Research},
      author = {Ada, River and Morgan Lin},
      year = {2026},
      journal = {Journal of Testable Systems},
      doi = {10.1000/harness.2026},
      abstract = {A fixture paper for the Memoria test environment harness.},
      references = {10.1000/beta; https://openalex.org/W999}
    }"""

    result = capture_bibtex_source(vault, bibtex, machine="test-machine")

    raw = vault / ".memoria/blobs/source-content/doi-10.1000_harness.2026/raw/harness2026.bib"
    source = state.catalog_source(vault, "doi-10.1000_harness.2026")

    assert result["source_path"] == "catalog/sources/doi-10.1000_harness.2026"
    assert result["check_status"] == "checked"
    assert source is not None
    assert source["check_status"] == "checked"
    assert source["title"] == "Harnessed Workflows for Durable Research"
    assert source["citekey"] == "harness2026"
    assert source["text_status"] == "abstract-only"
    assert source["resource"] == "https://doi.org/10.1000/harness.2026"
    assert source["identifiers"] == {"doi": "10.1000/harness.2026"}
    assert source["csl_json"]["author"] == [
        {"family": "Ada", "given": "River"},
        {"family": "Lin", "given": "Morgan"},
    ]
    with state.connect(vault) as conn:
        edges = conn.execute(
            """
            SELECT relation_type, target_id, target_doi, source_provider
            FROM work_graph_edges
            WHERE work_id = ?
            ORDER BY target_id
            """,
            ("doi-10.1000_harness.2026",),
        ).fetchall()
    assert [tuple(row) for row in edges] == [
        ("references", "doi:10.1000/beta", "10.1000/beta", "import"),
        ("references", "https://openalex.org/W999", "", "import"),
    ]
    assert raw.read_text(encoding="utf-8").startswith("@article{harness2026,")
    assert not (vault / "catalog/sources/doi-10.1000_harness.2026/source.md").exists()
    assert not (vault / "catalog/entities").exists()
    assert not (vault / "references.bib").exists()

    events = list(iter_jsonl(vault / "journal/test-machine.jsonl"))
    assert events[0]["workflow"] == "capture_bibtex_source"
    assert events[-1]["workflow"] == "capture_bibtex_source"


def test_capture_bibtex_source_does_not_create_entity_links(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    capture_bibtex_source(
        vault,
        """@article{first2026,
          title = {First Shared Entity Source},
          author = {Morgan Lin},
          year = {2026},
          journal = {Journal of Shared Metadata},
          doi = {10.1000/shared.one}
        }""",
        machine="test-machine",
    )

    capture_bibtex_source(
        vault,
        """@article{second2026,
          title = {Second Shared Entity Source},
          author = {Morgan Lin},
          year = {2026},
          journal = {Journal of Shared Metadata},
          doi = {10.1000/shared.two}
        }""",
        machine="test-machine",
    )

    assert state.catalog_source(vault, "doi-10.1000_shared.one") is not None
    assert state.catalog_source(vault, "doi-10.1000_shared.two") is not None
    assert not (vault / "catalog/entities/person-morgan-lin.md").exists()
    assert not (vault / "catalog/entities/venue-journal-of-shared-metadata.md").exists()


def test_capture_reference_edges_preserve_provider_graph(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Alpha source text.",
        csl_json={"id": "alpha", "title": "Alpha Source"},
        machine="test-machine",
    )
    state.replace_work_graph_edges(
        vault,
        "source-alpha",
        [
            {
                "relation_type": "references",
                "target_id": "doi:10.1000/provider",
                "target_title": "Provider Reference",
                "target_doi": "10.1000/provider",
                "source_provider": "openalex",
            },
            {
                "relation_type": "related",
                "target_id": "https://openalex.org/W9",
                "target_title": "Provider Related",
                "source_provider": "openalex",
            },
        ],
    )

    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Alpha source text.",
        csl_json={
            "id": "alpha",
            "title": "Alpha Source",
            "references": [
                {"DOI": "10.1000/provider", "title": "Imported duplicate"},
                {"DOI": "10.1000/imported", "title": "Imported Reference"},
            ],
        },
        machine="test-machine",
    )

    with state.connect(vault) as conn:
        edges = conn.execute(
            """
            SELECT relation_type, target_id, target_title, source_provider
            FROM work_graph_edges
            WHERE work_id = 'source-alpha'
            ORDER BY relation_type, target_id
            """
        ).fetchall()
    assert [tuple(row) for row in edges] == [
        ("references", "doi:10.1000/imported", "Imported Reference", "import"),
        ("references", "doi:10.1000/provider", "Provider Reference", "openalex"),
        ("related", "https://openalex.org/W9", "Provider Related", "openalex"),
    ]


def test_capture_source_does_not_materialize_entity_records(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "source-one",
        "First identity source",
        "A fixture source.",
        "First source text.",
        csl_json={
            "id": "one",
            "type": "article-journal",
            "title": "First identity source",
            "author": [
                {
                    "family": "River",
                    "given": "Ada",
                    "ORCID": "https://orcid.org/0000-0001-0000-0001",
                }
            ],
        },
        machine="test-machine",
    )
    capture_source(
        vault,
        "source-two",
        "Second identity source",
        "A fixture source.",
        "Second source text.",
        csl_json={
            "id": "two",
            "type": "article-journal",
            "title": "Second identity source",
            "author": [
                {
                    "family": "River",
                    "given": "Ada",
                    "ORCID": "0000-0002-0000-0002",
                }
            ],
        },
        machine="test-machine",
    )

    assert state.catalog_source(vault, "source-one") is not None
    assert state.catalog_source(vault, "source-two") is not None
    assert not (vault / "catalog/entities/person-ada-river.md").exists()


def test_recapturing_source_merges_existing_metadata(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Stable extracted text.",
        raw_bytes=b"stable raw bytes",
        raw_filename="alpha.txt",
        identifiers={"pmid": "12345"},
        csl_json={
            "id": "alpha",
            "type": "article-journal",
            "title": "Alpha Source",
            "author": [{"family": "Lin", "given": "Morgan"}],
        },
        provider_coverage="partial",
        machine="test-machine",
    )

    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Stable extracted text.",
        raw_bytes=b"stable raw bytes",
        raw_filename="alpha.txt",
        identifiers={"doi": "10.1000/alpha"},
        csl_json={
            "id": "alpha",
            "type": "article-journal",
            "title": "Alpha Source",
            "DOI": "10.1000/alpha",
            "issued": {"date-parts": [[2026]]},
        },
        provider_coverage="full",
        machine="test-machine",
    )

    source = state.catalog_source(vault, "source-alpha")
    assert source is not None
    assert source["provider_coverage"] == "full"
    assert source["identifiers"] == {"pmid": "12345", "doi": "10.1000/alpha"}
    assert source["csl_json"]["author"] == [{"family": "Lin", "given": "Morgan"}]
    assert source["csl_json"]["DOI"] == "10.1000/alpha"
    assert source["csl_json"]["issued"] == {"date-parts": [[2026]]}
    assert not (vault / "catalog/sources/source-alpha/source.md").exists()


def test_capture_bibtex_source_accepts_explicit_stable_work_id(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    bibtex = """@article{temporary2026,
      title = {Stable Source Identity},
      author = {Ada, River},
      year = {2026},
      journal = {Journal of Testable Systems},
      doi = {10.1000/stable.2026}
    }"""

    result = capture_bibtex_source(
        vault,
        bibtex,
        work_id="source-stable-identity",
        machine="test-machine",
    )
    source = state.catalog_source(vault, result["work_id"])

    assert result["source_path"] == "catalog/sources/source-stable-identity"
    assert source is not None
    assert source["work_id"] == "source-stable-identity"
    assert source["citekey"] == "temporary2026"


def test_capture_url_source_snapshots_html_text(tmp_path: Path, monkeypatch) -> None:
    vault = workspace(tmp_path)
    calls = []

    def fake_read(url: str, timeout: float) -> bytes:
        calls.append((url, timeout))
        return b"""
        <html><head><title>Harness URL</title><style>.x{}</style></head>
        <body><h1>Harness URL</h1><p>Captured page text.</p><script>ignore()</script></body>
        </html>
        """

    monkeypatch.setattr("memoria_vault.runtime.capture._read_url_bytes", fake_read)

    result = capture_url_source(
        vault,
        "https://example.test/path/page",
        timeout=1.0,
        machine="test-machine",
    )

    assert calls == [("https://example.test/path/page", 1.0)]
    assert result["source_path"] == "catalog/sources/url-example.test-path-page"
    source = state.catalog_source(vault, result["work_id"])
    assert source is not None
    assert source["title"] == "Harness URL"
    assert source["resource"] == "https://example.test/path/page"
    assert source["csl_json"]["type"] == "webpage"
    assert "Captured page text." in (vault / result["content_path"]).read_text(encoding="utf-8")
    assert b"<script>ignore()</script>" in (vault / result["raw_path"]).read_bytes()
    assert not (vault / "catalog/sources/url-example.test-path-page/source.md").exists()


def test_capture_url_source_fetches_from_loopback_http_server(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = (
                b"<html><head><title>Loopback URL</title></head>"
                b"<body><h1>Loopback URL</h1><p>Live local fetch text.</p></body></html>"
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format, *_args):
            return

    try:
        server = HTTPServer(("127.0.0.1", 0), Handler)
    except PermissionError as exc:
        pytest.skip(f"loopback socket unavailable in this sandbox: {exc}")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/source"
        result = capture_url_source(vault, url, timeout=2.0, machine="test-machine")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    source = state.catalog_source(vault, result["work_id"])
    assert source is not None
    assert source["check_status"] == "checked"
    assert source["title"] == "Loopback URL"
    assert source["resource"].startswith("http://127.0.0.1:")
    assert source["resource"].endswith("/source")
    assert "Live local fetch text." in (vault / result["content_path"]).read_text(encoding="utf-8")
    assert b"Live local fetch text." in (vault / result["raw_path"]).read_bytes()
    events = list(iter_jsonl(vault / "journal/test-machine.jsonl"))
    assert events[0]["workflow"] == "capture_url_source"
    assert events[-1]["status"] == "done"


def test_references_bib_projection_from_checked_sources(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    capture_bibtex_source(
        vault,
        """@article{harness2026,
          title = {Harnessed Workflows for Durable Research},
          author = {Ada, River and Lin, Morgan},
          year = {2026},
          journal = {Journal of Testable Systems},
          doi = {10.1000/harness.2026},
          abstract = {A fixture paper.}
        }""",
        machine="test-machine",
    )

    rendered = render_references_bib(vault)

    assert "@article{harness2026," in rendered
    assert "title = {Harnessed Workflows for Durable Research}" in rendered
    assert "author = {Ada, River and Lin, Morgan}" in rendered
    assert "year = {2026}" in rendered
    assert "doi = {10.1000/harness.2026}" in rendered

    result = write_references_bib(vault, commit=True, machine="test-machine")

    assert result["changed"] is True
    assert check_references_bib(vault)
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL, "bibliography.bib"}

    (vault / "bibliography.bib").write_text("stale\n", encoding="utf-8")
    assert not check_references_bib(vault)


def test_work_id_survives_pi_citekey_correction(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    capture_bibtex_source(
        vault,
        """@article{draftkey2026,
          title = {Stable Source Identity},
          author = {Ada, River},
          year = {2026},
          journal = {Journal of Testable Systems},
          doi = {10.1000/stable.2026}
        }""",
        work_id="source-stable-identity",
        machine="test-machine",
    )
    capture_bibtex_source(
        vault,
        """@article{corrected2026,
          title = {Stable Source Identity},
          author = {Ada, River},
          year = {2026},
          journal = {Journal of Testable Systems},
          doi = {10.1000/stable.2026}
        }""",
        work_id="source-stable-identity",
        machine="test-machine",
    )

    source = state.catalog_source(vault, "source-stable-identity")
    rendered = render_references_bib(vault)

    assert source is not None
    assert source["work_id"] == "source-stable-identity"
    assert source["citekey"] == "corrected2026"
    assert "@article{corrected2026," in rendered
    assert "@article{draftkey2026," not in rendered
