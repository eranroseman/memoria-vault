# ExecPlan — Consolidate the project into one folder (bare repo + worktrees)

Reorganize the on-disk project so opening **`~/memoria-vault`** shows everything —
repo, worktrees, scratch, sandbox — each governed by its own rules, using the
standard git **bare-repository + worktrees** layout.

Target chosen: **Option 1 (bare + worktrees)** — the industry idiom, no special
checkout, no gitignore hacks. **This plan executes Option 1 only.** Option 2 (a
normal `main/` checkout holding the `.git`) is a *materially different* procedure
— no `.bare`, different `git -C` targets, different upstream/worktree repair,
cleanup, and validation — **not** a one-line variant of this one; it is out of
scope here. If you want Option 2, it needs its own concrete sequence.

## 0. Metadata

- **Task:** Convert `~/memoria-vault` from a single checkout into a container
  holding `.bare/`, `main/`, `scratch/`, `worktrees/`, and `sandbox/`, then
  update path references. No re-clone; no data loss.
- **Worktree / branch for the doc-update PR:** `~/memoria-vault/worktrees/layout-paths`
  · `fix/layout-paths` off `origin/main` (created *after* the filesystem move).
  This plan lives on the `scratch` branch under `scratch/workflow-audit/`; the
  de-nest (Phase A, step 0) later moves it to `workflow-audit/`.
- **Related ADRs:** none required — this is a machine-local dev-environment
  convention documented in AGENTS.md, not a product/architecture decision.
- **Related issues / milestone:** —
- **Started:** 2026-07-04 · **Last updated:** 2026-07-04

## 1. Purpose / big picture

**Goal — in one sentence:** open a single folder, `~/memoria-vault`, and see the
*entire* project (repo, task worktrees, scratch, sandbox) in one place, with **each
part still governed by its own rules**. This plan changes only *where the pieces sit
on disk* — not the rules, not the history, not the workflow.

**Today the pieces are scattered across unrelated locations**, so no single folder
shows the project:

| Piece                  | Lives now at        | Its rule (unchanged by this plan) |
| ---------------------- | ------------------- | --------------------------------- |
| repo (`main`)          | `~/memoria-vault`   | PR + required CI                  |
| task worktrees         | `~/mv/<session>`    | branch → PR → main                |
| scratch fast-lane      | `~/mv/scratch`      | commit direct + push, no PR/CI    |
| sandbox (test vault)   | `~/Memoria-test`    | disposable install, runtime tests |

To find scratch you must know it lives at `~/mv/scratch`; to find a worktree you must
remember which `~/mv/<name>` it was. Opening `~/memoria-vault` shows only `main`.

When this plan is done, `~/memoria-vault/` is a **container** holding all of them as
siblings under one roof — same rules, one folder to open:

```
~/memoria-vault/
  .bare/          the git object store (bare repo)        · standard name
  .git            file: "gitdir: ./.bare"
  main/           main branch checkout                    · rule: PR + required CI
  scratch/        scratch orphan-branch checkout          · rule: commit direct + push, no PR/CI
  worktrees/      task/feature worktrees                  · rule: branch → PR → main
  sandbox/        the sandbox (was ~/Memoria-test)        · rule: disposable install, runtime tests
```

Each part "follows its own rules" because they are branches with their own
governance (main protected by its ruleset; feature branches PR'd) plus a sandbox
that is not under the repo's git at all. Because the container is not itself a
working tree, nothing needs gitignoring.

**Scratch specifically** is a worktree on the **`scratch` orphan branch** — the
git-idiomatic mechanism for versioned content that shares no history with `main`
(the same pattern as `gh-pages`/asset branches). This is what its constraints
require: it must have **history + GitHub backup** (so it is a real branch pushed
to `origin/scratch`, *not* gitignored — the gitignored `_notes/` approach caused
problems precisely because it had neither), yet must **skip the PR/CI cycle** (so
it is not on `main`). Being orphan (scratch-only content, no full-repo mirror) is
what fixes the drift/misfiling/stale-analysis the earlier full-tree scratch branch
caused. Its rule: **commit direct + push to `origin/scratch`; no PR, no CI;
protected from deletion and force-push** (a minimal branch ruleset). Because
skipping PR/CI requires its own branch, and a checkout of a non-`main` branch is a
separate worktree, scratch is necessarily a **sibling**, not a subfolder of
`main/`.

## 2. Context and orientation

Terminology: a **bare repository** has no working tree — just the object store
(`objects/`, `refs/`, `config`, reflogs). A **linked worktree** is an additional
checkout of a branch that shares the bare repo's objects; git tracks it under
`.bare/worktrees/<name>/`, and the worktree's own `.git` is a *file* pointing
there. The `.git` file at the container root (`gitdir: ./.bare`) lets
**repo-management** commands (`git worktree`, `git branch`, `git fetch`) run from
`~/memoria-vault/` itself — but it points at a *bare* repo, so **working-tree**
commands (`git status`, `git add`) there fail; run those inside `main/`, `scratch/`,
or a worktree.

**Current on-disk state — enumerate LIVE at execution (concurrent sessions move it;
do NOT trust any snapshot baked into this doc):**
- Worktrees: `git -C ~/memoria-vault worktree list`
- Sandbox: `ls ~/Memoria-test` (disposable test vault, no functioning git)
- Stray cruft under `~/mv/`: `find ~/mv -maxdepth 1` (expect leftovers such as an
  empty `.git`, `main-merge/`, `.agents/`, `.codex/`)
- **Ignored/untracked local data** (feeds the step-6 preserve-gate — see below):
  `git -C ~/memoria-vault status --porcelain --ignored`
- (2026-07-04 audit snapshot — for context only, now stale: worktrees were
  `~/memoria-vault` [main], `~/mv/{adr-consolidate,revert-wa,scratch,stale-docs}`;
  as of last check only `~/memoria-vault` [main] and `~/mv/scratch` [scratch] remain.)

**Path references that will go stale:** the authoritative list is **whatever the
Phase B `git grep` (step 7) surfaces** — do not hardcode targets that may have moved
or been deleted. Illustrative examples: `AGENTS.md` (§1 worktree convention
`~/mv/<session>` and the "Where things live" table) and `scripts/refresh-test-vault.sh`
(`VAULT="$HOME/Memoria-test"`).

**HARD PREREQUISITES (the plan is unsafe without these — a 2026-07-04 pre-flight
audit found several of these unmet):**
1. **A quiet window that holds through BOTH Phase A and the Phase B merge** — no
   active agent session for the *whole* migration, not just Phase A. Two reasons:
   (a) the conversion transiently breaks every worktree's git linkage; (b) between
   Phase A finishing and the Phase B PR merging, the on-disk layout **contradicts
   AGENTS.md** (which still says worktrees live at `~/mv/<session>` and the repo is
   `~/memoria-vault`), so any session that starts in that gap will `cd` into a bare
   container and try to add a worktree under a `~/mv` that no longer exists.
   **Do not resume agent work until the Phase B PR has merged.** Given this repo's
   heavy concurrency (worktrees appear/vanish every few minutes), treat this as a
   scheduled maintenance window, not a lull.
2. **Every worktree clean** — the bare repo is built from *committed* state, so
   any uncommitted work is lost when old worktrees are removed. `git status` in
   every worktree must be empty. (Audit: `~/mv/adr-consolidate` still had
   uncommitted changes **and** 3 unpushed commits — an active session. Wait for it
   to commit AND push. Unpushed commits are captured by the clone; uncommitted
   changes are not.)
3. **No unresolved stashes** — `git clone --bare` does **not** copy stashes, so
   every `git stash`/rebase-autostash entry vanishes from the new layout (it
   survives only in the backup, and is fiddly to recover). `git stash list` must
   be **empty** before migrating. (Audit found TWO `autostash` entries in the
   shared git dir — a 161-file diff, and one holding `scratch/.notes` + a real
   214-line alpha.13 design change. This is the single biggest silent-data-loss
   risk.) Resolve each: `git -C ~/memoria-vault stash show -p stash@{N}` →
   apply/commit the real ones, drop confirmed-stale ones.
4. **Hermes gateway stopped** — Obsidian and Hermes are **not used in alpha.15**,
   so this is a light gate. The gateway is a systemd user service
   (`hermes-gateway.service`) that respawns on a plain `kill`, so stop it with
   `systemctl --user stop hermes-gateway.service` — only so no process holds the
   sandbox during the move. It **stays stopped; do not restart it** (nothing in
   alpha.15 needs it) and there is no runtime config to re-point. (Already stopped
   2026-07-04.)
5. **This plan committed to `scratch`** — so the bare clone captures it and it
   survives the move. (Done: commit `53ebbb61`.)

## 3. Plan of work

Three phases. Phase A is a local filesystem/git operation (no PR). Phase B is a
normal PR that fixes the now-stale *tracked* path references. Phase C is the
machine-local reconfiguration no PR can do. **The freeze (prereq 1) holds from the
start of Phase A until Phase B has merged;** Phase C follows.

**Phase A — build the container (local, reversible via backup).** First **de-nest
the `scratch` branch** (step 0: move its `scratch/…` content to the branch root,
commit, push) so the bare clone captures the flat layout and the scratch worktree
lands clean. Then back up the object store. Build the new layout *beside* the current
one (`~/memoria-vault-new`)
so nothing is destroyed until it is verified: create the bare repo (objects
hardlinked from the local repo — fast, no network), re-point its `origin` at the
real GitHub URL and set the remote-tracking fetch refspec (the one bare-repo
gotcha), drop the `gitdir` pointer, then `git worktree add` `main`, `scratch`, and
each feature branch into place. Move the sandbox in. Only once the new container
verifies do we remove the old checkout + old worktrees and swap the new container
to `~/memoria-vault`. Clean the `~/mv` cruft.

**Phase B — fix path references (PR).** From a worktree under the new layout,
branch off `origin/main`, grep *all* tracked files for the old paths, update the
stale conventions (AGENTS.md worktree path → `~/memoria-vault/worktrees/<session>`
and repo-root → `~/memoria-vault/main`; `refresh-test-vault.sh` default →
`~/memoria-vault/sandbox`; **whatever else the grep surfaces**) **plus the de-nest
doc-sync** (AGENTS.md scratch-flow `scratch/releases/<version>/` → `releases/<version>/`;
and **remove** `status_doctor`'s dead `scratch/releases` scan — do NOT rename it to
`releases`, see step 0's note), and open one PR. CI
is unaffected (it clones fresh); only local conventions change. **The freeze stays
in force until this PR merges** — until then the disk contradicts AGENTS.md.

**Phase C — post-migration reconfiguration (machine-local, no PR can do this).**
Things that reference the old paths but live *outside* the repo, so Phase B can't
touch them:
- **Runtime / sandbox path — N/A in alpha.15.** Obsidian and Hermes are not used,
  so there is no machine-local runtime config pointing at the sandbox to re-point
  and no gateway to restart. The sandbox folder still moves (Phase A) and its
  *tracked* default updates (Phase B); nothing else depends on it. (If a later
  stage adopts Hermes/Obsidian, re-point `~/.hermes` profiles + the Obsidian vault
  to `~/memoria-vault/sandbox` then.)
- **Branch upstreams.** The bare clone leaves branches with no upstream, so set it
  once (Phase A step, but verify here) — else bare `git pull`/`push` complain.
- **Shell / IDE.** Aliases, shell rc, and IDE/editor workspace files that assume
  the repo is at `~/memoria-vault` (now a container) or worktrees at `~/mv/` →
  update to `~/memoria-vault/main` and `~/memoria-vault/worktrees/`.

## 4. Concrete steps

Run these from a shell whose CWD is **`~`** (never inside a worktree being moved).
`TS` is a timestamp for the backup. Read the real remote URL rather than guessing.

0. **De-nest the `scratch` branch** (independent scratch-branch commit; must land
   *before* the bare clone in step 2 so the clone captures the flat layout). The
   `scratch/` wrapper is a fossil from when scratch was a subfolder of `main`; the
   orphan branch is entirely scratch, so the prefix is redundant and is the sole
   cause of the `~/memoria-vault/scratch/scratch/…` double-nest. Move the content to
   the branch root:

   ```bash
   cd <the scratch worktree>            # the only worktree on the scratch branch
   git ls-tree --name-only HEAD         # MUST show only "scratch" at root (no stray root files)
   git mv scratch/* .                   # releases/, workflow-audit/ -> branch root
   for f in scratch/.[!.]*; do [ -e "$f" ] && git mv "$f" .; done   # any dotfiles (none today)
   rmdir scratch
   PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "scratch: de-nest content to branch root"
   git push                             # origin/scratch — direct, no PR/CI (scratch rules)
   ```

   Expected: root now holds `releases/`, `workflow-audit/` directly; this plan moves
   to `workflow-audit/exec-plan-project-layout.md`. `pr-policy`'s main-side `scratch/`
   block is untouched (it guards main-branch worktrees, orthogonal to this branch's
   layout). Doc follow-ups in Phase B (step 7): update the AGENTS.md scratch-flow
   wording; and **remove** `status_doctor`'s `scratch/releases` scan — it globs its
   own worktree root (`ROOT = __file__/../..`, then `root/scratch/releases`), so
   post-container it cannot reach the sibling `~/memoria-vault/scratch/` at all, and
   renaming it to `releases` would wrongly point at `main/releases`. (It is already a
   dead no-op on `main` today, since `main` carries no `scratch/`.)

1. **Pre-flight + backup:**

   ```bash
   cd ~
   git -C ~/memoria-vault fetch --prune origin              # current origin tips (HIGH #1: avoid stale clone)
   git -C ~/memoria-vault branch -vv                        # inspect [ahead]/[behind] per branch
   for w in $(git -C ~/memoria-vault worktree list --porcelain | awk '/^worktree /{print $2}'); do
     git -C "$w" pull --ff-only 2>/dev/null || true         # fast-forward any behind branch BEFORE cloning
     echo "$w: $(git -C "$w" status --porcelain | wc -l) uncommitted"
   done                                                     # EVERY line: "0 uncommitted"
   git -C ~/memoria-vault branch -vv | grep '\[behind'      # MUST print NOTHING (else a branch is still stale — STOP)
   git -C ~/memoria-vault stash list                        # MUST be empty (prereq 3) — clone drops stashes
   systemctl --user stop hermes-gateway.service 2>/dev/null || true   # prereq 4 (MED #5: "No medium found" if no user bus — tolerate)
   pgrep -af 'gateway run' | grep -v pgrep && echo "gateway STILL running — kill: pkill -f 'gateway run'" || echo "no gateway process ✓"
   git -C ~/memoria-vault worktree list --porcelain \
     | awk '/^branch /{sub("refs/heads/","",$2);print $2}' > ~/mv-branches.txt         # live worktree→branch map (step 3)
   git -C ~/memoria-vault worktree list --porcelain | awk '/^worktree /{print $2}' \
     | grep "^$HOME/mv/" > ~/mv-worktree-paths.txt                                     # old worktree dirs under ~/mv (step 6 cleanup)
   ORIGIN=$(git -C ~/memoria-vault remote get-url origin); echo "origin=$ORIGIN"
   cp -r ~/memoria-vault/.git ~/memoria-vault-git-backup    # rollback — name deliberately clear of ~/mv
   ```

   Expected: fetch clean; **no branch prints `[behind …]`** (fast-forward it or
   STOP — a behind branch would clone stale and later falsely "match" origin);
   all worktrees `0 uncommitted`; `stash list` **empty**; Hermes inactive;
   `~/mv-branches.txt` lists every live worktree branch; a backup at
   `~/memoria-vault-git-backup` (NOT under `~/mv`, which gets deleted). **If any
   branch is behind, a stash exists, or a worktree is dirty, STOP.**

2. **Build the bare container beside the current one:**

   ```bash
   mkdir ~/memoria-vault-new
   git clone --bare ~/memoria-vault ~/memoria-vault-new/.bare        # hardlinks objects, all branches
   git -C ~/memoria-vault-new/.bare remote set-url origin "$ORIGIN"  # re-point to GitHub
   git -C ~/memoria-vault-new/.bare config remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'
   git -C ~/memoria-vault-new/.bare fetch origin                     # populate remote-tracking refs
   for b in $(git -C ~/memoria-vault-new/.bare for-each-ref --format='%(refname:short)' refs/heads); do
     git -C ~/memoria-vault-new/.bare branch --set-upstream-to="origin/$b" "$b" 2>/dev/null   # else pull/push complain (risk #3)
   done
   printf 'gitdir: ./.bare\n' > ~/memoria-vault-new/.git
   ```

   Expected: `.bare` exists; `git -C ~/memoria-vault-new branch -a` lists every
   local branch (main, scratch, fix/*) plus `remotes/origin/*`.

3. **Add the worktrees into their new homes.**

   > **Scratch was de-nested in step 0.** The `scratch`
   > branch's content lives at its **root** (`releases/`, `workflow-audit/`), not under
   > a `scratch/` wrapper, so `git worktree add scratch scratch` yields a clean
   > `~/memoria-vault/scratch/releases/…` — the standard worktree idiom (folder named
   > for the branch, content at the branch root), no double-nest. `pr-policy` still
   > blocks `scratch/` paths in *main* PRs; that guard is about main-branch worktrees
   > and is unaffected by the orphan branch's internal layout.

   ```bash
   cd ~/memoria-vault-new
   git worktree add main main
   git worktree add scratch scratch        # ~/memoria-vault/scratch/ = releases/ + workflow-audit/ directly (de-nested)
   # HIGH #2/#3: a worktree for every OTHER live branch, from the preflight snapshot;
   # sanitize the FULL branch path — basename alone would collide (fix/foo vs feature/foo).
   for b in $(grep -vxE 'main|scratch' ~/mv-branches.txt); do
     d="worktrees/$(printf '%s' "$b" | tr / __)"        # fix/foo -> fix__foo (unique, keeps context)
     [ -e "$d" ] && { echo "target $d already exists — STOP"; break; }
     git worktree add "$d" "$b"
   done
   git worktree list                                                  # all resolve under ~/memoria-vault-new
   ```

   Expected: `main/`, `scratch/`, and a `worktrees/<sanitized-branch>` for **every**
   branch in `~/mv-branches.txt`, no collisions; `worktree list` clean and complete.

4. **Move the sandbox in** (Hermes must not be using it — prereq 4):

   ```bash
   pgrep -af hermes | grep -v pgrep    # empty, or confirmed NOT bound to ~/Memoria-test
   mv ~/Memoria-test ~/memoria-vault-new/sandbox    # rename Memoria-test → sandbox
   ```

5. **Verify the new container BEFORE destroying the old one** — health **and a
   branch-tip manifest** (HIGH #3: never delete old state until every old branch
   tip + worktree is proven present in the new container):

   ```bash
   git -C ~/memoria-vault-new/main status            # clean
   git -C ~/memoria-vault-new/main fetch origin --dry-run   # refspec works, no error
   bash ~/memoria-vault-new/main/scripts/test.sh l0  # green
   ls ~/memoria-vault-new                            # .bare .git main scratch worktrees sandbox
   # MANIFEST 1 (HIGH #2): EVERY local branch ref — not just worktree-attached ones —
   # must survive in the new .bare (as tip or ancestor).
   git -C ~/memoria-vault for-each-ref --format='%(refname:short) %(objectname)' refs/heads > ~/mv-refs-manifest.txt
   fail=0
   while read b h; do
     newh=$(git -C ~/memoria-vault-new/.bare rev-parse "$b" 2>/dev/null)
     if [ -z "$newh" ]; then echo "MISSING branch $b"; fail=1
     elif [ "$newh" != "$h" ] && ! git -C ~/memoria-vault-new/.bare merge-base --is-ancestor "$h" "$newh" 2>/dev/null; then
       echo "branch $b: old tip $h NOT in new $newh"; fail=1; fi
   done < ~/mv-refs-manifest.txt
   # MANIFEST 2 (separate check): every OLD worktree's branch has a worktree in the new container
   for b in $(git -C ~/memoria-vault worktree list --porcelain | awk '/^branch /{sub("refs/heads/","",$2);print $2}'); do
     git -C ~/memoria-vault-new worktree list | grep -q "\[$b\]" || { echo "no worktree for $b"; fail=1; }
   done
   [ "$fail" = 0 ] && echo "MANIFEST OK — safe to swap" || echo "MANIFEST FAILED — DO NOT run step 6"
   ```

   Expected: clean status, fetch works, l0 green, all five entries present, and
   **`MANIFEST OK`** — every old branch HEAD is present (as tip or ancestor) in the
   new `.bare` with a matching worktree. **Do not run step 6 unless every check
   passes and MANIFEST is OK** — the old repo is still fully intact until then.

6. **Swap into place and clean up:**

   ```bash
   # HIGH — PRESERVE-GATE (run BEFORE the rm): the bare clone copied only git objects.
   # Ignored/untracked local data in the old checkout is NOT in .bare, and the rm below
   # destroys it permanently. On last check this included _papers (~2.1G) and _notes.
   git -C ~/memoria-vault status --porcelain --ignored \
     | awk '$1=="!!"||$1=="??"{print $2}' | sed 's#/.*#/#' | sort -u   # inventory — classify EACH:
   #   preserve (durable, not in git):  _papers/, _notes/, any local data  -> move it
   #   rebuild  (regenerable):          node_modules/, .venv/, .qmd/, *_cache/, .coverage
   #   delete   (confirmed junk):       let the rm handle it
   for p in _papers _notes ; do        # <-- EDIT this list to match the inventory above
     [ -e ~/memoria-vault/"$p" ] && mv ~/memoria-vault/"$p" ~/memoria-vault-new/main/"$p"
   done
   # Only once every durable path is moved and the remainder is confirmed regenerable/junk:
   rm -rf ~/memoria-vault          # old checkout — tracked content safely in .bare + main/
   mv ~/memoria-vault-new ~/memoria-vault
   # MED #4: surgical ~/mv cleanup — remove exactly the registered old worktrees +
   # known cruft, then rmdir ~/mv ONLY if genuinely empty (never a blind rm -rf ~/mv).
   while read -r d; do rm -rf "$d"; done < ~/mv-worktree-paths.txt   # old worktree dirs (from preflight)
   rm -rf ~/mv/main-merge ~/mv/.git ~/mv/.agents ~/mv/.codex          # the known cruft
   if [ -z "$(find ~/mv -mindepth 1 2>/dev/null)" ]; then rmdir ~/mv && echo "~/mv removed";
   else echo "~/mv NOT empty — inspect before removing:"; ls -la ~/mv; fi
   git -C ~/memoria-vault worktree prune
   git -C ~/memoria-vault worktree list   # everything under ~/memoria-vault/
   ( cd ~/memoria-vault/main && pre-commit install )   # the bare clone dropped the installed hooks
   ```

   Expected: durable ignored data (`_papers`, `_notes`, …) moved into `main/` **before**
   the rm; every registered old worktree + known cruft removed; `~/mv` **rmdir'd
   only if empty** (else it stops and lists what's left for you to inspect);
   `worktree list` shows all worktrees under `~/memoria-vault/`; hook re-installed.

7. **Phase B — the path-reference PR:**

   ```bash
   cd ~/memoria-vault
   git worktree add worktrees/layout-paths -b fix/layout-paths origin/main
   cd worktrees/layout-paths
   git grep -n -e '~/mv/' -e '/home/eranr/mv/' -e 'Memoria-test' -e '~/memoria-vault' -- . ':!scratch/'
   # edit whatever the grep surfaced (AGENTS.md, scripts/refresh-test-vault.sh, …)
   pre-commit run --all-files && bash scripts/test.sh all
   git push -u origin fix/layout-paths && gh pr create --base main --fill
   ```

   Expected: grep enumerates the references; after edits, gate green; PR opens
   (sensitive paths → `needs_human`). **Keep the freeze until this PR merges** —
   the disk contradicts AGENTS.md until then.

8. **Phase C — post-migration reconfiguration** (after the Phase B PR merges; this
   is what ends the freeze):

   ```bash
   # Hermes/Obsidian: N/A in alpha.15 — gateway stays stopped, no runtime re-point.
   git -C ~/memoria-vault/main branch -vv    # confirm upstreams set (Phase A) so pull/push work
   # shell/IDE: fix any alias / workspace file assuming ~/memoria-vault is the repo or ~/mv the worktree parent
   ```

   Expected: branch upstreams resolve; nothing you use references `~/mv` or assumes
   `~/memoria-vault` is a checkout. **Only now resume agent work.**

## 5. Validation and acceptance

- **Claim:** Opening `~/memoria-vault` shows `main/`, `scratch/`, `worktrees/`,
  `sandbox/` (plus `.bare`). **Prove:** `ls ~/memoria-vault`.
- **Claim:** every worktree resolves against the bare repo. **Prove:**
  `git -C ~/memoria-vault worktree list` — no "prunable"/broken entries.
- **Claim:** `git fetch`/`pull` behave normally (the bare gotcha is handled).
  **Prove:** `git -C ~/memoria-vault/main fetch origin` succeeds and updates
  `origin/*` refs.
- **Claim:** no work was lost. **Prove:** `git -C ~/memoria-vault/main log --oneline -3`
  matches pre-migration `origin/main`; each feature branch is present with its tip.
- **Claim:** the repo is healthy. **Prove:** `bash ~/memoria-vault/main/scripts/test.sh all` → all PASS.
- **Claim:** no stale path references remain in tracked files. **Prove:** the
  Phase B grep returns only intentional/historical mentions after the PR.

## 6. Idempotence and recovery

- **Reversible until step 6.** Everything before the swap builds
  `~/memoria-vault-new` beside the untouched original; abort by `rm -rf
  ~/memoria-vault-new` — nothing lost.
- **Rollback after the swap:** restore from the backup —
  `rm -rf ~/memoria-vault && <recreate a checkout>` using
  `~/memoria-vault-git-backup` (a full copy of the original `.git`, including the
  reflogs and any stashes). Keep the backup until you have run a full gate and a
  `git fetch`/`push` cycle from the new layout and are satisfied.
- **Re-run safety:** steps are guarded (step 5 gates the destructive step 6). A
  partial run leaves the original intact until step 6.

## 7. Progress

- [ ] Prereqs met: quiet window; every worktree clean (`adr-consolidate`
      committed + pushed); **`git stash list` empty** (2 autostashes resolved);
      **Hermes gateway stopped/confirmed clear**; this plan committed to `scratch`.
- [ ] Phase A: `scratch` de-nested + pushed (step 0); bare container built,
      verified (step 5); **durable ignored data (`_papers`/`_notes`/…) preserved into
      `main/`** (step-6 preserve-gate); swapped in (step 6); pre-commit re-installed.
- [ ] Sandbox at `~/memoria-vault/sandbox`; `~/mv` removed.
- [ ] Phase B: path-reference PR merged.
- [ ] Backup `~/memoria-vault-git-backup` deleted after a clean gate + fetch/push
      cycle.
- [ ] Close-out: this plan deleted per ExecPlan lifecycle.

## 8. Execution log

- 2026-07-04 — Plan authored for Option 1 (bare + worktrees) after comparing it
  to Option 2. Chose bare for robustness (object store not hostage to any one
  checkout) and idiom; the fetch-refspec is set during migration so the known
  bare-repo gotcha never bites. Built-beside-then-swap chosen over in-place
  conversion so the operation is reversible right up to the swap.

## 9. Surprises & discoveries

- 2026-07-04 — `git clone --bare` from the local repo captures only *committed*
  state, which is why "every worktree clean" is a hard prerequisite rather than a
  nicety — uncommitted work in a worktree would be silently dropped.
- 2026-07-04 (pre-flight audit) — `git clone --bare` **also drops stashes**, and
  the shared git dir held TWO `autostash` entries (a 161-file diff; one with
  `scratch/.notes` + a real 214-line alpha.13 design change). These would have
  vanished silently from the new layout — added as prereq 3. Also found a **live
  Hermes gateway** (`hermes_cli.main gateway run`) — moving the sandbox under a
  running runtime would break it (prereq 4). And `adr-consolidate` still had
  uncommitted + 3 unpushed commits. None were true blockers to the *plan*, but all
  are blockers to *running it safely* — hence the expanded pre-flight. Backup
  renamed `~/mv-git-backup` → `~/memoria-vault-git-backup` so the `rm -rf ~/mv`
  cleanup can't come near it; added a `pre-commit install` in `main/` since the
  bare clone drops the installed hook.

## 10. Interfaces & dependencies

- `git worktree` / `git clone --bare` / `git worktree repair` semantics; the
  bare-repo remote-tracking fetch refspec (`+refs/heads/*:refs/remotes/origin/*`).
- The real `origin` URL — read via `git remote get-url origin`, never hardcoded.
- Tracked path references: whatever the Phase B `git grep` surfaces (e.g. `AGENTS.md`,
  `scripts/refresh-test-vault.sh`) — not a hardcoded list; targets move and get deleted.
- CI is unaffected — GitHub Actions checks out fresh, independent of local layout.

## 11. Artifacts & notes

- Option comparison (bare vs normal) that produced this choice was delivered in
  session 2026-07-04; the operative conclusion (bare = more robust + idiomatic,
  one-time fetch-refspec cost) is captured in §1/§8 so this plan stands alone.
- Backup location: `~/memoria-vault-git-backup` (full copy of the pre-migration
  `.git`; the single backup-path name used throughout — deliberately not under
  `~/mv`, which the swap deletes).

## 12. Outcomes & retrospective

- **Shipped:** — (fill at close)
- **Still open:** —
- **Routed to:** AGENTS.md (new worktree/paths convention) via the Phase B PR.
- **Lessons:** —
