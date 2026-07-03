---
title: Configure a profile
parent: Hermes Agent
grand_parent: How-to guides
nav_order: 1
---

# Configure a profile

Alpha.15 does not ship installed Hermes profiles. There is no supported profile
configuration workflow, profile skill directory, lane override package, or
profile-only redeploy command.

To change what the system can do, edit the checked packaged operation manifests
under `src/memoria_vault/product/capabilities/operations/` and the corresponding
CLI/engine code.
Then run the capability and alpha.15 negative gates:

```bash
python -m pytest tests/test_capabilities.py tests/test_operations.py
python scripts/alpha14_negative_gate.py
```

Optional external adapters must wrap the standalone `memoria` CLI/engine. They
must not become the authority for operation manifests, provider config, write
policy, or scheduled work.

## Related

- Current command surface: [CLI](../../reference/cli.md)
- Operation manifests: [Operations](../../reference/operations.md)
- No installed profiles: [Installed profiles](../../reference/profile-capabilities.md)
