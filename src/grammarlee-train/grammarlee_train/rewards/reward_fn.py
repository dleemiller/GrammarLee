"""
Simple TRL-compatible reward function for GrammarLee.
"""

from __future__ import annotations
from typing import List, Dict, Optional

from grammarlee import parse_document
from .weights import load_config
from .aggregate import compute_reward, compute_component_scores

class GrammarLeeReward:
    """Simple reward function for GrammarLee training."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = load_config(config_path)
    
    def __call__(self, *, prompts: List[str], completions: List[List[Dict]], **batch) -> List[float]:
        """
        TRL-compatible reward function.
        
        Args:
            prompts: List of inline text (with anchors)
            completions: List of model completions (backmatter)
            
        Returns:
            List of rewards in [0, 1]
        """
        rewards = []
        
        for prompt, completion_msgs in zip(prompts, completions):
            # Extract generated backmatter
            backmatter = ""
            if completion_msgs and isinstance(completion_msgs[0], dict):
                backmatter = completion_msgs[0].get("content", "")
            
            # Combine into full document
            document = f"{prompt.rstrip()}\n\n--- BACKMATTER ---\n{backmatter.strip()}\n"
            
            # Parse and score
            try:
                parse_result = parse_document(document)
                breakdown = compute_reward(parse_result, self.config)
                rewards.append(breakdown.reward)
            except Exception:
                # On any error, give zero reward
                rewards.append(0.0)
        
        return rewards
    
    def evaluate_single(self, inline_text: str, backmatter: str) -> Dict:
        """Evaluate a single example with detailed breakdown."""
        document = f"{inline_text.rstrip()}\n\n--- BACKMATTER ---\n{backmatter.strip()}\n"
        parse_result = parse_document(document)
        
        # Get individual component scores
        scores = compute_component_scores(parse_result, self.config)
        
        # Compute final weighted reward
        breakdown = scores.compute(self.config)
        breakdown.parse_result = parse_result
        
        return {
            "reward": breakdown.reward,
            "gated": breakdown.gated,
            "notes": breakdown.notes,
            "components": {c.name: {"value": c.value, "details": c.details} for c in breakdown.components},
            "parse_errors": parse_result.errors,
            "num_anchors": len(parse_result.anchors),
            "num_edits": len(parse_result.edits),
            # Individual scores for direct access
            "individual_scores": {
                "has_backmatter": scores.has_backmatter.value,
                "no_parse_errors": scores.no_parse_errors.value,
                "anchors_covered": scores.anchors_covered.value,
                "action_consistency": scores.action_consistency.value,
                "valid_categories": scores.valid_categories.value,
                "comment_length": scores.comment_length.value,
                "no_duplicate_ids": scores.no_duplicate_ids.value
            }
        }

def make_reward_function(config_path: Optional[str] = None) -> GrammarLeeReward:
    """Create a reward function."""
    return GrammarLeeReward(config_path)
