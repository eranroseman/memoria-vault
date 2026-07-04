# Hermes upgrade notes

alpha.10 starts with Hermes update work. Installed alpha.9 baseline was:

```text
Hermes Agent v0.14.0 (2026.5.16)
```

Upgrade run on 2026-06-22:

```text
Hermes Agent v0.17.0 (2026.6.19) · upstream b1b20270
Project: /home/eranr/.hermes/hermes-agent
Python: 3.11.15
OpenAI SDK: 2.24.0
Up to date
```

Upgrade acceptance:

- `hermes --version` reports the new installed version. Done on 2026-06-22.
- `python src/.memoria/mcp/hermes_contract_doctor.py --vault /home/eranr/Memoria-test --json`
  passes. Done on 2026-06-22 with `ok: true`; warning preserved: dead
  denylist names `code_execution`, `run_command`, `send_message`.
- `python src/.memoria/mcp/board_export.py --cost-doctor` passes. Done on
  2026-06-22 with `ok: true` for `memoria-copi`, `memoria-librarian`, and
  `memoria-writer`.
- Profiles redeploy cleanly to `~/Memoria-test`. Not rerun yet.
- One live direct-tool deny and one Obsidian/MCP smoke pass succeed. Not rerun yet.

Open question from alpha.9 cleanup: after the upgrade, decide whether #859's
Hermes cleanup items still matter: Bitwarden, auxiliary routing, `reasoning_effort`,
and ADR-106 cost capture location.
