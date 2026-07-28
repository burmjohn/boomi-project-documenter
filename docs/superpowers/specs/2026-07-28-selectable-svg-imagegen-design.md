# Selectable SVG and ImageGen Diagram Design

**Date:** July 28, 2026

**Target release:** 2.0.0

**Status:** Approved for implementation planning

## Purpose

Boomi Project Documenter currently directs agents to write inline SVG diagrams
from a template. The existing evidence-driven visuals design specifies a
deterministic manifest-to-SVG renderer, but that renderer and its supporting
contracts have not yet been implemented.

Release 2.0.0 will close that gap and add an explicitly requested ImageGen mode
as an alternative final diagram format. Deterministic SVG remains the canonical
technical representation in both modes. ImageGen may refine a rasterized SVG
blueprint, but a generated image is never accepted without a recorded semantic
review against the evidence manifest.

## Goals

- Generate technical diagrams from a versioned evidence manifest instead of
  unconstrained hand-authored SVG.
- Let the requester select `none`, `svg`, or `imagegen` diagram mode.
- Invoke ImageGen only when the requester explicitly asks for it.
- Allow an accepted ImageGen PNG to be delivered separately, embedded in the
  standalone HTML report, or both.
- Preserve the standalone, safe, evidence-backed nature of generated reports.
- Fail closed when a generated image cannot be verified.
- Release the new output contract as version 2.0.0.

## Non-goals

- ImageGen does not infer topology, runtime behavior, deployment state, or
  evidence status.
- A generated PNG is not proof of process behavior.
- Strict validation does not claim to understand diagram pixels.
- The bundled test suite does not make paid or networked ImageGen calls.
- Version 2.0.0 implementation does not publish a release, create a Git tag, or
  modify an installed copy of the skill.

## Output selection

The documentation request selects one visual mode:

```text
visual mode: none | svg | imagegen
```

- `none` omits diagrams and documents the evidence limitation when appropriate.
- `svg` delivers the deterministic SVG and may embed it inline in standalone
  HTML.
- `imagegen` creates the same deterministic SVG as an internal canonical
  blueprint, rasterizes it, sends the raster reference to ImageGen, verifies
  the result, and delivers only the accepted PNG as the user-facing diagram.

ImageGen mode is opt-in. An agent must not select it merely because a visual
companion would be useful.

An accepted PNG supports these placements:

```text
placement: separate | embedded | both
```

In `separate` mode, the PNG is an independent deliverable and the standalone
HTML does not reference it. In `embedded` mode, the PNG is encoded as a bounded
`data:image/png;base64,...` value so the report remains a single portable file.
`both` produces the independent PNG and embeds the identical verified bytes.
Each diagram uses `<diagram-id>.png`; its verification record uses
`<diagram-id>.imagegen-verification.json`.

## Architecture

### Evidence manifest

`references/visual-manifest.schema.json` defines the versioned source contract
for project identity, evidence date, diagram type, nodes, labels, directed
edges, branch labels, evidence scope, evidence state, title, description, and
canonical parity facts.

The manifest is the only source of technical diagram content. Unsupported
diagram types, excess topology, invalid identifiers, missing accessibility
text, and incomplete evidence classification fail before rendering.

### Deterministic SVG renderer

`scripts/render_boomi_visual.py` validates the manifest and creates stable,
accessible SVG. Identical canonical input produces identical output. The
renderer escapes all evidence-derived text and assigns document-safe unique
IDs.

The renderer is required for `svg` and `imagegen` modes. In ImageGen mode, the
SVG is an internal truth artifact even when it is not included in the final
deliverables.

### ImageGen workflow

`scripts/capture_visual_preview.py` converts the canonical SVG into a raster
blueprint suitable for the runtime's ImageGen tool. The skill cannot assume
that a local Python process can call a host-specific image-generation tool, so
`references/imagegen-diagram-guide.md` defines the agent-facing invocation
workflow and constrained prompt.

The prompt instructs ImageGen to preserve:

- Every visible node and its exact label.
- Every edge, direction, branch label, and endpoint.
- Evidence-state distinctions and the accompanying legend.
- Diagram title and scope.

Stylistic refinement may change spacing, shape styling, color, typography, and
non-semantic ornament only when those changes do not obscure or alter the
manifest content.

## Semantic verification

ImageGen output is reviewed against the manifest and canonical blueprint before
inclusion. The reviewer checks every:

- Node and exact visible label.
- Directed connection and endpoint.
- Branch and branch label.
- Evidence-state marker and legend entry.
- Title, scope, warning, and disclosure.

`references/imagegen-verification.schema.json` defines a sidecar record
containing:

- Manifest SHA-256 digest.
- Canonical SVG SHA-256 digest.
- Generated PNG SHA-256 digest.
- Review timestamp and a nonempty reviewer identity string. An AI reviewer uses
  its agent and runtime identifier rather than a human name.
- Per-category verification results.
- Attempt count and final disposition.

Failed output may be regenerated at most three times. If no attempt passes,
ImageGen mode produces no diagram and the completion report states the
validation gap. The workflow does not silently fall back to publishing SVG
unless the requester authorizes that output.

The strict validator proves sidecar structure, digest consistency, attempt
bounds, safe image embedding, and final passing disposition. It does not claim
that those mechanical checks prove pixel-level semantic accuracy. That
limitation is stated in the guide and completion report.

## Standalone HTML safety

SVG reports retain the existing inline-SVG policy. ImageGen reports may contain
only a verified PNG encoded directly as a PNG data URL.

For ImageGen embedding, the Content Security Policy changes `img-src 'none'` to
`img-src data:`. Strict validation rejects:

- Non-PNG data URLs.
- Remote, protocol-relative, or local-file image sources.
- SVG image data URLs.
- Data URLs whose decoded PNG exceeds 8 MiB.
- Embedded bytes whose digest differs from the passing verification sidecar.
- Missing or duplicate embedded copies for any diagram selected for embedded
  placement.

All other script, style, URL, form, frame, object, and navigation restrictions
from the evidence-driven visuals design remain in force.

## Components

Release 2.0.0 adds or updates:

- `references/visual-manifest.schema.json`
- `references/visual-generation-guide.md`
- `references/imagegen-diagram-guide.md`
- `references/imagegen-verification.schema.json`
- `references/security-and-disclosure.md`
- `scripts/render_boomi_visual.py`
- `scripts/capture_visual_preview.py`
- `scripts/validate_boomi_docs.py`
- `SKILL.md`
- `agents/openai.yaml`
- `CHANGELOG.md`
- `tests/` and its valid, invalid, and adversarial fixtures

The existing visual HTML template and fictional sample are updated to
demonstrate the selectable output contract without presenting generated pixels
as runtime evidence.

## Error handling

- Invalid evidence manifests fail before any rendering or ImageGen invocation.
- Renderer and rasterization failures return nonzero status with an actionable
  message and leave no accepted output record.
- ImageGen tool unavailability is a validation gap, not a pass.
- A missing, stale, malformed, or failing verification sidecar rejects the PNG.
- Digest mismatches reject separate and embedded PNGs.
- Exhausted generation attempts omit the image and identify the failed checks.
- Legacy validator invocations retain their version 1 structural behavior.

## Testing

Standard-library unit and integration tests cover:

- Stable SVG output for identical canonical manifests.
- Supported diagram patterns, topology limits, escaping, accessibility, and
  globally unique IDs.
- `none`, `svg`, and `imagegen` output selection.
- Valid separate, embedded, and combined PNG placement fixtures.
- Missing, altered, stale, and malformed ImageGen verification records.
- Incorrect manifest, SVG, and PNG digests.
- Attempt counts of one through three and rejection above three.
- Fail-closed behavior after unsuccessful semantic reviews.
- Safe CSP and rejection of unsafe or oversized data URLs.
- Fact parity across the manifest, Markdown, HTML, SVG, and sidecar.
- Version and metadata agreement.

ImageGen integration tests use fixed generated-image fixtures and recorded
verification sidecars. A manual release evaluation performs fresh ImageGen
runs because generation is nondeterministic and may incur cost.

## Versioning and release boundary

This change upgrades the repository from 1.0.2 to 2.0.0 because it changes the
diagram source contract, output modes, validator behavior, package structure,
and evidence-review workflow.

Implementation aligns:

- `VERSION`
- README current-version and release documentation
- Skill metadata conventions
- `agents/openai.yaml`
- Validator and package tests
- `CHANGELOG.md`

Tagging, publishing, and updating installed copies remain separate actions that
require explicit authorization.

## Acceptance criteria

1. Every technical diagram begins with a schema-valid evidence manifest.
2. `svg` mode produces deterministic, accessible SVG.
3. `imagegen` mode is explicit opt-in and uses a rasterized canonical SVG as
   its reference.
4. No generated PNG is delivered or embedded without a passing, digest-matched
   semantic-verification sidecar.
5. Failed ImageGen output is retried no more than three times and is omitted
   when all attempts fail.
6. Embedded images remain standalone and pass the restricted PNG data-URL and
   CSP contract.
7. Strict validation distinguishes mechanical checks from semantic review.
8. Tests do not require network access or paid generation.
9. `VERSION`, README, metadata, tests, and `CHANGELOG.md` agree on 2.0.0.
10. The legacy validator interface remains available for version 1 documents.
