# Assets And Studio

Asset creation should start from a notebook alias or notebook ID that already contains the right sources.

## Create Surface

Current live `create` subcommands on Hetzner:

- `notebook`
- `audio`
- `video`
- `report`
- `infographic`
- `slides`
- `quiz`
- `flashcards`
- `data-table`
- `mindmap`

## Verified Creation Syntax

```bash
NLM=/home/david/.local/bin/nlm

$NLM create report <notebook> --format "Briefing Doc" --confirm
$NLM create report <notebook> --format "Create Your Own" --prompt "Summarize risks" --confirm

$NLM create audio <notebook> --format deep_dive --length short --focus "Auth flow" --confirm

$NLM create slides <notebook> --format detailed_deck --length short --focus "Architecture" --confirm

$NLM create infographic <notebook> --orientation landscape --detail detailed --focus "Platform overview" --confirm
```

Useful flags verified on Hetzner:

- report: `--format`, `--prompt`, `--language`, `--source-ids`, `--confirm`
- audio: `--format`, `--length`, `--language`, `--focus`, `--source-ids`, `--confirm`
- slides: `--format`, `--length`, `--language`, `--focus`, `--source-ids`, `--confirm`
- infographic: `--orientation`, `--detail`, `--language`, `--focus`, `--source-ids`, `--confirm`

For the rest of the asset families, inspect exact flags first:

```bash
NLM=/home/david/.local/bin/nlm
$NLM create video --help
$NLM create quiz --help
$NLM create flashcards --help
$NLM create data-table --help
$NLM create mindmap --help
```

## Studio Management

```bash
NLM=/home/david/.local/bin/nlm
$NLM studio status <notebook>
$NLM studio rename <artifact-id> "New Artifact Title"
$NLM studio delete <artifact-id> --confirm
```

Use `studio status` after generation work. Do not assume an artifact finished just because creation returned successfully.

## Downloads

Current live `download` subcommands on Hetzner:

- `audio`
- `video`
- `slide-deck`
- `infographic`
- `report`
- `mind-map`
- `data-table`
- `quiz`
- `flashcards`

Inspect format-specific flags before download:

```bash
NLM=/home/david/.local/bin/nlm
$NLM download report --help
$NLM download slide-deck --help
$NLM download infographic --help
```

## Export

Use export when the final output belongs in Google Docs or Sheets instead of local files:

```bash
NLM=/home/david/.local/bin/nlm
$NLM export artifact <artifact-id>
$NLM export to-docs <report-artifact-id>
$NLM export to-sheets <data-table-artifact-id>
```
