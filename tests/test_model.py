"""
Tests for models - focus on serialization edge cases and data integrity.
"""

import pytest
import json
from grammarlee import Change, TextEditSession


class TestTextEditSessionSerialization:
    
    def test_json_roundtrip_preserves_data(self):
        """Test that JSON export/import preserves all data exactly."""
        changes = [
            Change(1, "replace", "original", "revised", 0, 8, "test annotation"),
            Change(2, "insert", "", "new text", 10, 10),
            Change(3, "delete", "removed", "", 15, 22, None)
        ]
        
        original = TextEditSession("Original text here", "Revised text here", changes)
        
        # Round trip through JSON
        json_str = original.to_json()
        restored = TextEditSession.from_json(json_str)
        
        # Verify everything is preserved
        assert restored.original_text == original.original_text
        assert restored.revised_text == original.revised_text
        assert len(restored.changes) == len(original.changes)
        
        for orig_change, restored_change in zip(original.changes, restored.changes):
            assert orig_change.id == restored_change.id
            assert orig_change.type == restored_change.type
            assert orig_change.original == restored_change.original
            assert orig_change.revised == restored_change.revised
            assert orig_change.start_pos == restored_change.start_pos
            assert orig_change.end_pos == restored_change.end_pos
            assert orig_change.annotation == restored_change.annotation
    
    def test_json_handles_special_characters(self):
        """Test JSON serialization with problematic characters."""
        changes = [
            Change(1, "replace", 'text with "quotes"', "text with 'quotes'", 0, 15),
            Change(2, "insert", "", "text\nwith\nnewlines", 20, 20),
            Change(3, "delete", "unicode: 世界 🌍", "", 25, 35)
        ]
        
        session = TextEditSession("Original with\ttabs", "Revised\nwith\nnewlines", changes)
        
        # Should not raise exception
        json_str = session.to_json()
        restored = TextEditSession.from_json(json_str)
        
        # Verify special characters preserved
        assert restored.changes[0].original == 'text with "quotes"'
        assert "\n" in restored.changes[1].revised
        assert "世界" in restored.changes[2].original
    
    def test_empty_session_serialization(self):
        """Test serialization of session with no changes."""
        session = TextEditSession("same text", "same text", [])
        
        json_str = session.to_json()
        restored = TextEditSession.from_json(json_str)
        
        assert restored.original_text == "same text"
        assert restored.revised_text == "same text"
        assert len(restored.changes) == 0
    
    def test_invalid_json_raises_error(self):
        """Test that invalid JSON raises appropriate error."""
        with pytest.raises((json.JSONDecodeError, KeyError, TypeError)):
            TextEditSession.from_json("invalid json")
        
        with pytest.raises((KeyError, TypeError)):
            TextEditSession.from_json('{"missing": "required_fields"}')
