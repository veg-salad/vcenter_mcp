import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vcenter_mcp.registry import split_csv


class SplitCsvTests(unittest.TestCase):
    def test_handles_empty_values(self):
        self.assertIsNone(split_csv(""))
        self.assertIsNone(split_csv(None))

    def test_splits_and_strips(self):
        self.assertEqual(split_csv(" vm-1, vm-2 ,vm-3 "), ["vm-1", "vm-2", "vm-3"])


if __name__ == "__main__":
    unittest.main()
