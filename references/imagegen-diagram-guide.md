# ImageGen Diagram Guide

Use this workflow only when the requester explicitly selects `imagegen` as the
diagram mode. A generated PNG is an alternative presentation of the canonical
SVG blueprint; it is not an independent source of topology or runtime facts.

## Prerequisites

Before calling ImageGen:

1. Gather and classify the current Boomi evidence.
2. Create a schema-valid visual manifest.
3. Render the diagram with `scripts/render_boomi_visual.py`.
4. Validate the canonical SVG.
5. Capture the SVG as a raster blueprint with
   `scripts/capture_visual_preview.py`.

Example:

```bash
python3 scripts/render_boomi_visual.py \
  --manifest docs/visual-manifest.json \
  --output docs/diagrams/order-routing.svg

python3 scripts/capture_visual_preview.py \
  --svg docs/diagrams/order-routing.svg \
  --output docs/diagrams/order-routing-blueprint.png \
  --browser /path/to/chromium
```

Browser capture is an environmental prerequisite for ImageGen mode. If no
compatible browser is available, report that gap and omit the generated image.
Do not send unconstrained prose to ImageGen as a substitute.

## ImageGen invocation

Attach the rasterized blueprint as the referenced image and use this prompt,
replacing only the bracketed style phrase:

```text
Refine the attached technical diagram into [requested visual style].

Preserve every node, exact visible label, directed edge, endpoint, branch
label, evidence-state distinction, legend entry, title, and evidence scope.
Do not add, remove, rename, merge, split, redirect, or reorder technical
content. You may improve spacing, typography, color, shape styling, and
non-semantic ornament only when the result remains unambiguous. Return one
complete diagram with all original technical content visible.
```

The invocation must use the host runtime's image-generation tool with the
blueprint attached as its image reference. A local script does not assume
access to host credentials or tool APIs.

## Semantic review

Compare the generated image with both the manifest and the canonical SVG.
Review every item; a partial or inferred pass is a failure.

| Sidecar check | Required comparison |
| --- | --- |
| `nodes` | Every manifest node appears exactly once; no extra node appears. |
| `labels` | Every visible node and branch label is exact and legible. |
| `edges` | Every edge has the correct source, target, and direction. |
| `evidence_states` | Every state marker and legend meaning is preserved. |
| `title_and_scope` | The title, evidence scope, and disclosure remain accurate. |

On failure, generate another image from the same canonical blueprint with a
prompt that identifies the observed discrepancy. Stop after three total
attempts. If the third attempt fails, omit the image and report the failed
checks; do not silently publish the SVG instead.

## Verification record

For an accepted `<diagram-id>.png`, create
`<diagram-id>.imagegen-verification.json` using
`references/imagegen-verification.schema.json`. Record:

- SHA-256 of the canonical JSON manifest.
- SHA-256 of the exact canonical SVG bytes.
- SHA-256 of the exact accepted PNG bytes.
- ISO-8601 review timestamp.
- Human reviewer identity or AI agent/runtime identifier.
- Attempt count from 1 through 3.
- `true` for all five semantic checks.
- Final disposition `pass`.

An AI review must inspect the actual generated pixels. Hashes and schema
validation prove provenance and consistency, not semantic accuracy.

## Placement

- `separate`: deliver `<diagram-id>.png`; do not reference it from the
  standalone HTML.
- `embedded`: embed the verified bytes as one
  `data:image/png;base64,...` image with nonempty `alt` and
  `data-diagram-id="<diagram-id>"`.
- `both`: deliver the PNG and embed the identical verified bytes.

Embedded decoded PNG data must not exceed 8 MiB. HTML containing an embedded
PNG uses `img-src data:` in its Content Security Policy. HTML without an
embedded PNG retains `img-src 'none'`.

## Final validation

```bash
python3 scripts/validate_boomi_docs.py \
  --strict-generated \
  --manifest docs/visual-manifest.json \
  --svg docs/diagrams/order-routing.svg \
  --html docs/visual-guide.html \
  --imagegen-verification \
    docs/diagrams/order-routing.imagegen-verification.json
```

Treat a missing tool, browser, image, sidecar, review, or passing validator run
as a validation gap, not as successful ImageGen output.
