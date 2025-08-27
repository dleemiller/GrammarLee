from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple

from pydantic import BaseModel


@dataclass
class InlineAnchor:
    """Inline anchors discovered in the text (before backmatter)."""
    id: int
    kind: str                 # "replace_or_insert" | "delete"
    new_text: str             # for replace/insert; "" for delete
    span: Tuple[int, int]     # (start, end) indices in the raw inline block

class Edit(BaseModel):
    """One normalized edit line."""
    id: int
    old: str
    new: str
    category: str
    comment: str

@dataclass
class ParseResult:
    """Reusable output for downstream tasks (runtime-safe)."""
    inline_text: str                 # raw inline block (with anchors)
    backmatter_text: str             # raw backmatter block
    final_text: str                  # inline text with anchors applied/stripped
    anchors: List[InlineAnchor]      # discovered inline anchors
    edits: List[Edit]      # parsed backmatter edits
    errors: List[str] = field(default_factory=list)

