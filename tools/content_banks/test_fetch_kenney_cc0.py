import sys
import unittest
from unittest import mock
import urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from fetch_kenney_cc0 import _safe_member, resolve_download, PACKS, _request, MAX_REQUEST_ATTEMPTS


class KenneyContentBankTests(unittest.TestCase):
    def test_only_explicit_cc0_environment_packs_are_catalogued(self):
        self.assertEqual(set(PACKS), {"objects", "foliage"})
        for spec in PACKS.values():
            self.assertIn("kenney.nl/assets/", spec["page"])
            self.assertIn("object", spec["kind"])
            self.assertEqual(len(spec["sha256"]), 64)
            self.assertTrue(spec["archive"].endswith(".zip"))

    def test_resolves_only_https_kenney_download_links(self):
        page = b"""
        <html><body>
          <a href="/assets/tiny-town/download">Download</a>
          <a href="https://example.org/other.zip">Untrusted</a>
          <a href="http://kenney.nl/files/bad.zip">Insecure</a>
        </body></html>
        """
        self.assertEqual(
            resolve_download("https://kenney.nl/assets/tiny-town", page),
            "https://kenney.nl/assets/tiny-town/download"
        )

    def test_rejects_external_or_missing_download_links(self):
        with self.assertRaises(ValueError):
            resolve_download("https://kenney.nl/assets/tiny-town",
                             b'<a href="https://example.org/pack.zip">download</a>')

    def test_rejects_zip_path_traversal_and_windows_paths(self):
        for path in ("../escape.png", "/absolute.png", "folder/../../escape.png",
                     r"folder\\escape.png"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                _safe_member(path)

    def test_accepts_nested_relative_paths(self):
        self.assertEqual(_safe_member("Tiles/Tree.png"), "Tiles/Tree.png")

    @mock.patch("fetch_kenney_cc0.time.sleep")
    @mock.patch("fetch_kenney_cc0.urllib.request.urlopen")
    def test_retries_transient_503_then_returns_download(self, urlopen, sleep):
        failure = urllib.error.HTTPError(
            "https://example.test/pack.zip", 503, "busy", {"Retry-After": "0"}, None
        )
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = "https://example.test/pack.zip"
        response.read.return_value = b"archive"
        urlopen.side_effect = [failure, response]

        self.assertEqual(
            _request("https://example.test/pack.zip"),
            ("https://example.test/pack.zip", b"archive")
        )
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(0.0)

    @mock.patch("fetch_kenney_cc0.time.sleep")
    @mock.patch("fetch_kenney_cc0.urllib.request.urlopen")
    def test_stops_after_bounded_transient_failures(self, urlopen, sleep):
        failure = urllib.error.HTTPError(
            "https://example.test/pack.zip", 503, "busy", {}, None
        )
        urlopen.side_effect = failure

        with self.assertRaises(urllib.error.HTTPError):
            _request("https://example.test/pack.zip")

        self.assertEqual(urlopen.call_count, MAX_REQUEST_ATTEMPTS)
        self.assertEqual(sleep.call_count, MAX_REQUEST_ATTEMPTS - 1)


if __name__ == "__main__":
    unittest.main()
