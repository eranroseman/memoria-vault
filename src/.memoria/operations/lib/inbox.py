#!/usr/bin/env python3
"""inbox — the shared Inbox card writer (ADR-51).

Engines and lanes never invent card formats: every `candidate`/`gap`/`flag`/`alert`/
`work-prompt` goes through this one writer, so cards are always schema-shaped.
Proposals carry the honesty body (argument for · against · what tipped it · certainty —
never a verdict); verification cards lead with the finding; work prompts carry the
action + what happened + where to look — also never a verdict.

Usage: python3 inbox.py --self-test
"""

from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

import loudness as loudness_routing

PROPOSAL_TYPES = {"candidate", "gap"}
VERIFICATION_TYPES = {"flag", "alert"}
CERTAINTY = ("confident", "likely", "unsure")
RECOMMENDATION = ("inconclusive", "issues-found", "clean")
LOUDNESS = ("quiet", "notice", "alert", "block")


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:60] or "card"


def _yaml_str(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_proposal(vault: Path, card_type: str, title: str, action: str,
                   argument_for: str, argument_against: str, what_tipped_it: str,
                   certainty: str, raised_by: str, loudness: str = "notice",
                   citekey: str = "", url: str = "") -> Path:
    """Write a candidate/gap card with the honesty body (D49). Returns the path."""
    if card_type not in PROPOSAL_TYPES:
        raise ValueError(f"not a proposal type: {card_type}")
    if certainty not in CERTAINTY:
        raise ValueError(f"certainty must be one of {CERTAINTY}")
    if loudness not in LOUDNESS:
        raise ValueError(f"loudness must be one of {LOUDNESS}")
    today = datetime.date.today().isoformat()
    lines = [
        "---",
        f"title: {_yaml_str(title)}",
        f"type: {card_type}",
        "lifecycle: proposed",
        f"action: {_yaml_str(action)}",
        f"argument_for: {_yaml_str(argument_for)}",
        f"argument_against: {_yaml_str(argument_against)}",
        f"what_tipped_it: {_yaml_str(what_tipped_it)}",
        f"certainty: {certainty}",
    ]
    if citekey:
        lines.append(f"citekey: {_yaml_str(citekey)}")
    if url:
        lines.append(f"url: {_yaml_str(url)}")
    lines += [f"raised_by: {raised_by}", f"loudness: {loudness}",
              f"created: {today}", "---", ""]
    body = (f"# Action\n\n{action}\n\n# For\n\n{argument_for}\n\n"
            f"# Against\n\n{argument_against}\n\n# What tipped it\n\n{what_tipped_it}\n")
    return _write(vault, card_type, title, "\n".join(lines) + "\n" + body, loudness=loudness)


def write_finding(vault: Path, card_type: str, title: str, finding: str,
                  raised_by: str, agent_recommendation: str = "issues-found",
                  target: str = "", citekey: str = "", loudness: str = "alert",
                  evidence: str = "") -> Path:
    """Write a flag/alert card that leads with the finding (ADR-51)."""
    if card_type not in VERIFICATION_TYPES:
        raise ValueError(f"not a verification type: {card_type}")
    if agent_recommendation not in RECOMMENDATION:
        raise ValueError(f"agent_recommendation must be one of {RECOMMENDATION}")
    if loudness not in LOUDNESS:
        raise ValueError(f"loudness must be one of {LOUDNESS}")
    if card_type == "flag" and not (target or citekey):
        raise ValueError("a flag must point at a target or citekey")
    today = datetime.date.today().isoformat()
    lines = [
        "---",
        f"title: {_yaml_str(title)}",
        f"type: {card_type}",
        "lifecycle: proposed",
        f"finding: {_yaml_str(finding)}",
        f"agent_recommendation: {agent_recommendation}",
    ]
    if target:
        lines.append(f"target: {_yaml_str(target)}")
    if citekey:
        lines.append(f"citekey: {_yaml_str(citekey)}")
    lines += [f"raised_by: {raised_by}", f"loudness: {loudness}",
              f"created: {today}", "---", ""]
    body = f"# Finding\n\n{finding}\n"
    if evidence:
        body += f"\n# Evidence\n\n{evidence}\n"
    return _write(vault, card_type, title, "\n".join(lines) + "\n" + body, loudness=loudness)


def write_work_prompt(vault: Path, title: str, action: str, what_happened: str,
                      raised_by: str, target: str = "", task_id: str = "",
                      lane: str = "", loudness: str = "notice",
                      dedupe_slug: str = "") -> Path | None:
    """Write a `work-prompt` card (ADR-51 honesty rules: action + what happened +
    where to look — never a verdict). A prompt must point somewhere: `target`
    (output path) and/or `task_id` (board card). With `dedupe_slug` the filename
    is stable (`work-prompt-<slug>.md`) and an already-present card is left
    untouched — returns None instead of a path (idempotent emit)."""
    if loudness not in LOUDNESS:
        raise ValueError(f"loudness must be one of {LOUDNESS}")
    if not (target or task_id):
        raise ValueError("a work-prompt must point at a target or task_id")
    today = datetime.date.today().isoformat()
    lines = [
        "---",
        f"title: {_yaml_str(title)}",
        "type: work-prompt",
        "lifecycle: proposed",
        f"action: {_yaml_str(action)}",
        f"what_happened: {_yaml_str(what_happened)}",
    ]
    if target:
        lines.append(f"target: {_yaml_str(target)}")
    if task_id:
        lines.append(f"task_id: {_yaml_str(task_id)}")
    if lane:
        lines.append(f"lane: {_yaml_str(lane)}")
    lines += [f"raised_by: {raised_by}", f"loudness: {loudness}",
              f"created: {today}", "---", ""]
    body = f"# Action\n\n{action}\n\n# What happened\n\n{what_happened}\n"
    where = " · ".join(filter(None, (target, task_id and f"board card `{task_id}`")))
    if where:
        body += f"\n# Where to look\n\n{where}\n"
    content = "\n".join(lines) + "\n" + body
    if dedupe_slug:
        inbox = vault / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        path = inbox / f"work-prompt-{_slug(dedupe_slug)}.md"
        if path.exists():
            return None
        path.write_text(content, encoding="utf-8")
        loudness_routing.push_card(vault, path, {"title": title, "loudness": loudness})
        return path
    return _write(vault, "work-prompt", title, content, loudness=loudness)


def _write(vault: Path, card_type: str, title: str, content: str, loudness: str = "notice") -> Path:
    inbox = vault / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    base = f"{card_type}-{_slug(title)}"
    path = inbox / f"{base}.md"
    n = 1
    while path.exists():
        n += 1
        path = inbox / f"{base}-{n}.md"
    path.write_text(content, encoding="utf-8")
    loudness_routing.push_card(vault, path, {"title": title, "loudness": loudness, "type": card_type})
    return path


def _self_test() -> int:
    import tempfile
    failures = 0

    def check(label: str, ok: bool) -> None:
        nonlocal failures
        print(("  ok " if ok else "  FAIL ") + label)
        if not ok:
            failures += 1

    with tempfile.TemporaryDirectory() as td:
        v = Path(td)
        p = write_proposal(v, "candidate", "Smith 2024 on X", "Accept into catalog",
                           "fills the X gap", "venue is low-signal", "the gap outweighs",
                           "likely", "librarian", citekey="@smith2024")
        text = p.read_text(encoding="utf-8")
        check("proposal under inbox/", p.parent.name == "inbox")
        check("honesty fields present", all(k in text for k in (
            "argument_for", "argument_against", "what_tipped_it", "certainty")))
        check("no verdict on proposals", "agent_recommendation" not in text)
        f = write_finding(v, "flag", "Broken citekey", "citekey resolves nowhere",
                          "linter", target="notes/claims/c.md")
        check("finding leads", "# Finding" in f.read_text(encoding="utf-8"))
        dup = write_proposal(v, "candidate", "Smith 2024 on X", "a", "b", "c", "d",
                             "unsure", "librarian")
        check("no overwrite on collision", dup != p)
        try:
            write_finding(v, "flag", "t", "f", "linter")
            check("flag without target rejected", False)
        except ValueError:
            check("flag without target rejected", True)
        wp = write_work_prompt(v, "Review: Draft answer", "Review, then accept or archive",
                               "memoria-writer finished the draft", "board-export",
                               task_id="t_b2", dedupe_slug="review-t-b2")
        check("work-prompt written under inbox/", wp is not None and wp.parent.name == "inbox")
        check("work-prompt carries no verdict",
              "agent_recommendation" not in wp.read_text(encoding="utf-8"))
        again = write_work_prompt(v, "Review: Draft answer", "a", "b", "board-export",
                                  task_id="t_b2", dedupe_slug="review-t-b2")
        check("dedupe_slug makes re-emit a no-op", again is None)
        try:
            write_work_prompt(v, "t", "a", "w", "board-export")
            check("work-prompt without pointer rejected", False)
        except ValueError:
            check("work-prompt without pointer rejected", True)
    print("self-test:", "PASS" if failures == 0 else f"{failures} FAILURE(S)")
    return 1 if failures else 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(_self_test())
    print(__doc__)
