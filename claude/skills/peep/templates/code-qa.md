# Template: Code Question Answering

**Use when**: explaining how code works, answering "what does X do", architectural questions, code review without a specific change to verify, understanding behavior of unfamiliar code.

**Failure modes this template guards against** (full catalog in `references/failure-modes.md`):
- Guessing function behavior from naming conventions
- Confident-but-wrong elaborations (long reasoning chain that misses one step)
- Hand-waving past an edge case the question actually depends on

This template requires a function trace table and an alternative-hypothesis check. For inference-rule tagging on each property claim, see `references/claim-types.md`.

---

## Fill the certificate. Read every function you cite.

```
SEMI-FORMAL CODE ANALYSIS CERTIFICATE

QUESTION: [the question being answered, verbatim if possible]

FUNCTION TRACE TABLE
| Function/Method | File:Line | Param Types | Return Type | Verified Behavior | Key Detail |
|---|---|---|---|---|---|
| [name] | [path:N] | [...] | [...] | [what it ACTUALLY does — READ the source] | [edge case, caller, or mutation that matters] |
| [name] | [path:N] | [...] | [...] | [verified behavior] | [...] |

(Every row must come from reading the source. Mark third-party rows with
ASSUMPTION: ... if you cannot read them.)

DATA FLOW ANALYSIS
Variable: [key variable name]
- Created at: [file:line] as [value/type]
- Modified at: [file:line, or NEVER MODIFIED]
- Used at: [file:line(s)] where [final use]
- Key constraint: [what must be true for correct behavior]

(Repeat for each variable that materially affects the answer.)

SEMANTIC PROPERTIES (with evidence)
SP1: [Property claim, e.g. "the map is pre-populated with all valid keys"]
     — Evidence: [file:line shows X]
SP2: [...] — Evidence: [...]
SP3: [...] — Evidence: [...]

(Tag each property by inference type per `references/claim-types.md` —
empirical-from-trace, by-construction, by-invariant, by-contract.)

ALTERNATIVE HYPOTHESIS CHECK  (REQUIRED — protects against confident-wrong)
If the opposite answer were true, what evidence would exist?
  - Searched for: [what you looked for — be specific: grep pattern, file paths]
  - Found: [what you found — file:line]
  - Conclusion: [REFUTED / SUPPORTED]

GROUNDED ANSWER
[Answer the question. Every sentence must reference a specific row in
the trace table or a SPn property above. No claims that aren't traced.]
```

## Common slip: long reasoning chain that misses one step

The paper's `py_5` example: agent traced five function calls correctly but missed that downstream code already handled the edge case it identified, leading to a confident-but-wrong answer. The Alternative Hypothesis Check forces you to spend evidence on the opposite conclusion before committing.

## Common slip: guessing API differences from naming

Asked whether `m_sliceTypeStrMap.at(key)` differs from `m_sliceTypeStrMap[key]`, standard reasoning often invents non-existent edge cases ("if an invalid key is somehow passed..."). The trace table forces you to find where keys are actually generated, which often proves the speculative case impossible (cpp_3 in the paper).

## Tone

Skip prose recap. Open straight to `SEMI-FORMAL CODE ANALYSIS CERTIFICATE` and fill it.
