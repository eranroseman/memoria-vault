"""Policy-bound fetch helpers for the licensed seed corpus."""

from __future__ import annotations

import gzip
import io
import tarfile
from collections.abc import Callable
from http.client import HTTPException
from typing import Any
from urllib.parse import unquote, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, build_opener
from xml.parsers import expat

MAX_FETCH_BYTES = 32 * 1024 * 1024
MAX_TAR_MEMBERS = 128
MAX_TAR_TOTAL_BYTES = 32 * 1024 * 1024
MAX_PDF_MEMBER_BYTES = 32 * 1024 * 1024
MAX_PMC_XML_ELEMENTS = 1024


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_args: object, **_kwargs: object) -> None:
        """Turn redirects into an HTTP error instead of following a new URL."""


class _CappedTarStream:
    """Bound decompressed tar bytes before tarfile parses member metadata."""

    def __init__(self, stream: Any, limit: int, package_url: str) -> None:
        self._stream = stream
        self._limit = limit
        self._package_url = package_url
        self._read = 0

    def read(self, size: int = -1) -> bytes:
        remaining = self._limit - self._read
        request_size = remaining + 1 if size < 0 else min(size, remaining + 1)
        raw = self._stream.read(request_size)
        self._read += len(raw)
        if self._read > self._limit:
            raise ValueError(f"PMC OA package at {self._package_url} exceeds the byte limit")
        return raw


def _default_opener(url: str):
    """Open a URL with the resolver's fixed timeout and no redirect following."""
    return build_opener(_NoRedirect()).open(url, timeout=30.0)


def resolve_fetch(
    row: dict[str, Any],
    *,
    opener: Callable[[str], Any] | None = None,
    authorize_url: Callable[[str], None],
) -> bytes:
    """Fetch one declared PDF only after validating and authorizing every URL."""
    fetch = row.get("fetch") if isinstance(row.get("fetch"), dict) else {}
    method = str(fetch.get("method") or "")
    url = str(fetch.get("url") or "")
    active_opener = _default_opener if opener is None else opener
    if method in {"pdf-url", "arxiv-pdf"}:
        return _require_pdf(_fetch_bytes(url, active_opener, authorize_url), url)
    if method == "pmc-oa":
        return _resolve_pmc_oa(url, active_opener, authorize_url)
    raise ValueError(f"seed row {row.get('id')}: unsupported fetch method {method!r} for {url}")


def _fetch_bytes(
    url: str,
    opener: Callable[[str], Any],
    authorize_url: Callable[[str], None],
) -> bytes:
    canonical_url = _canonical_https_url(url)
    try:
        authorize_url(canonical_url)
    except PermissionError as exc:
        raise ValueError(f"seed fetch is not authorized: {canonical_url}") from exc
    try:
        with opener(canonical_url) as response:
            return _read_limited(response, MAX_FETCH_BYTES, canonical_url, "response")
    except (HTTPException, OSError) as exc:
        raise ValueError(f"seed fetch failed for {canonical_url}: {exc}") from exc


def _canonical_https_url(url: str) -> str:
    raw_url = str(url or "").strip()
    try:
        parsed = urlsplit(raw_url)
        port = parsed.port
    except ValueError as exc:
        raise ValueError(f"seed fetch requires a valid https URL: {raw_url}") from exc
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError(f"seed fetch requires an https URL: {raw_url}")
    if parsed.username is not None or parsed.password is not None or parsed.fragment:
        raise ValueError(f"seed fetch requires a credential-free URL: {raw_url}")
    if port not in {None, 443}:
        raise ValueError(f"seed fetch requires the default https port: {raw_url}")
    path = parsed.path or "/"
    _require_safe_path(path, raw_url)
    hostname = parsed.hostname.casefold()
    host = f"[{hostname}]" if ":" in hostname else hostname
    return urlunsplit(("https", host, path, parsed.query, ""))


def _require_safe_path(path: str, raw_url: str) -> None:
    lowered = path.casefold()
    if "%25" in lowered or "%2f" in lowered or "%5c" in lowered:
        raise ValueError(f"seed fetch has an unsafe URL path: {raw_url}")
    decoded = unquote(path)
    for candidate in (path, decoded):
        if "\\" in candidate or any(segment in {".", ".."} for segment in candidate.split("/")):
            raise ValueError(f"seed fetch has an unsafe URL path: {raw_url}")


def _read_limited(stream: Any, limit: int, url: str, label: str) -> bytes:
    raw = stream.read(limit + 1)
    if not isinstance(raw, bytes):
        raise ValueError(f"seed {label} from {url} is not bytes")
    if len(raw) > limit:
        raise ValueError(f"seed {label} from {url} exceeds the byte limit")
    return raw


def _require_pdf(raw: bytes, url: str) -> bytes:
    if not raw.startswith(b"%PDF-"):
        raise ValueError(f"fetched bytes from {url} are not a PDF")
    return raw


def _resolve_pmc_oa(
    record_url: str,
    opener: Callable[[str], Any],
    authorize_url: Callable[[str], None],
) -> bytes:
    canonical_record_url = _canonical_https_url(record_url)
    record = _fetch_bytes(canonical_record_url, opener, authorize_url)
    try:
        text = record.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"PMC OA XML at {canonical_record_url} is not UTF-8") from exc
    if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
        raise ValueError(f"PMC OA XML at {canonical_record_url} contains a DTD or entity")
    del text
    error_code: str | None = None
    pdf_href = ""
    tgz_href = ""
    element_count = 0

    def start_element(name: str, attrs: dict[str, str]) -> None:
        nonlocal element_count, error_code, pdf_href, tgz_href
        element_count += 1
        if element_count > MAX_PMC_XML_ELEMENTS:
            raise ValueError(f"PMC OA XML at {canonical_record_url} has too many XML elements")
        if name == "error" and error_code is None:
            error_code = attrs.get("code") or "unknown"
        elif name == "link":
            link_format = attrs.get("format") or ""
            href = attrs.get("href") or ""
            if link_format == "pdf" and href and not pdf_href:
                pdf_href = href
            elif link_format == "tgz" and href and not tgz_href:
                tgz_href = href

    def xml_declaration(_version: str, encoding: str | None, _standalone: int) -> None:
        if encoding is not None and encoding.casefold() != "utf-8":
            raise ValueError(f"PMC OA XML at {canonical_record_url} is not UTF-8")

    try:
        parser = expat.ParserCreate()
        parser.StartElementHandler = start_element
        parser.XmlDeclHandler = xml_declaration
        parser.Parse(record, True)
    except expat.ExpatError as exc:
        raise ValueError(f"PMC OA XML at {canonical_record_url} is malformed") from exc
    if error_code is not None:
        raise ValueError(f"PMC OA service error for {canonical_record_url}: {error_code}")
    if pdf_href:
        pdf_url = _canonical_https_url(_https_href(pdf_href))
        return _require_pdf(_fetch_bytes(pdf_url, opener, authorize_url), pdf_url)
    if tgz_href:
        package_url = _canonical_https_url(_https_href(tgz_href))
        package = _fetch_bytes(package_url, opener, authorize_url)
        return _pdf_from_tarball(package, package_url)
    raise ValueError(f"PMC OA record at {canonical_record_url} carries no pdf or tgz link")


def _https_href(href: str) -> str:
    value = href.strip()
    if value.startswith("ftp://"):
        return "https://" + value.removeprefix("ftp://")
    return value


def _pdf_from_tarball(package: bytes, package_url: str) -> bytes:
    try:
        stream_limit = MAX_TAR_TOTAL_BYTES + (2 * MAX_TAR_MEMBERS + 2) * tarfile.BLOCKSIZE
        with gzip.GzipFile(fileobj=io.BytesIO(package), mode="rb") as compressed:
            with tarfile.open(
                fileobj=_CappedTarStream(compressed, stream_limit, package_url), mode="r|"
            ) as archive:
                member_count = 0
                total_size = 0
                pdf_bytes: bytes | None = None
                for member in archive:
                    member_count += 1
                    if member_count > MAX_TAR_MEMBERS:
                        raise ValueError(f"PMC OA package at {package_url} has too many members")
                    if not member.isfile():
                        continue
                    if member.size < 0 or member.size > MAX_PDF_MEMBER_BYTES:
                        raise ValueError(f"PMC OA package at {package_url} has an oversized member")
                    total_size += member.size
                    if total_size > MAX_TAR_TOTAL_BYTES:
                        raise ValueError(
                            f"PMC OA package at {package_url} exceeds the member limit"
                        )
                    if not member.name.casefold().endswith(".pdf"):
                        continue
                    handle = archive.extractfile(member)
                    if handle is None:
                        raise ValueError(
                            f"PMC OA package at {package_url} cannot read {member.name}"
                        )
                    candidate = _require_pdf(
                        _read_limited(
                            handle,
                            MAX_PDF_MEMBER_BYTES,
                            f"{package_url}!{member.name}",
                            "PDF member",
                        ),
                        f"{package_url}!{member.name}",
                    )
                    if pdf_bytes is not None:
                        raise ValueError(
                            f"PMC OA package at {package_url} has multiple PDF members"
                        )
                    pdf_bytes = candidate
    except (tarfile.TarError, EOFError, OSError) as exc:
        raise ValueError(f"PMC OA package at {package_url} could not be read") from exc
    if pdf_bytes is None:
        raise ValueError(f"PMC OA package at {package_url} contains no PDF member")
    return pdf_bytes
