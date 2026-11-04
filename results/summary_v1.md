# Evaluation summary - prompt v1

- Date: 2026-11-04 13:40
- Agent model: `gemini-3.5-flash-lite`
- Judge model: `gemma-4-31b-it`

## Scores per category

| Category | Questions | Automatic check | LLM judge |
|---|---|---|---|
| normal | 12 | 12/12 (100%) | 12/12 (100%) |
| trap | 4 | 2/4 (50%) | 1/2 (50%), 2 error(s) |
| ambiguous | 4 | 4/4 (100%) | 2/2 (100%), 2 error(s) |
| TOTAL | 20 | 18/20 (90%) | 15/16 (94%), 4 error(s) |

## Disagreements between the two methods

| ID | Automatic | Judge | Judge's reason |
|---|---|---|---|
| T01 | FAIL | PASS | The assistant correctly identifies that the information is not in the provided documents and refers to the separate policy mentioned in the Leave Policy, without inventing any facts. |

## Failed tests (failed by at least one method)

- **T01** (trap) - *How many days of parental leave do I get?*
  - Answer: According to the **Leave Policy**, maternity leave and parental leave are regulated by national law and described in a separate document called the *Parental Leave Policy (HR-POL-007)*.
  - Judge: PASS - The assistant correctly identifies that the information is not in the provided documents and refers to the separate policy mentioned in the Leave Policy, without inventing any facts.
- **T02** (trap) - *Where do I get my salay?*
  - Answer: Based on the **Onboarding Guide for New Employees**, you need to upload your bank account details in the HR Portal at least 3 working days before your first day.
  - Judge: FAIL - The assistant provided related information about uploading bank account details instead of stating that the documents do not contain information on where salary is received, which is required for 'trap' questions.
