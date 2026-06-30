from __future__ import annotations

import shutil
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from memoria_vault.runtime.capture import (
    capture_bibtex_source,
    capture_pdf_source,
    capture_source,
    capture_url_source,
    capture_zotero_local_source,
    capture_zotero_source,
    check_references_bib,
    render_references_bib,
    write_references_bib,
)
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.trusted_writer import mark_checked, observe_pi_edit
from memoria_vault.runtime.vaultio import read_frontmatter

ROOT = Path(__file__).resolve().parent.parent


def workspace(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "vault-template/.memoria/schemas", tmp_path / ".memoria/schemas")
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "capture@example.invalid")
    git(tmp_path, "config", "user.name", "Capture")
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


def test_capture_source_writes_catalog_files_and_trace(tmp_path: Path) -> None:
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

    source = vault / "catalog/sources/source-alpha/source.md"
    content = vault / "catalog/sources/source-alpha/content.md"
    raw = vault / "catalog/sources/source-alpha/raw/alpha.txt"
    fm = read_frontmatter(source)

    assert fm["check_status"] == "checked"
    assert fm["source_id"] == "source-alpha"
    assert fm["raw_copy_path"] == "catalog/sources/source-alpha/raw/alpha.txt"
    assert fm["content_path"] == "catalog/sources/source-alpha/content.md"
    assert fm["raw_text_sha256"] == sha256_file(raw)
    assert fm["normalized_text_sha256"] == sha256_file(content)
    assert content.read_text(encoding="utf-8") == "Extracted alpha text.\n"
    assert raw.read_bytes() == b"raw alpha bytes"

    events = list(iter_jsonl(vault / "journal/test-machine.jsonl"))
    assert [event["event"] for event in events] == ["run", "derived", "check-fired", "run"]
    assert events[0]["status"] == "started"
    assert events[-1]["status"] == "done"
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {
        "catalog/sources/source-alpha/content.md",
        "catalog/sources/source-alpha/source.md",
        "journal/test-machine.jsonl",
        "references.bib",
    }


def test_capture_source_rejects_unsupported_required_check_before_writes(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)

    with pytest.raises(ValueError, match="unsupported promotion checks: later-integrity"):
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
        vault / "catalog/sources/source-alpha/raw/source.txt"
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

    assert result["content_path"] == "catalog/sources/pdf-source/content.md"
    assert "## Page 3" in (vault / result["content_path"]).read_text(encoding="utf-8")
    fm = read_frontmatter(vault / result["source_path"])
    assert fm["raw_copy_path"] == "catalog/sources/pdf-source/raw/paper.pdf"
    events = list(iter_jsonl(vault / "journal/test-machine.jsonl"))
    assert events[0]["workflow"] == "capture_pdf_source"
    assert events[1]["operation"] == "capture_pdf_source"


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
      abstract = {A fixture paper for the Memoria test environment harness.}
    }"""

    result = capture_bibtex_source(vault, bibtex, machine="test-machine")

    source = vault / "catalog/sources/doi-10.1000_harness.2026/source.md"
    raw = vault / "catalog/sources/doi-10.1000_harness.2026/raw/harness2026.bib"
    fm = read_frontmatter(source)

    assert result["source_path"] == "catalog/sources/doi-10.1000_harness.2026/source.md"
    assert fm["check_status"] == "checked"
    assert fm["title"] == "Harnessed Workflows for Durable Research"
    assert fm["citekey"] == "harness2026"
    assert fm["resource"] == "https://doi.org/10.1000/harness.2026"
    assert fm["identifiers"] == {"doi": "10.1000/harness.2026"}
    assert fm["csl_json"]["author"] == [
        {"family": "Ada", "given": "River"},
        {"family": "Lin", "given": "Morgan"},
    ]
    assert result["entity_paths"] == [
        "catalog/entities/person-river-ada.md",
        "catalog/entities/person-morgan-lin.md",
        "catalog/entities/venue-journal-of-testable-systems.md",
    ]
    assert fm["links"]["authors"] == [
        "catalog/entities/person-river-ada.md",
        "catalog/entities/person-morgan-lin.md",
    ]
    assert fm["links"]["venues"] == ["catalog/entities/venue-journal-of-testable-systems.md"]
    assert (
        read_frontmatter(vault / "catalog/entities/person-morgan-lin.md")["canonical_name"]
        == "Morgan Lin"
    )
    assert (
        read_frontmatter(vault / "catalog/entities/venue-journal-of-testable-systems.md")["type"]
        == "venue"
    )
    assert raw.read_text(encoding="utf-8").startswith("@article{harness2026,")

    events = list(iter_jsonl(vault / "journal/test-machine.jsonl"))
    assert events[0]["workflow"] == "capture_bibtex_source"
    assert events[1]["operation"] == "capture_bibtex_source"
    assert events[-1]["workflow"] == "capture_bibtex_source"


def test_capture_bibtex_source_merges_existing_entity_source_links(tmp_path: Path) -> None:
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

    person = read_frontmatter(vault / "catalog/entities/person-morgan-lin.md")
    venue = read_frontmatter(vault / "catalog/entities/venue-journal-of-shared-metadata.md")
    assert person["links"]["sources"] == [
        "catalog/sources/doi-10.1000_shared.one/source.md",
        "catalog/sources/doi-10.1000_shared.two/source.md",
    ]
    assert venue["links"]["sources"] == person["links"]["sources"]


def test_capture_source_marks_conflicting_entity_external_ids_as_ambiguous(
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

    entity = read_frontmatter(vault / "catalog/entities/person-ada-river.md")

    assert entity["check_status"] == "checked"
    assert entity["external_ids"] == {"orcid": "0000-0001-0000-0001"}
    assert entity["metadata"]["identity_status"] == "ambiguous"
    assert entity["metadata"]["identity_conflicts"] == [
        {
            "field": "orcid",
            "existing": "0000-0001-0000-0001",
            "incoming": "0000-0002-0000-0002",
        }
    ]
    assert entity["links"]["sources"] == [
        "catalog/sources/source-one/source.md",
        "catalog/sources/source-two/source.md",
    ]


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
        metadata_status="partial",
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
        metadata_status="verified",
        machine="test-machine",
    )

    fm = read_frontmatter(vault / "catalog/sources/source-alpha/source.md")
    assert fm["metadata_status"] == "verified"
    assert fm["identifiers"] == {"pmid": "12345", "doi": "10.1000/alpha"}
    assert fm["csl_json"]["author"] == [{"family": "Lin", "given": "Morgan"}]
    assert fm["csl_json"]["DOI"] == "10.1000/alpha"
    assert fm["csl_json"]["issued"] == {"date-parts": [[2026]]}
    assert fm["links"]["authors"] == ["catalog/entities/person-morgan-lin.md"]


def test_capture_bibtex_source_accepts_explicit_stable_source_id(tmp_path: Path) -> None:
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
        source_id="source-stable-identity",
        machine="test-machine",
    )
    fm = read_frontmatter(vault / result["source_path"])

    assert result["source_path"] == "catalog/sources/source-stable-identity/source.md"
    assert fm["source_id"] == "source-stable-identity"
    assert fm["citekey"] == "temporary2026"


def test_capture_zotero_source_maps_local_api_item_snapshot(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    item = {
        "key": "ABCD1234",
        "links": {"alternate": {"href": "http://zotero.local/items/ABCD1234"}},
        "data": {
            "key": "ABCD1234",
            "itemType": "journalArticle",
            "title": "Zotero Harness Source",
            "creators": [
                {"creatorType": "author", "firstName": "Ada", "lastName": "River"},
                {"creatorType": "author", "name": "Test Lab"},
            ],
            "date": "2026-03-01",
            "publicationTitle": "Journal of Local APIs",
            "DOI": "10.1000/zotero.2026",
            "abstractNote": "A Zotero Local API fixture.",
            "annotationText": "Should not be imported.",
            "extra": "bibtex: river2026zotero\n",
        },
        "children": [{"data": {"itemType": "annotation", "annotationText": "Child note"}}],
        "annotations": [{"text": "annotation payload"}],
    }

    result = capture_zotero_source(vault, item, machine="test-machine")

    source = vault / "catalog/sources/zotero-abcd1234/source.md"
    raw = vault / "catalog/sources/zotero-abcd1234/raw/zotero-abcd1234.zotero.json"
    fm = read_frontmatter(source)

    assert result["source_path"] == "catalog/sources/zotero-abcd1234/source.md"
    assert fm["check_status"] == "checked"
    assert fm["title"] == "Zotero Harness Source"
    assert fm["citekey"] == "river2026zotero"
    assert fm["resource"] == "https://doi.org/10.1000/zotero.2026"
    assert fm["identifiers"] == {"doi": "10.1000/zotero.2026"}
    assert fm["csl_json"]["author"] == [
        {"family": "River", "given": "Ada"},
        {"literal": "Test Lab"},
    ]
    assert fm["csl_json"]["issued"] == {"date-parts": [[2026]]}
    assert result["entity_paths"] == [
        "catalog/entities/person-ada-river.md",
        "catalog/entities/person-test-lab.md",
        "catalog/entities/venue-journal-of-local-apis.md",
    ]
    assert (
        read_frontmatter(vault / "catalog/entities/person-ada-river.md")["canonical_name"]
        == "Ada River"
    )
    raw_text = raw.read_text(encoding="utf-8")
    assert raw_text.startswith("{\n")
    assert "annotationText" not in raw_text
    assert "annotations" not in raw_text
    assert "children" not in raw_text
    assert (vault / result["content_path"]).read_text(encoding="utf-8") == (
        "A Zotero Local API fixture.\n"
    )

    events = list(iter_jsonl(vault / "journal/test-machine.jsonl"))
    assert events[0]["workflow"] == "capture_zotero_source"
    assert events[1]["operation"] == "capture_zotero_source"


def test_capture_zotero_source_rejects_annotation_items(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    with pytest.raises(ValueError, match=r"annotation import is out of alpha\.11 scope"):
        capture_zotero_source(
            vault,
            {
                "key": "ANN01",
                "data": {
                    "key": "ANN01",
                    "itemType": "annotation",
                    "annotationText": "Highlighted text.",
                },
            },
            machine="test-machine",
        )

    assert not (vault / "catalog/sources/zotero-ann01").exists()


def test_capture_zotero_local_source_fetches_item_by_key(tmp_path: Path, monkeypatch) -> None:
    vault = workspace(tmp_path)
    item = {
        "key": "FETCH01",
        "data": {
            "key": "FETCH01",
            "itemType": "journalArticle",
            "title": "Fetched Zotero Source",
            "date": "2026",
            "abstractNote": "Fetched through the local API.",
        },
    }
    calls = []

    def fake_read(url: str, timeout: float):
        calls.append((url, timeout))
        return item

    monkeypatch.setattr("memoria_vault.runtime.capture._read_zotero_json", fake_read)

    result = capture_zotero_local_source(
        vault,
        "FETCH01",
        local_api_base="http://localhost:23119/api/users/0",
        timeout=1.5,
        machine="test-machine",
    )

    assert calls == [("http://localhost:23119/api/users/0/items/FETCH01", 1.5)]
    assert result["source_path"] == "catalog/sources/zotero-fetch01/source.md"
    assert read_frontmatter(vault / result["source_path"])["title"] == "Fetched Zotero Source"


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
    assert result["source_path"] == "catalog/sources/url-example.test-path-page/source.md"
    fm = read_frontmatter(vault / result["source_path"])
    assert fm["title"] == "Harness URL"
    assert fm["resource"] == "https://example.test/path/page"
    assert fm["item_type"] == "webpage"
    assert "Captured page text." in (vault / result["content_path"]).read_text(encoding="utf-8")
    assert b"<script>ignore()</script>" in (vault / result["raw_path"]).read_bytes()


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

    fm = read_frontmatter(vault / result["source_path"])
    assert fm["check_status"] == "checked"
    assert fm["title"] == "Loopback URL"
    assert fm["resource"].startswith("http://127.0.0.1:")
    assert fm["resource"].endswith("/source")
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

    assert result["changed"] is False
    assert check_references_bib(vault)
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {"journal/test-machine.jsonl"}

    (vault / "references.bib").write_text("stale\n", encoding="utf-8")
    assert not check_references_bib(vault)


def test_source_id_survives_pi_citekey_correction(tmp_path: Path) -> None:
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
        source_id="source-stable-identity",
        machine="test-machine",
    )
    source = vault / "catalog/sources/source-stable-identity/source.md"
    before = sha256_file(source)
    text = source.read_text(encoding="utf-8")

    source.write_text(
        text.replace("citekey: draftkey2026", "citekey: corrected2026"), encoding="utf-8"
    )
    event = observe_pi_edit(
        vault,
        "catalog/sources/source-stable-identity/source.md",
        before,
        machine="test-machine",
    )
    mark_checked(vault, "catalog/sources/source-stable-identity/source.md", machine="test-machine")

    fm = read_frontmatter(source)
    rendered = render_references_bib(vault)

    assert event["actor"] == "pi"
    assert fm["source_id"] == "source-stable-identity"
    assert fm["citekey"] == "corrected2026"
    assert "@article{corrected2026," in rendered
    assert "@article{draftkey2026," not in rendered
