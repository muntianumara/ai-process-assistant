# AI Process Assistant

An HR/IT assistant that answers employee questions **only** from internal documentation,
cites the source document and section, and says **"I don't know"** instead of inventing an answer.
Unanswered questions are logged so the documentation can be improved.

The focus of the project is not only the agent, but **how to test it**: a fixed test set,
two evaluation methods (keyword check + LLM-as-judge), and prompt versions improved step by step
based on measured errors.

---

## 1. Problem

Employees ask HR and IT the same questions again and again (leave days, incident priorities,
onboarding steps). A chatbot could answer them, but a generic AI model:
- **invents plausible answers** when it does not know (hallucination);
- does not say **where** the answer comes from, so it cannot be verified;
- gives no signal about **what is missing** from the documentation.

## 2. Solution

- The agent receives the internal documents together with every question and must answer
  **only from them** (grounding). The model itself is not trained or changed.
- Every statement is followed by its source: `[Leave Policy, HR-POL-004, section 4]`.
- If the documents do not answer the question, the agent replies "I don't know" and the question
  is saved in `results/unanswered.csv` (simulating a Power Automate flow, see section 8).
- The system prompt is stored in versioned files (`prompts/v1.txt`, `v2.txt`, `v3.txt`)
  and every version is evaluated on the same 20 test questions.

## 3. Architecture

```
                      prompts/vN.txt (rules)
                              │
docs/*.md ──► load_documents ─┴─► system instruction ──┐
(3 fictional                                           ▼
 internal docs)        user question ──────────► Gemini 3.5 Flash-Lite
                                                       │
                                                       ▼
                                              answer + sources
                                                       │
                                     contains "I don't know"?
                                         │ yes             │ no
                                         ▼                 ▼
                          results/unanswered.csv     shown to the user
                          (timestamp, question,
                           prompt_version, status=New)

Evaluation (src/evaluate.py):
tests/test_cases.csv ──► agent ──► keyword + source check ──┐
   (20 questions)            └──► LLM judge (Gemma 4 31B) ──┴──► results/run_vN.csv
                                                                  results/summary_vN.md
src/compare.py: results of two versions ──► results/comparison_vX_vs_vY.md
```

| File | Purpose |
|---|---|
| `docs/` | 3 fictional internal documents (leave policy, IT incident reporting, onboarding guide) |
| `prompts/v1.txt` … `v3.txt` | Versions of the agent's system prompt |
| `prompts/judge.txt` | Grading rubric for the LLM judge |
| `src/agent.py` | The agent: loads documents, calls Gemini (with retry), logs unanswered questions |
| `src/evaluate.py` | Runs all test questions, grades them with both methods, writes scores |
| `src/compare.py` | Compares two evaluation runs |
| `src/check_setup.py` | Verifies API key, SDK and available models |
| `tests/test_cases.csv` | 20 test questions with expected answers and sources |
| `results/` | Evaluation results, comparisons, unanswered questions |
| `LEARNING_LOG.md` | Decisions, alternatives and lessons for every step (in Romanian) |

## 4. How to run

Requirements: Python 3.10+ and a free Google Gemini API key from
[Google AI Studio](https://aistudio.google.com).

```powershell
# 1. Store the API key as an environment variable (never in code)
setx GEMINI_API_KEY "your-key"        # then restart the terminal

# 2. Create a virtual environment and install the SDK
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Check the setup
python src/check_setup.py

# 4. Ask the agent a question
python src/agent.py "How many days of annual leave does a full-time employee get?"

# 5. Evaluate a prompt version (~40 min on the free tier because of rate limits)
python src/evaluate.py v3
python src/evaluate.py v3 --rejudge   # re-grade only rows where the judge had a server error

# 6. Compare two versions
python src/compare.py v2 v3
```

## 5. Test methodology

**Test set** (`tests/test_cases.csv`): 20 questions, each with an expected answer written
**from the source documents** (not from the agent's output) and reviewed manually.

| Category | Count | What it tests | Correct behaviour |
|---|---|---|---|
| normal | 12 | Finds the right fact in any of the 3 documents | Correct fact + correct source |
| trap | 4 | The answer is NOT in the documents (parental leave, salary, remote work, VPN) | "I don't know", nothing invented |
| ambiguous | 4 | The answer depends on the situation | Lists the options or asks a clarifying question |

The documents were designed together with the tests: concrete facts (24 days, extension 3100,
31 March) for normal questions, **intentional gaps** (policies that are referenced but not provided)
for trap questions, and context-dependent rules for ambiguous questions.
Two trap questions are **regression tests** for errors first found by manual exploratory testing.

**Two evaluation methods:**

| | Keyword + source check | LLM-as-judge |
|---|---|---|
| How | Required keywords (`24`, `31 March`) and the cited document (file name, title or ID) | A second model gets a rubric, the documents, the expected answer and the agent's answer, and returns PASS/FAIL + reason |
| Strengths | Fast, free, fully reproducible | Understands meaning, checks claims against the documents |
| Weaknesses | Blind to meaning: missed a wrongly attributed source and an invented reference | Can be inconsistent, costs extra calls, can be unavailable |

The judge uses a **different model family** (Gemma) than the agent (Gemini) to reduce
self-preference bias. Where the two methods disagree, a human decides.

**Fair comparison:** between versions only the prompt changes. Model, documents, test set,
judge and rubric stay the same, and `temperature=0` is used.

## 6. Results

| Category | v1 auto | v2 auto | v3 auto | v1 judge | v2 judge | v3 judge |
|---|---|---|---|---|---|---|
| normal (12) | 100% | 100% | 100% | 100% | 100% | 100% |
| trap (4) | **50%** | 100% | 100% | 75% | 75% | 100% |
| ambiguous (4) | 100% | **75%** | 100% | 100% | **75%** | 100% |
| **total (20)** | 90% | 95% | **100%** | 95% | 90% | **100%** |

**v1 → v2.** V1 answered every factual question correctly but failed half of the trap questions:
for "How many days of parental leave?" it only pointed to another policy without saying "I don't know"
(so the question was never logged), and for "Where do I get my salary?" it presented a *related* fact
(upload your bank details) as if it were the answer. V2 added explicit rules for when to say
"I don't know", a fixed citation format and a rule for situation-dependent questions.
Both trap errors were fixed, **but two regressions appeared**: the agent invented that VPN setup is
mentioned in the IT procedure (caught only by the LLM judge), and it refused a vague but answerable
question ("Who should I contact if I have a problem?").

**v2 → v3.** The rules were rewritten as an ordered decision (A: answer directly, B: list options for
vague or situation-dependent questions, C: "I don't know"), and the agent may only point to another
document if a provided document explicitly names the topic.
Both regressions were fixed and nothing else broke: V3 passed all 20 questions with both evaluation
methods. A first V3 draft did not fix the vague question; a quick 3-question smoke test caught this
before the 40-minute full run, and the case definitions were clarified.

**Important caveat:** V2 and V3 were improved by looking at errors on these same 20 questions, so
100% measures how well the prompt fixes the known cases, not how well it generalises. A fair final
check needs a **held-out set** of new questions that were never used while writing the prompt
(see Next steps).

Details: [`results/comparison_v1_vs_v2.md`](results/comparison_v1_vs_v2.md),
[`results/comparison_v2_vs_v3.md`](results/comparison_v2_vs_v3.md),
[`results/comparison_v1_vs_v3.md`](results/comparison_v1_vs_v3.md),
and `results/summary_vN.md` for each version.

**Key lessons**
- A prompt change can fix one error and create another. Only re-running the **whole** test set
  (regression testing) revealed this.
- The total score hides the most important information: v1 scored 90% overall while failing 50% of
  the trap questions.
- The keyword check and the LLM judge complement each other: the judge caught two errors the keywords
  missed (a wrongly attributed source, an invented reference).
- Examples from the test set were deliberately **not** copied into the prompt, to avoid overfitting.

## 7. Limitations

- **Small test set:** 20 questions; one question changes the score by 5%, so small differences can be noise.
- **The prompt was tuned on the test set:** v2 and v3 were written after reading v1/v2 errors on the same
  20 questions, so the 100% score of v3 is optimistic (risk of overfitting to the test set).
- **Non-determinism:** even with `temperature=0`, the same question sometimes got a different answer
  between runs. A more robust evaluation would run each version several times.
- **LLM judge:** not fully consistent (the same answer received PASS once and FAIL once) and its
  rubric is itself a prompt that needs validation.
- **"I don't know" detection** is a simple text match; it relies on the prompt producing the exact phrase.
- **All documents are sent with every question.** This works for 3 documents (~2,500 tokens),
  not for hundreds.
- **Free tier:** rate limits (the first judge model allowed only 20 requests/day), frequent temporary
  server errors, and data sent on the free tier may be used by the provider - acceptable only because
  the documents are fictional.
- **Fictional, clean documents:** real documentation has outdated versions and contradictions.

## 8. Mapping to Microsoft 365 (SharePoint, Power Automate, Copilot Studio)

| This project | Microsoft 365 equivalent |
|---|---|
| `docs/` folder | SharePoint document library (metadata: ID, version, owner) |
| `prompts/vN.txt` + `agent.py` | Copilot Studio agent: SharePoint as knowledge source, prompt as agent instructions |
| "I don't know" branch | Fallback / "no answer found" path of the agent |
| `log_unanswered()` → `unanswered.csv` | Power Automate flow: *Create item* in a Microsoft List "Unanswered questions" (Status: New / In progress / Answered) + Teams notification to HR |
| `tests/test_cases.csv` + `evaluate.py` | Test set run against each new version of the agent's instructions before publishing |

**Closed loop:** an unanswered question becomes a list item for HR → HR updates the document in
SharePoint → the agent can answer next time. The monthly share of unanswered questions is a simple
KPI for documentation quality. Switching from CSV to Microsoft Lists only requires changing the body
of `log_unanswered()`; the rest of the agent stays the same.

## 9. Next steps

- **Held-out test set:** 20+ new questions never used while improving the prompt, to measure generalisation.
- **Retrieval (RAG)** for larger document sets: search the relevant sections instead of sending all documents.
- **Run each evaluation several times** and report averages to reduce the effect of non-determinism.
- **Validate the judge** on a larger human-labelled sample and refine its rubric for borderline trap cases.
- **Structured output** (e.g. JSON with `answer`, `sources`, `answered: true/false`) instead of matching the text "I don't know".
- **Real integration:** Copilot Studio agent on a SharePoint library, Power Automate flow to Microsoft Lists, Teams channel.
- **Production setup:** a paid tier or an enterprise service with a data-protection agreement.
