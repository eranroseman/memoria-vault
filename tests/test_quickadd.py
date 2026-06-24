"""The QuickAdd palette config is internally consistent.

Every Macro choice in the shipped quickadd data.json points at a user script
that actually exists under system/scripts/, and every macro a choice embeds
carries an id (Obsidian resolves commands by these ids — a dangling reference
makes the palette entry a silent no-op). The per-task lane scripts (#203)
must also stay in sync with the delegation model: each script's lane/assignee
pair matches LANE_PROFILE in tasks_mcp.py, and each named skill is a real
skill directory under the assignee's profile.
"""

import json
import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
DATA = SRC / ".obsidian" / "plugins" / "quickadd" / "data.json"
SCRIPTS = SRC / "system" / "scripts"
PROFILES = SRC / ".memoria" / "profiles"
TASKS_MCP = SRC / ".memoria" / "mcp" / "tasks_mcp.py"

# The six per-task lane commands (one script per lane task).
LANE_SCRIPTS = [
    "catalog-source.js",
    "extract-claims.js",
    "link-claim.js",
    "map-corpus.js",
    "draft-section.js",
    "verify-draft.js",
]


def _choices():
    return json.loads(DATA.read_text(encoding="utf-8"))["choices"]


def test_command_labels_are_direct_and_article_free():
    expected = {
        "Memoria: archive claim note",
        "Memoria: archive fleeting note",
        "Memoria: capture fleeting",
        "Memoria: capture from Zotero selection",
        "Memoria: capture source from URL",
        "Memoria: load sample vault",
        "Memoria: remove sample vault",
        "Memoria: structured source capture",
        "Memoria: delegate task",
        "Memoria: catalog source",
        "Memoria: extract claims",
        "Memoria: link claim",
        "Memoria: map corpus",
        "Memoria: record exploration trace",
        "Memoria: draft section",
        "Memoria: verify draft",
        "Memoria: run pattern",
        "Memoria: assist find",
        "Memoria: assist search",
        "Memoria: assist patterns",
        "Memoria: assist ask",
        "Memoria: assist draft",
        "Memoria: assist explore",
        "Memoria: resolve inbox card",
        "Memoria: create linked claim note",
        "Memoria: write claim note",
        "Memoria: start project",
        "Memoria: refresh project gate",
        "Memoria: supersede thesis",
    }
    commands = {c["name"] for c in _choices() if c.get("command")}
    assert commands == expected
    for choice in _choices():
        if choice["type"] == "Macro":
            assert choice["macro"]["name"] == choice["name"]
    banned = re.compile(
        r"^Memoria: (?:delegate a task|catalog a source|link a claim|map the corpus|"
        r"draft a section|verify a draft|run a pattern|workspace )"
    )
    assert not any(banned.match(name) for name in commands)


def test_macro_choices_reference_existing_scripts():
    macros = [c for c in _choices() if c["type"] == "Macro"]
    assert macros, "no Macro choices found in quickadd data.json"
    for choice in macros:
        for cmd in choice["macro"]["commands"]:
            if cmd["type"] != "UserScript":
                continue
            script = SRC / cmd["path"]
            assert script.is_file(), f"{choice['name']}: script {cmd['path']} missing under src/"
            assert cmd["path"].startswith("system/scripts/"), (
                f"{choice['name']}: script {cmd['path']} outside system/scripts/"
            )


def test_quickadd_scripts_resolve_shared_helpers_from_vault_root():
    """QuickAdd runs user scripts from plugin context, not system/scripts/.

    A raw sibling import such as require("./quickadd-utils") breaks in Obsidian
    even though it works in a Node-shaped test harness.
    """
    for script in SCRIPTS.glob("*.js"):
        text = script.read_text(encoding="utf-8")
        assert 'require("./quickadd-utils")' not in text, script.name
        assert 'require("./quickadd-similarity")' not in text, script.name
    for script in SCRIPTS.glob("*.js"):
        text = script.read_text(encoding="utf-8")
        if "system/scripts/quickadd-" in text:
            assert "getBasePath" in text, script.name


def test_macro_ids_exist_and_are_unique():
    seen = set()
    for choice in _choices():
        ids = [choice["id"]]
        if choice["type"] == "Macro":
            assert choice["macro"].get("id"), f"{choice['name']}: macro has no id"
            ids.append(choice["macro"]["id"])
            ids += [cmd["id"] for cmd in choice["macro"]["commands"]]
        for i in ids:
            assert i not in seen, f"duplicate QuickAdd id {i}"
            seen.add(i)


def test_startup_macro_restores_saved_memoria_shell():
    choices = {c["name"]: c for c in _choices()}
    choice = choices["Memoria: restore shell on startup"]
    assert choice["type"] == "Macro"
    assert choice["command"] is False
    assert choice["runOnStartup"] is True

    [cmd] = choice["macro"]["commands"]
    assert cmd["path"] == "system/scripts/restore-memoria-shell.js"

    script = (SCRIPTS / "restore-memoria-shell.js").read_text(encoding="utf-8")
    assert 'WORKSPACE_NAME = "Memoria"' in script
    assert 'NAV_FILE = "_nav.md"' in script
    assert "RAIL_SETTLE_MS = 500" in script
    assert "internalPlugins?.plugins?.workspaces?.instance" in script
    assert "loadWorkspace(WORKSPACE_NAME)" in script
    assert "getLeavesOfType" in script
    assert "setTimeout(resolve, RAIL_SETTLE_MS)" in script
    assert "revealLeaf(navLeaf)" in script
    assert script.count("await revealNavRail(app)") == 2


def _lane_profile():
    """Parse LANE_PROFILE out of tasks_mcp.py (regex — no import, no deps)."""
    src = TASKS_MCP.read_text(encoding="utf-8")
    block = re.search(r"LANE_PROFILE\s*=\s*\{(.*?)\}", src, re.S).group(1)
    return dict(re.findall(r'"([\w-]+)":\s*"([\w-]+)"', block))


def _const(script_text, name):
    m = re.search(rf'const {name} = "([^"]+)"', script_text)
    return m.group(1) if m else None


def test_lane_scripts_match_lane_profile_and_skills():
    lane_profile = _lane_profile()
    seen_lanes = set()
    for fname in LANE_SCRIPTS:
        text = (SCRIPTS / fname).read_text(encoding="utf-8")
        lane, assignee, skill = (_const(text, n) for n in ("LANE", "ASSIGNEE", "SKILL"))
        assert lane and assignee and skill, f"{fname}: missing LANE/ASSIGNEE/SKILL const"
        assert lane in lane_profile, f"{fname}: lane '{lane}' not in tasks_mcp LANE_PROFILE"
        assert assignee == lane_profile[lane], (
            f"{fname}: assignee {assignee} != LANE_PROFILE[{lane}] ({lane_profile[lane]})"
        )
        skill_dir = PROFILES / assignee / "skills" / skill
        assert skill_dir.is_dir(), f"{fname}: skill dir {skill_dir} missing"
        seen_lanes.add(lane)
    assert seen_lanes == set(lane_profile) - {"code"}, (
        f"lane scripts cover {sorted(seen_lanes)}, expected every non-code lane"
    )


def test_assist_surface_commands_are_staged_and_skill_backed():
    verbs = {"find", "search", "patterns", "ask", "draft", "explore"}
    choices = {c["name"]: c for c in _choices()}
    for verb in verbs:
        name = f"Memoria: assist {verb}"
        choice = choices[name]
        assert choice["type"] == "Macro"
        [cmd] = choice["macro"]["commands"]
        assert cmd["type"] == "UserScript"
        assert cmd["path"] == "system/scripts/assist.js"
        assert cmd["settings"] == {"Verb": verb}

    script = (SCRIPTS / "assist.js").read_text(encoding="utf-8")
    assert "module.exports = {" in script
    assert "entry," in script
    assert "settings:" in script
    assert "getSelection" in script
    assert "RESULTS_STAGE" in script
    assert "Do not write directly to canonical/current notes" in script
    for marker in (
        "catalog-find-source",
        "map-report-coverage",
        "ask-question-source",
        "explore-framings",
        "draft-write-section",
        "patterns_run",
    ):
        assert marker in script
    for assignee, skill in (
        ("memoria-librarian", "catalog-find-source"),
        ("memoria-librarian", "map-report-coverage"),
        ("memoria-copi", "ask-question-source"),
        ("memoria-copi", "explore-framings"),
        ("memoria-writer", "draft-write-section"),
    ):
        assert (PROFILES / assignee / "skills" / skill).is_dir()


def test_structured_source_capture_is_palette_wired_and_staged():
    choices = {c["name"]: c for c in _choices()}
    choice = choices["Memoria: structured source capture"]
    [cmd] = choice["macro"]["commands"]
    assert cmd["path"] == "system/scripts/structured-source-capture.js"
    script = (SCRIPTS / "structured-source-capture.js").read_text(encoding="utf-8")
    similarity = (SCRIPTS / "quickadd-similarity.js").read_text(encoding="utf-8")
    for marker in (
        "openForm(FORM_NAME)",
        'FORM_NAME = "memoria-source-capture"',
        'SOURCE_FOLDER = "notes/sources/"',
        '"type: source"',
        '"lifecycle: proposed"',
        '"evidence_level: " + yamlString(data.evidence_level || "ungraded")',
        '"type: candidate"',
        '"raised_by: modalforms"',
        '"target: " + yamlString(sourcePath)',
        "preFileSimilarityShadow(app, cp, crypto",
    ):
        assert marker in script
    for marker in (
        "[!similarity]- Pre-file similarity shadow",
        'SIMILARITY_LOG = "system/logs/pre-file-similarity.jsonl"',
        "qmd search --format json --full-path -n 12",
    ):
        assert marker in similarity


def test_fleeting_capture_is_guided_and_queued_for_inbox_triage():
    choices = {c["name"]: c for c in _choices()}
    choice = choices["Memoria: capture fleeting"]
    assert choice["type"] == "Macro"
    [cmd] = choice["macro"]["commands"]
    assert cmd["path"] == "system/scripts/capture-fleeting.js"
    assert "openFile" not in choice

    script = (SCRIPTS / "capture-fleeting.js").read_text(encoding="utf-8")
    for marker in (
        "openForm(FORM_NAME)",
        'FORM_NAME = "memoria-fleeting-capture"',
        'FLEETING_FOLDER = "notes/fleeting/"',
        'TEMPLATE_PATH = "system/templates/fleeting.md"',
        "renderFleetingTemplate(template, title, date, data.body)",
        "Capture text is required.",
        "does not steal focus by opening itself",
    ):
        assert marker in script
    template = (SRC / "system" / "templates" / "fleeting.md").read_text(encoding="utf-8")
    for marker in ("type: fleeting", "lifecycle: proposed", "origin: human"):
        assert marker in template
    assert "openFile" not in script


def test_archive_fleeting_note_is_narrow_and_in_place():
    choices = {c["name"]: c for c in _choices()}
    choice = choices["Memoria: archive fleeting note"]
    assert choice["type"] == "Macro"
    [cmd] = choice["macro"]["commands"]
    assert cmd["path"] == "system/scripts/archive-active-note.js"
    assert cmd["settings"] == {"Type": "fleeting"}

    script = (SCRIPTS / "archive-active-note.js").read_text(encoding="utf-8")
    helper = (SCRIPTS / "quickadd-utils.js").read_text(encoding="utf-8")
    combined = script + helper
    for marker in (
        'folder: "notes/fleeting/"',
        'file.path.endsWith(".md")',
        'type: "fleeting"',
        'fm.lifecycle = "archived"',
        "fm.archived = todayIsoDate()",
        "processFrontMatter",
    ):
        assert marker in combined
    assert "unlink" not in combined
    assert "trash" not in combined
    assert "delete" not in combined


def test_archive_claim_note_is_narrow_and_in_place():
    choices = {c["name"]: c for c in _choices()}
    choice = choices["Memoria: archive claim note"]
    assert choice["type"] == "Macro"
    [cmd] = choice["macro"]["commands"]
    assert cmd["path"] == "system/scripts/archive-active-note.js"
    assert cmd["settings"] == {"Type": "claim"}

    script = (SCRIPTS / "archive-active-note.js").read_text(encoding="utf-8")
    helper = (SCRIPTS / "quickadd-utils.js").read_text(encoding="utf-8")
    combined = script + helper
    for marker in (
        'folder: "notes/claims/"',
        'file.path.endsWith(".md")',
        'type: "claim"',
        'fm.lifecycle = "archived"',
        "fm.archived = todayIsoDate()",
        "processFrontMatter",
    ):
        assert marker in combined
    assert "unlink" not in combined
    assert "trash" not in combined


def test_write_claim_note_uses_guided_form_and_template_renderer():
    choices = {c["name"]: c for c in _choices()}
    choice = choices["Memoria: write claim note"]
    assert choice["type"] == "Macro"
    assert "templatePath" not in choice
    [cmd] = choice["macro"]["commands"]
    assert cmd["path"] == "system/scripts/write-claim.js"

    script = (SCRIPTS / "write-claim.js").read_text(encoding="utf-8")
    for marker in (
        'FORM_NAME = "memoria-claim-capture"',
        'CLAIM_FOLDER = "notes/claims/"',
        'TEMPLATE_PATH = "system/templates/claim.md"',
        "openForm(FORM_NAME)",
        "renderClaimTemplate(template, data, today, similarity)",
        "preFileSimilarityShadow(app, cp, crypto",
        'source: "quickadd.write-claim"',
        'noteType: "claim"',
        '[[catalog/papers/" + source + "|" + source + "]]',
        "appendSimilarityTelemetry(app, similarity)",
        "getLeaf(true).openFile(created)",
    ):
        assert marker in script


def test_zotero_capture_writes_intake_log_where_readers_look():
    """capture-from-zotero.js must append its durability anchor to the same
    capture-intake.jsonl path the readers use (ingest_mcp INTAKE_LOG and the
    reconcile sweep) — a stale path silently drops the anchor (#427)."""
    ingest = (SRC / ".memoria" / "mcp" / "ingest_mcp.py").read_text(encoding="utf-8")
    intake_log = re.search(r'INTAKE_LOG\s*=\s*"([^"]+)"', ingest).group(1)
    script = (SCRIPTS / "capture-from-zotero.js").read_text(encoding="utf-8")
    log = _const(script, "LOG")
    assert log == intake_log, (
        f"capture-from-zotero.js writes {log!r} but ingest_mcp.py reads {intake_log!r}"
    )


def test_zotero_capture_writes_visible_candidate_card_and_resolves_hermes():
    script = (SCRIPTS / "capture-from-zotero.js").read_text(encoding="utf-8")
    assert "writeCandidateCard(params, citekey, title)" in script
    assert "writePaperStub(params, citekey, title)" in script
    assert "chooseCitekey(params, citekeys)" in script
    assert "params.quickAddApi.suggester(options, options)" in script
    assert "capturing the first" not in script
    assert '"inbox/candidate-zotero-" + slug(citekey, "source") + ".md"' in script
    assert '"catalog/papers/" + citekey + ".md"' in script
    for field in (
        "type: candidate",
        "lifecycle: proposed",
        "argument_for:",
        "argument_against:",
        "what_tipped_it:",
        "certainty: unsure",
        "citekey:",
        "raised_by: quickadd",
    ):
        assert field in script
    assert "function hermesCommand()" in script
    assert "command -v hermes" in script
    assert "$HOME/.local/bin" in script
    assert "Hermes not found on PATH" in script


def test_zotero_capture_materializes_schema_valid_tier0_catalog_stub():
    script = (SCRIPTS / "capture-from-zotero.js").read_text(encoding="utf-8")
    start = script.index("async function writePaperStub")
    stub = script[start : script.index("async function ensureFolder", start)]
    for marker in (
        '"type: paper"',
        '"lifecycle: current"',
        '"citekey: " + yamlString(citekey)',
        '"ingest_status: tier0"',
        '"relationships:"',
        '"  cited_by: []"',
        '"  authored_by: []"',
        '"  published_in: \\"\\""',
        "Captured from Zotero with citekey",
        "if (await exists(adapter, path)) return path;",
        'await ensureFolder(adapter, "catalog/papers")',
    ):
        assert marker in stub


def test_exploration_trace_capture_is_project_local_and_not_canonical():
    choices = {c["name"]: c for c in _choices()}
    choice = choices["Memoria: record exploration trace"]
    [cmd] = choice["macro"]["commands"]
    assert cmd["path"] == "system/scripts/record-exploration-trace.js"

    script = (SCRIPTS / "record-exploration-trace.js").read_text(encoding="utf-8")
    for marker in (
        'MAPS_DIR = "notes/fleeting/maps/"',
        '"type: fleeting"',
        '"origin: human"',
        '"# Exploration trace"',
        '"## Rejected direction"',
        '"## Why rejected"',
        '"## Evidence checked"',
        '"## Retry only if"',
        "never promoted automatically into canonical knowledge",
        "isMapReport(reportPath)",
    ):
        assert marker in script
    for forbidden in (
        "notes/claims/",
        "notes/hubs/",
        "projects/",
        "type: claim",
        "type: hub",
    ):
        assert forbidden not in script
    assert "hermes kanban create" not in script


def test_zotero_capture_uses_bbt_json_rpc_not_cayw():
    """Better BibTeX CAYW can invoke the active Zotero citation style.

    The capture command only needs the selected item's citekey, so it should
    use BBT's JSON-RPC citekey lookup instead of a formatter/style path.
    """
    script = (SCRIPTS / "capture-from-zotero.js").read_text(encoding="utf-8")
    assert "better-bibtex/json-rpc" in script
    # cspell:words citationkey
    assert '"method":"item.citationkey"' in script
    assert '"params":["selected"]' in script
    assert "parseSelectedCitekeys(raw)" in script
    assert "citekeysFromResult(first.result)" in script
    assert "collectCitekeys(result, keys)" in script
    assert "citationKey" in script
    assert "better-bibtex/cayw" not in script
    assert "format=biblatex" not in script
    assert "format=json" not in script


def test_url_capture_writes_visible_candidate_card():
    """URL capture must create a visible Inbox candidate, not only a Hermes task.

    The Inbox space's Needs me view is backed by inbox/inbox.base, so a URL
    capture that only creates a board card is invisible in Obsidian until another
    actor runs. Keep the QuickAdd script wired to a schema-shaped candidate card.
    """
    script = (SCRIPTS / "capture-from-url.js").read_text(encoding="utf-8")
    assert "writeCandidateCard(params, url)" in script
    assert '"inbox/" + stem + ".md"' in script
    for field in (
        "type: candidate",
        "lifecycle: proposed",
        "argument_for:",
        "argument_against:",
        "what_tipped_it:",
        "certainty: unsure",
        "raised_by: quickadd",
    ):
        assert field in script


def test_create_linked_claim_writes_schema_shaped_claim_and_source_link():
    script = (SCRIPTS / "create-linked-claim.js").read_text(encoding="utf-8")
    similarity = (SCRIPTS / "quickadd-similarity.js").read_text(encoding="utf-8")
    assert 'source.path.startsWith("notes/sources/")' in script
    assert '"notes/claims/" + slug(claim, "claim") + ".md"' in script
    for field in (
        "type: claim",
        "schema_version: 2",
        "lifecycle: current",
        "maturity: seedling",
        "sources:",
        "topics: []",
        "supports: []",
        "contradicts: []",
    ):
        assert field in script
    assert "appendWorthDistillingLink(sourceText, claimLink)" in script
    assert "app.vault.create(claimPath, frontmatter + body)" in script
    assert "app.vault.modify(source," in script
    assert "app.workspace.getLeaf(true).openFile(created)" in script
    assert "preFileSimilarityShadow(app, cp, crypto" in script
    assert "[!similarity]- Pre-file similarity shadow" in similarity
    assert 'SIMILARITY_LOG = "system/logs/pre-file-similarity.jsonl"' in similarity
    assert "qmd search --format json --full-path -n 12" in similarity
    assert (
        "Report-only qmd neighbour check; no block, auto-merge, or calibrated threshold."
        in similarity
    )
    assert 'event: "pre_file_similarity_shadow"' in similarity
    assert "query_sha256" in similarity and "query_chars" in similarity
    assert 'SIMILARITY_SCOPES = ["notes/claims/", "notes/sources/"]' in similarity


def test_link_claim_writes_suggestions_callout_before_delegating():
    script = (SCRIPTS / "link-claim.js").read_text(encoding="utf-8")
    utils = (SCRIPTS / "quickadd-utils.js").read_text(encoding="utf-8")

    assert "[!suggestions]- Link suggestions" in script
    assert "rankLinkSuggestions(params.app, claim, claimText)" in script
    assert "SUGGESTION_LIMIT = 10" in script
    assert "Forward candidates" in script
    assert "Backward candidates" in script
    assert "score.toFixed(3)" in script
    assert "appendCallout(params.app, claim, buildSuggestionsCallout(suggestions))" in script
    assert "async function appendCallout" in utils
    assert "app.vault.modify(file," in utils
    assert "optional LLM one-line explanations" in script
    assert "queueHermesCard(cp" in script
    assert "hermes kanban create" in utils


def test_link_claim_excludes_superseded_claims_by_default():
    script = (SCRIPTS / "link-claim.js").read_text(encoding="utf-8")
    assert "isSupersededClaim(text)" in script
    assert 'file.path.startsWith("notes/claims/") && isSupersededClaim(text)' in script
    assert "superseded_by" in script


def test_verify_draft_writes_verification_callout_before_delegating():
    script = (SCRIPTS / "verify-draft.js").read_text(encoding="utf-8")
    utils = (SCRIPTS / "quickadd-utils.js").read_text(encoding="utf-8")

    assert "[!verification] Verification trace" in script
    assert "traceDraftMarkers(draftText)" in script
    assert "Claim links found:" in script
    assert "Citekeys found:" in script
    assert "No claim links or citekeys found" in script
    assert "appendCallout(params.app, draft, buildVerificationCallout(trace))" in script
    assert "async function appendCallout" in utils
    assert "app.vault.modify(file," in utils
    assert "The deterministic [!verification] preflight callout has been written" in script
    assert "queueHermesCard(cp" in script
    assert "hermes kanban create" in utils


def test_capture_and_catalog_cards_request_source_note_stub():
    for fname in ("capture-from-url.js", "capture-from-zotero.js", "catalog-source.js"):
        script = (SCRIPTS / fname).read_text(encoding="utf-8")
        assert "proposed source-note stub" in script
        assert "notes/sources/ for the PI to fill" in script


def test_resolve_inbox_card_uses_schema_valid_lifecycles():
    script = (SCRIPTS / "resolve-inbox-card.js").read_text(encoding="utf-8")
    assert '"retracted"' not in script
    assert '"current (accept)": "current"' in script
    assert '"current (edited)": "current"' in script
    assert '"archived (reject)": "archived"' in script
    assert '"archived (done / no action)": "archived"' in script
    assert '"current (edited)": "edited"' in script
    assert 'ATTENTION_LOG = "system/logs/attention.jsonl"' in script
    assert 'TRIAGE_LOG = "system/logs/triage.jsonl"' in script
    assert 'DISPOSITION_LOG = "system/logs/disposition.jsonl"' in script
    assert 'event: "inbox_card_resolved"' in script
    assert 'event: "work_prompt_reviewed"' in script
    assert "duration_minutes: durationMinutes(openedAt, resolvedAt)" in script
    assert "appendJsonl(app, ATTENTION_LOG, attentionRow)" in script
    assert "appendJsonl(app, TRIAGE_LOG, triageRow)" in script
    assert "appendJsonl(app, DISPOSITION_LOG, dispositionRow)" in script


def test_delegate_task_picker_uses_work_labels_not_profile_ids():
    script = (SCRIPTS / "delegate-task.js").read_text(encoding="utf-8")
    assert "const LANE_LABELS" in script
    for label in (
        "Catalog sources",
        "Extract claims",
        "Link claims",
        "Map the corpus",
        "Draft prose",
        "Verify work",
        "Coordinate code handoff",
    ):
        assert label in script
    assert "laneNames.map((l) => LANE_LABELS[l])" in script
    assert 'l + " → " + LANES[l]' not in script


def test_map_corpus_treats_quickadd_empty_backslash_as_whole_corpus():
    script = (SCRIPTS / "map-corpus.js").read_text(encoding="utf-8")
    assert 'if (/^\\\\+$/.test(scope)) scope = "";' in script


def test_map_corpus_idempotency_key_allows_later_retries():
    script = (SCRIPTS / "map-corpus.js").read_text(encoding="utf-8")
    assert "Math.floor(Date.now() / 60000)" in script
    assert '+ "-" + retryWindow' in script


def test_lane_scripts_and_pattern_runner_are_wired_into_the_palette():
    wired = {
        cmd["path"]
        for c in _choices()
        if c["type"] == "Macro"
        for cmd in c["macro"]["commands"]
        if cmd["type"] == "UserScript"
    }
    for fname in [
        *LANE_SCRIPTS,
        "run-pattern.js",
        "delegate-task.js",
        "start-project.js",
        "refresh-project-gate.js",
        "supersede-thesis.js",
    ]:
        assert f"system/scripts/{fname}" in wired, f"{fname} not wired into quickadd data.json"


def test_start_project_scaffolds_project_gate_workspace():
    script = (SCRIPTS / "start-project.js").read_text(encoding="utf-8")
    for marker in (
        'FORM_NAME = "memoria-project-start"',
        'openForm(FORM_NAME, { values: { output_mode: "thesis" } })',
        '"projects/" + data.slug',
        'slug(data.slug || data.title, "project")',
        'root + "/project.md"',
        'root + "/thesis.md"',
        'root + "/project-gate-index.md"',
        '"code"',
        '"drafts"',
        '"exports"',
        '"# " + data.title',
        "Project · ",
        "Readiness details",
        "QuickAdd: Memoria: map corpus",
        "Project title is required.",
        "Provisional thesis is required for thesis-mode projects.",
        'outputMode === "thesis"',
        "data.provisional_thesis",
        '"  interesting: " + yamlString(data.finer_interesting)',
        '"  ethical: " + yamlString(data.finer_ethical)',
        "refutation_sufficiency: false",
        "QuickAdd: Memoria: refresh project gate",
    ):
        assert marker in script
    assert "![[project-gate-index]]" not in script
    assert 'inputPrompt("Provisional thesis' not in script


def test_refresh_project_gate_runs_structural_impact_operation():
    script = (SCRIPTS / "refresh-project-gate.js").read_text(encoding="utf-8")
    assert "structural_impact.py" in script
    assert "--project" in script
    assert "cp.execFile(python, args" in script
    assert ".memoria/.venv/Scripts/python.exe" in script
    assert ".memoria/.venv/bin/python" in script


def test_supersede_thesis_marks_old_and_raises_reconfirm_alert():
    script = (SCRIPTS / "supersede-thesis.js").read_text(encoding="utf-8")
    for marker in (
        "type: thesis",
        "superseded_by",
        "supersedes:",
        "active_thesis",
        "inbox/alert-thesis-pivot-",
        "type: alert",
        "Refresh the Project gate and re-confirm",
        "lifecycle: proposed",
    ):
        assert marker in script


def test_verify_draft_emits_visible_knowledge_gap_cards():
    script = (SCRIPTS / "verify-draft.js").read_text(encoding="utf-8")
    for marker in (
        "detectUngroundedAssertions(draftText)",
        "writeKnowledgeGapCards(params.app, ref, ungrounded)",
        "inbox/gap-draft-",
        "type: gap",
        "gap_type: additive",
        "raised_by: quickadd-verify-draft",
        "knowledge-gap card(s) were staged",
    ):
        assert marker in script
