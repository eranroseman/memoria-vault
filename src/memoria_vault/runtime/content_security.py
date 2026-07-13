"""Content-layer defenses for untrusted Markdown."""

from __future__ import annotations

import re

_FENCE_OPEN_RE = re.compile(r"^[ \t]{0,3}(?P<fence>`{3,}|~{3,})")
_HTML_TAG_RE = re.compile(r"<(?=[!/?A-Za-z])[^>]*>")
_HTML_OPEN_RE = re.compile(r"<(?=[!/?A-Za-z])")
_IMAGE_EMBED_RE = re.compile(r"!\[\[([^\]\n]*)\]\]")
_INLINE_LINK_RE = re.compile(r"(?P<image>!)?\[([^\]\n]*)\]\(\s*([^\n)]*?)\s*\)")
_REFERENCE_LINK_RE = re.compile(r"(?P<image>!)?\[([^\]\n]+)\]\[([^\]\n]*)\]")
_REFERENCE_DEFINITION_RE = re.compile(
    r"(?m)^(?P<indent>[ \t]{0,3})(?P<label>\[(?:\\.|[^\]\\\n])+\]):"
)
_IMAGE_OPEN_RE = re.compile(r"!\[")
_EXTERNAL_URL_RE = re.compile(
    r"(?<![\w/`:])(?:(?:https?|ftp)://|//|mailto:|www\.)"
    r"[^\s<>{}\[\]()`\"'&]+",
    re.IGNORECASE,
)
_TRAILING_URL_PUNCTUATION = ".,;:!?"


def _code_span(value: str) -> str:
    """Return a code span whose delimiter cannot occur in *value*."""
    longest_run = max((len(run) for run in re.findall(r"`+", value)), default=0)
    delimiter = "`" * (longest_run + 1)
    padding = " " if value.startswith("`") or value.endswith("`") else ""
    return f"{delimiter}{padding}{value}{padding}{delimiter}"


def _replace_inline_link(match: re.Match[str]) -> str:
    label = match.group(2)
    destination = match.group(3).strip()
    if destination.startswith("<") and destination.endswith(">"):
        destination = destination[1:-1]
    prefix = rf"\[{label}]" if match.group("image") else label
    return f"{prefix} ({_code_span(destination)})"


def _replace_reference_link(match: re.Match[str]) -> str:
    label = match.group(2)
    reference = match.group(3) or label
    prefix = rf"\[{label}]" if match.group("image") else label
    return f"{prefix} ({_code_span(reference)})"


def _replace_reference_definition(match: re.Match[str]) -> str:
    return f"{match.group('indent')}\\{match.group('label')}:"


def _replace_external_url(match: re.Match[str]) -> str:
    value = match.group(0)
    trailing = ""
    while value and value[-1] in _TRAILING_URL_PUNCTUATION:
        trailing = value[-1] + trailing
        value = value[:-1]
    return f"{_code_span(value)}{trailing}"


def _neutralize_plain_text(text: str) -> str:
    text = _INLINE_LINK_RE.sub(_replace_inline_link, text)
    text = _REFERENCE_LINK_RE.sub(_replace_reference_link, text)
    text = _REFERENCE_DEFINITION_RE.sub(_replace_reference_definition, text)
    text = _IMAGE_EMBED_RE.sub(r"\\[[\1]]", text)
    text = _IMAGE_OPEN_RE.sub(r"\\[", text)
    text = _HTML_TAG_RE.sub(
        lambda match: match.group(0).replace("<", "&lt;").replace(">", "&gt;"),
        text,
    )
    text = _HTML_OPEN_RE.sub("&lt;", text)
    return _EXTERNAL_URL_RE.sub(_replace_external_url, text)


def _neutralize_inline_text(text: str) -> str:
    """Neutralize non-fenced text while preserving inline code spans."""
    output: list[str] = []
    plain_start = 0
    cursor = 0
    while cursor < len(text):
        if text[cursor] != "`":
            cursor += 1
            continue

        opener_end = cursor + 1
        while opener_end < len(text) and text[opener_end] == "`":
            opener_end += 1
        delimiter = text[cursor:opener_end]
        closing = text.find(delimiter, opener_end)
        while closing != -1 and (
            (closing > 0 and text[closing - 1] == "`")
            or (closing + len(delimiter) < len(text) and text[closing + len(delimiter)] == "`")
        ):
            closing = text.find(delimiter, closing + len(delimiter))
        if closing == -1:
            cursor = opener_end
            continue

        output.append(_neutralize_plain_text(text[plain_start:cursor]))
        closing_end = closing + len(delimiter)
        output.append(text[cursor:closing_end])
        plain_start = closing_end
        cursor = closing_end

    output.append(_neutralize_plain_text(text[plain_start:]))
    return "".join(output)


def neutralize_untrusted_markdown(body: str) -> str:
    """Make machine- or third-party-derived Markdown safe to render.

    Image embeds and raw HTML become inert. Markdown links and external URLs
    become non-clickable code spans. Vault wikilinks and existing inline or
    fenced code remain unchanged. The transformation is idempotent.
    """
    output: list[str] = []
    plain_lines: list[str] = []
    fence_character: str | None = None
    fence_length = 0

    for line in body.splitlines(keepends=True):
        if fence_character is not None:
            output.append(line)
            closing = re.match(
                rf"^[ \t]{{0,3}}{re.escape(fence_character)}"
                rf"{{{fence_length},}}[ \t]*(?:\r?\n)?$",
                line,
            )
            if closing:
                fence_character = None
                fence_length = 0
            continue

        opening = _FENCE_OPEN_RE.match(line)
        if opening:
            output.append(_neutralize_inline_text("".join(plain_lines)))
            plain_lines.clear()
            fence = opening.group("fence")
            fence_character = fence[0]
            fence_length = len(fence)
            output.append(line)
            continue

        plain_lines.append(line)

    output.append(_neutralize_inline_text("".join(plain_lines)))
    return "".join(output)
