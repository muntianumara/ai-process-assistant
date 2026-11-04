"""
compare.py - Compares two evaluation runs and writes results/comparison_<old>_vs_<new>.md

It reads the saved results (it does NOT call the API) and shows:
  1. scores per category for both prompt versions (automatic check + LLM judge)
  2. which questions were fixed (FAIL -> PASS) or regressed (PASS -> FAIL)
  3. the exact differences between the two prompt files

Run:
    python src/compare.py v1 v2
"""

import difflib
import sys

from agent import PROMPTS_FOLDER
from evaluate import (
    JUDGE_MODEL,
    MODEL,
    RESULTS_FOLDER,
    compute_scores,
    load_saved_results,
)


def verdict_change(old_pass, new_pass):
    """Describe how one verdict changed between the two versions."""
    if old_pass == new_pass:
        return None
    return "fixed (FAIL -> PASS)" if new_pass else "REGRESSION (PASS -> FAIL)"


def compare(old_version, new_version):
    old_results = load_saved_results(old_version)
    new_results = load_saved_results(new_version)
    old_scores = compute_scores(old_results)
    new_scores = compute_scores(new_results)

    lines = [
        f"# Comparison: prompt {old_version} vs prompt {new_version}",
        "",
        f"- Agent model: `{MODEL}` (same for both versions)",
        f"- Judge model: `{JUDGE_MODEL}` (same for both versions)",
        "- Test set: `tests/test_cases.csv` (same 20 questions)",
        "- Only the prompt changed, so score differences come from the prompt.",
        "",
        "## 1. Scores per category",
        "",
        f"| Category | Automatic {old_version} | Automatic {new_version} "
        f"| Judge {old_version} | Judge {new_version} |",
        "|---|---|---|---|---|",
    ]
    for old_row, new_row in zip(old_scores, new_scores):
        lines.append(
            f"| {old_row['category']} | {old_row['automatic']} | {new_row['automatic']} "
            f"| {old_row['judge']} | {new_row['judge']} |"
        )

    # --- 2. Per-question changes ---------------------------------------------
    lines += ["", "## 2. Questions whose verdict changed", ""]
    new_by_id = {r["id"]: r for r in new_results}
    changes = []
    for old in old_results:
        new = new_by_id[old["id"]]
        auto_change = verdict_change(old["auto_pass"], new["auto_pass"])

        judge_change = None
        if old["judge_verdict"] in ("PASS", "FAIL") and new["judge_verdict"] in ("PASS", "FAIL"):
            judge_change = verdict_change(old["judge_verdict"] == "PASS",
                                          new["judge_verdict"] == "PASS")

        if auto_change or judge_change:
            changes.append(
                f"| {old['id']} | {old['question']} | {auto_change or 'no change'} "
                f"| {judge_change or 'no change'} |"
            )
    if changes:
        lines += ["| ID | Question | Automatic check | LLM judge |", "|---|---|---|---|"] + changes
    else:
        lines.append("No verdict changed.")

    # --- 3. Prompt differences -------------------------------------------------
    old_prompt = (PROMPTS_FOLDER / f"{old_version}.txt").read_text(encoding="utf-8").splitlines()
    new_prompt = (PROMPTS_FOLDER / f"{new_version}.txt").read_text(encoding="utf-8").splitlines()
    diff = difflib.unified_diff(old_prompt, new_prompt,
                                fromfile=f"prompts/{old_version}.txt",
                                tofile=f"prompts/{new_version}.txt", lineterm="")
    lines += [
        "",
        "## 3. What changed in the prompt",
        "",
        "Lines starting with `-` were removed, lines starting with `+` were added.",
        "",
        "```diff",
        *diff,
        "```",
    ]

    # The file name contains both versions, so a new comparison never overwrites an old one.
    output_file = RESULTS_FOLDER / f"comparison_{old_version}_vs_{new_version}.md"
    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_file


if __name__ == "__main__":
    old_version = sys.argv[1] if len(sys.argv) > 1 else "v1"
    new_version = sys.argv[2] if len(sys.argv) > 2 else "v2"
    print(f"Written: {compare(old_version, new_version)}")
