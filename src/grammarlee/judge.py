from typing import Literal

import dspy


class GrammarLeeJudge(dspy.Signature):
    original_text: str = dspy.InputField()
    edited_text: str = dspy.InputField()
    edit_level: Literal["light", "medium", "heavy"] = dspy.InputField()

    is_grammar_correct: bool = dspy.OutputField(
        desc="Is the final text grammatically correct?"
    )
    retains_original_meaning: bool = dspy.OutputField(
        desc="Does the edited text retain the original meaning?"
    )
    introduced_artifacts: bool = dspy.OutputField(
        desc="Did editing cause artifacts? (eg. double spaces, brackets)"
    )

    edit_precision: Literal["low", "medium", "high"] = dspy.OutputField()
    edit_recall: Literal["low", "medium", "high"] = dspy.OutputField()
    level_adherance: Literal["low", "medium", "high"] = dspy.OutputField()


GrammarLeeJudge.__doc__ = """
Your job is to evaluate how well an editor did at editing text.

The edited text -- above all -- must be grammatically correct. Secondarily, it should follow the style of
the original text (grammatical errors, lack of clarity, wordiness, spelling, etc are NOT considered stylistic).

Edit precision:
    `low` means there is a grammar error added by an edit, or 2 or more edits that could be meaningfully improved
    `medium` means there is one edit operation that could be significantly improved
    `high` means that all edit operations were of good quality

Edit recall:
    `low` means that there is a grammar error that was not fixed, or 2 or more missed edit operations
    `medium` means that there is one missed edit operation
    `high` means that text was edited appropriately

Edit Levels:
    `light` means the minimum edits required for grammatical correctness
    `medium` means adding corrections for style, clarity and wordiness
    `heavy` means extensive rewrites or rephrasing desired

Level Adherance:
    `low` means that the amount of editing diverged significantly from what was requested
    `medium` means that the amount of editing was slightly over or under requested
    `high` means that the requested level was followed well
"""
