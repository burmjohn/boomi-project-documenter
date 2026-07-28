from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_boomi_docs.py"
DOCS = ROOT / "tests" / "fixtures" / "docs"
MANIFEST = ROOT / "tests" / "fixtures" / "manifests" / "valid-routing.json"
SVG = ROOT / "tests" / "fixtures" / "rendered" / "order-routing.svg"
VALID_MARKDOWN = DOCS / "valid.md"
VALID_FACTS_HTML = DOCS / "valid-facts.html"
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def run_validator(*args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), *(str(arg) for arg in args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class LegacyValidationTests(unittest.TestCase):
    def test_reference_sample_still_passes(self) -> None:
        result = run_validator(
            "--html", ROOT / "references" / "sample-generated-visual-report.html"
        )

        self.assertEqual(result.returncode, 0, result.stderr)


class StrictHtmlValidationTests(unittest.TestCase):
    def test_evidence_honest_no_diagram_passes(self) -> None:
        result = run_validator(
            "--strict-generated", "--html", DOCS / "valid-no-diagram.html"
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_accessible_inline_svg_passes(self) -> None:
        result = run_validator(
            "--strict-generated", "--html", DOCS / "valid-svg.html"
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_active_script_is_rejected(self) -> None:
        result = run_validator(
            "--strict-generated", "--html", DOCS / "unsafe-script.html"
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("script elements are not allowed", result.stderr)

    def test_remote_and_css_urls_are_rejected(self) -> None:
        result = run_validator(
            "--strict-generated", "--html", DOCS / "unsafe-url.html"
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("external or local URL is not allowed", result.stderr)
        self.assertIn("CSS url() is not allowed", result.stderr)

    def test_empty_svg_is_rejected(self) -> None:
        result = run_validator(
            "--strict-generated", "--html", DOCS / "empty-svg.html"
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("SVG must contain visual elements", result.stderr)

    def test_table_requires_caption_and_scoped_headers(self) -> None:
        result = run_validator(
            "--strict-generated", "--html", DOCS / "inaccessible-table.html"
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("table requires a caption", result.stderr)
        self.assertIn("table header requires scope", result.stderr)

    def test_template_mode_allows_documented_placeholders(self) -> None:
        result = run_validator("--template", "--html", DOCS / "template.html")

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_strict_mode_rejects_placeholders(self) -> None:
        result = run_validator(
            "--strict-generated", "--html", DOCS / "template.html"
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("unresolved template placeholder", result.stderr)


class StrictCliTests(unittest.TestCase):
    def test_modes_are_mutually_exclusive(self) -> None:
        result = run_validator(
            "--strict-generated",
            "--template",
            "--html",
            DOCS / "valid-no-diagram.html",
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("not allowed with argument", result.stderr)

    def test_manifest_requires_exactly_one_markdown_file(self) -> None:
        result = run_validator(
            "--strict-generated",
            "--manifest",
            MANIFEST,
            "--svg",
            SVG,
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("exactly one Markdown file", result.stderr)


class FactParityTests(unittest.TestCase):
    def test_manifest_markdown_and_html_facts_match(self) -> None:
        result = run_validator(
            "--strict-generated",
            "--manifest",
            MANIFEST,
            "--markdown",
            VALID_MARKDOWN,
            "--html",
            VALID_FACTS_HTML,
            "--svg",
            SVG,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_html_fact_change_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            invalid_html = Path(temporary) / "invalid-facts.html"
            invalid_html.write_text(
                VALID_FACTS_HTML.read_text(encoding="utf-8").replace(
                    '"risk_counts":{"open":1}', '"risk_counts":{"open":2}'
                ),
                encoding="utf-8",
            )

            result = run_validator(
                "--strict-generated",
                "--manifest",
                MANIFEST,
                "--markdown",
                VALID_MARKDOWN,
                "--html",
                invalid_html,
                "--svg",
                SVG,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("HTML fact digest is invalid", result.stderr)


class RepositoryReleaseTests(unittest.TestCase):
    def test_release_version_is_aligned(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

        self.assertEqual(version, "2.0.0")
        self.assertIn(
            "Current version: `2.0.0`",
            (ROOT / "README.md").read_text(encoding="utf-8"),
        )
        changelog = ROOT / "CHANGELOG.md"
        self.assertTrue(changelog.is_file())
        self.assertIn(
            "## 2.0.0 - 2026-07-28",
            changelog.read_text(encoding="utf-8"),
        )


class ImageGenValidationTests(unittest.TestCase):
    def build_case(
        self,
        directory: Path,
        *,
        embedded: bool,
        png_digest: str | None = None,
        checks_pass: bool = True,
    ) -> tuple[Path, Path | None]:
        manifest_value = json.loads(MANIFEST.read_text(encoding="utf-8"))
        manifest_bytes = json.dumps(
            manifest_value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        png_path = directory / "order-routing.png"
        png_path.write_bytes(PNG_BYTES)
        sidecar = {
            "schema_version": 1,
            "diagram_id": "order-routing",
            "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "svg_sha256": hashlib.sha256(SVG.read_bytes()).hexdigest(),
            "png_sha256": png_digest or hashlib.sha256(PNG_BYTES).hexdigest(),
            "reviewed_at": "2026-07-28T12:00:00Z",
            "reviewer": "codex:test-runtime",
            "attempt_count": 1,
            "checks": {
                "nodes": checks_pass,
                "labels": True,
                "edges": True,
                "evidence_states": True,
                "title_and_scope": True,
            },
            "disposition": "pass",
        }
        sidecar_path = directory / "order-routing.imagegen-verification.json"
        sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")
        encoded = base64.b64encode(PNG_BYTES).decode("ascii")
        image = (
            f'<img data-diagram-id="order-routing" '
            f'alt="Verified order routing diagram" '
            f'src="data:image/png;base64,{encoded}">'
            if embedded
            else ""
        )
        image_csp = "data:" if embedded else "'none'"
        html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src {image_csp}; font-src 'none'; media-src 'none'; connect-src 'none'; frame-src 'none'; form-action 'none'; base-uri 'none'; object-src 'none'">
<title>Verified ImageGen flow</title>
<style>:focus-visible{{outline:2px solid}}@media print{{table{{break-inside:avoid}}}}</style>
</head><body><nav><a href="#main">Main</a></nav><main id="main">
<h1>Verified ImageGen flow</h1>
<template id="boomi-doc-facts">{{"sha256":"63c0425c1a26ab687e4ac7ed332e96a58bf1f56c19ed6020bbba62744aea8d29","facts":{{"component_versions":[{{"id":"process-1","name":"Receive Orders","version":4}}],"inventory_counts":{{"processes":1}},"next_step_ids":["verify-runtime"],"risk_counts":{{"open":1}},"risks":[{{"id":"risk-1","status":"open"}}]}}}}</template>
{image}
<table><caption>Evidence</caption><tr><th scope="col">Area</th></tr><tr><td>Flow</td></tr></table>
</main></body></html>"""
        html_path = directory / "verified-imagegen.html"
        html_path.write_text(html, encoding="utf-8")
        return sidecar_path, html_path

    def test_verified_embedded_png_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            sidecar, html = self.build_case(directory, embedded=True)

            result = run_validator(
                "--strict-generated",
                "--manifest",
                MANIFEST,
                "--markdown",
                VALID_MARKDOWN,
                "--svg",
                SVG,
                "--html",
                html,
                "--imagegen-verification",
                sidecar,
            )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_verified_separate_png_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            sidecar, _ = self.build_case(directory, embedded=False)

            result = run_validator(
                "--strict-generated",
                "--manifest",
                MANIFEST,
                "--markdown",
                VALID_MARKDOWN,
                "--svg",
                SVG,
                "--imagegen-verification",
                sidecar,
            )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_separate_png_keeps_no_image_csp_in_companion_html(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            sidecar, html = self.build_case(directory, embedded=False)

            result = run_validator(
                "--strict-generated",
                "--manifest",
                MANIFEST,
                "--markdown",
                VALID_MARKDOWN,
                "--svg",
                SVG,
                "--html",
                html,
                "--imagegen-verification",
                sidecar,
            )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_png_digest_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            sidecar, html = self.build_case(
                directory, embedded=True, png_digest="0" * 64
            )

            result = run_validator(
                "--strict-generated",
                "--manifest",
                MANIFEST,
                "--markdown",
                VALID_MARKDOWN,
                "--svg",
                SVG,
                "--html",
                html,
                "--imagegen-verification",
                sidecar,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("PNG digest does not match", result.stderr)

    def test_failed_semantic_check_rejects_png(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            sidecar, _ = self.build_case(
                directory, embedded=False, checks_pass=False
            )

            result = run_validator(
                "--strict-generated",
                "--manifest",
                MANIFEST,
                "--markdown",
                VALID_MARKDOWN,
                "--svg",
                SVG,
                "--imagegen-verification",
                sidecar,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("checks.nodes must be true", result.stderr)

    def test_non_png_bytes_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            sidecar, _ = self.build_case(directory, embedded=False)
            (directory / "order-routing.png").write_bytes(b"not a png")

            result = run_validator(
                "--strict-generated",
                "--manifest",
                MANIFEST,
                "--markdown",
                VALID_MARKDOWN,
                "--svg",
                SVG,
                "--imagegen-verification",
                sidecar,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("not a PNG file", result.stderr)


if __name__ == "__main__":
    unittest.main()
