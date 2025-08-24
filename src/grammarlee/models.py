from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple

class Action(str, Enum):
    REPLACE = "REPLACE"
    INSERT = "INSERT"
    DELETE = "DELETE"

@dataclass
class InlineAnchor:
    """Inline anchors discovered in the text (before backmatter)."""
    id: int
    kind: str                 # "replace_or_insert" | "delete"
    new_text: str             # for replace/insert; "" for delete
    span: Tuple[int, int]     # (start, end) indices in the raw inline block

@dataclass
class BackmatterEdit:
    """One normalized back-matter edit line."""
    id: int
    action: Action
    old: str
    new: str
    category: str
    comment: str
    is_valid_category: bool = True
    consistency_ok: bool = True

@dataclass
class ParseResult:
    """Reusable output for downstream tasks (runtime-safe)."""
    inline_text: str                 # raw inline block (with anchors)
    backmatter_text: str             # raw backmatter block
    final_text: str                  # inline text with anchors applied/stripped
    anchors: List[InlineAnchor]      # discovered inline anchors
    edits: List[BackmatterEdit]      # parsed backmatter edits
    errors: List[str] = field(default_factory=list)

