"""Verify private configuration precedence and errors without camera/model access."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("monitor_config", Path(__file__).parents[1] / "engine/config.py")
config = importlib.util.module_from_spec(spec)
with patch.dict(os.environ, {}, clear=True):
    spec.loader.exec_module(config)


class LocalCameraConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "config.local.json"
        self.environ = patch.dict(os.environ, {}, clear=True)
        self.environ.start()
        self.addCleanup(self.environ.stop)

    def write(self, value):
        self.path.write_text(json.dumps(value), encoding="utf-8")

    def test_missing_config_does_not_require_a_network_camera(self):
        self.assertEqual(config.load_mjpeg_url(self.path), "")

    def test_local_json_reads_camera_url(self):
        self.write({"mjpeg_url": "  http://localhost:8081/video_feed  "})
        self.assertEqual(config.load_mjpeg_url(self.path), "http://localhost:8081/video_feed")

    def test_environment_overrides_even_a_malformed_local_file(self):
        self.path.write_text("not json", encoding="utf-8")
        os.environ["INDUSTRIAL_SECURITY_MJPEG_URL"] = "https://localhost:8443/video_feed"
        self.assertEqual(config.load_mjpeg_url(self.path), os.environ["INDUSTRIAL_SECURITY_MJPEG_URL"])

    def test_blank_environment_falls_back_to_file(self):
        self.write({"mjpeg_url": "http://localhost:8081/video_feed"})
        os.environ["INDUSTRIAL_SECURITY_MJPEG_URL"] = "  "
        self.assertEqual(config.load_mjpeg_url(self.path), "http://localhost:8081/video_feed")

    def test_malformed_or_wrong_shape_json_has_a_clear_error(self):
        self.path.write_text("not json", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "JSON"):
            config.load_mjpeg_url(self.path)
        for value in [[], {"mjpeg_url": 123}]:
            with self.subTest(value=value):
                self.write(value)
                with self.assertRaises(ValueError):
                    config.load_mjpeg_url(self.path)

    def test_invalid_url_and_port_do_not_echo_credentials(self):
        for url in ["file:///private/video", "http://private-user:private-password@localhost:bad/video"]:
            with self.subTest(url=url):
                self.write({"mjpeg_url": url})
                with self.assertRaises(ValueError) as error:
                    config.load_mjpeg_url(self.path)
                self.assertNotIn("private-password", str(error.exception))
                self.assertNotIn(url, str(error.exception))

    def test_utf8_bom_from_windows_editor_is_accepted(self):
        self.path.write_text('{"mjpeg_url":"http://localhost:8081/video_feed"}', encoding="utf-8-sig")
        self.assertEqual(config.load_mjpeg_url(self.path), "http://localhost:8081/video_feed")


if __name__ == "__main__":
    unittest.main()
