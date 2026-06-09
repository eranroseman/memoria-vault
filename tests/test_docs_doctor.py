"""L1 component test for docs-doctor — extracted from its former --self-test (ADR-44)."""
from _util import load_script
_m = load_script("scripts/docs-doctor.py")
globals().update({k: getattr(_m, k) for k in dir(_m) if not k.startswith("__")})


def test_docs_doctor():
    def _run():
        """Synthetic-fixture unit tests for every check function."""
        import tempfile

        failures = 0

        def check(name, ok):
            nonlocal failures
            if not ok:
                failures += 1
            print(f"  {'PASS' if ok else 'FAIL'}  {name}")

        # --- gh_slug ---
        check("gh_slug: basic heading",
              gh_slug("Install requirements") == "install-requirements")
        check("gh_slug: strips backticks",
              gh_slug("`code` in heading") == "code-in-heading")
        check("gh_slug: strips link syntax",
              gh_slug("[text](url) heading") == "text-heading")
        check("gh_slug: removes punctuation",
              gh_slug("What's new?") == "whats-new")

        # --- check_readmes ---
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # root missing README -> error
            (root / "sub").mkdir()
            (root / "sub" / "a.md").write_text("# A\n")
            (root / "sub" / "b.md").write_text("# B\n")
            errs: list[str] = []
            check_readmes(root, errs)
            check("check_readmes: missing root README flagged",
                  any("missing README.md" in e for e in errs))
            check("check_readmes: missing sub README flagged (multi-file dir)",
                  any("sub/" in e and "missing README.md" in e for e in errs))

            # single-file folder needs no README
            (root / "single").mkdir()
            (root / "single" / "only.md").write_text("# Only\n")
            errs2: list[str] = []
            (root / "README.md").write_text("# Root\n")
            check_readmes(root, errs2)
            check("check_readmes: single-file folder not flagged",
                  not any("single/" in e for e in errs2))

        # --- check_frontmatter ---
        with tempfile.TemporaryDirectory() as td:
            # disallowed key
            bad = Path(td) / "bad.md"
            bad.write_text("---\nmode: reference\ntitle: X\n---\n# X\n")
            errs = []
            check_frontmatter(bad, errs)
            check("check_frontmatter: disallowed 'mode:' flagged", len(errs) == 1)

            # unquoted colon in value
            bad2 = Path(td) / "bad2.md"
            bad2.write_text("---\ntitle: Linter: detectors\n---\n# X\n")
            errs2 = []
            check_frontmatter(bad2, errs2)
            check("check_frontmatter: unquoted colon in value flagged", len(errs2) == 1)

            # clean frontmatter
            good = Path(td) / "good.md"
            good.write_text("---\ntitle: \"Clean: title\"\nstatus: draft\n---\n# X\n")
            errs3: list[str] = []
            check_frontmatter(good, errs3)
            check("check_frontmatter: clean file passes", len(errs3) == 0)

            # no frontmatter at all -> no error
            nofm = Path(td) / "nofm.md"
            nofm.write_text("# Just a heading\n")
            errs4: list[str] = []
            check_frontmatter(nofm, errs4)
            check("check_frontmatter: no frontmatter -> no error", len(errs4) == 0)

        # --- check_links ---
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "target.md").write_text("# Real heading\n## Sub section\n")
            # good link
            good = root / "good.md"
            good.write_text("[link](target.md)\n[anchor](target.md#sub-section)\n")
            errs = []
            check_links(good, errs)
            check("check_links: valid relative link + anchor pass", len(errs) == 0)

            # broken link
            bad = root / "bad.md"
            bad.write_text("[link](nonexistent.md)\n")
            errs2 = []
            check_links(bad, errs2)
            check("check_links: broken relative link flagged", len(errs2) == 1)

            # broken anchor
            bad2 = root / "bad2.md"
            bad2.write_text("[link](target.md#no-such-anchor)\n")
            errs3 = []
            check_links(bad2, errs3)
            check("check_links: broken anchor flagged", len(errs3) == 1)

            # link inside fenced code block -> ignored
            code = root / "code.md"
            code.write_text("```\n[link](nonexistent.md)\n```\n")
            errs4: list[str] = []
            check_links(code, errs4)
            check("check_links: link in fenced code ignored", len(errs4) == 0)

            # same-file anchor
            self_anchor = root / "self.md"
            self_anchor.write_text("# Top\n## Details\n[jump](#details)\n[bad](#nope)\n")
            errs5: list[str] = []
            check_links(self_anchor, errs5)
            check("check_links: same-file anchor valid passes, broken flagged", len(errs5) == 1)

        # --- check_wikilinks ---
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # a wikilink that resolves to a known doc -> error
            md = root / "test.md"
            md.write_text("See [[policy-mcp]] for details.\n")
            doc_names = {"policy-mcp.md", "readme.md"}
            errs = []
            check_wikilinks(md, errs, doc_names)
            check("check_wikilinks: resolving wikilink flagged", len(errs) == 1)

            # wikilink that does NOT resolve to any doc -> allowed (vault syntax)
            md2 = root / "test2.md"
            md2.write_text("See [[someCitekey]] here.\n")
            errs2 = []
            check_wikilinks(md2, errs2, doc_names)
            check("check_wikilinks: non-resolving wikilink allowed", len(errs2) == 0)

            # wikilink inside inline code -> ignored
            md3 = root / "test3.md"
            md3.write_text("Use `[[policy-mcp]]` syntax.\n")
            errs3: list[str] = []
            check_wikilinks(md3, errs3, doc_names)
            check("check_wikilinks: wikilink in inline code ignored", len(errs3) == 0)

        # --- check_link_text ---
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # link text that IS the filename -> error
            md = root / "test.md"
            md.write_text("[policy-mcp.md](policy-mcp.md)\n")
            errs = []
            check_link_text(md, errs)
            check("check_link_text: filename as link text flagged", len(errs) == 1)

            # link text that IS the stem -> error
            md2 = root / "test2.md"
            md2.write_text("[policy-mcp](policy-mcp.md)\n")
            errs2 = []
            check_link_text(md2, errs2)
            check("check_link_text: stem as link text flagged", len(errs2) == 1)

            # proper link text -> no error
            md3 = root / "test3.md"
            md3.write_text("[Policy MCP reference](policy-mcp.md)\n")
            errs3: list[str] = []
            check_link_text(md3, errs3)
            check("check_link_text: proper title text passes", len(errs3) == 0)

            # external link -> not checked
            md4 = root / "test4.md"
            md4.write_text("[policy-mcp](https://example.com/policy-mcp.md)\n")
            errs4: list[str] = []
            check_link_text(md4, errs4)
            check("check_link_text: external link not checked", len(errs4) == 0)

        # --- check_wikilink_aliases ---
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # bare wikilink -> error
            md = root / "test.md"
            md.write_text("See [[some-note]] for info.\n")
            errs = []
            check_wikilink_aliases(md, errs)
            check("check_wikilink_aliases: bare wikilink flagged", len(errs) == 1)

            # aliased wikilink -> ok
            md2 = root / "test2.md"
            md2.write_text("See [[some-note|Some Note]] for info.\n")
            errs2 = []
            check_wikilink_aliases(md2, errs2)
            check("check_wikilink_aliases: aliased wikilink passes", len(errs2) == 0)

            # anchor-only wikilink with no target -> not flagged (empty target after split)
            md3 = root / "test3.md"
            md3.write_text("See [[#heading]] here.\n")
            errs3: list[str] = []
            check_wikilink_aliases(md3, errs3)
            check("check_wikilink_aliases: anchor-only wikilink passes", len(errs3) == 0)

        # --- check_broken_vault_wikilinks ---
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            stems = {"real-note", "good"}
            # aliased link to a MISSING note -> error (the gap check_wikilink_aliases misses)
            md = root / "test.md"
            md.write_text("See [[ghost-note|A Title]] here.\n")
            errs = []
            check_broken_vault_wikilinks(md, errs, stems)
            check("check_broken_vault_wikilinks: aliased link to missing note flagged", len(errs) == 1)

            # aliased link to an EXISTING note -> ok
            md2 = root / "test2.md"
            md2.write_text("See [[real-note|A Title]] here.\n")
            errs2 = []
            check_broken_vault_wikilinks(md2, errs2, stems)
            check("check_broken_vault_wikilinks: aliased link to existing note passes", len(errs2) == 0)

            # bare link to existing note (with #anchor) -> ok
            md3 = root / "test3.md"
            md3.write_text("See [[good#section]] here.\n")
            errs3: list[str] = []
            check_broken_vault_wikilinks(md3, errs3, stems)
            check("check_broken_vault_wikilinks: link with anchor to existing note passes", len(errs3) == 0)

            # asset path -> not a note, ignored
            md4 = root / "test4.md"
            md4.write_text("![[90-assets/img.png]]\n")
            errs4: list[str] = []
            check_broken_vault_wikilinks(md4, errs4, stems)
            check("check_broken_vault_wikilinks: asset path ignored", len(errs4) == 0)

            # wikilink inside inline code -> ignored
            md5 = root / "test5.md"
            md5.write_text("Use `[[ghost-note]]` syntax.\n")
            errs5: list[str] = []
            check_broken_vault_wikilinks(md5, errs5, stems)
            check("check_broken_vault_wikilinks: wikilink in inline code ignored", len(errs5) == 0)

        # --- check_template_frontmatter ---
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # disallowed key inside yaml fence
            md = root / "tmpl.md"
            md.write_text("# Template\n\n```yaml\ntitle: X\nmode: reference\n```\n")
            errs = []
            check_template_frontmatter(md, errs)
            check("check_template_frontmatter: disallowed key in fence flagged", len(errs) == 1)

            # clean template
            md2 = root / "tmpl2.md"
            md2.write_text("# Template\n\n```yaml\ntitle: X\nstatus: draft\n```\n")
            errs2 = []
            check_template_frontmatter(md2, errs2)
            check("check_template_frontmatter: clean fence passes", len(errs2) == 0)

        # --- check_thin_folders (advisory) ---
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "README.md").write_text("# Root\n")
            (root / "thin").mkdir()
            (root / "thin" / "only.md").write_text("# Only\n")
            warns: list[str] = []
            check_thin_folders(root, warns)
            check("check_thin_folders: single-file folder flagged as advisory",
                  any("thin/" in w for w in warns))

        # --- heading_slugs ---
        with tempfile.TemporaryDirectory() as td:
            md = Path(td) / "h.md"
            md.write_text("# Top Level\n## Sub Heading\n<a id=\"custom-anchor\"></a>\n")
            slugs = heading_slugs(md)
            check("heading_slugs: top-level heading",
                  "top-level" in slugs)
            check("heading_slugs: sub heading",
                  "sub-heading" in slugs)
            check("heading_slugs: HTML id attribute",
                  "custom-anchor" in slugs)

        print(f"\n{'FAILED' if failures else 'OK'}: {failures} failing check(s) — docs-doctor self-test")
        return failures
    assert _run() == 0
