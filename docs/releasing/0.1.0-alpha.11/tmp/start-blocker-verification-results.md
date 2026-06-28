# Alpha.11 start-blocker verification results

Date: 2026-06-28

Verdict: **PARTIAL**.

| Claim | Status | Evidence |
| --- | --- | --- |
| qmd disposable bundle index/search | pass | fixture=/tmp/memoria-alpha11-start-blockers/qmd-bundle; init/update/search rc=0; found_stability=True |
| Zotero Local API item + annotation shape | partial-live | port_open=True; item_status=200; item_shape=True; annotation_status=200; annotation_list_shape=True; annotation_sample_present=False; errors=none |
| PDF quote/page/span/bbox preservation | fail-prereq | no local PDF extractor/generator found; modules={'fitz': False, 'pymupdf4llm': False, 'pypdf': False, 'pdfplumber': False, 'pdfminer': False, 'reportlab': False}; commands={'pdftotext': False, 'pdfinfo': False, 'mutool': False, 'qpdf': False} |
| Obsidian pane activation | partial-live-rest | enabled=True; static_registers_view_and_command=True; mock_activation=True; localhost_27124_open=True; rest_manifest_read=True; live_gui_activation_tested=False; port_note=open |
| source_id stability across citekey changes | pass | fixture=/tmp/memoria-alpha11-start-blockers/source-id; before_path=catalog/sources/src-alpha11-0001/source.md; after_path=catalog/sources/src-alpha11-0001/source.md; path_stable=True; citekey_changed=True; refs_still_resolve=True |

## Interpretation

- `qmd` and `source_id` are verified with disposable local fixtures.
- Zotero and Obsidian are live-app checks; if their local services are unreachable,
  the result is blocked rather than simulated.
- PDF span preservation is not verified because no local PDF extraction/generation
  toolchain is installed in this environment.
- The Obsidian plugin check proves static registration plus a mocked command/view
  activation path; it still does not prove visual rendering in a real Obsidian
  window.
