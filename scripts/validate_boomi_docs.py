#!/usr/bin/env python3
"""Validate generated Boomi Markdown, HTML, SVG, and visual evidence."""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

try:
    from .boomi_visual_contract import ContractError, load_manifest
except ImportError:  # Direct script execution.
    from boomi_visual_contract import ContractError, load_manifest


CSP_NO_IMAGES = (
    "default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; "
    "font-src 'none'; media-src 'none'; connect-src 'none'; frame-src 'none'; "
    "form-action 'none'; base-uri 'none'; object-src 'none'"
)
FORBIDDEN_TAGS = {"script", "form", "iframe", "frame", "embed", "object"}
VISUAL_SVG_TAGS = {
    "circle",
    "ellipse",
    "line",
    "path",
    "polygon",
    "polyline",
    "rect",
    "text",
}
URL_ATTRIBUTES = {
    "action",
    "data",
    "formaction",
    "href",
    "poster",
    "src",
    "srcset",
    "xlink:href",
}
PLACEHOLDER_PATTERN = re.compile(
    r"(?:\[[A-Z][^\]\n]{0,80}\]|\{\{[^{}\n]+\}\}|<[A-Z][A-Z0-9_-]*>)"
)


@dataclass
class TableFacts:
    captions: int = 0
    header_scopes: list[str | None] = field(default_factory=list)


@dataclass
class SvgFacts:
    attrs: dict[str, str | None]
    inside_scroll: bool
    visual_elements: int = 0
    title_ids: list[str] = field(default_factory=list)
    desc_ids: list[str] = field(default_factory=list)


class HtmlFacts(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.fragment_hrefs: list[str] = []
        self.aria_references: list[tuple[str, str]] = []
        self.tags: list[str] = []
        self.style_text: list[str] = []
        self.csp_values: list[str] = []
        self.forbidden_tags: list[str] = []
        self.event_handlers: list[str] = []
        self.unsafe_urls: list[tuple[str, str, str]] = []
        self.tables: list[TableFacts] = []
        self.svgs: list[SvgFacts] = []
        self._tag_stack: list[tuple[str, set[str]]] = []
        self._table_stack: list[TableFacts] = []
        self._svg_stack: list[SvgFacts] = []
        self._style_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_dict = {name.lower(): value for name, value in attrs}
        classes = set((attrs_dict.get("class") or "").split())
        self._tag_stack.append((tag, classes))
        self.tags.append(tag)

        element_id = attrs_dict.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicate_ids.add(element_id)
            self.ids.add(element_id)

        for name, value in attrs_dict.items():
            if name.startswith("on"):
                self.event_handlers.append(name)
            if name in {"aria-labelledby", "aria-describedby"} and value:
                for reference in value.split():
                    self.aria_references.append((name, reference))
            if name in URL_ATTRIBUTES and value:
                if tag == "a" and name == "href" and value.startswith("#"):
                    self.fragment_hrefs.append(value)
                elif tag in {"use", "lineargradient", "radialgradient"} and value.startswith(
                    "#"
                ):
                    pass
                else:
                    self.unsafe_urls.append((tag, name, value))

        if tag in FORBIDDEN_TAGS:
            self.forbidden_tags.append(tag)
        if tag == "meta" and (attrs_dict.get("http-equiv") or "").lower() == (
            "content-security-policy"
        ):
            self.csp_values.append(attrs_dict.get("content") or "")
        if tag == "meta" and (attrs_dict.get("http-equiv") or "").lower() == "refresh":
            self.forbidden_tags.append("meta refresh")
        if tag == "style":
            self._style_depth += 1
        if tag == "table":
            table = TableFacts()
            self.tables.append(table)
            self._table_stack.append(table)
        elif tag == "caption" and self._table_stack:
            self._table_stack[-1].captions += 1
        elif tag == "th" and self._table_stack:
            self._table_stack[-1].header_scopes.append(attrs_dict.get("scope"))

        if tag == "svg":
            inside_scroll = any(
                "diagram-scroll" in ancestor_classes
                for _, ancestor_classes in self._tag_stack[:-1]
            )
            svg = SvgFacts(attrs=attrs_dict, inside_scroll=inside_scroll)
            self.svgs.append(svg)
            self._svg_stack.append(svg)
        elif self._svg_stack and tag in VISUAL_SVG_TAGS:
            self._svg_stack[-1].visual_elements += 1
        elif self._svg_stack and tag == "title":
            if element_id:
                self._svg_stack[-1].title_ids.append(element_id)
        elif self._svg_stack and tag == "desc":
            if element_id:
                self._svg_stack[-1].desc_ids.append(element_id)

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        if self._style_depth:
            self.style_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "style" and self._style_depth:
            self._style_depth -= 1
        if tag == "table" and self._table_stack:
            self._table_stack.pop()
        if tag == "svg" and self._svg_stack:
            self._svg_stack.pop()
        for index in range(len(self._tag_stack) - 1, -1, -1):
            if self._tag_stack[index][0] == tag:
                del self._tag_stack[index:]
                break


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate_markdown(
    path: Path, text: str, errors: list[str], *, strict: bool = False
) -> None:
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
    if strict and PLACEHOLDER_PATTERN.search(text):
        fail(errors, f"{path}: unresolved template placeholder")


def validate_html_legacy(path: Path, text: str, errors: list[str]) -> None:
    facts = HtmlFacts()
    facts.feed(text)
    styles = "".join(facts.style_text)
    if "<!doctype html" not in text[:100].lower():
        fail(errors, f"{path}: missing HTML doctype")
    if "style" not in facts.tags:
        fail(errors, f"{path}: missing embedded style block")
    if "@media print" not in styles:
        fail(errors, f"{path}: missing print CSS")
    if "nav" not in facts.tags:
        fail(errors, f"{path}: missing navigation")
    if not facts.tables:
        fail(errors, f"{path}: missing table")
    if not facts.svgs:
        fail(errors, f"{path}: missing inline SVG diagram")
    if "script" in facts.tags:
        fail(errors, f"{path}: standalone guide must not include scripts")
    for href in facts.fragment_hrefs:
        anchor = href[1:]
        if anchor and anchor not in facts.ids:
            fail(errors, f"{path}: navigation anchor {href} has no matching id")
    for _, _, value in facts.unsafe_urls:
        if re.match(r"^(https?:)?//", value):
            fail(errors, f"{path}: external reference is not allowed: {value}")


def _validate_svg_facts(path: Path, svg: SvgFacts, errors: list[str]) -> None:
    if not svg.attrs.get("viewbox"):
        fail(errors, f"{path}: SVG requires viewBox")
    if svg.attrs.get("role") != "img":
        fail(errors, f"{path}: SVG requires role=\"img\"")
    labelled = (svg.attrs.get("aria-labelledby") or "").split()
    if len(labelled) != 2:
        fail(errors, f"{path}: SVG aria-labelledby must reference title and description")
    else:
        if labelled[0] not in svg.title_ids:
            fail(errors, f"{path}: SVG title reference is broken")
        if labelled[1] not in svg.desc_ids:
            fail(errors, f"{path}: SVG description reference is broken")
    if svg.visual_elements == 0:
        fail(errors, f"{path}: SVG must contain visual elements")
    if not svg.inside_scroll:
        fail(errors, f"{path}: SVG must be inside .diagram-scroll")


def validate_html_strict(
    path: Path,
    text: str,
    errors: list[str],
    *,
    allow_placeholders: bool,
) -> None:
    facts = HtmlFacts()
    try:
        facts.feed(text)
        facts.close()
    except Exception as exc:
        fail(errors, f"{path}: cannot parse HTML: {exc}")
        return
    styles = "".join(facts.style_text)
    styles_lower = styles.lower()

    if "<!doctype html" not in text[:100].lower():
        fail(errors, f"{path}: missing HTML doctype")
    if "style" not in facts.tags:
        fail(errors, f"{path}: missing embedded style block")
    if "@media print" not in styles_lower:
        fail(errors, f"{path}: missing print CSS")
    if ":focus-visible" not in styles_lower and ":focus" not in styles_lower:
        fail(errors, f"{path}: missing visible keyboard focus CSS")
    if "nav" not in facts.tags:
        fail(errors, f"{path}: missing navigation")
    if not facts.tables:
        fail(errors, f"{path}: missing table")
    if facts.csp_values != [CSP_NO_IMAGES]:
        fail(errors, f"{path}: missing or incorrect Content Security Policy")
    if facts.forbidden_tags:
        for tag in sorted(set(facts.forbidden_tags)):
            if tag == "script":
                fail(errors, f"{path}: script elements are not allowed")
            else:
                fail(errors, f"{path}: {tag} is not allowed")
    for handler in sorted(set(facts.event_handlers)):
        fail(errors, f"{path}: event handler {handler} is not allowed")
    for tag, name, value in facts.unsafe_urls:
        fail(
            errors,
            f"{path}: external or local URL is not allowed in "
            f"{tag}[{name}]: {value[:80]}",
        )
    if "@import" in styles_lower:
        fail(errors, f"{path}: CSS @import is not allowed")
    if re.search(r"url\s*\(", styles, re.IGNORECASE):
        fail(errors, f"{path}: CSS url() is not allowed")
    for element_id in sorted(facts.duplicate_ids):
        fail(errors, f"{path}: duplicate id {element_id}")
    for href in facts.fragment_hrefs:
        if href[1:] and href[1:] not in facts.ids:
            fail(errors, f"{path}: navigation anchor {href} has no matching id")
    for attribute, reference in facts.aria_references:
        if reference not in facts.ids:
            fail(errors, f"{path}: broken {attribute} reference {reference}")
    for table in facts.tables:
        if table.captions != 1:
            fail(errors, f"{path}: table requires a caption")
        for scope in table.header_scopes:
            if scope not in {"col", "row", "colgroup", "rowgroup"}:
                fail(errors, f"{path}: table header requires scope")
    for svg in facts.svgs:
        _validate_svg_facts(path, svg, errors)
    if facts.svgs:
        if not re.search(r"overflow-x\s*:\s*auto", styles, re.IGNORECASE):
            fail(errors, f"{path}: diagram CSS requires overflow-x: auto")
        if not re.search(r"min-width\s*:\s*720px", styles, re.IGNORECASE):
            fail(errors, f"{path}: diagram SVG CSS requires min-width: 720px")
        if not re.search(r"font-size\s*:\s*(?:1[4-9]|[2-9]\d)px", styles):
            fail(errors, f"{path}: diagram labels must be at least 14px")
    if not allow_placeholders and PLACEHOLDER_PATTERN.search(text):
        fail(errors, f"{path}: unresolved template placeholder")


def validate_svg(path: Path, text: str, errors: list[str]) -> None:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        fail(errors, f"{path}: invalid SVG XML: {exc}")
        return
    if root.tag.rsplit("}", 1)[-1] != "svg":
        fail(errors, f"{path}: root element must be SVG")
        return
    if not root.get("viewBox"):
        fail(errors, f"{path}: SVG requires viewBox")
    if root.get("role") != "img":
        fail(errors, f"{path}: SVG requires role=\"img\"")
    labelled = (root.get("aria-labelledby") or "").split()
    ids = {element.get("id") for element in root.iter() if element.get("id")}
    if len(labelled) != 2 or any(reference not in ids for reference in labelled):
        fail(errors, f"{path}: SVG aria-labelledby references are broken")
    visuals = [
        element
        for element in root.iter()
        if element.tag.rsplit("}", 1)[-1] in VISUAL_SVG_TAGS
    ]
    if not visuals:
        fail(errors, f"{path}: SVG must contain visual elements")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--markdown", action="append", default=[], help="Markdown file to validate"
    )
    parser.add_argument(
        "--html", action="append", default=[], help="Standalone HTML file to validate"
    )
    parser.add_argument("--svg", action="append", default=[], help="SVG file to validate")
    parser.add_argument(
        "--manifest", action="append", default=[], help="Visual manifest to validate"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--strict-generated", action="store_true")
    mode.add_argument("--template", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    errors: list[str] = []
    markdown_paths = [Path(item) for item in args.markdown]
    html_paths = [Path(item) for item in args.html]
    svg_paths = [Path(item) for item in args.svg]
    manifest_paths = [Path(item) for item in args.manifest]
    strict = bool(args.strict_generated or args.template)

    if not markdown_paths and not html_paths and not svg_paths and not manifest_paths:
        fail(errors, "provide at least one --markdown, --html, --svg, or --manifest file")
    if manifest_paths and not args.strict_generated:
        fail(errors, "--manifest requires --strict-generated")

    for path in manifest_paths:
        if not path.exists():
            fail(errors, f"{path}: file does not exist")
            continue
        try:
            load_manifest(path)
        except ContractError as exc:
            fail(errors, str(exc))

    for path in markdown_paths:
        if not path.exists():
            fail(errors, f"{path}: file does not exist")
            continue
        validate_markdown(path, read_text(path), errors, strict=args.strict_generated)

    for path in html_paths:
        if not path.exists():
            fail(errors, f"{path}: file does not exist")
            continue
        text = read_text(path)
        if strict:
            validate_html_strict(
                path, text, errors, allow_placeholders=bool(args.template)
            )
        else:
            validate_html_legacy(path, text, errors)

    for path in svg_paths:
        if not path.exists():
            fail(errors, f"{path}: file does not exist")
            continue
        validate_svg(path, read_text(path), errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Boomi documentation validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
