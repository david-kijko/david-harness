You are starting a brand-new project in an empty directory. There is no existing code, no framework choice, no test harness, no team conventions.

THE SPEC (verbatim from the user):
"Build me a CLI tool that reads CSV from stdin and writes JSON Lines to stdout. Each row becomes one JSON object using the header row as keys. Quoted fields with embedded commas should be parsed correctly. The tool should be invokable as `csv2jsonl < input.csv > output.jsonl`. Python is fine."

CONTEXT: You don't know yet if this is part of a larger pipeline, will be called once or millions of times, will run on a laptop or in a container, or will need to handle huge files (it's a one-off question to you, no follow-up). The user pressed Enter and is waiting.

PRODUCE: a written plan that you would hand to an implementer (or yourself) before writing any code. List every file you would create, every dependency you would add, every test you would write, and every command a fresh clone would type to verify the tool works. Do not actually create files; just produce the plan.

(Be especially explicit about: what you considered and rejected; whether you'd add any dependency at all; how a user would run the tests in a fresh clone.)
