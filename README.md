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

For most Claude Code repositories, no config changes are needed. The bundled
defaults cover the common `CLAUDE.md` to `AGENTS.md`, `.claude/skills` to
`.agents/skills`, and `.mcp.json` projection workflow.

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

## Config

Config is optional for normal use. Pass `--config path/to/config.json` only when
you need to override the bundled defaults.

`config.json` describes what repository-owned context should be discovered and
where Declaude Context Sync should project it.

The config has three sections:

- `discovery`: filename-based context discovery for `sync_context.py`
- `directory_links`: directory symlink rules for `sync_context.py`
- `gemini`: Gemini-specific generated settings for `sync_mcp.py`

Default config:

```json
{
  "discovery": {
    "source_filename": "CLAUDE.md",
    "target_filename": "AGENTS.md",
    "root_target_filenames": [
      "AGENTS.md",
      ".agents/AGENTS.md"
    ],
    "root_source_candidates": [
      "CLAUDE.md",
      ".claude/CLAUDE.md"
    ],
    "skip_dirs": [
      ".git",
      "node_modules"
    ]
  },
  "directory_links": [
    {
      "source_root": ".claude/skills",
      "target_root": ".agents/skills",
      "marker_file": "SKILL.md"
    }
  ],
  "gemini": {
    "context_file_names": [
      "AGENTS.md",
      "GEMINI.md"
    ]
  }
}
```

Field guide:

- `discovery.source_filename`: filename to search for under `--repo-root`
- `discovery.target_filename`: sibling filename to create next to nested source
  files
- `discovery.root_target_filenames`: target files to create from the first root
  source candidate that exists
- `discovery.root_source_candidates`: ordered root-level source candidates
- `discovery.skip_dirs`: directory names ignored during recursive discovery
- `directory_links[].source_root`: source directory to scan under `--repo-root`
- `directory_links[].target_root`: target directory where matching children are
  linked
- `directory_links[].marker_file`: file required inside a child directory before
  it is linked
- `gemini.context_file_names`: values written to generated Gemini
  `context.fileName`

`config.json` does not define MCP servers. `sync_mcp.py` reads MCP servers from
the target repository's `.mcp.json`, then projects them into `.gemini` and
`.codex` config files.
