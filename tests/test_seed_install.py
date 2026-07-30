"""Contract tests for the policy-bound seed-corpus PDF resolver.

Every response is injected.  These tests must stay offline: the resolver is a
byte-to-byte seam, not permission to reach the network during verification.
"""

from __future__ import annotations

import io
import re
import tarfile
from http.client import IncompleteRead
from urllib.error import HTTPError

import pytest

from memoria_vault.runtime import seed_install

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
