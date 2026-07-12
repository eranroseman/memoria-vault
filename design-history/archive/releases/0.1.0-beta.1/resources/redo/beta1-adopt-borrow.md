# beta.1 → what to ADOPT or BORROW

*Memoria alpha.16 redo. Facts-only: every verdict rests on a research finding, a
documented failure, or a verifiable fact — never "beta.1 built it" or an ADR.
Sources: RR = REVIEW-REFUTATIONS.md; ADV/BAR = beta.1 paper adversarial-review /
borrow-adapt-reject; DH = design-history line; GR = alpha15-gap-report §; HIST =
gap-history-analysis. 2026-07-05.*

**Governing fact:** the 401-paper adversarial pass found the research endorses
the *skeleton* and refutes the *strong claims layered on top* (RR L3, L101). So
from beta.1 we adopt its **skeleton implementations and engineering**, not its
clean-slate strong claims. Two beta.1 divergences from the alpha line are
positively **research-vindicated** (below); most of its *removals* are not, and
belong in the alpha.15-borrow list, not here.

## ADOPT — genuine technical improvements + research-vindicated, mission-serving

1. **Verbatim byte-exact span warrant; anchored paragraph as the stored/retrieved unit.** Research SURVIVOR (Omni-SimpleMem +53% F1 from full text over summaries, RR L101). beta.1's "atomic claim = index over the span, not the stored unit" is the *correct* reading of LongMemEval that the alpha line inverted (RR L35, L108). **Vindicated divergence.**
2. **Hybrid BM25+dense retrieval (RRF, MMR); no graph as the retrieval representation.** Research SURVIVOR — MemoryAgentBench put GraphRAG/Cognee/Zep *below* plain BM25 (RR L51, L111). beta.1 reads this correctly.
3. **Single VaultWriter** — one code path writes machine content; every invariant (human-file protection, taint, manifest, exfil linter) enforced once. The fail-closed lineage (ADR-27→28) relocated onto a single writer (HIST §11). Real safety gain.
4. **Snapshot → apply → verify → commit batch protocol + pathspec-limited commits + one-click revert.** Reversibility; continues ADR-127 commit hygiene (HIST §13). *Caveat: it must not replace the derivation-graph cascade — see alpha.15 ADAPT-1.*
5. **Cost / circuit-breaker machinery** — BYOK, normative price table, `max_tokens` ceilings, breaker at preview/pre-call, per-action $ preview. No alpha precedent, no research against; directly serves the "usable by a real researcher" bar (spend visible + bounded).
6. **Exfiltration linter — contain outputs, do not detect intent.** Research SUPPORTS: injection classifiers hit >90% adaptive bypass; containment is the necessary control (RR L9, L106; ADV survivor L91). Adopt the doctrine + write-time neutralization.
7. **Deterministic external grounding for metadata** — Zotero CSL-JSON over LLM metadata; two-stage reconcile against authoritative records. Research SURVIVOR — Rao & Callison-Burch: "a reliable mitigation must bypass LLM-based metadata construction entirely" (RR L85; ADV L101; BAR L21).
8. **Abstention + every printed number computed in code, never by the model.** Research SURVIVOR (Zou 2024: 37.1% vs 70.2% — a pipeline property; ADV L97).
9. **NLI calibration honesty upgrades:** dev-tuned thresholds on a tiny labeled set then frozen; HANS/PAWS launch gate; "**mentions = unknown stance, never no-contradiction**"; empty-contrasts ≠ agreement (MRMR); **`mc` relabeled "citation-correct," not "grounded"** (Wallat: up to 57% of RAG citations post-rationalized). Research — ADV #1 [BLOCKER], #3, #4; RR L71, L110. *(alpha.15 already had the HANS gate + shadow-first; beta.1's real additions are the dev-tune-then-freeze, the mc relabel, and the MRMR honesty.)*
10. **Section-expanded synthesis** — expand retrieved anchors to coherent slices before synthesis. Research — Hu 2026 (top-k fragments degrade integrative answers); ADV #6.
11. **Per-OS keychain for BYOK keys** (Keychain/DPAPI/Secret Service + 0600 fallback). Follows from BYOK; adopt with the cost machinery.
12. **Staged writes + offline contract** — catalog/search/notes work offline; LLM jobs queue and fail cleanly, never half-write. Robustness; serves single-user-multi-device.
13. **Deterministic distrust flags (`truncated`/`abstract_only`) + "no OCR" codification.** Honest continuation of the alpha rule (HIST §9).

## BORROW WITH CONDITION

14. **Local self-contained retrieval stack** (FTS5 + sqlite-vec + bge-small ONNX + deberta NLI, installer-bundled, hash-pinned). **Condition:** alpha.15's *committed spike* recorded that sqlite-vec+embeddings did **not** beat qmd on the fixture (DH 2152; GR §10), and beta.1 mislabeled the swap "convergence." Adopt only if it **re-clears the alpha.15 baseline-gated spike** — else it crosses an evidence-backed "did not clear the bar."
15. **Onboarding wizard + "install → grounded answer ≤ 30 min" contract.** Serves the usable-by-a-real-user bar; realizes the deferred ADR-113 walkthrough (HIST §15). **Condition:** the sample corpus must be real citable sources, never generated.
16. **In-file provenance markers only via three-way agreement** (marker + current block hash + DB `checks` row). Borrow the *three-way-agreement discipline* **only if** a UI marker is proven necessary; the **DB stays the authority** (alpha.15 meaning-only). Note it re-opens the forged-status/hash-churn surface alpha.15 closed (DH 2086); the gate mitigates but does not eliminate it — prefer DB-only unless the UI need is demonstrated.

## DO NOT ADOPT — beta.1 choices that are regressions or unresolved decisions (flagged, not defaults)

- **Obsidian-plugin-as-required UI + resident plugin-supervised daemon** — reverses alpha.14's keep-test (the product must run with only `vim`/`nano`/a file browser; GR §1) and the no-daemon architecture (ADR-95 rejection: "an unattended always-on loop conflicts with the no-daemon architecture"). This is the **stack decision (B)**, not a free adopt.
- **citekey as the primary key** — REJECT on the fact that citekeys mutate (Zotero re-exports the same work under a new key when metadata changes), so a mutable key cannot be identity (owner R-1). Stable `work_id` instead.
- **`record.md` as catalog authority (markdown)** — reverts the 867-entry-spike-grounded SQLite-authority (ADR-124); the catalog is relational and derives from the `.bib`. Keep SQLite authority (alpha.15 BORROW-7).
- **The argument-graph / hub / claim-substrate / typed-links / gap-over-both-graphs / faceting removals** — these are beta.1 *deletions*, not features to adopt. The research + the mission support *keeping* them; they are handled in the alpha.15-borrow list.
