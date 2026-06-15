"""L1 component tests for check-test-refs (ADR-44)."""

import check_test_refs as _m

MD_LINK = _m.MD_LINK
Path = _m.Path
REPO_PATH = _m.REPO_PATH
check_protocol = _m.check_protocol


def test_md_link_regex_matches_markdown_links():
    assert MD_LINK.findall("[text](target.md)") == ["target.md"]
    assert MD_LINK.findall("![alt](image.png)") == []
    assert MD_LINK.findall("[t](file.md#heading)") == ["file.md#heading"]
    assert len(MD_LINK.findall("[a](x.md) and [b](y.md)")) == 2


def test_repo_path_regex_matches_backticked_repo_paths():
    assert REPO_PATH.findall("`docs/reference/policy-mcp.md`") == ["docs/reference/policy-mcp.md"]
    assert REPO_PATH.findall("`project-files/tests/coverage-matrix.md`") == [
        "project-files/tests/coverage-matrix.md"
    ]
    assert REPO_PATH.findall("`src/something.md`") == []
    assert REPO_PATH.findall("docs/reference/policy-mcp.md") == []


def test_check_protocol_accepts_valid_links(tmp_path):
    proto_dir = tmp_path / "project-files" / "tests"
    proto_dir.mkdir(parents=True)
    (tmp_path / "docs" / "reference").mkdir(parents=True)
    (tmp_path / "docs" / "reference" / "policy-mcp.md").write_text("# Policy MCP\n")

    valid = proto_dir / "valid.md"
    valid.write_text(
        "See [policy](../../docs/reference/policy-mcp.md) and "
        "`docs/reference/policy-mcp.md` for details.\n"
        "[external](https://example.com) should be skipped.\n"
    )

    assert check_protocol(valid, tmp_path) == []


def test_check_protocol_reports_broken_relative_link(tmp_path):
    proto_dir = tmp_path / "project-files" / "tests"
    proto_dir.mkdir(parents=True)
    broken_link = proto_dir / "broken-link.md"
    broken_link.write_text("[missing](../../docs/nonexistent.md)\n")

    errs = check_protocol(broken_link, tmp_path)

    assert len(errs) == 1
    assert "broken link" in errs[0]


def test_check_protocol_reports_stale_repo_path(tmp_path):
    proto_dir = tmp_path / "project-files" / "tests"
    proto_dir.mkdir(parents=True)
    stale = proto_dir / "stale.md"
    stale.write_text("Refer to `docs/dissolved/old-page.md` here.\n")

    errs = check_protocol(stale, tmp_path)

    assert len(errs) == 1
    assert "stale repo path" in errs[0]


def test_check_protocol_reports_multiple_errors(tmp_path):
    proto_dir = tmp_path / "project-files" / "tests"
    proto_dir.mkdir(parents=True)
    multi = proto_dir / "multi.md"
    multi.write_text("[bad](../../no-such.md)\n`docs/fake/path.md` and `project-files/fake.md`\n")

    assert len(check_protocol(multi, tmp_path)) == 3
