# alpha.10 temporary carryover

Working artifacts carried forward from alpha.9. Delete or move these before
alpha.10 closes.

## From alpha.9 `tmp/`

| alpha.9 file | alpha.10 disposition |
| --- | --- |
| `current-state-baseline.md` | Carried forward as `current-state-baseline.md`; fill before building memory machinery. |
| `design-update-recommendations.md` | Reduced to #859 plus the baseline instrument; do not restore the full literature memo unless a scoped design PR needs it. |
| `probe-qwen-compliance.py` | Carried forward as a smoke probe. |
| `spike-nli-vs-cosine.py` | Carried forward as a smoke probe. |
| `hermes-clean-slate-design.md` / `hermes-014-utilization-audit.md` | Reduced to #859 and `hermes-upgrade.md`; closed gate findings already landed in alpha.9. |
| Hermes 0.17 recommendations | Captured in `hermes-017-recommendations.md`; includes Kilo provider, Bitwarden, and gateway multiplexing recommendations. |
| Hermes 0.17 feature evaluation | Captured in `hermes-017-feature-eval.md`; full report behind the recommendations. |
| Codex Hermes 0.17 feature evaluation | Captured in `hermes-017-feature-eval-codex.md`; Codex-authored report copy. |
| ADR enforcement / implementation audits | Not carried forward; alpha.9 landed the fixes and drift-doctor slice. |
| alpha.9 ExecPlan | Not carried forward; checkpoint closed. |
