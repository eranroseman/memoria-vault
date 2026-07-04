# Local LLM Installed-System Testing Design

## Goal

Prove Memoria works as an installed CLI system without making normal PRs depend
on Ollama, Obsidian, or external providers.

Assumption: `/home/eranr/Memoria-test` is disposable. Tests use fresh run
directories under it and reinstall from the current checkout.

## Test Levels

| Level | Purpose | Normal cadence |
| --- | --- | --- |
| `static` | lint, format, schema, docs refs, ADR index, workflow safety | every PR |
| `unit` | deterministic Python behavior | every PR |
| `contract` | CLI, operations, manifests, templates, projections | every PR |
| `package` | build/install artifact and offline e2e smoke | package-facing PRs, release PRs |
| `install` | fresh disposable vault install plus CLI wiring | nightly, release candidate |
| `runtime-local` | installed CLI workflow against a local LLM | nightly, release candidate |
| `live` | real external services/providers | manual or scheduled only |

`install` and `runtime-local` are the new confidence layers. They do not replace
the existing fast source gate.

## Local LLM Contract

Use an OpenAI-compatible local endpoint:

```text
provider: custom
base_url: http://127.0.0.1:11434/v1
model: memoria-qwen2.5:7b-64k
context_length: 65536
```

Required preflight:

```bash
curl -fsS http://127.0.0.1:11434/v1/models
ollama list
```

The gate should fail early if the configured model is absent.

## Install Gate

Command shape:

```bash
TEST_VAULT=/home/eranr/Memoria-test/vault-local-installed
MEMORIA_ENV=test \
MEMORIA_MODEL_PROVIDER=custom \
MEMORIA_MODEL_BASE_URL=http://127.0.0.1:11434/v1 \
MEMORIA_MODEL_NAME=memoria-qwen2.5:7b-64k \
MEMORIA_MODEL_CONTEXT_LENGTH=65536 \
  bash scripts/install.sh --vault "$TEST_VAULT" --no-apps --yes
```

Assertions:

- vault skeleton exists;
- `.memoria/golden/manifest.json` exists;
- `.memoria/.venv/bin/python` imports `memoria_vault` and `yaml`;
- installed CLI imports without Obsidian or external-provider configuration;
- local-provider config points at the local LLM endpoint;
- git hooks are wired when the vault is a git repo;
- golden restore reports no drift.

## Runtime-Local Gate

Run after `install`.

Command shape:

```bash
TEST_VAULT=/home/eranr/Memoria-test/vault-local-installed
MEMORIA_LOCAL_MODEL_PROVIDER=custom \
MEMORIA_LOCAL_MODEL_BASE_URL=http://127.0.0.1:11434/v1 \
MEMORIA_LOCAL_MODEL_NAME=memoria-qwen2.5:7b-64k \
MEMORIA_LOCAL_MODEL_CONTEXT_LENGTH=65536 \
OPENAI_API_KEY=dummy \
  bash scripts/test-local-installed.sh --vault "$TEST_VAULT" --real-model
```

Assertions:

- CLI dispatch reaches the local LLM;
- the installed `memoria` command loads from the disposable vault;
- forbidden direct write through Memoria operations is denied;
- audit row is appended with a task id;
- no forbidden artifact is created.

Do not assert generated prose. Runtime-local proves wiring and policy behavior,
not output quality.

## Release Cadence

```text
every PR:         static + unit + contract
package PR:       package
nightly:          install + runtime-local
release candidate: static + unit + contract + package + install + runtime-local
manual only:      live
```

## Notes

- Keep `/home/eranr/Memoria-test` disposable; never preserve state across gates.
- Prefer reinstall over repair. A dirty install target is test pollution.
- Keep Obsidian GUI validation separate unless the test explicitly needs GUI
  rendering; headless install/runtime checks should stay CLI-first.
