# Declaude Context Sync

Sync Claude-style context files, skills, and MCP config into agent-friendly
layouts for Codex, Gemini, and other tools.

## Current scope

The first supported operation is discovery-based symlinking. The tool finds a
source context format, then exposes a compatible target filename for another
tool.

Today the default config mirrors:

- the project-level `CLAUDE.md` into root `AGENTS.md`
- the project-level `CLAUDE.md` into `.agents/AGENTS.md`
- nested `*/CLAUDE.md` files into sibling `*/AGENTS.md` files
- `.claude/skills/*` directories into `.agents/skills/*`
- `.mcp.json` into generated Gemini and Codex MCP configs; Gemini context
  filenames default to `AGENTS.md` and `GEMINI.md`

## Usage

From this repository, pass the repository root you want to convert:

```bash
python3 sync_context.py --repo-root /path/to/repo
```

If this repository is checked out as a sibling of the target repo:

```bash
python3 sync_context.py --repo-root ../target-repo
```

Dry run:

```bash
python3 sync_context.py --repo-root /path/to/repo --dry-run
```

MCP config projection:

```bash
python3 sync_mcp.py --repo-root /path/to/repo --dry-run
```

By default, the scripts read `config.json` next to the script. You can pass
`--config path/to/config.json` to override discovery and generator settings.

## Discovery model

The default config uses these rules:

- project root source candidate order: `CLAUDE.md`, then `.claude/CLAUDE.md`
- project root targets: `AGENTS.md` and `.agents/AGENTS.md`
- nested source filename: `CLAUDE.md`
- target filename: `AGENTS.md`
- skipped directories: `.git`, `node_modules`

That means a repository with:

```text
.claude/CLAUDE.md
backend/CLAUDE.md
frontend/CLAUDE.md
```

will produce:

```text
AGENTS.md -> .claude/CLAUDE.md
.agents/AGENTS.md -> ../.claude/CLAUDE.md
backend/AGENTS.md -> CLAUDE.md
frontend/AGENTS.md -> CLAUDE.md
```

And skill directories like:

```text
.claude/skills/code-review/SKILL.md
.claude/skills/qa/SKILL.md
```

will produce:

```text
.agents/skills/code-review -> ../../.claude/skills/code-review
.agents/skills/qa -> ../../.claude/skills/qa
```

`--dry-run` is the safest way to inspect the inferred mapping set before writing
symlinks.
