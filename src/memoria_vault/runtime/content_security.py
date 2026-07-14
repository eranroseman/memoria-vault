"""Content-layer defenses for untrusted Markdown."""

from __future__ import annotations

import re
import shlex

_FENCE_OPEN_RE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})")
_NESTED_FENCE_OPEN_RE = re.compile(
    r"^(?P<prefix>(?:[ \t]*(?:(?:>[ \t]*)|(?:[-+*~:][ \t]+)|"
    r"(?:[^\s`~]+[.)][ \t]+))+|[ \t]+))"
    r"(?P<fence>`{3,}|~{3,})(?P<info>[^\r\n]*)(?P<line_ending>\r?\n)?$"
)
_RAW_FORMAT_FENCE_INFO_RE = re.compile(r"^[ \t]*\{[ \t]*=[^ \t}]+[ \t]*\}[ \t]*(?:\r?\n)?$")
_RAW_FORMAT_INLINE_ATTRIBUTE_RE = re.compile(r"\{[ \t]*=[^ \t}]+[ \t]*\}")
_TILDE_FENCE_LANGUAGE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9+._-]*$")
_TILDE_FENCE_ATTRIBUTES_RE = re.compile(
    r"^(?:(?P<language>[A-Za-z0-9][A-Za-z0-9+._-]*)[ \t]+)?"
    r"\{(?P<attributes>[^{}]+)\}$"
)
_TILDE_FENCE_ATTRIBUTE_NAME_RE = re.compile(r"^[A-Za-z_:][A-Za-z0-9_.:-]*$")
_HTML_TAG_RE = re.compile(r"<(?=[!/?A-Za-z])[^>]*>")
_HTML_OPEN_RE = re.compile(r"<(?=[!/?A-Za-z])")
_HTML_BLOCK_OPEN_RE = re.compile(
    r"""(?ix)
    (?:
        <!--
        | <\?
        | <!\[CDATA\[
        | <![A-Z]
        | </?(?:
            address|article|aside|base|basefont|blockquote|body|caption|center|col|
            colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|
            footer|form|h[1-6]|head|header|hr|html|iframe|legend|li|link|main|menu|
            menuitem|nav|noframes|ol|output|p|plaintext|pre|script|search|section|
            style|summary|table|tbody|td|tfoot|th|thead|textarea|title|tr|track|ul|wbr
        )(?=[ \t\r\n/>])
    )
    """
)
_ATX_HEADING_PREFIX_RE = re.compile(r"#{1,6}(?:[ \t]+|$)")
_LIST_PREFIX_RE = re.compile(r"(?:[-+*]|\d{1,9}[.)])[ \t]+")
_THEMATIC_OR_SETEXT_RE = re.compile(r"^[ \t]{0,3}(?:(?:\*[ \t]*){3,}|(?:_[ \t]*){3,}|[-=]+[ \t]*)$")
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


def _markdown_physical_lines(text: str) -> list[str]:
    """Split only physical Markdown LF lines, preserving their endings."""
    return [line for line in re.findall(r"[^\n]*(?:\n|$)", text) if line]


def markdown_code_span(value: str) -> str:
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
    return f"{prefix} ({markdown_code_span(destination)})"


def _replace_reference_link(match: re.Match[str]) -> str:
    label = match.group(2)
    reference = match.group(3) or label
    prefix = rf"\[{label}]" if match.group("image") else label
    return f"{prefix} ({markdown_code_span(reference)})"


def _replace_reference_definition(match: re.Match[str]) -> str:
    return f"\\{match.group('label')}:"


def _replace_external_url(match: re.Match[str]) -> str:
    value = match.group(0)
    trailing = ""
    while value and value[-1] in _TRAILING_URL_PUNCTUATION:
        trailing = value[-1] + trailing
        value = value[:-1]
    return f"{markdown_code_span(value)}{trailing}"


def _neutralize_pandoc_attribute_lists(text: str) -> str:
    """Make all untrusted Pandoc attribute-list openers literal."""
    output: list[str] = []
    copied_until = 0
    for index, character in enumerate(text):
        if character != "{" or _is_escaped_markdown_character(text, index):
            continue
        output.append(text[copied_until:index])
        output.append("\\{")
        copied_until = index + 1
    output.append(text[copied_until:])
    return "".join(output)


def _neutralize_plain_text(text: str) -> str:
    text = _neutralize_pandoc_attribute_lists(text)
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


def _is_escaped_markdown_character(text: str, index: int) -> bool:
    """Return whether the Markdown character at *index* is escaped in source."""
    backslashes = 0
    index -= 1
    while index >= 0 and text[index] == "\\":
        backslashes += 1
        index -= 1
    return bool(backslashes % 2)


def _is_fenced_code_opening(line: str, opening: re.Match[str]) -> bool:
    """Return whether *opening* can be a CommonMark fenced-code opener."""
    return opening.group("fence")[0] != "`" or "`" not in line[opening.end() :]


def _has_regular_tilde_fence_attributes(attributes: str) -> bool:
    """Return whether *attributes* contains only normal fenced-code attributes."""
    try:
        tokens = shlex.split(attributes, comments=False, posix=True)
    except ValueError:
        return False
    if not tokens:
        return False
    for token in tokens:
        if token[:1] in {"#", "."}:
            if not _TILDE_FENCE_ATTRIBUTE_NAME_RE.fullmatch(token[1:]):
                return False
            continue
        name, separator, value = token.partition("=")
        if not (separator and value and _TILDE_FENCE_ATTRIBUTE_NAME_RE.fullmatch(name)):
            return False
    return True


def _has_valid_tilde_fence_info(line: str, opening: re.Match[str]) -> bool:
    """Return whether a tilde fence has a non-raw or exact raw-format header."""
    suffix = line[opening.end() :]
    if _RAW_FORMAT_FENCE_INFO_RE.fullmatch(suffix):
        return True
    info = suffix.rstrip("\r\n").strip(" \t")
    if not info or _TILDE_FENCE_LANGUAGE_RE.fullmatch(info):
        return True
    attributes = _TILDE_FENCE_ATTRIBUTES_RE.fullmatch(info)
    return bool(attributes and _has_regular_tilde_fence_attributes(attributes["attributes"]))


def _tilde_fence_can_start_block(plain_lines: list[str]) -> bool:
    """Return whether a tilde fence is at a Markdown block boundary."""
    return not plain_lines or not plain_lines[-1].strip()


def _markdown_block_line_context(line: str) -> tuple[str, bool]:
    """Return the content after a Markdown block prefix and whether one was found."""
    indentation = min(len(line) - len(line.lstrip(" \t")), 3)
    content = line[indentation:]
    has_block_prefix = False
    while content.startswith(">"):
        has_block_prefix = True
        content = content[1:].lstrip(" \t")
    if content.startswith("|"):
        return content[1:].lstrip(" \t"), True
    for prefix in (_ATX_HEADING_PREFIX_RE, _LIST_PREFIX_RE):
        match = prefix.match(content)
        if match:
            return content[match.end() :], True
    return content, has_block_prefix


def _line_has_unescaped_html_tag(line: str) -> bool:
    return any(
        not _is_escaped_markdown_character(line, match.start())
        for match in _HTML_TAG_RE.finditer(line)
    )


def _line_starts_interrupting_markdown_block(line: str) -> bool:
    """Return whether *line* starts a block that ends the current paragraph."""
    _content, has_block_prefix = _markdown_block_line_context(line)
    fence_opening = _FENCE_OPEN_RE.match(line)
    return bool(
        has_block_prefix
        or (fence_opening and _is_fenced_code_opening(line, fence_opening))
        or _THEMATIC_OR_SETEXT_RE.fullmatch(line)
    )


def _contains_interrupting_html_block(content: str) -> bool:
    """Return whether raw HTML can make a multiline code span parse as blocks."""
    lines = _markdown_physical_lines(f"\0{content}\0")
    has_unescaped_html_tag = False
    has_interrupting_markdown_block = False
    for line in lines:
        block_content, has_block_prefix = _markdown_block_line_context(line)
        if _HTML_OPEN_RE.match(block_content) and (
            _HTML_BLOCK_OPEN_RE.match(block_content) or has_block_prefix
        ):
            return True
        has_unescaped_html_tag |= _line_has_unescaped_html_tag(line)
        has_interrupting_markdown_block |= _line_starts_interrupting_markdown_block(line)
    return has_unescaped_html_tag and (
        any(not line.strip() for line in lines) or has_interrupting_markdown_block
    )


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
        if _is_escaped_markdown_character(text, cursor):
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
            if text[probe:run_end] == delimiter:
                closing = probe
                break
            probe = run_end
        if closing == -1:
            output.append(text[plain_start:cursor])
            output.append("&#96;" * len(delimiter))
            plain_start = opener_end
            cursor = opener_end
            continue

        closing_end = closing + len(delimiter)
        content = text[opener_end:closing]
        if ("\n" in content or "\r" in content) and _contains_interrupting_html_block(content):
            # Markdown blocks can interrupt a would-be multiline code span before
            # raw HTML. Leave these ambiguous spans for the normal escape pass.
            output.append(text[plain_start:cursor])
            output.append("&#96;" * len(delimiter))
            output.append(content.replace("`", "&#96;"))
            output.append("&#96;" * len(delimiter))
            plain_start = closing_end
            cursor = closing_end
            continue
        output.append(text[plain_start:cursor])
        token = f"<{marker}{len(spans)}{marker}>"
        output.append(token)
        spans.append((token, text[cursor:closing_end]))
        raw_attribute = _RAW_FORMAT_INLINE_ATTRIBUTE_RE.match(text, closing_end)
        if raw_attribute:
            output.append("\\")
            output.append(raw_attribute.group())
            plain_start = raw_attribute.end()
            cursor = raw_attribute.end()
            continue
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


def _neutralize_fence_opening(line: str, opening: re.Match[str]) -> str:
    """Strip untrusted Pandoc attributes from a fenced-code opener."""
    suffix = line[opening.end() :]
    info = suffix.rstrip("\r\n").strip(" \t")
    if "{" not in info:
        return line
    line_ending = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
    language = info.partition("{")[0].strip()
    safe_info = language if _TILDE_FENCE_LANGUAGE_RE.fullmatch(language) else "text"
    return f"{line[: opening.end()]}{safe_info}{line_ending}"


def _literalize_fence_opening(line: str, opening: re.Match[str]) -> str:
    """Make an ambiguous fence opener prose before neutralizing its contents."""
    entity = "&#96;" if opening["fence"].startswith("`") else "&#126;"
    return f"{line[: opening.start('fence')]}{entity * len(opening['fence'])}{line[opening.end('fence') :]}"


def _neutralize_nested_fence_opening(line: str) -> str:
    """Make attribute-bearing nested fence openers literal."""
    opening = _NESTED_FENCE_OPEN_RE.match(line)
    if opening is None or "{" not in opening["info"]:
        return line
    return _literalize_fence_opening(line, opening)


def _neutralize_nested_fence_attributes(body: str) -> str:
    """Neutralize attributes on container-nested fence headers before code masking."""
    return "".join(
        _neutralize_nested_fence_opening(line) for line in _markdown_physical_lines(body)
    )


def neutralize_untrusted_markdown(body: str) -> str:
    """Make machine- or third-party-derived Markdown safe to render.

    Image embeds and raw HTML become inert. Markdown links and external URLs
    become non-clickable code spans. Vault wikilinks and existing inline or
    fenced-code content remains unchanged. Pandoc attribute lists become literal,
    and fenced-code attributes are stripped. The transformation is idempotent.
    """
    body = _neutralize_nested_fence_attributes(body)
    output: list[str] = []
    plain_lines: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    fence_lines: list[str] = []

    for line in _markdown_physical_lines(body):
        if fence_character is not None:
            fence_lines.append(line)
            closing = re.match(
                rf"^ {{0,3}}{re.escape(fence_character)}"
                rf"{{{fence_length},}}[ \t]*(?:\r?\n)?$",
                line,
            )
            if closing:
                output.extend(fence_lines)
                fence_character = None
                fence_length = 0
                fence_lines.clear()
            continue

        opening = _FENCE_OPEN_RE.match(line)
        tilde_fence = bool(opening and opening.group("fence")[0] == "~")
        tilde_fence_has_attributes = bool(opening and "{" in line[opening.end() :])
        if (
            opening
            and tilde_fence
            and tilde_fence_has_attributes
            and not _tilde_fence_can_start_block(plain_lines)
        ):
            plain_lines.append(_literalize_fence_opening(line, opening))
            continue
        if (
            opening
            and _is_fenced_code_opening(line, opening)
            and (
                not tilde_fence
                or (
                    _tilde_fence_can_start_block(plain_lines)
                    and (tilde_fence_has_attributes or _has_valid_tilde_fence_info(line, opening))
                )
            )
        ):
            output.append(_neutralize_inline_text("".join(plain_lines)))
            plain_lines.clear()
            fence = opening.group("fence")
            fence_character = fence[0]
            fence_length = len(fence)
            fence_lines.append(_neutralize_fence_opening(line, opening))
            continue

        plain_lines.append(line)

    plain_lines.extend(fence_lines)
    output.append(_neutralize_inline_text("".join(plain_lines)))
    return "".join(output)
