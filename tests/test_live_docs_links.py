"""Tests for the published docs live-link checker."""

from scripts.checks.check_live_docs_links import LiveDocsChecker


def test_live_docs_checker_accepts_internal_fragments_and_local_github_links(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "README.md").write_text("# Docs\n", encoding="utf-8")

    checker = LiveDocsChecker("https://example.invalid/memoria-vault/", tmp_path, timeout=1)
    pages = {
        "https://example.invalid/memoria-vault/": (
            '<a href="page/#target">page</a>'
            '<a href="https://github.com/eranroseman/memoria-vault/blob/main/docs/README.md">'
            "repo</a>"
        ),
        "https://example.invalid/memoria-vault/page/": '<h2 id="target">Target</h2>',
        "https://example.invalid/memoria-vault/page": '<h2 id="target">Target</h2>',
    }
    checker._fetch_html = pages.get  # type: ignore[method-assign]
    result = checker.run()

    assert result.errors == []
    assert result.pages == 2
    assert result.internal_link_refs_checked == 1
    assert result.external_targets_checked == 1


def test_live_docs_checker_reports_missing_fragment_and_local_github_target(tmp_path):
    checker = LiveDocsChecker("https://example.invalid/memoria-vault/", tmp_path, timeout=1)
    pages = {
        "https://example.invalid/memoria-vault/": (
            '<a href="page/#missing">page</a>'
            '<a href="https://github.com/eranroseman/memoria-vault/blob/main/docs/missing.md">'
            "repo</a>"
        ),
        "https://example.invalid/memoria-vault/page": "<h2>No anchor</h2>",
    }
    checker._fetch_html = pages.get  # type: ignore[method-assign]
    result = checker.run()

    assert any("missing fragment" in error for error in result.errors)
    assert any("GitHub blob target missing locally" in error for error in result.errors)
    assert result.bad_internal_fragments == 1
    assert result.broken_external_targets == 1


def test_live_docs_checker_checks_queued_external_targets(tmp_path):
    checker = LiveDocsChecker(
        "https://example.invalid/memoria-vault/",
        tmp_path,
        timeout=1,
        external_workers=1,
    )
    checker._fetch_html = lambda url: '<a href="https://docs.example.invalid/missing">x</a>'  # type: ignore[method-assign]

    def fake_external(url, source):
        return [], [f"{source}: external HTTP 404 {url}"], 1

    checker._check_external_target = fake_external  # type: ignore[method-assign]

    result = checker.run()

    assert result.external_targets_checked == 1
    assert result.broken_external_targets == 1
    assert result.errors == [
        "https://example.invalid/memoria-vault/: external HTTP 404 "
        "https://docs.example.invalid/missing"
    ]
