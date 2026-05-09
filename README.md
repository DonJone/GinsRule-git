# GinsRules Sync

每日自动从 [Gins-Rules](https://rules.ichimarugin728.dev) 同步代理规则文件，覆盖 **11 个客户端格式**、**6 个分类**、**134 条规则**。

> 感谢 [IchimaruGin728](https://rules.ichimarugin728.dev) 提供的 Gins-Rules 规则分发控制平面，统一了多格式代理规则的生成与分发。

## 目录结构

```
.
├── .github/workflows/sync.yml    # 每日自动同步 (UTC 00:00)
├── scripts/sync_rules.py         # 同步脚本 (动态发现 + ETag 增量)
├── manifest.json                 # ETag 缓存
├── requirements.txt
└── rules/
    ├── sing-box/                 # .srs   — Sing-box 二进制规则
    │   ├── proxy/{name}.srs
    │   ├── direct/{name}.srs
    │   ├── reject/{name}.srs
    │   ├── ip/{name}.srs
    │   ├── asn/{name}.srs
    │   └── ai/{name}.srs
    ├── mihomo/                   # .mrs   — Mihomo 二进制规则
    │   └── {proxy,direct,reject,ip,asn,ai}/*.mrs
    ├── stash/                    # .mrs   — Stash 二进制规则
    ├── surge/                    # .list  — Surge 规则列表
    ├── loon/                     # .lsr   — Loon 规则
    ├── quantumultx/              # .list  — QuantumultX 规则列表
    ├── shadowrocket/             # .list  — Shadowrocket 规则列表
    ├── surfboard/                # .list  — Surfboard 规则列表
    ├── surfboard-txt/            # .txt   — Surfboard 文本规则
    ├── egern/                    # .yaml  — Egern 规则
    ├── exclave/                  # .list  — Exclave 路由规则
    ├── Gins-Icons.json           # 图标集
    └── ruleset/
        ├── geoip.mmdb            # MaxMind GeoIP 数据库
        └── geoasn.mmdb           # MaxMind ASN 数据库
```

## 引用格式

### Raw (GitHub)

```
https://raw.githubusercontent.com/DonJone/GinsRule-git/master/rules/{client}/{category}/{name}.{ext}
```

示例：

```
# Sing-box 代理规则
https://raw.githubusercontent.com/DonJone/GinsRule-git/master/rules/sing-box/proxy/apple.srs
https://raw.githubusercontent.com/DonJone/GinsRule-git/master/rules/sing-box/reject/ads.srs

# Mihomo 规则
https://raw.githubusercontent.com/DonJone/GinsRule-git/master/rules/mihomo/proxy/google.mrs

# GeoIP 数据库
https://raw.githubusercontent.com/DonJone/GinsRule-git/master/rules/ruleset/geoip.mmdb
```

### jsDelivr CDN

```
https://cdn.jsdelivr.net/gh/DonJone/GinsRule-git@master/rules/{client}/{category}/{name}.{ext}
```

示例：

```
# Sing-box
https://cdn.jsdelivr.net/gh/DonJone/GinsRule-git@master/rules/sing-box/proxy/apple.srs

# Mihomo
https://cdn.jsdelivr.net/gh/DonJone/GinsRule-git@master/rules/mihomo/proxy/google.mrs
```

## 分类说明

| 分类 | 规则数 | 说明 |
|------|--------|------|
| `proxy` | 66 | 需代理访问的域名/服务 |
| `direct` | 28 | 直连域名（国内服务） |
| `reject` | 6 | 拒绝/广告屏蔽 |
| `ip` | 8 | GeoIP 分流 |
| `asn` | 20 | ASN 网络分流 |
| `ai` | 6 | AI 服务分流 |

## 客户端格式

| 客户端 | 扩展名 | 类型 |
|--------|--------|------|
| sing-box | `.srs` | 二进制规则集 |
| Mihomo / Stash | `.mrs` | 二进制规则集 |
| Surge / QuantumultX / Shadowrocket / Surfboard / Exclave | `.list` | 规则列表 |
| Surfboard (Opt) | `.txt` | 文本规则 |
| Loon | `.lsr` | Loon 规则 |
| Egern | `.yaml` | YAML 规则 |

## 自动同步

GitHub Actions 每日 UTC 00:00 运行，通过 ETag 对比增量更新。详情见 [sync.yml](.github/workflows/sync.yml)。

## 鸣谢

- [IchimaruGin728](https://rules.ichimarugin728.dev) — 规则分发控制平面
- 上游规则源：Loyalsoldier, MetaCubeX, Yuu518, Blackmatrix7 等
