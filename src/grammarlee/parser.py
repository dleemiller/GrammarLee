from __future__ import annotations

import importlib.resources as pkgres
import re
from typing import List, Tuple

from lark import Lark, Transformer, Token, v_args, UnexpectedInput
from .models import Action, BackmatterEdit, InlineAnchor, ParseResult

# -------------------------
# Config & patterns
# -------------------------

VALID_CATEGORIES = {
    "GRAMMAR", "SPELLING", "PUNCTUATION", "STYLE", "CLARITY", "WORD", "WORDINESS"
}


# Inline anchors:
#   [new text::ID] -> replacement/insertion
#   [#ID]          -> deletion (no visible text)
INLINE_TOKEN_RE = re.compile(
    r"""
    \[
      (?:
        (?P<new>[^\[\]#][^\[\]]*?)::(?P<id1>[1-9]\d*)
        |
        \#(?P<id2>[1-9]\d*)
      )
    \]
    """,
    re.VERBOSE,
)

def _unescape_minimal(s: str) -> str:
    """Minimal unescape used for back-matter quoted strings and inline render."""
    return (s.replace(r"\\", "\\")
             .replace(r"\"", "\"")
             .replace(r"\'", "'")
             .replace(r"\n", "\n")
             .replace(r"\r", "\r")
             .replace(r"\t", "\t"))

def parse_inline_anchors(inline_text: str) -> List[InlineAnchor]:
    anchors: List[InlineAnchor] = []
    for m in INLINE_TOKEN_RE.finditer(inline_text):
        if m.group("id1") is not None:
            anchors.append(InlineAnchor(
                id=int(m.group("id1")),
                kind="replace_or_insert",
                new_text=m.group("new"),  # store raw; unescape at render time
                span=m.span(),
            ))
        else:
            anchors.append(InlineAnchor(
                id=int(m.group("id2")),
                kind="delete",
                new_text="",
                span=m.span(),
            ))
    return anchors

def apply_inline(inline_text: str) -> str:
    def _repl(m: re.Match) -> str:
        if m.group("id1") is not None:
            return _unescape_minimal(m.group("new"))
        return ""
    rendered = INLINE_TOKEN_RE.sub(_repl, inline_text)
    return rendered.rstrip("\r\n")

def parse_document(pred: dspy.Example) -> ParseResult:
    inline_text = pred.edited_text
    anchors = parse_inline_anchors(inline_text)
    final_text = apply_inline(inline_text)
    edits = pred.edits

    errors: List[str] = []
    if len(anchors) != len(edits):
        errors.append("Edits not matching anchors.")
    if set(map(lambda x: x.id, anchors)) != set(map(lambda x: x.id, edits)):
        errors.append("Anchor IDs not matched.")

    return ParseResult(
        inline_text=inline_text,
        backmatter_text=backmatter_text,
        final_text=final_text,
        anchors=anchors,
        edits=edits,
        errors=errors,
    )

