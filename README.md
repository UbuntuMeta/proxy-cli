# Proxy Switch

A macOS proxy fast-switch tool supporting system proxy, terminal environment variables, NPM proxy, and Git proxy across four layers.

## Features

- **System proxy** — Configures macOS Wi-Fi proxy via `networksetup`
- **Terminal proxy** — Writes `http_proxy` / `https_proxy` to `~/.zshrc`
- **NPM proxy** — Sets `npm config set proxy / https-proxy`
- **Git proxy** — Sets `git config --global http.proxy / https.proxy`
- **`proxy on`** — Enable proxy in one command
- **`proxy off`** — Disable proxy in one command
- **`proxy status`** — Show current proxy status and exit IP
- **`proxy whitelist`** — Show NO_PROXY / no_proxy whitelist

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

# Show NO_PROXY / no_proxy whitelist
proxy whitelist

# Save named config
proxy save myproxy 192.168.1.100 8080

# Use a saved config
proxy on myproxy

# List saved configs
proxy list

# Delete a saved config
proxy del myproxy
```

## Notes

- macOS only
- System proxy operations may require admin privileges (password prompt)
- Exit IP check uses `ipinfo.io/ip` and requires internet connectivity
- Configs are stored in `~/.proxy_configs.json`
