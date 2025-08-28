import os
import dspy
from datasets import load_dataset

from .judge import GrammarLeeJudge
from .parser import parse_document
from .signature import GrammarLeeSignature

judge_lm = dspy.LM(
    os.getenv(
        "JUDGE_MODEL_ID",
        os.getenv("MODEL_ID", "openrouter/google/gemini-2.0-flash-001"),
    ),
    api_key=os.getenv("APIKEY", ""),
    temperature=0.0,
)
judge = dspy.ChainOfThought(GrammarLeeJudge)
judge.set_lm(judge_lm)


def load_grammar_dataset():
    dataset = load_dataset("dleemiller/grammar-correctable-texts", "gec")
    dev_data = dataset["dev"] if "dev" in dataset else dataset["train"]

    examples = []
    for item in dev_data:
        example = dspy.Example(text=item["text"]).with_inputs("text")
        examples.append(example)

    return examples


def reward_function(example, prediction, trace=None, pred_name=None, pred_trace=None):
    """GEPA reward function - returns dspy.Prediction(score, feedback)."""
    original_text = example.text

    # Structure score from parser
    parse_result = parse_document(prediction, original_text=original_text)
    structure_score = 1.0 - (len(parse_result.errors) * 0.2) if parse_result else 0.0
    structure_score = max(0.0, min(1.0, structure_score))

    # Judge score - use all judge components
    final_text = (
        parse_result.final_text
        if parse_result
        else getattr(prediction, "edited_text", "")
    )

    judge_result = judge(
        original_text=original_text,
        edited_text=final_text,
        edit_level=getattr(example, "edit_level", "medium"),
    )

    # Calculate judge score using all components
    judge_score = 0.0

    # Core requirements (60% of judge score)
    if getattr(judge_result, "is_grammar_correct", False):
        judge_score += 0.25
    if getattr(judge_result, "retains_original_meaning", False):
        judge_score += 0.25
    if not getattr(judge_result, "introduced_artifacts", True):  # False is good
        judge_score += 0.10

    # Quality metrics (40% of judge score)
    precision = getattr(judge_result, "edit_precision", "low")
    precision_scores = {"low": 0.0, "medium": 0.05, "high": 0.10}
    judge_score += precision_scores.get(precision, 0.0)

    recall = getattr(judge_result, "edit_recall", "low")
    recall_scores = {"low": 0.0, "medium": 0.05, "high": 0.10}
    judge_score += recall_scores.get(recall, 0.0)

    adherence = getattr(judge_result, "level_adherance", "low")
    adherence_scores = {"low": 0.0, "medium": 0.05, "high": 0.10}
    judge_score += adherence_scores.get(adherence, 0.0)

    # Combined score (50/50 as requested)
    combined_score = 0.5 * structure_score + 0.5 * judge_score

    # Feedback
    feedback_parts = [
        f"Score: {combined_score:.3f} (structure: {structure_score:.3f}, judge: {judge_score:.3f})"
    ]

    if pred_name == "predict":  # ChainOfThought module name
        if hasattr(prediction, "reasoning"):
            feedback_parts.append(f"Reasoning: {prediction.reasoning}")
        if parse_result and parse_result.errors:
            feedback_parts.append(f"Structure errors: {parse_result.errors}")

        # Judge details for feedback
        feedback_parts.append(
            f"Grammar correct: {getattr(judge_result, 'is_grammar_correct', False)}"
        )
        feedback_parts.append(
            f"Meaning retained: {getattr(judge_result, 'retains_original_meaning', False)}"
        )
        feedback_parts.append(
            f"Artifacts introduced: {getattr(judge_result, 'introduced_artifacts', True)}"
        )
        feedback_parts.append(
            f"Precision: {getattr(judge_result, 'edit_precision', 'low')}"
        )
        feedback_parts.append(f"Recall: {getattr(judge_result, 'edit_recall', 'low')}")
        feedback_parts.append(
            f"Level adherence: {getattr(judge_result, 'level_adherance', 'low')}"
        )

    if combined_score < 0.5:
        if structure_score < judge_score:
            feedback_parts.append("Focus on anchor format and edit alignment")
        else:
            feedback_parts.append("Focus on grammar accuracy and edit quality")

    feedback = " ".join(feedback_parts)
    return dspy.Prediction(score=combined_score, feedback=feedback)


def optimize_with_gepa(train_set, val_set):
    # Configure main LM
    lm = dspy.LM(
        os.getenv("MODEL_ID", "openrouter/google/gemini-2.0-flash-001"),
        api_key=os.getenv("APIKEY", ""),
        temperature=0.5,
    )
    dspy.settings.configure(lm=lm)

    # Configure GEPA
    reflection_lm = dspy.LM(
        os.getenv(
            "REFLECTION_MODEL_ID", "openrouter/anthropic/claude-3-5-sonnet-20241022"
        ),
        api_key=os.getenv("APIKEY", ""),
        temperature=1.0,
        max_tokens=32000,
    )

    optimizer = dspy.GEPA(
        metric=reward_function, auto="medium", reflection_lm=reflection_lm, seed=42
    )

    # Just return the ChainOfThought directly - no wrapper needed
    program = dspy.ChainOfThought(GrammarLeeSignature)

    return optimizer.compile(student=program, trainset=train_set, valset=val_set)
