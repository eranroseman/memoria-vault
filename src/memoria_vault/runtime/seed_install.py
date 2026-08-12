"""Policy-bound fetch helpers for the licensed seed corpus."""

from __future__ import annotations

import gzip
import io
import tarfile
from collections.abc import Callable
from http.client import HTTPException
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from xml.parsers import expat

from memoria_vault.product.seed_corpus import load_seed_manifest
from memoria_vault.runtime import state
from memoria_vault.runtime.capture import stage_pdf_source
from memoria_vault.runtime.trusted_writer import OperationContext, validate_operation_context
from memoria_vault.runtime.vaultio import iter_markdown, read_frontmatter

MAX_FETCH_BYTES = 32 * 1024 * 1024
MAX_TAR_MEMBERS = 128
MAX_TAR_TOTAL_BYTES = 32 * 1024 * 1024
MAX_PDF_MEMBER_BYTES = 32 * 1024 * 1024
MAX_PMC_XML_ELEMENTS = 1024
MAX_SEED_DIAGNOSTIC_BYTES = 1_024
SEED_FETCH_USER_AGENT = "Memoria/0.1 (+https://github.com/eranroseman/memoria-vault)"


def _bounded_seed_error(value: BaseException) -> str:
    return str(value).encode("utf-8")[:MAX_SEED_DIAGNOSTIC_BYTES].decode("utf-8", errors="ignore")


class SeedInstallAllFailed(ValueError):  # noqa: N818 -- public contract names the outcome.
    def __init__(self, diagnostics: dict[str, list[Any]]) -> None:
        self.diagnostics = diagnostics
        names = ", ".join(str(entry["id"]) for entry in diagnostics["failed"]) or "<no rows>"
        super().__init__(f"seed install left zero rows present; failed rows: {names}")


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
    request = Request(url, headers={"User-Agent": SEED_FETCH_USER_AGENT})
    return build_opener(_NoRedirect()).open(request, timeout=30.0)


def resolve_fetch(
    row: dict[str, Any],
    *,
    opener: Callable[[str], Any] | None = None,
    authorize_url: Callable[[str], None],
) -> bytes:
    """Fetch one declared PDF only after validating and authorizing every URL."""
    fetch = row.get("fetch")
    if not isinstance(fetch, dict):
        fetch = {}
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


def seed_install(
    vault: Path,
    rows: list[dict[str, Any]] | None = None,
    *,
    opener: Callable[[str], Any] | None = None,
    authorize_url: Callable[[str], None],
    context: OperationContext,
) -> dict[str, Any]:
    """Install the seed corpus through the shipped local-PDF capture seam.

    Idempotency and honesty (O1 spec section 2): each row pre-checks
    state.catalog_source and skips on a hit - no fetch, no journal event,
    no commit; failures are per-row and named; the failure exit fires only
    when zero rows are present (admitted + skipped both empty).
    """
    validate_operation_context(vault, context)
    vault = Path(vault)
    if rows is None:
        rows = load_seed_manifest()
    admitted: list[str] = []
    skipped: list[str] = []
    failed: list[dict[str, str]] = []
    for row in rows:
        work_id = str(row["id"])
        if state.catalog_source(vault, work_id) is not None:
            skipped.append(work_id)
            continue
        try:
            raw = resolve_fetch(row, opener=opener, authorize_url=authorize_url)
            stage_pdf_source(
                vault,
                work_id,
                str(row["title"]),
                f"Seed corpus source: {row['title']}",
                raw,
                context=context,
                raw_filename=f"{work_id}.pdf",
                resource=_row_resource(row),
                identifiers=_row_identifiers(row),
                csl_json=_row_csl(row),
            )
        except Exception as exc:  # noqa: BLE001 -- per-row honesty: name the row, keep going.
            failed.append({"id": work_id, "error": _bounded_seed_error(exc)})
            continue
        admitted.append(work_id)
    if not admitted and not skipped:
        raise SeedInstallAllFailed({"admitted": admitted, "skipped": skipped, "failed": failed})
    notices: list[str] = []
    if not _has_active_project(vault):
        notices.append(
            "no active project found - frame your tutorial project first "
            "(docs/tutorials/01) or discovery ranking starts empty"
        )
    return {
        "admitted": admitted,
        "skipped": skipped,
        "failed": failed,
        "notices": notices,
        "telemetry": _emit_seed_installed(vault),
    }


def _row_identifiers(row: dict[str, Any]) -> dict[str, Any]:
    identifier = str(row.get("identifier") or "")
    if identifier.startswith("doi:"):
        return {"doi": identifier.removeprefix("doi:")}
    if identifier.startswith("arxiv:"):
        return {"arxiv": identifier.removeprefix("arxiv:")}
    return {}


def _row_resource(row: dict[str, Any]) -> str:
    identifier = str(row.get("identifier") or "")
    if identifier.startswith("doi:"):
        return f"https://doi.org/{identifier.removeprefix('doi:')}"
    if identifier.startswith("arxiv:"):
        return f"https://arxiv.org/abs/{identifier.removeprefix('arxiv:')}"
    return str(row.get("license_evidence") or "")


def _row_csl(row: dict[str, Any]) -> dict[str, Any]:
    # Mirrors cli._csl_json so seed rows carry the same catalog metadata shape
    # as `memoria work add`.
    csl: dict[str, Any] = {
        "id": str(row["id"]),
        "type": "article-journal",
        "title": str(row["title"]),
    }
    identifiers = _row_identifiers(row)
    if "doi" in identifiers:
        csl["DOI"] = identifiers["doi"]
    resource = _row_resource(row)
    if resource:
        csl["URL"] = resource
    return csl


def _has_active_project(vault: Path) -> bool:
    # Active = type: project and not lifecycle archived/retracted - the repo's
    # concept-file convention (knowledge.py _is_current_frontmatter); covers
    # projects/<slug>.md and projects/<slug>/project.md homes.
    projects_root = vault / "projects"
    if not projects_root.is_dir():
        return False
    for path in iter_markdown(projects_root):
        frontmatter = read_frontmatter(path)
        if frontmatter.get("type") != "project":
            continue
        if frontmatter.get("lifecycle") in {"retracted", "archived"}:
            continue
        return True
    return False


def _emit_seed_installed(vault: Path) -> dict[str, str]:
    """Record the required first-install observer; section T owns the helper."""
    from memoria_vault.runtime.onboarding_steps import emit_onboarding_step

    event_id = emit_onboarding_step(vault, "seed-installed")
    if event_id is None:
        return {"status": "unavailable"}
    return {"status": "emitted", "event_id": event_id}
