# Conductor - Context-Driven Development for Claude Code

**Measure twice, code once.**

Conductor is a Claude Code skill that transforms Claude into a proactive project manager following a strict protocol to **specify, plan, and implement** software features and bug fixes.

## Installation

This skill is automatically available as a global skill in Claude Code. No additional installation required.

## Commands

Claude exposes these as hyphenated slash commands.

| Command | Description |
|---------|-------------|
| `/conductor-setup` | Initialize project with Conductor methodology (run once per project) |
| `/conductor-superconductor [spec-path]` | Launch the deterministic requirements-to-implementation pipeline |
| `/conductor-newTrack [description]` | Create a new feature or bug fix track |
| `/conductor-implement [track]` | Execute tasks from the current track's plan |
| `/conductor-status` | Display project progress overview |
| `/conductor-revert [target]` | Git-aware revert of tracks, phases, or tasks |

## Philosophy

Control your code. By treating **context as a managed artifact** alongside your code, you transform your repository into a single source of truth that drives every agent interaction with deep, persistent project awareness.

**Lifecycle:** Context -> Spec & Plan -> Implement

## Features

- **Plan before you build**: Create specs and plans that guide implementation
- **Maintain context**: Ensure AI follows style guides, tech stack choices, and product goals
- **Iterate safely**: Review plans before code is written
- **Work as a team**: Project-level context becomes shared foundation
- **Smart revert**: Git-aware revert that understands logical units of work

## Getting Started

1. Navigate to your project directory
2. Run `/conductor-setup`
3. Follow the interactive prompts to define your product, tech stack, and workflow
4. Create your first track with `/conductor-newTrack`
5. Implement with `/conductor-implement`

## Directory Structure

After setup, your project will have:

```
conductor/
├── product.md              # Product vision and goals
├── product-guidelines.md   # Brand and style guidelines
├── tech-stack.md           # Technology choices
├── workflow.md             # Development workflow (TDD, etc.)
├── code_styleguides/       # Language-specific style guides
├── tracks.md               # Master list of all tracks
└── tracks/
    └── <track_id>/
        ├── metadata.json
        ├── spec.md
        └── plan.md
```

## Workflow Integration

Conductor integrates with Claude Code's capabilities:

- **TodoWrite**: Tracks progress through tasks
- **AskUserQuestion**: Interactive prompts with options
- **Task agents**: Codebase exploration and planning
- **Git integration**: Commits, notes, and reverts

## License

Apache-2.0 (adapted from [gemini-cli-extensions/conductor](https://github.com/gemini-cli-extensions/conductor))
