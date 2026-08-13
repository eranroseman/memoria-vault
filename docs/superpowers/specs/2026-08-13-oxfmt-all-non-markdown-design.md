# Oxfmt all-non-Markdown design

- **Date:** 2026-08-13
- **Status:** approved for planning

## Decision

Memoria will format every tracked, Oxfmt-supported non-Markdown file with the
same pinned Oxfmt release in the editor, pre-commit hook, build, and required
gate. This includes configuration, vendored Vale styles, frozen JSON records,
and seeded Obsidian artifacts. Markdown, `.markdown`, and MDX remain outside
the policy because this decision is explicitly non-Markdown and those files
can contain literal command output in fenced blocks.

The policy covers JavaScript and TypeScript; JSON; YAML; TOML; CSS, SCSS, Less,
PostCSS, and WXSS; GraphQL; HTML and Angular component HTML; Vue; Handlebars;
MJML; and Svelte. Svelte support requires the formatter's separately pinned
runtime dependency and enabled Svelte option, even though no Svelte file is
currently tracked.

## Why the build must participate

The Obsidian adapter ships `main.js` and `styles.css` twice: once as source or
fresh esbuild output, and once in `workspace_seed`. Its existing package check
compares those bytes exactly. Formatting the seeded copies after the build
would therefore make the formatter and the build fight each other.

`packages/memoria-obsidian/scripts/build.mjs` will instead use its pinned Oxfmt
API to format the fresh esbuild bundle as `main.js` and the stylesheet as
`styles.css` before it writes or compares either artifact. It will fail with
the formatter's diagnostics if formatting reports an error. The manifest stays
byte-for-byte source data. `npm run check --prefix packages/memoria-obsidian`
therefore remains the single parity check: the committed seed must equal the
canonical formatted build output.

The build reads the root formatter options but does not apply path ignores to
these generated artifacts. Scope selection belongs to the hook; canonicalizing
the release output belongs to the build.

## Formatter policy

The upstream Oxfmt hook labels only JavaScript-family files by default. The
repository configuration will override that selection with the generic file
type and an explicit regex listing the non-Markdown suffixes above. It will
keep filename passing enabled, so unsupported files never reach Oxfmt and a
commit that changes only Python does not cause a formatter error.

`.oxfmtrc.json` will retain only narrow non-source exclusions for disposable
working directories. It will exclude Markdown-family paths and no tracked
non-Markdown repository surface. The hook and the adapter package will each
pin the same Oxfmt and Svelte versions, so the VS Code extension, hook, and
build do not format differently.

## Regression boundaries

The current ownership test will gain a separate formatting-scope assertion. It
will derive supported non-Markdown tracked paths, prove each reaches the Oxfmt
hook, and prove Markdown-family files do not. It will not weaken the existing
YAML, JSON, or CSS ownership checks: formatting is an additional policy, not a
replacement for syntax validation or linting.

The adapter contract tests will prove that committed artifacts remain both
build-current and Oxfmt-clean. The formatter test will use the package-local,
pinned executable rather than a machine-global installation. A tooling test
will pin the hook's broad type policy and the formatter/Svelte version parity.

## Migration and verification

The first canonicalization touches 174 currently tracked inputs; 27 change:
17 YAML, 6 JSON, 1 TOML, 2 CSS, and 1 generated JavaScript bundle. The changes
are intentional, including the vendored Vale styles and the frozen
`paper-review-verdicts.json` record. Structured files must retain equal parsed
values before and after formatting; Vale must still load its vendored rules.

After the formatter canonicalizes source files, the adapter build regenerates
the two seeded release artifacts. Their bytes participate in all 39 floor
goldens, so the implementation will update them only with the existing local
`MEMORIA_FLOOR_UPDATE_GOLDENS=1` workflow, review the digest-only changes, and
rerun the floor suite without that flag.

Acceptance requires a clean manual Oxfmt hook, adapter package check, Vale
hook, focused policy and artifact tests, normal floor suite, and
`python scripts/verify`. The working spec and implementation plan retire after
the completed change has a durable home in the shipped configuration, tests,
and Git history.

## Non-goals

- Format Markdown or MDX.
- Add a local wrapper that duplicates the pre-commit hook's file selection.
- Relax the adapter's byte-parity check or exclude generated release artifacts
  from formatting.
- Treat formatting as a substitute for JSON parsing, yamllint, Vale, or the
  existing package and floor contracts.
