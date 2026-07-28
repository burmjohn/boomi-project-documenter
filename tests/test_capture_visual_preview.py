from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import capture_visual_preview as capture


ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "scripts" / "capture_visual_preview.py"


class CaptureCommandTests(unittest.TestCase):
    def test_capture_command_is_reproducible(self) -> None:
        command = capture.build_browser_command(
            Path("/usr/bin/chromium"),
            Path("/tmp/input.svg"),
            Path("/tmp/out.png"),
        )

        self.assertEqual(command[0], "/usr/bin/chromium")
        self.assertIn("--headless=new", command)
        self.assertIn("--window-size=1440,900", command)
        self.assertIn("--force-device-scale-factor=1", command)
        self.assertIn("--hide-scrollbars", command)
        self.assertIn("--screenshot=/tmp/out.png", command)
        self.assertEqual(command[-1], "file:///tmp/input.svg")

    def test_missing_svg_fails_before_browser_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPTURE),
                    "--svg",
                    str(Path(temporary) / "missing.svg"),
                    "--output",
                    str(Path(temporary) / "out.png"),
                    "--browser",
                    "/missing/chromium",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("SVG file does not exist", result.stderr)

    def test_non_svg_input_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "input.txt"
            source.write_text("<svg></svg>", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPTURE),
                    "--svg",
                    str(source),
                    "--output",
                    str(directory / "out.png"),
                    "--browser",
                    "/missing/chromium",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("input must use the .svg extension", result.stderr)


if __name__ == "__main__":
    unittest.main()
