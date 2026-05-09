#!/usr/bin/env python3
"""Sync rule files from Gins-Rules control plane to local repository.

Discovers rules by parsing the homepage HTML (not hardcoded),
detects changes via ETag comparison, and downloads only updated files.
"""

import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape
from pathlib import Path

import requests

BASE_URL = "https://rules.ichimarugin728.dev"
RULES_DIR = Path("rules")
MANIFEST_FILE = Path("manifest.json")
HEADERS = {"User-Agent": "GinsRules-Sync/1.0 (+https://github.com)"}
MAX_WORKERS = 8
REQUEST_TIMEOUT = 30

CLIENTS = {
    "sing-box":      {"ext": ".srs",  "pattern": "/ruleset/singbox/{cat}/{name}.srs"},
    "mihomo":        {"ext": ".mrs",  "pattern": "/ruleset/mihomo/{cat}/{name}.mrs"},
    "stash":         {"ext": ".mrs",  "pattern": "/ruleset/stash/{cat}/{name}.mrs"},
    "surge":         {"ext": ".list", "pattern": "/ruleset/surge/{cat}/{name}.list"},
    "loon":          {"ext": ".lsr",  "pattern": "/ruleset/loon/{cat}/{name}.lsr"},
    "quantumultx":   {"ext": ".list", "pattern": "/ruleset/quantumultx/{cat}/{name}.list"},
    "shadowrocket":  {"ext": ".list", "pattern": "/ruleset/shadowrocket/{cat}/{name}.list"},
    "surfboard":     {"ext": ".list", "pattern": "/ruleset/surfboard/{cat}/{name}.list"},
    "surfboard-txt": {"ext": ".txt",  "pattern": "/ruleset/surfboard/{cat}/{name}.txt"},
    "egern":         {"ext": ".yaml", "pattern": "/ruleset/egern/{cat}/{name}.yaml"},
    "exclave":       {"ext": ".list", "pattern": "/ruleset/exclave/{cat}/{name}.list"},
}

EXTRAS = [
    "/ruleset/geoip.mmdb",
    "/ruleset/geoasn.mmdb",
    "/Gins-Icons.json",
]


def discover_rules():
    """Parse homepage HTML to extract all {category, name} pairs."""
    print("→ Fetching homepage to discover rules...")
    resp = requests.get(BASE_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    html = resp.text

    # Astro props use HTML-encoded JSON like props="{&quot;name&quot;:...}"
    props_pattern = re.compile(r'props="({[^}]+})"')
    rules = {}
    for raw in props_pattern.findall(html):
        try:
            data = json.loads(unescape(raw))
            if "name" in data and "category" in data:
                cat = data["category"][1]
                name = data["name"][1]
                # Strip extension to get base name
                base = re.sub(r"\.(txt|json|yaml|list)$", "", name)
                rules.setdefault(cat, set()).add(base)
        except (json.JSONDecodeError, IndexError, KeyError):
            continue

    total = sum(len(v) for v in rules.values())
    print(f"  Discovered {total} rules across {len(rules)} categories:")
    for cat in sorted(rules):
        print(f"    {cat}: {len(rules[cat])} rules")
    return rules


def build_urls(rules):
    """Build download URLs for all client×rule combinations."""
    urls = {}
    for client, cfg in CLIENTS.items():
        for cat, names in rules.items():
            for name in names:
                url_path = cfg["pattern"].format(cat=cat, name=name)
                url = f"{BASE_URL}{url_path}"
                local_path = RULES_DIR / client
                if client == "surfboard-txt":
                    local_path = RULES_DIR / client / cat / f"{name}.txt"
                else:
                    local_path = RULES_DIR / client / cat / f"{name}{cfg['ext']}"
                urls[url] = str(local_path)

    for extra in EXTRAS:
        url = f"{BASE_URL}{extra}"
        local_path = RULES_DIR / extra.lstrip("/")
        urls[url] = str(local_path)

    print(f"→ Built {len(urls)} URLs to check")
    return urls


def load_manifest():
    """Load existing ETag manifest."""
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE) as f:
            return json.load(f)
    return {}


def save_manifest(manifest):
    """Persist ETag manifest sorted by URL."""
    with open(MANIFEST_FILE, "w") as f:
        json.dump(dict(sorted(manifest.items())), f, indent=2)
    print(f"  Manifest saved ({len(manifest)} entries)")


def check_and_download(url, local_path, old_etag):
    """HEAD a URL, compare ETag, download if changed/new. Returns (url, old_etag, new_etag_or_None, changed_bool)."""
    try:
        head = requests.head(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if head.status_code == 404:
            return (url, old_etag, None, False)
        head.raise_for_status()
        new_etag = head.headers.get("etag", "").strip('"')
    except requests.RequestException as e:
        print(f"  ⚠ HEAD failed for {url}: {e}")
        return (url, old_etag, None, False)

    if old_etag and new_etag and old_etag == new_etag:
        return (url, old_etag, new_etag, False)

    # Download
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(resp.content)
        # Re-read etag from GET response in case HEAD didn't have one
        final_etag = resp.headers.get("etag", new_etag or "").strip('"')
        status = "UPDATED" if old_etag else "NEW"
        print(f"  [{status}] {url} → {local_path}")
        return (url, old_etag, final_etag, True)
    except requests.RequestException as e:
        print(f"  ✗ Download failed for {url}: {e}")
        return (url, old_etag, None, False)


CATEGORY_LABELS = {
    "proxy":  "需代理访问的域名/服务",
    "direct": "直连域名（国内服务）",
    "reject": "拒绝/广告屏蔽",
    "ip":     "GeoIP 分流",
    "asn":    "ASN 网络分流",
    "ai":     "AI 服务分流",
}

README_FILE = Path("README.md")


def count_files():
    """Count downloaded files per client. Returns {client: count}."""
    counts = {}
    if RULES_DIR.exists():
        for d in sorted(RULES_DIR.iterdir()):
            if d.is_dir():
                count = sum(1 for _ in d.rglob("*") if _.is_file())
                if count > 0:
                    counts[d.name] = count
    return counts


def update_readme(rules):
    """Replace auto-marked sections in README with live data."""
    if not README_FILE.exists():
        return

    text = README_FILE.read_text()

    # --- Summary line ---
    total_rules = sum(len(v) for v in rules.values())
    num_cats = len(rules)
    summary_new = (
        f"每日自动从 [Gins-Rules](https://rules.ichimarugin728.dev) "
        f"同步代理规则文件，覆盖 **11 个客户端格式**、"
        f"**{num_cats} 个分类**、**{total_rules} 条规则**。"
    )
    text = re.sub(
        r"<!-- AUTO_START: summary -->.*<!-- AUTO_END: summary -->",
        f"<!-- AUTO_START: summary -->\n{summary_new}\n<!-- AUTO_END: summary -->",
        text,
        flags=re.DOTALL,
    )

    # --- Category table ---
    table_lines = [
        "| 分类 | 规则数 | 说明 |",
        "|------|--------|------|",
    ]
    for cat in sorted(rules):
        label = CATEGORY_LABELS.get(cat, "")
        table_lines.append(f"| `{cat}` | {len(rules[cat])} | {label} |")
    table_str = "\n".join(table_lines)
    text = re.sub(
        r"<!-- AUTO_START: categories -->.*<!-- AUTO_END: categories -->",
        f"<!-- AUTO_START: categories -->\n{table_str}\n<!-- AUTO_END: categories -->",
        text,
        flags=re.DOTALL,
    )

    # --- Last sync timestamp ---
    now = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    sync_badge = f"> 最近同步: {now} · 共 {total_rules} 条规则 · {sum(count_files().values())} 个文件"
    if "<!-- AUTO_START: sync_time -->" in text:
        text = re.sub(
            r"<!-- AUTO_START: sync_time -->.*<!-- AUTO_END: sync_time -->",
            f"<!-- AUTO_START: sync_time -->\n{sync_badge}\n<!-- AUTO_END: sync_time -->",
            text,
            flags=re.DOTALL,
        )
    else:
        # Insert after summary marker
        text = text.replace(
            "<!-- AUTO_END: summary -->",
            f"<!-- AUTO_END: summary -->\n\n<!-- AUTO_START: sync_time -->\n{sync_badge}\n<!-- AUTO_END: sync_time -->",
        )

    README_FILE.write_text(text)
    print("  README updated")


def main():
    start_time = time.time()

    # 1. Discover rules from homepage
    rules = discover_rules()
    if not rules:
        print("✗ No rules discovered — site structure may have changed")
        sys.exit(1)

    # 2. Build URL list
    urls = build_urls(rules)

    # 3. Load manifest
    manifest = load_manifest()
    print(f"→ Loaded manifest with {len(manifest)} cached ETags")

    # 4. Check and download in parallel
    changed = 0
    skipped = 0
    not_found = 0
    new_manifest = {}
    print(f"→ Checking {len(urls)} files ({MAX_WORKERS} workers)...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(check_and_download, url, path, manifest.get(url)): url
            for url, path in urls.items()
        }
        for future in as_completed(futures):
            url, old_etag, new_etag, was_changed = future.result()
            if new_etag:
                new_manifest[url] = new_etag
            else:
                # Preserve old etag for files that still 404
                if old_etag:
                    new_manifest[url] = old_etag

            if was_changed:
                changed += 1
            elif new_etag is None and not old_etag:
                not_found += 1
            else:
                skipped += 1

    # 5. Save manifest
    save_manifest(new_manifest)

    # 6. Update README with live counts
    update_readme(rules)

    elapsed = time.time() - start_time
    print(f"\n→ Done in {elapsed:.1f}s — {changed} changed, {skipped} unchanged, {not_found} not found")

    # 7. Exit code: 0 = no changes, 1 = changes detected
    if changed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
