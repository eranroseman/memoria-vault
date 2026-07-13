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
    r"(?<!\\)(?P<label>\[(?:\\[^\r\n]|[^\]\\\r\n]|(?:\r\n?|\n)(?!(?:\r\n?|\n)))+\]):"
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


def markdown_code_span(value: str) -> str:
    """Return a code span that cannot be closed by *value*."""
    return _code_span(value)


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
    return f"\\{match.group('label')}:"


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


def neutralize_untrusted_markdown_fragment(fragment: str) -> str:
    """Make untrusted Markdown safe for interpolation into Markdown scaffolding.

    Unlike :func:`neutralize_untrusted_markdown`, this transform treats
    user-supplied backticks as text. Call it for a fragment that a writer will
    place inside headings, templates, or its own code delimiters.
    """
    return _neutralize_plain_text(fragment.replace("`", "&#96;"))


def _is_escaped_backtick(text: str, index: int) -> bool:
    """Return whether the backtick at *index* is escaped in Markdown source."""
    backslashes = 0
    index -= 1
    while index >= 0 and text[index] == "\\":
        backslashes += 1
        index -= 1
    return bool(backslashes % 2)


def _mask_inline_code_spans(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Replace inline code spans with unique tokens while preserving their source."""
    output: list[str] = []
    spans: list[tuple[str, str]] = []
    marker = "\0"
    while marker in text:
        marker += "\0"
    plain_start = 0
    cursor = 0
    while cursor < len(text):
        if text[cursor] != "`":
            cursor += 1
            continue

        opener_end = cursor + 1
        while opener_end < len(text) and text[opener_end] == "`":
            opener_end += 1
        if _is_escaped_backtick(text, cursor):
            cursor = opener_end
            continue

        delimiter = text[cursor:opener_end]
        closing = -1
        probe = opener_end
        while probe < len(text):
            if text[probe] != "`":
                probe += 1
                continue
            run_end = probe + 1
            while run_end < len(text) and text[run_end] == "`":
                run_end += 1
            if not _is_escaped_backtick(text, probe) and text[probe:run_end] == delimiter:
                closing = probe
                break
            probe = run_end
        if closing == -1:
            output.append(text[plain_start:cursor])
            output.append("&#96;" * len(delimiter))
            plain_start = opener_end
            cursor = opener_end
            continue

        output.append(text[plain_start:cursor])
        closing_end = closing + len(delimiter)
        token = f"<{marker}{len(spans)}{marker}>"
        output.append(token)
        spans.append((token, text[cursor:closing_end]))
        plain_start = closing_end
        cursor = closing_end

    output.append(text[plain_start:])
    return "".join(output), spans


def _neutralize_inline_text(text: str) -> str:
    """Neutralize non-fenced text while preserving inline code spans."""
    masked, spans = _mask_inline_code_spans(text)
    neutralized = _neutralize_plain_text(masked)
    for token, source in spans:
        neutralized = neutralized.replace(token, source)
    return neutralized


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
