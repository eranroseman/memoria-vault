"""The repo-root constant, kept apart from `tests/helpers.py` on purpose.

`tests/helpers.py` imports `memoria_vault.runtime.{state, policy.audit,
trusted_writer, vaultio}` at module level, so anything that imports
`tests.helpers` pulls that whole runtime stack in with it. Two structural
guards -- `test_import_layering.py` and `test_testing_levels.py` -- are
AST-only by design, specifically so they never import the code they judge;
several other files (cspell scope, node tooling, the verify-script and
test-vault-install checks, ...) have no first-party imports of their own
either. All of them need only a `Path` here. If they got it from
`tests.helpers` instead, a broken `runtime.state` -- exactly the state
mid-move, e.g. tasks 6-7 of this plan -- would make them fail at pytest
*collection* instead of doing their job.

Keep this module stdlib-only. Do not merge it back into `helpers.py`.
"""

from __future__ import annotations

from pathlib import Path

# The one place test code derives the repo root. Everything else imports
# this (directly, or via tests.helpers' re-export): a file that computes
# the root from its own __file__ breaks silently when it moves.
ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_SEED = ROOT / "src/memoria_vault/product/workspace_seed"
