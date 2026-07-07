import unittest
import json

from wifi_datahub.adapters.profile_registry import DATASET_ADAPTERS
from wifi_datahub.catalog import repository_root, validate_catalog


class CatalogTests(unittest.TestCase):
    def test_catalog_is_valid(self):
        entries, errors = validate_catalog()
        self.assertGreaterEqual(len(entries), 10)
        self.assertEqual(errors, [])

    def test_every_dataset_has_a_conversion_example(self):
        root = repository_root()
        examples = json.loads((root / "catalog" / "examples.json").read_text(encoding="utf-8"))["datasets"]
        entries, _ = validate_catalog(root)
        self.assertEqual(set(examples), {entry["id"] for entry in entries})
        self.assertTrue(all(example["expected_shape"].startswith("[") for example in examples.values()))

    def test_profile_handlers_are_dataset_specific(self):
        root = repository_root()
        adapters = json.loads((root / "catalog" / "adapters.json").read_text(encoding="utf-8"))["datasets"]
        self.assertNotIn("official-profile", {config["handler"] for config in adapters.values()})
        for dataset_id in DATASET_ADAPTERS:
            self.assertEqual(adapters[dataset_id]["handler"], dataset_id)


if __name__ == "__main__":
    unittest.main()
