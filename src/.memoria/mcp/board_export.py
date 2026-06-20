#!/usr/bin/env python3
"""Board exporter -- project the Hermes Kanban into Dataview-queryable files and
append the per-card telemetry time-series.

The authoritative board is the Hermes built-in Kanban (~/.hermes/kanban.db).
Obsidian's Dataview cannot query that database, so this script writes read-only
projections the dashboards consume, plus append-only event logs the metrics
aggregator and any publication analysis read (see docs/reference/telemetry.md):

  system/board/<task_id>.md          one markdown file per live card  (board-state dashboard)
  system/logs/board-state.jsonl   per-lane queue-depth snapshot, one line per run (status line)
  system/logs/board-transitions.jsonl  per-card state/review transitions (time-series)
  system/logs/disposition.jsonl   accept | edit | reject per review decision (QuickAdd review action)
  system/logs/cost.jsonl          API spend + token counts per card at completion
  system/logs/cost-misses.jsonl   completion rows whose Hermes session join could not be completed
  system/logs/blind-review-samples.jsonl  deterministic sample requests for blind re-review
  inbox/work-prompt-review-*.md   ONE review prompt per card that reaches `done`
                                  (the Inbox is the PI's slice of the board, ADR-51)

Transitions/cost are computed by diffing this run's board against the previous run,
cached in `system/logs/.board-state-cache.json`. Source of truth:
`hermes kanban list --json` (or `--from-json <file>` for tests/offline). Cost rows
join completed cards to Hermes per-profile `state.db` session rows through
`hermes kanban show <id> --json` -> `runs[].metadata.worker_session_id`.
The export is ONE-WAY (board -> files). Run on a cron cadence (~60s); the Linter
owns rotation/cleanup of the projected files and logs.

    python board_export.py --vault <path>                  # read `hermes kanban list --json`
    python board_export.py --vault <path> --from-json cards.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Direct cron/script execution may run before an editable install is active.
_RUNTIME_ROOT = Path(__file__).resolve().parent.parent
_REPO_DIR = Path(__file__).resolve().parents[3]
for _path in (_RUNTIME_ROOT, _REPO_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from _shared import resolve_vault
from board_export_common import (
    BLIND_REVIEW_RELPATH,
    BOARD_RELDIR,
    COST_MISSES_RELPATH,
    COST_RELPATH,
    DISPOSITION_RELPATH,
    LIVE_STATUSES,
    REQUIRED_SESSION_COLUMNS,
    REVIEW_QUEUE_STATES,
    SNAPSHOT_RELPATH,
    STATE_CACHE_RELPATH,
    TERMINAL_REVIEW,
    TRANSITIONS_RELPATH,
    _first,
    _iso_ts,
    _metadata,
    _metadata_value,
    load_cards,
    normalize,
    worker_session_ids,
)
from board_export_cost import (
    CostDoctorError,
    HermesCostLookup,
    _hermes_home,
    cost_event_from_session,
    cost_miss,
    load_card_detail,
    read_session_row,
    run_cost_doctor,
    state_db_for_lane,
    validate_session_schema,
)
from board_export_events import (
    REVIEW_PROMPT_FRESH_SECONDS,
    _recently_done,
    compute_events,
    export_events,
    export_review_prompts,
    load_state_cache,
    newly_done,
    save_state_cache,
    should_sample_blind_review,
)
from board_export_projection import (
    _yaml_scalar,
    board_snapshot,
    card_markdown,
    export_markdown,
    export_snapshot,
)


def run_export(
    vault: Path, from_json: Path | None = None, hermes_home: Path | str | None = None
) -> dict:
    cards = load_cards(from_json)
    prev = load_state_cache(vault)
    cost_lookup = None
    if from_json is None:
        run_cost_doctor(hermes_home)
        cost_lookup = HermesCostLookup(hermes_home=hermes_home)
    events = export_events(vault, prev, cards, cost_lookup=cost_lookup)  # diff BEFORE cache update
    prompts = export_review_prompts(vault, prev, cards)
    exported = export_markdown(vault, cards)
    snap = export_snapshot(vault, cards)
    save_state_cache(vault, cards)
    return {
        "exported_cards": len(exported),
        "snapshot": snap["totals"],
        "events": events,
        "review_prompts": prompts,
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--vault", help="vault root")
    ap.add_argument(
        "--from-json",
        type=Path,
        help="read cards from a JSON file instead of `hermes kanban list --json`",
    )
    ap.add_argument(
        "--hermes-home",
        type=Path,
        help="Hermes home directory (default: $HERMES_HOME or ~/.hermes)",
    )
    ap.add_argument(
        "--cost-doctor",
        action="store_true",
        help="validate Hermes session-store cost capture and exit",
    )
    args = ap.parse_args()

    if args.cost_doctor:
        try:
            print(json.dumps(run_cost_doctor(args.hermes_home), indent=2))
        except CostDoctorError as exc:
            sys.exit(f"[board_export] cost doctor failed: {exc}")
        return

    if not args.vault:
        ap.error("provide --vault <path>")
    vault = resolve_vault(args.vault)

    try:
        result = run_export(vault, args.from_json, hermes_home=args.hermes_home)
    except FileNotFoundError:
        sys.exit("`hermes` not found on PATH (and no --from-json given).")
    except subprocess.CalledProcessError as exc:
        sys.exit(f"`hermes kanban list --json` failed (exit {exc.returncode}): {exc.stderr}")
    except CostDoctorError as exc:
        sys.exit(f"[board_export] cost doctor failed: {exc}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
