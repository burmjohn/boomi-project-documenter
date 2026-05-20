---
name: boomi-project-documenter
description: >-
  Create or refresh evidence-backed documentation for Boomi integration
  projects. Use when an AI agent needs to inspect Boomi component XML, API
  inventory exports, process folders, connector settings, maps, profiles,
  cross references, deployment or execution evidence, and existing docs to
  produce technical Markdown, supporting docs, standalone visual HTML guides,
  evidence notes, stale-claim scans, or completion reports for Boomi projects.
metadata:
  version: 1.0.1
---

# Boomi Project Documenter

## Outcome

Produce Boomi project documentation that is technically reviewable and
stakeholder-readable. Treat Markdown as the source of truth, and create
standalone visual HTML only as a companion that summarizes the same evidence.

This skill complements Boomi Companion:
`https://github.com/OfficialBoomi/boomi-companion`. Use Boomi Companion for
Boomi-oriented development tooling, skills, and companion workflows. Use this
skill when the task is specifically to document a Boomi project from local
evidence.

## Workflow

1. Establish the evidence set before writing:
   - Existing Markdown and HTML docs in the workspace.
   - Current Boomi component XML, usually under `active-development/`.
   - Latest API inventory exports and any previous baseline inventory.
   - Pull logs, sync-state files, deployment records, execution logs, and test
     results when present.
2. Separate fact classes:
   - Current facts proven by current XML, current inventory, deployment
     records, or execution evidence.
   - Historical notes from old pulls, previous docs, old test runs, and stale
     assets.
   - Inferences that are likely but not directly proven.
   - Open risks, unresolved dependencies, and verification gaps.
3. Generate or refresh Markdown first. Use
   `references/markdown-documentation-template.md` for the main structure.
4. Generate standalone visual HTML after the Markdown is stable. Use
   `references/visual-html-guide-template.html` for structure, navigation,
   responsive CSS, print behavior, and diagram style.
5. Verify before completion. Use `references/evidence-and-verification.md` and
   the scripts in `scripts/`.
6. Report changed files, evidence used, verification checks, and remaining risks.

## Fact Rules

Preserve exact evidence values when they matter:

- Component names, IDs, versions, folder paths, and modified dates.
- Connection names, operation names, profile names, and map names.
- Cross-reference names, property names, and exact error text.

Use exact dates such as `May 20, 2026`; avoid `today`, `latest`, `recent`, and
similar relative wording unless the date is also stated.

Do not claim a component is deployed, active at runtime, production-ready, or
unused unless direct evidence proves it. Do not claim there are no sandbox,
test, deprecated, or legacy dependencies unless the current reference check
proves that.

Label old failures and old dependencies as historical when current evidence
shows they are no longer active blockers. State unresolved dependencies plainly,
including the exact component or reference that keeps the risk open.

Avoid generic claims such as "fully automated", "complete", "secure", or "no
risk" without evidence.

## Markdown Requirements

Use the main Markdown document for the complete technical briefing. Keep it
direct and implementation-focused:

- Start with purpose and scope.
- Name the evidence basis and exclusions.
- Include a current baseline with key component versions and inventory counts.
- Explain the end-to-end flow in runtime order.
- Use tables for component baselines, inventory counts, risks, validation
  status, and next steps.
- Use numbered lists for process flows and verification sequences.
- Use code formatting for component names, paths, properties, operations, table
  names, and exact errors.
- Keep historical notes near the topic they clarify.

For focused topics, add supporting Markdown pages under `docs/` only when a
topic would make the main document hard to scan.

## Visual HTML Requirements

Create a portable HTML companion only after the Markdown facts are stable:

- Use one standalone `.html` file with embedded CSS.
- Include a left navigation rail with working anchors.
- Include a hero section with project name, purpose, evidence date, and status.
- Include status cards for versions, inventory counts, risks, confirmations, or
  verification outcomes.
- Use inline SVG diagrams for real system behavior: process flow, routing,
  external interactions, response handling, or error paths.
- Use tables for baselines, risks, and next steps.
- Make the page responsive and print-friendly.
- Avoid external scripts, external CSS, external images, stock imagery, and
  decorative filler.
- Ensure every visual explains a real behavior or evidence-backed decision.

## Bundled References

- Read `references/markdown-documentation-template.md` before drafting the main
  Markdown document.
- Read `references/visual-html-guide-template.html` before creating a
  standalone visual guide.
- Read `references/evidence-and-verification.md` when gathering evidence,
  comparing inventories, validating claims, or writing completion reports.
- Read `references/example-prompts-and-reports.md` when the user asks for a
  reusable prompt, evidence note, or final completion summary.
- Read `references/sample-generated-visual-report.html` when the user needs an
  example of a completed fictional visual report.

## Scripts

- Run `scripts/validate_boomi_docs.py --markdown <main.md> --html <guide.html>`
  to check basic Markdown/HTML structure, standalone HTML constraints,
  navigation anchors, and required visual elements.

## Completion Report

End with evidence, not broad assurance:

- Files created or updated.
- Current inventory or XML evidence used.
- Key current versions, counts, and changed components when known.
- Remaining risks, unsupported claims avoided, and verification gaps.
- Checks that passed and checks that could not run.
