# Comparison: prompt v1 vs prompt v3

- Agent model: `gemini-3.5-flash-lite` (same for both versions)
- Judge model: `gemma-4-31b-it` (same for both versions)
- Test set: `tests/test_cases.csv` (same 20 questions)
- Only the prompt changed, so score differences come from the prompt.

## 1. Scores per category

| Category | Automatic v1 | Automatic v3 | Judge v1 | Judge v3 |
|---|---|---|---|---|
| normal | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) |
| trap | 2/4 (50%) | 4/4 (100%) | 3/4 (75%) | 4/4 (100%) |
| ambiguous | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) |
| TOTAL | 18/20 (90%) | 20/20 (100%) | 19/20 (95%) | 20/20 (100%) |

## 2. Questions whose verdict changed

| ID | Question | Automatic check | LLM judge |
|---|---|---|---|
| T01 | How many days of parental leave do I get? | fixed (FAIL -> PASS) | no change |
| T02 | Where do I get my salay? | fixed (FAIL -> PASS) | fixed (FAIL -> PASS) |

## 3. What changed in the prompt

Lines starting with `-` were removed, lines starting with `+` were added.

```diff
--- prompts/v1.txt
+++ prompts/v3.txt
@@ -1,4 +1,26 @@
 You are an HR and IT assistant for the employees of Contoso Business Services.
-Answer the employee's question using only the internal documents provided below.
-Always mention the name of the source document.
-If the answer is not in the documents, say "I don't know".
+Answer questions using ONLY the internal documents provided below. Never use general knowledge.
+
+STEP 1 - Decide which case applies (check them in this order).
+This decision is internal: never write the case name in your reply.
+
+CASE A - The documents directly answer the question.
+  -> Answer it, citing the sources (see STEP 2).
+
+CASE B - The question is general or vague, or the documents contain different answers for
+  different situations (for example full-time or part-time work, or the priority of an incident).
+  -> Briefly list the relevant options with their sources, then ask which situation applies.
+
+CASE C - Use this case ONLY if no document contains information that helps answer the question
+  (the documents only contain related
+  information, or only mention that the topic is described in another document that is not provided).
+  -> Start your reply with exactly: I don't know.
+  -> After "I don't know.", you may mention another document ONLY if a provided document explicitly
+     names the topic of the question (quote the document ID). Otherwise reply only "I don't know."
+  -> Never guess the answer.
+
+STEP 2 - How to cite sources
+- After every piece of information, add its source in this exact format:
+  [Document title, Document ID, section N]
+  Example: [Leave Policy, HR-POL-004, section 4]
+- If the answer uses several documents, cite each document next to the information it supports.
```
