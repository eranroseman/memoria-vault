# MCP Servers

These files are executable adapters between Hermes and Memoria's deterministic
runtime. Keep transport and argument handling thin; reusable policy semantics
belong in the installed `memoria.runtime.policy` package, while operation logic
belongs in `../operations/`.

Every mutating vault operation must pass through the policy MCP and complete its
audit record. Servers should degrade explicitly when optional dependencies or
external services are unavailable, and must never print secrets.

The scripts remain direct executable entry points for Hermes compatibility.
Package imports are bootstrapped from the enclosing `.memoria` directory.
