---
topic: workflows
---

# Maintain MOCs

**Group.** Maintenance
**Goal.** Create and grow Maps of Content so the claim graph stays navigable.

Other workflows *link to* a MOC ([promote](../upstream/promote.md), [refactor](refactor.md)) but none documents *creating* one. A MOC (`30-synthesis/03-moc/`) is a navigational hub note, authored by the human; agents may surface candidates but never write into the review-gated synthesis zone.

## When to create a MOC

Create one when a cluster of claim-notes crosses the thresholds in [vault/linking-patterns.md](../../../reference/linking-patterns.md): roughly ≥ 15–20 related claims, a recurring topic across ≥ 3 sources, or an orphan cluster the [`open-questions`](../../../explanation/dashboards/open-questions.md) / drift surfaces keep flagging.

## Steps

1. The human (or an agent, as a candidate) notices a cluster that has outgrown ad-hoc links.
2. Human creates a `moc` note in `30-synthesis/03-moc/` from the template.
3. Human links the member claim-notes and sets `scope` / `parent_moc` as needed.
4. As the cluster grows, the human splits a child MOC off or promotes the MOC's anchor claims toward `reference-note`.

## Owners

The **human** authors and curates MOCs (synthesis is a review-gated, human-only zone). Agents may *propose* a MOC or candidate members; the policy MCP degrades any agent write to `30-synthesis/03-moc/` to `dry_run`.

## Commands

No CLI command — performed directly in the vault or via the Obsidian interface.

## Related

- Reference: [vault/linking-patterns.md](../../../reference/linking-patterns.md) — MOC tiers and creation thresholds.
- Note type: [vault/note-types.md](../../../reference/note-types.md) — `moc`.
- Stage: [promote](../upstream/promote.md) — where claims mature toward MOC membership.
