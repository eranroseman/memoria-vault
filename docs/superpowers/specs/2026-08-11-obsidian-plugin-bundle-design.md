# Obsidian Plugin Bundle Design

## Goal

Ship a Memoria Obsidian plugin that desktop Obsidian can load, and prevent a
Node-only test from masking the same loader failure again.

## Problem

The seeded `main.js` imports five sibling files with `require("./…")`.
Desktop Obsidian evaluates the entrypoint with its renderer loader, where those
relative imports resolve from Electron rather than the plugin directory. The
files are present, but Obsidian 1.12 reports `Cannot find module './schema'`.

The current package test loads the entrypoint through ordinary Node resolution
after seeding every sibling module. It therefore proves a different loader
contract than Obsidian uses.

## Scope

The corrective PR will:

- make `packages/memoria-obsidian/` the sole source home for the plugin;
- use esbuild to emit one CommonJS `main.js` into the workspace seed;
- retain `manifest.json` and `styles.css` as release artifacts;
- copy only those three files into initialized vaults;
- add a regression test that loads the emitted entrypoint without local helper
  files; and
- correct the wizard's plugin-vault command to use `init --workspace … --yes`.

It will not change plugin behavior, alter an existing vault automatically, or
add a second plugin implementation. A PI can recreate the explicitly
disposable manual-test vault after the corrected artifact lands.

## Architecture

### Source and artifact boundary

`packages/memoria-obsidian/src/` will hold `main.js` and its pure helper
modules. `packages/memoria-obsidian/scripts/build.mjs` will bundle the entry
module with esbuild and write the generated `main.js` to
`src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/`.
The same build step will copy the manifest and stylesheet from the package
source to that release directory.

The generated entrypoint uses CommonJS. It bundles Memoria's local modules,
leaves `obsidian` external for the host to provide, and leaves Node built-ins
such as `child_process` external. The workspace bundle roster will contain the
generated entrypoint, manifest, and stylesheet only.

### Build contract

`esbuild` will be a development dependency of the plugin package. The package
will expose a build command and a check mode that compares generated output
with the committed workspace seed. This keeps the checked-in seed—the artifact
that `memoria init` installs—reviewable and prevents source/artifact drift.

### Regression proof

The package test will copy only the generated `main.js` to a temporary plugin
directory. A Node host stub will provide `obsidian` while ordinary local module
resolution remains unavailable. Loading the entrypoint must export the plugin
class and run `onload()` without attempting a `require("./…")` import.

Existing helper-module tests will import the canonical package source. Bundle,
CLI, installer, provenance, and fixture assertions will describe the reduced
three-file runtime roster. The wizard test will assert the corrected
`--workspace` command.

## Failure handling and acceptance

If the build output is stale, the check command fails before a release artifact
can be committed. If the generated entrypoint retains a local runtime import,
the isolated-loader test fails. Desktop Obsidian 1.12 is the manual acceptance
host: after a fresh disposable-vault initialization, enabling Memoria must load
without the `./schema` error before the wizard proceeds to connection checks.

## Validation

Run the focused plugin and wizard tests, the build-drift check, and the
repository verification gate. The known local `mcp` environment mismatch is
tracked separately; CI's required `verify` and `gitleaks` checks remain the
merge evidence.
