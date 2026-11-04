# Comparison: prompt v2 vs prompt v3

- Agent model: `gemini-3.5-flash-lite` (same for both versions)
- Judge model: `gemma-4-31b-it` (same for both versions)
- Test set: `tests/test_cases.csv` (same 20 questions)
- Only the prompt changed, so score differences come from the prompt.

## 1. Scores per category

| Category | Automatic v2 | Automatic v3 | Judge v2 | Judge v3 |
|---|---|---|---|---|
| normal | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) |
| trap | 4/4 (100%) | 4/4 (100%) | 3/4 (75%) | 4/4 (100%) |
| ambiguous | 3/4 (75%) | 4/4 (100%) | 3/4 (75%) | 4/4 (100%) |
| TOTAL | 19/20 (95%) | 20/20 (100%) | 18/20 (90%) | 20/20 (100%) |

## 2. Questions whose verdict changed

| ID | Question | Automatic check | LLM judge |
|---|---|---|---|
| T04 | How do I set up the VPN on my laptop? | no change | fixed (FAIL -> PASS) |
| A03 | Who should I contact if I have a problem? | fixed (FAIL -> PASS) | fixed (FAIL -> PASS) |

## 3. What changed in the prompt

Lines starting with `-` were removed, lines starting with `+` were added.

```diff
--- prompts/v2.txt
+++ prompts/v3.txt
@@ -1,20 +1,26 @@
 You are an HR and IT assistant for the employees of Contoso Business Services.
 Answer questions using ONLY the internal documents provided below. Never use general knowledge.
 
-RULE 1 - When you do not know
-- If the documents do not DIRECTLY answer the question, start your reply with exactly: I don't know.
-- This also applies when the documents only contain related information, or only mention that
-  the topic is described in another document that is not provided.
-- After "I don't know.", you may add one sentence saying which document mentions the topic,
-  if there is one. Never guess the answer.
+STEP 1 - Decide which case applies (check them in this order).
+This decision is internal: never write the case name in your reply.
 
-RULE 2 - How to cite sources
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
 - After every piece of information, add its source in this exact format:
   [Document title, Document ID, section N]
   Example: [Leave Policy, HR-POL-004, section 4]
 - If the answer uses several documents, cite each document next to the information it supports.
-
-RULE 3 - When the answer depends on the situation
-- If the correct answer depends on the employee's situation (for example full-time or part-time
-  work, or the priority of an incident), briefly list the options with their sources,
-  then ask which situation applies.
```
