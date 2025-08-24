"""
Simple configuration for GrammarLee rewards.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional
import yaml

# Simple default configuration
DEFAULT_CONFIG = {
    "gate_on_parse_errors": True,
    "gate_on_duplicate_ids": False,  # Option to gate on duplicates
    "gate_on_extreme_comments": True,  # Gate on extremely long comments
    "max_comment_length": 100,
    "extreme_comment_length": 200,  # Gate threshold
    
    # Component weights - rebalanced for GRPO effectiveness
    "weights": {
        "has_backmatter": 0.1,
        "no_parse_errors": 0.15,
        "anchors_covered": 0.3,        # Most critical
        "action_consistency": 0.25,    # Most critical
        "valid_categories": 0.1,
        "comment_length": 0.1,         # Increased from 0.03 - meaningful penalty
        "no_duplicate_ids": 0.1        # Increased from 0.02 - duplicates are serious
    }
}

def load_config(config_path: Optional[str] = None) -> Dict:
    """Load configuration, merging with defaults."""
    config = DEFAULT_CONFIG.copy()
    
    if config_path:
        path = Path(config_path)
        if path.exists():
            with path.open('r') as f:
                user_config = yaml.safe_load(f) or {}
            
            # Simple merge - overwrite defaults
            config.update(user_config)
            if "weights" in user_config:
                config["weights"].update(user_config["weights"])
    
    return config

def save_config(config: Dict, output_path: str) -> None:
    """Save configuration to file."""
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
