"""
Data models for LLM text editing with change tracking.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
import json


@dataclass
class Change:
    """Represents a single text change with stable ID."""
    id: int                   # Monotonically increasing ID
    type: str                 # "insert", "delete", "replace" 
    original: str             # Original text (empty for inserts)
    revised: str              # Revised text (empty for deletes)
    start_pos: int           # Character position in original text
    end_pos: int             # Character position in original text
    annotation: Optional[str] = None  # Optional LLM annotation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class TextEditSession:
    """Container for a complete text editing session."""
    original_text: str
    revised_text: str
    changes: List[Change]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'original_text': self.original_text,
            'revised_text': self.revised_text,
            'changes': [change.to_dict() for change in self.changes]
        }
    
    def to_json(self) -> str:
        """Export as JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TextEditSession:
        """Create instance from dictionary."""
        return cls(
            original_text=data['original_text'],
            revised_text=data['revised_text'],
            changes=[Change(**change_data) for change_data in data['changes']]
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> TextEditSession:
        """Create instance from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
