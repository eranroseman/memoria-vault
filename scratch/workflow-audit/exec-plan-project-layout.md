# ExecPlan - Consolidate the project into one folder (normal checkouts + worktrees)

Reorganize the on-disk project so opening **`~/memoria-vault`** shows the whole
local project: the main checkout, the scratch checkout, feature worktrees, and the
test sandbox. Use boring Git: `main/` and `scratch/` are separate normal checkouts
with their own `.git`; feature worktrees are linked from `main/.git`.

Target chosen: **separate `main/` + `scratch/` checkouts, with main-owned feature
worktrees.** This replaces the earlier `.bare` container design. The `.bare` layout
was elegant but created the wrong failure mode here: a root `.git -> .bare` makes
`sandbox/` sit under Git discovery even though it is supposed to be outside the repo.
The normal-checkout layout satisfies the actual requirement with less migration
risk and fewer tool surprises.

## 0. Metadata

- **Task:** Convert the current scattered local layout into a single project
  container:

  ```text
  ~/memoria-vault/
    main/        normal checkout, branch main, owns main/.git
    scratch/     normal checkout, branch scratch, owns scratch/.git
    worktrees/   feature worktrees linked to main/.git
    sandbox/     disposable test vault, outside main/scratch Git discovery
  ```

- **Worktree / branch for the doc-update PR:** after the filesystem move,
  `~/memoria-vault/worktrees/layout-paths` on branch `fix/layout-paths` off
  `origin/main`.
- **Scratch plan location:** this plan currently lives on `origin/scratch` under
  `scratch/workflow-audit/`; Phase A step 0 de-nests the scratch branch, so it then
  lives at `workflow-audit/exec-plan-project-layout.md`.
- **Related ADRs:** none required. This is a machine-local dev-environment
  convention documented in `AGENTS.md`, not a product architecture decision.
- **Started:** 2026-07-04. **Last updated:** 2026-07-04.

## 1. Purpose / Big Picture

Goal: open `~/memoria-vault` and see the whole local project in one place, while
each part keeps its existing rule:

| Piece | Lives now | Lives after | Rule |
|---|---|---|---|
| main repo | `~/memoria-vault` | `~/memoria-vault/main` | PR + required CI |
| task worktrees | `~/mv/<session>` | `~/memoria-vault/worktrees/<branch>` | branch -> PR -> main |
| scratch fast lane | `~/mv/scratch` | `~/memoria-vault/scratch` | commit direct + push, no PR/CI |
| test sandbox | `~/Memoria-test` | `~/memoria-vault/sandbox` | disposable runtime/install target |

There is **no root `.git`** at `~/memoria-vault`. That is intentional. Git commands
run inside the checkout they apply to:

- `git -C ~/memoria-vault/main ...` for main and feature worktree management.
- `git -C ~/memoria-vault/scratch ...` for scratch.
- `~/memoria-vault/sandbox` is not under main/scratch Git discovery.

Scratch is a separate normal checkout of the orphan `scratch` branch. It has its
own `.git`, its own remote, and its own branch rules. This avoids the confusing
`scratch/scratch/...` nesting and avoids sharing main's worktree registry.

Feature branches remain Git worktrees because that is what they are for: cheap
parallel checkouts sharing `main/.git`.

## 2. Current-State Rules

Do not trust a baked-in snapshot. Before running the migration, enumerate live
state:

```bash
git -C ~/memoria-vault status --short --branch
git -C ~/memoria-vault worktree list --porcelain
git -C ~/memoria-vault branch -vv
git -C ~/memoria-vault stash list
git -C ~/memoria-vault status --porcelain --ignored
find ~/mv -maxdepth 1 -mindepth 1 -print 2>/dev/null || true
ls -la ~/Memoria-test
```

Important consequences:

- Moving the current `~/memoria-vault` checkout whole into `main/` preserves tracked
  files, untracked files, ignored files, stashes, hooks, caches, `_papers/`,
  `_notes/`, `.qmd/`, `.venv/`, and any other local state. This is simpler and safer
  than cloning and then trying to reconstruct ignored data.
- Moving feature worktree directories whole preserves any local ignored files inside
  them too.
- Scratch must be clean, pushed, and removed from the old main worktree registry
  before the old main checkout is moved.
- The old `~/Memoria-test` is disposable, but it is still moved into `sandbox/`
  rather than deleted. If a later refresh wants a blank vault, refresh it after the
  layout is stable.

## 3. Hard Prerequisites

1. **Quiet window until the Phase B PR merges.** The disk layout changes before
   `AGENTS.md` does. No other agent session should start or continue during Phase A
   or while the Phase B path-reference PR is open.

2. **Every worktree clean.** Run `git status --porcelain` in every registered
   worktree. Stop unless every result is empty.

3. **No unresolved stashes.** Run `git -C ~/memoria-vault stash list`. Stop unless
   it is empty. Resolve real stashes before migrating.

4. **Scratch plan committed and pushed.** `git -C ~/mv/scratch status --short` must
   be clean and `scratch` must be aligned with `origin/scratch`.

5. **Hermes gateway not holding the sandbox.** Alpha.15 does not use Hermes or
   Obsidian, but do not move a path while a process has it open. Use
   `systemctl --user stop hermes-gateway.service 2>/dev/null || true`, then check
   `pgrep -af 'gateway run'`.

## 4. Plan Of Work

Three phases:

- **Phase A:** local filesystem migration. No PR.
- **Phase B:** normal PR updating tracked path references.
- **Phase C:** local shell/editor follow-up.

The freeze lasts from the start of Phase A until the Phase B PR has merged.

## 5. Concrete Steps

Run from `~`, never from a worktree being moved.

### 0. De-Nest The Scratch Branch

The current orphan `scratch` branch still has a top-level tracked `scratch/`
directory. Because the branch itself is scratch, that wrapper is redundant and
causes `scratch/scratch/...` after checkout.

```bash
cd ~/mv/scratch
git pull --ff-only origin scratch
git ls-tree --name-only HEAD            # must print only: scratch
git mv scratch/* .
for f in scratch/.[!.]*; do [ -e "$f" ] && git mv "$f" .; done
rmdir scratch
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "scratch: de-nest content to branch root"
git push origin HEAD:scratch
cd ~

old_scratch=$(git -C ~/memoria-vault worktree list --porcelain \
  | awk '/^worktree /{w=$2} /^branch refs\/heads\/scratch$/{print w}')
[ -n "$old_scratch" ] && git -C ~/memoria-vault worktree remove "$old_scratch"
```

Expected: the scratch branch root now contains `releases/`, `workflow-audit/`, etc.
This plan's path becomes `workflow-audit/exec-plan-project-layout.md`.
The old linked scratch worktree no longer appears in
`git -C ~/memoria-vault worktree list`.

Phase B must update tracked docs that still describe `scratch/releases/...`. For
`scripts/status_doctor.py`, remove the dead `root/scratch/releases` scan; do not
rename it to `root/releases`, because the doctor runs from a main worktree root, not
from the project container root.

### 1. Preflight And Backup

```bash
cd ~
git -C ~/memoria-vault fetch --prune origin

for w in $(git -C ~/memoria-vault worktree list --porcelain | awk '/^worktree /{print $2}'); do
  git -C "$w" pull --ff-only 2>/dev/null || true
  echo "$w: $(git -C "$w" status --porcelain | wc -l) uncommitted"
done

if git -C ~/memoria-vault branch -vv | grep '\[behind'; then
  echo "behind branch - STOP"
  exit 1
fi

if [ -n "$(git -C ~/memoria-vault stash list)" ]; then
  git -C ~/memoria-vault stash list
  echo "stashes present - STOP"
  exit 1
fi

systemctl --user stop hermes-gateway.service 2>/dev/null || true
if pgrep -af 'gateway run' | grep -v pgrep; then
  echo "gateway still running - STOP"
  exit 1
fi
echo "no gateway process"

git -C ~/memoria-vault worktree list --porcelain \
  | awk '/^worktree /{w=$2} /^branch /{sub("refs/heads/","",$2); print $2 "\t" w}' \
  > ~/mv-worktrees.tsv

git -C ~/memoria-vault for-each-ref --format='%(refname:short) %(objectname)' refs/heads \
  > ~/mv-refs-manifest.txt

ORIGIN=$(git -C ~/memoria-vault remote get-url origin)
cp -a ~/memoria-vault/.git ~/memoria-vault-git-backup
```

Stop unless:

- every worktree prints `0 uncommitted`;
- no branch is behind;
- `git stash list` is empty;
- no gateway process is running;
- `~/mv-worktrees.tsv` lists every current worktree;
- `~/memoria-vault-git-backup` exists.

### 2. Build The New Container By Moving Existing State

Move the existing main checkout whole. This preserves ignored and untracked local
data without a fragile copy whitelist.

```bash
mv ~/memoria-vault ~/memoria-vault-main-moving
mkdir -p ~/memoria-vault-new/worktrees
mv ~/memoria-vault-main-moving ~/memoria-vault-new/main
```

Expected: `~/memoria-vault-new/main/.git` is the original real `.git` directory.

### 3. Move Feature Worktrees Under The Container

Move existing linked worktree directories. Do not flatten branch names; `fix/foo`
should live at `worktrees/fix/foo`.

```bash
while IFS="$(printf '\t')" read -r branch path; do
  case "$branch" in
    main) continue ;;
    scratch) continue ;;
  esac

  target="$HOME/memoria-vault-new/worktrees/$branch"
  mkdir -p "$(dirname "$target")"
  [ -e "$target" ] && { echo "target exists: $target - STOP"; exit 1; }
  mv "$path" "$target"
done < ~/mv-worktrees.tsv

git -C ~/memoria-vault-new/main worktree repair \
  $(awk -F '\t' '$1!="main" && $1!="scratch"{print ENVIRON["HOME"] "/memoria-vault-new/worktrees/" $1}' ~/mv-worktrees.tsv)
```

Expected: feature worktrees are under `~/memoria-vault-new/worktrees/...`, preserving
branch path structure.

### 4. Create Scratch As A Separate Normal Checkout

Create an independent checkout of `scratch` with its own `.git`.

```bash
git clone --branch scratch --single-branch ~/memoria-vault-new/main ~/memoria-vault-new/scratch
git -C ~/memoria-vault-new/scratch remote set-url origin "$ORIGIN"
git -C ~/memoria-vault-new/scratch fetch --prune origin
git -C ~/memoria-vault-new/scratch branch --set-upstream-to=origin/scratch scratch
```

Expected:

```bash
git -C ~/memoria-vault-new/scratch rev-parse --absolute-git-dir
# /home/eranr/memoria-vault-new/scratch/.git
```

### 5. Move The Sandbox

Move the disposable sandbox into the project container. Because there is no root
`.git`, the sandbox is not under main/scratch Git discovery.

```bash
mv ~/Memoria-test ~/memoria-vault-new/sandbox
```

Expected: `~/memoria-vault-new/sandbox` exists. A later test refresh can rebuild it
in place.

### 6. Remove Known Accidental Local Cruft

Remove the malformed literal UNC `.codex` folder only if it is still present under
the moved main checkout and contains no real work. This is not the real `~/.codex`;
it is the accidental directory whose name begins with `\\wsl.localhost`.

```bash
find ~/memoria-vault-new/main -maxdepth 1 -name '*wsl.localhost*' -print

bad_unc=$(find ~/memoria-vault-new/main -maxdepth 1 -name '*wsl.localhost*' -print -quit)
if [ -n "$bad_unc" ]; then
  find "$bad_unc" -maxdepth 4 -type f -print
  if [ -z "$(find "$bad_unc" -type f -print -quit)" ]; then
    rm -r "$bad_unc"
  else
    echo "UNC-like local folder has files - inspect before removing: $bad_unc"
    exit 1
  fi
fi
```

Expected: either no malformed UNC folder exists, or it was empty and removed.

### 7. Verify Before Final Swap

```bash
git -C ~/memoria-vault-new/main status --short --branch
git -C ~/memoria-vault-new/scratch status --short --branch
git -C ~/memoria-vault-new/main worktree list

bash ~/memoria-vault-new/main/scripts/test.sh l0

fail=0
while read -r branch old_tip; do
  new_tip=$(git -C ~/memoria-vault-new/main rev-parse "$branch" 2>/dev/null) || {
    echo "missing branch: $branch"; fail=1; continue
  }
  if [ "$new_tip" != "$old_tip" ] \
    && ! git -C ~/memoria-vault-new/main merge-base --is-ancestor "$old_tip" "$new_tip"; then
    echo "branch $branch lost old tip $old_tip -> $new_tip"
    fail=1
  fi
done < ~/mv-refs-manifest.txt

git -C ~/memoria-vault-new/sandbox rev-parse --show-toplevel >/tmp/sandbox-git-root 2>/dev/null || true
cat /tmp/sandbox-git-root

[ "$fail" = 0 ] && echo "MANIFEST OK - safe to swap" || echo "MANIFEST FAILED - STOP"
```

Expected:

- main and scratch are clean;
- `test.sh l0` passes;
- every local branch tip survived;
- sandbox is either not a Git repo or its Git root is `~/memoria-vault-new/sandbox`,
  never `main`;
- manifest says OK.

### 8. Final Swap And Old Directory Cleanup

Only run this after step 7 passes.

```bash
mv ~/memoria-vault-new ~/memoria-vault

while IFS="$(printf '\t')" read -r branch path; do
  case "$path" in
    "$HOME"/mv/*)
      [ -e "$path" ] && { echo "leftover moved worktree still exists: $path - STOP"; exit 1; }
      ;;
  esac
done < ~/mv-worktrees.tsv

rm -rf ~/mv/main-merge ~/mv/.git ~/mv/.agents ~/mv/.codex
if [ -d ~/mv ] && [ -z "$(find ~/mv -mindepth 1 2>/dev/null)" ]; then
  rmdir ~/mv
elif [ -d ~/mv ]; then
  echo "~/mv not empty - inspect before removing:"
  find ~/mv -maxdepth 2 -mindepth 1 -print
fi

( cd ~/memoria-vault/main && pre-commit install )
```

Do not blindly `rm -rf ~/mv`. The plan only removes exact known cruft after moved
worktrees are gone.

### 9. Phase B - Path Reference PR

```bash
cd ~/memoria-vault/main
git worktree add ../worktrees/layout-paths -b fix/layout-paths origin/main
cd ../worktrees/layout-paths

git grep -n \
  -e '~/mv/' \
  -e '/home/eranr/mv/' \
  -e 'Memoria-test' \
  -e '~/memoria-vault' \
  -e 'scratch/releases' \
  -- . ':!scratch/'

# Edit whatever the grep surfaces:
# - AGENTS.md: main path, scratch path, worktree parent, sandbox path.
# - scripts/refresh-test-vault.sh: default sandbox path.
# - scripts/status_doctor.py: remove dead main-side scratch/releases scan.
# - any other current tracked references found by grep.

pre-commit run --all-files
bash scripts/test.sh all
git push -u origin fix/layout-paths
gh pr create --base main --fill
gh pr checks <n> --watch
```

Freeze remains in effect until this PR merges.

### 10. Phase C - Local Follow-Up

After Phase B merges:

```bash
git -C ~/memoria-vault/main branch -vv
git -C ~/memoria-vault/scratch branch -vv
git -C ~/memoria-vault/main worktree list
```

Update shell aliases, editor workspaces, and habits that still point at
`~/memoria-vault` as a checkout or `~/mv` as the worktree parent.

## 6. Validation And Acceptance

- **Container shape:** `find ~/memoria-vault -maxdepth 1 -mindepth 1 -printf '%f\n'`
  shows `main`, `scratch`, `worktrees`, and `sandbox`; it does not show `.bare` or
  root `.git`.
- **Main is normal Git:** `git -C ~/memoria-vault/main status --short --branch`
  works and `git -C ~/memoria-vault/main rev-parse --absolute-git-dir` points inside
  `~/memoria-vault/main/.git`.
- **Scratch is normal Git:** `git -C ~/memoria-vault/scratch status --short --branch`
  works and its git dir is `~/memoria-vault/scratch/.git`.
- **Feature worktrees resolve:** `git -C ~/memoria-vault/main worktree list` lists
  feature worktrees under `~/memoria-vault/worktrees/` and no old `~/mv/...` paths.
- **Sandbox is outside main/scratch Git discovery:** `git -C ~/memoria-vault/sandbox
  rev-parse --show-toplevel` fails, or returns `~/memoria-vault/sandbox`; it must not
  return `~/memoria-vault/main` or `~/memoria-vault/scratch`.
- **No branch refs lost:** every line in `~/mv-refs-manifest.txt` resolves to the
  same commit or a descendant.
- **Repo healthy:** `bash ~/memoria-vault/main/scripts/test.sh all` passes.
- **Path docs fixed:** Phase B grep returns only intentional/historical mentions.

## 7. Recovery

- Before step 8, rollback is just moving directories back:

  ```bash
  mv ~/memoria-vault-new/main ~/memoria-vault
  # Move any feature worktrees back using ~/mv-worktrees.tsv if needed.
  ```

- After step 8, `~/memoria-vault/main/.git` is the original Git directory moved
  whole. `~/memoria-vault-git-backup` is still available as an extra object-store
  backup. Keep it until `test.sh all`, `git fetch`, and one push cycle succeed from
  the new layout.

## 8. Progress

- [ ] Scratch de-nested and pushed.
- [ ] Quiet-window preflight clean: all worktrees clean, no stashes, no gateway
      process, current refs/worktrees captured.
- [ ] Main moved whole to `~/memoria-vault/main`.
- [ ] Scratch created as independent checkout at `~/memoria-vault/scratch`.
- [ ] Feature worktrees moved under `~/memoria-vault/worktrees/`.
- [ ] Sandbox moved to `~/memoria-vault/sandbox`.
- [ ] Malformed UNC `.codex` cruft removed or proven absent.
- [ ] Phase B path-reference PR merged.
- [ ] Full validation passes.
- [ ] Backup removed after successful fetch/push cycle.
- [ ] Close-out: this plan deleted per ExecPlan lifecycle.

## 9. Execution Log

- 2026-07-04 - Replaced the `.bare` target with normal `main/` and `scratch/`
  checkouts. Reason: the `.bare` root `.git` convenience pointer made sandbox Git
  discovery wrong and created more migration risk than it removed. Moving the current
  main checkout whole also preserves ignored local data without a fragile preserve
  whitelist.

## 10. Notes

- Branch names can be directory paths. A branch `fix/foo` should live at
  `worktrees/fix/foo`; do not sanitize it to `fix_foo`.
- The old `scratch/releases/...` main-side doctor scan is already dead after scratch
  became an orphan branch. Remove it; do not retarget it to `releases`.
- Do not hardcode deleted workflow files in Phase B. Let `git grep` own the target
  list.
