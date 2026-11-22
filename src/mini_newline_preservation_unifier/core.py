"""Collapse mixed CR, LF, and CRLF line endings to a single style.

The module keeps a record of every original line ending so that offsets in
the unified text can be mapped back to the original document.  No third-party
packages are used, and no I/O is performed; the caller passes a string in and
receives a string plus metadata out.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple


class NewlineStyle(Enum):
    """The line-ending sequences the unifier understands.

    ``MIXED`` is only ever returned by :func:`detect_newline_style`; it is not
    a valid target for :func:`unify_newlines`.
    """

    LF = "\n"
    CR = "\r"
    CRLF = "\r\n"
    MIXED = "mixed"


@dataclass(frozen=True)
class LineEndingRecord:
    """One line ending found in the original document.

    Attributes:
        original_start: Index in the original text where the line ending
            begins.  For a CRLF this is the index of ``\r``.
        original_end: Index in the original text one past the end of the line
            ending.  For a CRLF this is the index after ``\n``.
        unified_start: Index in the unified text where the replacement line
            ending begins.
        unified_end: Index in the unified text one past the replacement.
        style: The style of the original line ending.
    """

    original_start: int
    original_end: int
    unified_start: int
    unified_end: int
    style: NewlineStyle


@dataclass(frozen=True)
class UnifyResult:
    """The outcome of :func:`unify_newlines`.

    Attributes:
        text: The document with every line ending replaced by the target
            style.
        records: One :class:`LineEndingRecord` per original line ending, in
            document order.
        target_style: The style that was written into ``text``.
    """

    text: str
    records: Tuple[LineEndingRecord, ...]
    target_style: NewlineStyle


def _scan_line_endings(text: str) -> List[Tuple[int, int, NewlineStyle]]:
    """Return ``(start, end, style)`` for each line ending in *text*.

    A CRLF is treated as a single line ending rather than a CR followed by an
    LF; that is the only interpretation under which a mixed document can be
    normalised without inventing an empty line.
    """

    endings: List[Tuple[int, int, NewlineStyle]] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "\r":
            if i + 1 < n and text[i + 1] == "\n":
                endings.append((i, i + 2, NewlineStyle.CRLF))
                i += 2
            else:
                endings.append((i, i + 1, NewlineStyle.CR))
                i += 1
        elif ch == "\n":
            endings.append((i, i + 1, NewlineStyle.LF))
            i += 1
        else:
            i += 1
    return endings


def detect_newline_style(text: str) -> NewlineStyle:
    """Report the line-ending style used by *text*.

    A document with no line endings reports :attr:`NewlineStyle.LF`, because
    that is the style :func:`unify_newlines` would write if asked to unify an
    empty document.  A document with more than one distinct style reports
    :attr:`NewlineStyle.MIXED`.
    """

    seen = set()
    for _, _, style in _scan_line_endings(text):
        seen.add(style)
    if not seen:
        return NewlineStyle.LF
    if len(seen) == 1:
        return next(iter(seen))
    return NewlineStyle.MIXED


def unify_newlines(
    text: str,
    target: Optional[NewlineStyle] = None,
) -> UnifyResult:
    """Rewrite every line ending in *text* to a single style.

    Args:
        text: The document to normalise.
        target: The style to write.  When ``None`` the style is inferred from
            the document: a document whose endings are already consistent is
            left alone, and a mixed document is normalised to LF.  Passing
            :attr:`NewlineStyle.MIXED` is rejected because it is not a
            concrete line ending.

    Returns:
        A :class:`UnifyResult` holding the rewritten text, the mapping
        records, and the style that was written.

    Raises:
        ValueError: If *target* is :attr:`NewlineStyle.MIXED`.
        TypeError: If *text* is not a string.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a str")
    if target is NewlineStyle.MIXED:
        raise ValueError("MIXED is not a concrete line-ending style")

    if target is None:
        detected = detect_newline_style(text)
        # A mixed document has no single style to preserve, so LF is the
        # neutral choice.  A consistent document is left as it is.
        target = NewlineStyle.LF if detected is NewlineStyle.MIXED else detected

    replacement = target.value
    pieces: List[str] = []
    records: List[LineEndingRecord] = []
    unified_cursor = 0
    original_cursor = 0

    for start, end, style in _scan_line_endings(text):
        # Copy the run of non-line-ending characters before this ending.
        chunk = text[original_cursor:start]
        pieces.append(chunk)
        unified_cursor += len(chunk)

        unified_start = unified_cursor
        pieces.append(replacement)
        unified_cursor += len(replacement)

        records.append(
            LineEndingRecord(
                original_start=start,
                original_end=end,
                unified_start=unified_start,
                unified_end=unified_cursor,
                style=style,
            )
        )
        original_cursor = end

    # Trailing text after the last line ending, and the empty-document case.
    tail = text[original_cursor:]
    pieces.append(tail)

    return UnifyResult(
        text="".join(pieces),
        records=tuple(records),
        target_style=target,
    )
