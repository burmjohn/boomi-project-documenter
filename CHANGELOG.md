# Changelog

This file records user-visible changes to Boomi Project Documenter.

## 2.0.0 - 2026-07-28

Version 2.0.0 replaces unconstrained inline-diagram authoring with a versioned
visual contract and adds an explicitly requested ImageGen alternative.

### Added

- Versioned visual-manifest and ImageGen-verification schemas.
- Dependency-free manifest validation and canonical SHA-256 encoding.
- Deterministic, accessible SVG rendering for five diagram patterns.
- Reproducible SVG blueprint capture for host-runtime ImageGen tools.
- Explicit `none`, `svg`, and `imagegen` visual-mode guidance.
- Five-category semantic review and digest-matched verification sidecars for
  generated PNGs.
- Safe separate, embedded, and combined PNG placement with an 8 MiB decoded
  embedding limit.
- Strict standalone HTML, SVG, manifest, fact-parity, and ImageGen validation.
- Security, disclosure, visual-generation, and ImageGen workflow references.
- Codex display metadata and a standard-library regression suite.

### Changed

- ImageGen is opt-in and never runs merely because a visual companion exists.
- Markdown remains the documentation source of truth, while the visual manifest
  becomes the source of technical diagram content.
- Standalone HTML uses an exact Content Security Policy and accessible,
  responsive diagram and table contracts.
- Skill frontmatter no longer carries a product version field.

### Compatibility

Legacy validator invocations without `--strict-generated` or `--template`
retain version 1 structural checks. Version 2 generated artifacts use strict
mode and include their manifest, Markdown, SVG files, and any ImageGen
verification sidecars.
