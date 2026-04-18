# Proxy Switch

macOS 代理快速切换工具，支持系统代理、终端环境变量和 NPM 代理三个层次。

## 功能

- **系统代理** — 通过 `networksetup` 配置 macOS Wi-Fi 代理
- **终端代理** — 设置 `http_proxy` / `https_proxy` 环境变量到 `~/.zshrc`
- **NPM 代理** — 配置 `npm config set proxy / https-proxy`
- **`proxy on`** — 一键开启代理
- **`proxy off`** — 一键关闭代理
- **`proxy status`** — 查看当前代理状态及出口 IP

## 安装

```bash
# 1. 安装 proxy 命令到 ~/.zshrc
python set_proxy.py --install

# 2. 使其生效
source ~/.zshrc
```

## 使用

```bash
# 开启代理
proxy on 192.168.1.100 8080

# 关闭代理
proxy off

# 查看状态
proxy status
```

## 注意事项

- 仅支持 macOS
- 系统代理操作需要管理员权限（可能会提示输入密码）
- 出口 IP 检测使用 `ifconfig.me`，需联网
