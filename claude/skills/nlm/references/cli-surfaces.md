# CLI Surfaces

Use `NLM=/home/david/.local/bin/nlm` on Hetzner when `nlm` is not on `PATH`.

## Core Checks

```bash
NLM=/home/david/.local/bin/nlm
$NLM login --check
$NLM doctor
$NLM --help
```

## Top-Level Command Surface

Current live groups on Hetzner:

- `login`, `notebook`, `note`, `source`, `chat`, `studio`, `research`, `alias`
- `config`, `download`, `share`, `export`, `skill`, `setup`, `doctor`
- `batch`, `cross`, `pipeline`, `tag`
- `audio`, `report`, `quiz`, `flashcards`, `mindmap`, `slides`, `infographic`, `video`, `data-table`
- umbrella verbs: `create`, `list`, `get`, `delete`, `add`, `rename`, `status`, `describe`, `query`, `sync`, `content`, `stale`, `configure`, `set`, `show`, `install`, `uninstall`, `update`

## Notebook Lifecycle

```bash
NLM=/home/david/.local/bin/nlm
$NLM notebook list
$NLM notebook create "Project Notebook"
$NLM notebook get <id-or-alias>
$NLM notebook describe <id-or-alias>
$NLM notebook rename <id-or-alias> "New Title"
$NLM notebook delete <id-or-alias> --confirm
```

## Querying

```bash
NLM=/home/david/.local/bin/nlm
$NLM notebook query <id-or-alias> "What does this notebook cover?"
$NLM notebook query <id-or-alias> "What changed in auth?" --source-ids <id1,id2>
$NLM notebook query <id-or-alias> "Continue from above" --conversation-id <id>
$NLM batch query "Compare these notebooks" --notebooks <id1,id2>
$NLM cross query "What overlaps or conflicts?" --notebooks <id1,id2>
```

## Sources

`nlm source add` live syntax on Hetzner:

```bash
NLM=/home/david/.local/bin/nlm
$NLM source list <notebook-id>
$NLM source add <notebook-id> --url https://example.com --wait
$NLM source add <notebook-id> --text "inline content" --title "Notes" --wait
$NLM source add <notebook-id> --drive <drive-file-id> --type slides --wait
$NLM source add <notebook-id> --youtube https://youtu.be/... --wait
$NLM source add <notebook-id> --file ./document.pdf --wait
$NLM source get <source-id>
$NLM source describe <source-id>
$NLM source content <source-id>
$NLM source rename <source-id> "Canonical Title"
$NLM source delete <source-id> --confirm
```

## Aliases

```bash
NLM=/home/david/.local/bin/nlm
$NLM alias list
$NLM alias set project-wiki <notebook-id>
$NLM alias get project-wiki
$NLM alias delete project-wiki
```

Use aliases whenever repeated notebook access matters more than one-off scripting.

## Sharing and Export

```bash
NLM=/home/david/.local/bin/nlm
$NLM share status <notebook-id>
$NLM share public <notebook-id>
$NLM share private <notebook-id>
$NLM share invite <notebook-id> collaborator@example.com
$NLM share batch <notebook-id> collaborators.csv

$NLM export artifact <artifact-id>
$NLM export to-docs <artifact-id>
$NLM export to-sheets <artifact-id>
```

## Pipelines and Setup

```bash
NLM=/home/david/.local/bin/nlm
$NLM pipeline list
$NLM pipeline run <pipeline-name> <notebook-id>
$NLM pipeline create ./pipeline.yaml

$NLM skill list
$NLM skill update
$NLM setup --help
```

Use `--help` on any subgroup before using a less common verb:

```bash
$NLM <group> --help
$NLM <group> <command> --help
```
