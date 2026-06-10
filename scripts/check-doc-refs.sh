#!/usr/bin/env bash
# check-doc-refs.sh — verify docs/ references in staged/passed files.
#
# Pre-commit passes the list of changed files as arguments.
# Checks:
#   4a. bare repo-relative docs/<path>.md refs must point to an existing file
#   4b. GitHub Pages URLs must map to a real docs file
#   4c. github blob URLs for docs/ are banned (use Pages URLs instead)
#
# Exit 1 on any failure.

PAGES="https://eranroseman.github.io/memoria-vault/"

fail=0

for f in "$@"; do
  [ -f "$f" ] || continue

  # 4a. bare repo-relative docs/<path>.md must exist
  while IFS= read -r ref; do
    [ -f "$ref" ] || { echo "check-doc-refs: $f -> missing $ref" >&2; fail=1; }
  done < <(grep -oE 'docs/[A-Za-z0-9/_.-]+\.md' "$f" | sort -u)

  # 4b. GitHub Pages URL must map to a real docs file (strip #anchor, trailing /)
  while IFS= read -r url; do
    rel="${url#${PAGES}}"
    rel="${rel%%#*}"   # strip anchor
    rel="${rel%/}"     # strip trailing slash
    [ -f "docs/$rel.md" ] || [ -f "docs/$rel/index.md" ] || [ -f "docs/$rel/README.md" ] \
      || { echo "check-doc-refs: $f -> Pages URL with no docs target: $url" >&2; fail=1; }
  done < <(grep -oE "https://eranroseman\.github\.io/memoria-vault/[A-Za-z0-9/_-]+" "$f" | sort -u)

  # 4c. github blob URLs for docs/ are banned — convention is Pages URLs only
  if grep -q 'github\.com/eranroseman/memoria-vault/blob/main/docs/' "$f"; then
    echo "check-doc-refs: $f uses a github blob URL for docs/ — use the Pages URL instead" >&2
    fail=1
  fi
done

exit "$fail"
