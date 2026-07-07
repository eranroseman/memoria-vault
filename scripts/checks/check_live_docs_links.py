#!/usr/bin/env python3
"""Crawl the published docs site and fail on hard-broken links."""

from __future__ import annotations

import argparse
import concurrent.futures
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib import error, parse, request

GITHUB_REPO = "github.com"
GITHUB_REPO_PATH = "/eranroseman/memoria-vault/"
HARD_EXTERNAL_FAILURES = {400, 404, 410}


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {name: value for name, value in attrs if value}
        if "id" in attr:
            self.ids.add(attr["id"])
        if "name" in attr:
            self.ids.add(attr["name"])
        if tag in {"a", "link"} and "href" in attr:
            self.links.append(attr["href"])


@dataclass
class CrawlResult:
    pages: int = 0
    links: int = 0
    internal_targets_checked: int = 0
    internal_link_refs_checked: int = 0
    broken_internal_targets: int = 0
    bad_internal_fragments: int = 0
    external_targets_checked: int = 0
    broken_external_targets: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class LiveDocsChecker:
    def __init__(
        self,
        base_url: str,
        root: Path,
        timeout: float = 10.0,
        internal_workers: int = 16,
        external_workers: int = 24,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.base = parse.urlparse(self.base_url)
        self.root = root
        self.timeout = timeout
        self.internal_workers = max(1, internal_workers)
        self.external_workers = max(1, external_workers)
        self.seen_pages: set[str] = set()
        self.seen_external: set[str] = set()
        self.pending_external: dict[str, str] = {}
        self.html_cache: dict[str, str | None] = {}
        self.page_ids: dict[str, set[str]] = {}
        self.internal_fragment_refs: list[tuple[str, str, str]] = []
        self.result = CrawlResult()

    def run(self) -> CrawlResult:
        pending = {self._page_url(self.base_url)}
        while pending:
            batch = sorted(url for url in pending if url not in self.seen_pages)
            pending = set()
            if not batch:
                continue
            self.seen_pages.update(batch)
            for page_url, html in self._fetch_pages(batch):
                if html is None:
                    continue
                self.result.pages += 1
                parser = _Links()
                parser.feed(html)
                self.page_ids[page_url] = parser.ids
                self._check_fragment(page_url, parser.ids)
                pending.update(self._handle_links(page_url, parser.links))
        self._check_internal_fragments()
        self._check_pending_external()
        return self.result

    def _fetch_pages(self, urls: list[str]) -> list[tuple[str, str | None]]:
        if len(urls) == 1:
            url = urls[0]
            return [(url, self._fetch_html(url))]
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.internal_workers) as pool:
            return list(zip(urls, pool.map(self._fetch_html, urls), strict=True))

    def _handle_links(self, page_url: str, links: list[str]) -> set[str]:
        pending: set[str] = set()
        for href in links:
            if self._skip(href):
                continue
            self.result.links += 1
            target = parse.urljoin(page_url, href)
            clean, fragment = parse.urldefrag(target)
            if self._is_internal(clean):
                self.result.internal_link_refs_checked += 1
                if fragment:
                    self.internal_fragment_refs.append((page_url, clean, fragment))
                if self._looks_like_page(clean):
                    pending.add(clean)
            elif self._is_same_repo_github(clean):
                self._check_same_repo_github(clean, page_url)
            else:
                self._check_external(clean, page_url)
        return pending

    def _check_internal_fragments(self) -> None:
        for page_url, clean, fragment in self.internal_fragment_refs:
            ids = self.page_ids.get(clean)
            if ids is None:
                ids = self._ids_for(clean)
            if fragment not in ids:
                self.result.bad_internal_fragments += 1
                self.result.errors.append(f"{page_url}: missing fragment {clean}#{fragment}")

    def _ids_for(self, url: str) -> set[str]:
        html = self._fetch_html(url)
        if html is None:
            return set()
        parser = _Links()
        parser.feed(html)
        return parser.ids

    def _fetch_html(self, url: str) -> str | None:
        if url in self.html_cache:
            return self.html_cache[url]
        try:
            if self._is_internal(url):
                self.result.internal_targets_checked += 1
            with request.urlopen(url, timeout=self.timeout) as response:
                content_type = response.headers.get("content-type", "")
                body = response.read()
        except error.HTTPError as exc:
            if self._is_internal(url):
                self.result.broken_internal_targets += 1
            self.result.errors.append(f"{url}: HTTP {exc.code}")
            self.html_cache[url] = None
            return None
        except (OSError, TimeoutError, error.URLError) as exc:
            if self._is_internal(url):
                self.result.broken_internal_targets += 1
            self.result.errors.append(f"{url}: {exc}")
            self.html_cache[url] = None
            return None

        if "text/html" not in content_type:
            self.html_cache[url] = None
            return None
        html = body.decode("utf-8", errors="replace")
        self.html_cache[url] = html
        return html

    def _check_fragment(self, url: str, ids: set[str]) -> None:
        _, fragment = parse.urldefrag(url)
        if fragment and fragment not in ids:
            self.result.bad_internal_fragments += 1
            self.result.errors.append(f"{url}: missing fragment")

    def _check_external(self, url: str, source: str) -> None:
        if url in self.seen_external:
            return
        self.seen_external.add(url)
        self.result.external_targets_checked += 1
        self.pending_external[url] = source

    def _check_pending_external(self) -> None:
        if not self.pending_external:
            return
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.external_workers) as pool:
            checks = {
                pool.submit(self._check_external_target, url, source): url
                for url, source in sorted(self.pending_external.items())
            }
            for check in concurrent.futures.as_completed(checks):
                warnings, errors, broken = check.result()
                self.result.warnings.extend(warnings)
                self.result.errors.extend(errors)
                self.result.broken_external_targets += broken

    def _check_external_target(self, url: str, source: str) -> tuple[list[str], list[str], int]:
        req = request.Request(url, method="HEAD", headers={"User-Agent": "MemoriaLinkCheck/1"})
        try:
            with request.urlopen(req, timeout=self.timeout):
                return [], [], 0
        except error.HTTPError as exc:
            if exc.code in {405, 403}:
                return [], [], 0
            if exc.code in HARD_EXTERNAL_FAILURES:
                return [], [f"{source}: external HTTP {exc.code} {url}"], 1
            return [f"{source}: external HTTP {exc.code} {url}"], [], 0
        except (OSError, TimeoutError, error.URLError) as exc:
            return [f"{source}: external unchecked {url} ({exc})"], [], 0

    def _check_same_repo_github(self, url: str, source: str) -> None:
        if url in self.seen_external:
            return
        parsed = parse.urlparse(url)
        parts = parsed.path.removeprefix(GITHUB_REPO_PATH).split("/")
        if len(parts) < 3 or parts[1] != "main" or parts[0] not in {"blob", "tree"}:
            self._check_external(url, source)
            return

        self.seen_external.add(url)
        self.result.external_targets_checked += 1
        local = self.root / "/".join(parts[2:])
        exists = local.is_dir() if parts[0] == "tree" else local.is_file()
        if not exists:
            self.result.broken_external_targets += 1
            self.result.errors.append(
                f"{source}: GitHub {parts[0]} target missing locally: {local}"
            )

    def _is_internal(self, url: str) -> bool:
        parsed = parse.urlparse(url)
        return (
            parsed.scheme in {"http", "https"}
            and parsed.netloc == self.base.netloc
            and parsed.path.startswith(self.base.path)
        )

    def _is_same_repo_github(self, url: str) -> bool:
        parsed = parse.urlparse(url)
        return parsed.netloc == GITHUB_REPO and parsed.path.startswith(GITHUB_REPO_PATH)

    def _looks_like_page(self, url: str) -> bool:
        path = parse.urlparse(url).path
        return path.endswith(("/", ".html", ".htm")) or "." not in Path(path).name

    @staticmethod
    def _page_url(url: str) -> str:
        clean, _ = parse.urldefrag(url)
        return clean

    @staticmethod
    def _skip(href: str) -> bool:
        return href.startswith(("mailto:", "tel:", "javascript:")) or not href.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-url",
        default="https://eranroseman.github.io/memoria-vault/",
        help="Published docs root to crawl.",
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Candidate repo root.")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--internal-workers", type=int, default=16)
    parser.add_argument("--external-workers", type=int, default=24)
    args = parser.parse_args(argv)

    result = LiveDocsChecker(
        args.base_url,
        args.root,
        timeout=args.timeout,
        internal_workers=args.internal_workers,
        external_workers=args.external_workers,
    ).run()
    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    for failure in result.errors:
        print(f"error: {failure}", file=sys.stderr)
    print(f"live-docs-links: pages crawled: {result.pages}")
    print(f"live-docs-links: internal targets checked: {result.internal_targets_checked}")
    print(f"live-docs-links: internal link refs checked: {result.internal_link_refs_checked}")
    print(f"live-docs-links: broken internal targets: {result.broken_internal_targets}")
    print(f"live-docs-links: bad internal fragments: {result.bad_internal_fragments}")
    print(f"live-docs-links: external targets checked: {result.external_targets_checked}")
    print(f"live-docs-links: broken external targets: {result.broken_external_targets}")
    print(f"live-docs-links: total links checked: {result.links}")
    if result.errors:
        print(f"live-docs-links: FAILED ({len(result.errors)} error(s))", file=sys.stderr)
        return 1
    print("live-docs-links: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
