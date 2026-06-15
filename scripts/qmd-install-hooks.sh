#!/usr/bin/env bash
# Install (or remove) git hooks that keep the repo-local qmd index fresh.
#
#   bash scripts/qmd-install-hooks.sh            # install
#   bash scripts/qmd-install-hooks.sh --uninstall
#
# The hooks delegate to scripts/qmd-codebase-index.sh (single source of truth) and run it
# in the background, non-blocking (the indexer holds its own lock). They no-op when ./.qmd
# is absent, so installing them is harmless until you build the index. Opt-in: wired only
# when you pass dev-setup.sh --with-hooks, or run this script directly.
#
# Behaviour per event:
#   post-commit / post-merge -> full refresh (BM25 + incremental vectors): `qmd ... --embed`
#   post-checkout (branch switch only) -> BM25 refresh only (no re-embed on branch hops)
set -eu

unset CDPATH
cd "$(dirname -- "$0")/.." || exit 1

note() { printf '  %s\n' "$1"; }

MARKER='# >>> memoria qmd-refresh hook >>>'
HOOKS="$(git rev-parse --git-path hooks 2>/dev/null)" || { note "not a git repo — nothing to do."; exit 0; }
mkdir -p "$HOOKS"

DISPATCHERS="post-commit post-merge post-checkout"

if [ "${1:-}" = "--uninstall" ]; then
  rm -f "$HOOKS/qmd-refresh"
  for h in $DISPATCHERS; do
    if [ -f "$HOOKS/$h" ] && head -n 3 "$HOOKS/$h" | grep -qF "$MARKER"; then
      rm -f "$HOOKS/$h"; note "removed $h"
    fi
  done
  note "qmd refresh hooks uninstalled."
  exit 0
fi

# Shared worker: arg1 = full|bm25. Resolves the repo, no-ops without an index, backgrounds
# the indexer so the commit/checkout returns immediately. Logs to .qmd/refresh.log.
cat > "$HOOKS/qmd-refresh" <<EOF
#!/usr/bin/env sh
$MARKER
ROOT=\$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
[ -d "\$ROOT/.qmd" ] || exit 0
[ -f "\$ROOT/scripts/qmd-codebase-index.sh" ] || exit 0
flag=""
[ "\${1:-full}" = "full" ] && flag="--embed"
( cd "\$ROOT" && bash scripts/qmd-codebase-index.sh \$flag ) </dev/null >>"\$ROOT/.qmd/refresh.log" 2>&1 &
exit 0
EOF
chmod +x "$HOOKS/qmd-refresh"
note "installed shared worker: qmd-refresh"

install_dispatcher() {
  h="$1"; mode="$2"; guard="$3"
  if [ -f "$HOOKS/$h" ] && ! head -n 3 "$HOOKS/$h" | grep -qF "$MARKER"; then
    note "WARNING: $h exists and is not managed by us — left untouched."
    note "  add this line yourself: exec \"\$(dirname \"\$0\")/qmd-refresh\" $mode"
    return
  fi
  {
    printf '#!/usr/bin/env sh\n%s\n' "$MARKER"
    [ -n "$guard" ] && printf '%s\n' "$guard"
    printf 'exec "$(dirname "$0")/qmd-refresh" %s\n' "$mode"
  } > "$HOOKS/$h"
  chmod +x "$HOOKS/$h"
  note "installed $h ($mode)"
}

install_dispatcher post-commit  full ''
install_dispatcher post-merge   full ''
# post-checkout args: $1=prev-HEAD $2=new-HEAD $3=branch-flag (1=branch switch, 0=file checkout)
install_dispatcher post-checkout bm25 '[ "$3" = "1" ] || exit 0'

note "done. The index refreshes in the background after commits/merges/branch switches."
note "(no-op until you build it: bash scripts/qmd-codebase-index.sh --embed)"
