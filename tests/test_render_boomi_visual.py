from __future__ import annotations

import copy
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts import boomi_visual_contract as contract
from scripts import render_boomi_visual as renderer


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests" / "fixtures" / "manifests" / "valid-routing.json"
RENDERER = ROOT / "scripts" / "render_boomi_visual.py"


class RendererTests(unittest.TestCase):
    def test_render_is_stable_accessible_and_scrollable(self) -> None:
        diagram = contract.load_manifest(MANIFEST)["diagrams"][0]

        first = renderer.render_diagram(diagram)
        second = renderer.render_diagram(diagram)

        self.assertEqual(first, second)
        self.assertTrue(first.startswith("<svg "))
        self.assertIn('role="img"', first)
        self.assertIn(
            'aria-labelledby="order-routing-title order-routing-desc"', first
        )
        self.assertIn('viewBox="0 0 960 ', first)
        self.assertIn("min-width:720px", first)
        self.assertIn("font-size:14px", first)
        self.assertIn("<title id=\"order-routing-title\">Order routing</title>", first)
        self.assertIn("Evidence scope: configuration", first)
        self.assertNotIn("<script", first)

    def test_evidence_text_is_escaped(self) -> None:
        diagram = copy.deepcopy(contract.load_manifest(MANIFEST)["diagrams"][0])
        diagram["nodes"][0]["label"] = 'Receive <order> & "verify"'

        svg = renderer.render_diagram(diagram)

        self.assertIn("Receive &lt;order&gt; &amp; &quot;verify&quot;", svg)
        self.assertNotIn("Receive <order>", svg)

    def test_vertical_layout_is_taller_than_wide(self) -> None:
        diagram = copy.deepcopy(contract.load_manifest(MANIFEST)["diagrams"][0])
        diagram["orientation"] = "vertical"

        svg = renderer.render_diagram(diagram)

        self.assertIn('viewBox="0 0 720 760"', svg)

    def test_internal_ids_are_prefixed_for_multi_diagram_embedding(self) -> None:
        diagram = contract.load_manifest(MANIFEST)["diagrams"][0]

        svg = renderer.render_diagram(diagram)

        self.assertIn('id="order-routing-receive"', svg)
        self.assertIn('id="order-routing-receive-route"', svg)
        self.assertNotIn('id="receive"', svg)

    def test_routing_branches_share_depth_without_crossing_sibling_nodes(self) -> None:
        diagram = contract.load_manifest(MANIFEST)["diagrams"][0]

        root = ET.fromstring(renderer.render_diagram(diagram))
        namespace = {"svg": "http://www.w3.org/2000/svg"}

        def rect_for(group_id: str) -> ET.Element:
            group = root.find(f".//svg:g[@id='{group_id}']", namespace)
            self.assertIsNotNone(group)
            rect = group.find("svg:rect", namespace)  # type: ignore[union-attr]
            self.assertIsNotNone(rect)
            return rect  # type: ignore[return-value]

        deliver = rect_for("order-routing-deliver")
        review = rect_for("order-routing-review")
        route = rect_for("order-routing-route")
        invalid_group = root.find(
            ".//svg:g[@id='order-routing-route-review']", namespace
        )
        self.assertIsNotNone(invalid_group)
        invalid_line = invalid_group.find("svg:line", namespace)  # type: ignore[union-attr]
        self.assertIsNotNone(invalid_line)

        self.assertEqual(deliver.get("x"), review.get("x"))
        self.assertNotEqual(deliver.get("y"), review.get("y"))
        route_center_x = float(route.get("x", "0")) + float(route.get("width", "0")) / 2
        review_center_x = (
            float(review.get("x", "0")) + float(review.get("width", "0")) / 2
        )
        review_left_x = float(review.get("x", "0"))
        self.assertGreater(float(invalid_line.get("x1", "0")), route_center_x)
        self.assertGreaterEqual(float(invalid_line.get("x2", "0")), review_left_x)
        self.assertLess(float(invalid_line.get("x2", "0")), review_center_x)


class RendererCliTests(unittest.TestCase):
    def run_renderer(self, *args: object) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(RENDERER), *(str(arg) for arg in args)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_output_dir_writes_diagram_named_svg(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)

            result = self.run_renderer(
                "--manifest", MANIFEST, "--output-dir", output_dir
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                sorted(path.name for path in output_dir.iterdir()),
                ["order-routing.svg"],
            )
            self.assertIn("Rendered 1 diagram", result.stdout)

    def test_single_output_writes_exact_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "diagram.svg"

            result = self.run_renderer("--manifest", MANIFEST, "--output", output)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.read_text(encoding="utf-8").startswith("<svg "))


if __name__ == "__main__":
    unittest.main()
