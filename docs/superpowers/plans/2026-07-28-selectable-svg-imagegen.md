# Selectable SVG and ImageGen Diagrams Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Release Boomi Project Documenter 2.0.0 with manifest-driven deterministic SVG diagrams and an explicitly requested, verified ImageGen PNG alternative.

**Architecture:** A dependency-free Python contract module validates and canonicalizes visual manifests and verification sidecars. The SVG renderer consumes that contract; the strict documentation validator checks generated Markdown, HTML, SVG, PNG embedding, and digest parity, while legacy validation remains compatible. ImageGen itself remains a host-agent workflow: a rasterized canonical SVG is supplied to the runtime tool, and only a digest-matched, semantically reviewed PNG may be delivered.

**Tech Stack:** Python 3 standard library, `unittest`, JSON Schema documents as normative references, HTML/SVG, optional Chromium-compatible browser for preview capture.

## Global Constraints

- ImageGen is explicit opt-in through `visual_mode: "imagegen"`.
- Supported visual modes are exactly `none`, `svg`, and `imagegen`.
- Supported ImageGen placements are exactly `separate`, `embedded`, and `both`.
- Every `svg` or `imagegen` diagram begins with a valid version-1 visual manifest.
- ImageGen receives a rasterized deterministic SVG blueprint, never unconstrained prose alone.
- Every delivered ImageGen PNG requires a passing semantic-review sidecar whose manifest, SVG, and PNG SHA-256 digests match.
- Generation is limited to three attempts and fails closed without silent SVG publication.
- Embedded images are PNG data URLs with decoded size at most 8 MiB.
- No runtime dependencies are added; automated tests make no network or paid ImageGen calls.
- Legacy validator invocations keep version-1 structural behavior.
- `VERSION`, README, skill/display metadata, tests, and `CHANGELOG.md` must agree on `2.0.0`.
- Tagging, publishing, and installed-skill updates are outside implementation scope.

---

### Task 1: Visual contract and schemas

**Files:**
- Create: `scripts/boomi_visual_contract.py`
- Create: `references/visual-manifest.schema.json`
- Create: `references/imagegen-verification.schema.json`
- Create: `tests/test_visual_contract.py`
- Create: `tests/fixtures/manifests/valid-routing.json`
- Create: `tests/fixtures/manifests/invalid-too-many-nodes.json`
- Create: `tests/fixtures/verification/valid-routing.imagegen-verification.json`

**Interfaces:**
- Produces: `ContractError(ValueError)`.
- Produces: `load_manifest(path: Path) -> dict[str, object]`.
- Produces: `validate_manifest(value: object) -> dict[str, object]`.
- Produces: `canonical_json(value: object) -> bytes`.
- Produces: `sha256_bytes(value: bytes) -> str`.
- Produces: `validate_verification(value: object) -> dict[str, object]`.
- The manifest root contains `schema_version`, `project`, `facts`, and `diagrams`.
- Each diagram contains `id`, `type`, `orientation`, `title`, `description`, `evidence_scope`, `nodes`, and `edges`.

- [ ] **Step 1: Write failing contract tests**

```python
class ManifestContractTests(unittest.TestCase):
    def test_valid_manifest_is_normalized(self):
        manifest = contract.load_manifest(FIXTURES / "manifests/valid-routing.json")
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["diagrams"][0]["id"], "order-routing")

    def test_more_than_nine_nodes_is_rejected(self):
        with self.assertRaisesRegex(contract.ContractError, "at most 9 nodes"):
            contract.load_manifest(FIXTURES / "manifests/invalid-too-many-nodes.json")

    def test_canonical_json_is_stable(self):
        left = contract.canonical_json({"é": 1, "a": 2})
        right = contract.canonical_json({"a": 2, "é": 1})
        self.assertEqual(left, right)
        self.assertEqual(left, b'{"a":2,"\\xc3\\xa9":1}')
```

- [ ] **Step 2: Run the focused tests and confirm RED**

Run: `python3 -m unittest tests.test_visual_contract -v`

Expected: import failure for `scripts.boomi_visual_contract`.

- [ ] **Step 3: Implement the contract module and normative schemas**

Use recursive type checks rather than a JSON Schema dependency. Reject unknown
schema versions, non-object roots, duplicate diagram/node/edge IDs, diagram IDs
outside `^[a-z0-9]+(?:-[a-z0-9]+)*$`, unsupported types, missing endpoints,
more than nine nodes, and more than three outgoing decision branches.

Canonical encoding is:

```python
def canonical_json(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")

def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
```

The verification schema requires `schema_version`, `diagram_id`,
`manifest_sha256`, `svg_sha256`, `png_sha256`, `reviewed_at`, `reviewer`,
`attempt_count`, `checks`, and `disposition`. `attempt_count` is 1–3,
all five named checks are `true`, and accepted output uses disposition `pass`.

- [ ] **Step 4: Run contract tests and confirm GREEN**

Run: `python3 -m unittest tests.test_visual_contract -v`

Expected: all tests pass.

- [ ] **Step 5: Commit the visual contract**

```bash
git add scripts/boomi_visual_contract.py references/visual-manifest.schema.json references/imagegen-verification.schema.json tests/test_visual_contract.py tests/fixtures
git commit -m "Add the versioned visual contract"
```

### Task 2: Deterministic accessible SVG renderer

**Files:**
- Create: `scripts/render_boomi_visual.py`
- Create: `tests/test_render_boomi_visual.py`
- Create: `tests/fixtures/rendered/order-routing.svg`

**Interfaces:**
- Consumes: `load_manifest`, `canonical_json`, and `ContractError`.
- Produces: `render_diagram(diagram: dict[str, object]) -> str`.
- Produces CLI: `--manifest FILE (--output FILE | --output-dir DIR)`.
- Supports diagram types `context`, `routing`, `subprocess`, `failure`, and `state`.

- [ ] **Step 1: Write failing renderer tests**

```python
class RendererTests(unittest.TestCase):
    def test_render_is_stable_and_accessible(self):
        diagram = contract.load_manifest(MANIFEST)["diagrams"][0]
        first = renderer.render_diagram(diagram)
        self.assertEqual(first, renderer.render_diagram(diagram))
        self.assertIn('role="img"', first)
        self.assertIn('aria-labelledby="order-routing-title order-routing-desc"', first)
        self.assertIn('viewBox="0 0 960 ', first)
        self.assertNotIn("<script", first)

    def test_cli_writes_one_file_per_sorted_diagram(self):
        result = run_renderer("--manifest", MANIFEST, "--output-dir", output_dir)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(sorted(p.name for p in output_dir.iterdir()), ["order-routing.svg"])
```

- [ ] **Step 2: Run renderer tests and confirm RED**

Run: `python3 -m unittest tests.test_render_boomi_visual -v`

Expected: import failure for `scripts.render_boomi_visual`.

- [ ] **Step 3: Implement the renderer**

Use fixed layout constants, deterministic node ordering, XML escaping through
`html.escape(..., quote=True)`, and IDs prefixed by diagram ID. Horizontal
layout assigns node boxes on a grid; vertical layout transposes coordinates.
Edges render after nodes and use per-diagram arrow markers. Evidence state is
represented by both a CSS class and a visible text legend. Labels are at least
14 px; root SVG has `min-width:720px`, `viewBox`, `<title>`, `<desc>`, and
`aria-labelledby`.

CLI rules:

```python
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--output", type=Path)
group.add_argument("--output-dir", type=Path)
```

`--output` rejects manifests with other than one diagram. `--output-dir`
writes `<diagram-id>.svg` in sorted diagram-ID order.

- [ ] **Step 4: Run renderer tests and update the golden fixture**

Run: `python3 -m unittest tests.test_render_boomi_visual -v`

Expected: all tests pass and the checked-in golden SVG matches exact output.

- [ ] **Step 5: Commit the renderer**

```bash
git add scripts/render_boomi_visual.py tests/test_render_boomi_visual.py tests/fixtures/rendered/order-routing.svg
git commit -m "Render deterministic accessible Boomi diagrams"
```

### Task 3: Strict validator foundation and safe HTML

**Files:**
- Modify: `scripts/validate_boomi_docs.py`
- Create: `tests/test_validate_boomi_docs.py`
- Create: `tests/fixtures/docs/valid.md`
- Create: `tests/fixtures/docs/valid-svg.html`
- Create: `tests/fixtures/docs/valid-no-diagram.html`
- Create: `tests/fixtures/docs/unsafe-script.html`
- Create: `tests/fixtures/docs/unsafe-url.html`

**Interfaces:**
- Consumes: manifest contract and rendered SVG.
- Extends CLI with repeatable `--svg`, repeatable `--manifest`,
  `--strict-generated`, and `--template`.
- Produces `validate_markdown(..., strict: bool)`,
  `validate_html(..., strict: bool)`, and `validate_svg(...)`.
- Legacy mode is selected when neither `--strict-generated` nor `--template`
  is supplied.

- [ ] **Step 1: Characterize legacy behavior and add failing strict tests**

```python
def test_legacy_sample_still_passes(self):
    result = run_validator("--html", REFERENCE_SAMPLE)
    self.assertEqual(result.returncode, 0, result.stderr)

def test_strict_allows_evidence_honest_no_diagram(self):
    result = run_validator("--strict-generated", "--html", VALID_NO_DIAGRAM)
    self.assertEqual(result.returncode, 0, result.stderr)

def test_strict_rejects_active_content(self):
    result = run_validator("--strict-generated", "--html", UNSAFE_SCRIPT)
    self.assertEqual(result.returncode, 1)
    self.assertIn("script elements are not allowed", result.stderr)
```

- [ ] **Step 2: Run validator tests and confirm RED without regressing legacy**

Run: `python3 -m unittest tests.test_validate_boomi_docs -v`

Expected: legacy characterization passes; new strict CLI tests fail.

- [ ] **Step 3: Refactor the HTML parser and add strict safety checks**

Track duplicate IDs, anchors, ARIA references, captions, `scope` attributes,
SVG semantics, scripts, handlers, forms, frames, embeds, objects, meta refresh,
URL-bearing attributes, CSS imports, CSS URLs, placeholders, and exact CSP.
Allow only HTML fragment links and internal SVG `url(#id)`/`href="#id"`
references. In strict mode, diagram absence is valid; when SVG exists, enforce
the complete SVG contract and `.diagram-scroll` source rule.

Parse Markdown headings at line start, and in strict paired mode parse the
canonical `boomi-doc-facts` JSON payload and digest rather than relying on
keywords alone.

- [ ] **Step 4: Run focused and legacy checks**

Run: `python3 -m unittest tests.test_validate_boomi_docs -v`

Run: `python3 scripts/validate_boomi_docs.py --html references/visual-html-guide-template.html`

Run: `python3 scripts/validate_boomi_docs.py --html references/sample-generated-visual-report.html`

Expected: all commands pass; unsafe fixtures fail only inside assertions.

- [ ] **Step 5: Commit strict structural validation**

```bash
git add scripts/validate_boomi_docs.py tests/test_validate_boomi_docs.py tests/fixtures/docs
git commit -m "Add strict standalone document validation"
```

### Task 4: Verified ImageGen PNG contract

**Files:**
- Modify: `scripts/validate_boomi_docs.py`
- Modify: `tests/test_validate_boomi_docs.py`
- Create: `tests/fixtures/imagegen/order-routing.png`
- Create: `tests/fixtures/imagegen/order-routing.imagegen-verification.json`
- Create: `tests/fixtures/docs/valid-imagegen-embedded.html`
- Create: `tests/fixtures/docs/invalid-imagegen-digest.html`

**Interfaces:**
- Adds repeatable CLI option `--imagegen-verification FILE`.
- Valid verification filenames are `<diagram-id>.imagegen-verification.json`.
- Separate PNG lookup is relative to its sidecar unless `--html` contains the
  digest-matched embedded bytes.

- [ ] **Step 1: Write failing PNG verification tests**

```python
def test_verified_embedded_png_passes(self):
    result = run_validator(
        "--strict-generated",
        "--manifest", MANIFEST,
        "--svg", SVG,
        "--html", VALID_IMAGEGEN_HTML,
        "--imagegen-verification", SIDECAR,
    )
    self.assertEqual(result.returncode, 0, result.stderr)

def test_digest_mismatch_fails(self):
    result = run_validator(
        "--strict-generated",
        "--manifest", MANIFEST,
        "--svg", SVG,
        "--html", INVALID_DIGEST_HTML,
        "--imagegen-verification", SIDECAR,
    )
    self.assertEqual(result.returncode, 1)
    self.assertIn("PNG digest", result.stderr)
```

- [ ] **Step 2: Run the focused tests and confirm RED**

Run: `python3 -m unittest tests.test_validate_boomi_docs.ImageGenValidationTests -v`

Expected: parser rejects the unknown option or verification checks are absent.

- [ ] **Step 3: Implement fail-closed ImageGen validation**

Decode only `data:image/png;base64,` with `base64.b64decode(..., validate=True)`.
Reject decoded data over `8 * 1024 * 1024`, invalid PNG signature, missing or
duplicate diagram images, attempts outside 1–3, any false semantic check, any
disposition other than `pass`, and manifest/SVG/PNG digest mismatch. Require
`img-src data:` only for HTML that embeds a verified PNG; retain
`img-src 'none'` otherwise.

- [ ] **Step 4: Run validation tests**

Run: `python3 -m unittest tests.test_validate_boomi_docs -v`

Expected: all tests pass.

- [ ] **Step 5: Commit the ImageGen verification boundary**

```bash
git add scripts/validate_boomi_docs.py tests/test_validate_boomi_docs.py tests/fixtures/imagegen tests/fixtures/docs
git commit -m "Validate reviewed ImageGen diagram output"
```

### Task 5: Blueprint capture and ImageGen agent guide

**Files:**
- Create: `scripts/capture_visual_preview.py`
- Create: `references/imagegen-diagram-guide.md`
- Create: `tests/test_capture_visual_preview.py`

**Interfaces:**
- Produces CLI:
  `capture_visual_preview.py --svg FILE --output FILE --browser FILE`.
- Captures a `1440x900`, scale-factor-1, transparent-background-disabled PNG.
- Guide defines prompt text, comparison checklist, sidecar creation, maximum
  three attempts, and omission behavior.

- [ ] **Step 1: Write failing command-construction tests**

```python
def test_capture_command_is_reproducible(self):
    command = capture.build_browser_command(
        Path("/usr/bin/chromium"), Path("/tmp/input.svg"), Path("/tmp/out.png")
    )
    self.assertIn("--window-size=1440,900", command)
    self.assertIn("--force-device-scale-factor=1", command)
    self.assertIn("--screenshot=/tmp/out.png", command)
    self.assertTrue(command[-1].startswith("file://"))
```

- [ ] **Step 2: Run capture tests and confirm RED**

Run: `python3 -m unittest tests.test_capture_visual_preview -v`

Expected: import failure for `scripts.capture_visual_preview`.

- [ ] **Step 3: Implement capture and write the exact workflow guide**

Validate input suffix/existence, resolve the browser path, construct the fixed
headless command without a shell, run with a 30-second timeout, verify the PNG
signature, and replace output atomically only on success.

The guide must tell the agent to use the captured blueprint as the referenced
image, preserve exact topology/text, inspect the result visually against all
five sidecar check categories, calculate digests, stop after three attempts,
and omit the image when verification fails.

- [ ] **Step 4: Run capture tests**

Run: `python3 -m unittest tests.test_capture_visual_preview -v`

Expected: all tests pass without requiring a browser binary.

- [ ] **Step 5: Commit capture and workflow guidance**

```bash
git add scripts/capture_visual_preview.py references/imagegen-diagram-guide.md tests/test_capture_visual_preview.py
git commit -m "Add the verified ImageGen diagram workflow"
```

### Task 6: Skill, templates, sample, and security guidance

**Files:**
- Modify: `SKILL.md`
- Modify: `references/visual-html-guide-template.html`
- Modify: `references/sample-generated-visual-report.html`
- Modify: `references/evidence-and-verification.md`
- Create: `references/visual-generation-guide.md`
- Create: `references/security-and-disclosure.md`
- Create: `agents/openai.yaml`
- Modify: `README.md`
- Test: `tests/test_validate_boomi_docs.py`

**Interfaces:**
- Skill selects `none`, `svg`, or explicit `imagegen`, then routes to the
  corresponding guide and commands.
- Templates include canonical fact payloads, exact CSP, accessible tables, and
  either inline deterministic SVG or verified PNG placeholders in template
  mode.

- [ ] **Step 1: Add failing repository-content tests**

```python
def test_skill_routes_all_visual_modes(self):
    skill = (ROOT / "SKILL.md").read_text()
    for value in ("none", "svg", "imagegen"):
        self.assertIn(f"`{value}`", skill)
    self.assertIn("only when explicitly requested", skill)

def test_display_metadata_names_the_skill(self):
    metadata = (ROOT / "agents/openai.yaml").read_text()
    self.assertIn("Boomi Project Documenter", metadata)
```

- [ ] **Step 2: Run repository-content tests and confirm RED**

Run: `python3 -m unittest tests.test_validate_boomi_docs.RepositoryContentTests -v`

Expected: missing guide/metadata and visual-mode assertions fail.

- [ ] **Step 3: Update skill and reference content**

Keep `SKILL.md` concise. Route evidence classification to the existing evidence
guide, manifest/SVG behavior to `visual-generation-guide.md`, ImageGen
invocation and review to `imagegen-diagram-guide.md`, and audience/redaction to
`security-and-disclosure.md`. Remove the version field from skill frontmatter
per the 2.0 design and place display metadata in `agents/openai.yaml`.

Update the HTML template and fictional sample to satisfy strict CSP,
accessibility, scrolling, facts, and diagram semantics. Do not include a
purportedly generated sample PNG without a valid sidecar.

- [ ] **Step 4: Validate references and content**

Run: `python3 -m unittest tests.test_validate_boomi_docs -v`

Run: `python3 scripts/validate_boomi_docs.py --template --html references/visual-html-guide-template.html`

Run: `python3 scripts/validate_boomi_docs.py --strict-generated --html references/sample-generated-visual-report.html`

Expected: all commands pass.

- [ ] **Step 5: Commit skill and references**

```bash
git add SKILL.md README.md agents references tests/test_validate_boomi_docs.py
git commit -m "Document selectable evidence-driven diagrams"
```

### Task 7: Version 2.0.0 release alignment and full verification

**Files:**
- Modify: `VERSION`
- Modify: `README.md`
- Create: `CHANGELOG.md`
- Modify: `tests/test_validate_boomi_docs.py`

**Interfaces:**
- `VERSION` contains exactly `2.0.0`.
- README current version is `2.0.0`.
- `CHANGELOG.md` has a dated `2.0.0` entry covering manifest SVG, optional
  ImageGen, verification, strict validation, and compatibility.

- [ ] **Step 1: Add a failing version-alignment test**

```python
def test_release_version_is_aligned(self):
    version = (ROOT / "VERSION").read_text().strip()
    self.assertEqual(version, "2.0.0")
    self.assertIn("Current version: `2.0.0`", (ROOT / "README.md").read_text())
    self.assertIn("## 2.0.0 - 2026-07-28", (ROOT / "CHANGELOG.md").read_text())
```

- [ ] **Step 2: Run the version test and confirm RED**

Run: `python3 -m unittest tests.test_validate_boomi_docs.RepositoryContentTests.test_release_version_is_aligned -v`

Expected: failure because `VERSION` is `1.0.2` and `CHANGELOG.md` is absent.

- [ ] **Step 3: Align version and changelog**

Set `VERSION` to `2.0.0`, update all README release references and layout
examples, and add the dated changelog entry. Do not create or push a tag.

- [ ] **Step 4: Run complete verification**

Run: `python3 -m unittest discover -s tests -v`

Run: `python3 -m compileall -q scripts tests`

Run: `python3 scripts/render_boomi_visual.py --manifest tests/fixtures/manifests/valid-routing.json --output /tmp/order-routing.svg`

Run: `python3 scripts/validate_boomi_docs.py --html references/sample-generated-visual-report.html`

Run: `python3 scripts/validate_boomi_docs.py --template --html references/visual-html-guide-template.html`

Run: `python3 /home/jburmeister/.codex/skills/.system/skill-creator/scripts/quick_validate.py .`

Expected: all tests and commands pass. If the external skill validator is not
installed at that exact path, record that command as an environmental
validation gap rather than a pass.

- [ ] **Step 5: Inspect scope and commit release alignment**

Run: `git diff --check`

Run: `git status --short`

Run: `git diff --stat HEAD`

Confirm only plan-owned files changed, then:

```bash
git add VERSION README.md CHANGELOG.md tests/test_validate_boomi_docs.py
git commit -m "Release Boomi Project Documenter 2.0.0"
```

### Task 8: Exact-revision completion audit

**Files:**
- No planned changes.

**Interfaces:**
- Verifies the committed revision rather than the pre-commit worktree.

- [ ] **Step 1: Record the exact revision and clean-tree state**

Run: `git rev-parse HEAD`

Run: `git status --short`

Expected: a commit hash and no output from `git status --short`.

- [ ] **Step 2: Re-run the full committed-revision test suite**

Run: `python3 -m unittest discover -s tests -v`

Run: `python3 -m compileall -q scripts tests`

Expected: all tests pass.

- [ ] **Step 3: Review release diff and exclusions**

Run: `git diff 66500ed..HEAD --stat`

Run: `git log --oneline 66500ed..HEAD`

Confirm no tag, publish, deployment, or installed-skill mutation occurred.

- [ ] **Step 4: Report evidence and remaining manual checks**

Report the exact tested revision, test counts, validator commands, version
alignment, and any unavailable browser/ImageGen manual release evaluation.
State explicitly that fixed fixtures validate the workflow but do not replace
a fresh paid ImageGen release evaluation.
