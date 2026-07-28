from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_boomi_docs.py"
DOCS = ROOT / "tests" / "fixtures" / "docs"


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


if __name__ == "__main__":
    unittest.main()
