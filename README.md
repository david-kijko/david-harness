# peep archive

Orphan branch storing peep contracts and checkit verification runs.

Layout:
```
peep-<sha8>/
  spec.txt                  verbatim user SPEC the peepID hashes
  contract.md               filled SEMI-FORMAL certificate
  mental-model.brief.md     author's architecture brief (the agent's own words)
  mental-model.png          rendered architecture diagram
  checkit/
    run-1/
      actual-architecture.brief.md
      actual-architecture.png
      gap-report.md
      verdict.md            PERFECT|VERIFIED|ARCH_GAP|LOGIC_GAP|BEHAVIORAL_FAIL|FAILED
      corrective-prompt.md  only present when verdict in {LOGIC_GAP, BEHAVIORAL_FAIL, FAILED}
      proofshot/            optional browser automation artifacts
    run-2/ ...
```

peepID = first 8 hex chars of sha256(verbatim SPEC). Same SPEC -> same peepID
-> idempotent archive folder. Edits to the SPEC produce a new peepID.

Pushed automatically by the peep skill after each contract and by checkit
after each verification run.
