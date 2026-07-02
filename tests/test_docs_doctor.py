"""L1 component tests for docs_doctor (ADR-44)."""

import docs_doctor as _m

check_broken_vault_wikilinks = _m.check_broken_vault_wikilinks
check_bare_adr_codes = _m.check_bare_adr_codes
check_frontmatter = _m.check_frontmatter
check_hidden_compatibility_page = _m.check_hidden_compatibility_page
check_link_text = _m.check_link_text
check_links = _m.check_links
check_model_spine_link = _m.check_model_spine_link
check_readmes = _m.check_readmes
check_reference_readme_index = _m.check_reference_readme_index
check_site_excluded_targets = _m.check_site_excluded_targets
check_site_local_links = _m.check_site_local_links
check_site_nav_hierarchy = _m.check_site_nav_hierarchy
check_template_frontmatter = _m.check_template_frontmatter
check_thin_folders = _m.check_thin_folders
check_vocabulary_reference_mirror = _m.check_vocabulary_reference_mirror
check_wikilink_aliases = _m.check_wikilink_aliases
check_wikilinks = _m.check_wikilinks
gh_slug = _m.gh_slug
heading_slugs = _m.heading_slugs
site_excluded_dirs = _m._site_excluded_dirs


def test_gh_slug_matches_github_heading_rules():
    assert gh_slug("Install requirements") == "install-requirements"
    assert gh_slug("`code` in heading") == "code-in-heading"
    assert gh_slug("[text](url) heading") == "text-heading"
    assert gh_slug("What's new?") == "whats-new"


def test_check_readmes_flags_missing_indexes_only_for_multi_file_folders(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "a.md").write_text("# A\n")
    (tmp_path / "sub" / "b.md").write_text("# B\n")
    (tmp_path / "single").mkdir()
    (tmp_path / "single" / "only.md").write_text("# Only\n")
    release = tmp_path / "releasing" / "0.1.0-alpha.11"
    release.mkdir(parents=True)
    (release / "release-plan-0.1.0-alpha.11.md").write_text("# Plan\n")
    (release / "validation-log.md").write_text("# Evidence\n")

    errs: list[str] = []
    check_readmes(tmp_path, errs)

    assert any("missing README.md" in e for e in errs)
    assert any("sub/" in e and "missing README.md" in e for e in errs)
    assert not any("0.1.0-alpha.11/" in e for e in errs)

    (tmp_path / "README.md").write_text("# Root\n")
    errs2: list[str] = []
    check_readmes(tmp_path, errs2)

    assert not any("single/" in e for e in errs2)


def test_check_frontmatter_flags_disallowed_keys_and_unquoted_colons(tmp_path):
    bad = tmp_path / "bad.md"
    bad.write_text("---\nmode: reference\ntitle: X\n---\n# X\n")
    bad2 = tmp_path / "bad2.md"
    bad2.write_text("---\ntitle: Linter: detectors\n---\n# X\n")

    errs: list[str] = []
    errs2: list[str] = []
    check_frontmatter(bad, errs)
    check_frontmatter(bad2, errs2)

    assert len(errs) == 1
    assert len(errs2) == 1


def test_check_frontmatter_accepts_clean_and_missing_frontmatter(tmp_path):
    good = tmp_path / "good.md"
    good.write_text('---\ntitle: "Clean: title"\nstatus: draft\n---\n# X\n')
    nofm = tmp_path / "nofm.md"
    nofm.write_text("# Just a heading\n")

    errs: list[str] = []
    errs2: list[str] = []
    check_frontmatter(good, errs)
    check_frontmatter(nofm, errs2)

    assert errs == []
    assert errs2 == []


def test_check_links_validates_relative_links_and_anchors(tmp_path):
    (tmp_path / "target.md").write_text("# Real heading\n## Sub section\n")
    good = tmp_path / "good.md"
    good.write_text("[link](target.md)\n[anchor](target.md#sub-section)\n")
    bad = tmp_path / "bad.md"
    bad.write_text("[link](nonexistent.md)\n")
    bad_anchor = tmp_path / "bad-anchor.md"
    bad_anchor.write_text("[link](target.md#no-such-anchor)\n")
    self_anchor = tmp_path / "self.md"
    self_anchor.write_text("# Top\n## Details\n[jump](#details)\n[bad](#nope)\n")

    good_errs: list[str] = []
    bad_errs: list[str] = []
    anchor_errs: list[str] = []
    self_errs: list[str] = []
    check_links(good, good_errs)
    check_links(bad, bad_errs)
    check_links(bad_anchor, anchor_errs)
    check_links(self_anchor, self_errs)

    assert good_errs == []
    assert len(bad_errs) == 1
    assert len(anchor_errs) == 1
    assert len(self_errs) == 1


def test_check_links_ignores_links_inside_fenced_code(tmp_path):
    code = tmp_path / "code.md"
    code.write_text("```\n[link](nonexistent.md)\n```\n")
    errs: list[str] = []

    check_links(code, errs)

    assert errs == []


def test_check_wikilinks_flags_doc_resolving_wikilinks_but_allows_vault_citations(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("See [[policy-mcp]] for details.\n")
    md2 = tmp_path / "test2.md"
    md2.write_text("See [[someCitekey]] here.\n")
    md3 = tmp_path / "test3.md"
    md3.write_text("Use `[[policy-mcp]]` syntax.\n")

    doc_names = {"policy-mcp.md", "readme.md"}
    errs: list[str] = []
    errs2: list[str] = []
    errs3: list[str] = []
    check_wikilinks(md, errs, doc_names)
    check_wikilinks(md2, errs2, doc_names)
    check_wikilinks(md3, errs3, doc_names)

    assert len(errs) == 1
    assert errs2 == []
    assert errs3 == []


def test_check_link_text_flags_filename_or_stem_as_link_text(tmp_path):
    filename_text = tmp_path / "filename.md"
    filename_text.write_text("[policy-mcp.md](policy-mcp.md)\n")
    stem_text = tmp_path / "stem.md"
    stem_text.write_text("[policy-mcp](policy-mcp.md)\n")
    proper = tmp_path / "proper.md"
    proper.write_text("[Policy gate reference](policy-mcp.md)\n")
    external = tmp_path / "external.md"
    external.write_text("[policy-mcp](https://example.com/policy-mcp.md)\n")

    filename_errs: list[str] = []
    stem_errs: list[str] = []
    proper_errs: list[str] = []
    external_errs: list[str] = []
    check_link_text(filename_text, filename_errs)
    check_link_text(stem_text, stem_errs)
    check_link_text(proper, proper_errs)
    check_link_text(external, external_errs)

    assert len(filename_errs) == 1
    assert len(stem_errs) == 1
    assert proper_errs == []
    assert external_errs == []


def test_check_wikilink_aliases_requires_aliases_except_anchor_only_links(tmp_path):
    bare = tmp_path / "bare.md"
    bare.write_text("See [[some-note]] for info.\n")
    aliased = tmp_path / "aliased.md"
    aliased.write_text("See [[some-note|Some Note]] for info.\n")
    anchor = tmp_path / "anchor.md"
    anchor.write_text("See [[#heading]] here.\n")

    bare_errs: list[str] = []
    aliased_errs: list[str] = []
    anchor_errs: list[str] = []
    check_wikilink_aliases(bare, bare_errs)
    check_wikilink_aliases(aliased, aliased_errs)
    check_wikilink_aliases(anchor, anchor_errs)

    assert len(bare_errs) == 1
    assert aliased_errs == []
    assert anchor_errs == []


def test_check_broken_vault_wikilinks_validates_note_targets_and_ignores_assets_or_code(tmp_path):
    stems = {"real-note", "good"}
    missing = tmp_path / "missing.md"
    missing.write_text("See [[ghost-note|A Title]] here.\n")
    existing = tmp_path / "existing.md"
    existing.write_text("See [[real-note|A Title]] here.\n")
    anchor = tmp_path / "anchor.md"
    anchor.write_text("See [[good#section]] here.\n")
    asset = tmp_path / "asset.md"
    asset.write_text("![[90-assets/img.png]]\n")
    code = tmp_path / "code.md"
    code.write_text("Use `[[ghost-note]]` syntax.\n")

    missing_errs: list[str] = []
    existing_errs: list[str] = []
    anchor_errs: list[str] = []
    asset_errs: list[str] = []
    code_errs: list[str] = []
    check_broken_vault_wikilinks(missing, missing_errs, stems)
    check_broken_vault_wikilinks(existing, existing_errs, stems)
    check_broken_vault_wikilinks(anchor, anchor_errs, stems)
    check_broken_vault_wikilinks(asset, asset_errs, stems)
    check_broken_vault_wikilinks(code, code_errs, stems)

    assert len(missing_errs) == 1
    assert existing_errs == []
    assert anchor_errs == []
    assert asset_errs == []
    assert code_errs == []


def test_reference_readme_index_flags_missing_reference_pages(tmp_path):
    reference = tmp_path / "docs" / "reference"
    reference.mkdir(parents=True)
    (reference / "README.md").write_text("[A](a.md)\n", encoding="utf-8")
    (reference / "a.md").write_text("# A\n", encoding="utf-8")
    (reference / "b.md").write_text("# B\n", encoding="utf-8")

    errors: list[str] = []
    check_reference_readme_index(tmp_path, errors)

    assert len(errors) == 1
    assert "reference index omits page(s): b.md" in errors[0]


def test_check_template_frontmatter_validates_yaml_fences(tmp_path):
    bad = tmp_path / "tmpl.md"
    bad.write_text("# Template\n\n```yaml\ntitle: X\nmode: reference\n```\n")
    good = tmp_path / "tmpl2.md"
    good.write_text("# Template\n\n```yaml\ntitle: X\nstatus: draft\n```\n")

    bad_errs: list[str] = []
    good_errs: list[str] = []
    check_template_frontmatter(bad, bad_errs)
    check_template_frontmatter(good, good_errs)

    assert len(bad_errs) == 1
    assert good_errs == []


def test_check_thin_folders_warns_for_site_folders_but_skips_site_excluded(tmp_path):
    (tmp_path / "README.md").write_text("# Root\n")
    (tmp_path / "thin").mkdir()
    (tmp_path / "thin" / "only.md").write_text("# Only\n")
    (tmp_path / "releasing").mkdir()
    (tmp_path / "releasing" / "README.md").write_text("# Releasing\n")
    (tmp_path / "releasing" / "plan.md").write_text("# Plan\n")

    warns: list[str] = []
    check_thin_folders(tmp_path, warns)

    assert any("thin/" in w for w in warns)
    assert not any("releasing/" in w for w in warns)


def test_check_site_local_links_blocks_published_pages_that_leave_the_site(tmp_path):
    repo = tmp_path
    root = repo / "docs"
    (root / "reference").mkdir(parents=True)
    (repo / "src").mkdir()
    (repo / "src" / "file.py").write_text("x = 1\n")
    (root / "reference" / "sibling.md").write_text("# Sibling\n")
    published = root / "reference" / "x.md"
    published.write_text("[code](../../src/file.py)\n[doc](sibling.md)\n")

    errs: list[str] = []
    check_site_local_links(published, root, errs)

    assert len(errs) == 1
    assert "leaves the published site" in errs[0]


def test_check_site_local_links_allows_in_site_excluded_and_inline_code_links(tmp_path):
    repo = tmp_path
    root = repo / "docs"
    (root / "reference").mkdir(parents=True)
    (repo / "src").mkdir()
    (repo / "src" / "file.py").write_text("x = 1\n")
    (root / "reference" / "sibling.md").write_text("# Sibling\n")
    doc = root / "reference" / "onlydoc.md"
    doc.write_text("[doc](sibling.md)\n")
    code = root / "reference" / "codey.md"
    code.write_text("Edit `[x](../../src/file.py)` here.\n")
    (root / "releasing").mkdir()
    excluded = root / "releasing" / "plan.md"
    excluded.write_text("[code](../../src/file.py)\n")

    doc_errs: list[str] = []
    code_errs: list[str] = []
    excluded_errs: list[str] = []
    check_site_local_links(doc, root, doc_errs)
    check_site_local_links(code, root, code_errs)
    check_site_local_links(excluded, root, excluded_errs)

    assert doc_errs == []
    assert code_errs == []
    assert excluded_errs == []


def test_site_excluded_dirs_are_read_from_jekyll_config(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()
    (root / "_config.yml").write_text(
        'exclude:\n  - internal/\n  - "**/tmp/"\n',
        encoding="utf-8",
    )
    _m._SITE_EXCLUDE_CACHE.clear()

    assert site_excluded_dirs(root) == {"internal"}


def test_check_site_excluded_targets_blocks_published_links_to_excluded_docs(tmp_path):
    root = tmp_path / "docs"
    ref = root / "reference"
    internal = root / "internal"
    adr = root / "adr"
    ref.mkdir(parents=True)
    internal.mkdir()
    adr.mkdir()
    (root / "_config.yml").write_text("exclude:\n  - internal/\n", encoding="utf-8")
    (internal / "README.md").write_text("# Internal\n", encoding="utf-8")
    (adr / "README.md").write_text("# Decisions\n", encoding="utf-8")
    page = ref / "page.md"
    page.write_text("[bad](../internal/README.md)\n[good](../adr/README.md)\n")
    _m._SITE_EXCLUDE_CACHE.clear()

    errs: list[str] = []
    check_site_excluded_targets(page, root, errs)

    assert len(errs) == 1
    assert "excluded page" in errs[0]


def test_check_model_spine_link_warns_when_model_is_repeated_without_spine_link(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()
    page = root / "overview.md"
    page.write_text("Memoria is a research operating system with a Co-PI.\n", encoding="utf-8")
    linked = root / "linked.md"
    linked.write_text(
        "Memoria is a research operating system. See [Home](README.md#the-model).\n",
        encoding="utf-8",
    )

    warnings: list[str] = []
    linked_warnings: list[str] = []
    check_model_spine_link(page, root, warnings)
    check_model_spine_link(linked, root, linked_warnings)

    assert len(warnings) == 1
    assert linked_warnings == []


def test_check_hidden_compatibility_page_rejects_hidden_permalink_stub(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()
    page = root / "old-page.md"
    page.write_text(
        "---\n"
        "title: Old page\n"
        "nav_exclude: true\n"
        "permalink: /old-page/\n"
        "---\n\n"
        "# Old page\n\n"
        "Moved.\n",
        encoding="utf-8",
    )

    errors: list[str] = []
    check_hidden_compatibility_page(page, root, errors)

    assert len(errors) == 1
    assert "hidden compatibility pages are forbidden" in errors[0]


def test_check_site_nav_hierarchy_validates_parent_containers(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()
    (root / "README.md").write_text(
        "---\ntitle: Home\nhas_children: true\n---\n# Home\n", encoding="utf-8"
    )
    (root / "reference.md").write_text(
        "---\ntitle: Reference\nhas_children: true\n---\n# Reference\n", encoding="utf-8"
    )
    (root / "group.md").write_text(
        "---\ntitle: Group\nparent: Reference\n---\n# Group\n", encoding="utf-8"
    )
    (root / "child.md").write_text(
        "---\ntitle: Child\nparent: Group\ngrand_parent: Reference\n---\n# Child\n",
        encoding="utf-8",
    )

    errors: list[str] = []
    check_site_nav_hierarchy(root, errors)

    assert len(errors) == 1
    assert "not marked has_children: true" in errors[0]


def test_check_site_nav_hierarchy_requires_grandparent_for_nested_children(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()
    (root / "reference.md").write_text(
        "---\ntitle: Reference\nhas_children: true\n---\n# Reference\n", encoding="utf-8"
    )
    (root / "group.md").write_text(
        "---\ntitle: Group\nparent: Reference\nhas_children: true\n---\n# Group\n",
        encoding="utf-8",
    )
    (root / "child.md").write_text(
        "---\ntitle: Child\nparent: Group\n---\n# Child\n",
        encoding="utf-8",
    )
    (root / "bad.md").write_text(
        "---\ntitle: Bad\nparent: Group\ngrand_parent: Missing\n---\n# Bad\n",
        encoding="utf-8",
    )

    errors: list[str] = []
    check_site_nav_hierarchy(root, errors)

    assert any("must set grand_parent: Reference" in error for error in errors)
    assert any("parent 'Group' under 'Missing' has no published page" in error for error in errors)


def test_check_bare_adr_codes_requires_links_in_published_docs(tmp_path):
    root = tmp_path / "docs"
    ref = root / "reference"
    adr = root / "adr"
    releasing = root / "releasing"
    ref.mkdir(parents=True)
    adr.mkdir()
    releasing.mkdir()

    bad = ref / "bad.md"
    bad.write_text("This mentions (ADR-12) bare.\n")
    good = ref / "good.md"
    good.write_text("This links [ADR-12](../adr/12-no-frontend-linter.md).\n")
    historical = adr / "12-no-frontend-linter.md"
    historical.write_text("Historical prose can say (ADR-12).\n")
    internal = releasing / "plan.md"
    internal.write_text("Release scratch can say (ADR-12).\n")

    bad_errs: list[str] = []
    good_errs: list[str] = []
    historical_errs: list[str] = []
    internal_errs: list[str] = []
    check_bare_adr_codes(bad, root, bad_errs)
    check_bare_adr_codes(good, root, good_errs)
    check_bare_adr_codes(historical, root, historical_errs)
    check_bare_adr_codes(internal, root, internal_errs)

    assert len(bad_errs) == 1
    assert good_errs == []
    assert historical_errs == []
    assert internal_errs == []


def test_check_bare_adr_codes_treats_site_excluded_subroots_as_internal(tmp_path):
    root = tmp_path / "docs" / "releasing" / "0.1.0-alpha.6"
    root.mkdir(parents=True)
    plan = root / "plan.md"
    plan.write_text("Release prose can say (ADR-80) when scanned as a subroot.\n")

    errs: list[str] = []
    check_bare_adr_codes(plan, root, errs)

    assert errs == []


def test_heading_slugs_collects_markdown_headings_and_html_ids(tmp_path):
    md = tmp_path / "h.md"
    md.write_text('# Top Level\n## Sub Heading\n<a id="custom-anchor"></a>\n')

    slugs = heading_slugs(md)

    assert "top-level" in slugs
    assert "sub-heading" in slugs
    assert "custom-anchor" in slugs


def test_check_vocabulary_reference_mirror_compares_source_terms(tmp_path):
    repo = tmp_path
    (repo / "src" / "system").mkdir(parents=True)
    (repo / "docs" / "reference").mkdir(parents=True)
    (repo / "src" / "system" / "vocabulary.md").write_text(
        "## research_area\n\n- alpha — A\n\n## methodology\n\n- beta — B\n",
        encoding="utf-8",
    )
    (repo / "docs" / "reference" / "vocabulary.md").write_text(
        "### `research_area`\n\n| Term | Definition |\n| --- | --- |\n| `alpha` | A |\n\n"
        "### `methodology`\n\n| Term | Definition |\n| --- | --- |\n| `gamma` | G |\n",
        encoding="utf-8",
    )

    errs: list[str] = []
    check_vocabulary_reference_mirror(repo, errs)

    assert len(errs) == 1
    assert "methodology vocabulary mirror differs" in errs[0]
