---
title: Explore a topic neighborhood
parent: Knowledge
grand_parent: How-to guides
nav_order: 4
---

# Explore a topic neighborhood

Surface checked claims, questions, tensions, Works, and hubs around a topic
with `memoria explore`.

## Prerequisites

- Checked workspace knowledge relevant to the topic.
- A workspace path.

## Steps

**1. Surface the topic.**

```bash
memoria explore "JITAI receptivity" --workspace .
```

The command is read-only. It ranks checked, displayable retrieval documents,
then expands the graph neighborhood of its seeds.

**2. Use a comparison or narrower slice when useful.**

```bash
memoria explore "JITAI receptivity" --versus "EMA compliance" --depth 2 --workspace .
memoria explore "JITAI receptivity" --project project-alpha --workspace .
```

`--versus` compares two topic neighborhoods. `--project <project>` limits the
result to a checked project slice. The default depth is one hop and the maximum
is two.

**3. Inspect the result.**

Use `--json` for the complete grouped payload or `--trace` to see pipeline
counts. An empty result says what the checked universe did not contain;
unchecked, stale, and gated material remains excluded.

`memoria explore` is not `memoria project explore`: the latter lists candidates
from the exploration channel rather than surfacing this checked topic
neighborhood.

## Verify

- Returned material is from the checked retrieval universe.
- A comparison reports both neighborhoods and their intersection.
- The command does not create a request, journal row, or workspace file.

## Related

- Retrieval details: [Search](../../reference/pipelines-and-io/search.md)
- Exact command and flags: [CLI](../../reference/commands-and-transports/cli.md)
- Engine boundary: [Engine read API](../../reference/commands-and-transports/read-api.md)
