import os
from typing import Literal

import dspy
from dotenv import load_dotenv
from grammarlee.judge import GrammarLeeJudge
from grammarlee.parser import parse_document
from grammarlee.signature import GrammarLeeSignature


load_dotenv()

MODEL_ID = os.getenv("MODEL_ID", "openrouter/google/gemini-2.0-flash-001")
lm = dspy.LM(MODEL_ID, api_key=os.environ["APIKEY"], temperature=0.5)
dspy.settings.configure(lm=lm)
editor = dspy.Predict(GrammarLeeSignature)

JUDGE_MODEL_ID = os.getenv("MODEL_ID", "openrouter/google/gemini-2.0-flash-001")
judge_lm = dspy.LM(JUDGE_MODEL_ID, api_key=os.environ["APIKEY"], temperature=0.0)
judge = dspy.Predict(GrammarLeeJudge)
judge.set_lm(judge_lm)


def main(edit_level: Literal["light", "medium", "heavy"] = "heavy"):
    text = "Da studnet are bored"
    pred = editor(text=text, edit_level=edit_level)

    result = parse_document(pred, text)
    _eval = judge(
        original_text=text, edited_text=result.final_text, edit_level=edit_level
    )
    print(result)
    print(_eval)


if __name__ == "__main__":
    main(edit_level="medium")
