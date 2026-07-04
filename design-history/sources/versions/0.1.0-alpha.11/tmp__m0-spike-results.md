# Alpha.11 M0 spike results

Date: 2026-06-28

Fixture: `/tmp/memoria-alpha11-m0-spike-fixture`

Verdict: **GO only for narrow scaffolding; live spikes still required**.

| Check | Status | Evidence | Next verification |
| --- | --- | --- | --- |
| 1. Storage shape / OKF round-trip | partial-pass | required_missing=[]; ids_match=True; refs_ok=True; knowledge_export_md=7. No external OKF validator was available, so this is structure-only. | Run the same fixture through a real OKF validator/importer before ADR acceptance. |
| 2. Schema reset | pass | schema_problems=[]; source_id_stable_after_citekey_change=True; refs_still_resolve=True. | Convert this fixture shape into JSON Schema tests for the alpha.11 type map. |
| 3. Integrity spine feasibility | pass | before_visible=['knowledge/digest-alpha', 'knowledge/hub-drift', 'knowledge/note-alpha', 'knowledge/note-quote', 'knowledge/project-alpha']; staging_hidden=True; good_promoted=True; poison_quarantined=True; poison_hidden=True; rollback={'rolled_back': ['knowledge/digest-beta', 'knowledge/note-machine-beta'], 'flagged': ['knowledge/note-human-beta']}. | Replace this in-memory/file simulation with production trusted-writer and git tests. |
| 4. Wiki engine adopt-vs-build | partial-pass | skill_exists=True; docs_exist=True; docs_mentions_5_15=True; script_syntax=[('build.sh', True), ('bootstrap.sh', True)]. No live compile/model quality run was attempted. | Run one real `llm-wiki` compile on the fixture source corpus and score output quality. |
| 5. Obsidian plugin feasibility | partial-pass | plugin_exists=True; has_view=True; read_only=True; missing_alpha11_tokens=['rollback', 'Co-PI', 'conversation']. Current plugin proves packaging/static view pattern only, not the alpha.11 Co-PI/rollback surface. | Build a disposable alpha.11 plugin pane and test it in Obsidian on Memoria-test. |
| 6. Seeded-error harness design | pass | expected=['broken_ref', 'stale_as_current', 'unchecked_leak', 'unsupported_marker']; detected=['broken_ref', 'stale_as_current', 'unchecked_leak', 'unsupported_marker']; recall=1.00. This validates harness shape, not semantic/NLI recall. | Add crafted-injection and unwarranted-claim cases once semantic detectors exist. |

## Interpretation

The disposable fixture proves the reset shape is internally coherent enough to
continue planning: nested bundles, the schema reset, the read barrier simulation,
cascade rollback semantics, and seeded-error scoring can be represented with plain
files. It does **not** prove external OKF conformance, real LLM wiki quality, or the
alpha.11 Obsidian plugin surface. Those remain the shortest live spikes before
production alpha.11 implementation.
