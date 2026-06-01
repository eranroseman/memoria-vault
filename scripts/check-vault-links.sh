#!/usr/bin/env bash
# Verify every docs/ reference under vault/ resolves.
#
# vault/ ships to the runtime WITHOUT the docs/ tree, so vault files must
# reference Memoria's docs via absolute GitHub Pages URLs that map to a real docs
# file. Bare docs/<path>.md mentions (a drift-detector's scan inputs) must also
# name a real file. github blob URLs are banned (convention: Pages URLs only).
# External Hermes docs (hermes-agent.nousresearch.com/docs/...) carry no `.md`
# and are naturally skipped.
#
# Scans the whole vault/ tree — this is the CI backstop for the per-diff
# .githooks/pre-commit guard, which programmatic commits (obsidian-git
# auto-backup) and --no-verify bypass.
set -uo pipefail

PAGES="https://eranroseman.github.io/memoria-vault/"
fail=0

while IFS= read -r f; do
  # bare repo-relative docs/<path>.md must exist
  while IFS= read -r ref; do
    [ -n "$ref" ] || continue
    [ -f "$ref" ] || { echo "::error file=$f::missing doc reference: $ref"; fail=1; }
  done < <(grep -oE 'docs/[A-Za-z0-9/_.-]+\.md' "$f" 2>/dev/null | sort -u)

  # GitHub Pages URL must map to a real docs file
  while IFS= read -r url; do
    [ -n "$url" ] || continue
    rel="${url#"$PAGES"}"; rel="${rel%/}"
    if [ ! -f "docs/$rel.md" ] && [ ! -f "docs/$rel/index.md" ] && [ ! -f "docs/$rel/README.md" ]; then
      echo "::error file=$f::Pages URL with no docs target: $url"; fail=1
    fi
  done < <(grep -oE "${PAGES}[A-Za-z0-9/_-]+" "$f" 2>/dev/null | sort -u)

  # github blob URLs for docs/ are banned
  if grep -q 'github.com/eranroseman/memoria-vault/blob/main/docs/' "$f" 2>/dev/null; then
    echo "::error file=$f::uses a github blob URL for docs/ — use the Pages URL instead"; fail=1
  fi
done < <(find vault -type f \( -name '*.md' -o -name '*.py' -o -name '*.yaml' -o -name '*.yml' \) \
           -not -path 'vault/.obsidian/*')

if [ "$fail" -ne 0 ]; then
  echo "docs-links: FAILED — fix the references above (vault/ must use Pages URLs that resolve)."
  exit 1
fi
echo "docs-links: OK — all vault/ docs references resolve."
