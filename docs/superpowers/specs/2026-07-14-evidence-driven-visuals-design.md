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

Automatic extraction of arbitrary Boomi XML into a fully laid-out diagram is
outside this release. Agents continue to interpret project evidence, but they
must express the result through a constrained visual contract that can be
validated.

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
- Create an SVG only when current evidence establishes a useful topology,
  relationship, decision, or state transition.
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

Each diagram declares:

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

## SVG and responsive behavior

Every SVG includes a `viewBox`, `role="img"`, unique `<title>` and `<desc>` IDs,
and a valid `aria-labelledby` reference. Marker, gradient, filter, title, and
description IDs are globally unique within the HTML document.

Wide diagrams appear in an overflow container with a minimum readable width.
Mobile layouts may use a vertical SVG when that improves comprehension. Labels
must not be scaled below a readable size. Complex diagrams are split when they
exceed approximately nine primary nodes, three major branches, or one screen of
readable content.

Tables include captions and explicit header scopes. Navigation exposes visible
keyboard focus. Smooth scrolling is disabled for reduced-motion preferences.
Print styles avoid splitting diagrams and critical tables when practical.

## Standalone HTML safety

Visual reports contain embedded CSS and inline SVG only. The validator rejects:

- Scripts, inline event-handler attributes, forms, frames, embeds, and objects.
- Meta refresh and active navigation directives.
- External or local linked images.
- External stylesheets, CSS imports, and CSS URLs.
- Unsafe URL schemes.
- Duplicate IDs, broken local anchors, and broken ARIA references.
- Unresolved template placeholders in generated output.

A strict Content Security Policy is included where it does not undermine the
standalone format.

## Validator architecture

The validator separates structural guarantees from evidence review:

- Markdown validation parses actual headings rather than accepting keywords
  anywhere in the file.
- HTML validation checks safety, portability, navigation, table accessibility,
  SVG semantics, and document-wide ID integrity.
- Diagram presence is conditional. When SVG exists, the complete SVG contract
  applies.
- A paired Markdown/HTML invocation checks selected canonical facts for parity.
- Validation messages state exactly what was checked and do not imply semantic
  truth beyond those checks.

The command-line interface remains backward compatible for `--markdown` and
`--html`. New strict generated-output and parity checks use explicit options so
the placeholder reference templates can still be linted as templates.

## Package structure

The package gains:

- `agents/openai.yaml` for Codex display metadata.
- `references/visual-generation-guide.md` for the diagram taxonomy and contract.
- `references/security-and-disclosure.md` for audience and redaction rules.
- `tests/` with standard-library unit tests and valid/adversarial fixtures.

`SKILL.md` stays concise and routes agents to the focused references. The GitHub
README remains project-facing but no longer duplicates normative details that
belong in the skill or references.

## Sample and preview lifecycle

The fictional sample demonstrates routing fan-out and an error path, identifies
static wiring versus runtime evidence, includes accessible tables and SVG, and
uses the same visual contract as generated reports.

Preview generation documents a fixed viewport and headless-browser command.
The preview must include the primary diagram. Browser rendering remains an
optional release check when a compatible browser is available; source and
validator checks remain dependency-free.

## Testing strategy

The existing baseline is the RED phase:

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

Forward tests repeat the branching and error-path fixture with the revised
skill.
Success requires consistent static-wiring language, readable responsive SVG
handling, evidence-state labeling, safe HTML, and passing strict validation.

## Acceptance criteria

The update is complete when:

1. The skill clearly selects Markdown, HTML, SVG, and PNG outputs based on the
   request and evidence.
2. Visual guidance covers context, routing, subprocess, and failure topologies.
3. Every technical diagram identifies its evidence scope and state.
4. Generated SVG and HTML meet the accessibility, responsive, safety, and
   portability contracts.
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

This is a backward-compatible feature release. Existing `--markdown` and
`--html` invocations continue to work, while stricter validation is available
for generated outputs. The release should increment the minor version because
it adds workflow guidance, references, validation behavior, metadata, and test
coverage without changing the skill's core purpose.
