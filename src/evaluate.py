"""
evaluate.py - Runs the agent on every test question and scores the answers.

Built step by step:
  6.1 Run the agent on all test questions and save the answers
  6.2 Simple automatic check (keywords + cited source)
  6.3 LLM-as-judge
  6.4 Scores per category + summary file

Run:
    python src/evaluate.py v1
Uses prompts/v1.txt and saves:
    results/run_v1.csv      every question, answer and verdict
    results/summary_v1.md   scores per category + disagreements + failed tests

Re-judge only the rows where the judge failed (ERROR), without asking the agent again:
    python src/evaluate.py v1 --rejudge
"""

import csv
import json
import sys
import time
from datetime import datetime

from google import genai

# We reuse the agent's own functions, so we test exactly the code a user would run.
from agent import (
    MODEL,
    PROJECT_ROOT,
    ask_gemini,
    build_system_instruction,
    is_unanswered,
    load_documents,
    load_prompt,
)

TEST_FILE = PROJECT_ROOT / "tests" / "test_cases.csv"
RESULTS_FOLDER = PROJECT_ROOT / "results"
PAUSE_SECONDS = 4  # pause after each agent call (free tier: 15 requests/minute)

# The judge is a model from a DIFFERENT family (Gemma, not Gemini):
# a model tends to grade its own answers too kindly (self-preference bias).
# Free tier for Gemma 4 31B: 14,400 requests/day, but only 16K tokens/minute.
# One judge call sends ~3,300 tokens (documents + answer), so we wait 15 s
# after each judge call to stay under ~4 calls per minute.
# (gemini-3.5-flash was tried first, but its free tier allows only 20 requests/day.)
JUDGE_MODEL = "gemma-4-31b-it"
JUDGE_PAUSE_SECONDS = 15

# The agent may cite a document by its file name, its title or its ID.
# We accept all three forms: we check WHICH document it cites, not the style.
SOURCE_NAMES = {
    "leave_policy.md": ["leave_policy.md", "Leave Policy", "HR-POL-004"],
    "it_incident_reporting.md": ["it_incident_reporting.md", "IT Incident Reporting", "IT-PRO-012"],
    "onboarding_guide.md": ["onboarding_guide.md", "Onboarding Guide", "HR-GUI-002"],
}


def load_test_cases():
    """Read tests/test_cases.csv into a list of dictionaries (one per question)."""
    with open(TEST_FILE, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


# --- 6.2 Simple automatic check --------------------------------------------
def normalize(text):
    """Lower-case the text and replace the curly apostrophe (’) with a normal one (')."""
    return text.lower().replace("’", "'")


def check_keywords(answer, must_contain):
    """True if the answer contains every required group of keywords.

    Format of must_contain:  "1 hour|one hour;3100"
      ";" separates groups that are ALL required
      "|" separates alternatives inside a group (ONE of them is enough)
    """
    answer = normalize(answer)
    for group in must_contain.split(";"):
        alternatives = group.split("|")
        if not any(normalize(word) in answer for word in alternatives):
            return False
    return True


def check_sources(answer, expected_source):
    """True if the answer cites every expected document (in any accepted form).

    Returns None when no source is expected (trap questions).
    """
    if not expected_source:
        return None
    answer = normalize(answer)
    for file_name in expected_source.split(";"):
        accepted_names = SOURCE_NAMES[file_name]
        if not any(normalize(name) in answer for name in accepted_names):
            return False
    return True


def grade_automatically(result):
    """Add the columns keywords_ok, source_ok and auto_pass to one result."""
    keywords_ok = check_keywords(result["answer"], result["must_contain"])
    source_ok = check_sources(result["answer"], result["expected_source"])

    result["keywords_ok"] = keywords_ok
    result["source_ok"] = "n/a" if source_ok is None else source_ok
    if result["category"] == "trap":
        # must_contain is "I don't know" -> the keyword check is the whole test
        result["auto_pass"] = keywords_ok
    else:
        result["auto_pass"] = keywords_ok and source_ok
    return result


# --- 6.3 LLM-as-judge ------------------------------------------------------
def build_judge_instruction(documents):
    """The judge gets its rules (prompts/judge.txt) + the same documents as the agent,
    so it can check the answer against the source data."""
    return build_system_instruction(load_prompt("judge"), documents)


def grade_with_judge(client, judge_instruction, result):
    """Ask the judge model for a verdict and add judge_verdict / judge_reason to the result."""
    expected_source = result["expected_source"] or "none (the answer is not in the documents)"
    message = (
        f"CATEGORY: {result['category']}\n"
        f"QUESTION: {result['question']}\n"
        f"EXPECTED ANSWER: {result['expected_answer']}\n"
        f"EXPECTED SOURCE: {expected_source}\n"
        f"ASSISTANT ANSWER:\n{result['answer']}"
    )
    try:
        # The Gemma servers often return temporary 500/503 errors,
        # so the judge gets more retries than the agent (waits: 5, 10, 20, 40, 80 s).
        raw_reply = ask_gemini(client, judge_instruction, message,
                               model=JUDGE_MODEL, json_output=True, max_attempts=6)
        reply = json.loads(raw_reply)          # text -> Python dictionary
        verdict = reply["verdict"].upper()
        reason = reply["reason"]
    except Exception as error:
        # The judge failed or did not return valid JSON: mark it, a human must check.
        verdict = "ERROR"
        reason = str(error)

    result["judge_verdict"] = verdict
    result["judge_reason"] = reason
    return result


# --- 6.1 Run the agent -----------------------------------------------------
def run_agent_on_tests(prompt_version, test_cases):
    """Ask the agent every test question and return the test cases + the answers."""
    documents = load_documents()
    system_instruction = build_system_instruction(load_prompt(prompt_version), documents)
    judge_instruction = build_judge_instruction(documents)
    client = genai.Client()  # reads GEMINI_API_KEY from the environment

    results = []
    for number, test in enumerate(test_cases, start=1):
        print(f"[{number}/{len(test_cases)}] {test['id']}: {test['question']}")
        try:
            answer = ask_gemini(client, system_instruction, test["question"])
        except Exception as error:
            # One failed question should not stop the whole evaluation.
            answer = f"ERROR: {error}"

        result = dict(test)  # copy all columns of the test case
        result["answer"] = answer
        result["said_dont_know"] = is_unanswered(answer)
        grade_automatically(result)
        time.sleep(PAUSE_SECONDS)

        grade_with_judge(client, judge_instruction, result)
        time.sleep(JUDGE_PAUSE_SECONDS)

        results.append(result)
    return results


# --- 6.4 Scores per category -----------------------------------------------
CATEGORIES = ["normal", "trap", "ambiguous"]


def percent(passed, total):
    """Format a score like '11/12 (92%)'."""
    if total == 0:
        return "-"
    return f"{passed}/{total} ({round(100 * passed / total)}%)"


def compute_scores(results):
    """Return one row per category (+ TOTAL) with the scores of both methods."""
    rows = []
    for category in CATEGORIES + ["TOTAL"]:
        if category == "TOTAL":
            items = results
        else:
            items = [r for r in results if r["category"] == category]

        auto_passed = sum(1 for r in items if r["auto_pass"] is True)

        # Judge errors (server did not answer) are NOT counted as failures:
        # we simply don't know the verdict, so they are reported separately.
        judged = [r for r in items if r["judge_verdict"] in ("PASS", "FAIL")]
        judge_passed = sum(1 for r in judged if r["judge_verdict"] == "PASS")
        judge_errors = len(items) - len(judged)

        judge_text = percent(judge_passed, len(judged))
        if judge_errors:
            judge_text += f", {judge_errors} error(s)"

        rows.append({
            "category": category,
            "questions": len(items),
            "automatic": percent(auto_passed, len(items)),
            "judge": judge_text,
        })
    return rows


def find_disagreements(results):
    """Questions where the automatic check and the judge give different verdicts."""
    return [
        r for r in results
        if r["judge_verdict"] in ("PASS", "FAIL")
        and (r["judge_verdict"] == "PASS") != r["auto_pass"]
    ]


def write_summary(prompt_version, scores, results):
    """Write results/summary_<version>.md: scores, disagreements and failed tests."""
    lines = [
        f"# Evaluation summary - prompt {prompt_version}",
        "",
        f"- Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- Agent model: `{MODEL}`",
        f"- Judge model: `{JUDGE_MODEL}`",
        "",
        "## Scores per category",
        "",
        "| Category | Questions | Automatic check | LLM judge |",
        "|---|---|---|---|",
    ]
    for row in scores:
        lines.append(f"| {row['category']} | {row['questions']} | {row['automatic']} | {row['judge']} |")

    lines += ["", "## Disagreements between the two methods", ""]
    disagreements = find_disagreements(results)
    if disagreements:
        lines += ["| ID | Automatic | Judge | Judge's reason |", "|---|---|---|---|"]
        for r in disagreements:
            auto = "PASS" if r["auto_pass"] else "FAIL"
            # new lines or "|" inside the text would break the Markdown table
            reason = r["judge_reason"].replace("\n", " ").replace("|", "/")
            lines.append(f"| {r['id']} | {auto} | {r['judge_verdict']} | {reason} |")
    else:
        lines.append("None.")

    lines += ["", "## Failed tests (failed by at least one method)", ""]
    failed = [r for r in results if not r["auto_pass"] or r["judge_verdict"] == "FAIL"]
    if failed:
        for r in failed:
            short_answer = r["answer"].replace("\n", " ")[:200]
            lines.append(f"- **{r['id']}** ({r['category']}) - *{r['question']}*")
            lines.append(f"  - Answer: {short_answer}")
            lines.append(f"  - Judge: {r['judge_verdict']} - {r['judge_reason']}")
    else:
        lines.append("None.")

    summary_file = RESULTS_FOLDER / f"summary_{prompt_version}.md"
    summary_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary_file


def load_saved_results(prompt_version):
    """Read results/run_<version>.csv back into a list of dictionaries."""
    with open(RESULTS_FOLDER / f"run_{prompt_version}.csv", newline="", encoding="utf-8") as file:
        results = list(csv.DictReader(file))
    for r in results:
        # CSV stores everything as text: turn "True"/"False" back into True/False
        r["auto_pass"] = r["auto_pass"] == "True"
    return results


def rejudge_errors(prompt_version):
    """Send to the judge again only the saved rows whose verdict is ERROR."""
    results = load_saved_results(prompt_version)
    client = genai.Client()
    judge_instruction = build_judge_instruction(load_documents())

    to_rejudge = [r for r in results if r["judge_verdict"] == "ERROR"]
    print(f"Re-judging {len(to_rejudge)} answer(s) with verdict ERROR\n")
    for r in to_rejudge:
        grade_with_judge(client, judge_instruction, r)
        print(f"{r['id']}: {r['judge_verdict']} - {r['judge_reason'][:100]}")
        time.sleep(JUDGE_PAUSE_SECONDS)
    return results


def save_results(results, prompt_version):
    """Write all results to results/run_<version>.csv and return the file path."""
    output_file = RESULTS_FOLDER / f"run_{prompt_version}.csv"
    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    return output_file


if __name__ == "__main__":
    # Arguments: the prompt version (e.g. v1) and the optional flag --rejudge
    arguments = [a for a in sys.argv[1:] if not a.startswith("--")]
    prompt_version = arguments[0] if arguments else "v1"

    if "--rejudge" in sys.argv:
        results = rejudge_errors(prompt_version)
    else:
        print(f"Evaluating prompt {prompt_version} with model {MODEL}\n")
        results = run_agent_on_tests(prompt_version, load_test_cases())

    output_file = save_results(results, prompt_version)

    scores = compute_scores(results)
    summary_file = write_summary(prompt_version, scores, results)

    print(f"\n{'Category':10} | {'Questions':9} | {'Automatic check':16} | LLM judge")
    for row in scores:
        print(f"{row['category']:10} | {row['questions']:9} | {row['automatic']:16} | {row['judge']}")

    print(f"\nDetails: {output_file.relative_to(PROJECT_ROOT)}")
    print(f"Summary: {summary_file.relative_to(PROJECT_ROOT)}")
