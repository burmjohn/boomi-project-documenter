#!/usr/bin/env python3
"""Render deterministic, accessible SVG diagrams from a Boomi visual manifest."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping
from html import escape
from pathlib import Path
from typing import Any

try:
    from .boomi_visual_contract import ContractError, load_manifest
except ImportError:  # Direct script execution.
    from boomi_visual_contract import ContractError, load_manifest


BOX_WIDTH = 170
BOX_HEIGHT = 76
HORIZONTAL_WIDTH = 960
HORIZONTAL_HEIGHT = 420
VERTICAL_WIDTH = 720


def _text(value: object) -> str:
    return escape(str(value), quote=True)


def _positions(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    orientation: str,
) -> tuple[int, int, dict[str, tuple[int, int]]]:
    if orientation == "vertical":
        height = 160 + len(nodes) * 150
        return (
            VERTICAL_WIDTH,
            height,
            {
                str(node["id"]): ((VERTICAL_WIDTH - BOX_WIDTH) // 2, 70 + index * 150)
                for index, node in enumerate(nodes)
            },
        )

    node_order = {str(node["id"]): index for index, node in enumerate(nodes)}
    indegree = {node_id: 0 for node_id in node_order}
    outgoing: dict[str, list[str]] = {node_id: [] for node_id in node_order}
    for edge in edges:
        source = str(edge["from"])
        target = str(edge["to"])
        outgoing[source].append(target)
        indegree[target] += 1

    depths = {node_id: 0 for node_id in node_order}
    ready = sorted(
        (node_id for node_id, count in indegree.items() if count == 0),
        key=node_order.get,
    )
    while ready:
        source = ready.pop(0)
        for target in sorted(outgoing[source], key=node_order.get):
            depths[target] = max(depths[target], depths[source] + 1)
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
                ready.sort(key=node_order.get)

    layers: dict[int, list[str]] = {}
    for node_id in node_order:
        layers.setdefault(depths[node_id], []).append(node_id)
    max_depth = max(layers, default=0)
    max_rows = max((len(layer) for layer in layers.values()), default=1)
    height = max(HORIZONTAL_HEIGHT, 180 + max_rows * 140)
    x_step = (
        (HORIZONTAL_WIDTH - 80 - BOX_WIDTH) / max_depth if max_depth else 0
    )
    positions: dict[str, tuple[int, int]] = {}
    for depth, layer in sorted(layers.items()):
        x = round(40 + depth * x_step)
        if len(layer) == 1:
            y_values = [(height - 80 - BOX_HEIGHT) // 2]
        else:
            available = height - 160
            y_gap = (available - len(layer) * BOX_HEIGHT) / (len(layer) - 1)
            y_values = [
                round(60 + row * (BOX_HEIGHT + y_gap))
                for row in range(len(layer))
            ]
        for node_id, y in zip(layer, y_values, strict=True):
            positions[node_id] = (x, y)
    return HORIZONTAL_WIDTH, height, positions


def _box_boundary_point(
    center_x: int, center_y: int, delta_x: int, delta_y: int
) -> tuple[int, int]:
    if delta_x == 0 and delta_y == 0:
        return center_x, center_y
    x_scale = (BOX_WIDTH / 2) / abs(delta_x) if delta_x else float("inf")
    y_scale = (BOX_HEIGHT / 2) / abs(delta_y) if delta_y else float("inf")
    scale = min(x_scale, y_scale)
    return round(center_x + delta_x * scale), round(center_y + delta_y * scale)


def _edge_line(
    edge: Mapping[str, object],
    positions: Mapping[str, tuple[int, int]],
    diagram_id: str,
    marker_id: str,
) -> str:
    source_x, source_y = positions[str(edge["from"])]
    target_x, target_y = positions[str(edge["to"])]
    source_center = (source_x + BOX_WIDTH // 2, source_y + BOX_HEIGHT // 2)
    target_center = (target_x + BOX_WIDTH // 2, target_y + BOX_HEIGHT // 2)
    delta_x = target_center[0] - source_center[0]
    delta_y = target_center[1] - source_center[1]
    source_anchor = _box_boundary_point(
        source_center[0], source_center[1], delta_x, delta_y
    )
    target_anchor = _box_boundary_point(
        target_center[0], target_center[1], -delta_x, -delta_y
    )
    label_x = (source_anchor[0] + target_anchor[0]) // 2
    label_y = (source_anchor[1] + target_anchor[1]) // 2 - 8
    label = str(edge["label"])
    label_svg = (
        f'<text class="edge-label" x="{label_x}" y="{label_y}">{_text(label)}</text>'
        if label
        else ""
    )
    return (
        f'<g id="{_text(diagram_id)}-{_text(edge["id"])}">'
        f'<line class="edge" x1="{source_anchor[0]}" y1="{source_anchor[1]}" '
        f'x2="{target_anchor[0]}" y2="{target_anchor[1]}" '
        f'marker-end="url(#{marker_id})"/>'
        f"{label_svg}</g>"
    )


def _node_group(
    node: Mapping[str, object], x: int, y: int, diagram_id: str
) -> str:
    node_id = f"{_text(diagram_id)}-{_text(node['id'])}"
    label = _text(node["label"])
    kind = _text(node["kind"])
    evidence_state = _text(node["evidence_state"])
    return (
        f'<g id="{node_id}" class="node {kind} evidence-{evidence_state}">'
        f'<rect x="{x}" y="{y}" width="{BOX_WIDTH}" height="{BOX_HEIGHT}" rx="10"/>'
        f'<text x="{x + BOX_WIDTH // 2}" y="{y + 34}">{label}</text>'
        f'<text class="state-label" x="{x + BOX_WIDTH // 2}" y="{y + 57}">'
        f"{evidence_state}</text></g>"
    )


def render_diagram(diagram: dict[str, object]) -> str:
    """Render one validated diagram into stable standalone SVG text."""

    diagram_id = str(diagram["id"])
    nodes = list(diagram["nodes"])  # type: ignore[arg-type]
    edges = list(diagram["edges"])  # type: ignore[arg-type]
    width, height, positions = _positions(
        nodes, edges, str(diagram["orientation"])
    )
    title_id = f"{diagram_id}-title"
    desc_id = f"{diagram_id}-desc"
    marker_id = f"{diagram_id}-arrow"

    edge_markup = "".join(
        _edge_line(edge, positions, diagram_id, marker_id)
        for edge in sorted(edges, key=lambda item: str(item["id"]))
    )
    node_markup = "".join(
        _node_group(node, *positions[str(node["id"])], diagram_id) for node in nodes
    )
    states = sorted({str(node["evidence_state"]) for node in nodes})
    legend_items = "".join(
        f'<text class="legend-item evidence-{_text(state)}" '
        f'x="{40 + index * 180}" y="{height - 32}">{_text(state)}</text>'
        for index, state in enumerate(states)
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" class="boomi-diagram" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-labelledby="{title_id} {desc_id}" '
        f'style="min-width:720px">'
        f'<title id="{title_id}">{_text(diagram["title"])}</title>'
        f'<desc id="{desc_id}">{_text(diagram["description"])} '
        f'Evidence scope: {_text(diagram["evidence_scope"])}.</desc>'
        "<defs>"
        f'<marker id="{marker_id}" markerWidth="10" markerHeight="10" '
        'refX="9" refY="3" orient="auto" markerUnits="strokeWidth">'
        '<path d="M0,0 L0,6 L9,3 z"/></marker>'
        "</defs>"
        "<style>"
        ".boomi-diagram{font-family:Arial,sans-serif;background:#fff;color:#172033}"
        ".node rect{fill:#edf7f7;stroke:#087f8c;stroke-width:2}"
        ".node text{text-anchor:middle;font-size:14px;fill:#172033}"
        ".state-label,.legend-item{font-size:14px;font-style:italic}"
        ".evidence-observed rect{stroke-width:4}"
        ".evidence-inferred rect,.evidence-unverified rect{stroke-dasharray:7 5}"
        ".evidence-historical rect{stroke:#667085}"
        ".edge{stroke:#087f8c;stroke-width:2;fill:none}"
        ".edge-label{font-size:14px;text-anchor:middle;fill:#172033}"
        ".legend-item{text-anchor:start;fill:#172033}"
        "</style>"
        f"{edge_markup}{node_markup}"
        f'<g aria-label="Evidence state legend">{legend_items}</g>'
        "</svg>\n"
    )


def _write_svg(path: Path, svg: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    output = parser.add_mutually_exclusive_group(required=True)
    output.add_argument("--output", type=Path)
    output.add_argument("--output-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        diagrams = sorted(manifest["diagrams"], key=lambda item: str(item["id"]))
        if args.output is not None:
            if len(diagrams) != 1:
                raise ContractError(
                    "--output requires a manifest containing exactly one diagram"
                )
            _write_svg(args.output, render_diagram(diagrams[0]))
        else:
            assert args.output_dir is not None
            args.output_dir.mkdir(parents=True, exist_ok=True)
            for diagram in diagrams:
                _write_svg(
                    args.output_dir / f"{diagram['id']}.svg",
                    render_diagram(diagram),
                )
    except (ContractError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    noun = "diagram" if len(diagrams) == 1 else "diagrams"
    print(f"Rendered {len(diagrams)} {noun}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
