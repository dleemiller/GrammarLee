"""
Tests for ChangeDetector class - focus on actual requirements and edge cases.
"""

import pytest
from grammarlee import ChangeDetector


class TestChangeDetector:
    
    def test_revert_all_requirement(self):
        """CORE REQUIREMENT: reject all must return exact original text."""
        detector = ChangeDetector()
        
        # Edge case: overlapping changes
        original = "The quick brown fox jumps over the lazy dog. It was sunny."
        revised = "A fast brown fox leaps over a sleeping dog. It is sunny."
        
        session = detector.detect_changes(original, revised)
        reject_all = {change.id: "reject" for change in session.changes}
        result = detector.apply_user_decisions(session, reject_all)
        
        assert result == original
    
    def test_accept_all_requirement(self):
        """CORE REQUIREMENT: accept all must return exact revised text."""
        detector = ChangeDetector()
        
        # Edge case: multiple insertions and deletions
        original = "I like cats and dogs but not birds."
        revised = "I really love cats, dogs, and also birds."
        
        session = detector.detect_changes(original, revised)
        accept_all = {change.id: "accept" for change in session.changes}
        result = detector.apply_user_decisions(session, accept_all)
        
        assert result == revised
    
    def test_monotonic_ids_requirement(self):
        """CORE REQUIREMENT: IDs must be monotonically increasing from 1."""
        detector = ChangeDetector()
        
        original = "First sentence. Second sentence. Third sentence."
        revised = "1st sentence. 2nd sentence. 3rd sentence."
        
        session = detector.detect_changes(original, revised)
        
        ids = [change.id for change in session.changes]
        assert ids == sorted(ids), "IDs not monotonic"
        assert min(ids) == 1, "IDs don't start at 1"
        assert max(ids) == len(ids), "IDs not consecutive"
    
    def test_complex_mixed_changes(self):
        """Test complex real-world editing scenario."""
        detector = ChangeDetector()
        
        original = "At present, I have three kinds of birds, one of them is yellow canary, the second one is finch, and the third one is combination of two kinds of birds, Each bird has his own special voice."
        revised = "Currently, I have three types of birds: one is a yellow canary, the second is a finch, and the third is a hybrid. Each bird has its own unique voice."
        
        session = detector.detect_changes(original, revised)
        
        # Test partial acceptance
        decisions = {}
        for i, change in enumerate(session.changes):
            decisions[change.id] = "accept" if i % 2 == 0 else "reject"
        
        result = detector.apply_user_decisions(session, decisions)
        
        # Result should be different from both original and revised
        assert result != original
        assert result != revised
        assert len(result) > 0
    
    def test_position_tracking_accuracy(self):
        """Test that change positions are tracked correctly through multiple edits."""
        detector = ChangeDetector()
        
        original = "abc def ghi jkl"
        revised = "ABC def GHI jkl"  # Change 1st and 3rd words only
        
        session = detector.detect_changes(original, revised)
        
        # Should have at least 2 changes
        assert len(session.changes) >= 2, f"Expected multiple changes, got {len(session.changes)}"
        
        # Accept only first change, reject the rest
        decisions = {}
        for i, change in enumerate(session.changes):
            decisions[change.id] = "accept" if i == 0 else "reject"
        
        result = detector.apply_user_decisions(session, decisions)
        
        # Should have only first change applied
        assert result != original, "Result should differ from original"
        assert result != revised, "Result should differ from fully revised"
        assert "ABC" in result, "First change should be applied"
    
    def test_no_changes_scenario(self):
        """Test when original and revised are identical."""
        detector = ChangeDetector()
        
        text = "This text is unchanged."
        session = detector.detect_changes(text, text)
        
        assert len(session.changes) == 0
        
        # Should still return original text
        result = detector.apply_user_decisions(session, {})
        assert result == text
