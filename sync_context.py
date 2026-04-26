#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover source context files and create compatible symlinks."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to the repository whose context files should be projected.",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to the JSON config file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned actions without changing the filesystem.",
    )
    return parser.parse_args()


def load_config(config_path: Path) -> dict:
    try:
        return json.loads(config_path.read_text())
    except FileNotFoundError as exc:
        raise SystemExit(f"Config not found: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {config_path}: {exc}") from exc


def default_config_path() -> Path:
    return Path(__file__).resolve().parent / "config.json"


def resolve_config_path(config_arg: str | None) -> Path:
    if config_arg:
        return Path(config_arg).expanduser().resolve()
    return default_config_path()


def resolve_repo_root(repo_root_arg: str) -> Path:
    repo_root = Path(repo_root_arg).expanduser().resolve()
    if not repo_root.exists():
        raise SystemExit(f"Repo root does not exist: {repo_root}")
    if not repo_root.is_dir():
        raise SystemExit(f"Repo root is not a directory: {repo_root}")
    return repo_root


def ensure_under_root(path: Path, repo_root: Path, field_name: str) -> None:
    try:
        path.resolve(strict=False).relative_to(repo_root)
    except ValueError as exc:
        raise SystemExit(f"{field_name} escapes repo root: {path}") from exc


def ensure_parent(path: Path, dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)


def load_discovery_config(config: dict) -> dict:
    discovery = config.get("discovery", {})
    if not isinstance(discovery, dict):
        raise SystemExit("Config field 'discovery' must be an object")
    return discovery


def normalize_string_list(value: object, field_name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SystemExit(f"Config field '{field_name}' must be a list of strings")
    return value


def should_skip_path(path: Path, skipped_dirs: set[str]) -> bool:
    return any(part in skipped_dirs for part in path.parts)


def discover_file_links(repo_root: Path, discovery: dict) -> list[tuple[str, str]]:
    source_filename = discovery.get("source_filename", "CLAUDE.md")
    target_filename = discovery.get("target_filename", "AGENTS.md")
    root_target_filenames = discovery.get("root_target_filenames", [target_filename])
    root_source_candidates = discovery.get(
        "root_source_candidates",
        ["CLAUDE.md", ".claude/CLAUDE.md"],
    )
    skip_dirs = set(
        normalize_string_list(
            discovery.get("skip_dirs", [".git", "node_modules"]),
            "discovery.skip_dirs",
        )
    )

    if not isinstance(source_filename, str) or not source_filename:
        raise SystemExit("Config field 'discovery.source_filename' must be a string")
    if not isinstance(target_filename, str) or not target_filename:
        raise SystemExit("Config field 'discovery.target_filename' must be a string")

    root_candidates = normalize_string_list(
        root_source_candidates, "discovery.root_source_candidates"
    )
    root_targets = normalize_string_list(
        root_target_filenames, "discovery.root_target_filenames"
    )

    links: list[tuple[str, str]] = []
    consumed_sources: set[Path] = set()

    for candidate in root_candidates:
        source = repo_root / candidate
        if source.exists():
            for root_target in root_targets:
                links.append((candidate, root_target))
            consumed_sources.add(source.resolve())
            break

    for source in repo_root.rglob(source_filename):
        if should_skip_path(source.relative_to(repo_root), skip_dirs):
            continue
        if source.resolve() in consumed_sources:
            continue

        relative_source = source.relative_to(repo_root)
        target = relative_source.parent / target_filename
        links.append((str(relative_source), str(target)))

    links.sort(key=lambda item: item[1])
    return links


def discover_directory_links(repo_root: Path, config: dict) -> list[tuple[str, str]]:
    skill_links = config.get("directory_links", [])
    if not isinstance(skill_links, list):
        raise SystemExit("Config field 'directory_links' must be a list")

    links: list[tuple[str, str]] = []

    for entry in skill_links:
        if not isinstance(entry, dict):
            raise SystemExit("Each 'directory_links' entry must be an object")

        source_root = entry.get("source_root")
        target_root = entry.get("target_root")
        marker_file = entry.get("marker_file", "SKILL.md")

        if not isinstance(source_root, str) or not source_root:
            raise SystemExit("Each directory link entry needs string 'source_root'")
        if not isinstance(target_root, str) or not target_root:
            raise SystemExit("Each directory link entry needs string 'target_root'")
        if not isinstance(marker_file, str) or not marker_file:
            raise SystemExit("Each directory link entry needs string 'marker_file'")

        source_root_path = repo_root / source_root
        if not source_root_path.exists():
            continue

        for child in sorted(source_root_path.iterdir()):
            if not child.is_dir():
                continue
            if not (child / marker_file).exists():
                continue

            relative_source = child.relative_to(repo_root)
            relative_target = Path(target_root) / child.name
            links.append((str(relative_source), str(relative_target)))

    return links


def discover_links(repo_root: Path, config: dict) -> list[tuple[str, str]]:
    discovery = load_discovery_config(config)
    links = discover_file_links(repo_root, discovery)
    links.extend(discover_directory_links(repo_root, config))
    links.sort(key=lambda item: item[1])
    return links


def sync_link(repo_root: Path, source_str: str, target_str: str, dry_run: bool) -> None:
    source = repo_root / source_str
    target = repo_root / target_str
    ensure_under_root(source, repo_root, "Source path")
    ensure_under_root(target, repo_root, "Target path")

    if not source.exists():
        raise SystemExit(f"Source does not exist: {source}")

    ensure_parent(target, dry_run)

    relative_source = Path(os.path.relpath(source, start=target.parent))
    action_prefix = "DRY RUN:" if dry_run else "LINK:"

    if target.is_symlink():
        current = Path(os.readlink(target))
        if current == relative_source:
            print(f"{action_prefix} {target} already points to {relative_source}")
            return
        if dry_run:
            print(
                f"{action_prefix} would refuse existing symlink at {target}: "
                f"points to {current}, expected {relative_source}"
            )
            return
        raise SystemExit(
            f"Refusing to replace existing symlink at {target}: points to {current}"
        )

    if target.exists():
        if dry_run:
            print(f"{action_prefix} would refuse existing file at {target}")
            return
        raise SystemExit(f"Refusing to replace existing file at {target}")

    print(f"{action_prefix} {target} -> {relative_source}")
    if not dry_run:
        target.symlink_to(relative_source)


def main() -> int:
    args = parse_args()
    config_path = resolve_config_path(args.config)
    repo_root = resolve_repo_root(args.repo_root)
    config = load_config(config_path)
    links = discover_links(repo_root, config)

    for source, target in links:
        sync_link(repo_root, source, target, args.dry_run)

    return 0


if __name__ == "__main__":
    sys.exit(main())
