# Example Prompts and Reports

Use these examples as generic patterns. Replace bracketed values with
project-specific facts from the workspace.

## Documentation Refresh Prompt

```text
Use $boomi-project-documenter to create or refresh Markdown and standalone
visual HTML documentation for the Boomi project in [workspace path].

Requirements:
- Read existing docs, current Boomi component XML, and the current inventory
  export with its exact path and export date before writing.
- Follow the canonical Documentation Levels taxonomy and missing-evidence
  fallback rule from `SKILL.md`.
- Explain the integration purpose, connected system roles, current status, and
  open decisions before listing component details, only as supported by current
  evidence.
- Compare the current inventory with the prior baseline when both are available.
- Preserve exact component names, IDs, versions, folder paths, modified dates,
  operation names, profile names, and property names.
- Separate current facts from historical notes, unsupported inferences, and
  open risks.
- Do not claim deployment, runtime activity, production readiness, or zero
  dependency without direct evidence.
- Update the main Markdown documentation and any focused supporting docs that
  are affected by the current evidence.
- Create a standalone visual HTML guide with embedded CSS only, working
  navigation, status cards, tables, and inline SVG diagrams.
- Verify that Markdown and HTML agree on key versions, counts, dates, risks,
  and next steps.
- Run stale-claim scans and record the verification checks performed.
```

## Evidence Note

```markdown
## Evidence used

- Current inventory: `active-development/inventories/[inventory].json`,
  `[count]` records, exported `[Month DD, YYYY]`.
- Previous baseline: `active-development/inventories/[previous].json`,
  `[count]` records, exported `[Month DD, YYYY]`.
- Diff result: `[added]` added, `[removed]` removed, `[changed]` changed.
- Current XML inspected: `active-development/process/`,
  `active-development/map/`, `active-development/connector-settings/`,
  `active-development/connector-action/`, and `[other folders]`.
- Execution evidence: `[path or "none found in workspace"]`.

## Verification checks

- Parsed key XML files for component names, IDs, versions, and references.
- Checked that Markdown and HTML agree on the current inventory, versions, risk
  count, and next steps.
- Checked that HTML navigation anchors resolve.
- Checked that the HTML has embedded CSS and no external scripts, stylesheets,
  or images.
- Ran stale-claim scans for old inventory names, old versions, unsupported
  runtime claims, and historical errors.
```

## Completion Report

```markdown
Completed the Boomi documentation refresh.

Updated:

- `[main documentation].md` - refreshed executive summary, operational runtime
  narrative, implementation baseline, system boundary, risks, and next steps.
- `docs/[focused topic].md` - added focused troubleshooting or dependency
  details.
- `[visual guide].html` - created a standalone visual guide with embedded CSS,
  working navigation, status cards, tables, and inline SVG diagrams.

Evidence:

- Current inventory: `[path]`, `[count]` records, exported `[Month DD, YYYY]`.
- Inventory comparison: `[added]` added, `[removed]` removed, and `[changed]`
  changed.
- XML inspected: `[paths]`.

Verification:

- `scripts/validate_boomi_docs.py --markdown [main].md --html [guide].html`
  passed.
- Stale-claim scan passed for old inventory names, old versions, unsupported
  runtime claims, and historical errors.
- `git diff --check` passed.

Remaining risk:

- `[specific component/reference/test gap]` still needs `[specific follow-up]`
  before claiming `[deployment, runtime, production, or dependency status]`.
```

## Synthetic Generated Examples

The following examples are fully fictional. They show the level of specificity
expected in generated output without using any organization-specific project
details.

### Completed Evidence Note

```markdown
## Evidence used

- Current inventory: `active-development/inventories/component_inventory_20260520.json`,
  42 records, exported May 20, 2026.
- Previous baseline: `active-development/inventories/component_inventory_20260518.json`,
  39 records, exported May 18, 2026.
- Diff result: 3 added, 0 removed, and 4 changed.
- Current XML inspected: `active-development/process/`,
  `active-development/map/`, `active-development/profile.json/`,
  `active-development/connector-settings/`, and
  `active-development/connector-action/`.
- Execution evidence: no execution logs were present in the workspace.

## Verification checks

- Parsed XML for `MAIN - Receive Order Status` version 12,
  `SUB - Normalize Status Payload` version 7, and
  `MAP - Status JSON to Canonical` version 5.
- Confirmed the visual guide and Markdown baseline both state 42 current
  inventory records and 4 changed components.
- Confirmed the HTML guide has embedded CSS, working section anchors, tables,
  and inline SVG diagrams.
- Confirmed no deployment or runtime activity claim appears without execution
  evidence.
```

### Completed Documentation Refresh Report

```markdown
Completed the Boomi documentation refresh for `Sample Order Status Hub`.

Updated:

- `sample-order-status-documentation.md` - added executive summary, operational
  process flow, implementation baseline, system boundary, risk summary, and next
  steps.
- `docs/sample-order-status-validation.md` - added the focused verification
  notes for component XML, inventory comparison, and HTML checks.
- `sample-order-status-visual.html` - created a standalone visual guide with
  embedded CSS, status cards, component tables, and inline SVG diagrams.

Evidence:

- Current inventory: `active-development/inventories/component_inventory_20260520.json`,
  42 records, exported May 20, 2026.
- Inventory comparison: 3 added, 0 removed, and 4 changed.
- XML inspected: `active-development/process/`,
  `active-development/map/`, `active-development/profile.json/`, and
  `active-development/connector-action/`.

Verification:

- `validate_boomi_docs.py --markdown sample-order-status-documentation.md --html sample-order-status-visual.html`
  passed.
- Manual stale-claim scan found no old inventory filenames or old component
  versions.
- `git diff --check` passed.

Remaining risk:

- No execution logs were available, so the documentation does not claim runtime
  activity or deployment status.
```

### Completed Risk and Status Summary

| Area | Status | Evidence | Next check |
| --- | --- | --- | --- |
| Component inventory | Current fact | `component_inventory_20260520.json` reports 42 records. | Re-export inventory before the next documentation refresh. |
| Main process flow | Current fact | `MAIN - Receive Order Status` version 12 calls `SUB - Normalize Status Payload`. | Confirm execution behavior with a test run. |
| Mapping behavior | Current fact | `MAP - Status JSON to Canonical` version 5 maps source status fields into the canonical profile. | Validate with representative status payloads. |
| Delivery path | Inference | `SUB - Send Status Update` references a generic HTTP connector action. | Review connector action XML and execution logs before claiming runtime delivery. |
| Runtime status | Not found | No execution logs or deployment records were present. | Run an environment-specific execution check. |

## Supporting Docs to Add Only When Needed

Create supporting docs under `docs/` when the main document would become too
dense:

- `docs/dependency-status.md` for sandbox, deprecated, test, or legacy
  references.
- `docs/connector-and-environment-status.md` for connector settings,
  environment extensions, and deployment-specific checks.
- `docs/data-model-and-mapping.md` for source, canonical, and target profiles
  or map behavior.
- `docs/operational-validation.md` for execution logs, test runs, and evidence
  gaps.

Do not create supporting docs just to mirror the main document.
