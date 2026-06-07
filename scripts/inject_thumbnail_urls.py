#!/usr/bin/env python3
"""
inject_thumbnail_urls.py — data.js の recent_html に thumbnail_url を埋め込む

- thumbs/ にある WebP と wiki 名（sanitized）をマッチング
- 該当があれば "thumbnail_url": "thumbs/<sanitized>.webp" を追加
- 無ければスキップ
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_JS = ROOT / "data.js"
THUMBS_DIR = ROOT / "thumbs"


def sanitize_filename(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_\-]", "_", name)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "untitled"


def main():
    text = DATA_JS.read_text(encoding="utf-8")
    m = re.search(r"(window\.CORIN_DATA\s*=\s*)(\{.*\})(\s*;?\s*)$", text, re.DOTALL)
    if not m:
        print("❌ data.js parse 失敗"); return 1
    prefix, raw, suffix = m.group(1), m.group(2), m.group(3) or ";\n"
    obj = json.loads(raw)
    items = obj.get("recent_html") or []
    if not items:
        print("❌ recent_html 空"); return 1

    matched = 0
    missing = 0
    for item in items:
        wiki = item.get("wiki") or ""
        if not wiki:
            continue
        webp = THUMBS_DIR / f"{sanitize_filename(wiki)}.webp"
        if webp.exists():
            item["thumbnail_url"] = f"thumbs/{webp.name}"
            matched += 1
        else:
            # 既存の thumbnail_url を消しておく（再生成防止）
            item.pop("thumbnail_url", None)
            missing += 1

    new_json = json.dumps(obj, ensure_ascii=False, indent=2)
    new_text = f"{prefix}{new_json};\n"
    DATA_JS.write_text(new_text, encoding="utf-8")
    print(f"✅ 反映: {matched} 件 / ⏭ 該当WebP無し: {missing} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
