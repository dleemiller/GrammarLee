import pytest
import dspy
from pathlib import Path

from grammarlee.optimize import reward_function
from grammarlee.models import Edit


class MockPrediction:
    def __init__(self):
        self.edited_text = "The [student::1] is bored."
        self.edits = [
            Edit(id=1, old="Da", new="The", category="GRAMMAR", comment="fix")
        ]
        self.reasoning = "Fixed the article."


def test_reward_function_format():
    """Test reward function returns correct GEPA format."""
    example = dspy.Example(text="Da studnet are bored").with_inputs("text")
    prediction = MockPrediction()

    result = reward_function(example, prediction)

    assert isinstance(result, dspy.Prediction)
    assert hasattr(result, "score")
    assert hasattr(result, "feedback")
    assert isinstance(result.score, (int, float))
    assert isinstance(result.feedback, str)


def test_reward_function_with_pred_name():
    """Test with pred_name parameter."""
    example = dspy.Example(text="Da studnet are bored").with_inputs("text")
    prediction = MockPrediction()

    result = reward_function(example, prediction, pred_name="predict")
    assert isinstance(result, dspy.Prediction)
