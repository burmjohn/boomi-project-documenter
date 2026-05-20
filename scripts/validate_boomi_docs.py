#!/usr/bin/env python3
"""Validate generated Boomi Markdown and standalone HTML documentation."""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class HtmlFacts(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.hrefs: list[str] = []
        self.tags: list[str] = []
        self.external_refs: list[str] = []
        self.has_style = False
        self.has_print_css = False
        self.current_tag: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag)
        self.current_tag = tag
        attrs_dict = dict(attrs)
        if "id" in attrs_dict and attrs_dict["id"]:
            self.ids.add(attrs_dict["id"] or "")
        if tag == "a" and attrs_dict.get("href", "").startswith("#"):
            self.hrefs.append(attrs_dict["href"] or "")
        if tag == "style":
            self.has_style = True
        for attr in ("href", "src"):
            value = attrs_dict.get(attr)
            if value and re.match(r"^(https?:)?//", value):
                self.external_refs.append(value)
        if tag == "link" and attrs_dict.get("rel") in {"stylesheet", "preload", "preconnect"}:
            self.external_refs.append(attrs_dict.get("href") or "<link>")

    def handle_data(self, data: str) -> None:
        if self.current_tag == "style" and "@media print" in data:
            self.has_print_css = True

    def handle_endtag(self, tag: str) -> None:
        if self.current_tag == tag:
            self.current_tag = None


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate_markdown(path: Path, text: str, errors: list[str]) -> None:
    if not re.search(r"^# .+", text, re.MULTILINE):
        fail(errors, f"{path}: missing level-1 title")
    required_patterns = {
        "scope/evidence": r"(?i)\b(scope|evidence basis|evidence used)\b",
        "baseline": r"(?i)\b(baseline|component version|inventory)\b",
        "flow": r"(?i)\b(flow|process sequence|end-to-end|orchestration)\b",
        "risk/status": r"(?i)\b(risk|status|dependency|verification)\b",
        "next steps": r"(?i)\b(next steps|recommended next)\b",
    }
    for label, pattern in required_patterns.items():
        if not re.search(pattern, text):
            fail(errors, f"{path}: missing {label} section or wording")
    if len(re.findall(r"\|.+\|", text)) < 4:
        fail(errors, f"{path}: expected at least one Markdown table")
    if re.search(r"(?i)\b(today|yesterday|tomorrow|recently|latest)\b", text):
        fail(errors, f"{path}: relative time wording needs exact dates")


def validate_html(path: Path, text: str, errors: list[str]) -> None:
    facts = HtmlFacts()
    facts.feed(text)
    if "<!doctype html" not in text[:100].lower():
        fail(errors, f"{path}: missing HTML doctype")
    if not facts.has_style:
        fail(errors, f"{path}: missing embedded style block")
    if not facts.has_print_css:
        fail(errors, f"{path}: missing print CSS")
    if "nav" not in facts.tags:
        fail(errors, f"{path}: missing navigation")
    if "table" not in facts.tags:
        fail(errors, f"{path}: missing table")
    if "svg" not in facts.tags:
        fail(errors, f"{path}: missing inline SVG diagram")
    if "script" in facts.tags:
        fail(errors, f"{path}: standalone guide must not include scripts")
    for href in facts.hrefs:
        anchor = href[1:]
        if anchor and anchor not in facts.ids:
            fail(errors, f"{path}: navigation anchor {href} has no matching id")
    for ref in facts.external_refs:
        fail(errors, f"{path}: external reference is not allowed: {ref}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--markdown", action="append", default=[], help="Markdown file to validate")
    parser.add_argument("--html", action="append", default=[], help="Standalone HTML file to validate")
    args = parser.parse_args()

    errors: list[str] = []
    markdown_paths = [Path(item) for item in args.markdown]
    html_paths = [Path(item) for item in args.html]

    if not markdown_paths and not html_paths:
        fail(errors, "provide at least one --markdown or --html file")

    for path in markdown_paths:
        if not path.exists():
            fail(errors, f"{path}: file does not exist")
            continue
        validate_markdown(path, read_text(path), errors)

    for path in html_paths:
        if not path.exists():
            fail(errors, f"{path}: file does not exist")
            continue
        validate_html(path, read_text(path), errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Boomi documentation validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
