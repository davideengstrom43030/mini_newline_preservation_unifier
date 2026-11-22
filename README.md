# mini_newline_preservation_unifier

Normalise mixed CR, LF, and CRLF line endings in one string while keeping a
record of where every original ending was, so offsets can be mapped back.

```python
from mini_newline_preservation_unifier import (
    NewlineStyle,
    detect_newline_style,
    unify_newlines,
)

text = "alpha\r\nbeta\ngamma\rdelta"

print(detect_newline_style(text))          # NewlineStyle.MIXED

result = unify_newlines(text, NewlineStyle.LF)
print(repr(result.text))                   # 'alpha\nbeta\ngamma\ndelta'
print(result.target_style)                 # NewlineStyle.LF

for record in result.records:
    print(record.original_start, record.unified_start, record.style)
```

## Why this exists

Text that has travelled through several editors, version-control filters, or
network transports often ends up with a mixture of `\r\n`, `\n`, and `\r`.
Collapsing it is easy; collapsing it without losing the ability to say "this
character in the normalised text came from that character in the original" is
not.  This library does both, returning the rewritten string together with one
immutable `LineEndingRecord` per original line ending.

The trade-off is deliberate: the library only rewrites line endings.  It does
not touch indentation, trailing whitespace, or any other formatting, because a
unifier that also reformats is impossible to map back reliably.

## API

- `NewlineStyle` — enum with `LF`, `CR`, `CRLF`, and `MIXED`.  `MIXED` is only
  ever produced by `detect_newline_style`; it is rejected as a target.
- `detect_newline_style(text) -> NewlineStyle` — a document with no line
  endings reports `LF`.  A document with more than one distinct ending reports
  `MIXED`.  A CRLF counts as one ending, not a CR plus an LF.
- `unify_newlines(text, target=None) -> UnifyResult` — rewrite every ending to
  `target`.  When `target` is `None` the style is inferred: a consistent
  document keeps its own style, and a mixed document is normalised to `LF`.
  Passing `NewlineStyle.MIXED` raises `ValueError`; passing a non-string raises
  `TypeError`.
- `UnifyResult` — frozen dataclass with `text`, `records`, and `target_style`.
- `LineEndingRecord` — frozen dataclass with `original_start`, `original_end`,
  `unified_start`, `unified_end`, and `style`.

## The awkward edge

A CRLF is treated as a single line ending, so it produces one record whose
`original_end - original_start` is 2.  If you instead scan for `\r` and `\n`
independently you will see two endings and invent an empty line when
normalising.  This library picks the single-ending reading and tests it
explicitly.

Empty input is also handled: it reports `LF`, produces no records, and returns
an empty string.
