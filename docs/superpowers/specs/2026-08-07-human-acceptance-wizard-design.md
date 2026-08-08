# Human Acceptance Wizard Design

## Goal

Create one executable, one-run Bash wizard for the three remaining human-only acceptance checks: U3-PLUG.11, U3-CANVAS.5, and LOOP.13.

## Scope

The wizard lives at `scripts/human-acceptance-wizard.sh`. It guides a PI through the checks in dependency order, displays the authoritative commands and expected evidence, pauses for manual actions, and records the PI's observations in a local run log.

It does not drive Obsidian, select or export licensed Zotero records, enter credentials, run commands that mutate a vault, choose a triage disposition, or make a stop decision. It also never prints or stores a handshake token.

## Interaction model

The wizard uses the shared wizard template unchanged above its `STAGES` marker. Its authored section adds a `--section` selector for `plugin`, `canvas`, `loop13`, or `all`; each invocation writes to a fresh private temporary Markdown log unless `RUN_LOG` names a durable path.

Each focused stage states its preconditions, shows the command or desktop path the PI must use, asks the PI to record the observed outcome, and pauses. Stages that can enqueue a durable change or delete a disposable vault require an explicit confirmation. A failure or a justified stop remains a recorded result, never a reason to claim a green run.

## Stage structure

The `plugin` section covers the disposable-vault connection, settings, token non-persistence, Attention pane, keyboard and queue behavior, `rebuttal` relation completion, recovery states, theme adaptation, polling cadence, and cleanup.

The `canvas` section covers the generated-canvas banner, scratch fork, one manually drawn `supports` edge, the diverged badge, edge graduation, and proof that the plugin made no direct vault write.

The `loop13` section covers licensed Zotero inputs, a fresh real vault, the seeded-error gate, time to first answer, frozen retrieval fixtures, the 10-work stage, human triage and instrumentation proof, the stop decision, the conditional 100-work stage, Phase 2 rehearsal, and the PI-authored acceptance record.

## Evidence and safety

The run log is a working aid. The PI transfers the Obsidian outcomes to the relevant PR description and writes the final LOOP.13 record at `docs/superpowers/specs/<date>-staged-import-acceptance-run.md`. The script may provide a checklist for those final steps, but it must not author findings, stop reasons, or a commit on the PI's behalf.

The wizard records no secrets. It treats real-vault paths, Zotero exports, provider access, and human judgment as PI-owned inputs. It names plan ambiguities rather than inventing an argument, a UI control, a retrieval fixture, or a decision-rule schema.

## Validation

Validate the generated script with `bash -n` and ShellCheck when available. Statically trace every manual requirement from the three plan tasks to a wizard stage. The full repository gate is outside this change because the local environment lacks the required `mcp>=2,<3` optional dependency.
