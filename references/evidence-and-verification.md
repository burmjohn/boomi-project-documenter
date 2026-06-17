# Evidence and Verification Guide

Use this guide when gathering Boomi evidence, refreshing docs, or verifying claims.

## Evidence Order

Prefer current, local, inspectable evidence:

1. Current Boomi component XML under the active development folder.
2. Current API inventory export.
3. Previous baseline inventory export for diff counts.
4. Sync-state records, pull logs, and promotion logs.
5. Deployment records and execution logs.
6. Existing Markdown or HTML docs.
7. Older pull folders and generated artifacts.

Treat older folders and older generated docs as historical unless current
inventory or current XML points to the same component IDs and versions.

## Inventory Comparison

When two inventory files exist:

- Compare component IDs, names, types, versions, folder paths, and modified
  dates.
- Record added, removed, and changed components.
- Separate account-wide inventory counts from the documented runtime flow.
- Avoid claiming a changed component was pulled unless a pull log, local XML, or
  sync-state record proves it.

Suggested evidence note:

```markdown
## Evidence used

- Current inventory: `[path]`, `[count]` records, exported `[date]`.
- Previous baseline: `[path]`, `[count]` records, exported `[date]`.
- Diff result: `[added]` added, `[removed]` removed, `[changed]` changed.
- Current XML inspected: `[folder or file list]`.
- Deployment or execution evidence: `[path or "not found"]`.
```

## XML Inspection Checklist

Check the XML for:

- Component `id`, `name`, `type`, `version`, folder path, and current-version
  markers.
- Process call shapes and referenced component IDs.
- Connector settings and connector actions.
- Map, profile, document cache, cross-reference, route, and process property
  references.
- Error paths, catch branches, notification processes, and response handlers.
- Environment extensions and dynamic document or process properties.
- Sandbox, test, deprecated, archived, or legacy references.

Do not rely on component names alone when IDs are available.

## Claim Classification

Use these labels in notes or tables when helpful:

- Current fact: Supported by current XML, current inventory, deployment
  evidence, or execution evidence.
- Historical note: Supported by older docs, old pulls, old generated assets, or
  old test logs.
- Inference: Likely based on wiring or naming, but not directly proven.
- Open risk: A dependency, reference, test gap, or unsupported claim that needs
  follow-up.
- Not found: Searched for evidence and did not find it. This is not proof of
  absence unless the search scope is complete.

## Stale-Claim Scans

Adapt search patterns to the project. Scan for:

- Old inventory filenames and old export dates.
- Old component versions.
- Claims such as `current`, `latest`, `deployed`, `runtime`, `production`,
  `complete`, `no active`, and `zero`.
- Sandbox, test, deprecated, archive, legacy, and temporary folder names.
- Old error text that may have been copied forward.
- Old route keys, connection names, operation names, table names, and endpoint names.

Example:

```bash
rg -n \
  'component_search_|runtime|deployed|current|latest|historical|sandbox' \
  README.md docs '*.md' '*.html'
rg -n \
  'deprecated|legacy|temporary|zero|no active|complete|production' \
  README.md docs '*.md' '*.html'
```

## Markdown Verification

Verify:

- The title and purpose match the documented project.
- The high-level overview follows the canonical Documentation Levels taxonomy
  and missing-evidence fallback rule from `SKILL.md`.
- Audience, purpose, system boundary, status, and decisions are stated without
  unsupported business or runtime claims.
- Scope names the evidence basis and exclusions.
- Inventory counts and component versions match the current evidence.
- End-to-end flow follows current process wiring.
- Unsupported deployment or runtime claims are removed or qualified.
- Risks identify exact components, operations, maps, profiles, or references.
- Historical notes are labeled.
- Markdown and HTML agree on key versions, dates, counts, risks, and next
  steps.

## HTML Verification

Verify:

- The file is standalone: embedded CSS, no external scripts, no external CSS,
  and no external images.
- Navigation links resolve to existing IDs.
- Diagrams are inline `<svg>` elements and explain real system behavior.
- Tables are readable on small screens.
- Print CSS is present.
- The hero and status cards match Markdown facts.
- No decorative filler or unsupported visuals are present.

## Completion Report Pattern

```markdown
## Completed

Updated:

- `[file]` - `[what changed]`
- `[file]` - `[what changed]`

Evidence:

- Current inventory: `[path]`, `[count]` records, `[date]`.
- XML inspected: `[paths]`.
- Changed components: `[count]` changed, `[count]` added, `[count]` removed.

Verification:

- `[check]` passed.
- `[check]` passed.
- `[check]` could not run because `[reason]`.

Remaining risk:

- `[specific risk and next check]`.
```
