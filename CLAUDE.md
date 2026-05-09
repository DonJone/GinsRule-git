# CLAUDE.md

## Project overview

GinsRules Sync — daily automated mirror of proxy rule files from `rules.ichimarugin728.dev`. A single `scripts/sync_rules.py` script discovers rules, checks for updates via ETag, and downloads changes. GitHub Actions runs it on a cron.

## Architecture

```
Homepage HTML (Astro) → parse props JSON → {category, name} pairs
                                            ↓
                  URL map: /ruleset/{client}/{cat}/{name}.{ext}
                                            ↓
                  HEAD each URL → compare ETag with manifest.json
                                            ↓
                  ETag changed/missing → GET → save to rules/{client}/{cat}/
```

## Key files

| File | Purpose |
|------|---------|
| `scripts/sync_rules.py` | Core sync logic — the only script |
| `manifest.json` | ETag cache, auto-maintained by the script |
| `.github/workflows/sync.yml` | Daily cron + manual trigger |
| `rules/` | Downloaded rule files, committed to repo |

## How sync_rules.py works

1. **Discovery**: Fetches homepage, regex-extracts Astro `props="..."` attributes, parses as JSON. Filters for entries with both `name` and `category` fields. Strips `.txt` extension from names to get base names. **No hardcoded rule list** — adapts automatically when upstream adds/removes rules.

2. **URL building**: Maps each `{category, name}` through the client config (see `CLIENTS` dict) plus `EXTRAS` for mmdb/icon files.

3. **Change detection**: For each URL, sends HEAD request, compares `ETag` header against `manifest.json`. Same ETag → skip. Different or new → GET download.

4. **Exit code**: `0` = no changes, `1` = changes detected. Workflow uses this to decide whether to commit.

## Adding a new client format

Add an entry to the `CLIENTS` dict in `scripts/sync_rules.py`:

```python
"new-client": {"ext": ".ext", "pattern": "/ruleset/newclient/{cat}/{name}.ext"},
```

The script will automatically pick it up on next run.

## Adding extra files (like mmdb)

Add the URL path to the `EXTRAS` list:

```python
EXTRAS = [
    "/ruleset/geoip.mmdb",
    "/ruleset/geoasn.mmdb",
    "/Gins-Icons.json",
    "/new-file.dat",  # added
]
```

## Upstream site changes

If the homepage HTML structure changes and rule discovery breaks:
1. Fetch the new HTML: `curl -s https://rules.ichimarugin728.dev > /tmp/gins.html`
2. Look for how rule names/categories are embedded (currently Astro `props` JSON)
3. Update the regex/parsing logic in `discover_rules()`

## Manual sync

```bash
pip install requests
python scripts/sync_rules.py
```

## Workflow permissions

The workflow needs `contents: write` to push commits. This is configured in `sync.yml`.
