# Markdown Documentation Template

Use this template for the primary technical Markdown document. Replace
bracketed values with facts from current Boomi evidence. Remove sections that
are not supported by evidence.

## Title and Purpose

```markdown
# [Project Name] Boomi project documentation

This document describes the Boomi integration components under `[project root or folder]`.
It explains the current evidence basis, the main runtime flow, supporting services,
known risks, and recommended next steps.
```

## High-Level Overview

Use the canonical Documentation Levels taxonomy from `SKILL.md`. Start with a
stakeholder-readable summary before detailed component tables, then name the
audience levels and the use case each level can act on:

```markdown
## High-level overview

`[Project Name]` supports `[business or operational capability]` by moving
`[source document/event]` from `[source system role]` through Boomi to
`[target system role]`.

Current evidence shows `[proven current status]`. The main open questions are
`[risk or dependency]`, `[runtime/deployment gap]`, and `[validation gap]`.

| Documentation level | Use case for this project | Evidence basis |
| --- | --- | --- |
| `[level from SKILL.md]` | `[decision or task supported]` | `[evidence notes]` |
```

Keep the overview factual and apply the missing-evidence fallback rule from
`SKILL.md`.

## Scope and Evidence Basis

Include:

- Workspace path or evidence root.
- Current inventory export path and record count.
- Previous baseline inventory path when comparing changes.
- Component XML folders inspected.
- Deployment, execution, or test evidence inspected.
- Explicit exclusions, such as archived folders, sandbox folders, old pulls, or
  unrelated component branches.

Example:

```markdown
## Scope

The documentation covers current components under `[Boomi folder path]`.
The evidence basis is `[inventory path]`, which returned `[count]` current
component records on `[date]`, plus component XML under `[local XML root]`.
Older pull folders and generated artifacts are historical unless the current
inventory or sync-state evidence points to them.
```

## Current Baseline

Use tables for component and inventory facts:

```markdown
## Current component baseline

| Component | Type | Current version | Folder path | Last modified |
| --- | --- | ---: | --- | --- |
| `[component name]` | Process | `[version]` | `[folder path]` | `[timestamp]` |
| `[component name]` | Map | `[version]` | `[folder path]` | `[timestamp]` |

| Component type | Count |
| --- | ---: |
| Processes | `[count]` |
| Maps | `[count]` |
| Connector settings | `[count]` |
| Connector actions | `[count]` |
| Profiles | `[count]` |
| Cross references | `[count]` |
```

State inventory counts as inventory context. Do not imply every component
participates in the documented runtime path unless wiring evidence proves it.

## End-to-End Flow

Write the runtime sequence in the order it runs:

```markdown
## End-to-end process flow

1. `[entry process]` receives or retrieves `[source document/event]`.
2. The entry process calls `[core orchestration process]`.
3. `[normalization step]` prepares the source payload for mapping.
4. `[map or transform]` converts the document into `[canonical or target model]`.
5. `[routing or decision component]` selects `[route or destination]` using
   `[property or condition]`.
6. `[delivery component]` sends the result to `[destination type]`.
7. `[response handler]` records status, errors, acknowledgements, or audit output.
8. `[notification or framework component]` handles errors or operational alerts.
```

## Process Sections

Use one section per major process or reusable service:

```markdown
## Main entry process

`[component name]` is the entry point for `[event/source]`.
It uses `[connection]` and `[operation]` version `[version]`.

Key behavior:

- `[proven behavior]`
- `[proven behavior]`
- `[historical note or risk if relevant]`
```

Recommended sections:

- High-level overview.
- System boundary and connected system roles.
- Main entry process.
- Core orchestration process.
- Routing or decision model.
- Data conversion and mapping.
- Delivery and response handling.
- Shared connectors, libraries, and framework services.
- Data model summary.
- Current implementation status.
- Dependency, sandbox, deployment, and runtime status.
- Recommended next steps.

## Risk and Status Tables

Use explicit status language:

```markdown
## Dependency and deployment status

| Area | Status | Evidence | Risk |
| --- | --- | --- | --- |
| `[area]` | Proven current | `[file or inventory row]` | None identified from current evidence |
| `[area]` | Open risk | `[component and version]` | `[specific unresolved issue]` |
| `[area]` | Historical only | `[old run or old pull]` | Do not treat as current blocker |
```

## Recommended Next Steps

Make each next step testable:

```markdown
## Recommended next steps

1. Confirm `[route or dependency]` is intended for `[environment/use]`.
2. Test `[map/process]` with `[representative input]` and record output
   evidence.
3. Verify `[connector or response handler]` writes expected status to
   `[target system]`.
4. Replace or retire `[open dependency]` before claiming production readiness.
5. Run an end-to-end execution from `[source]` through
   `[final status/audit target]`.
```

## Language Guardrails

Use:

- "Current XML shows..."
- "The current inventory contains..."
- "The current process references..."
- "Historical evidence shows..."
- "No current evidence was found for..."

Avoid:

- "The project is live" without deployment or execution evidence.
- "No dependencies remain" without a current reference scan.
- "Fully complete" without passing verification.
- Relative date claims without naming the exact inventory and date.
