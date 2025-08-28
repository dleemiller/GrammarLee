#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "src"))

from grammarlee.optimize import load_grammar_dataset, optimize_with_gepa


def main():
    load_dotenv()

    if "APIKEY" not in os.environ:
        print("Error: APIKEY environment variable not set")
        return 1

    print("Loading dataset...")
    dataset = load_grammar_dataset()

    split_point = int(0.7 * len(dataset))
    train_set = dataset[:split_point]
    val_set = dataset[split_point:]

    print(f"Training: {len(train_set)}, Validation: {len(val_set)}")
    print("Running GEPA optimization...")

    try:
        optimized_program = optimize_with_gepa(train_set, val_set)
        optimized_program.save("optimized_grammar_program.json")
        print("Optimization complete. Saved to optimized_grammar_program.json")

        # Quick test
        result = optimized_program(text="Da studnet are bored", edit_level="medium")
        print(f"Test result: {getattr(result, 'edited_text', result)}")

        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
