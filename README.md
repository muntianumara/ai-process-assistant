# AI Process Assistant

> Work in progress. This README will be completed in step 8.

An AI agent that answers HR/IT questions **only** from internal documentation,
cites the source document, and says "I don't know" instead of inventing answers.

## Project structure

```
ai-process-assistant/
├── docs/            # Fictional internal documents (the agent's only source of truth)
├── prompts/         # Versioned system prompts (v1.txt, v2.txt, ...)
├── src/             # Agent and evaluation code
├── tests/           # Test cases (questions + expected answers)
├── results/         # Evaluation outputs (run_v1.csv, comparison.md, ...)
├── LEARNING_LOG.md  # What was done at each step and why
├── requirements.txt # Python dependencies
└── .gitignore       # Keeps secrets (.env) and cache files out of git
```

## LLM provider and API key

The agent uses **Google Gemini** (free tier from Google AI Studio) through the
official `google-genai` Python SDK.

The code reads the key from the `GEMINI_API_KEY` environment variable.
It is never stored in code or committed to git.

To verify your setup: `python src/check_setup.py`
