#!/usr/bin/env python3
"""Regression tests for matching Godot CLI and runtime build identities."""
import unittest

from validate_catalog_validation_report import engine_versions_match


class GodotEngineVersionMatchTests(unittest.TestCase):
    def test_cli_truncated_hash_matches_full_runtime_hash(self):
        self.assertTrue(engine_versions_match(
            "4.5.1.stable.official.f62fdbde1",
            "Godot 4.5.1.stable.official.f62fdbde15035c5576dad93e586201f4d41ef0cb",
        ))

    def test_different_build_hash_is_rejected(self):
        self.assertFalse(engine_versions_match(
            "4.5.1.stable.official.f62fdbde1",
            "Godot 4.5.1.stable.official.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        ))

    def test_different_patch_version_is_rejected(self):
        self.assertFalse(engine_versions_match(
            "4.5.1.stable.official.f62fdbde1",
            "Godot 4.5.2.stable.official.f62fdbde15035c5576dad93e586201f4d41ef0cb",
        ))

    def test_non_hex_or_short_hash_is_rejected(self):
        self.assertFalse(engine_versions_match(
            "4.5.1.stable.official.f62fdbde1",
            "Godot 4.5.1.stable.official.f62fdbde1ZZZZ",
        ))


if __name__ == "__main__":
    unittest.main()
