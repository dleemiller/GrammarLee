"""
Simple, direct reward components for GrammarLee training.
Uses the parser's built-in quality indicators directly.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Set
from collections import Counter

from grammarlee import ParseResult

@dataclass
class ComponentScore:
    name: str
    value: float
    details: Dict | None = None

def clamp01(x: float) -> float:
    """Clamp value to [0, 1] range."""
    return max(0.0, min(1.0, x))

def score_has_backmatter(pr: ParseResult) -> ComponentScore:
    """Check if backmatter delimiter was found."""
    has_content = bool(pr.backmatter_text and pr.backmatter_text.strip())
    return ComponentScore("has_backmatter", 1.0 if has_content else 0.0)

def score_no_parse_errors(pr: ParseResult) -> ComponentScore:
    """Check for absence of parse errors."""
    has_errors = len(pr.errors) > 0
    return ComponentScore("no_parse_errors", 0.0 if has_errors else 1.0)

def score_anchors_covered(pr: ParseResult) -> ComponentScore:
    """Check if all anchors have corresponding edits."""
    if not pr.anchors:
        return ComponentScore("anchors_covered", 1.0, {"anchor_ids": [], "edit_ids": []})
    
    anchor_ids = {a.id for a in pr.anchors}
    edit_ids = {e.id for e in pr.edits}
    
    covered = len(anchor_ids & edit_ids)
    total = len(anchor_ids)
    score = covered / total if total > 0 else 1.0
    
    return ComponentScore("anchors_covered", score, {
        "anchor_ids": sorted(anchor_ids),
        "edit_ids": sorted(edit_ids),
        "covered": covered,
        "total": total
    })

def score_action_consistency(pr: ParseResult) -> ComponentScore:
    """Use parser's built-in action consistency check."""
    if not pr.edits:
        # If we have anchors but no edits, that's a fundamental failure
        if pr.anchors:
            return ComponentScore("action_consistency", 0.0, {"consistent_count": 0, "total": 0, "reason": "anchors_present_but_no_edits"})
        else:
            return ComponentScore("action_consistency", 1.0, {"consistent_count": 0, "total": 0, "reason": "no_anchors_no_edits"})
    
    consistent = sum(1 for e in pr.edits if e.consistency_ok)
    total = len(pr.edits)
    score = consistent / total
    
    return ComponentScore("action_consistency", score, {
        "consistent_count": consistent,
        "total": total,
        "inconsistent_ids": [e.id for e in pr.edits if not e.consistency_ok]
    })

def score_valid_categories(pr: ParseResult) -> ComponentScore:
    """Use parser's built-in category validation."""
    if not pr.edits:
        # If we have anchors but no edits, that's a fundamental failure
        if pr.anchors:
            return ComponentScore("valid_categories", 0.0, {"valid_count": 0, "total": 0, "reason": "anchors_present_but_no_edits"})
        else:
            return ComponentScore("valid_categories", 1.0, {"valid_count": 0, "total": 0, "reason": "no_anchors_no_edits"})
    
    valid = sum(1 for e in pr.edits if e.is_valid_category)
    total = len(pr.edits)
    score = valid / total
    
    return ComponentScore("valid_categories", score, {
        "valid_count": valid,
        "total": total,
        "invalid": [(e.id, e.category) for e in pr.edits if not e.is_valid_category]
    })



def score_comment_length(pr: ParseResult, max_length: int = 100) -> ComponentScore:
    """Penalize overly long comments."""
    if not pr.edits:
        # If we have anchors but no edits, that's a fundamental failure
        if pr.anchors:
            return ComponentScore("comment_length", 0.0, {"lengths": [], "max_length": max_length, "reason": "anchors_present_but_no_edits"})
        else:
            return ComponentScore("comment_length", 1.0, {"lengths": [], "max_length": max_length, "reason": "no_anchors_no_edits"})
    
    lengths = [len(e.comment or "") for e in pr.edits]
    # Score based on how many are within reasonable length
    reasonable = sum(1 for length in lengths if length <= max_length)
    total = len(lengths)
    score = reasonable / total
    
    return ComponentScore("comment_length", score, {
        "lengths": lengths,
        "max_length": max_length,
        "reasonable_count": reasonable,
        "total": total,
        "too_long_ids": [e.id for e in pr.edits if len(e.comment or "") > max_length]
    })

def score_no_duplicate_ids(pr: ParseResult) -> ComponentScore:
    """Penalize duplicate IDs in anchors or edits."""
    anchor_ids = [a.id for a in pr.anchors]
    edit_ids = [e.id for e in pr.edits]
    
    anchor_counts = Counter(anchor_ids)
    edit_counts = Counter(edit_ids)
    
    # Count unique IDs vs total IDs
    unique_anchors = len(set(anchor_ids))
    unique_edits = len(set(edit_ids))
    total_anchors = len(anchor_ids)
    total_edits = len(edit_ids)
    
    if total_anchors + total_edits == 0:
        return ComponentScore("no_duplicate_ids", 1.0, {"duplicates": []})
    
    total_unique = unique_anchors + unique_edits
    total_ids = total_anchors + total_edits
    score = total_unique / total_ids
    
    duplicates = []
    for id_, count in anchor_counts.items():
        if count > 1:
            duplicates.append(f"anchor_{id_}")
    for id_, count in edit_counts.items():
        if count > 1:
            duplicates.append(f"edit_{id_}")
    
    return ComponentScore("no_duplicate_ids", score, {
        "duplicates": duplicates,
        "total_unique": total_unique,
        "total_ids": total_ids
    })
