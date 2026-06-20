from __future__ import annotations

import unittest

from main import build_message


class GeneratedCliTest(unittest.TestCase):
    def test_build_message(self) -> None:
        self.assertEqual(build_message("Ada"), "Hello, Ada.")
        self.assertEqual(build_message("Ada", excited=True), "Hello, Ada!")


if __name__ == "__main__":
    unittest.main()
