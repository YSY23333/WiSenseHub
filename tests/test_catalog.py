import unittest

from wifi_datahub.catalog import validate_catalog


class CatalogTests(unittest.TestCase):
    def test_catalog_is_valid(self):
        entries, errors = validate_catalog()
        self.assertGreaterEqual(len(entries), 10)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
