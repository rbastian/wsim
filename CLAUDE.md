# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Issue Tracking

This project uses **beads** (`bd` command) for issue tracking:

- Issue prefix: `wsim-` (e.g., `wsim-w5u`)
- All commands support `--json` flag for structured output
- Always run `bd sync` after making issue changes to commit and push
- Include issue ID in commit messages: `git commit -m "Fix bug (wsim-abc)"`

### Common Commands

```bash
# Find actionable work
bd ready

# Create issues (always include description)
bd create "Title" -p 1 --description "Details"

# Work on tasks
bd show <id>                              # View details
bd update <id> --status in_progress       # Claim task
bd update <id> --notes "Progress notes"   # Add notes
bd close <id> --reason "Completed"        # Close task

# Dependencies
bd dep add <child-id> <parent-id>         # Create blocking dependency

# Sync with git
bd sync                                   # Export, commit, push
```

## Git Workflow

**NEVER push directly to main branch.** All changes must go through pull requests.

1. Create feature branch: `git checkout -b feature/wsim-<id>-<description>`
2. Make changes and commit
3. Push branch: `git push -u origin feature/wsim-<id>-<description>`
4. Open PR: `gh pr create --title "Title (wsim-<id>)" --body "..."`
5. Wait for user to merge

## Development Setup

Project is in early setup phase. Check beads issues (`bd ready`) for current work items.
