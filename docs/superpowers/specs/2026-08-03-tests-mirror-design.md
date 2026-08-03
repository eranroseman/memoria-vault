# `tests/` mirror — design and decision

Date: 2026-08-03. Status: **design, not authorised**. Supersedes the one-line
ruling in `2026-08-02-src-tests-structure-audit.md` §7-8, which declined the
mirror first on a safety claim that has since been fixed, then on grounds that
were correct but unmeasured. This document measures them.

Question: should `tests/` be reorganised into subdirectories mirroring the
`src/memoria_vault/` package tree?

---

## 1. What changed since the last ruling

Both blockers the earlier audit named are **paid for**, in stage 4 of that same
spec (#1734):

- `tests/test_testing_levels.py` uses `rglob` and asserts non-emptiness, so a
  move can no longer silently empty the level gate.
- `tests/paths.py` holds the repo-root constant; 17 test files import `ROOT`
  from it instead of walking `__file__`. One holdout remains.
- `tests/test_dotted_target_literals.py` resolves every `^memoria_vault\.`
  string literal in `tests/`, so a stale monkeypatch target fails statically
  rather than patching nothing.

The mirror is therefore **no longer unsafe**. The remaining question is whether
it is useful, which is a different and weaker claim than the one previously
recorded.

---

## 2. The measurement that decides it

The mirror's premise is that a test file belongs under the module it exercises.
Measured over all 159 `test_*.py` files by parsing their imports:

| Shape | Files | Share |
| --- | --- | --- |
| Exercises **exactly one** `memoria_vault` package — an unambiguous home | **28** | 18% |
| Exercises **two or more** packages — no derivable home | **106** | 67% |
| Imports **nothing** from `memoria_vault` (static, lint, e2e, harness) | **25** | 16% |

**83% of the suite has no home derivable from its imports.** That is not a
defect in the tests. It is what the level distribution predicts:

| Level | Files |
| --- | --- |
| `contract` | 73 |
| `runtime` | 39 |
| `static` | 17 |
| `unit` | 14 |
| `package` | 7 |
| `floor` | 5 |
| `live` | 1 |

Only 14 files are `unit`. The suite is deliberately integration-shaped —
`contract` and `runtime` together are 112 of 156 — and integration tests cross
modules by definition. `test_attention_view.py` touches seven packages
(`engine`, `runtime.attention`, `runtime.capabilities`, `runtime.vaultio`,
`runtime.vocabulary`, `runtime.http_transport`, and `runtime` itself). There is
no fact of the matter about which directory it belongs in.

A mirror imposes a one-to-one structure on a many-to-many relation. The 106
ambiguous files would each be placed by a judgment call, and the resulting tree
would encode 106 opinions that no future reader can verify or re-derive.

### The obvious alternative measures no better

Grouping by filename prefix instead (`test_cli_*`, `test_attention_*`, …):
**48 of 159 files fall in a family of three or more. 111 are singletons or
pairs.** A tree built from that leaves two thirds of the suite in a
miscellaneous bucket, which is the `lib/` problem again with a different name.

---

## 3. Options

### A. Leave `tests/` flat — **recommended**

- **For:** 159 files in one directory is flat but findable, and `rg`/IDE search
  answers "where is the test for X" better than a tree built on 106 guesses.
  Costs nothing. Keeps `git log --follow` intact for the whole suite.
- **Against:** the directory listing is long, and no structure signals which
  area a file belongs to.

### B. Mirror `src/`, placing ambiguous files by primary subject

- **For:** matches the convention most Python projects use; makes the src
  reorganisation visible on the test side.
- **Against:** requires 106 individual judgment calls that nothing verifies;
  the 25 import-free files have no home at all and need an invented one; the
  tree would be up to four levels deep, since `src/` now reaches depth 3.
  Deletes nothing, so AGENTS.md's preferred remedy is unavailable.

### C. Group only the unambiguous 28 and the 25 orphans, leave 106 flat

- **For:** every placement is derivable; no judgment calls.
- **Against:** produces a half-organised tree — the exact coexistence state that
  `runtime/subsystems/` demonstrated is worse than either end. A reader must
  learn both schemes.

**Recommendation: A.** The measurement is the argument. If 83% of files cannot
be placed from evidence, the tree records opinions rather than facts, and the
next person to disagree has no way to settle it. Option C is explicitly worse
than both A and B for the reason `subsystems/` already taught this repo.

This is a recommendation, not a veto. If B is wanted anyway, §4 is executable.

---

## 4. If B is authorised: the design

### 4.1 Placement rule, in priority order

1. **One package imported** → `tests/<package path>/` (28 files, derivable).
2. **Many packages** → the package whose behaviour the file's *assertions*
   name, not the one it imports most. Recorded per file in the PR body so a
   reviewer can disagree with a specific call rather than the whole tree.
3. **No `memoria_vault` import** → by function, not subject:
   - `tests/gates/` — the 17 `static` files that check scripts, docs, spelling,
     workflow safety (`test_cspell_scope.py`, `test_doc_claims_gate.py`,
     `test_removed_surface_gate.py`, `test_import_layering.py`, …)
   - `tests/floor/` — the 5 floor-sweep files plus their fixtures
   - `tests/package/` — the 7 build/install/e2e files
4. **Shared helpers stay at `tests/` root** — `helpers.py`, `paths.py`,
   `cli_test_helpers.py`, `floor_lib.py`, `retrieval_fixtures.py`, `conftest.py`.
   Moving them would break the `tests.helpers` import path that 40+ files use
   and buy nothing.

### 4.2 Levels stay in `pytestmark`

Directories must **not** encode level. Level and area are orthogonal: a
`runtime.knowledge` test may be `unit` or `runtime`, and the gate selects by
marker across the whole tree. `tests/test_testing_levels.py` already enforces
exactly one registered level per file and now globs recursively, so it keeps
working unchanged. Any proposal to make directories carry level is a second
source of truth for the same fact.

### 4.3 What breaks, and what does not

| Concern | Status |
| --- | --- |
| Level gate silently empties | **Fixed** — `rglob` + non-vacuity assert |
| `__file__` root walks | **Fixed** — `tests/paths.py`, 17 files; 1 holdout to convert first |
| Stale monkeypatch string targets | **Covered** — `test_dotted_target_literals.py` fails them statically |
| `import conftest` in `test_tmpfs_tmpdir.py` | pytest's prepend import mode puts `tests/` on `sys.path` regardless of subdirectory, so the bare import keeps resolving. Verify empirically before relying on it. |
| `tests/fixtures/**` relative paths | `retrieval_fixtures.py` and `floor_lib.py` resolve fixture dirs from their own location — convert to `tests.paths` first |
| Floor goldens | Unaffected: they hash the seeded vault, not test paths |
| `git log --follow` | Degrades for every moved file. Unavoidable; the reason to do it once rather than incrementally |

### 4.4 Staging

1. Convert the last `__file__` root holdout and the two fixture-dir constants
   to `tests.paths`. No moves. Independently mergeable.
2. Create the directories and move the **28 derivable** files. Mechanical,
   reviewable, and reversible.
3. Move the **25 import-free** files into `gates/`, `floor/`, `package/`.
   Also derivable.
4. Move the 106 ambiguous files **in themed batches**, each PR carrying its
   placement rationale in the body. One giant PR here is unreviewable.

Each stage must be green under `python scripts/verify` on its own, and no stage
may leave a file importable from two paths.

---

## 5. Open questions

1. Is B authorised at all, given §2? If the answer rests on "most projects do
   it this way", say so explicitly — that is a legitimate reason, and it is a
   different reason than the evidence supports.
2. If B proceeds, who arbitrates the 106 placements, and is a reviewer expected
   to check them or accept them? The answer determines whether stage 4 is four
   PRs or forty.
3. Should `tests/unit/` exist as a peer of the mirror for the 14 `unit` files,
   or do they mirror like everything else? They are the only files for which
   the mirror premise actually holds.
