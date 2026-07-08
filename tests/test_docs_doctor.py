"""L1 component tests for docs_doctor."""

from scripts.checks import docs_doctor as _m

check_broken_vault_wikilinks = _m.check_broken_vault_wikilinks
check_bare_adr_codes = _m.check_bare_adr_codes
check_doc_refs = _m.check_doc_refs
check_frontmatter = _m.check_frontmatter
check_hidden_compatibility_page = _m.check_hidden_compatibility_page
check_link_text = _m.check_link_text
check_links = _m.check_links
check_readmes = _m.check_readmes
check_reference_readme_index = _m.check_reference_readme_index
check_reference_rosters = _m.check_reference_rosters
check_reference_source_contract = _m.check_reference_source_contract
check_site_excluded_targets = _m.check_site_excluded_targets
check_site_local_links = _m.check_site_local_links
check_site_nav_hierarchy = _m.check_site_nav_hierarchy
check_template_frontmatter = _m.check_template_frontmatter
check_vocabulary_reference_mirror = _m.check_vocabulary_reference_mirror
check_wikilink_aliases = _m.check_wikilink_aliases
check_wikilinks = _m.check_wikilinks
empirical_event_schema_values = _m._empirical_event_schema_values
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


def test_check_doc_refs_accepts_pages_html_urls(tmp_path):
    (tmp_path / "docs" / "reference").mkdir(parents=True)
    (tmp_path / "docs" / "reference" / "memory-substrates.md").write_text(
        "# Memory substrates\n",
        encoding="utf-8",
    )
    source = tmp_path / "source.md"
    source.write_text(
        "[Memory substrates](https://eranroseman.github.io/memoria-vault/reference/memory-substrates.html)\n",
        encoding="utf-8",
    )

    errors: list[str] = []
    check_doc_refs(tmp_path, [str(source)], errors)

    assert errors == []


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
    ref.mkdir(parents=True)
    internal.mkdir()
    (root / "_config.yml").write_text("exclude:\n  - internal/\n", encoding="utf-8")
    (internal / "README.md").write_text("# Internal\n", encoding="utf-8")
    (root / "explanation.md").write_text("# Explanation\n", encoding="utf-8")
    page = ref / "page.md"
    page.write_text("[bad](../internal/README.md)\n[good](../explanation.md)\n")
    _m._SITE_EXCLUDE_CACHE.clear()

    errs: list[str] = []
    check_site_excluded_targets(page, root, errs)

    assert len(errs) == 1
    assert "excluded page" in errs[0]


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


def test_check_bare_adr_codes_blocks_bare_codes_in_published_docs(tmp_path):
    root = tmp_path / "docs"
    ref = root / "reference"
    releasing = root / "releasing"
    ref.mkdir(parents=True)
    releasing.mkdir()

    bad = ref / "bad.md"
    bad.write_text("This mentions (ADR-12) bare.\n")
    good = ref / "good.md"
    good.write_text("This links [the design-history context](../README.md).\n")
    internal = releasing / "plan.md"
    internal.write_text("Release scratch can say (ADR-12).\n")

    bad_errs: list[str] = []
    good_errs: list[str] = []
    internal_errs: list[str] = []
    check_bare_adr_codes(bad, root, bad_errs)
    check_bare_adr_codes(good, root, good_errs)
    check_bare_adr_codes(internal, root, internal_errs)

    assert len(bad_errs) == 1
    assert good_errs == []
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
    seed_system = repo / "src/memoria_vault/product/workspace_seed/system"
    seed_system.mkdir(parents=True)
    (repo / "docs" / "reference").mkdir(parents=True)
    (seed_system / "vocabulary.md").write_text(
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


def test_reference_source_contract_requires_guard_checks_and_generated_markers(tmp_path):
    repo = tmp_path
    ref = repo / "docs" / "reference"
    ref.mkdir(parents=True)
    (ref / "README.md").write_text(
        "| File | What | Source |\n"
        "| --- | --- | --- |\n"
        "| [A](a.md) | A | Manual |\n"
        "| [B](b.md) | B | Guarded mirror |\n"
        "| [C](c.md) | C | Generated |\n",
        encoding="utf-8",
    )
    (ref / "a.md").write_text("# A\n", encoding="utf-8")
    (ref / "b.md").write_text("# B\n", encoding="utf-8")
    (ref / "c.md").write_text("# C\n", encoding="utf-8")
    (ref / "_sources.yml").write_text(
        "pages:\n"
        "  a.md:\n"
        "    status: Manual\n"
        "    owner: docs/reference/a.md\n"
        "  b.md:\n"
        "    status: Guarded mirror\n"
        "    owner: src/b.py\n"
        "  c.md:\n"
        "    status: Generated\n"
        "    owner: scripts/c.py\n",
        encoding="utf-8",
    )

    errs: list[str] = []
    check_reference_source_contract(repo, errs)

    assert any("b.md guarded mirror must name a drift check" in err for err in errs)
    assert any("c.md: source status is Generated" in err for err in errs)


def test_reference_rosters_compare_docs_to_source_rosters(tmp_path):
    repo = tmp_path
    ref = repo / "docs" / "reference"
    ref.mkdir(parents=True)
    (repo / "src" / "memoria_vault" / "engine").mkdir(parents=True)
    (repo / "src" / "memoria_vault" / "runtime").mkdir(parents=True)
    ops = repo / "src" / "memoria_vault" / "product" / "capabilities" / "operations"
    ops.mkdir(parents=True)
    (repo / "src" / "memoria_vault" / "engine" / "api.py").write_text(
        "def read_status(workspace):\n    pass\ndef _helper():\n    pass\n",
        encoding="utf-8",
    )
    (repo / "src" / "memoria_vault" / "runtime" / "http_transport.py").write_text(
        'if path == "/status":\n    pass\n',
        encoding="utf-8",
    )
    (repo / "src" / "memoria_vault" / "runtime" / "mcp_transport.py").write_text(
        '@app.tool(description="Read status.")\ndef status():\n    pass\n',
        encoding="utf-8",
    )
    (repo / "src" / "memoria_vault" / "engine" / "empirical_events.py").write_text(
        "SURFACES = frozenset({'obsidian'})\n"
        "WORKFLOWS = frozenset({'gap'})\n"
        "DECISIONS = frozenset({'accept'})\n"
        "OUTCOMES = frozenset({'queued'})\n"
        "REASON_CODES = frozenset({'useful'})\n"
        "EVENT_REQUIRED_FIELDS = {'disposition.recorded': frozenset({'workflow'})}\n"
        "ALLOWED_FIELDS = frozenset({'event_id', 'workflow'})\n",
        encoding="utf-8",
    )
    (ops / "capture-source.md").write_text(
        "---\noperation_id: capture-source\n---\n# Operation\n",
        encoding="utf-8",
    )
    for name in (
        "system-actions.md",
        "prompt-operations.md",
        "read-api.md",
        "local-http-transport.md",
        "mcp-transport.md",
        "empirical-events.md",
    ):
        (ref / name).write_text("# Empty\n", encoding="utf-8")

    errs: list[str] = []
    check_reference_rosters(repo, errs)

    assert any("operation manifest roster omits: capture-source" in err for err in errs)
    assert any("engine API roster omits: read_status" in err for err in errs)
    assert any("HTTP endpoint roster omits: /status" in err for err in errs)
    assert any("MCP tool roster omits: status" in err for err in errs)
    assert any(
        "empirical event schema roster omits: accept, disposition.recorded" in err for err in errs
    )


def test_empirical_event_schema_roster_extracts_starred_required_fields(tmp_path):
    source = tmp_path / "empirical_events.py"
    source.write_text(
        "BASE_REQUIRED_FIELDS = frozenset({'event_id', 'event_type', 'timestamp'})\n"
        "EVENT_REQUIRED_FIELDS = {'session.started': frozenset({'workflow'})}\n"
        "ALLOWED_FIELDS = frozenset({*BASE_REQUIRED_FIELDS, 'workflow'})\n",
        encoding="utf-8",
    )

    values = empirical_event_schema_values(source)

    assert {"event_id", "event_type", "timestamp", "session.started", "workflow"} <= values
