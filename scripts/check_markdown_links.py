"""Validate local links in tracked Markdown at one immutable Git revision."""

from __future__ import annotations

import argparse
import functools
import posixpath
import re
import subprocess
import unicodedata
import urllib.parse
from pathlib import PurePosixPath


def _git_output(*arguments: str) -> str:
    return subprocess.check_output(["git", *arguments]).decode("utf-8")


def _commit(revision: str) -> str:
    return _git_output(
        "rev-parse",
        "--verify",
        "--end-of-options",
        f"{revision}^{{commit}}",
    ).strip()


def _slug(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[`*_~]", "", text).strip().lower()
    text = unicodedata.normalize("NFC", text)
    text = "".join(
        character for character in text if character.isalnum() or character in " -_"
    )
    return re.sub(r"\s+", "-", text)


def check_revision(revision: str) -> tuple[int, int, int, tuple[str, ...]]:
    """Return file/link/fragment counts and errors for one commit."""
    commit = _commit(revision)
    all_paths = tuple(
        line
        for line in _git_output("ls-tree", "-r", "--name-only", commit).splitlines()
        if line
    )
    tracked_paths = frozenset(all_paths)
    tracked_directories = frozenset(
        parent.as_posix()
        for name in all_paths
        for parent in PurePosixPath(name).parents
        if parent.as_posix() != "."
    )
    markdown_files = tuple(
        PurePosixPath(name) for name in all_paths if name.lower().endswith(".md")
    )

    @functools.lru_cache(maxsize=None)
    def blob_text(path: PurePosixPath) -> str:
        return _git_output("show", f"{commit}:{path.as_posix()}")

    def source_without_fences(path: PurePosixPath):
        fence: str | None = None
        for line_number, line in enumerate(blob_text(path).splitlines(), 1):
            match = re.match(r"^\s*(`{3,}|~{3,})", line)
            if match:
                token = match.group(1)[0]
                if fence is None:
                    fence = token
                elif token == fence:
                    fence = None
                continue
            if fence is None:
                yield line_number, line

    @functools.lru_cache(maxsize=None)
    def anchors(path: PurePosixPath) -> frozenset[str]:
        result: set[str] = set()
        seen: dict[str, int] = {}
        for _, line in source_without_fences(path):
            result.update(
                re.findall(
                    r"""<a\s+(?:[^>]*?\s)?id=["']([^"']+)["'][^>]*>""",
                    line,
                    re.IGNORECASE,
                )
            )
            heading = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
            if heading is None:
                continue
            base = _slug(heading.group(2))
            occurrence = seen.get(base, 0)
            result.add(base if occurrence == 0 else f"{base}-{occurrence}")
            seen[base] = occurrence + 1
        return frozenset(result)

    link_pattern = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
    local_links = 0
    fragment_links = 0
    errors: list[str] = []
    for source in markdown_files:
        for line_number, line in source_without_fences(source):
            for raw_target in link_pattern.findall(line):
                target = raw_target.strip()
                if target.startswith("<") and ">" in target:
                    target = target[1 : target.index(">")]
                else:
                    target = target.split(maxsplit=1)[0]
                if not target or re.match(
                    r"^(?:https?|mailto|tel):", target, re.IGNORECASE
                ):
                    continue
                local_links += 1
                path_part, _, fragment = urllib.parse.unquote(target).partition("#")
                if fragment:
                    fragment_links += 1
                if path_part:
                    destination_text = posixpath.normpath(
                        (source.parent / path_part).as_posix()
                    )
                    if destination_text == ".." or destination_text.startswith("../"):
                        errors.append(
                            f"{source}:{line_number}: target escapes repository: {target}"
                        )
                        continue
                    destination = PurePosixPath(destination_text)
                else:
                    destination = source
                destination_name = destination.as_posix()
                if (
                    destination_name not in tracked_paths
                    and destination_name not in tracked_directories
                ):
                    errors.append(f"{source}:{line_number}: missing target: {target}")
                    continue
                if (
                    fragment
                    and destination_name in tracked_paths
                    and destination.suffix.lower() == ".md"
                ):
                    target_anchors = anchors(destination)
                    if (
                        fragment not in target_anchors
                        and _slug(fragment) not in target_anchors
                    ):
                        errors.append(
                            f"{source}:{line_number}: missing heading fragment: {target}"
                        )
    return len(markdown_files), local_links, fragment_links, tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision", default="HEAD")
    args = parser.parse_args()
    files, links, fragments, errors = check_revision(args.revision)
    print(f"tracked_markdown_files={files}")
    print(f"local_links={links}")
    print(f"fragments={fragments}")
    print(f"errors={len(errors)}")
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
