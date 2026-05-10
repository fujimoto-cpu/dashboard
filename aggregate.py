#!/usr/bin/env python3
"""
CORIN Dashboard — daily aggregator
Phase 2: 既存リポのHTMLリンク組み立て + brand-analysis ランダム抽出
       + trend-digest MD読み込み + CORIN手紙生成 + 天気取得
ローカル実行用。/ohayo の Step 1.5-D から起動される想定。
"""

import datetime
import json
import os
import random
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

# === パス設定 ===
HOME = Path.home()
CORIN_ROOT = HOME / "Documents/corin"
DASHBOARD_ROOT = HOME / "Documents/dashboard"
NOTES_DIR = CORIN_ROOT / "00_🏢 company/secretary/notes"
TREND_DIGEST_DIR = NOTES_DIR / "trend-digest"
XWATCH_DIR = CORIN_ROOT / "20_📂 Zettelkasten/x-watch"

# === 天気取得（wttr.in・APIキー不要） ===
def get_weather():
    """wttr.in を curl 経由で取得（macOSのPython SSL問題回避）"""
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "10", "https://wttr.in/Tokyo?format=j1"],
            capture_output=True, text=True, timeout=12
        )
        if result.returncode != 0 or not result.stdout:
            return None
        data = json.loads(result.stdout)
        cur = data["current_condition"][0]
        desc = cur.get("lang_ja", [{}])[0].get("value") or cur.get("weatherDesc", [{}])[0].get("value", "")
        return {"desc": desc, "temp": cur["temp_C"]}
    except Exception as e:
        print(f"[weather] failed: {e}", file=sys.stderr)
        return None

# === ブランド分析ランダム1件 ===
def pick_brand():
    if not NOTES_DIR.exists():
        return None
    candidates = list(NOTES_DIR.glob("*-brand-analysis.html"))
    if not candidates:
        return None
    chosen = random.choice(candidates)
    try:
        html = chosen.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    # ブランド名抽出（hero-title優先、なければtitleタグ）
    hero_title = re.search(r'<h1[^>]*class=["\'][^"\']*hero-title[^"\']*["\'][^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
    if hero_title:
        raw = re.sub(r"<[^>]+>", " ", hero_title.group(1))
        name = re.sub(r"\s+", " ", raw).strip()
    else:
        title_match = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
        if title_match:
            name = title_match.group(1).strip()
            # 「— ブランド分析レポート」「- Brand Analysis」等を除去
            name = re.sub(r"\s*[-–—].*?(ブランド分析|Brand Analysis).*$", "", name, flags=re.IGNORECASE).strip()
        else:
            name = chosen.stem.replace("-brand-analysis", "").replace("-", " ").title()

    # タグライン（hero-sub）
    sub_match = re.search(r'<p[^>]*class=["\'][^"\']*hero-sub[^"\']*["\'][^>]*>(.*?)</p>', html, re.IGNORECASE | re.DOTALL)
    if sub_match:
        raw = re.sub(r"<[^>]+>", " ", sub_match.group(1))
        tagline = re.sub(r"\s+", " ", raw).strip()
    else:
        tagline = name

    # ヒーロー画像（リモートURL優先・ローカルパスは除外）
    image_url = None
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE):
        src = m.group(1)
        if src.startswith(("http://", "https://")):
            image_url = src
            break

    # INSIGHT タイトル ランダム1件（span/div両対応）
    insight_titles = re.findall(
        r'<(?:span|div)[^>]*class=["\'][^"\']*insight-title[^"\']*["\'][^>]*>([^<]+)</(?:span|div)>',
        html, re.IGNORECASE
    )
    if insight_titles:
        insight = random.choice(insight_titles).strip()
    else:
        # fallback: insight クラス全般
        any_insight = re.search(
            r'<[^>]+class=["\'][^"\']*insight[^"\']*["\'][^>]*>(.*?)</[a-z]+>',
            html, re.IGNORECASE | re.DOTALL
        )
        if any_insight:
            raw = re.sub(r"<[^>]+>", " ", any_insight.group(1))
            insight = re.sub(r"\s+", " ", raw).strip()[:140]
        else:
            insight = "詳しくはObsidianで全文を読んでね。"

    return {
        "name": name,
        "tagline": tagline,
        "insight": insight,
        "image_url": image_url,
        "local_path": f"00_🏢 company/secretary/notes/{chosen.name}",
    }

# === trend-digest MD ===
def read_trend_digest(today_str):
    path = TREND_DIGEST_DIR / f"{today_str}.md"
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    # 各カテゴリの先頭タイトル（##や### 直下のboldタイトル）を拾う
    items = re.findall(r"\*\*\[([^\]]+)\]\*\*", text)
    if not items:
        items = re.findall(r"^###?\s+(.+)$", text, re.MULTILINE)
    items = items[:6]
    if not items:
        return None
    return {"summary": "<br>".join(f"• {i}" for i in items)}

# === x-watch MD ===
def read_xwatch(today_str, hour):
    timing = "morning" if hour < 12 else "evening"
    path = XWATCH_DIR / f"{today_str}-{timing}.md"
    if not path.exists():
        # fallback: 直近のファイル
        if XWATCH_DIR.exists():
            files = sorted(XWATCH_DIR.glob("*.md"), reverse=True)
            if files:
                path = files[0]
            else:
                return None
        else:
            return None
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    # ハイライトTOP3 抽出（callout内 or リスト）
    highlights = re.findall(r"🥇\s*\[?([^\]\n]+)\]?", text)
    highlights += re.findall(r"🥈\s*\[?([^\]\n]+)\]?", text)
    highlights += re.findall(r"🥉\s*\[?([^\]\n]+)\]?", text)
    if not highlights:
        highlights = [m.strip() for m in re.findall(r"^-\s+(.+)$", text, re.MULTILINE)[:3]]
    if not highlights:
        return None
    return {"summary": "<br>".join(f"• {h.strip()}" for h in highlights[:5])}

# === CORIN手紙 ===
ASCII_ARTS = [
    " /) /)\n(  • •)\n⊃ 🍵",
    " /)/) ˚｡´☆\n( . .) ☆´˚｡\n⊃  ❤️ ☆",
    "  (\\(\\\n(o- .•)❤️\no_(\")(\" )",
    " /)/)\n( ≧ ▽≦)\n⊃  🎶",
]

def make_letter(weather, brand, today_dt, weekday_jp):
    is_weekend = today_dt.weekday() >= 5
    is_monday = today_dt.weekday() == 0
    is_friday = today_dt.weekday() == 4

    greeting_pool = [
        "ゆりこ、おはよ！",
        "ゆりこ！おはよう〜",
        "おはよ、ゆりこ。",
    ]
    greeting = random.choice(greeting_pool)

    body_lines = []
    if weather:
        body_lines.append(f"今日は{weather['desc']}、{weather['temp']}度。")

    if is_monday:
        body_lines.append("月曜だね。今週の3つ、決めにいこ。/monday 待ってるよ。")
    elif is_friday:
        body_lines.append("金曜日。土日に持ち越さないこと、整理しよ。")
    elif is_weekend:
        body_lines.append("週末。仕事は把握だけ、自分のために動こ。")
    else:
        body_lines.append("今日も70%ルールでいこう。完璧じゃなくていいよ。")

    if brand:
        body_lines.append(f"今日の倉庫から：<strong>{brand['name']}</strong> のこと思い出してね。")

    body_lines.append("いってらっしゃい！")

    body_html = "<br>".join(body_lines)
    html = (
        f"<p class='letter-greeting'>{greeting}</p>"
        f"<p class='letter-text'>{body_html}</p>"
        f"<p class='letter-sign'>— CORIN</p>"
    )
    return {"ascii": random.choice(ASCII_ARTS), "html": html}

# === git commit & push ===
def git_push():
    if not (DASHBOARD_ROOT / ".git").exists():
        print("[git] not a git repo, skipping push", file=sys.stderr)
        return
    try:
        subprocess.run(["git", "-C", str(DASHBOARD_ROOT), "add", "data.js"], check=True)
        # diff があれば commit
        result = subprocess.run(
            ["git", "-C", str(DASHBOARD_ROOT), "diff", "--cached", "--quiet"]
        )
        if result.returncode == 0:
            print("[git] no changes to commit")
            return
        subprocess.run(
            ["git", "-C", str(DASHBOARD_ROOT), "commit", "-m",
             f"auto: daily update {datetime.date.today().isoformat()}"],
            check=True
        )
        subprocess.run(["git", "-C", str(DASHBOARD_ROOT), "push"], check=True)
        print("[git] pushed")
    except subprocess.CalledProcessError as e:
        print(f"[git] failed: {e}", file=sys.stderr)

# === MEADOW. セクション読み込み ===
def read_meadow(today_dt):
    """🦋 MEADOW. の進捗情報を読み込む"""
    meadow_dir = CORIN_ROOT / "01_🏠 private/meadow"
    if not meadow_dir.exists():
        return None

    month_str = today_dt.strftime("%Y-%m")
    iso_year, iso_week, _ = today_dt.isocalendar()
    week_str = f"{iso_year}-W{iso_week:02d}"

    # 今月のテーマ会
    theme_party_file = meadow_dir / "theme-party" / f"{month_str}.md"
    theme_party_status = "未企画"
    if theme_party_file.exists():
        theme_party_status = "企画済み"

    # 最新Magazine
    magazine_dir = meadow_dir / "magazine"
    latest_magazine = None
    if magazine_dir.exists():
        vol_dirs = sorted([d for d in magazine_dir.iterdir() if d.is_dir() and d.name.startswith("VOL-")])
        if vol_dirs:
            latest_magazine = vol_dirs[-1].name

    # 今週のダッシュボード
    dashboard_file = meadow_dir / "dashboard" / f"{week_str}.md"
    this_week_dashboard = dashboard_file.exists()

    summary_lines = []
    summary_lines.append(f"🍡 今月のテーマ会: {theme_party_status}")
    summary_lines.append(f"📖 最新Magazine: {latest_magazine or '未生成'}")
    summary_lines.append(f"📋 今週のダッシュボード: {'更新済み' if this_week_dashboard else '/lifeで生成'}")

    return {
        "summary": "  /  ".join(summary_lines),
        "theme_party_status": theme_party_status,
        "theme_party_file": str(theme_party_file) if theme_party_file.exists() else None,
        "latest_magazine": latest_magazine,
        "this_week_dashboard": this_week_dashboard,
    }


# === メイン ===
def main():
    today_dt = datetime.date.today()
    today_str = today_dt.strftime("%Y-%m-%d")
    weekday_jp = ["月", "火", "水", "木", "金", "土", "日"][today_dt.weekday()]
    hour = datetime.datetime.now().hour

    print(f"=== CORIN Dashboard aggregate {today_str}（{weekday_jp}）===")

    weather = get_weather()
    print(f"[weather] {weather}")
    brand = pick_brand()
    print(f"[brand] {brand['name'] if brand else 'none'}")
    trend = read_trend_digest(today_str)
    print(f"[trend-digest] {'found' if trend else 'none'}")
    xwatch = read_xwatch(today_str, hour)
    print(f"[xwatch] {'found' if xwatch else 'none'}")
    meadow = read_meadow(today_dt)
    print(f"[meadow] {meadow['summary'] if meadow else 'none'}")

    letter = make_letter(weather, brand, today_dt, weekday_jp)

    data = {
        "date": today_str,
        "letter": letter,
        "ai": {
            "summary": f"X AIトレンド本日のレポート（HTMLで全10件解説）"
        },
        "fashion": {
            "summary": f"日本・韓国・世界のトレンド計6本（HTMLで全件解説）"
        },
        "trend": trend or {"summary": "（本日のtrend-digestはまだ作成されていません）"},
        "xwatch": xwatch or {"summary": "Obsidian x-watch/ で確認してね"},
        "brand": brand or {
            "name": "（brand-analysis未検出）",
            "tagline": "/brand-analysis でブランド分析HTMLを蓄積するとここに登場",
            "insight": "",
            "image_url": None,
            "local_path": "",
        },
        "ip": {"url": "https://fujimoto-cpu.github.io/ip-news-reporter/"},
        "meadow": meadow or {"summary": "🦋 MEADOW. ディレクトリ未検出"},
    }

    output = DASHBOARD_ROOT / "data.js"
    output.write_text(
        f"window.CORIN_DATA = {json.dumps(data, ensure_ascii=False, indent=2)};\n",
        encoding="utf-8"
    )
    print(f"✅ data.js generated: {output}")

    # 自動 git commit & push（オプション）
    if os.environ.get("DASHBOARD_AUTO_PUSH", "1") == "1":
        git_push()

if __name__ == "__main__":
    main()
