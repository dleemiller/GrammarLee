"""
Change detection and management for LLM text editing.
"""

from __future__ import annotations
import re
from typing import Dict, List, Tuple
from difflib import SequenceMatcher

from .models import Change, TextEditSession


class ChangeDetector:
    """Detects and manages changes between original and revised text."""
    
    def __init__(self):
        self._change_id_counter = 0
    
    def detect_changes(self, original: str, revised: str) -> TextEditSession:
        """
        Detect changes between original and revised text.
        Returns a TextEditSession with detected changes.
        """
        # Reset counter for new session
        self._change_id_counter = 0
        
        # Use word-level diffing for better semantic grouping
        original_words = self._tokenize_with_positions(original)
        revised_words = self._tokenize_with_positions(revised)
        
        original_tokens = [w[0] for w in original_words]
        revised_tokens = [w[0] for w in revised_words]
        
        matcher = SequenceMatcher(a=original_tokens, b=revised_tokens, autojunk=False)
        
        changes = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue
            
            # Get text segments
            if i1 < i2:
                start_pos = original_words[i1][1]  # Start of first changed token
                end_pos = original_words[i2-1][2]  # End of last changed token
                original_segment = original[start_pos:end_pos]
            else:
                # Insert case - position between tokens
                start_pos = original_words[i1][1] if i1 < len(original_words) else len(original)
                end_pos = start_pos
                original_segment = ""
            
            if j1 < j2:
                revised_start = revised_words[j1][1] if j1 < len(revised_words) else len(revised)
                revised_end = revised_words[j2-1][2] if j2 <= len(revised_words) else len(revised)
                revised_segment = revised[revised_start:revised_end]
            else:
                revised_segment = ""
            
            # Determine change type
            if original_segment and revised_segment:
                change_type = "replace"
            elif original_segment:
                change_type = "delete"
            elif revised_segment:
                change_type = "insert"
            else:
                continue  # Skip empty changes
            
            # Create change with monotonic ID
            change = Change(
                id=self._next_change_id(),
                type=change_type,
                original=original_segment,
                revised=revised_segment,
                start_pos=start_pos,
                end_pos=end_pos
            )
            
            changes.append(change)
        
        return TextEditSession(
            original_text=original,
            revised_text=revised,
            changes=changes
        )
    
    def _next_change_id(self) -> int:
        """Get next monotonic change ID."""
        self._change_id_counter += 1
        return self._change_id_counter
    
    def _tokenize_with_positions(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Tokenize text into words with their character positions.
        Returns list of (token, start_pos, end_pos).
        """
        # Match words, numbers, or single punctuation
        pattern = r'\b\w+\b|\S'
        tokens = []
        
        for match in re.finditer(pattern, text):
            token = match.group()
            start = match.start()
            end = match.end()
            tokens.append((token, start, end))
        
        return tokens
    
    def add_annotation(self, session: TextEditSession, change_id: int, annotation: str) -> bool:
        """Add LLM annotation to a specific change."""
        for change in session.changes:
            if change.id == change_id:
                change.annotation = annotation
                return True
        return False
    
    def apply_user_decisions(self, session: TextEditSession, decisions: Dict[int, str]) -> str:
        """
        Apply user accept/reject decisions to generate final text.
        
        Args:
            session: The TextEditSession containing original text and changes
            decisions: Dict mapping change_id -> "accept" | "reject"
        
        Returns:
            Final text with decisions applied
            
        Note: If all changes are rejected, returns original text.
              If all changes are accepted, returns revised text.
        """
        # Quick path: if all rejected, return original
        if all(decisions.get(change.id, "reject") == "reject" for change in session.changes):
            return session.original_text
            
        # Quick path: if all accepted, return revised
        if all(decisions.get(change.id, "reject") == "accept" for change in session.changes):
            return session.revised_text
        
        # Build result by processing original text and applying accepted changes
        result = []
        last_pos = 0
        
        # Sort changes by start position
        sorted_changes = sorted(session.changes, key=lambda c: c.start_pos)
        
        for change in sorted_changes:
            decision = decisions.get(change.id, "reject")
            
            # Add text before this change
            if change.start_pos > last_pos:
                result.append(session.original_text[last_pos:change.start_pos])
            
            if decision == "accept":
                # Use the revised text
                if change.type == "insert":
                    result.append(change.revised)
                    last_pos = change.start_pos  # Insert doesn't advance position in original
                elif change.type == "delete":
                    # Skip the deleted text, don't add anything
                    last_pos = change.end_pos
                elif change.type == "replace":
                    result.append(change.revised)
                    last_pos = change.end_pos
            else:  # reject
                # Use the original text  
                if change.type == "insert":
                    # Skip the insertion, don't add anything
                    last_pos = change.start_pos
                elif change.type == "delete":
                    # Keep the deleted text
                    result.append(change.original)
                    last_pos = change.end_pos
                elif change.type == "replace":
                    # Keep the original text
                    result.append(change.original)  
                    last_pos = change.end_pos
        
        # Add remaining text
        if last_pos < len(session.original_text):
            result.append(session.original_text[last_pos:])
        
        return ''.join(result)
