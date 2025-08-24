#!/usr/bin/env python3
"""
Simple test suite for GrammarLee reward system.
"""

def test_perfect_case():
    """Test perfect case gets high reward."""
    from grammarlee import parse_document
    from grammarlee_train.rewards.aggregate import compute_component_scores
    from grammarlee_train.rewards.weights import load_config
    
    document = '''Fix the [word::1] here.

--- BACKMATTER ---
[1] REPLACE "word" -> "term" [GRAMMAR](better choice)'''
    
    parse_result = parse_document(document)
    scores = compute_component_scores(parse_result, load_config())
    breakdown = scores.compute(load_config())
    
    assert breakdown.reward > 0.9, f"Expected high reward, got {breakdown.reward}"
    assert not breakdown.gated
    print(f"✓ Perfect case: {breakdown.reward:.3f}")

def test_parse_errors():
    """Test parse errors gate to zero."""
    from grammarlee import parse_document
    from grammarlee_train.rewards.aggregate import compute_component_scores
    from grammarlee_train.rewards.weights import load_config
    
    document = '''Fix the [word::1] here.

--- BACKMATTER ---
malformed backmatter'''
    
    parse_result = parse_document(document)
    scores = compute_component_scores(parse_result, load_config())
    breakdown = scores.compute(load_config())
    
    assert breakdown.gated, "Should be gated"
    assert breakdown.reward == 0.0, "Gated reward should be 0"
    print(f"✓ Parse errors: gated={breakdown.gated}")

def test_missing_edits():
    """Test anchors without edits get low reward."""
    from grammarlee import parse_document
    from grammarlee_train.rewards.aggregate import compute_component_scores
    from grammarlee_train.rewards.weights import load_config
    
    document = '''Fix the [word::1] and [term::2] here.

--- BACKMATTER ---
'''
    
    parse_result = parse_document(document)
    scores = compute_component_scores(parse_result, load_config())
    breakdown = scores.compute(load_config())
    
    assert breakdown.reward < 0.4, f"Expected low reward, got {breakdown.reward}"
    assert scores.anchors_covered.value == 0.0, "Should have no coverage"
    print(f"✓ Missing edits: {breakdown.reward:.3f}")

def test_duplicate_ids():
    """Test duplicate IDs are penalized."""
    from grammarlee import parse_document
    from grammarlee_train.rewards.aggregate import compute_component_scores
    from grammarlee_train.rewards.weights import load_config
    
    document = '''Fix [word::1] and [term::1] here.

--- BACKMATTER ---
[1] REPLACE "word" -> "better" [GRAMMAR](fix)'''
    
    parse_result = parse_document(document)
    scores = compute_component_scores(parse_result, load_config())
    
    assert scores.no_duplicate_ids.value < 1.0, "Should penalize duplicates"
    print(f"✓ Duplicates: {scores.no_duplicate_ids.value:.3f}")

def test_wrong_actions():
    """Test wrong action types are penalized."""
    from grammarlee import parse_document
    from grammarlee_train.rewards.aggregate import compute_component_scores
    from grammarlee_train.rewards.weights import load_config
    
    document = '''Fix the [word::1] here.

--- BACKMATTER ---
[1] INSERT "word" -> "term" [GRAMMAR](wrong action)'''
    
    parse_result = parse_document(document)
    scores = compute_component_scores(parse_result, load_config())
    
    assert scores.action_consistency.value < 1.0, "Should penalize wrong action"
    print(f"✓ Wrong actions: {scores.action_consistency.value:.3f}")

def test_realistic_example():
    """Test realistic multi-edit scenario."""
    from grammarlee import parse_document
    from grammarlee_train.rewards.aggregate import compute_component_scores
    from grammarlee_train.rewards.weights import load_config
    
    document = '''The [companie's::1] new [stratagey::2] is [definately::3] working.

--- BACKMATTER ---
[1] REPLACE "companie's" -> "company's" [SPELLING](fix apostrophe)
[2] REPLACE "stratagey" -> "strategy" [SPELLING](misspelling)  
[3] REPLACE "definately" -> "definitely" [SPELLING](common error)'''
    
    parse_result = parse_document(document)
    scores = compute_component_scores(parse_result, load_config())
    breakdown = scores.compute(load_config())
    
    assert breakdown.reward > 0.8, f"Expected high reward, got {breakdown.reward}"
    assert scores.anchors_covered.value == 1.0, "Should have full coverage"
    print(f"✓ Realistic: {breakdown.reward:.3f}")

def test_component_access():
    """Test individual component access works."""
    from grammarlee import parse_document
    from grammarlee_train.rewards.aggregate import compute_component_scores
    from grammarlee_train.rewards.weights import load_config
    
    document = '''Fix the [word::1] here.

--- BACKMATTER ---
[1] REPLACE "word" -> "term" [GRAMMAR](good)'''
    
    parse_result = parse_document(document)
    scores = compute_component_scores(parse_result, load_config())
    
    # Test individual component access
    assert hasattr(scores, 'has_backmatter')
    assert hasattr(scores, 'anchors_covered')
    assert hasattr(scores, 'action_consistency')
    
    assert scores.has_backmatter.value == 1.0
    assert scores.anchors_covered.value == 1.0
    assert scores.action_consistency.value == 1.0
    
    print(f"✓ Component access works")

def run_all_tests():
    """Run all tests."""
    print("GrammarLee Reward Tests")
    print("=" * 25)
    
    test_perfect_case()
    test_parse_errors()  
    test_missing_edits()
    test_duplicate_ids()
    test_wrong_actions()
    test_realistic_example()
    test_component_access()
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    run_all_tests()
