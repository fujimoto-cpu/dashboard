#!/usr/bin/env python3
"""
take_thumbnails.py — hub.html 用サムネイル一括撮影

- data.js から recent_html を読み取り、html_path を file:// として Chrome headless で撮影
- 1200x750 viewport で PNG 撮影 → cwebp で WebP 変換 → thumbs/ に保存
- ファイル名は wiki 値の sanitized 版

Usage:
  python3 scripts/take_thumbnails.py            # 既存スキップ
  python3 scripts/take_thumbnails.py --force    # 再撮影
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_JS = ROOT / "data.js"
THUMBS_DIR = ROOT / "thumbs"

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
VIEWPORT = "1200,750"
WEBP_QUALITY = "75"


def parse_recent_html(data_js_text: str) -> list[dict]:
    """data.js から JS の object literal を抽出して dict 化"""
    # window.CORIN_DATA = { ... }; の中身を抜く
    m = re.search(r"window\.CORIN_DATA\s*=\s*(\{.*\})\s*;?\s*$", data_js_text, re.DOTALL)
    if not m:
        raise RuntimeError("data.js: window.CORIN_DATA = {...} が見つからない")
    raw = m.group(1)
    obj = json.loads(raw)
    return obj.get("recent_html", [])


def sanitize_filename(name: str) -> str:
    """wiki 値をファイル名安全に。日本語含む文字は _ 置換"""
    s = re.sub(r"[^A-Za-z0-9_\-]", "_", name)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "untitled"


def to_file_url(path: str) -> str:
    """ローカルパス → file:// URL（絵文字・スペース・日本語をエスケープ）"""
    if path.startswith("file://"):
        return path
    # ファイル存在しなければスキップ
    if not Path(path).exists():
        return ""
    quoted = urllib.parse.quote(path, safe="/")
    return f"file://{quoted}"


def take_screenshot(file_url: str, out_png: Path) -> bool:
    """Chrome headless で PNG 撮影。成功 True/失敗 False"""
    cmd = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-sandbox",
        "--virtual-time-budget=2000",
        f"--window-size={VIEWPORT}",
        f"--screenshot={out_png}",
        file_url,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=30)
        if proc.returncode != 0:
            print(f"  ❌ Chrome 失敗: rc={proc.returncode}")
            return False
        return out_png.exists() and out_png.stat().st_size > 1000
    except subprocess.TimeoutExpired:
        print(f"  ⏱ Chrome タイムアウト")
        return False


def png_to_webp(png_path: Path, webp_path: Path) -> bool:
    """cwebp で PNG → WebP 変換（quality 75・縮小なし）"""
    cmd = ["cwebp", "-q", WEBP_QUALITY, "-resize", "800", "0", str(png_path), "-o", str(webp_path)]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=15)
        return proc.returncode == 0 and webp_path.exists()
    except Exception as e:
        print(f"  ❌ cwebp 失敗: {e}")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="既存サムネも上書き")
    args = ap.parse_args()

    THUMBS_DIR.mkdir(exist_ok=True)
    data_js_text = DATA_JS.read_text(encoding="utf-8")
    items = parse_recent_html(data_js_text)

    print(f"📷 recent_html: {len(items)} 件")
    success = 0
    skipped = 0
    failed = 0

    for i, item in enumerate(items, 1):
        wiki = item.get("wiki") or ""
        html_path = item.get("html_path") or ""
        if not wiki or not html_path:
            print(f"[{i}/{len(items)}] ⏭ wiki または html_path 欠損 → skip")
            failed += 1
            continue

        fname = sanitize_filename(wiki)
        out_webp = THUMBS_DIR / f"{fname}.webp"

        if out_webp.exists() and not args.force:
            print(f"[{i}/{len(items)}] ⏭ 既存: {fname}.webp")
            skipped += 1
            continue

        file_url = to_file_url(html_path)
        if not file_url:
            print(f"[{i}/{len(items)}] ❌ HTML ファイル不存在: {html_path}")
            failed += 1
            continue

        print(f"[{i}/{len(items)}] 📸 {wiki[:50]}")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_png = Path(tmp.name)

        try:
            if not take_screenshot(file_url, tmp_png):
                failed += 1
                continue
            if not png_to_webp(tmp_png, out_webp):
                failed += 1
                continue
            size_kb = out_webp.stat().st_size // 1024
            print(f"  ✅ {fname}.webp ({size_kb} KB)")
            success += 1
        finally:
            if tmp_png.exists():
                tmp_png.unlink()

    print(f"\n📊 結果: ✅ {success} 件 / ⏭ {skipped} 件 / ❌ {failed} 件")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
