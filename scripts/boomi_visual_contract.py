#!/usr/bin/env python3
"""Shared validation and canonicalization for Boomi visual artifacts."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
DIAGRAM_TYPES = {"context", "routing", "subprocess", "failure", "state"}
ORIENTATIONS = {"horizontal", "vertical"}
NODE_KINDS = {
    "source",
    "step",
    "decision",
    "target",
    "error",
    "subprocess",
    "system",
    "state",
}
EVIDENCE_SCOPES = {"configuration", "observed-execution", "mixed"}
EVIDENCE_STATES = {"configured", "observed", "inferred", "unverified", "historical"}
VERIFICATION_CHECKS = {
    "nodes",
    "labels",
    "edges",
    "evidence_states",
    "title_and_scope",
}


class ContractError(ValueError):
    """Raised when a visual artifact violates the versioned contract."""


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise ContractError(f"{path}: cannot read JSON: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(
            f"{path}: invalid JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc


def canonical_json(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _object(value: object, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{path} must be an object")
    return value


def _array(value: object, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ContractError(f"{path} must be an array")
    return value


def _string(
    value: object,
    path: str,
    *,
    allowed: set[str] | None = None,
    identifier: bool = False,
    allow_empty: bool = False,
) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise ContractError(f"{path} must be a nonempty string")
    if allowed is not None and value not in allowed:
        choices = ", ".join(sorted(allowed))
        raise ContractError(f"{path} must be one of: {choices}")
    if identifier and not ID_PATTERN.fullmatch(value):
        raise ContractError(
            f"{path} must use lowercase letters, digits, and single hyphens"
        )
    return value


def _integer(value: object, path: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ContractError(f"{path} must be an integer of at least {minimum}")
    return value


def _require_keys(value: dict[str, Any], path: str, keys: set[str]) -> None:
    missing = sorted(keys - value.keys())
    if missing:
        raise ContractError(f"{path} is missing required field: {missing[0]}")


def _validate_project(value: object) -> dict[str, Any]:
    project = _object(value, "project")
    _require_keys(project, "project", {"id", "name", "evidence_date"})
    _string(project["id"], "project.id")
    _string(project["name"], "project.name")
    evidence_date = _string(project["evidence_date"], "project.evidence_date")
    try:
        datetime.strptime(evidence_date, "%Y-%m-%d")
    except ValueError as exc:
        raise ContractError("project.evidence_date must use YYYY-MM-DD") from exc
    return project


def _validate_facts(value: object) -> dict[str, Any]:
    facts = _object(value, "facts")
    required = {
        "component_versions",
        "inventory_counts",
        "risk_counts",
        "risks",
        "next_step_ids",
    }
    _require_keys(facts, "facts", required)
    _array(facts["component_versions"], "facts.component_versions")
    _object(facts["inventory_counts"], "facts.inventory_counts")
    _object(facts["risk_counts"], "facts.risk_counts")
    _array(facts["risks"], "facts.risks")
    next_steps = _array(facts["next_step_ids"], "facts.next_step_ids")
    for index, item in enumerate(next_steps):
        _string(item, f"facts.next_step_ids[{index}]", identifier=True)
    return facts


def _validate_diagram(value: object, index: int) -> dict[str, Any]:
    path = f"diagrams[{index}]"
    diagram = _object(value, path)
    required = {
        "id",
        "type",
        "orientation",
        "title",
        "description",
        "evidence_scope",
        "nodes",
        "edges",
    }
    _require_keys(diagram, path, required)
    diagram_id = _string(diagram["id"], f"{path}.id", identifier=True)
    _string(diagram["type"], f"{path}.type", allowed=DIAGRAM_TYPES)
    _string(diagram["orientation"], f"{path}.orientation", allowed=ORIENTATIONS)
    _string(diagram["title"], f"{path}.title")
    _string(diagram["description"], f"{path}.description")
    _string(
        diagram["evidence_scope"],
        f"{path}.evidence_scope",
        allowed=EVIDENCE_SCOPES,
    )

    nodes = _array(diagram["nodes"], f"{path}.nodes")
    if not nodes:
        raise ContractError(f"diagram {diagram_id} must contain at least 1 node")
    if len(nodes) > 9:
        raise ContractError(f"diagram {diagram_id} supports at most 9 nodes")

    node_ids: set[str] = set()
    decision_ids: set[str] = set()
    for node_index, item in enumerate(nodes):
        node_path = f"{path}.nodes[{node_index}]"
        node = _object(item, node_path)
        _require_keys(
            node,
            node_path,
            {"id", "label", "kind", "evidence_state"},
        )
        node_id = _string(node["id"], f"{node_path}.id", identifier=True)
        if node_id in node_ids:
            raise ContractError(f"diagram {diagram_id} has duplicate node id {node_id}")
        node_ids.add(node_id)
        _string(node["label"], f"{node_path}.label")
        kind = _string(node["kind"], f"{node_path}.kind", allowed=NODE_KINDS)
        _string(
            node["evidence_state"],
            f"{node_path}.evidence_state",
            allowed=EVIDENCE_STATES,
        )
        if kind == "decision":
            decision_ids.add(node_id)

    edges = _array(diagram["edges"], f"{path}.edges")
    edge_ids: set[str] = set()
    outgoing_decisions = {node_id: 0 for node_id in decision_ids}
    for edge_index, item in enumerate(edges):
        edge_path = f"{path}.edges[{edge_index}]"
        edge = _object(item, edge_path)
        _require_keys(edge, edge_path, {"id", "from", "to", "label"})
        edge_id = _string(edge["id"], f"{edge_path}.id", identifier=True)
        if edge_id in edge_ids:
            raise ContractError(f"diagram {diagram_id} has duplicate edge id {edge_id}")
        edge_ids.add(edge_id)
        source = _string(edge["from"], f"{edge_path}.from", identifier=True)
        target = _string(edge["to"], f"{edge_path}.to", identifier=True)
        _string(edge["label"], f"{edge_path}.label", allow_empty=True)
        for endpoint in (source, target):
            if endpoint not in node_ids:
                raise ContractError(
                    f"diagram {diagram_id} edge {edge_id} references unknown node {endpoint}"
                )
        if source in outgoing_decisions:
            outgoing_decisions[source] += 1

    for node_id, count in outgoing_decisions.items():
        if count > 3:
            raise ContractError(
                f"diagram {diagram_id} decision {node_id} supports at most "
                "3 outgoing branches"
            )
    return diagram


def validate_manifest(value: object) -> dict[str, Any]:
    manifest = _object(value, "manifest")
    _require_keys(
        manifest,
        "manifest",
        {"schema_version", "project", "facts", "diagrams"},
    )
    if _integer(manifest["schema_version"], "schema_version", minimum=1) != 1:
        raise ContractError("schema_version must be 1")
    _validate_project(manifest["project"])
    _validate_facts(manifest["facts"])
    diagrams = _array(manifest["diagrams"], "diagrams")
    diagram_ids: set[str] = set()
    for index, value_item in enumerate(diagrams):
        diagram = _validate_diagram(value_item, index)
        diagram_id = str(diagram["id"])
        if diagram_id in diagram_ids:
            raise ContractError(f"manifest has duplicate diagram id {diagram_id}")
        diagram_ids.add(diagram_id)
    return manifest


def load_manifest(path: Path) -> dict[str, Any]:
    return validate_manifest(load_json(path))


def validate_verification(value: object) -> dict[str, Any]:
    verification = _object(value, "verification")
    required = {
        "schema_version",
        "diagram_id",
        "manifest_sha256",
        "svg_sha256",
        "png_sha256",
        "reviewed_at",
        "reviewer",
        "attempt_count",
        "checks",
        "disposition",
    }
    _require_keys(verification, "verification", required)
    if _integer(verification["schema_version"], "schema_version", minimum=1) != 1:
        raise ContractError("verification schema_version must be 1")
    _string(verification["diagram_id"], "diagram_id", identifier=True)
    for field in ("manifest_sha256", "svg_sha256", "png_sha256"):
        digest = _string(verification[field], field)
        if not DIGEST_PATTERN.fullmatch(digest):
            raise ContractError(f"{field} must be a lowercase SHA-256 digest")
    reviewed_at = _string(verification["reviewed_at"], "reviewed_at")
    try:
        datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError("reviewed_at must be an ISO-8601 timestamp") from exc
    _string(verification["reviewer"], "reviewer")
    attempts = _integer(verification["attempt_count"], "attempt_count", minimum=1)
    if attempts > 3:
        raise ContractError("attempt_count must be between 1 and 3")
    checks = _object(verification["checks"], "checks")
    _require_keys(checks, "checks", VERIFICATION_CHECKS)
    for field in sorted(VERIFICATION_CHECKS):
        if checks[field] is not True:
            raise ContractError(f"checks.{field} must be true")
    if verification["disposition"] != "pass":
        raise ContractError("disposition must be pass for accepted output")
    return verification
