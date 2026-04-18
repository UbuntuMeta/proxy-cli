# Proxy Switch

macOS 代理快速切换工具，支持系统代理、终端环境变量、NPM 和 Git 代理四个层次。

## 功能

- **系统代理** — 通过 `networksetup` 配置 macOS Wi-Fi 代理
- **终端代理** — 将 `http_proxy` / `https_proxy` 写入 `~/.zshrc`
- **NPM 代理** — 设置 `npm config set proxy / https-proxy`
- **Git 代理** — 设置 `git config --global http.proxy / https.proxy`
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
# 通过 IP 和端口开启代理
proxy on 192.168.1.100 8080

# 关闭代理
proxy off

# 查看状态
proxy status

# 保存命名配置
proxy save myproxy 192.168.1.100 8080
proxy on myproxy

# 查看已保存的配置
proxy list

# 删除已保存的配置
proxy del myproxy
```

## 注意事项

- 仅支持 macOS
- 系统代理操作需要管理员权限（可能会提示输入密码）
- 出口 IP 检测使用 `ipinfo.io/ip`，需联网
