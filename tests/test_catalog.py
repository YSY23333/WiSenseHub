import unittest
import json

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


if __name__ == "__main__":
    unittest.main()
