---
title: Operation postures
parent: Explanation
nav_order: 3
has_children: true
permalink: /explanation/profiles/
---

# Operation postures

Alpha.15 does not ship installed Hermes profiles. The old profile language maps
to current concepts this way:

| Old profile concept | Alpha.15 replacement |
| --- | --- |
| Co-PI profile | `memoria ask` / `memoria project ask` query flow |
| Background lane profile | Checked operation manifest plus request row |
| Profile skill | Capability manifest or operation implementation |
| Lane override | Operation `allowed_paths` / optional adapter policy |
| Kanban card | Operation request and attention item |

The durable source of truth is now
`src/memoria_vault/product/capabilities/operations/` plus the standalone
CLI/engine. Optional adapters may present chat or board
interfaces, but they must call the same engine and may not become the authority
for capabilities, provider config, or write policy.

## Delegation posture

Delegation is request based in alpha.15. A request can narrow scope through input
refs, output intents, and required checks, but it cannot widen the operation
manifest's authority.

## Related

- Current command surface: [CLI](../../reference/cli.md)
- Operation manifests: [Operations](../../reference/operations.md)
- No installed profiles: [Installed profiles](../../reference/profile-capabilities.md)
