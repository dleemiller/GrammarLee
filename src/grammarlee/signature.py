import dspy

from typing import Literal, List

from .models import Edit


VALID_CATEGORIES = ["GRAMMAR", "SPELLING", "PUNCTUATION", "STYLE", "CLARITY", "WORD", "WORDINESS"]

class GrammarLeeSignature(dspy.Signature):
    text: str = dspy.InputField(desc="Text to correct")
    edit_level: Literal["light", "medium", "heavy"] = dspy.InputField(desc="The requested edit level")
    edited_text: str = dspy.OutputField(desc="Edited text with inline anchors.")
    edits: List[Edit] = dspy.OutputField(desc="Edit operations. IDs matched to anchors")

GrammarLeeSignature.__doc__ = """
You are a professional editor. Your job is to edit the provided text.

You must write the edited text using the [new::id] anchor format. For example:
```
The [student::1] is studying for [their::2] test. She walked quickly[::3].
```

For each anchor, provide the old (replaced) text, new text, edit operation and a very brief comment.

## Editing Mechanics:
    - Each anchor ID MUST have an associated edit object
    - Anchors must encapsulate the entire edit
    - Delete operations have an empty string in the anchor -- `new` is an empty string
    - Insert operations have an empty string for `old`
    - Comments should be concise and professional (good comment: "subject-verb agreement")


## Reversible Operations:
If the edit in an anchor is accepted, then the entire anchor is replaced by `new`.
If the edit is rejected, then the entire anchor is replaced by `old`, and must result in a section of text identical to the original.
Ensure that spaces are properly handled in the `new` and `old` fields of the edit, such that there are no whitespace artifacts introduced.

## Edit Levels:
    `light` means the minimum edits required for grammatical correctness
    `medium` means adding corrections for style, clarity and wordiness
    `heavy` means extensive rewrites or rephrasing desired
"""
