"""
agent.py - AI Process Assistant

Answers HR/IT questions using ONLY the internal documents in the docs/ folder.

Built step by step:
  3.1 Load the documents from disk
  3.2 Send question + documents to Gemini
  3.3 Detect "I don't know" and log the question in results/unanswered.csv

Run:
    python src/agent.py "How many days of annual leave do I have?"
"""

import csv
import sys
import time
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import errors, types

# --- Settings --------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_FOLDER = PROJECT_ROOT / "docs"
PROMPTS_FOLDER = PROJECT_ROOT / "prompts"
UNANSWERED_FILE = PROJECT_ROOT / "results" / "unanswered.csv"

# The phrase the prompt asks the model to use when it cannot answer.
NO_ANSWER_PHRASE = "i don't know"

MODEL = "gemini-3.5-flash-lite"   # pinned version, so test runs stay comparable
PROMPT_VERSION = "v3"             # which file from prompts/ to use (v3 = best evaluated version)


# --- 3.1 Load the documents ------------------------------------------------
def load_documents():
    """Read every .md file from docs/ and return a dictionary {file name: text}."""
    documents = {}
    # sorted() -> always the same order, so every run sends the model the same input
    for file_path in sorted(DOCS_FOLDER.glob("*.md")):
        # encoding="utf-8" avoids problems with special characters on Windows
        documents[file_path.name] = file_path.read_text(encoding="utf-8")
    return documents


# --- 3.2 Build the system instruction and call Gemini ----------------------
def load_prompt(version):
    """Read the rules of the agent from prompts/<version>.txt (e.g. prompts/v1.txt)."""
    return (PROMPTS_FOLDER / f"{version}.txt").read_text(encoding="utf-8")


def build_system_instruction(prompt_text, documents):
    """Put the rules first, then every document wrapped in <document> tags.

    The tags show the model clearly where each document starts and ends
    and what its file name is, so it can cite the correct source.
    """
    parts = [prompt_text, "", "DOCUMENTS:"]
    for name, text in documents.items():
        parts.append(f'<document name="{name}">\n{text}\n</document>')
    return "\n".join(parts)


def ask_gemini(client, system_instruction, question, model=MODEL, json_output=False,
               max_attempts=4):
    """Send one question to Gemini and return the text of the answer.

    model       - which Gemini model to use (the judge in evaluate.py uses another one)
    json_output - True asks Gemini to reply with JSON only (used by the judge)

    Free-tier servers are sometimes busy (error 503) or we send too many
    requests (error 429). In those cases we wait and try again, doubling the
    waiting time each attempt (5s, 10s, 20s) - this is called "exponential backoff".
    """
    wait_seconds = 5
    for attempt in range(1, max_attempts + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=question,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0,  # least random answers -> more reproducible tests
                    response_mime_type="application/json" if json_output else None,
                ),
            )
            return response.text.strip()
        except errors.APIError as error:
            temporary_problem = error.code in (429, 500, 503)
            if not temporary_problem or attempt == max_attempts:
                raise  # a real error (e.g. wrong key) -> stop and show it
            print(f"  [attempt {attempt}] error {error.code}, retrying in {wait_seconds}s...")
            time.sleep(wait_seconds)
            wait_seconds *= 2


# --- 3.3 Detect "I don't know" and log the question ------------------------
def is_unanswered(answer):
    """Return True if the answer contains the "I don't know" phrase.

    Simple V1 check: it only works if the model uses exactly this phrase.
    """
    # lower() -> ignore upper/lower case; replace() -> the model sometimes
    # writes a "curly" apostrophe (’) instead of the normal one (')
    normalized = answer.lower().replace("’", "'")
    return NO_ANSWER_PHRASE in normalized


def log_unanswered(question):
    """Append the question as a new row in results/unanswered.csv.

    This simulates a Power Automate flow that adds a new item
    to a Microsoft List, where HR/IT can follow it up.
    """
    file_is_new = not UNANSWERED_FILE.exists()
    # "a" = append: add at the end of the file, never overwrite old rows
    with open(UNANSWERED_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if file_is_new:
            writer.writerow(["timestamp", "question", "prompt_version", "status"])
        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            question,
            PROMPT_VERSION,
            "New",
        ])


# This block runs only when we start the file directly (python src/agent.py),
# not when another file imports it (evaluate.py will import it later).
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python src/agent.py "your question"')
        sys.exit(1)
    question = sys.argv[1]

    documents = load_documents()
    system_instruction = build_system_instruction(load_prompt(PROMPT_VERSION), documents)

    # genai.Client() automatically reads the GEMINI_API_KEY environment variable
    client = genai.Client()

    print(f"Question: {question}\n")
    answer = ask_gemini(client, system_instruction, question)
    print(answer)

    if is_unanswered(answer):
        log_unanswered(question)
        print(f"\n[Unanswered -> question saved in {UNANSWERED_FILE.relative_to(PROJECT_ROOT)}]")
