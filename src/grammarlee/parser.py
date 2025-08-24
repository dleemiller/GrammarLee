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

# Delimiter tolerant to surrounding spaces
DELIM_RE = re.compile(r"^\s*--- BACKMATTER ---\s*$", flags=re.MULTILINE)

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

# -------------------------
# Grammar loading
# -------------------------

def _load_lark_grammar() -> str:
    with pkgres.files("grammarlee.grammar").joinpath("backmatter.lalr").open("r", encoding="utf-8") as f:
        return f.read()

# -------------------------
# Transformer
# -------------------------


@v_args(inline=True)
class _BackmatterTransformer(Transformer):
    def lines(self, *items):
        return list(items)

    def empty(self):
        return []

    # [ ID ] ACTION quoted -> quoted [CATEGORY] ( COMMENT )
    def line(self, _lb, id_tok, _rb, action_tok, old_q, _arrow, new_q, category_str, _lp, comment_str, _rp):
        return (int(id_tok.value), action_tok.value, old_q, new_q, category_str, comment_str)

    def quoted(self, tok: Token):
        s = tok.value[1:-1]
        if tok.type == "DQSTR":
            s = s.replace(r'\"', '"')
        elif tok.type == "SQSTR":
            s = s.replace(r"\'", "'")
    
        # Common escapes
        s = (s
             .replace(r"\\", "\\")
             .replace(r"\n", "\n")
             .replace(r"\r", "\r")
             .replace(r"\t", "\t"))
        return s
    

    # [CATEGORY] -> return just the inner token's value (no validation here!)
    def category(self, _lb, cat_tok: Token, _rb):
        return cat_tok.value

    # COMMENT as concatenation of CCHAR tokens, then unescape '\)' only
    def comment(self, tok=None):
        if tok is None:
            return ""
        return tok.value.replace(r"\)", ")")

    def empty_comment(self):
        return ""


# -------------------------
# Public API
# -------------------------

def split_sections(document: str) -> Tuple[str, str]:
    parts = DELIM_RE.split(document, maxsplit=1)
    if len(parts) == 2:
        inline_text, backmatter_text = parts
        return inline_text, backmatter_text.lstrip()
    return document, ""

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

def _parse_backmatter_raw(backmatter_text: str) -> List[tuple]:
    grammar = _load_lark_grammar()
    parser = Lark(
        grammar,
        start="start",
        parser="lalr",
        maybe_placeholders=False,
        propagate_positions=False,
        lexer="contextual",
    )
    tree = parser.parse(backmatter_text)
    return _BackmatterTransformer().transform(tree)

def parse_backmatter(backmatter_text: str) -> List[BackmatterEdit]:
    if not backmatter_text.strip():
        return []
    try:
        tuples = _parse_backmatter_raw(backmatter_text)
    except UnexpectedInput:
        return []
    edits: List[BackmatterEdit] = []
    for (id_num, action, old, new, category, comment) in tuples:
        cat_ok = category in VALID_CATEGORIES
        if action == Action.REPLACE.value:
            consistency_ok = (old != "") and (new != "")
        elif action == Action.INSERT.value:
            consistency_ok = (old == "") and (new != "")
        elif action == Action.DELETE.value:
            consistency_ok = (old != "") and (new == "")
        else:
            consistency_ok = False
        edits.append(BackmatterEdit(
            id=id_num,
            action=Action(action),
            old=old,
            new=new,
            category=category,
            comment=comment,
            is_valid_category=cat_ok,
            consistency_ok=consistency_ok,
        ))
    return edits

def parse_document(document: str) -> ParseResult:
    inline_text, backmatter_text = split_sections(document)
    anchors = parse_inline_anchors(inline_text)
    final_text = apply_inline(inline_text)
    edits = parse_backmatter(backmatter_text)

    errors: List[str] = []
    if backmatter_text.strip() and not edits:
        errors.append("Backmatter parse error: check grammar/quoting/categories.")

    return ParseResult(
        inline_text=inline_text,
        backmatter_text=backmatter_text,
        final_text=final_text,
        anchors=anchors,
        edits=edits,
        errors=errors,
    )

