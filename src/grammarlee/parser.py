from __future__ import annotations

import re
from typing import Iterator, List, Tuple, Any

from .models import InlineAnchor, ParseResult, Edit  # keep your own models

# Explicit export so it's obvious what's public
__all__ = [
    "INLINE_TOKEN_RE",
    "iter_inline_matches",
    "parse_inline_anchors",
    "apply_inline",
    "parse_document",
]

# --------------------------------------------------------------------
# Inline anchors (depth-aware):
#   [new text::ID] -> replace/insert
#   [::ID]         -> delete (empty replacement)
# --------------------------------------------------------------------
INLINE_TOKEN_RE = re.compile(
    r"""
    \[
      (?P<new>[^\[\]]*?)      # new text (no brackets)
      ::
      (?P<id>[1-9]\d*)        # positive integer ID
    \]
    """,
    re.VERBOSE,
)

def _unescape_minimal(s: str) -> str:
    # keep your unescape semantics here
    return (s.replace(r"\\", "\\")
             .replace(r"\"", "\"")
             .replace(r"\'", "'")
             .replace(r"\n", "\n")
             .replace(r"\r", "\r")
             .replace(r"\t", "\t"))

def iter_inline_matches(s: str) -> Iterator[re.Match]:
    """
    Yield INLINE_TOKEN_RE matches only at bracket-depth 0.
    Prevents false positives like '[a[b::1]'.
    """
    i, n, depth = 0, len(s), 0
    while i < n:
        ch = s[i]
        if ch == '[':
            if depth == 0:
                m = INLINE_TOKEN_RE.match(s, i)
                if m:
                    yield m
                    i = m.end()
                    continue
            depth += 1
        elif ch == ']':
            depth = max(0, depth - 1)
        i += 1

def parse_inline_anchors(inline_text: str) -> List[InlineAnchor]:
    anchors: List[InlineAnchor] = []
    for m in iter_inline_matches(inline_text):
        new = m.group("new")
        anchors.append(InlineAnchor(
            id=int(m.group("id")),
            kind="delete" if new == "" else "replace_or_insert",
            new_text=new,          # keep raw; unescape later
            span=m.span(),
        ))
    return anchors

def apply_inline(inline_text: str) -> str:
    """
    Render inline anchors by substituting:
      - replace/insert -> unescaped new text
      - delete         -> empty string
    """
    out: List[str] = []
    last = 0
    for m in iter_inline_matches(inline_text):
        out.append(inline_text[last:m.start()])
        out.append(_unescape_minimal(m.group("new")))  # empty => delete
        last = m.end()
    out.append(inline_text[last:])
    return "".join(out).rstrip("\r\n")

# --------------------------------------------------------------------
# Public entry point used by tests/callers
# --------------------------------------------------------------------
def parse_document(pred: Any) -> ParseResult:
    """
    Build a ParseResult from a prediction-like object.

    Expected attributes on `pred`:
      - edited_text: str     (required)
      - edits: List[Edit]    (optional; default empty)
      - backmatter_text: str (optional; default "")
    """
    inline_text: str = getattr(pred, "edited_text", "") or ""
    edits: List[Edit] = list(getattr(pred, "edits", []) or [])
    backmatter_text: str = getattr(pred, "backmatter_text", "") or ""

    anchors = parse_inline_anchors(inline_text)
    final_text = apply_inline(inline_text)

    errors: List[str] = []
    anchor_ids = {a.id for a in anchors}
    edit_ids = {e.id for e in edits} if edits else set()

    if edits and (len(anchors) != len(edits)):
        errors.append("Edits not matching anchors.")
    if edits and (anchor_ids != edit_ids):
        errors.append("Anchor IDs not matched.")

    return ParseResult(
        inline_text=inline_text,
        backmatter_text=backmatter_text,
        final_text=final_text,
        anchors=anchors,
        edits=edits,
        errors=errors,
    )

