# Visual generation guide

Use this guide to decide whether a Boomi report needs a diagram and to create
that diagram from current evidence. The visual manifest is the source of truth
for every technical visual.

## Select an output mode

Choose one mode after the Markdown facts are stable.

| Mode | Use when | Delivered visual |
| --- | --- | --- |
| `none` | The requester doesn't need a diagram, or evidence doesn't establish useful topology. | No diagram; explain the evidence gap in prose. |
| `svg` | The requester needs an exact, portable technical diagram. | Deterministic standalone SVG, optionally embedded inline in HTML. |
| `imagegen` | The requester explicitly asks for an AI-generated alternative. | Verified PNG derived from the canonical SVG blueprint. |

Don't invoke ImageGen automatically. Read
`imagegen-diagram-guide.md` before you use `imagegen` mode.

## Classify visual evidence

Assign evidence scope and state before you create diagram nodes or edges.

- `configuration` describes current component XML or inventory-backed wiring.
- `observed-execution` describes behavior supported by current execution logs
  or test results.
- `mixed` includes both and makes the distinction visible.

Use one evidence state for each node:

- `configured`: Current evidence proves the configuration.
- `observed`: Current execution or test evidence proves the behavior.
- `inferred`: Wiring or naming suggests the element, but evidence doesn't prove
  its behavior.
- `unverified`: The element exists, but its relevant state wasn't verified.
- `historical`: Only historical evidence supports the element.

Color isn't sufficient. The renderer adds text and stroke treatment so each
state remains distinguishable without color.

## Choose a diagram pattern

Select the smallest pattern that answers the documentation question.

| Type | Use for |
| --- | --- |
| `context` | External systems and the Boomi boundary. |
| `routing` | Decisions, branches, route keys, and destinations. |
| `subprocess` | Parent-to-child process relationships. |
| `failure` | Error, retry, notification, and response paths. |
| `state` | Evidence-backed state transitions. |

Split the visual when it needs more than nine primary nodes or a decision needs
more than three outgoing branches. Don't compress an unreadable process into
one image.

## Create the manifest

Create UTF-8 JSON that conforms to `visual-manifest.schema.json`. Preserve
evidence values exactly, including component IDs, names, versions, branch
labels, and dates.

Each manifest contains:

- `schema_version` set to `1`.
- Project ID, project name, and evidence date.
- Canonical parity facts for Markdown and HTML.
- One or more diagrams with unique lowercase hyphenated IDs.
- Nodes, directed edges, evidence scope, title, and accessible description.

Validate and render the manifest with:

```bash
python3 scripts/render_boomi_visual.py \
  --manifest docs/visual-manifest.json \
  --output-dir docs/diagrams
```

Use `--output FILE` only when the manifest contains exactly one diagram.

## Embed deterministic SVG

In `svg` mode, keep the standalone SVG as the canonical artifact and copy its
exact markup inline into the standalone HTML. Don't reference the SVG through
an `<img>` element.

Place every inline SVG inside:

```html
<div class="diagram-scroll">
  <!-- Exact rendered SVG markup -->
</div>
```

The HTML source must provide horizontal scrolling, a `720px` SVG minimum
width, labels of at least `14px`, visible focus, reduced-motion behavior, and
print rules that avoid splitting the diagram.

## Validate generated output

Run strict validation with every artifact that belongs to the report.

```bash
python3 scripts/validate_boomi_docs.py \
  --strict-generated \
  --markdown docs/project-documentation.md \
  --html docs/visual-guide.html \
  --manifest docs/visual-manifest.json \
  --svg docs/diagrams/order-routing.svg
```

Treat a missing renderer, malformed manifest, unsupported topology, validation
failure, or missing evidence as a gap. Don't hand-author replacement topology
that bypasses the manifest.

## Common mistakes

Avoid these failures when you create visuals:

- Treating configured wiring as observed runtime behavior.
- Adding systems, branches, retries, or outcomes that the evidence doesn't
  establish.
- Reusing node or SVG IDs across diagrams.
- Shrinking a wide diagram until labels are unreadable.
- Publishing ImageGen output without its semantic review and digest-matched
  sidecar.
- Falling back to an unrequested output mode without requester authorization.
