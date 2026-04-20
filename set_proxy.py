from __future__ import annotations

import os
import subprocess
import argparse
import platform
import json
from typing import Optional


class ProxyConfigStore:
    """Persistently stores named proxy configurations in ~/.proxy_configs.json."""
    CONFIG_PATH: str = os.path.expanduser("~/.proxy_configs.json")

    @classmethod
    def _read(cls) -> dict[str, dict[str, str]]:
        if os.path.exists(cls.CONFIG_PATH):
            with open(cls.CONFIG_PATH) as f:
                return json.load(f)
        return {}

    @classmethod
    def _write(cls, data: dict[str, dict[str, str]]) -> None:
        with open(cls.CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def save(cls, name: str, ip: str, port: str) -> None:
        configs = cls._read()
        configs[name] = {"ip": ip, "port": port}
        cls._write(configs)
        print(f"Saved '{name}' -> {ip}:{port}")

    @classmethod
    def list(cls) -> None:
        configs = cls._read()
        if not configs:
            print("No saved configs. Use 'proxy save <name> <ip> <port>'")
            return
        print("Saved configs:")
        print("-" * 40)
        for name, cfg in configs.items():
            print(f"  {name}:  {cfg['ip']}:{cfg['port']}")

    @classmethod
    def get(cls, name: str) -> Optional[dict[str, str]]:
        configs = cls._read()
        return configs.get(name)

    @classmethod
    def delete(cls, name: str) -> bool:
        configs = cls._read()
        if name not in configs:
            print(f"Config '{name}' not found")
            return False
        del configs[name]
        cls._write(configs)
        print(f"Deleted '{name}'")
        return True


class ProxyManager:
    """
    Manages system, terminal (zsh), npm and git proxy settings on macOS.
    Supports enabling and disabling proxies across all layers.
    """
    SERVICE: str = "Wi-Fi"

    def __init__(self, ip: Optional[str] = None, port: Optional[str] = None) -> None:
        self.ip: Optional[str] = ip
        self.port: Optional[str] = port
        self.system: str = platform.system()

    def _is_darwin(self) -> bool:
        return self.system == "Darwin"

    def run(self, cmd: str, shell: bool = True, check: bool = True) -> None:
        subprocess.run(cmd, shell=shell, check=check)

    def set_system_proxy(self) -> None:
        """Configure macOS system proxy via networksetup (Wi-Fi service)."""
        if not self._is_darwin():
            raise RuntimeError(f"system proxy is only supported on macOS (current: {self.system})")
        self.run(f'networksetup -setwebproxy "{self.SERVICE}" {self.ip} {self.port}')
        self.run(f'networksetup -setsecurewebproxy "{self.SERVICE}" {self.ip} {self.port}')
        self.run(f'networksetup -setwebproxystate "{self.SERVICE}" on')
        self.run(f'networksetup -setsecurewebproxystate "{self.SERVICE}" on')

    def run_zsh(self, cmd: str) -> None:
        """Run a command in zsh to properly source ~/.zshrc."""
        print(f"zsh -c '{cmd}'")

    def set_terminal_proxy(self) -> None:
        """
        Write proxy export lines to ~/.zshrc inside markers for easy tracking.
        Returns the source command to apply to the current shell.
        """
        zshrc = os.path.expanduser("~/.zshrc")
        proxy_var = f"http_proxy=http://{self.ip}:{self.port}"
        https_var = f"https_proxy=http://{self.ip}:{self.port}"
        marker_start = "# >>> proxy setup >>>"
        marker_end = "# <<< proxy setup <<<"

        lines: list[str] = []
        skip_block = False

        if os.path.exists(zshrc):
            with open(zshrc, "r") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped == marker_start:
                        skip_block = True
                        continue
                    if stripped == marker_end:
                        skip_block = False
                        continue
                    if skip_block:
                        continue
                    # Skip old proxy export lines outside the marker block
                    if any(line.strip().startswith(v) for v in
                           ["export http_proxy=", "export https_proxy=",
                            "export HTTP_PROXY=", "export HTTPS_PROXY=",
                            "http_proxy=", "https_proxy=",
                            "HTTP_PROXY=", "HTTPS_PROXY="]):
                        continue
                    lines.append(line)

        with open(zshrc, "w") as f:
            f.writelines(lines)
            f.write(f"\n{marker_start}\n")
            f.write(f"export {proxy_var}\n")
            f.write(f"export {https_var}\n")
            f.write(f"{marker_end}\n")

        print(f"source {zshrc}")

    def set_npm_proxy(self) -> None:
        """Configure npm to use the proxy via npm config."""
        proxy_url = f"http://{self.ip}:{self.port}"
        self.run(f'npm config set proxy {proxy_url}')
        self.run(f'npm config set https-proxy {proxy_url}')

    def clear_zshrc_proxy(self) -> None:
        """Remove all proxy export lines from ~/.zshrc."""
        zshrc = os.path.expanduser("~/.zshrc")
        if os.path.exists(zshrc):
            lines: list[str] = []
            with open(zshrc, "r") as f:
                for line in f:
                    # Preserve lines that aren't proxy exports
                    if not any(line.strip().startswith(v) for v in
                               ["export http_proxy=", "export https_proxy=",
                                "export HTTP_PROXY=", "export HTTPS_PROXY=",
                                "http_proxy=", "https_proxy=",
                                "HTTP_PROXY=", "HTTPS_PROXY="]):
                        lines.append(line)

            with open(zshrc, "w") as f:
                f.writelines(lines)

        # Note: proxy vars remain set in the current shell session.
        # Open a new terminal or manually run: unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY

    def disable_system_proxy(self) -> None:
        """Disable macOS system proxy via networksetup."""
        if not self._is_darwin():
            raise RuntimeError(f"system proxy is only supported on macOS (current: {self.system})")
        self.run(f'networksetup -setwebproxystate "{self.SERVICE}" off')
        self.run(f'networksetup -setsecurewebproxystate "{self.SERVICE}" off')

    def set_git_proxy(self) -> None:
        """Configure Git global proxy via git config."""
        proxy_url = f"http://{self.ip}:{self.port}"
        self.run(f'git config --global http.proxy {proxy_url}')
        self.run(f'git config --global https.proxy {proxy_url}')

    def clear_git_proxy(self) -> None:
        """Remove Git global proxy configuration."""
        self.run("git config --global --unset http.proxy", check=False)
        self.run("git config --global --unset https.proxy", check=False)

    def disable_npm_proxy(self) -> None:
        """Remove npm proxy configuration."""
        self.run("npm config delete proxy", check=False)
        self.run("npm config delete https-proxy", check=False)

    def enable(self) -> None:
        """Enable proxy across all layers (system, terminal, npm, git)."""
        if not self.ip or not self.port:
            raise ValueError("--ip and --port are required to enable proxy")
        self.set_system_proxy()
        self.set_terminal_proxy()
        self.set_npm_proxy()
        self.set_git_proxy()
        self.run_zsh("source ~/.zshrc")
        self.print_message('proxy is set successfully!')

    def print_message(self, message: str) -> None:
        print(f"echo '{message}'")

    def disable(self) -> None:
        """Disable proxy across all layers (system, terminal, npm, git)."""
        self.disable_system_proxy()
        self.clear_zshrc_proxy()
        self.disable_npm_proxy()
        self.clear_git_proxy()
        self.unset_proxy_env_variables()
        self.run_zsh("source ~/.zshrc")
        self.print_message('proxy has been removed!')

    def unset_proxy_env_variables(self) -> None:
        print(f'unset all_proxy ALL_PROXY http_proxy https_proxy')

    def status(self) -> None:
        """Print current proxy status for all layers."""
        print("Proxy Status:")
        print("-" * 40)

        # System proxy
        if self._is_darwin():
            try:
                web = subprocess.run(
                    ["networksetup", "-getwebproxy", self.SERVICE],
                    capture_output=True, text=True
                )
                secure = subprocess.run(
                    ["networksetup", "-getsecurewebproxy", self.SERVICE],
                    capture_output=True, text=True
                )
                web_on = "Yes" in web.stdout
                secure_on = "Yes" in secure.stdout
                print(f"  System proxy:  {'enabled' if web_on and secure_on else 'disabled'}")
            except Exception as e:
                print(f"  System proxy:  error ({e})")
        else:
            print(f"  System proxy:  not supported (not macOS)")

        # Terminal env vars
        http_v = os.environ.get("http_proxy", "")
        https_v = os.environ.get("https_proxy", "")
        HTTP_V = os.environ.get("HTTP_PROXY", "")
        HTTPS_V = os.environ.get("HTTPS_PROXY", "")
        all_env = http_v or https_v or HTTP_V or HTTPS_V
        if all_env:
            print(f"  http_proxy:    {http_v or HTTP_V or '(https only)'}")
            print(f"  https_proxy:   {https_v or HTTPS_V or '(http only)'}")
        else:
            print(f"  Terminal vars: not set")

        # NPM proxy
        try:
            npm_proxy = subprocess.run(
                ["npm", "config", "get", "proxy"],
                capture_output=True, text=True
            )
            npm_https = subprocess.run(
                ["npm", "config", "get", "https-proxy"],
                capture_output=True, text=True
            )
            np = npm_proxy.stdout.strip()
            nh = npm_https.stdout.strip()
            if np == "null":
                print(f"  NPM proxy:      not set")
            else:
                print(f"  NPM proxy:      {np}")
                if nh != "null":
                    print(f"  NPM https-proxy: {nh}")
        except Exception as e:
            print(f"  NPM proxy:      error ({e})")

        # Git proxy
        try:
            git_http = subprocess.run(
                ["git", "config", "--global", "--get", "http.proxy"],
                capture_output=True, text=True
            )
            git_https = subprocess.run(
                ["git", "config", "--global", "--get", "https.proxy"],
                capture_output=True, text=True
            )
            gh = git_http.stdout.strip()
            ghs = git_https.stdout.strip()
            if gh or ghs:
                if gh and gh != ghs:
                    print(f"  Git http.proxy:  {gh}")
                    print(f"  Git https.proxy: {ghs}")
                else:
                    print(f"  Git proxy:       {gh or ghs}")
            else:
                print(f"  Git proxy:       not set")
        except Exception as e:
            print(f"  Git proxy:       error ({e})")

        # Proxy IP
        print("-" * 40)
        print("  Checking Proxy IP...")
        try:
            ip = subprocess.run(
                ["curl", "-s", "ipinfo.io/ip"],
                capture_output=True, text=True, timeout=10
            )
            if ip.returncode == 0 and ip.stdout.strip():
                print(f"  Proxy IP:       {ip.stdout.strip()}")
            else:
                print("  Proxy IP:       (failed)")
        except Exception:
            print("  Proxy IP:       (unavailable)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manage system, terminal (zsh), npm and git proxy settings on macOS.",
        epilog="""
First-time setup:
  python set_proxy.py --install
  source ~/.zshrc

Usage:
  proxy on <ip> <port>   - Enable proxy with raw IP:port
  proxy on <name>        - Enable proxy using a saved config
  proxy off              - Disable proxy
  proxy status           - Show proxy status
  proxy save <name> <ip> <port>  - Save a named config
  proxy list             - List saved configs
  proxy del <name>       - Delete a saved config

Direct script usage:
  python set_proxy.py --install   - Install proxy function to ~/.zshrc

Examples:
  proxy on 192.168.1.100 8080
  proxy on myproxy
  proxy save myproxy 192.168.1.100 8080
  proxy list
  proxy del myproxy
  proxy off

The script manages four proxy layers:
  1. macOS system proxy (networksetup for Wi-Fi)
  2. Terminal proxy (export http_proxy/https_proxy in ~/.zshrc)
  3. NPM proxy (npm config set proxy / https-proxy)
  4. Git proxy (git config --global http/https.proxy)

Configs are stored in ~/.proxy_configs.json
"""
    )
    parser.add_argument("--ip", help="Proxy IP address (required to enable)")
    parser.add_argument("--port", help="Proxy port number (required to enable)")
    parser.add_argument("--off", action="store_true", help="Disable proxy instead of enabling")
    parser.add_argument("--status", action="store_true", help="Show current proxy status")
    parser.add_argument("--save", metavar="NAME", help="Save current --ip/--port as a named config")
    parser.add_argument("--list", action="store_true", help="List all saved proxy configs")
    parser.add_argument("--del", metavar="NAME", dest="delete_name", help="Delete a saved proxy config")
    parser.add_argument("--use", metavar="NAME", help="Load a saved config and enable proxy with it")
    parser.add_argument("--install", action="store_true", help="Install proxy function to ~/.zshrc")
    args: argparse.Namespace = parser.parse_args()

    # Handle config management commands
    if args.list:
        ProxyConfigStore.list()
        return

    if args.delete_name:
        ProxyConfigStore.delete(args.delete_name)
        return

    if args.save:
        if not args.ip or not args.port:
            print("Error: --save requires --ip and --port")
            return
        ProxyConfigStore.save(args.save, args.ip, args.port)
        return

    # --use <name> loads a saved config and enabling proxy with it
    if args.use:
        cfg = ProxyConfigStore.get(args.use)
        if not cfg:
            print(f"Config '{args.use}' not found. Use 'proxy list' to see saved configs.")
            return
        manager = ProxyManager(ip=cfg["ip"], port=cfg["port"])
        manager.enable()
        return

    if args.install:
        zshrc = os.path.expanduser("~/.zshrc")
        script_path = os.path.abspath(__file__)
        func_block = f'''
# >>> proxy function >>>
proxy() {{
  case "$1" in
    on)
      if [ -z "$2" ]; then
        echo "Usage: proxy on <ip> <port>   or   proxy on <saved_name>"
        return 1
      fi
      if [ -n "$3" ]; then
        # Two args: raw IP and port
        eval "$(python {script_path} --ip "$2" --port "$3")"
      else
        # One arg: saved config name
        eval "$(python {script_path} --use "$2")"
      fi
      ;;
    off)
      eval "$(python {script_path} --off)"
      ;;
    status)
      python {script_path} --status
      ;;
    save)
      if [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
        echo "Usage: proxy save <name> <ip> <port>"
        return 1
      fi
      python {script_path} --save "$2" --ip "$3" --port "$4"
      ;;
    list)
      python {script_path} --list
      ;;
    del)
      if [ -z "$2" ]; then
        echo "Usage: proxy del <name>"
        return 1
      fi
      python {script_path} --del "$2"
      ;;
    *)
      echo "Usage: proxy <on|off|status|save|list|del> [args]"
      ;;
  esac
}}
# <<< proxy function <<<
'''
        # Remove old install block if exists
        lines: list[str] = []
        skip = False
        if os.path.exists(zshrc):
            with open(zshrc, "r") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped == "# >>> proxy function >>>":
                        skip = True
                        continue
                    if stripped == "# <<< proxy function <<<":
                        skip = False
                        continue
                    if skip:
                        continue
                    lines.append(line)

        with open(zshrc, "w") as f:
            f.writelines(lines)
            f.write(func_block)

        print(f"proxy function installed to {zshrc}. Run 'source {zshrc}' or restart terminal.")
        return

    if args.status:
        manager = ProxyManager()
        manager.status()
        return

    manager = ProxyManager(ip=args.ip, port=args.port)

    if args.off:
        manager.disable()
    else:
        manager.enable()


if __name__ == "__main__":
    main()
