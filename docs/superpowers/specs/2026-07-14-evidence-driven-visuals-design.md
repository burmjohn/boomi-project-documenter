# Evidence-driven visual documentation design

## Purpose

Update `boomi-project-documenter` so it produces safer, more consistent Boomi
documentation and generates technical SVG, HTML, and raster previews that remain
traceable to project evidence.

The update preserves Markdown as the documentation source of truth. Visual
artifacts summarize the same verified facts and never substitute generated
imagery for technical evidence.

## Scope

This release covers the complete skill package:

- Core workflow and trigger metadata.
- Evidence selection, freshness, conflict resolution, and disclosure safety.
- Visual selection, diagram semantics, SVG accessibility, and responsive layout.
- Standalone HTML safety and portability.
- Markdown-to-HTML fact consistency.
- Validator behavior and regression fixtures.
- Codex UI metadata.
- Reproducible sample HTML and preview generation guidance.

Automatic extraction of arbitrary Boomi XML is outside this release. Agents
continue to interpret project evidence into a versioned JSON manifest. A
bundled deterministic renderer converts that manifest into SVG that can be
validated, embedded in HTML, and captured as a PNG preview.

## Design principles

1. Evidence controls every claim and visual element.
2. Markdown is required; visual outputs are conditional.
3. Static wiring and observed execution are different claim scopes.
4. Technical diagrams are deterministic SVG, not generative raster imagery.
5. PNG previews are reproducible derivatives of canonical HTML or SVG.
6. Safety, accessibility, and portability are validator contracts.
7. The package remains dependency-light and uses Python's standard library for
   validation and tests.

## Output selection

The workflow first determines requested deliverables and available evidence.

- Always create or refresh the requested Markdown documentation.
- Create standalone HTML when the user requests it or when a visual companion
  materially improves the documentation.
- Create a visual manifest and standalone SVG only when current evidence
  establishes a useful topology, relationship, decision, or state transition.
- Embed the rendered SVG inline when creating standalone HTML. The standalone
  SVG remains the canonical diagram artifact and must not be referenced through
  an `<img>` element.
- When evidence cannot support a diagram, state the gap in prose. The validator
  must accept this evidence-honest omission.
- Create PNG previews only from the completed HTML or SVG. Do not use AI image
  generation for architecture, process wiring, runtime status, or evidence.

## Evidence and disclosure model

The skill classifies evidence before writing:

- Inventory and platform API evidence establish component existence and current
  version.
- Local XML establishes behavior only when component ID and version align with
  the current inventory or a documented pull/sync record.
- Deployment records establish deployed versions and environments.
- Execution logs and test results establish observed runtime behavior.
- Existing documents and old pulls are historical unless current evidence
  re-establishes their claims.

Conflicts become explicit open risks. The agent does not silently choose the
most convenient source.

Before publishing, the agent classifies the audience and removes credentials,
tokens, secrets, personal data, sensitive payloads, internal host details, and
secret-bearing query parameters. Exact technical values are preserved only when
they are relevant and safe for the intended audience. All evidence inserted
into HTML or SVG is escaped as text.

## Visual contract

Each diagram starts from a JSON manifest with `schemaVersion: 1`. The manifest
contains project identity, evidence date, diagram scope, canonical parity facts,
and one or more diagrams. Each diagram declares:

- A unique diagram ID.
- A title and meaningful description.
- A scope of `static-wiring`, `observed-runtime`, `system-context`, or
  `data-relationship`.
- Nodes with unique IDs, semantic types, labels, and evidence references.
- Edges with unique IDs, semantic types, labels, and evidence references.
- Evidence states of `proven-current`, `inferred`, `historical`, or `open-risk`.

Supported node types are trigger, process, decision, subprocess, external
system, datastore, transform, response, and error handler. Supported edge types
are sequence, conditional, call, asynchronous, retry, response, and error.

The skill provides patterns for:

- System context.
- Linear process flow.
- Routing and fan-out.
- Subprocess calls.
- Error, retry, and response paths.

Evidence state uses text labels plus stroke or shape treatment. Color is never
the only distinction. A legend explains every state and non-obvious edge type.
Diagrams include a nearby evidence note that identifies whether the visual shows
configuration or observed execution.

The renderer command is:

```bash
python3 scripts/render_boomi_visual.py \
  --manifest path/to/visual-manifest.json \
  --output-dir path/to/diagrams
```

The renderer validates the manifest, escapes all text, assigns globally unique
SVG IDs, and produces a stable layout for identical input. It supports the five
documented diagram patterns. Unsupported manifest types or layouts fail with a
nonzero exit code and an actionable error. `--output-dir` writes one SVG per
diagram as `<diagram-id>.svg`, sorted by diagram ID. Diagram IDs must contain
only lowercase letters, digits, and hyphens. For a manifest containing exactly
one diagram, `--output FILE` may be used instead. The two output options are
mutually exclusive.

Canonical parity facts are project ID and name, evidence date, component IDs
and versions, inventory and risk counts, risk IDs and statuses, and ordered
next-step IDs. Markdown and HTML embed the same normalized fact object and its
SHA-256 digest. Markdown uses a `boomi-doc-facts` HTML comment; HTML uses an
inert `<template id="boomi-doc-facts">` element. Strict validation parses both
objects, recomputes their digests, and compares them with the manifest.

Canonical JSON is encoded as UTF-8 without a byte-order mark using sorted keys,
no insignificant whitespace, unescaped Unicode, and separators `,` and `:`.
This is equivalent to Python `json.dumps(value, sort_keys=True,
ensure_ascii=False, separators=(",", ":"))`. The digest is SHA-256 over only
those encoded fact-object bytes, excluding the Markdown comment or HTML
template wrapper.

## SVG and responsive behavior

Every SVG includes a `viewBox`, `role="img"`, unique `<title>` and `<desc>` IDs,
and a valid `aria-labelledby` reference. Marker, gradient, filter, title, and
description IDs are globally unique within the HTML document.

Every diagram appears in `.diagram-scroll`, which uses `overflow-x: auto`. The
SVG uses `min-width: 720px`, and diagram labels use at least `14px`. These
source rules keep labels readable at the `375px` mobile verification viewport
by scrolling instead of shrinking. A vertical layout may be selected in the
manifest. The renderer rejects a single diagram with more than nine primary
nodes or three outgoing branches from one decision and instructs the caller to
split it.

Tables include captions and explicit header scopes. Navigation exposes visible
keyboard focus. Smooth scrolling is disabled for reduced-motion preferences.
Print styles avoid splitting diagrams and critical tables when practical.

## Standalone HTML safety

Visual reports contain embedded CSS and inline SVG only. The validator rejects:

- Scripts, inline event-handler attributes, forms, frames, embeds, and objects.
- Meta refresh and active navigation directives.
- External or local linked images.
- External stylesheets, CSS imports, and CSS URLs.
- URL-bearing attributes other than HTML fragment navigation and internal SVG
  references.
- Duplicate IDs, broken local anchors, and broken ARIA references.
- Unresolved template placeholders in generated output.

HTML `<a href>` values may contain only `#id` fragments. SVG `href` and
`xlink:href` values may contain only `#id`, and SVG paint or marker references
may contain only `url(#id)`. The validator rejects `src`, `srcset`, `data`,
`action`, `formaction`, and `poster` attributes, protocol-relative values, and
all URI schemes in other element or attribute contexts.

Generated HTML includes this exact Content Security Policy:

```text
default-src 'none'; style-src 'unsafe-inline'; img-src 'none';
font-src 'none'; media-src 'none'; connect-src 'none'; frame-src 'none';
form-action 'none'; base-uri 'none'; object-src 'none'
```

## Validator architecture

The validator separates structural guarantees from evidence review:

- Markdown validation parses actual headings rather than accepting keywords
  anywhere in the file.
- HTML validation checks safety, portability, navigation, table accessibility,
  SVG semantics, and document-wide ID integrity.
- Diagram presence is conditional. When SVG exists, the complete SVG contract
  applies.
- A paired Markdown/HTML invocation checks the defined canonical parity facts.
- Validation messages state exactly what was checked and do not imply semantic
  truth beyond those checks.

The command-line interface is:

```text
validate_boomi_docs.py
  [--markdown FILE ...]
  [--html FILE ...]
  [--svg FILE ...]
  [--manifest FILE ...]
  [--strict-generated | --template]
```

Repeated `--markdown`, `--html`, and `--svg` options remain supported. Legacy
invocations without a mode retain version 1 structural behavior. `--template`
allows documented placeholders but applies safety and structural checks.
`--strict-generated` rejects placeholders and applies the complete generated
output contract. One or more manifests require `--strict-generated`, exactly
one Markdown file, at most one HTML file, and exactly one SVG for every diagram
declared across the manifests. SVG filenames and diagram IDs must match.
Invalid option combinations and all validation failures return exit code `1`;
argument syntax errors return `2` through `argparse`.

## Package structure

The package gains:

- `agents/openai.yaml` for Codex display metadata.
- `references/visual-generation-guide.md` for the diagram taxonomy and contract.
- `references/visual-manifest.schema.json` for the versioned visual and parity
  data contract.
- `references/security-and-disclosure.md` for audience and redaction rules.
- `scripts/render_boomi_visual.py` for deterministic manifest-to-SVG rendering.
- `scripts/capture_visual_preview.py` for reproducible optional PNG capture.
- `tests/` with standard-library unit tests and valid/adversarial fixtures.

`SKILL.md` stays concise and routes agents to the focused references. The GitHub
README remains project-facing but no longer duplicates normative details that
belong in the skill or references.

## Sample and preview lifecycle

The fictional sample demonstrates routing fan-out and an error path, identifies
static wiring versus runtime evidence, includes accessible tables and SVG, and
uses the same visual contract as generated reports.

Preview generation uses:

```bash
python3 scripts/capture_visual_preview.py \
  --html references/sample-generated-visual-report.html \
  --output assets/sample-generated-visual-report.png \
  --browser /path/to/chromium
```

The script uses a `1440x1800` viewport, light color mode, device scale factor
`1`, and a full-page capture. It requires the `#primary-diagram` element to be
present and above the initial `1200px` fold, writes a `1440px`-wide PNG, and
records the HTML SHA-256 digest in a sibling metadata file. A freshness check
fails when the source digest and preview metadata differ. Browser capture is an
optional release check when a compatible Chromium binary is available; source
and validator checks remain dependency-free.

## Testing strategy

Committed fixtures and tests preserve the RED phase:

- One independent agent interpreted `retryCount="2"` as two completed retries,
  while another correctly treated runtime semantics as unverified.
- Both agents generated approximately 980–1000 unit-wide SVGs that scale to
  unreadable text on a narrow viewport.
- The current validator accepts an empty SVG, external CSS imports and URLs, and
  an inline `onload` handler.
- The current validator rejects an evidence-honest HTML report with no diagram.

Regression tests cover:

- Valid Markdown, HTML, and paired documents.
- Conditional no-diagram output.
- Empty or inaccessible SVGs.
- Duplicate and broken IDs.
- Unsafe HTML and CSS surfaces.
- Linked images and unsafe URL schemes.
- Unresolved placeholders in strict generated-output mode.
- Table accessibility.
- Fact parity between Markdown and HTML.
- Version and package metadata consistency.

The repository stores the synthetic inventory, XML, exact forward-test prompt,
and evaluator checklist under `tests/fixtures/forward-test/`. Model-based
forward testing remains a manual release evaluation because its output is
nondeterministic. Two clean-context runs must preserve static-wiring language,
avoid retry/runtime claims, use the manifest renderer, identify evidence
states, and pass strict validation. The completion report retains the prompts,
model/runtime identity, artifact paths, and evaluator verdicts.

## Acceptance criteria

The update is complete when:

1. The skill clearly selects Markdown, HTML, standalone and inline SVG, and PNG
   outputs based on the request and evidence.
2. Visual guidance covers context, routing, subprocess, and failure topologies.
3. Every technical diagram is rendered from the versioned manifest and
   identifies its evidence scope and state.
4. Generated SVG and HTML meet the accessibility, responsive, safety, and
   portability contracts, including the measurable `375px` mobile source rules.
5. Evidence conflicts, redactions, and runtime limitations are explicit.
6. The validator rejects every recorded adversarial baseline and accepts the
   evidence-honest no-diagram case.
7. The validator has regression tests that fail before implementation and pass
   afterward.
8. The sample HTML and preview demonstrate the improved visual workflow.
9. Skill metadata and package validation pass.
10. Two fresh-context forward tests produce factually consistent reports without
    inventing retry or runtime semantics.

## Release impact

This is release `2.0.0`. Existing validator invocations remain available in
legacy mode, but the skill changes its evidence model, output contract, package
layout, and strict validation expectations. Those changes meet this repository's
major-version criteria. Release verification must keep `VERSION`, README release
text, package metadata, and the Git tag aligned. `SKILL.md` no longer stores a
version field in frontmatter.
