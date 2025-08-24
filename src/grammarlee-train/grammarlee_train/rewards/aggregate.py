"""
Clean aggregation with individually addressable component scores.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict

from grammarlee import ParseResult
from .components import (
    ComponentScore, score_has_backmatter, score_no_parse_errors,
    score_anchors_covered, score_action_consistency, score_valid_categories,
    score_comment_length, score_no_duplicate_ids, clamp01
)

@dataclass
class ComponentScores:
    """Individual component scores before weighting."""
    has_backmatter: ComponentScore
    no_parse_errors: ComponentScore
    anchors_covered: ComponentScore
    action_consistency: ComponentScore
    valid_categories: ComponentScore
    comment_length: ComponentScore
    no_duplicate_ids: ComponentScore
    
    def to_list(self) -> List[ComponentScore]:
        """Convert to list for compatibility."""
        return [
            self.has_backmatter,
            self.no_parse_errors,
            self.anchors_covered,
            self.action_consistency,
            self.valid_categories,
            self.comment_length,
            self.no_duplicate_ids
        ]
    
    def compute(self, config: Dict) -> RewardBreakdown:
        """Apply weights and compute final reward."""
        components = self.to_list()
        notes = []
        
        # Check gating conditions
        gated = False
        
        # Gate on parse errors
        if config.get("gate_on_parse_errors", True) and self.no_parse_errors.value == 0.0:
            gated = True
            notes.append("Gated due to parse errors")
        
        # Gate on duplicate IDs (optional)
        elif config.get("gate_on_duplicate_ids", False) and self.no_duplicate_ids.value < 1.0:
            gated = True
            notes.append("Gated due to duplicate IDs")
        
        # Gate on extremely long comments (requires parse_result for detailed check)
        # This will be handled at the compute_reward level
        
        if gated:
            return RewardBreakdown(None, True, components, 0.0, notes)
        
        # Apply weights and compute weighted average
        weights = config.get("weights", {})
        total_weighted = 0.0
        total_weight = 0.0
        
        for comp in components:
            weight = weights.get(comp.name, 1.0)  # Default weight of 1.0
            total_weighted += weight * comp.value
            total_weight += weight
        
        reward = total_weighted / total_weight if total_weight > 0 else 0.0
        reward = clamp01(reward)
        
        # Add notes for debugging
        if reward < 0.3:
            low_components = [c.name for c in components if c.value < 0.5]
            if low_components:
                notes.append(f"Low scoring components: {', '.join(low_components)}")
        
        return RewardBreakdown(None, False, components, reward, notes)

@dataclass
class RewardBreakdown:
    parse_result: ParseResult | None  # Optional for flexibility
    gated: bool
    components: List[ComponentScore]
    reward: float
    notes: List[str]

def compute_component_scores(parse_result: ParseResult, config: Dict) -> ComponentScores:
    """Compute individual component scores."""
    return ComponentScores(
        has_backmatter=score_has_backmatter(parse_result),
        no_parse_errors=score_no_parse_errors(parse_result),
        anchors_covered=score_anchors_covered(parse_result),
        action_consistency=score_action_consistency(parse_result),
        valid_categories=score_valid_categories(parse_result),
        comment_length=score_comment_length(parse_result, config.get("max_comment_length", 100)),
        no_duplicate_ids=score_no_duplicate_ids(parse_result)
    )

def compute_reward(parse_result: ParseResult, config: Dict) -> RewardBreakdown:
    """
    Compute reward from parse result.
    
    Two-step process:
    1. Compute individual component scores
    2. Apply weights and compute final reward
    """
    # Get individual component scores
    scores = compute_component_scores(parse_result, config)
    
    # Check for extreme comment gating (needs parse_result access)
    if config.get("gate_on_extreme_comments", True):
        extreme_threshold = config.get("extreme_comment_length", 200)
        for edit in parse_result.edits:
            if len(edit.comment or "") > extreme_threshold:
                return RewardBreakdown(
                    parse_result, True, scores.to_list(), 0.0,
                    [f"Gated due to extremely long comment (>{extreme_threshold} chars)"]
                )
    
    # Compute final weighted reward
    breakdown = scores.compute(config)
    breakdown.parse_result = parse_result  # Add parse result to final breakdown
    
    # Additional contextual notes
    if len(parse_result.edits) == 0 and len(parse_result.anchors) > 0:
        breakdown.notes.append("Anchors present but no edits generated")
    
    return breakdown
