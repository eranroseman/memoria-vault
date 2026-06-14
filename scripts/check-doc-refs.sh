#!/usr/bin/env bash
# check-doc-refs.sh — verify docs/ references in staged/passed files.
#
# Pre-commit passes the list of changed files as arguments.
# Checks:
#   4a. bare repo-relative docs/<path>.md refs must point to an existing file
#   4b. GitHub Pages URLs must map to a real docs file
#   4c. github blob/tree URLs for *published* docs/ are banned (use Pages URLs);
#       the build-excluded folders are exempt — they have no Pages route.
#
# Exit 1 on any failure.

PAGES="https://eranroseman.github.io/memoria-vault/"

# Folders build-excluded from the Pages site — keep in sync with the `exclude:`
# list in docs/_config.yml. Links to these use GitHub blob/tree URLs.
EXCLUDED='(contributing|releasing|testing)'

fail=0

for f in "$@"; do
  [ -f "$f" ] || continue
  case "$f" in
    tests/*) continue ;;  # tests contain synthetic paths that exercise validators
  esac

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

  # 4c. github blob/tree URLs for *published* docs/ are banned (use Pages URLs).
  #     Build-excluded folders ($EXCLUDED) have no Pages route, so GitHub URLs to
  #     them are allowed; flag any GitHub docs/ URL that is NOT under an excluded path.
  if grep -oE 'github\.com/eranroseman/memoria-vault/(blob|tree)/main/docs/[A-Za-z0-9/_.-]*' "$f" \
       | grep -qvE "/(blob|tree)/main/docs/${EXCLUDED}(/|$)"; then
    echo "check-doc-refs: $f uses a github URL for a published docs/ path — use the Pages URL instead" >&2
    fail=1
  fi
done

exit "$fail"
