from __future__ import annotations

import copy
import unittest
from pathlib import Path

from scripts import boomi_visual_contract as contract


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class ManifestContractTests(unittest.TestCase):
    def test_valid_manifest_is_normalized(self) -> None:
        manifest = contract.load_manifest(FIXTURES / "manifests" / "valid-routing.json")

        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["diagrams"][0]["id"], "order-routing")
        self.assertEqual(manifest["diagrams"][0]["nodes"][0]["evidence_state"], "configured")

    def test_more_than_nine_nodes_is_rejected(self) -> None:
        with self.assertRaisesRegex(contract.ContractError, "at most 9 nodes"):
            contract.load_manifest(
                FIXTURES / "manifests" / "invalid-too-many-nodes.json"
            )

    def test_duplicate_node_ids_are_rejected(self) -> None:
        manifest = contract.load_manifest(FIXTURES / "manifests" / "valid-routing.json")
        invalid = copy.deepcopy(manifest)
        invalid["diagrams"][0]["nodes"][1]["id"] = "receive"

        with self.assertRaisesRegex(contract.ContractError, "duplicate node id"):
            contract.validate_manifest(invalid)

    def test_edge_endpoint_must_exist(self) -> None:
        manifest = contract.load_manifest(FIXTURES / "manifests" / "valid-routing.json")
        invalid = copy.deepcopy(manifest)
        invalid["diagrams"][0]["edges"][0]["to"] = "missing"

        with self.assertRaisesRegex(contract.ContractError, "unknown node"):
            contract.validate_manifest(invalid)

    def test_canonical_json_is_stable_utf8(self) -> None:
        left = contract.canonical_json({"é": 1, "a": 2})
        right = contract.canonical_json({"a": 2, "é": 1})

        self.assertEqual(left, right)
        self.assertEqual(left, b'{"a":2,"\xc3\xa9":1}')
        self.assertEqual(
            contract.sha256_bytes(b"boomi"),
            "e056c895e8f10250aa962b70dc0c8e078a2a7d21e0bafe5f3feea460405a72b3",
        )


class VerificationContractTests(unittest.TestCase):
    def test_passing_verification_is_accepted(self) -> None:
        value = contract.load_json(
            FIXTURES
            / "verification"
            / "order-routing.imagegen-verification.json"
        )

        verified = contract.validate_verification(value)

        self.assertEqual(verified["diagram_id"], "order-routing")
        self.assertEqual(verified["disposition"], "pass")

    def test_false_semantic_check_is_rejected(self) -> None:
        value = contract.load_json(
            FIXTURES
            / "verification"
            / "order-routing.imagegen-verification.json"
        )
        invalid = copy.deepcopy(value)
        invalid["checks"]["edges"] = False

        with self.assertRaisesRegex(contract.ContractError, "checks.edges must be true"):
            contract.validate_verification(invalid)

    def test_more_than_three_attempts_is_rejected(self) -> None:
        value = contract.load_json(
            FIXTURES
            / "verification"
            / "order-routing.imagegen-verification.json"
        )
        invalid = copy.deepcopy(value)
        invalid["attempt_count"] = 4

        with self.assertRaisesRegex(contract.ContractError, "between 1 and 3"):
            contract.validate_verification(invalid)


if __name__ == "__main__":
    unittest.main()
