# Proxy Switch

A macOS proxy fast-switch tool supporting system proxy, terminal environment variables, and NPM proxy across three layers.

## Features

- **System proxy** — Configures macOS Wi-Fi proxy via `networksetup`
- **Terminal proxy** — Writes `http_proxy` / `https_proxy` to `~/.zshrc`
- **NPM proxy** — Sets `npm config set proxy / https-proxy`
- **`proxy on`** — Enable proxy in one command
- **`proxy off`** — Disable proxy in one command
- **`proxy status`** — Show current proxy status and exit IP

## Setup

```bash
# 1. Install the proxy function to ~/.zshrc
python set_proxy.py --install

# 2. Activate it
source ~/.zshrc
```

## Usage

```bash
# Enable proxy
proxy on 192.168.1.100 8080

# Disable proxy
proxy off

# Check status
proxy status
```

## Notes

- macOS only
- System proxy operations may require admin privileges (password prompt)
- Exit IP check uses `ifconfig.me` and requires internet connectivity
