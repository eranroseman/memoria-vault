"""Contract tests for the policy-bound seed-corpus PDF resolver.

Every response is injected.  These tests must stay offline: the resolver is a
byte-to-byte seam, not permission to reach the network during verification.
"""

from __future__ import annotations

import io
import json
import re
import tarfile
from contextlib import redirect_stderr, redirect_stdout
from http.client import IncompleteRead
from pathlib import Path
from urllib.error import HTTPError

import pytest

from memoria_vault.runtime import seed_install, state
from memoria_vault.runtime.content_security import neutralize_untrusted_markdown
from tests.helpers import (
    call_with_context,
    copy_memoria_dirs,
    git,
    init_cli_workspace,
    init_git,
)

pytestmark = pytest.mark.contract

PDF_BYTES = b"%PDF-1.4 seed fixture bytes\n"
PDF_URL = "https://www.frontiersin.org/articles/10.3389/feduc.2019.00005/pdf"
PMC_RECORD_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC6099118"
PMC_PDF_URL = "https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/aa/bb/PMC6099118.pdf"
PMC_TGZ_URL = "https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_package/aa/bb/PMC6099118.tar.gz"


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self, limit: int | None = None) -> bytes:
        return self._payload if limit is None else self._payload[:limit]

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *_exc: object) -> bool:
        return False


def _opener(responses: dict[str, bytes]):
    calls: list[str] = []

    def opener(url: str) -> _FakeResponse:
        calls.append(url)
        if url not in responses:
            raise AssertionError(f"unexpected fetch: {url}")
        return _FakeResponse(responses[url])

    opener.calls = calls
    return opener


def _poisoned_opener(url: str) -> _FakeResponse:
    raise AssertionError(f"this call must not fetch: {url}")


def _allow_url(_url: str) -> None:
    return None


def _pdf_row(url: str = PDF_URL, method: str = "pdf-url") -> dict:
    return {
        "id": "moreira-2019-retrieval-practice",
        "title": "Retrieval Practice",
        "fetch": {"method": method, "url": url},
    }


def _pmc_row() -> dict:
    return {
        "id": "chen-2018-undesirable-difficulty",
        "title": "Undesirable Difficulty",
        "fetch": {"method": "pmc-oa", "url": PMC_RECORD_URL},
    }


def _pmc_xml(*links: tuple[str, str]) -> bytes:
    link_xml = "".join(
        f'<link format="{link_format}" href="{href}"/>' for link_format, href in links
    )
    return f"<OA><record>{link_xml}</record></OA>".encode()


def _tarball(members: list[tuple[str, bytes]]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, payload in members:
            info = tarfile.TarInfo(name=name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
    return buffer.getvalue()


def _tarball_with_pdf_symlink() -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        info = tarfile.TarInfo(name="linked.pdf")
        info.type = tarfile.SYMTYPE
        info.linkname = "article.pdf"
        archive.addfile(info)
    return buffer.getvalue()


def _tarball_with_pax_metadata(metadata_bytes: int) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz", format=tarfile.PAX_FORMAT) as archive:
        info = tarfile.TarInfo(name="article.pdf")
        info.size = len(PDF_BYTES)
        info.pax_headers = {"comment": "x" * metadata_bytes}
        archive.addfile(info, io.BytesIO(PDF_BYTES))
    return buffer.getvalue()


def test_resolve_fetch_downloads_a_direct_pdf_after_authorization() -> None:
    opener = _opener({PDF_URL: PDF_BYTES})
    authorized: list[str] = []

    result = seed_install.resolve_fetch(_pdf_row(), opener=opener, authorize_url=authorized.append)

    assert result == PDF_BYTES
    assert authorized == [PDF_URL]
    assert opener.calls == [PDF_URL]


def test_resolve_fetch_requires_an_explicit_authorizer() -> None:
    with pytest.raises(TypeError):
        seed_install.resolve_fetch(_pdf_row(), opener=_poisoned_opener)  # type: ignore[call-arg]


def test_resolve_fetch_authorizes_before_opening_a_direct_pdf() -> None:
    events: list[str] = []

    def authorize(url: str) -> None:
        assert url == PDF_URL
        events.append("authorize")

    def opener(url: str) -> _FakeResponse:
        assert url == PDF_URL
        assert events == ["authorize"]
        events.append("open")
        return _FakeResponse(PDF_BYTES)

    assert (
        seed_install.resolve_fetch(_pdf_row(), opener=opener, authorize_url=authorize) == PDF_BYTES
    )
    assert events == ["authorize", "open"]


def test_resolve_fetch_canonicalizes_a_default_port_and_host_before_authorizing() -> None:
    source_url = "https://WWW.FRONTIERSIN.ORG:443/articles/10.3389/feduc.2019.00005/pdf"
    canonical_url = PDF_URL
    opener = _opener({canonical_url: PDF_BYTES})
    authorized: list[str] = []

    assert (
        seed_install.resolve_fetch(
            _pdf_row(source_url), opener=opener, authorize_url=authorized.append
        )
        == PDF_BYTES
    )
    assert authorized == [canonical_url]
    assert opener.calls == [canonical_url]


def test_resolve_fetch_downloads_a_pinned_arxiv_pdf() -> None:
    url = "https://export.arxiv.org/pdf/2411.14199v1"
    opener = _opener({url: PDF_BYTES})

    assert (
        seed_install.resolve_fetch(
            _pdf_row(url, "arxiv-pdf"), opener=opener, authorize_url=_allow_url
        )
        == PDF_BYTES
    )


def test_resolve_fetch_rewrites_pmc_ftp_href_after_authorizing_both_urls() -> None:
    ftp_url = PMC_PDF_URL.replace("https://", "ftp://")
    opener = _opener({PMC_RECORD_URL: _pmc_xml(("pdf", ftp_url)), PMC_PDF_URL: PDF_BYTES})
    authorized: list[str] = []

    result = seed_install.resolve_fetch(_pmc_row(), opener=opener, authorize_url=authorized.append)

    assert result == PDF_BYTES
    assert authorized == [PMC_RECORD_URL, PMC_PDF_URL]
    assert opener.calls == [PMC_RECORD_URL, PMC_PDF_URL]


def test_resolve_fetch_prefers_a_pmc_pdf_link_to_a_package() -> None:
    package = _tarball([("article.pdf", b"%PDF-1.4 package\n")])
    opener = _opener(
        {
            PMC_RECORD_URL: _pmc_xml(("tgz", PMC_TGZ_URL), ("pdf", PMC_PDF_URL)),
            PMC_PDF_URL: PDF_BYTES,
            PMC_TGZ_URL: package,
        }
    )

    assert (
        seed_install.resolve_fetch(_pmc_row(), opener=opener, authorize_url=_allow_url) == PDF_BYTES
    )
    assert opener.calls == [PMC_RECORD_URL, PMC_PDF_URL]


def test_resolve_fetch_extracts_one_pdf_from_a_pmc_package() -> None:
    package = _tarball([("article.nxml", b"<article/>"), ("article.pdf", PDF_BYTES)])
    opener = _opener({PMC_RECORD_URL: _pmc_xml(("tgz", PMC_TGZ_URL)), PMC_TGZ_URL: package})

    assert (
        seed_install.resolve_fetch(_pmc_row(), opener=opener, authorize_url=_allow_url) == PDF_BYTES
    )


def test_resolve_fetch_rejects_a_pmc_package_without_a_pdf() -> None:
    opener = _opener(
        {
            PMC_RECORD_URL: _pmc_xml(("tgz", PMC_TGZ_URL)),
            PMC_TGZ_URL: _tarball([("article.nxml", b"<article/>")]),
        }
    )

    with pytest.raises(ValueError, match=re.escape(PMC_TGZ_URL)):
        seed_install.resolve_fetch(_pmc_row(), opener=opener, authorize_url=_allow_url)


def test_resolve_fetch_surfaces_pmc_service_errors() -> None:
    opener = _opener({PMC_RECORD_URL: b'<OA><error code="idIsNotOpenAccess">closed</error></OA>'})

    with pytest.raises(ValueError, match="idIsNotOpenAccess") as exc_info:
        seed_install.resolve_fetch(_pmc_row(), opener=opener, authorize_url=_allow_url)

    assert PMC_RECORD_URL in str(exc_info.value)


def test_resolve_fetch_rejects_non_pdf_bytes() -> None:
    opener = _opener({PDF_URL: b"<html>login wall</html>"})

    with pytest.raises(ValueError, match=re.escape(PDF_URL)):
        seed_install.resolve_fetch(_pdf_row(), opener=opener, authorize_url=_allow_url)


@pytest.mark.parametrize(
    "url",
    [
        "http://insecure.test/paper.pdf",
        "https:///missing-host.pdf",
        "https://user:secret@example.test/paper.pdf",
        "https://example.test:444/paper.pdf",
        "https://example.test/paper.pdf#fragment",
    ],
)
def test_resolve_fetch_rejects_invalid_urls_before_authorizer_or_opener(url: str) -> None:
    authorized: list[str] = []

    with pytest.raises(ValueError, match=re.escape(url)):
        seed_install.resolve_fetch(
            _pdf_row(url), opener=_poisoned_opener, authorize_url=authorized.append
        )

    assert authorized == []


def test_resolve_fetch_rejects_an_unsupported_method_before_authorizer_or_opener() -> None:
    authorized: list[str] = []

    with pytest.raises(ValueError, match=re.escape(PDF_URL)):
        seed_install.resolve_fetch(
            _pdf_row(PDF_URL, "html"), opener=_poisoned_opener, authorize_url=authorized.append
        )

    assert authorized == []


def test_resolve_fetch_uses_the_default_opener_at_call_time(monkeypatch) -> None:
    opener = _opener({PDF_URL: PDF_BYTES})
    monkeypatch.setattr(seed_install, "_default_opener", opener)

    assert seed_install.resolve_fetch(_pdf_row(), authorize_url=_allow_url) == PDF_BYTES
    assert opener.calls == [PDF_URL]


def test_authorizer_denial_prevents_the_direct_request() -> None:
    calls: list[str] = []

    def deny(url: str) -> None:
        calls.append(url)
        raise PermissionError("outside policy")

    with pytest.raises(ValueError, match=re.escape(PDF_URL)):
        seed_install.resolve_fetch(_pdf_row(), opener=_poisoned_opener, authorize_url=deny)

    assert calls == [PDF_URL]


def test_authorizer_denial_prevents_the_second_pmc_request() -> None:
    opener = _opener({PMC_RECORD_URL: _pmc_xml(("pdf", PMC_PDF_URL))})
    calls: list[str] = []

    def authorize(url: str) -> None:
        calls.append(url)
        if url == PMC_PDF_URL:
            raise PermissionError("outside policy")

    with pytest.raises(ValueError, match=re.escape(PMC_PDF_URL)):
        seed_install.resolve_fetch(_pmc_row(), opener=opener, authorize_url=authorize)

    assert calls == [PMC_RECORD_URL, PMC_PDF_URL]
    assert opener.calls == [PMC_RECORD_URL]


def test_resolve_fetch_validates_a_rewritten_pmc_href_before_authorizing_it() -> None:
    unsafe_ftp_href = "ftp://user:secret@ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/paper.pdf"
    rewritten_url = unsafe_ftp_href.replace("ftp://", "https://")
    opener = _opener({PMC_RECORD_URL: _pmc_xml(("pdf", unsafe_ftp_href))})
    authorized: list[str] = []

    with pytest.raises(ValueError, match=re.escape(rewritten_url)):
        seed_install.resolve_fetch(_pmc_row(), opener=opener, authorize_url=authorized.append)

    assert authorized == [PMC_RECORD_URL]
    assert opener.calls == [PMC_RECORD_URL]


@pytest.mark.parametrize(
    "suffix",
    [
        "/safe/../escape.pdf",
        "/safe/%2e%2e/escape.pdf",
        "/safe/%252e%252e/escape.pdf",
        "/safe%2fescape.pdf",
        "/safe%5cescape.pdf",
    ],
)
def test_resolve_fetch_rejects_unsafe_paths_before_authorizer_or_opener(suffix: str) -> None:
    authorized: list[str] = []
    url = f"https://allowed.test{suffix}"

    with pytest.raises(ValueError, match=re.escape(url)):
        seed_install.resolve_fetch(
            _pdf_row(url),
            opener=_poisoned_opener,
            authorize_url=authorized.append,
        )

    assert authorized == []


@pytest.mark.parametrize(
    "payload",
    [
        b'<!DOCTYPE OA [<!ENTITY boom "boom">]><OA>&boom;</OA>',
        b'<!doctype OA [<!entity boom "boom">]><OA>&boom;</OA>',
        '<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE OA [<!ENTITY boom "boom">]><OA>&boom;</OA>'.encode(
            "utf-16"
        ),
        b"\xffnot-utf8",
        b"<OA>",
    ],
)
def test_resolve_fetch_rejects_unsafe_or_malformed_pmc_xml(payload: bytes) -> None:
    opener = _opener({PMC_RECORD_URL: payload})

    with pytest.raises(ValueError, match=re.escape(PMC_RECORD_URL)):
        seed_install.resolve_fetch(_pmc_row(), opener=opener, authorize_url=_allow_url)


def test_resolve_fetch_rejects_a_non_utf8_pmc_xml_declaration() -> None:
    payload = (
        b'<?xml version="1.0" encoding="ISO-8859-1"?>'
        b'<OA><record><link format="pdf" href="' + PMC_PDF_URL.encode() + b'"/></record></OA>'
    )
    opener = _opener({PMC_RECORD_URL: payload, PMC_PDF_URL: PDF_BYTES})

    with pytest.raises(ValueError, match=re.escape(PMC_RECORD_URL)):
        seed_install.resolve_fetch(_pmc_row(), opener=opener, authorize_url=_allow_url)

    assert opener.calls == [PMC_RECORD_URL]


def test_resolve_fetch_rejects_a_pmc_xml_element_count_over_limit(monkeypatch) -> None:
    monkeypatch.setattr(seed_install, "MAX_PMC_XML_ELEMENTS", 3, raising=False)
    opener = _opener(
        {
            PMC_RECORD_URL: _pmc_xml(
                ("pdf", ""),
                ("pdf", ""),
                ("pdf", PMC_PDF_URL),
            ),
            PMC_PDF_URL: PDF_BYTES,
        }
    )

    with pytest.raises(ValueError, match="too many XML elements"):
        seed_install.resolve_fetch(_pmc_row(), opener=opener, authorize_url=_allow_url)

    assert opener.calls == [PMC_RECORD_URL]


def test_resolve_fetch_normalizes_redirect_and_transport_failures() -> None:
    def redirect(url: str) -> _FakeResponse:
        raise HTTPError(url, 302, "Found", hdrs=None, fp=None)

    with pytest.raises(ValueError, match=re.escape(PDF_URL)):
        seed_install.resolve_fetch(_pdf_row(), opener=redirect, authorize_url=_allow_url)

    def broken(_url: str) -> _FakeResponse:
        raise OSError("connection broke")

    with pytest.raises(ValueError, match=re.escape(PDF_URL)):
        seed_install.resolve_fetch(_pdf_row(), opener=broken, authorize_url=_allow_url)

    class ReadFailure(_FakeResponse):
        def read(self, limit: int | None = None) -> bytes:
            raise OSError("read broke")

    with pytest.raises(ValueError, match=re.escape(PDF_URL)):
        seed_install.resolve_fetch(
            _pdf_row(), opener=lambda _url: ReadFailure(PDF_BYTES), authorize_url=_allow_url
        )

    class IncompleteReadFailure(_FakeResponse):
        def read(self, limit: int | None = None) -> bytes:
            raise IncompleteRead(b"%PDF-partial", 32)

    with pytest.raises(ValueError, match=re.escape(PDF_URL)):
        seed_install.resolve_fetch(
            _pdf_row(),
            opener=lambda _url: IncompleteReadFailure(PDF_BYTES),
            authorize_url=_allow_url,
        )


def test_resolve_fetch_propagates_programmer_errors() -> None:
    def bug(_url: str) -> _FakeResponse:
        raise RuntimeError("fixture bug")

    with pytest.raises(RuntimeError, match="fixture bug"):
        seed_install.resolve_fetch(_pdf_row(), opener=bug, authorize_url=_allow_url)


def test_resolve_fetch_rejects_an_oversized_response(monkeypatch) -> None:
    monkeypatch.setattr(seed_install, "MAX_FETCH_BYTES", 4)
    opener = _opener({PDF_URL: b"%PDF-oversized"})

    with pytest.raises(ValueError, match=re.escape(PDF_URL)):
        seed_install.resolve_fetch(_pdf_row(), opener=opener, authorize_url=_allow_url)


def test_resolve_fetch_reads_exact_response_limits_and_accepts_the_boundary(monkeypatch) -> None:
    monkeypatch.setattr(seed_install, "MAX_FETCH_BYTES", len(PDF_BYTES))
    response = _FakeResponse(PDF_BYTES)
    limits: list[int | None] = []
    original_read = response.read

    def read(limit: int | None = None) -> bytes:
        limits.append(limit)
        return original_read(limit)

    monkeypatch.setattr(response, "read", read)

    assert (
        seed_install.resolve_fetch(
            _pdf_row(), opener=lambda _url: response, authorize_url=_allow_url
        )
        == PDF_BYTES
    )
    assert limits == [len(PDF_BYTES) + 1]


def test_resolve_fetch_rejects_a_malformed_pmc_package() -> None:
    opener = _opener(
        {PMC_RECORD_URL: _pmc_xml(("tgz", PMC_TGZ_URL)), PMC_TGZ_URL: b"not a tar file"}
    )

    with pytest.raises(ValueError, match=re.escape(PMC_TGZ_URL)):
        seed_install.resolve_fetch(_pmc_row(), opener=opener, authorize_url=_allow_url)


def test_resolve_fetch_rejects_an_oversized_pmc_member(monkeypatch) -> None:
    monkeypatch.setattr(seed_install, "MAX_PDF_MEMBER_BYTES", len(PDF_BYTES) - 1)
    package = _tarball([("article.pdf", PDF_BYTES)])
    opener = _opener({PMC_RECORD_URL: _pmc_xml(("tgz", PMC_TGZ_URL)), PMC_TGZ_URL: package})

    with pytest.raises(ValueError, match=re.escape(PMC_TGZ_URL)):
        seed_install.resolve_fetch(_pmc_row(), opener=opener, authorize_url=_allow_url)


def test_resolve_fetch_reads_exact_pmc_member_limits_and_accepts_the_boundary(monkeypatch) -> None:
    monkeypatch.setattr(seed_install, "MAX_PDF_MEMBER_BYTES", len(PDF_BYTES))
    monkeypatch.setattr(seed_install, "MAX_TAR_TOTAL_BYTES", len(PDF_BYTES))
    package = _tarball([("article.pdf", PDF_BYTES)])
    opener = _opener({PMC_RECORD_URL: _pmc_xml(("tgz", PMC_TGZ_URL)), PMC_TGZ_URL: package})
    original_read_limited = seed_install._read_limited
    calls: list[tuple[int, str]] = []

    def read_limited(stream, limit: int, url: str, label: str) -> bytes:
        calls.append((limit, label))
        return original_read_limited(stream, limit, url, label)

    monkeypatch.setattr(seed_install, "_read_limited", read_limited)

    assert (
        seed_install.resolve_fetch(_pmc_row(), opener=opener, authorize_url=_allow_url) == PDF_BYTES
    )
    assert (len(PDF_BYTES), "PDF member") in calls


def test_resolve_fetch_rejects_pmc_members_over_the_aggregate_cap(monkeypatch) -> None:
    monkeypatch.setattr(seed_install, "MAX_TAR_TOTAL_BYTES", len(PDF_BYTES))
    package = _tarball([("article.pdf", PDF_BYTES), ("appendix.txt", b"x")])
    opener = _opener({PMC_RECORD_URL: _pmc_xml(("tgz", PMC_TGZ_URL)), PMC_TGZ_URL: package})

    with pytest.raises(ValueError, match=re.escape(PMC_TGZ_URL)):
        seed_install.resolve_fetch(_pmc_row(), opener=opener, authorize_url=_allow_url)


def test_resolve_fetch_rejects_pax_metadata_over_the_archive_byte_cap(monkeypatch) -> None:
    monkeypatch.setattr(seed_install, "MAX_TAR_TOTAL_BYTES", len(PDF_BYTES))
    package = _tarball_with_pax_metadata(tarfile.BLOCKSIZE * (2 * seed_install.MAX_TAR_MEMBERS + 4))
    opener = _opener({PMC_RECORD_URL: _pmc_xml(("tgz", PMC_TGZ_URL)), PMC_TGZ_URL: package})

    with pytest.raises(ValueError, match=re.escape(PMC_TGZ_URL)):
        seed_install.resolve_fetch(_pmc_row(), opener=opener, authorize_url=_allow_url)


def test_resolve_fetch_rejects_a_pmc_package_with_too_many_members() -> None:
    members = [(f"{index}.txt", b"x") for index in range(128)]
    members.append(("article.pdf", PDF_BYTES))
    package = _tarball(members)
    opener = _opener({PMC_RECORD_URL: _pmc_xml(("tgz", PMC_TGZ_URL)), PMC_TGZ_URL: package})

    with pytest.raises(ValueError, match=re.escape(PMC_TGZ_URL)):
        seed_install.resolve_fetch(_pmc_row(), opener=opener, authorize_url=_allow_url)


def test_resolve_fetch_rejects_an_ambiguous_pmc_package() -> None:
    package = _tarball([("first.pdf", PDF_BYTES), ("second.pdf", PDF_BYTES)])
    opener = _opener({PMC_RECORD_URL: _pmc_xml(("tgz", PMC_TGZ_URL)), PMC_TGZ_URL: package})

    with pytest.raises(ValueError, match=re.escape(PMC_TGZ_URL)):
        seed_install.resolve_fetch(_pmc_row(), opener=opener, authorize_url=_allow_url)


def test_resolve_fetch_rejects_a_non_pdf_regular_pmc_member() -> None:
    package = _tarball([("article.pdf", b"not a PDF")])
    opener = _opener({PMC_RECORD_URL: _pmc_xml(("tgz", PMC_TGZ_URL)), PMC_TGZ_URL: package})

    with pytest.raises(ValueError, match=re.escape(PMC_TGZ_URL)):
        seed_install.resolve_fetch(_pmc_row(), opener=opener, authorize_url=_allow_url)


def test_resolve_fetch_ignores_a_nonregular_pdf_member() -> None:
    opener = _opener(
        {
            PMC_RECORD_URL: _pmc_xml(("tgz", PMC_TGZ_URL)),
            PMC_TGZ_URL: _tarball_with_pdf_symlink(),
        }
    )

    with pytest.raises(ValueError, match=re.escape(PMC_TGZ_URL)):
        seed_install.resolve_fetch(_pmc_row(), opener=opener, authorize_url=_allow_url)


# --- M.3: seed_install engine, worker operation, CLI ------------------------


def _workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas")
    init_git(tmp_path, "seed@example.invalid", "Seed")
    return tmp_path


def _patch_pdf_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "memoria_vault.runtime.capture._extract_pdf_pages",
        lambda _raw: [{"page": 1, "text": "The seed fixture reports one anchored finding."}],
    )


def _seed_row() -> dict:
    """A manifest-shaped pdf-url row (id/title/identifier/license_evidence/fetch)."""
    return {
        "id": "moreira-2019-retrieval-practice",
        "title": "Retrieval Practice in Classroom Settings",
        "identifier": "doi:10.3389/feduc.2019.00005",
        "license": "CC BY",
        "license_evidence": "https://www.frontiersin.org/articles/10.3389/feduc.2019.00005/full",
        "fetch": {"method": "pdf-url", "url": PDF_URL},
    }


def _seed_pmc_row() -> dict:
    return {
        "id": "chen-2018-undesirable-difficulty",
        "title": "Undesirable Difficulty Effects",
        "identifier": "doi:10.3389/fpsyg.2018.01483",
        "license": "CC BY 4.0",
        "license_evidence": "https://www.frontiersin.org/articles/10.3389/fpsyg.2018.01483/full",
        "fetch": {"method": "pmc-oa", "url": PMC_RECORD_URL},
    }


def _seed_arxiv_row() -> dict:
    return {
        "id": "asai-2024-openscholar",
        "title": "OpenScholar",
        "identifier": "arxiv:2411.14199v1",
        "license": "CC BY 4.0",
        "license_evidence": "https://arxiv.org/abs/2411.14199v1",
        "fetch": {"method": "arxiv-pdf", "url": "https://export.arxiv.org/pdf/2411.14199v1"},
    }


def _run_seed_install(vault: Path, **kwargs):
    kwargs.setdefault("authorize_url", _allow_url)
    return call_with_context(seed_install.seed_install, vault, **kwargs)


def _telemetry_steps(vault: Path) -> list[str]:
    with state.connect(vault) as conn:
        return [
            json.loads(row["payload_json"])["step"]
            for row in conn.execute(
                "SELECT payload_json FROM telemetry_events WHERE event_type = 'onboarding-step'"
                " ORDER BY ts"
            )
        ]


def _refuse_telemetry_inserts(vault: Path) -> None:
    # Produced, not mocked, and surgical: only inserts into telemetry_events fail.
    # (connect() skips the DDL on current DBs, so a dropped table would stay
    # dropped; the trigger blocks writes without mutating the schema.)
    with state.connect(vault) as conn:
        conn.execute(
            "CREATE TRIGGER telemetry_sink_offline BEFORE INSERT ON telemetry_events"
            " BEGIN SELECT RAISE(ABORT, 'telemetry sink offline'); END"
        )


def test_seed_install_admits_rows_through_the_pdf_capture_seam(tmp_path, monkeypatch) -> None:
    vault = _workspace(tmp_path)
    _patch_pdf_pages(monkeypatch)
    pdf_row, pmc_row = _seed_row(), _seed_pmc_row()
    opener = _opener(
        {
            PDF_URL: PDF_BYTES,
            PMC_RECORD_URL: _pmc_xml(("pdf", "ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/x.pdf")),
            "https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/x.pdf": PDF_BYTES,
        }
    )

    result = _run_seed_install(vault, rows=[pdf_row, pmc_row], opener=opener)

    assert result["admitted"] == [pdf_row["id"], pmc_row["id"]]
    assert result["skipped"] == []
    assert result["failed"] == []
    source = state.catalog_source(vault, pdf_row["id"])
    assert source is not None
    assert source["check_status"] == "unchecked"
    assert source["identifiers"]["doi"] == "10.3389/feduc.2019.00005"
    assert source["resource"] == "https://doi.org/10.3389/feduc.2019.00005"
    assert source["csl_json"]["DOI"] == "10.3389/feduc.2019.00005"
    assert source["csl_json"]["title"] == pdf_row["title"]
    assert state.catalog_source(vault, pmc_row["id"]) is not None


def test_seed_install_carries_arxiv_identifiers_into_the_catalog(tmp_path, monkeypatch) -> None:
    # The arXiv branch of the identifier/resource mapping: without this row only the
    # DOI branch is covered, and an arXiv-blind mapper passes every other test here.
    vault = _workspace(tmp_path)
    _patch_pdf_pages(monkeypatch)
    row = _seed_arxiv_row()

    result = _run_seed_install(vault, rows=[row], opener=_opener({row["fetch"]["url"]: PDF_BYTES}))

    assert result["admitted"] == [row["id"]]
    source = state.catalog_source(vault, row["id"])
    assert source is not None
    assert source["identifiers"] == {"arxiv": "2411.14199v1"}
    assert source["resource"] == "https://arxiv.org/abs/2411.14199v1"
    assert source["csl_json"]["URL"] == "https://arxiv.org/abs/2411.14199v1"
    assert "DOI" not in source["csl_json"]


def test_seed_install_falls_back_to_license_evidence_without_an_identifier(
    tmp_path, monkeypatch
) -> None:
    vault = _workspace(tmp_path)
    _patch_pdf_pages(monkeypatch)
    row = _seed_row()
    row.pop("identifier")

    result = _run_seed_install(vault, rows=[row], opener=_opener({PDF_URL: PDF_BYTES}))

    assert result["admitted"] == [row["id"]]
    source = state.catalog_source(vault, row["id"])
    assert source is not None
    assert source["identifiers"] == {}
    assert source["resource"] == row["license_evidence"]


def test_seed_install_rerun_skips_without_fetch_journal_or_commit(tmp_path, monkeypatch) -> None:
    vault = _workspace(tmp_path)
    _patch_pdf_pages(monkeypatch)
    row = _seed_row()
    first = _run_seed_install(vault, rows=[row], opener=_opener({PDF_URL: PDF_BYTES}))
    assert first["admitted"] == [row["id"]]
    journal = vault / ".memoria/journal/test-machine.jsonl"
    events_before = journal.read_text(encoding="utf-8").count("\n")
    head_before = git(vault, "rev-parse", "HEAD")

    rerun = _run_seed_install(vault, rows=[row], opener=_poisoned_opener)

    assert rerun["admitted"] == []
    assert rerun["failed"] == []
    assert rerun["skipped"] == [row["id"]]
    assert journal.read_text(encoding="utf-8").count("\n") == events_before
    assert git(vault, "rev-parse", "HEAD") == head_before


def test_seed_install_continues_past_a_failed_row(tmp_path, monkeypatch) -> None:
    vault = _workspace(tmp_path)
    _patch_pdf_pages(monkeypatch)
    bad, good = _seed_pmc_row(), _seed_row()
    xml = b'<OA><error code="idIsNotOpenAccess">nope</error></OA>'
    opener = _opener({PMC_RECORD_URL: xml, PDF_URL: PDF_BYTES})

    result = _run_seed_install(vault, rows=[bad, good], opener=opener)

    assert result["admitted"] == [good["id"]]
    assert [entry["id"] for entry in result["failed"]] == [bad["id"]]
    assert "idIsNotOpenAccess" in result["failed"][0]["error"]
    assert result["skipped"] == []
    # The failed row left no catalog residue; the good row after it still landed.
    assert state.catalog_source(vault, bad["id"]) is None
    assert state.catalog_source(vault, good["id"]) is not None


def test_seed_install_all_failed_raises_bounded_diagnostics(tmp_path, monkeypatch) -> None:
    vault = _workspace(tmp_path)
    first, second = _seed_row(), _seed_row()
    second["id"] = "second-failure"
    hostile = "<img src=x onerror=alert(1)> " + "é" * 2_000

    def fail(row, **_kwargs):
        raise ValueError(f"{row['id']}: {hostile}")

    monkeypatch.setattr(seed_install, "resolve_fetch", fail)
    with pytest.raises(seed_install.SeedInstallAllFailed) as exc_info:
        _run_seed_install(vault, rows=[first, second])

    diagnostics = exc_info.value.diagnostics
    assert diagnostics["admitted"] == []
    assert diagnostics["skipped"] == []
    assert [entry["id"] for entry in diagnostics["failed"]] == [first["id"], second["id"]]
    assert all(len(entry["error"].encode("utf-8")) <= 1_024 for entry in diagnostics["failed"])
    assert _telemetry_steps(vault) == []


def test_seed_install_survives_a_failed_row_when_another_row_is_present(
    tmp_path, monkeypatch
) -> None:
    # Emptiness is the failure exit, not failure itself: one skipped row is enough
    # to keep a run successful even when every other row failed.
    vault = _workspace(tmp_path)
    _patch_pdf_pages(monkeypatch)
    present, broken = _seed_row(), _seed_pmc_row()
    _run_seed_install(vault, rows=[present], opener=_opener({PDF_URL: PDF_BYTES}))

    result = _run_seed_install(
        vault,
        rows=[present, broken],
        opener=_opener({PMC_RECORD_URL: b'<OA><error code="idIsNotOpenAccess"/></OA>'}),
    )

    assert result["skipped"] == [present["id"]]
    assert [entry["id"] for entry in result["failed"]] == [broken["id"]]


def test_frame_first_notice_tracks_active_projects(tmp_path, monkeypatch) -> None:
    vault = _workspace(tmp_path)
    _patch_pdf_pages(monkeypatch)
    row = _seed_row()

    result = _run_seed_install(vault, rows=[row], opener=_opener({PDF_URL: PDF_BYTES}))
    assert any("frame your" in notice for notice in result["notices"])

    archived = vault / "projects/old/project.md"
    archived.parent.mkdir(parents=True)
    archived.write_text(
        "---\ntype: project\ntitle: Old project\nlifecycle: archived\n"
        "tags: []\nlinks: {}\n---\n# Old project\n",
        encoding="utf-8",
    )
    rerun = _run_seed_install(vault, rows=[row], opener=_poisoned_opener)
    assert any("frame your" in notice for notice in rerun["notices"])

    active = vault / "projects/tutorial/project.md"
    active.parent.mkdir(parents=True)
    active.write_text(
        "---\ntype: project\ntitle: Tutorial project\ntags: []\nlinks: {}\n"
        "---\n# Tutorial project\n",
        encoding="utf-8",
    )
    final = _run_seed_install(vault, rows=[row], opener=_poisoned_opener)
    assert final["notices"] == []


def test_frame_first_notice_ignores_non_project_markdown(tmp_path, monkeypatch) -> None:
    # A note that merely lives under projects/ is not a framed project, and a
    # retracted project is not an active one.
    vault = _workspace(tmp_path)
    _patch_pdf_pages(monkeypatch)
    row = _seed_row()
    for rel, frontmatter in (
        ("projects/notes/stray.md", "type: note\ntitle: Stray note\n"),
        ("projects/dropped/project.md", "type: project\ntitle: Dropped\nlifecycle: retracted\n"),
    ):
        path = vault / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\n{frontmatter}tags: []\nlinks: {{}}\n---\n# x\n", encoding="utf-8")

    result = _run_seed_install(vault, rows=[row], opener=_opener({PDF_URL: PDF_BYTES}))

    assert any("frame your" in notice for notice in result["notices"])


def test_seed_installed_step_emits_on_first_install(tmp_path, monkeypatch) -> None:
    vault = _workspace(tmp_path)
    _patch_pdf_pages(monkeypatch)
    row = _seed_row()

    result = _run_seed_install(vault, rows=[row], opener=_opener({PDF_URL: PDF_BYTES}))

    # The real helper, the real sink: a first successful install records the step.
    assert result["telemetry"]["status"] == "emitted"
    assert result["telemetry"]["event_id"]
    assert _telemetry_steps(vault) == ["seed-installed"]
    with state.connect(vault) as conn:
        row_out = conn.execute(
            "SELECT event_type, session_id, surface FROM telemetry_events WHERE event_id = ?",
            (result["telemetry"]["event_id"],),
        ).fetchone()
    assert row_out["event_type"] == "onboarding-step"
    # Server-side emit: the client envelope columns stay NULL (their producer is a
    # client-submitted empirical event, fixtured in tests/test_telemetry_events.py).
    assert row_out["session_id"] is None
    assert row_out["surface"] is None


def test_seed_install_completes_when_the_telemetry_sink_refuses(tmp_path, monkeypatch) -> None:
    vault = _workspace(tmp_path)
    _patch_pdf_pages(monkeypatch)
    _refuse_telemetry_inserts(vault)
    row = _seed_row()

    result = _run_seed_install(vault, rows=[row], opener=_opener({PDF_URL: PDF_BYTES}))

    # Never raises into its caller: the install completed and reported honestly.
    assert result["telemetry"] == {"status": "unavailable"}
    assert result["admitted"] == [row["id"]]
    assert state.catalog_source(vault, row["id"]) is not None
    assert _telemetry_steps(vault) == []


def test_memoria_seed_install_cli_end_to_end_offline(tmp_path, capsys, monkeypatch) -> None:
    from memoria_vault.cli import main
    from memoria_vault.product.seed_corpus import load_seed_manifest

    workspace = init_cli_workspace(tmp_path, capsys)
    _patch_pdf_pages(monkeypatch)
    responses: dict[str, bytes] = {}
    for row in load_seed_manifest():
        url = row["fetch"]["url"]
        if row["fetch"]["method"] == "pmc-oa":
            pmcid = url.rsplit("=", 1)[-1]
            href = f"ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/{pmcid}.pdf"
            responses[url] = _pmc_xml(("pdf", href))
            responses[f"https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/{pmcid}.pdf"] = PDF_BYTES
        else:
            responses[url] = PDF_BYTES
    monkeypatch.setattr("memoria_vault.runtime.seed_install._default_opener", _opener(responses))

    rc = main(["seed", "install", "--workspace", str(workspace), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["ok"] is True
    all_ids = sorted(row["id"] for row in load_seed_manifest())
    assert sorted(payload["result"]["admitted"]) == all_ids
    assert any("frame your" in notice for notice in payload["result"]["notices"])
    # T.2 wired `memoria init` to emit `init-done`, so the CLI arc records both steps
    # in order -- which is exactly the pair the spec §5 delta is measured from.
    assert _telemetry_steps(workspace) == ["init-done", "seed-installed"]

    # Acceptance-criteria idempotence: the re-run admits nothing new, exits
    # clean, and performs zero fetches (a fetch would raise loudly).
    monkeypatch.setattr("memoria_vault.runtime.seed_install._default_opener", _poisoned_opener)
    rc = main(["seed", "install", "--workspace", str(workspace), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["result"]["admitted"] == []
    assert sorted(payload["result"]["skipped"]) == all_ids


def test_seed_install_all_failed_cli_and_request_show_preserve_safe_diagnostics(
    tmp_path, capsys, monkeypatch
) -> None:
    from memoria_vault.cli import main

    workspace = init_cli_workspace(tmp_path, capsys)
    first, second = _seed_row(), _seed_row()
    second["id"] = "second-failure"
    hostile = "<img src=x onerror=alert(1)> " + "é" * 2_000

    monkeypatch.setattr(
        "memoria_vault.runtime.seed_install.load_seed_manifest",
        lambda: [first, second],
    )

    def fail(row, **_kwargs):
        raise ValueError(f"{row['id']}: {hostile}")

    monkeypatch.setattr("memoria_vault.runtime.seed_install.resolve_fetch", fail)

    rc = main(["seed", "install", "--workspace", str(workspace), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 1
    diagnostics = payload["result"]["diagnostics"]
    assert diagnostics["admitted"] == []
    assert diagnostics["skipped"] == []
    assert [entry["id"] for entry in diagnostics["failed"]] == [first["id"], second["id"]]

    rc = main(
        [
            "request",
            "show",
            payload["job"]["request_id"],
            "--workspace",
            str(workspace),
            "--json",
        ]
    )
    request_payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    request_failed = request_payload["request"]["job"]["diagnostics"]["failed"]
    assert [entry["id"] for entry in request_failed] == [first["id"], second["id"]]
    assert [entry["error"] for entry in request_failed] == [
        neutralize_untrusted_markdown(entry["error"]) for entry in diagnostics["failed"]
    ]

    stream = io.StringIO()
    with redirect_stdout(stream), redirect_stderr(stream):
        rc = main(["seed", "install", "--workspace", str(workspace)])
    text = stream.getvalue()
    assert rc == 1
    first_line = f"failed row {first['id']}:"
    second_line = f"failed row {second['id']}:"
    assert first_line in text
    assert second_line in text
    assert text.index(first_line) < text.index(second_line) < text.index("FAILED:")


def test_seed_install_worker_authorizes_every_url_against_the_operation_policy(
    tmp_path, capsys, monkeypatch
) -> None:
    # The worker supplies require_allowed_network as the authorizer; a row outside
    # the manifest's finite allowlist must be refused before any opener call.
    from memoria_vault.cli import main

    workspace = init_cli_workspace(tmp_path, capsys)
    _patch_pdf_pages(monkeypatch)
    allowed, off_policy = _seed_row(), _seed_row()
    off_policy["id"] = "off-policy-row"
    off_policy["fetch"] = {"method": "pdf-url", "url": "https://example.invalid/off-policy.pdf"}
    monkeypatch.setattr(
        "memoria_vault.runtime.seed_install.load_seed_manifest",
        lambda: [allowed, off_policy],
    )
    monkeypatch.setattr(
        "memoria_vault.runtime.seed_install._default_opener", _opener({PDF_URL: PDF_BYTES})
    )

    rc = main(["seed", "install", "--workspace", str(workspace), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert payload["result"]["admitted"] == [allowed["id"]]
    # Refused by the policy, before the opener (which has no entry for that URL
    # and would have raised its own "unexpected fetch" instead).
    assert [entry["id"] for entry in payload["result"]["failed"]] == ["off-policy-row"]
    assert "not authorized" in payload["result"]["failed"][0]["error"]
    assert "https://example.invalid/off-policy.pdf" in payload["result"]["failed"][0]["error"]


def test_seed_install_requires_pi_actor(tmp_path, capsys) -> None:
    from memoria_vault.cli import main

    workspace = init_cli_workspace(tmp_path, capsys)

    rc = main(["seed", "install", "--workspace", str(workspace), "--actor", "agent", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert payload["ok"] is False
    assert "requires PI actor authority" in str(payload["result"]["error"])


def test_seed_install_operation_never_fetches_on_an_unconfirmed_payload(
    tmp_path, capsys, monkeypatch
) -> None:
    # A generic `operation run` sweep over the catalog (tests/test_parity_fixture.py
    # runs one as actor=pi) must not start the seed corpus download: the poisoned
    # opener below turns any fetch into a loud failure, and the refusal must arrive
    # without one.
    from memoria_vault.cli import main

    workspace = init_cli_workspace(tmp_path, capsys)
    monkeypatch.setattr("memoria_vault.runtime.seed_install._default_opener", _poisoned_opener)

    rc = main(
        [
            "operation",
            "run",
            "--workspace",
            str(workspace),
            "seed-install",
            "--payload-json",
            "{}",
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert payload["ok"] is False
    assert "seed-install requires install: true" in str(payload["result"]["error"])
    assert state.catalog_source(workspace, "asai-2024-openscholar") is None
