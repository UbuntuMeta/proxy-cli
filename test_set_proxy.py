import os
import tempfile
import unittest
from unittest.mock import patch

import sys
sys.path.insert(0, os.path.dirname(__file__))
from set_proxy import ProxyManager


class TestProxyManagerEnableDisable(unittest.TestCase):
    """Tests for enable() and disable() orchestration."""

    @patch.object(ProxyManager, "run")
    def test_enable_calls_all_subsystems(self, mock_run):
        pm = ProxyManager(ip="192.168.1.1", port="8080")
        pm.enable()
        mock_run.assert_any_call('networksetup -setwebproxy "Wi-Fi" 192.168.1.1 8080')
        mock_run.assert_any_call('networksetup -setsecurewebproxy "Wi-Fi" 192.168.1.1 8080')
        mock_run.assert_any_call('networksetup -setwebproxystate "Wi-Fi" on')
        mock_run.assert_any_call('networksetup -setsecurewebproxystate "Wi-Fi" on')
        mock_run.assert_any_call('npm config set proxy http://192.168.1.1:8080')
        mock_run.assert_any_call('npm config set https-proxy http://192.168.1.1:8080')
        mock_run.assert_any_call('git config --global http.proxy http://192.168.1.1:8080')
        mock_run.assert_any_call('git config --global https.proxy http://192.168.1.1:8080')

    @patch.object(ProxyManager, "run")
    def test_disable_calls_all_subsystems(self, mock_run):
        pm = ProxyManager(ip="192.168.1.1", port="8080")
        pm.disable()
        mock_run.assert_any_call('networksetup -setwebproxystate "Wi-Fi" off')
        mock_run.assert_any_call('networksetup -setsecurewebproxystate "Wi-Fi" off')
        mock_run.assert_any_call("npm config delete proxy")
        mock_run.assert_any_call("npm config delete https-proxy")
        mock_run.assert_any_call("git config --global --unset http.proxy")
        mock_run.assert_any_call("git config --global --unset https.proxy")

    def test_enable_raises_when_ip_missing(self):
        pm = ProxyManager(ip=None, port="8080")
        with self.assertRaises(ValueError) as ctx:
            pm.enable()
        self.assertIn("--ip and --port are required", str(ctx.exception))

    def test_enable_raises_when_port_missing(self):
        pm = ProxyManager(ip="192.168.1.1", port=None)
        with self.assertRaises(ValueError) as ctx:
            pm.enable()
        self.assertIn("--ip and --port are required", str(ctx.exception))


class TestSystemProxy(unittest.TestCase):
    """Tests for system proxy on non-Darwin platforms."""

    @patch.object(ProxyManager, "run")
    def test_set_system_proxy_rejects_non_darwin(self, mock_run):
        pm = ProxyManager(ip="192.168.1.1", port="8080")
        pm.system = "Linux"
        with self.assertRaises(RuntimeError) as ctx:
            pm.set_system_proxy()
        self.assertIn("only supported on macOS", str(ctx.exception))
        mock_run.assert_not_called()

    @patch.object(ProxyManager, "run")
    def test_disable_system_proxy_rejects_non_darwin(self, mock_run):
        pm = ProxyManager(ip="192.168.1.1", port="8080")
        pm.system = "Windows"
        with self.assertRaises(RuntimeError) as ctx:
            pm.disable_system_proxy()
        self.assertIn("only supported on macOS", str(ctx.exception))
        mock_run.assert_not_called()


class TestTerminalProxyIdempotent(unittest.TestCase):
    """Tests for set_terminal_proxy() idempotency."""

    def test_set_terminal_proxy_creates_file_if_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            zshrc_path = os.path.join(tmpdir, ".zshrc")
            with patch.object(ProxyManager, "run"), \
                 patch.dict(os.environ, {"HOME": tmpdir}):
                pm = ProxyManager(ip="10.0.0.1", port="3128")
                pm._is_darwin = lambda: True
                with patch.object(pm, "run"):
                    pm.set_terminal_proxy()
                with open(zshrc_path, "r") as f:
                    content = f.read()
                self.assertIn("export http_proxy=http://10.0.0.1:3128", content)
                self.assertIn("export https_proxy=http://10.0.0.1:3128", content)

    def test_set_terminal_proxy_removes_old_entries_before_adding(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            zshrc_path = os.path.join(tmpdir, ".zshrc")
            original = (
                "export PATH=/usr/bin\n"
                "export http_proxy=http://old:999\n"
                "export https_proxy=http://old:999\n"
                "export FOO=bar\n"
            )
            with open(zshrc_path, "w") as f:
                f.write(original)

            with patch.object(ProxyManager, "run"), \
                 patch.dict(os.environ, {"HOME": tmpdir}):
                pm = ProxyManager(ip="10.0.0.1", port="3128")
                pm._is_darwin = lambda: True
                with patch.object(pm, "run"):
                    pm.set_terminal_proxy()
                with open(zshrc_path, "r") as f:
                    content = f.read()

            self.assertNotIn("old:999", content)
            self.assertIn("export PATH=/usr/bin", content)
            self.assertIn("export FOO=bar", content)
            self.assertIn("export http_proxy=http://10.0.0.1:3128", content)
            self.assertIn("export https_proxy=http://10.0.0.1:3128", content)

    def test_set_terminal_proxy_no_double_lines_on_second_call(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            zshrc_path = os.path.join(tmpdir, ".zshrc")

            with patch.object(ProxyManager, "run"), \
                 patch.dict(os.environ, {"HOME": tmpdir}):
                pm = ProxyManager(ip="10.0.0.1", port="3128")
                pm._is_darwin = lambda: True
                with patch.object(pm, "run"):
                    pm.set_terminal_proxy()
                    pm.set_terminal_proxy()

            with open(zshrc_path, "r") as f:
                lines = f.readlines()
            proxy_lines = [l for l in lines if "http_proxy" in l or "https_proxy" in l]
            self.assertEqual(len(proxy_lines), 2,
                             f"Expected 2 proxy lines, got {proxy_lines}")


class TestClearZshrcProxy(unittest.TestCase):
    """Tests for clear_zshrc_proxy()."""

    def test_removes_only_proxy_lines(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            zshrc_path = os.path.join(tmpdir, ".zshrc")
            original = (
                "export PATH=/usr/bin\n"
                "export http_proxy=http://old:999\n"
                "export https_proxy=http://old:999\n"
                "export HTTP_PROXY=http://old:999\n"
                "export HTTPS_PROXY=http://old:999\n"
                "export FOO=bar\n"
            )
            with open(zshrc_path, "w") as f:
                f.write(original)

            with patch.object(ProxyManager, "run"), \
                 patch.dict(os.environ, {"HOME": tmpdir}):
                pm = ProxyManager(ip="10.0.0.1", port="3128")
                pm._is_darwin = lambda: True
                with patch.object(pm, "run"):
                    pm.clear_zshrc_proxy()

            with open(zshrc_path, "r") as f:
                content = f.read()

            self.assertNotIn("http_proxy", content)
            self.assertNotIn("https_proxy", content)
            self.assertIn("export PATH=/usr/bin", content)
            self.assertIn("export FOO=bar", content)

    def test_handles_missing_zshrc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(ProxyManager, "run"), \
                 patch.dict(os.environ, {"HOME": tmpdir}):
                pm = ProxyManager(ip="10.0.0.1", port="3128")
                pm._is_darwin = lambda: True
                with patch.object(pm, "run"):
                    pm.clear_zshrc_proxy()


class TestNpmProxy(unittest.TestCase):
    """Tests for npm proxy methods."""

    @patch.object(ProxyManager, "run")
    def test_set_npm_proxy(self, mock_run):
        pm = ProxyManager(ip="10.0.0.1", port="3128")
        pm.set_npm_proxy()
        mock_run.assert_any_call("npm config set proxy http://10.0.0.1:3128")
        mock_run.assert_any_call("npm config set https-proxy http://10.0.0.1:3128")

    @patch.object(ProxyManager, "run")
    def test_disable_npm_proxy(self, mock_run):
        pm = ProxyManager(ip="10.0.0.1", port="3128")
        pm.disable_npm_proxy()
        mock_run.assert_any_call("npm config delete proxy")
        mock_run.assert_any_call("npm config delete https-proxy")


if __name__ == "__main__":
    unittest.main()
