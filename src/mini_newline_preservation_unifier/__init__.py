"""Public API for mini_newline_preservation_unifier.

Only the names listed in ``__all__`` are considered stable.  The
implementation lives in :mod:`mini_newline_preservation_unifier.core`.
"""

from .core import (
    NewlineStyle,
    LineEndingRecord,
    UnifyResult,
    detect_newline_style,
    unify_newlines,
)

__all__ = [
    "NewlineStyle",
    "LineEndingRecord",
    "UnifyResult",
    "detect_newline_style",
    "unify_newlines",
]
