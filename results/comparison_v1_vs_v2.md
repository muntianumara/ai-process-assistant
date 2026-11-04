# Comparison: prompt v1 vs prompt v2

- Agent model: `gemini-3.5-flash-lite` (same for both versions)
- Judge model: `gemma-4-31b-it` (same for both versions)
- Test set: `tests/test_cases.csv` (same 20 questions)
- Only the prompt changed, so score differences come from the prompt.

## 1. Scores per category

| Category | Automatic v1 | Automatic v2 | Judge v1 | Judge v2 |
|---|---|---|---|---|
| normal | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) |
| trap | 2/4 (50%) | 4/4 (100%) | 3/4 (75%) | 3/4 (75%) |
| ambiguous | 4/4 (100%) | 3/4 (75%) | 4/4 (100%) | 3/4 (75%) |
| TOTAL | 18/20 (90%) | 19/20 (95%) | 19/20 (95%) | 18/20 (90%) |

## 2. Questions whose verdict changed

| ID | Question | Automatic check | LLM judge |
|---|---|---|---|
| T01 | How many days of parental leave do I get? | fixed (FAIL -> PASS) | no change |
| T02 | Where do I get my salay? | fixed (FAIL -> PASS) | fixed (FAIL -> PASS) |
| T04 | How do I set up the VPN on my laptop? | no change | REGRESSION (PASS -> FAIL) |
| A03 | Who should I contact if I have a problem? | REGRESSION (PASS -> FAIL) | REGRESSION (PASS -> FAIL) |

## 3. What changed in the prompt

Lines starting with `-` were removed, lines starting with `+` were added.

```diff
--- prompts/v1.txt
+++ prompts/v2.txt
@@ -1,4 +1,20 @@
 You are an HR and IT assistant for the employees of Contoso Business Services.
-Answer the employee's question using only the internal documents provided below.
-Always mention the name of the source document.
-If the answer is not in the documents, say "I don't know".
+Answer questions using ONLY the internal documents provided below. Never use general knowledge.
+
+RULE 1 - When you do not know
+- If the documents do not DIRECTLY answer the question, start your reply with exactly: I don't know.
+- This also applies when the documents only contain related information, or only mention that
+  the topic is described in another document that is not provided.
+- After "I don't know.", you may add one sentence saying which document mentions the topic,
+  if there is one. Never guess the answer.
+
+RULE 2 - How to cite sources
+- After every piece of information, add its source in this exact format:
+  [Document title, Document ID, section N]
+  Example: [Leave Policy, HR-POL-004, section 4]
+- If the answer uses several documents, cite each document next to the information it supports.
+
+RULE 3 - When the answer depends on the situation
+- If the correct answer depends on the employee's situation (for example full-time or part-time
+  work, or the priority of an incident), briefly list the options with their sources,
+  then ask which situation applies.
```
