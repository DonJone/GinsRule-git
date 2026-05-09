# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

GinsRules — multi-client proxy rule distribution. This repo stores auto-generated rule files for 12 proxy platforms, synced from `rules.ichimarugin728.dev`. All files are committed as-is; there is no build/test/lint step.

## Repository structure

```
{client}/{category}/{name}.{ext}   — rule files
ruleset/                           — shared binary files (geoip.mmdb, geoasn.mmdb)
Gins-Icons.json                    — 8917 icon URL mappings (JSON list)
```

## Client platforms and formats

| Client | Extension | Format |
|--------|-----------|--------|
| surge | `.list` | Text: `TYPE,value` (comma-separated) |
| surfboard | `.list` | Text: `TYPE,value` |
| shadowrocket | `.list` | Text: `TYPE,value` |
| quantumultx | `.list` | Text: `TYPE,value,policy` (3-field) |
| exclave | `.list` | Text: `TYPE,value` |
| loon | `.lsr` | Text-based rules |
| surfboard-txt | `.txt` | Text-based rules |
| egern | `.yaml` | YAML structured rules |
| mihomo | `.mrs` | Binary rule set format |
| stash | `.mrs` | Binary rule set format |
| sing-box | `.srs` | Binary rule set format |

## Rule categories

- `ai/` — AI service routing (openai, claude, gemini, copilot, apple-intelligence, ai-other)
- `asn/` — ASN-based routing (google, apple, microsoft, amazon, cloudflare, etc.)
- `direct/` — Direct-connect rules (Chinese services: alibaba, tencent, bilibili, etc.)
- `ip/` — GeoIP and private IP routing (cn, !cn, jp, sg, private, us, hk, tw)
- `proxy/` — Proxied service routing (youtube, telegram, tiktok, twitter, etc.)
- `reject/` — Block/reject rules (ads, tracking, privacy, tencentvideo)

Not all categories exist for all clients. `quantumultx` and `surfboard-txt` have fewer categories (no asn, no ip).

## How files are updated

Files are synced by `scripts/sync_rules.py` in the parent repo (`/home/don/code-git/my/`). That script discovers rules from the upstream homepage, compares ETags against a manifest, and downloads changed files. GitHub Actions runs it on a cron. The resulting files land here and are auto-committed.

## Manual operations

- **Regenerate from upstream**: Run `python scripts/sync_rules.py` from the parent repo, not this one.
- **Add a new client format**: Edit `CLIENTS` dict in the parent repo's sync script.
- **Add/remove rules**: Changes flow from upstream `rules.ichimarugin728.dev` — this repo is the mirror, not the source.

## Important notes

- `.mrs` and `.srs` files are binary — use `git diff --binary` or `git diff --stat` to review changes without garbled output.
- `Gins-Icons.json` is a JSON list of `{name, url, source, theme}` objects, not a keyed dict.
- All commits to this repo are automated. Manual commits should be rare and intentional.
