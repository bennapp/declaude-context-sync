# Declaude Context Sync

This directory holds small Python utilities that translate Claude-oriented
context into compatible layouts for other agent CLIs.

## Purpose

The current goal is to treat Claude context as the source of truth, then expose
that same context to other tools without copying file contents.

Today that means:

- discover project and nested `CLAUDE.md` files
- create matching `AGENTS.md` symlinks for Codex-compatible context loading,
  including both root `AGENTS.md` and `.agents/AGENTS.md`
- discover `.claude/skills/*` directories that contain `SKILL.md`
- create matching `.agents/skills/*` symlinks
- generate Gemini settings that include `context.fileName` entries for
  `AGENTS.md` and preserve `GEMINI.md` by default

The public invocation model is repository-root explicit: pass `--repo-root` for
the repository whose context should be projected. This lets the tool live as a
sibling checkout, a vendored directory, or an installed script without assuming a
specific repository layout.

This should stay discovery-driven. Avoid hardcoding per-repo paths beyond the
configured roots and filename conventions.

## Design Constraints

- Prefer symlinks over duplicated files so Claude, Codex, and Gemini-style
  context stays in sync automatically.
- Keep the tool repo-agnostic and config-driven.
- Refuse to overwrite real files or incorrect symlinks.
- Root context discovery should prefer the first configured source candidate.
- Root context projection may target more than one path when the config asks for
  it.
- `.agents/AGENTS.md` should point directly at the Claude source file, not
  indirectly through root `AGENTS.md`.
- Nested discovery should mirror sibling files consistently, for example
  `backend/CLAUDE.md -> backend/AGENTS.md`.

## Expected Direction

If support expands beyond Codex-style targets, extend config and discovery rules
instead of adding one-off scripts for each CLI. The source context should remain
Claude-authored files and skill directories where possible.
