"""Markdown masking and evidence-marker extraction. Pure text; zero SQLite."""

from __future__ import annotations

import re

import yaml

from memoria_vault.runtime.content_security import (
    classify_fenced_code_opening,
    fenced_code_closes,
)
from memoria_vault.runtime.evidence import EvidenceMarker, parse_evidence_marker
from memoria_vault.runtime.vaultio import frontmatter_bounds as _yaml_frontmatter_bounds

_DIRECT_EVIDENCE_MARKER_RE = re.compile(
    r"(?m)^(?![ \t>|\ufeff])(?!(?:[-+*]|\d+[.)]|:)[ \t]+)"
    r"(?P<prefix>[^\r\n]*\S)[ \t]+(?P<marker>%%ev:\s*[^\r\n]*?%%)"
    r"[ \t`\\*_~]*\r?$"
)
_RAW_EVIDENCE_MARKER_RE = re.compile(r"%%ev:\s*.*?%%")
_FENCED_DIV_RE = re.compile(r"^[ \t]{0,3}(?P<fence>:{3,})(?P<suffix>[^\r\n]*)$")
_QUOTED_FENCE_OPEN_RE = re.compile(
    r"^ {0,3}(?P<quote>(?:>[ \t]*)+)(?P<fence>`{3,}|~{3,})(?P<info>[^\r\n]*)(?:\r?\n)?$"
)
_QUOTED_LINE_RE = re.compile(r"^ {0,3}(?P<quote>(?:>[ \t]*)+)(?P<content>[^\r\n]*)(?:\r?\n)?$")
_LIST_FENCE_OPEN_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<marker>(?:[-+*]|\d{1,9}[.)]))(?P<spacing>[ \t]+)"
    r"(?P<fence>`{3,}|~{3,})(?P<info>[^\r\n]*)(?:\r?\n)?$"
)
_COMPOUND_LIST_QUOTE_FENCE_OPEN_RE = re.compile(
    r"^(?P<indent> *)(?P<marker>(?:[-+*]|\d{1,9}[.)]))(?P<spacing> +)"
    r"(?P<quote>> +)(?P<fence>`{3,}|~{3,})(?P<info>[^\r\n]*)(?:\r?\n)?$"
)
_LIST_ITEM_LINE_RE = re.compile(r"^[ \t]*(?:[-+*]|\d{1,9}[.)])[ \t]+")
_ATX_HEADING_LINE_RE = re.compile(r"^[ ]{0,3}#{1,6}(?:[ \t]+|$)")
_THEMATIC_BREAK_LINE_RE = re.compile(
    r"^[ \t]{0,3}(?:(?:\*[ \t]*){3,}|(?:_[ \t]*){3,}|(?:-[ \t]*){3,})(?:\r?\n)?$"
)
_SAFE_VISIBILITY_FENCE_INFO_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9+._-]*$")
_CITATION_TABLE_CONTAINER_PREFIX_RE = re.compile(
    r"^[ \t]*(?:(?:>[ \t]*)+|(?:[-+*]|\d{1,9}[.)])[ \t]+)"
)
_MARKDOWN_CONTAINER_RE = re.compile(
    r"^[ ]{0,3}(?:>[ \t]*|(?:[-+*~:]|\d+[.)]|"
    r"\((?:\d+|[IVXLCDMivxlcdm]+|@[^\s)]*|[A-Za-z#])\)|"
    r"@[^\s.)]*[.)]|[A-Za-z#][.)]|[IVXLCDMivxlcdm]+[.)])(?:[ \t]+|$))"
)
_MAX_YAML_FRONTMATTER_INDENT = 256


def _mask_markdown_code(value: str) -> str:
    return re.sub(r"\S", "x", value)


def _markdown_lines(text: str) -> list[str]:
    """Split only physical Markdown LF lines, preserving offsets and endings."""
    return [line for line in re.findall(r"[^\n]*(?:\n|$)", text) if line]


def _is_markdown_blank_line(line: str) -> bool:
    """Return whether a physical line is blank in Markdown's ASCII sense."""
    return not line.rstrip("\r\n").strip(" \t")


def _mask_html_comments(text: str) -> str:
    """Mask HTML comments without changing offsets or line boundaries."""
    masked: list[str] = []
    copied_until = 0
    cursor = 0
    while cursor < len(text):
        start = text.find("<!--", cursor)
        if start < 0:
            break
        end = text.find("-->", start + 4)
        end = len(text) if end < 0 else end + 3
        masked.append(text[copied_until:start])
        masked.append(_mask_markdown_code(text[start:end]))
        copied_until = end
        cursor = end
    masked.append(text[copied_until:])
    return "".join(masked)


def _html_tag_at(text: str, start: int) -> tuple[str, bool, int] | None:
    """Return an HTML tag's name, shape, and end offset when one starts at *start*."""
    index = start + 1
    closing = index < len(text) and text[index] == "/"
    if closing:
        index += 1
    if index >= len(text) or text[index].isspace() or text[index] in "/!?><":
        return None
    name_start = index
    while index < len(text) and not text[index].isspace() and text[index] not in "/><":
        index += 1
    name = text[name_start:index].lower()
    quote = ""
    while index < len(text):
        character = text[index]
        if quote:
            if character == quote:
                quote = ""
        elif character in {'"', "'"}:
            quote = character
        elif character == "<":
            return None
        elif character == ">":
            return name, closing, index + 1
        index += 1
    return None


def _has_raw_html_element(text: str) -> bool:
    """Return whether *text* contains an unescaped raw HTML element."""
    cursor = 0
    while cursor < len(text):
        start = text.find("<", cursor)
        if start < 0:
            return False
        if _preceding_backslash_count(text, start) % 2:
            cursor = start + 1
            continue
        if text.startswith("</", start):
            return True
        tag = _html_tag_at(text, start)
        if tag is not None:
            return True
        cursor = start + 1
    return False


def _mask_html_declarations(text: str) -> str:
    """Mask processing instructions and declarations without moving offsets."""
    masked: list[str] = []
    copied_until = 0
    cursor = 0
    while cursor < len(text):
        processing_start = text.find("<?", cursor)
        declaration_start = text.find("<!", cursor)
        starts = [start for start in (processing_start, declaration_start) if start >= 0]
        if not starts:
            break
        start = min(starts)
        if start == declaration_start and text.startswith("<!--", start):
            cursor = start + 4
            continue
        if text.startswith("<![CDATA[", start):
            end = text.find("]]>", start + len("<![CDATA["))
            end = len(text) if end < 0 else end + 3
        elif start == processing_start:
            end = text.find("?>", start + 2)
            end = len(text) if end < 0 else end + 2
        else:
            end = text.find(">", start + 2)
            end = len(text) if end < 0 else end + 1
        masked.append(text[copied_until:start])
        masked.append(_mask_markdown_code(text[start:end]))
        copied_until = end
        cursor = end
    masked.append(text[copied_until:])
    return "".join(masked)


def _mask_yaml_frontmatter(text: str) -> str:
    """Mask a closed YAML frontmatter block at the beginning of a Markdown file."""
    bounds = _yaml_frontmatter_bounds(text)
    if bounds is None:
        return text
    _body_start, _body_end, end = bounds
    return _mask_markdown_code(text[:end]) + text[end:]


def _mask_yaml_mapping_frontmatter(text: str) -> str | None:
    """Mask initial YAML mappings, or return ``None`` when they fail closed."""
    bounds = _yaml_frontmatter_bounds(text)
    if bounds is None:
        return text
    body_start, body_end, end = bounds
    body = text[body_start:body_end]
    if any(
        len(line) - len(line.lstrip(" \t")) > _MAX_YAML_FRONTMATTER_INDENT
        for line in _markdown_lines(body)
    ):
        return None
    try:
        frontmatter = yaml.safe_load(body)
    except RecursionError:
        return None
    except yaml.YAMLError:
        return text
    if not isinstance(frontmatter, dict):
        return text
    return _mask_markdown_code(text[:end]) + text[end:]


def _has_mmd_title_field(text: str) -> bool:
    """Return whether an initial mmd_title_block field could hide a control."""
    return re.match(r"\A\ufeff?[ \t]*[\w-][\w \t-]*:", text) is not None


def _has_abbreviation_syntax(text: str) -> bool:
    """Return whether an abbreviation definition could hide a control."""
    return re.search(r"(?m)^\*\[", text) is not None


def _mask_markdown_containers(text: str) -> str:
    """Mask container blocks so only top-level prose can establish a binding."""
    masked: list[str] = []
    in_container = False
    for line in _markdown_lines(text):
        body = line.rstrip("\r\n")
        if _is_markdown_blank_line(line):
            in_container = False
            masked.append(line)
        elif in_container or _MARKDOWN_CONTAINER_RE.match(body):
            in_container = True
            masked.append(_mask_markdown_code(line))
        else:
            masked.append(line)
    return "".join(masked)


def _mask_definition_terms(text: str) -> str:
    """Mask a definition-list term when its marker line follows it."""
    lines = _markdown_lines(text)
    for index, line in enumerate(lines):
        body = line.rstrip("\r\n")
        if not index or not re.match(r"^[ ]{0,3}[:~][ \t]+", body):
            continue
        term_index = index - 1
        if _is_markdown_blank_line(lines[term_index]):
            term_index -= 1
        if term_index >= 0 and not _is_markdown_blank_line(lines[term_index]):
            lines[term_index] = _mask_markdown_code(lines[term_index])
    return "".join(lines)


def _mask_markdown_headings(text: str) -> str:
    """Mask ATX and Setext headings, which are not direct prose claims."""
    lines = _markdown_lines(text)
    for index, line in enumerate(lines):
        body = line.rstrip("\r\n")
        if heading := re.match(r"^[ ]{0,3}#{1,6}(?:[ \t]+|$)", body):
            lines[index] = line[: heading.end()] + _mask_markdown_code(line[heading.end() :])
        if index and re.match(r"^[ ]{0,3}(?:=+|-+)[ \t]*$", body):
            if not _is_markdown_blank_line(lines[index - 1]):
                lines[index - 1] = _mask_markdown_code(lines[index - 1])
    return "".join(lines)


def _mask_markdown_ranges(text: str, ranges: list[tuple[int, int]]) -> str:
    """Mask sorted or overlapping ranges without changing text offsets."""
    if not ranges:
        return text
    masked: list[str] = []
    copied_until = 0
    for range_start, end in sorted(ranges):
        if end <= copied_until:
            continue
        start = max(range_start, copied_until)
        masked.append(text[copied_until:start])
        masked.append(_mask_markdown_code(text[start:end]))
        copied_until = end
    masked.append(text[copied_until:])
    return "".join(masked)


def _mask_multiline_delimited_constructs(text: str, opener: str, closer: str) -> str:
    """Mask multiline balanced constructs with one delimiter pass."""
    starts: list[int] = []
    ranges: list[tuple[int, int]] = []
    last_line_break = -1
    index = 0
    while index < len(text):
        character = text[index]
        if character == "\\":
            index += 2
            continue
        if character in "\r\n":
            last_line_break = index
        elif character == opener:
            starts.append(index)
        elif character == closer and starts:
            start = starts.pop()
            if last_line_break > start:
                ranges.append((start, index + 1))
        index += 1
    if starts and last_line_break > starts[0]:
        ranges.append((starts[0], len(text)))
    return _mask_markdown_ranges(text, ranges)


def _mask_multiline_bracket_constructs(text: str) -> str:
    """Mask multiline Markdown inline constructs before accepting controls."""
    return _mask_multiline_delimited_constructs(text, "[", "]")


def _mask_multiline_parenthesized_constructs(text: str) -> str:
    """Mask multiline Markdown destinations and titles before accepting controls."""
    return _mask_multiline_delimited_constructs(text, "(", ")")


def _reference_definition_header_end(text: str, start: int) -> int | None:
    """Return the end of a reference-definition header beginning at *start*."""
    index = start
    while index < len(text) and index - start < 3 and text[index] == " ":
        index += 1
    if index >= len(text) or text[index] != "[":
        return None
    index += 1
    while index < len(text):
        character = text[index]
        if character == "\\":
            index += 2
            continue
        if character in "\r\n":
            next_line = index + (2 if text.startswith("\r\n", index) else 1)
            if next_line >= len(text) or text[next_line] in "\r\n":
                return None
            index = next_line
            continue
        if character == "]":
            probe = index + 1
            while probe < len(text) and text[probe] in " \t":
                probe += 1
            if probe < len(text) and text[probe] == ":":
                return probe + 1
        index += 1
    return None


def _line_end(text: str, start: int) -> int:
    newline = text.find("\n", start)
    return len(text) if newline < 0 else newline + 1


def _mask_reference_definitions(text: str) -> str:
    """Mask reference and footnote definitions, including multiline labels."""
    masked: list[str] = []
    copied_until = 0
    cursor = 0
    while cursor < len(text):
        header_end = _reference_definition_header_end(text, cursor)
        if header_end is None:
            cursor = _line_end(text, cursor)
            continue
        end = _line_end(text, header_end)
        while end < len(text) and not _is_markdown_blank_line(text[end : _line_end(text, end)]):
            end = _line_end(text, end)
        masked.append(text[copied_until:cursor])
        masked.append(_mask_markdown_code(text[cursor:end]))
        copied_until = end
        cursor = end
    masked.append(text[copied_until:])
    return "".join(masked)


def _mask_fenced_divs(text: str) -> str:
    """Mask Pandoc fenced Divs, including nested attributed Divs."""
    masked: list[str] = []
    fences: list[int] = []
    for line in _markdown_lines(text):
        body = line.rstrip("\r\n")
        divider = _FENCED_DIV_RE.match(body)
        if not fences:
            if divider is None:
                masked.append(line)
                continue
            fences.append(len(divider["fence"]))
            masked.append(_mask_markdown_code(line))
            continue

        masked.append(_mask_markdown_code(line))
        if divider is None:
            continue
        fence_length = len(divider["fence"])
        if divider["suffix"].strip(" \t"):
            fences.append(fence_length)
        elif fence_length >= fences[-1]:
            fences.pop()
    return "".join(masked)


def _has_tex_math_pair(
    text: str,
    opener: str,
    closer: str,
    *,
    active_closer_required: bool,
) -> bool:
    """Return whether a Pandoc single-backslash TeX-math pair is active."""
    opened = False
    index = 0
    while index < len(text):
        if text[index] != "\\":
            index += 1
            continue
        run_start = index
        while index < len(text) and text[index] == "\\":
            index += 1
        if index == len(text):
            break
        delimiter = text[index]
        run_length = index - run_start
        if delimiter == opener and run_length % 2:
            opened = True
        elif opened and delimiter == closer and (not active_closer_required or run_length % 2):
            return True
        index += 1
    return False


def _has_raw_tex_syntax(text: str) -> bool:
    """Return whether active raw TeX syntax can affect draft visibility."""
    for match in re.finditer(r"\\(.)", text, flags=re.DOTALL):
        if _preceding_backslash_count(text, match.start()) % 2 == 0 and match[1].isalpha():
            return True
    if _has_tex_math_pair(text, "[", "]", active_closer_required=False):
        return True
    if _has_tex_math_pair(text, "(", ")", active_closer_required=True):
        return True
    for match in re.finditer(r"\$", text):
        if _preceding_backslash_count(text, match.start()) % 2 == 0:
            return True
    for match in re.finditer(r"(?m)^[ \t]{0,3}%", text):
        if _preceding_backslash_count(text, match.end() - 1) % 2 == 0:
            return True
    return False


def _has_pandoc_attribute_syntax(text: str) -> bool:
    """Return whether active Pandoc attribute syntax can affect draft visibility."""
    for match in re.finditer(r"\{\s*(?:=|[#.]|[^{}\s=]+[ \t]*=)", text):
        if _preceding_backslash_count(text, match.start()) % 2 == 0:
            return True
    return False


def _has_footnote_definition(text: str) -> bool:
    """Return whether a footnote definition makes direct binding ambiguous."""
    return re.search(r"(?m)^[ \t]*\[\^[^\]\r\n]+\]:", text) is not None


def _has_pandoc_table_syntax(text: str) -> bool:
    """Return whether Pandoc table syntax makes direct claim binding ambiguous."""
    if re.search(
        r"(?m)^[ \t]*[|+]?[ \t]*:?-+:?[ \t]*(?:[|+][ \t]*:?-+:?[ \t]*)+[|+]?[ \t]*$",
        text,
    ):
        return True
    if re.search(r"(?m)^[ \t]*\+(?:[-=]+\+)+[ \t]*$", text):
        return True
    if re.search(r"(?m)^[ \t]*:?-+:?(?:[ \t]+:?-+:?)+[ \t]*$", text):
        return True
    if re.search(r"(?m)^[ \t]+:?-+:?[ \t]*$", text):
        return True
    return len(re.findall(r"(?m)^[ \t]*-+[ \t]*$", text)) >= 2


def _table_container_text(text: str) -> str:
    """Flatten quote/list prefixes before fail-closed table visibility checks."""
    lines: list[str] = []
    for raw_line in _markdown_lines(text):
        line = raw_line
        while match := _CITATION_TABLE_CONTAINER_PREFIX_RE.match(line):
            line = line[match.end() :]
        lines.append(line)
    return "".join(lines)


def _has_ambiguous_pandoc_table_syntax(text: str) -> bool:
    """Return whether table grammar can change Markdown visibility in a container."""
    return _has_pandoc_table_syntax(text) or _has_pandoc_table_syntax(_table_container_text(text))


def markdown_citation_visibility_is_ambiguous(text: str) -> bool:
    """Return whether table grammar can change visible raw citation boundaries."""
    return _has_ambiguous_pandoc_table_syntax(text)


def _backtick_run_end(text: str, start: int) -> int:
    end = start
    while end < len(text) and text[end] == "`":
        end += 1
    return end


def _preceding_backslash_count(text: str, index: int) -> int:
    count = 0
    index -= 1
    while index >= 0 and text[index] == "\\":
        count += 1
        index -= 1
    return count


def _inline_code_interior_lines(content: str) -> list[str]:
    """Return complete physical lines strictly between inline-code delimiters."""
    if "\n" not in content:
        return []
    lines = _markdown_lines(content)[1:]
    return lines if content.endswith("\n") else lines[:-1]


def _inline_code_span_is_definite(content: str, *, opener_line: str, closer_line: str) -> bool:
    """Return whether a multiline backtick pair avoids known block boundaries."""
    if re.search(r"\r(?!\n)", content):
        return False
    if _QUOTED_LINE_RE.match(opener_line) or _LIST_ITEM_LINE_RE.match(opener_line):
        return False
    if _QUOTED_LINE_RE.match(closer_line) or _LIST_ITEM_LINE_RE.match(closer_line):
        return False
    return not any(
        _is_markdown_blank_line(line)
        or re.fullmatch(r"[ \t]*-+[ \t]*(?:\r?\n)?", line)
        or re.match(r"^[ \t]{0,3}[:~][ \t]+", line)
        or _QUOTED_LINE_RE.match(line)
        or _LIST_ITEM_LINE_RE.match(line)
        or _has_ambiguous_pandoc_table_syntax(line)
        for line in _inline_code_interior_lines(content)
    )


def _mask_inline_code_spans(text: str, *, conservative: bool = False) -> str:
    """Mask inline-code delimiter runs using an indexed linear scan.

    Visibility checks can require a stricter multiline interpretation: masking a
    span that Pandoc parses as blocks would hide a live citation from the export
    gate.
    """
    runs: list[tuple[int, int]] = []
    index = 0
    while index < len(text):
        if text[index] != "`":
            index += 1
            continue
        run_end = _backtick_run_end(text, index)
        runs.append((index, run_end))
        index = run_end

    choices: list[tuple[tuple[int, int] | None, tuple[int, int] | None]] = [(None, None)] * len(
        runs
    )
    next_closer_by_length: dict[int, int] = {}
    for run_index in range(len(runs) - 1, -1, -1):
        start, end = runs[run_index]
        length = end - start
        full_choice = None
        for delimiter_length in range(length, 0, -1):
            if closer_start := next_closer_by_length.get(delimiter_length):
                full_choice = (delimiter_length, closer_start)
                break
        suffix_choice = None
        for delimiter_length in range(length - 1, 0, -1):
            if closer_start := next_closer_by_length.get(delimiter_length):
                suffix_choice = (delimiter_length, closer_start)
                break
        choices[run_index] = (full_choice, suffix_choice)
        next_closer_by_length[length] = start

    runs_by_start = {start: (run_index, end) for run_index, (start, end) in enumerate(runs)}
    masked: list[str] = []
    copied_until = 0
    index = 0
    while index < len(text):
        if text[index] != "`":
            index += 1
            continue
        run_index, opener_end = runs_by_start[index]
        escaped = _preceding_backslash_count(text, index) % 2
        choice = choices[run_index][1 if escaped else 0]
        if choice is None:
            index = opener_end
            continue
        delimiter_length, closer_start = choice
        span_start = opener_end - delimiter_length
        closer_end = closer_start + delimiter_length
        opener_line_start = text.rfind("\n", 0, span_start) + 1
        closer_line_end = text.find("\n", closer_start)
        closer_line_end = len(text) if closer_line_end == -1 else closer_line_end
        if conservative and not _inline_code_span_is_definite(
            text[opener_end:closer_start],
            opener_line=text[opener_line_start:opener_end],
            closer_line=text[closer_start:closer_line_end],
        ):
            index = runs_by_start[closer_start][1]
            continue
        masked.append(text[copied_until:span_start])
        masked.append(_mask_markdown_code(text[span_start:closer_end]))
        copied_until = closer_end
        index = closer_end
    masked.append(text[copied_until:])
    return "".join(masked)


def _container_fence_opening(
    fence: str, info: str, plain_lines: list[str]
) -> tuple[str, int] | None:
    """Return one accepted nested fence's delimiter, if its header is trustworthy."""
    if (
        fence.startswith("`")
        and info.strip()
        and not _SAFE_VISIBILITY_FENCE_INFO_RE.fullmatch(info.strip())
    ):
        return None
    opening, literalize = classify_fenced_code_opening(f"{fence}{info}", plain_lines)
    if opening is None:
        return None
    if literalize:
        info = info.strip()
        boundary_opening, boundary_literalize = classify_fenced_code_opening(fence, plain_lines)
        if (
            fence.startswith("~")
            and re.fullmatch(r"[^\s`{}]+", info)
            and boundary_opening is not None
            and not boundary_literalize
        ):
            return fence[0], len(fence)
        return None
    fence = opening.group("fence")
    return fence[0], len(fence)


def _quoted_fence_closes(line: str, character: str, length: int, quote_depth: int) -> bool:
    """Return whether a blockquote fence closes on this physical line."""
    if fenced_code_closes(line, character, length):
        return True
    match = re.match(r"^ {0,3}(?P<quote>(?:>[ \t]*)+)(?P<content>[^\r\n]*)(?:\r?\n)?$", line)
    return bool(
        match
        and match["quote"].count(">") <= quote_depth
        and fenced_code_closes(match["content"], character, length)
    )


def _quoted_fence_contains(line: str) -> bool:
    """Return whether a physical line remains inside a blockquote container."""
    return _QUOTED_LINE_RE.match(line) is not None


def _list_fence_closes(line: str, character: str, length: int, indentation: int) -> bool:
    """Return whether a list-contained fence closes on this physical line."""
    if fenced_code_closes(line, character, length):
        return True
    prefix = line[:indentation]
    return bool(
        len(prefix) == indentation
        and all(prefix_character in " \t" for prefix_character in prefix)
        and fenced_code_closes(line[indentation:], character, length)
    )


def _list_fence_contains(line: str, indentation: int) -> bool:
    """Return whether a physical line remains an indented list continuation."""
    prefix = line[:indentation]
    return len(prefix) == indentation and all(
        prefix_character in " \t" for prefix_character in prefix
    )


def _quote_list_fence_opening(
    line: str, quote_context: list[str]
) -> tuple[str, int, str, int] | None:
    """Return a narrow quote-to-list fence only when its outer context is safe."""
    quote = _QUOTED_LINE_RE.match(line)
    if quote is None or quote["quote"].count(">") != 1:
        return None
    quote_prefix = line[: quote.start("content")]
    if "\t" in quote_prefix:
        return None
    list_item = _LIST_FENCE_OPEN_RE.match(quote["content"])
    if (
        list_item is None
        or list_item["indent"]
        or "\t" in list_item["spacing"]
        or (fence := _container_fence_opening(list_item["fence"], list_item["info"], quote_context))
        is None
    ):
        return None
    return *fence, quote_prefix, list_item.start("fence")


def _list_quote_fence_opening(
    line: str, list_context: list[str]
) -> tuple[str, int, str, int] | None:
    """Return a narrow list-to-quote fence only when its outer context is safe."""
    match = _COMPOUND_LIST_QUOTE_FENCE_OPEN_RE.match(line)
    if (
        match is None
        or (fence := _container_fence_opening(match["fence"], match["info"], list_context)) is None
    ):
        return None
    return *fence, match["quote"], match.start("quote")


def _quote_list_fence_inner_line(line: str, quote_prefix: str, indentation: int) -> str | None:
    """Return the virtual list-content line under an exact outer quote prefix."""
    if not line.startswith(quote_prefix):
        return None
    inner = line[len(quote_prefix) :]
    prefix = inner[:indentation]
    if len(prefix) != indentation or prefix != " " * indentation:
        return None
    return inner[indentation:]


def _quote_list_fence_closes(
    line: str, character: str, length: int, quote_prefix: str, indentation: int
) -> bool:
    """Return whether a strict quote-to-list fence closes on this line."""
    if fenced_code_closes(line, character, length):
        return True
    if not line.startswith(quote_prefix):
        return False
    after_quote = line[len(quote_prefix) :]
    if fenced_code_closes(after_quote, character, length):
        return True
    inner = _quote_list_fence_inner_line(line, quote_prefix, indentation)
    return inner is not None and fenced_code_closes(inner, character, length)


def _list_quote_fence_inner_line(line: str, quote_prefix: str, indentation: int) -> str | None:
    """Return the virtual quote-content line under an exact list continuation."""
    prefix = line[:indentation]
    if len(prefix) != indentation or prefix != " " * indentation:
        return None
    inner = line[indentation:]
    if not inner.startswith(quote_prefix):
        return None
    return inner[len(quote_prefix) :]


def _list_quote_fence_closes(
    line: str, character: str, length: int, quote_prefix: str, indentation: int
) -> bool:
    """Return whether a strict list-to-quote fence closes on this line."""
    if fenced_code_closes(line, character, length):
        return True
    inner = _list_quote_fence_inner_line(line, quote_prefix, indentation)
    return inner is not None and fenced_code_closes(inner, character, length)


def _quote_fence_context(
    quote_depth: int,
    quote_block_boundaries: dict[int, bool],
    plain_block_boundary: bool,
) -> list[str]:
    """Return a fail-closed context for a quote-contained fence opener."""
    if quote_depth in quote_block_boundaries:
        return [] if quote_block_boundaries[quote_depth] else ["prose"]
    if not quote_block_boundaries:
        return [] if plain_block_boundary else ["prose"]
    return (
        []
        if all(quote_block_boundaries.get(depth, False) for depth in range(1, quote_depth))
        else ["prose"]
    )


def _remember_container_plain_line(
    line: str,
    quote_block_boundaries: dict[int, bool],
    list_item_active: bool,
    plain_block_boundary: bool,
) -> tuple[bool, bool]:
    """Retain the immediate context needed to classify a later container fence."""
    starts_at_block_boundary = plain_block_boundary
    quote = _QUOTED_LINE_RE.match(line)
    plain_heading = quote is None and starts_at_block_boundary and _ATX_HEADING_LINE_RE.match(line)
    list_item = (
        quote is None and _LIST_ITEM_LINE_RE.match(line) and not _THEMATIC_BREAK_LINE_RE.match(line)
    )
    if _is_markdown_blank_line(line):
        list_item_active = False
    elif list_item:
        list_item_active = list_item_active or starts_at_block_boundary
    if _is_markdown_blank_line(line):
        plain_block_boundary = True
    elif plain_heading or (list_item and list_item_active):
        plain_block_boundary = True
    else:
        plain_block_boundary = False
    if quote is None:
        quote_block_boundaries.clear()
        return list_item_active, plain_block_boundary
    quote_depth = quote["quote"].count(">")
    quote_ancestors_at_boundary = bool(quote_block_boundaries) or starts_at_block_boundary
    quote_ancestors_at_boundary &= all(
        quote_block_boundaries.get(depth, True) for depth in range(1, quote_depth)
    )
    quote_starts_at_boundary = quote_ancestors_at_boundary and quote_block_boundaries.get(
        quote_depth, starts_at_block_boundary if not quote_block_boundaries else True
    )
    for depth in range(1, quote_depth):
        quote_block_boundaries[depth] = False
    for depth in list(quote_block_boundaries):
        if depth > quote_depth:
            del quote_block_boundaries[depth]
    quote_content = quote["content"]
    quote_boundary = quote_ancestors_at_boundary and (
        _is_markdown_blank_line(quote_content)
        or bool(_THEMATIC_BREAK_LINE_RE.match(quote_content))
        or bool(quote_starts_at_boundary and _ATX_HEADING_LINE_RE.match(quote_content))
    )
    quote_block_boundaries[quote_depth] = quote_boundary
    return list_item_active, plain_block_boundary


def _mask_container_fenced_code_literals(text: str) -> str:
    """Mask only paired blockquote/list fences without hiding later prose."""
    lines: list[str] = []
    pending: list[str] = []
    quote_block_boundaries: dict[int, bool] = {}
    kind = ""
    fence_character = ""
    fence_length = 0
    quote_depth = 0
    list_indentation = 0
    compound_prefix = ""
    compound_indentation = 0
    list_item_active = False
    plain_block_boundary = True
    table_rule_pending = False
    for line in _markdown_lines(text):
        if kind:
            if kind == "quote":
                closes = _quoted_fence_closes(line, fence_character, fence_length, quote_depth)
            elif kind == "list":
                list_prefix = line[:list_indentation]
                closes = "\t" not in list_prefix and _list_fence_closes(
                    line, fence_character, fence_length, list_indentation
                )
            elif kind == "quote-list":
                closes = _quote_list_fence_closes(
                    line,
                    fence_character,
                    fence_length,
                    compound_prefix,
                    compound_indentation,
                )
            else:
                closes = _list_quote_fence_closes(
                    line,
                    fence_character,
                    fence_length,
                    compound_prefix,
                    compound_indentation,
                )
            if closes:
                pending.append(line)
                lines.extend(_mask_markdown_code(pending_line) for pending_line in pending)
                pending.clear()
                quote_block_boundaries.clear()
                plain_block_boundary = True
                table_rule_pending = False
                kind = ""
                fence_character = ""
                fence_length = 0
                quote_depth = 0
                list_indentation = 0
                compound_prefix = ""
                compound_indentation = 0
                continue
            if kind == "quote":
                contains = _quoted_fence_contains(line)
            elif kind == "list":
                list_prefix = line[:list_indentation]
                contains = "\t" not in list_prefix and _list_fence_contains(line, list_indentation)
            elif kind == "quote-list":
                contains = (
                    _quote_list_fence_inner_line(line, compound_prefix, compound_indentation)
                    is not None
                )
            else:
                contains = (
                    _list_quote_fence_inner_line(line, compound_prefix, compound_indentation)
                    is not None
                )
            if contains:
                pending.append(line)
                continue
            lines.extend(pending)
            for pending_line in pending:
                list_item_active, plain_block_boundary = _remember_container_plain_line(
                    pending_line,
                    quote_block_boundaries,
                    list_item_active,
                    plain_block_boundary,
                )
                table_rule_pending = not _is_markdown_blank_line(pending_line) and (
                    table_rule_pending or _has_ambiguous_pandoc_table_syntax(pending_line)
                )
            pending.clear()
            kind = ""
            fence_character = ""
            fence_length = 0
            quote_depth = 0
            list_indentation = 0
            compound_prefix = ""
            compound_indentation = 0

        quote = _QUOTED_FENCE_OPEN_RE.match(line)
        quote_context = (
            ["prose"]
            if list_item_active
            else _quote_fence_context(
                quote["quote"].count(">"), quote_block_boundaries, plain_block_boundary
            )
            if quote
            else []
        )
        if (
            not table_rule_pending
            and quote
            and (fence := _container_fence_opening(quote["fence"], quote["info"], quote_context))
        ):
            kind = "quote"
            fence_character, fence_length = fence
            quote_depth = quote["quote"].count(">")
            quote_block_boundaries.clear()
            list_item_active = False
            plain_block_boundary = True
            table_rule_pending = False
            pending.append(line)
            continue

        list_item = _LIST_FENCE_OPEN_RE.match(line)
        list_context = [] if list_item_active or plain_block_boundary else ["prose"]
        if (
            not table_rule_pending
            and list_item
            and "\t" not in list_item["indent"] + list_item["spacing"]
            and (
                fence := _container_fence_opening(
                    list_item["fence"], list_item["info"], list_context
                )
            )
        ):
            kind = "list"
            fence_character, fence_length = fence
            list_indentation = list_item.start("fence")
            quote_block_boundaries.clear()
            list_item_active = True
            plain_block_boundary = True
            table_rule_pending = False
            pending.append(line)
            continue

        compound_quote_context = (
            ["prose"]
            if list_item_active
            else _quote_fence_context(1, quote_block_boundaries, plain_block_boundary)
        )
        if not table_rule_pending and (
            compound := _quote_list_fence_opening(line, compound_quote_context)
        ):
            kind = "quote-list"
            fence_character, fence_length, compound_prefix, compound_indentation = compound
            quote_block_boundaries.clear()
            list_item_active = False
            plain_block_boundary = True
            table_rule_pending = False
            pending.append(line)
            continue

        compound_list_context = [] if list_item_active or plain_block_boundary else ["prose"]
        if not table_rule_pending and (
            compound := _list_quote_fence_opening(line, compound_list_context)
        ):
            kind = "list-quote"
            fence_character, fence_length, compound_prefix, compound_indentation = compound
            quote_block_boundaries.clear()
            list_item_active = True
            plain_block_boundary = True
            table_rule_pending = False
            pending.append(line)
            continue

        lines.append(line)
        list_item_active, plain_block_boundary = _remember_container_plain_line(
            line,
            quote_block_boundaries,
            list_item_active,
            plain_block_boundary,
        )
        table_rule_pending = not _is_markdown_blank_line(line) and (
            table_rule_pending or _has_ambiguous_pandoc_table_syntax(line)
        )
    lines.extend(pending)
    return "".join(lines)


def _mask_top_level_code_literals(text: str) -> str:
    """Mask top-level fenced code while preserving the shared fence semantics."""
    lines: list[str] = []
    plain_lines: list[str] = []
    fence_char = ""
    fence_length = 0
    literal_tilde_fence_length = 0
    for line in _markdown_lines(text):
        if fence_char:
            lines.append(_mask_markdown_code(line))
            if fenced_code_closes(line, fence_char, fence_length):
                fence_char = ""
                fence_length = 0
            continue

        if literal_tilde_fence_length:
            if fenced_code_closes(line, "~", literal_tilde_fence_length):
                literal_tilde_fence_length = 0
            plain_lines.append(line)
            lines.append(_mask_markdown_code(line) if re.match(r"^(?: {4}|\t)", line) else line)
            continue

        opening, literalize = classify_fenced_code_opening(line, plain_lines)
        if opening is not None and not literalize:
            fence = opening.group("fence")
            fence_char = fence[0]
            fence_length = len(fence)
            lines.append(_mask_markdown_code(line))
            plain_lines.clear()
            continue

        if literalize and opening is not None:
            if opening.group("fence").startswith("~"):
                literal_tilde_fence_length = len(opening.group("fence"))
        plain_lines.append(line)
        lines.append(_mask_markdown_code(line) if re.match(r"^(?: {4}|\t)", line) else line)

    return "".join(lines)


def _visibility_fenced_code_opening(
    line: str, at_block_boundary: bool
) -> tuple[re.Match[str] | None, bool]:
    """Classify only fence headers whose visible-code semantics are definite."""
    opening, literalize = classify_fenced_code_opening(line, [] if at_block_boundary else ["prose"])
    if opening is None or literalize:
        return opening, literalize
    info = line[opening.end() :].rstrip("\r\n").strip(" \t")
    if info and not _SAFE_VISIBILITY_FENCE_INFO_RE.fullmatch(info):
        return None, False
    return opening, False


def _mask_visibility_top_level_code_literals(text: str) -> str:
    """Mask only definite top-level code without recreating Pandoc's containers."""
    lines: list[str] = []
    pending_fence: list[str] = []
    fence_char = ""
    fence_length = 0
    literal_tilde_fence_length = 0
    indented_code = False
    at_block_boundary = True
    seen_nonblank = False
    table_rule_pending = False
    for line in _markdown_lines(text):
        if fence_char:
            pending_fence.append(line)
            if fenced_code_closes(line, fence_char, fence_length):
                lines.extend(_mask_markdown_code(pending_line) for pending_line in pending_fence)
                pending_fence.clear()
                fence_char = ""
                fence_length = 0
                at_block_boundary = True
                seen_nonblank = True
                table_rule_pending = False
            continue

        if indented_code:
            if re.match(r"^(?: {4}|\t)", line):
                lines.append(_mask_markdown_code(line))
                continue
            if _is_markdown_blank_line(line):
                lines.append(line)
                continue
            indented_code = False
            at_block_boundary = True
            seen_nonblank = True

        if literal_tilde_fence_length:
            if fenced_code_closes(line, "~", literal_tilde_fence_length):
                literal_tilde_fence_length = 0
            lines.append(line)
            if _is_markdown_blank_line(line):
                at_block_boundary = True
            else:
                at_block_boundary = False
                seen_nonblank = True
            table_rule_pending = not _is_markdown_blank_line(line) and (
                table_rule_pending or _has_ambiguous_pandoc_table_syntax(line)
            )
            continue

        if re.match(r"^(?: {4}|\t)", line) and not seen_nonblank:
            lines.append(_mask_markdown_code(line))
            indented_code = True
            continue

        opening, literalize = _visibility_fenced_code_opening(line, at_block_boundary)
        if not table_rule_pending and opening is not None and not literalize:
            fence = opening.group("fence")
            fence_char = fence[0]
            fence_length = len(fence)
            pending_fence.append(line)
            continue

        if literalize and opening is not None and opening.group("fence").startswith("~"):
            literal_tilde_fence_length = len(opening.group("fence"))
        lines.append(line)
        if _is_markdown_blank_line(line):
            at_block_boundary = True
        else:
            at_block_boundary = bool(at_block_boundary and _ATX_HEADING_LINE_RE.match(line))
            seen_nonblank = True
        table_rule_pending = not _is_markdown_blank_line(line) and (
            table_rule_pending or _has_ambiguous_pandoc_table_syntax(line)
        )

    lines.extend(pending_fence)
    return "".join(lines)


def markdown_code_literals_masked(text: str) -> str:
    """Mask Markdown code literals while preserving source offsets and visible prose.

    This deliberately leaves headings and other rendered Markdown intact for
    callers that need to inspect direct Markdown controls.
    """
    fenced = _mask_top_level_code_literals(text)
    fenced = _mask_container_fenced_code_literals(fenced)
    return _mask_inline_code_spans(fenced)


def markdown_visible_code_literals_masked(text: str) -> str:
    """Mask only definite code literals before checking rendered Markdown syntax.

    Unlike :func:`markdown_code_literals_masked`, this does not treat every
    four-space or tab-prefixed physical line as code: indented code cannot
    interrupt a paragraph, so doing so could hide a visible Pandoc citation.
    """
    fenced = _mask_visibility_top_level_code_literals(text)
    fenced = _mask_container_fenced_code_literals(fenced)
    return _mask_inline_code_spans(fenced, conservative=True)


def _markdown_control_text(text: str) -> str:
    """Mask non-rendering syntax so only direct Markdown controls can bind evidence."""

    yaml_for_table = _mask_yaml_mapping_frontmatter(text)
    if yaml_for_table is None:
        return _mask_markdown_code(text)
    if (
        "\r" in text
        or _has_raw_html_element(text)
        or _has_pandoc_attribute_syntax(text)
        or _has_raw_tex_syntax(text)
        or _has_footnote_definition(text)
        or _has_mmd_title_field(text)
        or _has_abbreviation_syntax(text)
        or _has_ambiguous_pandoc_table_syntax(yaml_for_table)
    ):
        return _mask_markdown_code(text)
    nonbinding = _mask_html_comments(text)
    nonbinding = _mask_html_declarations(nonbinding)
    nonbinding = _mask_yaml_frontmatter(nonbinding)
    nonbinding = _mask_definition_terms(nonbinding)
    nonbinding = _mask_markdown_headings(nonbinding)
    nonbinding = _mask_markdown_containers(nonbinding)
    nonbinding = _mask_reference_definitions(nonbinding)
    nonbinding = _mask_multiline_bracket_constructs(nonbinding)
    nonbinding = _mask_multiline_parenthesized_constructs(nonbinding)
    nonbinding = _mask_fenced_divs(nonbinding)
    return markdown_code_literals_masked(nonbinding)


def _direct_evidence_marker_matches(text: str) -> list[tuple[re.Match[str], EvidenceMarker]]:
    """Return evidence markers in direct Markdown claim lines from control text."""
    matches: list[tuple[re.Match[str], EvidenceMarker]] = []
    for match in _DIRECT_EVIDENCE_MARKER_RE.finditer(text):
        try:
            marker = parse_evidence_marker(match["marker"])
        except ValueError:
            continue
        matches.append((match, marker))
    return matches


def evidence_marker_occurrences_from_markdown(
    text: str,
) -> list[tuple[EvidenceMarker, bool]]:
    """Return raw evidence markers and whether each is a direct visible occurrence."""
    direct_spans = {span for span, _marker in direct_evidence_marker_spans_from_markdown(text)}
    occurrences: list[tuple[EvidenceMarker, bool]] = []
    for match in _RAW_EVIDENCE_MARKER_RE.finditer(text):
        try:
            marker = parse_evidence_marker(match.group(0))
        except ValueError:
            continue
        occurrences.append((marker, match.span() in direct_spans))
    return occurrences


def direct_evidence_marker_spans_from_markdown(
    text: str,
) -> list[tuple[tuple[int, int], EvidenceMarker]]:
    """Return source spans and markers that appear on direct, visible claim lines."""
    control_text = _markdown_control_text(text)
    return [
        (match.span("marker"), marker)
        for match, marker in _direct_evidence_marker_matches(control_text)
    ]


def evidence_markers_from_markdown(text: str) -> list[EvidenceMarker]:
    """Return markers that appear on direct, visible Markdown claim lines."""
    return [marker for _span, marker in direct_evidence_marker_spans_from_markdown(text)]
