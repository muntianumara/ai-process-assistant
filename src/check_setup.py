"""
check_setup.py - Verifies that the environment is ready before we build the agent.

It checks, in order:
  1. The GEMINI_API_KEY environment variable exists.
  2. The google-genai package is installed.
  3. Which models this API key can use right now
     (model names change often, so we ask the API instead of guessing).
  4. One tiny test call to a model.

Run:
    python src/check_setup.py                    # tests the default model
    python src/check_setup.py gemini-3.5-flash   # tests a specific model
"""

import os
import sys

# A pinned (fixed) model version: results stay comparable between test runs.
# Aliases like "gemini-flash-latest" can silently switch to a newer model.
DEFAULT_TEST_MODEL = "gemini-3.5-flash-lite"


def main():
    # --- 1. Is the API key set? -------------------------------------------
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: the GEMINI_API_KEY environment variable is not set.")
        print("Set it with:  setx GEMINI_API_KEY \"your-key\"  then restart VS Code.")
        sys.exit(1)
    # We never print the key itself, only its length.
    print(f"[OK] GEMINI_API_KEY found ({len(api_key)} characters).")

    # --- 2. Is the SDK installed? -----------------------------------------
    try:
        from google import genai
    except ImportError:
        print("ERROR: the google-genai package is not installed.")
        print("Run:  pip install -r requirements.txt")
        sys.exit(1)
    print("[OK] google-genai package is installed.")

    client = genai.Client(api_key=api_key)

    # --- 3. Which models can we use? --------------------------------------
    print("\nModels that support text generation (generateContent):")
    for model in client.models.list():
        actions = model.supported_actions or []
        if "generateContent" in actions:
            print("   ", model.name)

    # --- 4. One small test call -------------------------------------------
    model_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TEST_MODEL
    print(f"\nTest call to model: {model_name}")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Reply with exactly: setup works",
        )
        print("[OK] Model replied:", response.text.strip())
    except Exception as error:
        print("ERROR during the test call:", error)
        print("Hints: 429 = rate limit reached (wait and retry);")
        print("       404 = model name not available (pick one from the list above);")
        print("       400/403 = key problem (check the key in Google AI Studio).")
        sys.exit(1)

    print("\nEverything is ready.")


if __name__ == "__main__":
    main()
