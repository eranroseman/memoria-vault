# ADR enforcement audit — "enforcement is a mechanism, not a label"

Audit date: 2026-06-21. Read-only. Audited against the AGENTS.md working principle:
*"A boundary is real only where code stops the disallowed path … An ADR may describe a boundary, but it must name the enforcing mechanism and a check that proves it; the doc asserting a guarantee is never the thing that holds it."*

Source of truth for runtime behaviour (verified on-box, not from release notes):
- Hermes v0.14.0 at `~/.hermes/hermes-agent`. `tools/registry.py:390 dispatch()` runs any registered tool by name with **no enablement check**; `model_tools.py:370` `disabled_toolsets` is schema-subtraction only (hides a tool from the model, does not remove it from the runtime).
- Real Memoria write gate: the `memoria-policy-gate` Hermes **plugin** (`src/.memoria/plugins/memoria-policy-gate/__init__.py`), which calls `policy_hook.evaluate_pre` (`src/.memoria/mcp/policy_hook.py`) → `policy_mcp.PolicyEngine` → the pure decision core `memoria/runtime/policy/decision.py`.
- Decision core: **default-deny on write** (`decision.py:142` — "no allow rule matches" → deny), per-lane path globs from `src/.memoria/lane-overrides/*.yaml`, review-gated prefixes (`paths.py:9` = `notes/claims/`, `notes/hubs/`, schema-extendable) degraded to `dry_run`/block (`decision.py:146`), hard-deny of `file`/`terminal`/`code_execution` and obsidian `command_execute`/`vault_delete`/`vault_move` (`policy_hook.py:88,107`), fail-closed plugin (`__init__.py:54`).
- Lane globs confirmed: Co-PI `write: []` + `deny.write: ["**"]`; Writer `allow.write: projects/**`, `deny.write: notes/claims/**, notes/hubs/**, catalog/**, inbox/**, system/**`.

Severity legend:
- **THEATER** — the ADR asserts a guarantee that does NOT actually hold on the installed version (no code stops the disallowed path).
- **MIS-ATTRIBUTED** — the guarantee DOES hold on-box, but the ADR credits the wrong thing (a classification/config/naming/"the architecture") instead of the real mechanism (the 28/23 pattern).
- **CORRECT** — guarantee holds and the ADR names the real mechanism + a check.
- **N/A** — no boundary/guarantee claim.
- **DEFERRED** — accepted/proposed but unimplemented; guarantee is a design intent, not yet code. Not theater (nothing ships claiming it holds), but flagged so it is not mistaken for an enforced boundary.

---

## Ranked findings (boundary-claiming ADRs)

### Tier 1 — guarantee does NOT hold on-box, or is credited to a non-mechanism that an agent merely sees

| ADR | Claimed boundary | Attributes enforcement to | Real mechanism + test on-box? | Severity | One-line fix |
|---|---|---|---|---|---|
| **04 – Folders encode lifecycle** | "Agent permissions align with stages (`Librarian` writes to `20-sources/`, never to `30-synthesis/`)." | "the folder structure itself" + "agent permissions align with stages" | **PARTIAL.** The boundary holds, but NOT because of the folder tree — folders are inert. It holds because the lane-override globs deny those paths and the gate default-denies. The ADR credits the taxonomy (the 23 defect) and never names the gate. | **MIS-ATTRIBUTED** | Add a note: alignment is enforced by the lane-override `allow.write`/`deny.write` globs in the policy gate (`decision.py:140-145`), not by folder naming. |
| **46 – Seven-layer architecture** | "MCP is a policy gate, not an execution sandbox: agents reach engines and the Vault only through it." "The strict each-layer-depends-only-on-the-one-below contract binds the agent write-path." | "the architecture" / layer-dependency contract | **PARTIAL.** "Only through MCP" holds, but the dependency *contract* is a diagram, not enforced. It holds because no profile ships `file`/`terminal`/`code_execution` AND `policy_hook` hard-denies them at dispatch + default-denies unknown tools. The ADR attributes the boundary to the layering itself. | **MIS-ATTRIBUTED** | Point the "only through MCP" claim at `policy_hook.DENY_DIRECT_TOOLS` + default-deny (ADR-28's corrected mechanism), not the layer contract. |
| **60 – Cross-vault knowledge sharing** | "MCP-mediated read access to a second Memoria vault, strictly read-only — no writes, no card creation — with the policy MCP enforcing the boundary." | "the policy MCP enforcing the boundary" | **NO.** No cross-vault read-only mechanism exists on-box (no foreign-vault path scope in the decision core; the gate governs the single local vault root, `policy_hook.vault_root()`). The named enforcer does not yet implement the named boundary. | **DEFERRED (theater-risk if read as live)** | Mark explicitly "not yet implemented"; when built, the read-only boundary needs a real foreign-vault scope in the policy engine + a deny-write test, or it is theater. |
| **22 – Build on Hermes** | "Hermes moves work; Memoria decides what work means and what may become canonical." (worker/knowledge boundary) | "the governing rule of thumb" / "extension point" design; "the policy MCP that gates writes" (in passing) | **PARTIAL.** The canonical-write boundary holds via the gate's review-gated-prefix → dry_run path, but the ADR frames it as a design rule-of-thumb and only glances at the gate. | **MIS-ATTRIBUTED (mild)** | Name the review-gated-prefix degradation (`decision.py:146`, `paths.py:9`) as the thing that actually stops canonicalization. |

### Tier 2 — guarantee holds, but the ADR mis-describes *why* (the canonical 28/23 pattern; both already corrected — listed for the family, not re-reported)

| ADR | Claimed boundary | Attributes enforcement to | Real mechanism on-box | Severity | Note |
|---|---|---|---|---|---|
| **28 – Write gate as plugin** | single gated path is sufficient; fail-closed | (original) `agent.disabled_toolsets` | plugin's own hard-deny + default-deny (`policy_hook.py`) | **ALREADY CORRECTED** (2026-06-21 note) | Template; excluded from new findings. |
| **23 – Scoped memory substrates** | cross-lane isolation | the scope×lifespan taxonomy | per-profile dirs + every profile denying `session_search`/`moa`/`delegation` + kanban card as sole channel; durable-write via per-lane path globs | **ALREADY CORRECTED** (2026-06-21 note) | Template; excluded from new findings. |
| **02 – Seven specialist profiles** | "permission enforcement is practical … a specialist profile's write scope is narrow and checkable by the policy MCP" | "the policy MCP" (correctly), via narrow lane scope | Holds: lane-override globs + default-deny. Names the right enforcer. | **CORRECT-ish** (superseded by 48) | Already credits the policy MCP. Fine. |

### Tier 3 — guarantee holds AND the ADR names the real mechanism + a check (correct)

| ADR | Claimed boundary | Mechanism named (verified on-box) | Severity |
|---|---|---|---|
| **03 – Structural review gate** | review-gated write degraded to `dry_run`, "does not reach disk … only path to canonical is human approval" | policy MCP at write time → `decision.py:146` returns `dry_run` for `is_review_gated(path)`; prefixes in `paths.py:9` + schema. **Caveat:** enforcement is on the *write*, not on card column-advance — see note below. | CORRECT (with caveat) |
| **21 – L3 autonomy ceiling** | agents "never canonize"; scheduled ops write `10-inbox/` only; enforced "structurally, through the policy MCP, not prompt" | Holds via review-gated prefixes + lane globs; corrected note already retires the Coder exception. | CORRECT |
| **27 – Hermes native config / gate** | obsidian is the only write path | Holds; ADR already carries the 2026-06-02 partial-supersession note pointing the *mechanism* at ADR-28's plugin. | CORRECT |
| **31 – Native obsidian MCP** | native writes gated with no matcher change; hard-deny `command_execute`/`vault_delete`/`vault_move` | `policy_hook.WRITE_KEYWORDS` substring match + `DENY_OBSIDIAN` (`policy_hook.py:107`); test-pinned. | CORRECT |
| **32 – External access over MCP** | no profile ships `terminal`/`file`/`code_execution`, "fail-closed by the policy plugin's denylist" | `policy_hook.DENY_DIRECT_TOOLS` (`:88`) + default-deny; matches ADR-28's real mechanism. | CORRECT |
| **33 – Cluster MCP** | Mapper "fully sandboxed", no arbitrary exec/network | disabled toolsets backed by the same plugin hard-deny; typed cluster MCP tools only. | CORRECT (relies on 28/32 enforcement) |
| **41 – Configurable review-gate mode** | blocking mode refuses to advance a card without `review_status: approved` | `REVIEW_MODE`/`review_mode` field + audit stamping (`audit.py:14,28`). **Caveat:** the *write* gate is the hard stop; card-advance refusal is board-dispatch logic — see note. | CORRECT (with caveat) |
| **49 – Catalog/Bases linter as commit gate** | pre-commit `schema-check` gates git-tracked writes; "monitor for live edits (detects, does not block)" | Honest about scope: pre-commit hook blocks at commit; cron/CI only monitors. Names mechanism + the detect-vs-block boundary. | CORRECT |
| **53 – Pattern library** | "a pattern never writes a gated zone (output to staging, else dry-run and lint fails)" | single runner chokepoint + output-target validation + the gate's dry_run for gated zones. | CORRECT |
| **55 – Golden copy / template protection** | "agents cannot overwrite `system/templates/` because every lane denies `system/**` … enforced by the write gate; human overwrite detected as golden-copy drift" | Verified: Writer lane `deny.write: system/**`, Co-PI `deny **`; default-deny; `golden_restore.py` SHA manifest. Test-pinned (`tests/test_policy_mcp.py`, `tests/test_golden_restore.py`). | CORRECT (gold standard — names mechanism AND test) |
| **56 – Extraction-uncertainty flag** | below a confidence floor, never merge silently → Inbox flag | confidence floor in `.memoria/schemas/calibration.yaml`; routing, not a hard block (honestly stated). | CORRECT |
| **63 – Multi-machine: one dispatcher per vault** | "exactly one Hermes dispatcher per vault, enforced by isolation" | `HERMES_HOME` + separate vault path; an operational/config invariant, honestly described as such. | CORRECT (operational, not code-stopped — see note) |
| **71 – Structured capture** | "the deterministic Linter remains the single enforcement authority; unknown values rejected, not coerced" | Linter validates against per-type schema in `.memoria/schemas/`; form is prevention-at-entry, Linter is the authority. Names mechanism + defense-in-depth. | CORRECT |
| **74 – Pinned plugin supply chain** | checksum proves the reviewed artifact is present (explicitly NOT trust) | `plugin-provenance-lock.json` + `plugin_provenance_doctor.py` in required lint/L0; honestly scopes what the checksum does and does not prove. | CORRECT (exemplary honesty about the limit of the guarantee) |
| **76 – Reconciling installer / policy core** | "if the host cannot import the installed core, the gate fails closed" | stdlib-only policy core imported by MCP servers; fail-closed on import error (matches `policy_hook.py:238` + plugin `__init__.py:54`). | CORRECT |
| **80 – Containerized test-env** | harness MUST include a negative deny-assertion: a known-deny write through the live ADR-28 plugin is blocked with a deny audit row | This IS the check the principle demands — a test that proves the gate fires. Shipped Phase 1 (#582). | CORRECT (this is the proof-of-boundary other ADRs should cite) |
| **84 – Read-only inspector** | "reads … adds no write path" | UI pane reads dashboards/logs; no write tool wired. | CORRECT |
| **104 – Telemetry three planes** | audit plane append-only + per-write SHA-256; tamper-evidence is Git, not in-file crypto; diagnostic plane never captures agent cognition | append-only via `append_jsonl` + hash pairing; Git as the Merkle substrate; diagnostic scope is Memoria's own MCP/Operations. Detective not preventive — honestly stated, amends ADR-25 without changing its semantics. | CORRECT (detective integrity, correctly framed) |
| **105 – Content-light diagnostic plane** | deny-by-default for raw payloads; out of vault/Git; "nothing sent anywhere automatically"; redaction self-test | location outside vault + `.gitignore` backstop + ephemeral self-disarming capture + redaction golden-corpus self-test (names a check). | CORRECT |
| **25 – Two session logs** | append-only + hash-paired ⇒ tamper *detectable* (explicitly "detective, not preventive") | `audit-unpaired-writes` + `vault-hash-drift` Linter detectors. Honestly scopes the guarantee as detection. | CORRECT |
| **30 – Deterministic ingest** | "every write gated and audited; nothing captured is ever lost" | gate + append-only `capture-intake.jsonl` + log-reconciliation + board-serialized re-ingest. | CORRECT |
| **77 – Project gate** | "PI is the only actor who can promote the thesis to `current`" | thesis→`current` is a review-gated write (`notes/` review-gated prefix path); deterministic Operations compute, PI promotes. | CORRECT (rides ADR-03 enforcement) |
| **78 – Thesis note type** | "transition to `current` is review-gated"; schema rejects born-`current` | review-gated prefix + schema validation by the Linter. | CORRECT |
| **97 – Writer-proposed claim notes** | "the policy MCP continues to deny agent writes to `notes/claims/`" | Verified: `notes/claims/` is a review-gated prefix (`paths.py:9`) AND in Writer `deny.write`. Names the right enforcer + path. | CORRECT |
| **96 – Code-lane keep/revert** | "human promotion remains required"; lane-bounded write-scope | lane write-scope confines outputs; promotion is a gated write. (Proposed — mechanism is the existing gate.) | CORRECT-by-design |
| **95 – Nightly discovery loop** | "keeps human confirmation gates intact"; "policy MCP continues to deny agent writes" | rides the existing gate; proposed. | CORRECT-by-design |
| **107 – OKF bundle** | "nothing from a foreign bundle reaches a canonical surface ungated" | imports enter as candidates subject to the write/link gates (ADR-28). | CORRECT-by-design |
| **48 / 72 / 83 / 01 – Co-PI read-only / "every write is a card" / direct relate** | Co-PI has zero write paths; relate control is "a convenience writer, not a new source of truth" | Verified: `copi.yaml` `write: []` + `deny.write: ["**"]` → default-deny stops every Co-PI write at the gate. The strongest, cleanest on-box boundary in the set. | CORRECT |

### Notable caveat threaded through 03 / 41 / 77 / 78 (the review gate)

The review gate's guarantee holds **at the write boundary**: a write into a review-gated prefix (`notes/claims/`, `notes/hubs/`, schema-extendable) is degraded to `dry_run`/block by the policy gate (`decision.py:146`). That is a real, code-stopped boundary, correctly described.

What is NOT a code-stopped boundary on-box is **card column-advance**: I found no dispatch/Operations code that refuses to move a card out of `done`/awaiting-review without `review_status: approved`. ADR-41 phrases blocking mode as "dispatch refuses to advance a card … without human approval." The *write* into canonical zones is gated regardless of card state (so the guarantee that matters — nothing canonical lands unapproved — holds via the write gate), but the literal "dispatch refuses to advance the card" sentence is board/process discipline, not a verified code stop. Worth a one-line note in 41 so the enforced part (the write) is not conflated with the unenforced part (the column move).

---

## N/A — no boundary/guarantee claim (batched)

These ADRs make process, vocabulary, schema-shape, packaging, ranking, or capability-addition decisions with no security/isolation/integrity/gating guarantee to enforce:

05*, 06*, 07, 08, 09, 10*, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 24*, 26, 29, 34, 35, 36, 37, 38, 39, 40, 42, 43, 44, 45, 47, 50, 51, 52, 54, 57, 58, 59, 61, 62, 64, 65, 66, 67, 68, 69, 70, 73, 75, 79, 81, 82, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 98, 99, 100, 101, 102, 103, 106, 108, 109, 110.

\* Soft/source-of-truth claims worth a glance but not boundary-enforcement defects:
- **05 / 06** — citekey/wikilink stability rests on a *human pinning discipline* ("non-negotiable"), explicitly a practice, not a mechanism. Honest, not a defect.
- **10 / 98 / 103 / 109 / 85 / 102** — "single source of truth" / "documentary, validated not inferred" / "source-as-truth" claims, enforced (where enforced at all) by schema + Linter validation, which they generally name. 98 is the weakest: "remain documentary and validated … not inferred truth" with no named enforcer — borderline, but it is a *proposed* ADR and the claim is about author-intent vocabulary, so low blast radius.
- **24** — single-researcher *scope* boundary; a design-assumption boundary, not a runtime one. Correctly framed.
- **39 / 51 / 54** — acceptance checklists / honesty card / classify automation are explicitly "not machine-checkable" / "a prompt for the human", so they make no false enforcement claim.

---

## Method + coverage

- **Total ADR files in `docs/adr/`:** 112, of which **110 are ADRs** (excluding `README.md` and `_template.md`).
- **Read in full:** all 110 (split across four parallel passes, 01-30 / 31-60 / 61-90 / 91-110; no sampling, per AGENTS.md full-coverage rule). On-box source verified directly by the auditor.
- **Made a boundary/guarantee claim:** ~38 ADRs (the tables above). The remaining ~72 are N/A.
- **New defects (excluding the already-corrected 28/23 templates):**
  - **Mis-attributed (holds, wrong "why"):** 04, 46, 22 — credit folders / the layer-contract / a rule-of-thumb instead of the lane globs + plugin hard-deny + default-deny.
  - **Deferred/theater-risk if read as live:** 60 (cross-vault read-only has no on-box enforcer yet).
  - **Phrasing caveat:** 41 (and by extension 03/77/78) conflates the enforced write-gate with an unenforced card-column-advance.
- **Verified-correct exemplars** other ADRs should cite for the "+ a check" half of the principle: **55** (test-pinned deny + golden-restore), **74** (provenance doctor in required lint, honest about the limit), **80** (live negative deny-assertion that proves the gate fires), **105** (redaction golden-corpus self-test).

No ADR was edited. This is a read-only audit; the only file written is this report.
