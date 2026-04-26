# Declaude Context Sync

Sync Claude-style context files, skills, and MCP config into agent-friendly
layouts for Codex, Gemini, and other tools.

## Supports

Declaude Context Sync currently focuses on repository-owned context that can be
safely projected with symlinks or generated config files.

- Project instructions: mirrors the project-level `CLAUDE.md` into root
  `AGENTS.md` and `.agents/AGENTS.md`
- Nested instructions: mirrors nested `*/CLAUDE.md` files into sibling
  `*/AGENTS.md` files
- Skills: links `.claude/skills/*` directories into `.agents/skills/*`
- MCP config: projects `.mcp.json` into generated Gemini and Codex MCP configs
- Gemini context names: defaults Gemini context loading to `AGENTS.md` and
  `GEMINI.md`

## Limitations

- Claude auto memory is not synced.
- Claude hooks are not converted.
- User-level and managed Claude configuration is not read.
- `@path` imports inside `CLAUDE.md` are not expanded.
- `.claude/rules/`, `.claude/commands/`, `.claude/agents/`, output styles,
  plugins, permissions, and general `.claude/settings*.json` settings are not
  projected today.

Those omissions are intentional. Claude stores some context outside the
repository, such as user settings, managed policy, and machine-local auto memory.
Hooks can run shell commands or agent checks, so translating them across tools
would require security and behavior decisions this project should not make
silently. Declaude Context Sync keeps the first version narrow: expose
repository-authored instructions, skills, and MCP config without pretending every
Claude Code feature has an equivalent in every agent CLI.

Relevant Claude Code docs:

- [Memory](https://code.claude.com/docs/en/memory)
- [Hooks](https://code.claude.com/docs/en/hooks)
- [Settings](https://code.claude.com/docs/en/settings)
- [Skills and commands](https://code.claude.com/docs/en/slash-commands)
- [Subagents](https://code.claude.com/docs/en/sub-agents)

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
