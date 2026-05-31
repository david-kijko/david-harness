# READ-ONLY ROOT-CAUSE DIAGNOSIS — single hypothesis lane

You are a FRESH Codex session (gpt-5.5 high) with NO memory of any prior chat. Everything you
need is in this brief. You are investigating ONE hypothesis for a known bug. **Do NOT edit, fix,
commit, or push anything.** This is a read-only investigation. Your job is to either CONFIRM or
REFUTE the hypothesis with traced `file:line` evidence, and propose a precise fix if confirmed.

## Repo
`{{REPO}}` (a clone at the deployed HEAD; the bug reproduces against the live deployment built from this code).

## The bug (issue statement)
{{ISSUE}}

## Reproduction / observed failure (from the characterize lane)
{{REPRO}}

## YOUR hypothesis to pressure-test
{{HYPOTHESIS}}

## How to investigate
1. Trace the exact code path implicated by THIS hypothesis end-to-end. Open every file you cite and
   quote the literal lines (with `path:line`). Follow the data: which component/endpoint/function
   produces the user-visible failure, and why.
2. Where it helps, probe the LIVE running system to ground a claim (read-only only):
   - Backend container logs / endpoints (e.g. `sudo docker logs <container> --tail 200`,
     or curl the API **through the frontend origin**, never assert without output).
   - Grep the served bundle / source for the implicated symbol.
   Paste literal command output for anything load-bearing. Do not infer state you did not observe.
3. Apply **5-Whys** down to the true root cause — do not stop at the first surface symptom.

## EXA IS MANDATORY WHEN UNSURE
If your confidence in the root cause OR in the proposed fix is **below 0.6**, you MUST run the exa
CLI before concluding, in diagnosis mode (5-Whys → root cause → verify → fix → prevention), and cite
the sources:

```
python3 ~/.claude/skills/exa/scripts/exa_cli.py run --query "<your rewritten query>" --format compact-markdown
```

Set `exa_used=true` if you consulted it. Be honest — a low-confidence honest answer is worth far
more than a confident guess.

## Deliverable (return EXACTLY this structured object)
- `key`: the hypothesis slug you were given.
- `confirmed`: true only if the traced evidence shows THIS hypothesis is the actual cause.
- `confidence`: 0..1, calibrated honestly. Do NOT round up.
- `evidence`: array of `file:line` citations + literal observed facts (log lines, response bodies).
- `proposed_fix`: precise change that would resolve it (file:line + what to change), or "" if refuted.
- `exa_used`: true/false per the mandate above.

Forbidden: claiming "confirmed" without a `file:line` the synthesizer can re-open. If you could not
prove it, say so and set confirmed=false with low confidence.
