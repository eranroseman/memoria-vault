"""Multi-entry splitting for `memoria work import` (O2 spec section 2).

The shipped single-entry builders (`bibtex_capture_payload` /
`csl_capture_payload`, runtime/capture.py) parse exactly one entry and stay
untouched; these splitters cut a multi-entry file into per-entry chunks that
feed them. A BibTeX entry whose container never closes is returned as the
final chunk so the bulk driver can name the failure instead of dropping it.
"""

from __future__ import annotations

import json
import re
from typing import Any

from memoria_vault.runtime.capture import bibtex_capture_payload, csl_capture_payload


def split_bibtex_entries(text: str) -> list[str]:
    """Split BibTeX text on top-level @ boundaries, brace- and paren-aware."""
    entries: list[str] = []
    index = text.find("@")
    while index != -1:
        end = _entry_end(text, index)
        if end is None:
            entries.append(text[index:].strip())
            break
        entries.append(text[index : end + 1].strip())
        index = text.find("@", end + 1)
    return entries


def _entry_end(text: str, start: int) -> int | None:
    """Index of the container close matching this entry's opener, or None.

    A second top-level ``@`` before any opener ends the (malformed) chunk
    just before it; an unclosed container returns None (tail chunk).
    """
    closer = ""
    depth = 0
    for index in range(start + 1, len(text)):
        char = text[index]
        if not closer:
            if char == "{":
                closer, depth = "}", 1
            elif char == "(":
                closer, depth = ")", 1
            elif char == "@":
                return index - 1
        elif char == "{" and closer == "}":
            depth += 1
        elif char == "(" and closer == ")":
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return index
    return None


def split_csl_entries(text: str) -> list[str]:
    """Split CSL-JSON: array -> per-item dumps; single object -> [text]."""
    data = json.loads(text)
    if isinstance(data, dict):
        return [text]
    if isinstance(data, list):
        items: list[str] = []
        for index, item in enumerate(data, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"CSL array item {index} must be a JSON object")
            items.append(json.dumps(item, ensure_ascii=False, sort_keys=True))
        return items
    raise ValueError("CSL import expects a JSON object or array of objects")


_CITEKEY = re.compile(r"@\s*[^({\s][^({]*[{(]\s*([^,\s{}()]+)")


def build_entry_payload(fmt: str, entry_text: str) -> dict[str, Any]:
    """Build one capture-source payload from one split entry chunk."""
    if fmt == "bibtex":
        return bibtex_capture_payload(entry_text)
    item = json.loads(entry_text)
    if not isinstance(item, dict):
        raise ValueError("CSL entry must be a JSON object")
    return csl_capture_payload(item, raw_text=entry_text)


def entry_ref(fmt: str, entry_text: str, index: int) -> str:
    """Name a failed entry: citekey / CSL id when recoverable, else the index."""
    if fmt == "bibtex":
        if match := _CITEKEY.match(entry_text.strip()):
            return match.group(1)
    else:
        try:
            item = json.loads(entry_text)
        except ValueError:
            item = None
        if isinstance(item, dict) and str(item.get("id") or "").strip():
            return str(item["id"])
    return f"entry-{index}"
