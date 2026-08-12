# Seed-install reliability design

**Issue:** #1820
**Status:** implemented; beta.2 review tracked in #1822
**Related:** #1702, #1822

## Problem

`memoria seed install` must work in a normal installation, but the beta.1
runtime omits its PDF parser. When every row fails, the worker stores only the
row IDs, so a PI cannot see why a real-vault install failed. Four seeded PMC
records now resolve to upstream package URLs that return 404, and the original
Frontiers URL redirects. The existing resolver intentionally rejects redirects.

The repair keeps that security boundary. It makes the parser a standard runtime
dependency, replaces broken seed endpoints with pinned direct PDFs, and preserves
per-row failure evidence when an install has no usable rows.

## Decisions

### Standard PDF parser

Add `PyMuPDF>=1.24,<2` to the default project dependencies. This is the
PI-approved AGPL route for beta.1. #1822 records the required beta.2 review of
licensing, native-parser exposure, limits, and alternatives.

`stage_pdf_source()` must reject raw PDF input larger than 32 MiB before it
hands bytes to PyMuPDF. The existing limits remain: at most 1,000 pages and
8 MiB of extracted UTF-8 text. If the installed environment is inconsistent,
the error must say that the PyMuPDF runtime dependency is unavailable and that
the user should reinstall Memoria.

This change prevents a normal installation from failing all PDF captures only
because a required parser is absent. It does not make arbitrary PDFs safe: the
raw-byte, page-count, and extracted-text limits remain the worker boundary.

### Seed sources and network policy

Keep the resolver's current no-redirect behavior. It must continue to validate,
authorize, and fetch every URL itself, using HTTPS, the default port,
credential-free URLs, and safe paths. A 3xx response remains a row failure; no
generic redirect support is added.

Replace the four Frontiers rows that now need a redirect or a stale PMC
artifact with their verified, redirect-free publisher PDF URLs:

| Existing row | Direct PDF URL |
| --- | --- |
| `chen-2018-undesirable-difficulty` | `https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2018.01483/pdf` |
| `moreira-2019-retrieval-practice` | `https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2019.00005/pdf` |
| `ose-askvik-2020-handwriting` | `https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2020.01810/pdf` |
| `mirzababaei-2021-toulmin-agent` | `https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2021.645516/pdf` |

Replace the unavailable Morrison row with an honest new record, rather than
reusing its identifier for another paper:

| Field | Value |
| --- | --- |
| ID | `hu-luo-fleming-2019-metamemory-offloading` |
| Title | *A role for metamemory in cognitive offloading* |
| DOI | `10.1016/j.cognition.2019.104012` |
| License | CC BY 4.0 |
| License evidence | `https://discovery.ucl.ac.uk/id/eprint/10077673/` |
| Direct PDF | `https://discovery.ucl.ac.uk/id/eprint/10077673/1/Fleming_A%20role%20for%20metamemory%20in%20cognitive%20offloading_VoR.pdf` |
| Role | External-memory and cognitive-offloading anchor |

The source directly studies choosing external memory versus unaided recall.
Its repository endpoint returns a PDF without a redirect. The manifest keeps its
eight-row corpus and the same license floor.

The provider currently returns HTTP 403 only to the headerless Python request
used by the resolver, while the exact declared URL returns a PDF to the same
redirect-free request with a conventional User-Agent. The seed opener therefore
sends the fixed, non-secret `Memoria/0.1 (+https://github.com/eranroseman/memoria-vault)`
User-Agent. It adds no cookies, credentials, referer, Accept header, redirect
handling, retry, or destination authority; canonicalization, authorization,
limits, and PDF validation are unchanged.

The capability documents must replace the broad Frontiers `/articles/` prefix
with only the three listed `/journals/<journal>/articles/` prefixes, and add
the single UCL repository-file prefix. The PMC OA prefixes remain for normal user
imports, but no shipped seed row depends on their currently stale artifacts.

### Release-time source preflight

Add a marked live check for the shipped manifest. It is not part of the normal
PR gate. On demand, it must resolve each manifest row through the production
resolver with the production capability policy and report, for every row:

- the row ID;
- every requested canonical URL;
- whether a PDF was admitted; and
- the bounded failure diagnostic when it was not.

The command or test must neither write a vault nor mask a source failure. It is
the release/seed-refresh guard that detects future provider drift before a
real-vault onboarding run does.

### Durable all-failed diagnostics

Keep successful and partial installs unchanged: their result contains
`admitted`, `skipped`, `failed`, `notices`, and telemetry. An install with
zero admitted and zero skipped rows must still become a failed worker request,
not a successful result with an error field.

Introduce a seed-specific exception that carries the already collected
diagnostic payload. The worker stores that payload under `job.diagnostics` when
it marks the request failed. It contains the three lists `admitted`, `skipped`,
and `failed`. Each `failed` item retains the existing `{id, error}` shape, and
its error is truncated to 1,024 UTF-8 bytes. The failed CLI result and
`memoria request show` expose the same payload.

Error text can contain remote or file-derived strings. The request-read
sanitizer must neutralize recursively within `job.diagnostics`, as it already
does for `error`. The failed job stores only the bounded diagnostic text; no
CLI, HTTP, or MCP request-read path may serve it unneutralized.

For non-JSON CLI output, print every failed-row diagnostic before the final
failure line. For JSON output, preserve the standard `ok: false` envelope and
put the diagnostics in `result.diagnostics`.

## Implementation boundaries

- Do not add a redirect-following mechanism, a redirect allowlist, or an
  unbounded provider resolver.
- Do not loosen the manifest license floor or silently skip a broken source.
- Do not add PyMuPDF to `requirements-dev.txt`; it belongs in the installed
  runtime dependency set.
- Do not change the existing PMC OA resolver. The seed corpus stops relying on
  its currently stale records, while ordinary PMC imports retain their bounded
  two-hop behavior.
- Do not use cookies, browser impersonation, credentials, referer, or redirect
  following to accommodate a provider. The one static seed User-Agent is the
  complete compatibility allowance.
- Do not treat a process exit code as the seeded-error verdict during #1702.
  Its JSON `result.passed` remains the import gate.

## Test and verification design

The implementation plan must include tests before each behavior change:

1. Assert that package metadata installs a bounded PyMuPDF runtime dependency.
   Exercise a valid local PDF through the real parser, without mocking
   `_extract_pdf_pages`, and retain focused limit tests for raw bytes, pages,
   and extracted text.
2. Pin all eight manifest IDs, identifiers, licenses, methods, and direct URLs.
   Assert the new narrow capability prefixes and reject redirects without a
   second fetch.
3. Use deterministic opener fixtures to prove a full seed install admits every
   manifest row, remains idempotent on rerun, and emits telemetry only after a
   successful first install.
4. Force distinct failures for every row and assert that CLI JSON, CLI text,
   the failed worker job, and `memoria request show` preserve each row's reason.
   Include hostile diagnostic text to prove recursive neutralization.
5. Update the existing floor fixture from a missing-parser refusal to a
   successful valid-PDF capture, regenerating only the affected goldens.
6. Update the ingest and system-action references to describe PyMuPDF as a
   standard runtime dependency and explain the parser limits.
7. Run the marked live source preflight once after implementation and record its
   result in #1820. Run it again during beta.2 as part of #1822; it is not a
   substitute for deterministic CI.
8. Prove the default seed opener sends the fixed User-Agent through a real
   `urllib.request.Request` while retaining `_NoRedirect`.

## Acceptance criteria

- A clean supported Python installation imports `fitz` through the installed
  Memoria package.
- Seed install stays redirect-free and limited to explicit capability prefixes.
- The shipped corpus has eight openly licensed, directly fetchable seed PDFs.
- A full all-failed run gives the PI a durable, safe reason for every row.
- A partial run continues to admit available rows and reports failed rows.
- A valid local PDF capture succeeds in CI, and parser resource limits refuse
  oversized input before native parsing.
- The beta.1 repair and its beta.2 dependency review remain traceable through
  #1820 and #1822.
