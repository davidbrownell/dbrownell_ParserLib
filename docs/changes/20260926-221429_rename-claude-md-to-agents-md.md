---
type: Change
title: Renamed CLAUDE.md to AGENTS.md
description: Replaced the Claude-specific agent instruction file with the agent-agnostic AGENTS.md and updated it to python_development template version 0.8.0.
resource: /AGENTS.md
tags:
  - config
  - agents
generated: { by: claude-code/claude-opus-5-5, at: 2026-09-26T22:14:29Z }
status: stable
---

# Summary
- Removed `CLAUDE.md` and added `AGENTS.md` with equivalent content.
- Updated the version marker from `0.6.0` to `python_development Version: 0.8.0`.
- Clarified "SOLID" as "SOLID design principles".
- Added a `General` section under Python Development: run `python`-related tasks using `uv`.

# Rationale
`AGENTS.md` is the cross-tool convention for coding-agent instructions, allowing any agent (not only Claude Code) to discover the repository's conventions.

# Notes
Claude Code loads `CLAUDE.md` by default, not `AGENTS.md`. A `CLAUDE.md` containing `@AGENTS.md` restores automatic loading in Claude Code if needed.
