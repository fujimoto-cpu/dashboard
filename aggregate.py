#!/usr/bin/env python3
"""
CORIN Dashboard v2 — daily aggregator
- 天気 / brand-analysis / trend-digest / x-watch / MEADOW.
- v2追加: /collection 連携で推し画像 / 今夜の楽しみ / 今日の一枚 / コレクション統計
"""

import datetime
import json
import os
import random
import re
import subprocess
import sys
from pathlib import Path

# === パス設定 ===
HOME = Path.home()
CORIN_ROOT = HOME / "Documents/corin"
DASHBOARD_ROOT = HOME / "Documents/dashboard"
NOTES_DIR = CORIN_ROOT / "00_🏢 company/secretary/notes"
TREND_DIGEST_DIR = NOTES_DIR / "trend-digest"
XWATCH_DIR = CORIN_ROOT / "20_📂 Zettelkasten/x-watch"
DAILY_NOTE_DIR = CORIN_ROOT / "03_📒 Daily Note/daily"
COLLECTION_DATA = CORIN_ROOT / "01_🏠 private/meadow/collection/data.json"
OSHI_HISTORY = DASHBOARD_ROOT / "oshi_history.json"
PROJECTS_OVERVIEW = CORIN_ROOT / "30_🧠 context/projects-overview.md"
PROJECTS_DIR = CORIN_ROOT / "00_🏢 company/projects"
HTML_INDEX = CORIN_ROOT / "00_🏢 company/secretary/outputs/INDEX.md"
ZETTEL_DIR = CORIN_ROOT / "20_📂 Zettelkasten"
LINKS_CONFIG = DASHBOARD_ROOT / "links_config.json"

# === 天気取得 ===
WEATHER_ICONS = [
    (r"晴|sunny|clear", "☀️"),
    (r"雨|rain|shower", "🌧"),
    (r"雪|snow", "❄️"),
    (r"雷|thunder", "⛈"),
    (r"曇|cloud|overcast", "☁️"),
    (r"霧|fog|mist", "🌫"),
]

def weather_icon(desc):
    if not desc:
        return "☁️"
    low = desc.lower()
    for pattern, icon in WEATHER_ICONS:
        if re.search(pattern, low):
            return icon
    return "☁️"

def get_weather():
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
        temp = cur["temp_C"]
        return {"desc": desc, "temp": temp, "icon": weather_icon(desc)}
    except Exception as e:
        print(f"[weather] failed: {e}", file=sys.stderr)
        return None

# === ブランド分析 ===
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

    hero_title = re.search(r'<h1[^>]*class=["\'][^"\']*hero-title[^"\']*["\'][^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
    if hero_title:
        raw = re.sub(r"<[^>]+>", " ", hero_title.group(1))
        name = re.sub(r"\s+", " ", raw).strip()
    else:
        title_match = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
        if title_match:
            name = title_match.group(1).strip()
            name = re.sub(r"\s*[-–—].*?(ブランド分析|Brand Analysis).*$", "", name, flags=re.IGNORECASE).strip()
        else:
            name = chosen.stem.replace("-brand-analysis", "").replace("-", " ").title()

    sub_match = re.search(r'<p[^>]*class=["\'][^"\']*hero-sub[^"\']*["\'][^>]*>(.*?)</p>', html, re.IGNORECASE | re.DOTALL)
    if sub_match:
        raw = re.sub(r"<[^>]+>", " ", sub_match.group(1))
        tagline = re.sub(r"\s+", " ", raw).strip()
    else:
        tagline = name

    image_url = None
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE):
        src = m.group(1)
        if src.startswith(("http://", "https://")):
            image_url = src
            break

    insight_titles = re.findall(
        r'<(?:span|div)[^>]*class=["\'][^"\']*insight-title[^"\']*["\'][^>]*>([^<]+)</(?:span|div)>',
        html, re.IGNORECASE
    )
    if insight_titles:
        insight = random.choice(insight_titles).strip()
    else:
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

# === trend-digest ===
def read_trend_digest(today_str):
    path = TREND_DIGEST_DIR / f"{today_str}.md"
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    items = re.findall(r"\*\*\[([^\]]+)\]\*\*", text)
    if not items:
        items = re.findall(r"^###?\s+(.+)$", text, re.MULTILINE)
    items = items[:6]
    if not items:
        return None
    return {"summary": "<br>".join(f"• {i}" for i in items)}

# === x-watch ===
def read_xwatch(today_str, hour):
    timing = "morning" if hour < 12 else "evening"
    path = XWATCH_DIR / f"{today_str}-{timing}.md"
    if not path.exists():
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
    highlights = re.findall(r"🥇\s*\[?([^\]\n]+)\]?", text)
    highlights += re.findall(r"🥈\s*\[?([^\]\n]+)\]?", text)
    highlights += re.findall(r"🥉\s*\[?([^\]\n]+)\]?", text)
    if not highlights:
        highlights = [m.strip() for m in re.findall(r"^-\s+(.+)$", text, re.MULTILINE)[:3]]
    if not highlights:
        return None
    return {"summary": "<br>".join(f"• {h.strip()}" for h in highlights[:5])}

# === MEADOW. ===
def read_meadow(today_dt):
    meadow_dir = CORIN_ROOT / "01_🏠 private/meadow"
    if not meadow_dir.exists():
        return None

    month_str = today_dt.strftime("%Y-%m")
    iso_year, iso_week, _ = today_dt.isocalendar()
    week_str = f"{iso_year}-W{iso_week:02d}"

    theme_party_file = meadow_dir / "theme-party" / f"{month_str}.md"
    theme_party_status = "企画済み" if theme_party_file.exists() else "未企画"

    magazine_dir = meadow_dir / "magazine"
    latest_magazine = None
    if magazine_dir.exists():
        vol_dirs = sorted([d for d in magazine_dir.iterdir() if d.is_dir() and d.name.startswith("VOL-")])
        if vol_dirs:
            latest_magazine = vol_dirs[-1].name

    dashboard_file = meadow_dir / "dashboard" / f"{week_str}.md"
    this_week_dashboard = dashboard_file.exists()

    summary_lines = [
        f"🍡 今月のテーマ会: {theme_party_status}",
        f"📖 最新Magazine: {latest_magazine or '未生成'}",
        f"📋 今週のダッシュボード: {'更新済み' if this_week_dashboard else '/lifeで生成'}",
    ]
    return {
        "summary": "  /  ".join(summary_lines),
        "theme_party_status": theme_party_status,
        "latest_magazine": latest_magazine,
        "this_week_dashboard": this_week_dashboard,
    }

# === /collection 連携 ===
def load_collection():
    if not COLLECTION_DATA.exists():
        return None
    try:
        return json.loads(COLLECTION_DATA.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[collection] load failed: {e}", file=sys.stderr)
        return None

def all_collection_items(coll):
    """全カテゴリのitemをフラット化（category_key/category_label付与）"""
    if not coll or "categories" not in coll:
        return []
    items = []
    for key, cat in coll["categories"].items():
        for it in cat.get("items", []):
            items.append({**it, "category_key": key, "category_label": cat.get("label", key)})
    return items

def pick_oshi(coll):
    """画像付きitemから直近3枚を除外してランダム1枚"""
    items = [it for it in all_collection_items(coll) if it.get("image_path") or it.get("image")]
    if not items:
        return None
    history = []
    if OSHI_HISTORY.exists():
        try:
            history = json.loads(OSHI_HISTORY.read_text(encoding="utf-8"))
        except Exception:
            history = []
    recent = set(history[-3:])
    pool = [it for it in items if (it.get("id") or it.get("image_path") or it.get("image")) not in recent]
    if not pool:
        pool = items
    chosen = random.choice(pool)
    chosen_id = chosen.get("id") or chosen.get("image_path") or chosen.get("image")
    history.append(chosen_id)
    history = history[-10:]
    try:
        OSHI_HISTORY.write_text(json.dumps(history, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    img = chosen.get("image_path") or chosen.get("image")
    # ローカルパスはfile:// に変換（GitHub Pagesでは表示できないが、ローカル閲覧時はOK）
    if img and not img.startswith(("http://", "https://", "data:", "file://")):
        # 相対パスならcollection相対 → 絶対パス → file://
        cp = COLLECTION_DATA.parent / img
        if cp.exists():
            img = "file://" + str(cp)
    return {
        "image": img,
        "title": chosen.get("title") or chosen.get("name", ""),
        "caption": chosen.get("caption") or chosen.get("note") or chosen.get("description", ""),
        "category_label": chosen.get("category_label", ""),
    }

def collection_stats(coll, today_dt):
    """今月追加されたitemをカテゴリ別に集計"""
    if not coll or "categories" not in coll:
        return None
    month_prefix = today_dt.strftime("%Y-%m")
    rows = []
    total = 0
    for key, cat in coll["categories"].items():
        c = 0
        for it in cat.get("items", []):
            ts = it.get("created") or it.get("date") or it.get("added_at") or ""
            if ts.startswith(month_prefix):
                c += 1
        rows.append({"key": key, "label": cat.get("label", key), "count": c})
        total += c
    return {"categories": rows, "total": total}

# === 📚 ライブラリ（fujimoto-cpu の GitHub Pages リポ自動取得） ===
LIBRARY_ICONS = [
    (r"dashboard", "🦋"),
    (r"bigbang|kpop|k-pop|idol", "👑"),
    (r"basket|nba|bleague", "🏀"),
    (r"heike|kabuki|theater|noh|opera", "🎭"),
    (r"cowork", "📘"),
    (r"ai|trend", "🤖"),
    (r"fashion", "👗"),
    (r"brand", "🎨"),
    (r"ip[-_]|news", "📰"),
    (r"literature|reader", "📚"),
    (r"manifesto", "✊"),
    (r"rag|guide", "🎀"),
    (r"sns|x[-_]", "🐦"),
]

def library_icon(name):
    low = name.lower()
    for pattern, icon in LIBRARY_ICONS:
        if re.search(pattern, low):
            return icon
    return "📄"

def get_library():
    """gh CLI で fujimoto-cpu の公開リポ一覧を取得し、dashboard 本体を除外して返す"""
    try:
        result = subprocess.run(
            ["gh", "repo", "list", "fujimoto-cpu", "--limit", "100",
             "--no-archived", "--visibility", "public",
             "--json", "name,description,homepageUrl,pushedAt"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0 or not result.stdout:
            print(f"[library] gh failed: {result.stderr}", file=sys.stderr)
            return []
        repos = json.loads(result.stdout)
    except Exception as e:
        print(f"[library] failed: {e}", file=sys.stderr)
        return []

    items = []
    for r in repos:
        name = r.get("name", "")
        if name == "dashboard":
            continue  # 自分自身は除外
        url = r.get("homepageUrl") or f"https://fujimoto-cpu.github.io/{name}/"
        items.append({
            "name": name,
            "description": r.get("description") or "",
            "url": url,
            "icon": library_icon(name),
            "pushed_at": r.get("pushedAt", ""),
        })
    # 直近更新順
    items.sort(key=lambda x: x.get("pushed_at", ""), reverse=True)
    return items

# === 今夜の楽しみ（Daily Note Day Plannerから18時以降を抽出） ===
def read_tonight(today_str):
    path = DAILY_NOTE_DIR / f"{today_str}.md"
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    # Day Plannerセクション抽出
    section = re.search(r"Day [Pp]lanner.*?(?=\n##|\Z)", text, re.DOTALL)
    if not section:
        return None
    block = section.group(0)
    # `- [ ] HH:MM - HH:MM 内容` または `- [x]` パターン
    pattern = re.compile(r"-\s*\[[ x]\]\s*(\d{1,2}):(\d{2})\s*-\s*(?:\d{1,2}:\d{2}|__:__)\s+(.+?)(?:\n|$)")
    candidates = []
    for mm in pattern.finditer(block):
        h = int(mm.group(1))
        mn = int(mm.group(2))
        content = mm.group(3).strip()
        # #private タグや 🎀 で始まる楽しみ予定を優先
        is_private = "#private" in content or "🎀" in content
        if h >= 18 and h <= 26:
            content_clean = re.sub(r"#\w+", "", content).strip()
            content_clean = re.sub(r"\s+", " ", content_clean)
            candidates.append({
                "hour": h,
                "time": f"{h:02d}:{mn:02d}",
                "summary": content_clean,
                "is_private": is_private,
            })
    if not candidates:
        return None
    # プライベート優先 → 早い順
    candidates.sort(key=lambda x: (not x["is_private"], x["hour"]))
    pick = candidates[0]
    return {"time": pick["time"], "summary": pick["summary"]}

def read_schedule(today_str):
    """Daily Note の `## 📅 今日のカレンダー` テーブルから今日の予定をパース。"""
    path = DAILY_NOTE_DIR / f"{today_str}.md"
    if not path.exists():
        return {"events": [], "note_exists": False}
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {"events": [], "note_exists": False}

    section = re.search(r"##\s*[📅🗓].*?今日のカレンダー.*?(?=\n##|\Z)", text, re.DOTALL)
    if not section:
        return {"events": [], "note_exists": True}

    block = section.group(0)
    row_pat = re.compile(
        r"^\|\s*(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$",
        re.MULTILINE,
    )
    events = []
    for m in row_pat.finditer(block):
        start, end, content, cal = m.group(1), m.group(2), m.group(3).strip(), m.group(4).strip()
        is_private = "プライベート" in cal or "🎀" in content or "private" in cal.lower()
        title = re.sub(r"^\[🎀\]\s*", "", content).strip()
        events.append({
            "start": start,
            "end": end,
            "title": title,
            "tag": "private" if is_private else "work",
        })
    return {"events": events, "note_exists": True}

# === CORIN手紙 ===
ASCII_ARTS = [
    " /) /)\n(  • •)\n⊃ 🍵",
    " /)/) ˚｡´☆\n( . .) ☆´˚｡\n⊃  ❤️ ☆",
    "  (\\(\\\n(o- .•)❤️\no_(\")(\" )",
    " /)/)\n( ≧ ▽≦)\n⊃  🎶",
]

def make_letter(weather, brand, today_dt):
    is_weekend = today_dt.weekday() >= 5
    is_monday = today_dt.weekday() == 0
    is_friday = today_dt.weekday() == 4

    greeting = random.choice([
        "ゆりこ、おはよ！",
        "ゆりこ！おはよう〜",
        "おはよ、ゆりこ。",
    ])

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

# === Mission Control 用4関数（2026-05-30 追加） ===

# プロジェクト概要 → カテゴリ別案件
def categorize_by_tags(tags_str, client):
    """tags / client から表示カテゴリ slug を推定"""
    t = (tags_str or "").lower()
    c = (client or "").lower()
    # 優先順：AI推進 → 自動化 → プライベート → デザイン（デフォルト）
    if any(k in t for k in ["ai推進", "ai-推進", "ai効果", "ai活用", "rag", "ai_pulse"]):
        return "ai", "🤖 AI推進"
    if any(k in t for k in ["自動化", "automation", "スキル", "ツール", "skill"]):
        return "auto", "⚙️ 自動化・ツール"
    if any(k in t for k in ["meadow", "private", "プライベート"]) or "meadow" in c:
        return "private", "🦋 プライベート"
    return "design", "🎨 デザイン・制作"


def parse_project_hubs():
    """projects/ 配下の type:project ハブmd を全スキャン → カテゴリ別グループ化（projects-overview.md 廃止後の新方式・2026-06-02）"""
    cats_map = {
        "design": {"name": "🎨 デザイン・制作", "slug": "design", "projects": []},
        "ai": {"name": "🤖 AI推進", "slug": "ai", "projects": []},
        "auto": {"name": "⚙️ 自動化・ツール", "slug": "auto", "projects": []},
        "private": {"name": "🦋 プライベート", "slug": "private", "projects": []},
        "done": {"name": "✅ 完了案件", "slug": "done", "projects": []},
    }

    for hub_path in PROJECTS_DIR.rglob("*.md"):
        sp = str(hub_path)
        if "/bk/" in sp or "/_templates/" in sp or "/終了した案件/" in sp:
            continue
        try:
            content = hub_path.read_text(encoding="utf-8")
        except Exception:
            continue
        m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not m:
            continue
        fm_raw = m.group(1)
        fm = {}
        for line in fm_raw.split("\n"):
            mm = re.match(r"^([a-zA-Z案件_-]+):\s*(.+?)\s*$", line)
            if mm:
                fm[mm.group(1)] = mm.group(2).strip('"').strip("'")
        if fm.get("type") != "project":
            continue
        # tags チェック（project-board 必須）
        tags = fm.get("tags", "")
        if "project-board" not in tags.lower():
            continue
        status = fm.get("status", "in-progress").lower()
        client = fm.get("client", "")
        proj_key = fm.get("案件") or hub_path.stem
        name = client or proj_key
        # status からカテゴリ判定
        if status in ("done", "archived", "cancelled"):
            cat_slug = "done"
            status_label = "📦 archived" if status in ("archived", "done") else "❌ " + status
        else:
            cat_slug, _ = categorize_by_tags(tags, client)
            status_emoji = {"in-progress": "🔄", "planning": "⏳", "waiting": "⏸", "paused": "🔵"}.get(status, "🔄")
            status_label = f"{status_emoji} {status}"

        # 説明：本文の最初の意味ある行を取る（## 📋 概要 or 最初の文）
        body = content[m.end():]
        desc = ""
        for line in body.split("\n"):
            s = line.strip()
            if not s or s.startswith("#") or s.startswith(">") or s.startswith("|") or s.startswith("-"):
                continue
            if s.startswith("---") or s.startswith("```"):
                continue
            desc = s[:80]
            break

        cats_map[cat_slug]["projects"].append({
            "name": name,
            "hub": hub_path.stem,
            "status": status_label,
            "desc": desc,
            "_last_updated": fm.get("last_updated", ""),
            "_priority": fm.get("priority", "P3"),
        })

    # done 以外は priority + last_updated 順、done は last_updated 降順
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    for cat_slug, cat in cats_map.items():
        if cat_slug == "done":
            cat["projects"].sort(key=lambda p: p.get("_last_updated", ""), reverse=True)
        else:
            cat["projects"].sort(key=lambda p: (priority_order.get(p.get("_priority", "P3"), 3), -1 * (p.get("_last_updated", "") > "")))
        for p in cat["projects"]:
            p.pop("_last_updated", None)
            p.pop("_priority", None)

    # 空カテゴリは出さない
    return [c for c in cats_map.values() if c["projects"]]


def parse_projects_overview():
    """projects-overview.md のテーブルからカテゴリ別案件リストを抽出（後方互換・廃止予定）"""
    if not PROJECTS_OVERVIEW.exists():
        return []
    text = PROJECTS_OVERVIEW.read_text(encoding="utf-8")
    categories = []
    current_cat = None
    cat_emojis = {
        "🎨 デザイン・制作": "design",
        "🤖 AI推進": "ai",
        "⚙️ 自動化・ツール": "auto",
        "🦋 プライベート": "private",
        "✅ 完了案件": "done",
    }
    for line in text.split("\n"):
        # H2 セクション検出
        m_h2 = re.match(r"^##\s+(.+?)(?:\s*\(.*\))?$", line)
        if m_h2:
            title = m_h2.group(1).strip()
            slug = cat_emojis.get(title)
            if slug:
                current_cat = {"name": title, "slug": slug, "projects": []}
                categories.append(current_cat)
            else:
                current_cat = None
            continue
        # テーブル行検出（| **xxx** | ... | ... | ... |）
        if current_cat and line.startswith("|") and "**" in line:
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) < 4:
                continue
            name_col = cols[0]
            hub_col = cols[1]
            status_col = cols[2]
            desc_col = cols[3]
            # 案件名抽出（**name** から）
            m_name = re.search(r"\*\*(.+?)\*\*", name_col)
            if not m_name:
                continue
            name = m_name.group(1).replace("*", "").strip()
            # ハブmd wiki-link 抽出
            hub_link = None
            m_hub = re.search(r"\[\[(.+?)\]\]", hub_col)
            if m_hub:
                hub_link = m_hub.group(1).split("|")[0].strip()
            # 残りの説明列
            status_clean = status_col.replace("**", "").strip()
            desc_clean = desc_col.replace("**", "").strip()
            current_cat["projects"].append({
                "name": name,
                "hub": hub_link,  # 案件名（wiki-linkのファイル名・None=未作成）
                "status": status_clean,
                "desc": desc_clean[:80],
            })
    return categories


def check_hub_md(hub_name):
    """指定された名前のハブmdを探して frontmatter + 関連リンク抽出"""
    if not hub_name:
        return None
    # PROJECTS_DIR 配下から hub_name.md を再帰検索
    candidates = list(PROJECTS_DIR.rglob(f"{hub_name}.md"))
    candidates = [c for c in candidates if "/bk/" not in str(c) and "/_templates/" not in str(c)]
    if not candidates:
        return None
    hub_path = candidates[0]
    try:
        content = hub_path.read_text(encoding="utf-8")
    except Exception:
        return None
    # frontmatter
    fm = {}
    m = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if m:
        for line in m.group(1).split("\n"):
            mm = re.match(r"^([a-zA-Z案件_]+):\s*(.+?)\s*$", line)
            if mm:
                fm[mm.group(1)] = mm.group(2).strip('"').strip("'")
    # 「🔗 関連リンク」セクションから URL 抽出
    # H2 形式 or callout 形式（> [!note] 🔗 関連リンク）の両方対応
    links = []
    section_patterns = [
        r"##\s*🔗\s*関連リンク.*?(?=\n##\s|\n---|\Z)",
        r">\s*\[![\w-]+\]-?\s*🔗\s*関連リンク.*?(?=\n---|\n##\s|\n\n[^>]|\Z)",
    ]
    for pat in section_patterns:
        section_match = re.search(pat, content, re.DOTALL)
        if not section_match:
            continue
        section = section_match.group(0)
        # Markdownリンク [text](url)
        for label, url in re.findall(r"\[([^\[\]]+)\]\(([^)]+)\)", section):
            if url.startswith("http") or url.startswith("obsidian://"):
                links.append({"label": label.strip(), "url": url.strip()})
        # 内部wiki-link（オプション・Obsidian URI化）
        for wiki in re.findall(r"\[\[([^\]|]+?)(?:\|[^\]]+)?\]\]", section):
            from urllib.parse import quote
            uri = f"obsidian://advanced-uri?vault=corin&filepath={quote(wiki + '.md')}"
            links.append({"label": wiki[:18], "url": uri})
        break  # 最初にマッチしたセクションで打ち切り
    # Obsidian URI（ハブmdを開く）
    vault_path = str(hub_path).replace(str(CORIN_ROOT) + "/", "")
    from urllib.parse import quote
    obsidian_uri = f"obsidian://advanced-uri?vault=corin&filepath={quote(vault_path)}"
    # 11工程進捗抽出
    process_progress = extract_process_progress(content)
    return {
        "exists": True,
        "path": str(hub_path),
        "obsidian_uri": obsidian_uri,
        "frontmatter": fm,
        "links": links[:6],  # 多すぎ防止
        "process_progress": process_progress,
    }


def extract_process_progress(content):
    """ハブmdから『📊 走らせた工程』セクションを抽出して11工程の状態を返す

    Returns:
        {
            "K": "✅"|"🔄"|"⬜"|"N/A",
            "0": "...",
            ...
            "R-final": "...",
            "completed_count": int,
            "total_count": int,  # N/A除外
        }
    """
    # デフォルト：全工程未着手
    progress_keys = ["K", "0", "0-1", "A", "B", "C", "Z", "V", "Y", "R-mid", "R-final"]
    result = {k: "⬜" for k in progress_keys}

    # セクション抽出
    section_match = re.search(
        r"##\s*📊\s*走らせた工程.*?(?=\n##\s|\n---|\Z)",
        content, re.DOTALL
    )
    if not section_match:
        return None  # セクション無い場合は None
    section = section_match.group(0)

    # 工程記号 → 工程キーのマッピング
    process_map = [
        ("🇰", "K"),
        ("🅾-1", "0-1"),   # 0-1 を 0 より先にチェック（順序重要）
        ("🅾", "0"),
        ("🅰️", "A"),
        ("🅱️", "B"),
        ("🅲", "C"),
        ("🅩", "Z"),
        ("🇻", "V"),
        ("🇾", "Y"),
        ("🇷-mid", "R-mid"),
        ("🇷-final", "R-final"),
    ]

    # 状態判定の優先順位
    status_patterns = [
        ("✅", "✅"),
        ("🔄", "🔄"),
        ("N/A", "N/A"),
        ("⬜", "⬜"),
    ]

    for line in section.split("\n"):
        if not line.startswith("|"):
            continue
        # 各工程に対してマッチング
        for emoji, key in process_map:
            if emoji in line:
                # 状態判定
                for pattern, status in status_patterns:
                    if pattern in line:
                        result[key] = status
                        break
                break  # 1行1工程

    # 集計
    total = sum(1 for v in result.values() if v != "N/A")
    completed = sum(1 for v in result.values() if v == "✅")
    in_progress = sum(1 for v in result.values() if v == "🔄")

    result["completed_count"] = completed
    result["in_progress_count"] = in_progress
    result["total_count"] = total
    return result


def find_meeting_notes(project_name):
    """Zettelkasten から案件名一致する議事メモ wiki-link 候補を取得"""
    if not ZETTEL_DIR.exists() or not project_name:
        return []
    keywords = [project_name]
    # 案件名にスペースあれば分割
    if " " in project_name:
        keywords.extend(project_name.split())
    results = []
    for md in ZETTEL_DIR.rglob("*.md"):
        if "/bk/" in str(md) or "/_templates/" in str(md):
            continue
        name = md.stem
        if any(kw in name for kw in keywords if len(kw) >= 2):
            results.append(name)
    return sorted(results)[:5]


def get_active_projects():
    """projects/ 配下のハブmd全スキャン + 各案件のハブmd詳細 + 議事録紐付け（2026-06-02 新方式）"""
    categories = parse_project_hubs()
    # フォールバック：もし projects/ スキャンが空なら旧方式（projects-overview.md）
    if not categories:
        categories = parse_projects_overview()
    for cat in categories:
        for proj in cat["projects"]:
            proj["hub_info"] = check_hub_md(proj["hub"])
            proj["meetings"] = find_meeting_notes(proj["name"])
    return categories


def _normalize_for_dedup(title: str) -> str:
    """バージョン違いの重複検出用にタイトルを正規化"""
    t = title.strip()
    # 末尾の v数字・_v数字・(モック vN) を削除
    t = re.sub(r"[（(]\s*モック\s+v\s*\d+\s*[）)]\s*$", "", t)
    t = re.sub(r"\s*[_-]?v\s*\d+\s*$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+", " ", t).strip()
    return t.lower()


def rebuild_html_index():
    """scripts/rebuild_index.py を実行して INDEX.md を全件再生成する。
    get_recent_html() は INDEX.md をパースするため、新規HTMLを取りこぼさないよう
    aggregate の前段で必ず走らせる（2026-06-14 自動連鎖バグ修正）。"""
    script = DASHBOARD_ROOT / "scripts" / "rebuild_index.py"
    if not script.exists():
        print("[rebuild_index] scripts/rebuild_index.py が見つからない → スキップ")
        return
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            last = (result.stdout.strip().splitlines() or ["(no output)"])[-1]
            print(f"[rebuild_index] OK → {last}")
        else:
            print(f"[rebuild_index] 失敗(returncode={result.returncode}): {result.stderr.strip()[:200]}")
    except Exception as e:
        print(f"[rebuild_index] 例外: {e}")


def get_recent_html(limit=20):
    """INDEX.md パース → 新しい順N件 + MD骨子存在判定（バージョン違い重複制御）"""
    if not HTML_INDEX.exists():
        return []
    text = HTML_INDEX.read_text(encoding="utf-8")
    entries = []
    current_category = None
    # 簡易パース：H2セクション + テーブル行
    for line in text.split("\n"):
        m_h2 = re.match(r"^##\s+(.+?)$", line)
        if m_h2:
            current_category = m_h2.group(1).strip()
            # 「📝 運用メモ」等メタセクションはスキップ
            if "運用" in current_category:
                current_category = None
            continue
        if not current_category or not line.startswith("|"):
            continue
        if line.startswith("|---") or "日付" in line:
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) < 4:
            continue
        date_str = cols[0]
        title_col = cols[1]
        html_col = cols[2]
        md_col = cols[3]
        # 日付形式チェック
        if not re.match(r"\d{4}-\d{2}-\d{2}", date_str):
            continue
        # HTML パス抽出（[📄 HTML](/path)）
        m_url = re.search(r"\(([^)]+\.html)\)", html_col)
        html_path = m_url.group(1) if m_url else ""
        # タイトル抽出（wiki-link または平文）
        m_title = re.search(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]\s*(.*)", title_col)
        if m_title:
            wiki_name = m_title.group(1).strip()
            display = (m_title.group(2) or wiki_name).strip()
        else:
            wiki_name = ""
            display = title_col.strip()
        has_md = "⚠" not in md_col
        entries.append({
            "date": date_str,
            "title": display[:60],
            "wiki": wiki_name,
            "category": current_category,
            "html_path": html_path,
            "html_url": f"file://{html_path}" if html_path else "",
            "has_md": has_md,
        })
    # 新しい順
    entries.sort(key=lambda e: e["date"], reverse=True)
    # バージョン違いを最新1件に絞る
    seen_keys = set()
    deduped = []
    for e in entries:
        key = (e["category"], _normalize_for_dedup(e["title"]))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(e)
    return deduped[:limit]


def get_static_links():
    """links_config.json を読む（仕事/プライベート両方）"""
    if not LINKS_CONFIG.exists():
        return {"work": [], "private": []}
    try:
        return json.loads(LINKS_CONFIG.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[links_config] parse failed: {e}", file=sys.stderr)
        return {"work": [], "private": []}


# === git commit & push ===
def git_push():
    if not (DASHBOARD_ROOT / ".git").exists():
        print("[git] not a git repo, skipping push", file=sys.stderr)
        return
    try:
        subprocess.run(["git", "-C", str(DASHBOARD_ROOT), "add", "data.js", "oshi_history.json", "links_config.json", "index.html", "style.css", "theme.js", "scripts/"], check=False)
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

# === メイン ===
def main():
    today_dt = datetime.date.today()
    today_str = today_dt.strftime("%Y-%m-%d")
    weekday_jp = ["月", "火", "水", "木", "金", "土", "日"][today_dt.weekday()]
    hour = datetime.datetime.now().hour

    print(f"=== CORIN Dashboard v2 aggregate {today_str}（{weekday_jp}）===")

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

    coll = load_collection()
    oshi = pick_oshi(coll) if coll else None
    print(f"[oshi] {'image: ' + (oshi.get('image') or '') if oshi else 'none (collection empty)'}")
    coll_stats = collection_stats(coll, today_dt) if coll else None
    print(f"[collection_stats] total={coll_stats['total'] if coll_stats else 0}")
    tonight = read_tonight(today_str)
    print(f"[tonight] {tonight['summary'] if tonight else 'none'}")
    schedule = read_schedule(today_str)
    print(f"[schedule] {len(schedule['events'])} events")
    library = get_library()
    print(f"[library] {len(library)} repos")

    letter = make_letter(weather, brand, today_dt)

    # === Mission Control データ ===
    # INDEX.md を先に再生成（新規HTMLを取りこぼさないため・get_recent_html は INDEX.md をパースする）
    rebuild_html_index()
    active_projects = get_active_projects()
    print(f"[mission-control] active_projects: {sum(len(c['projects']) for c in active_projects)} 件")
    recent_html = get_recent_html(limit=20)
    print(f"[mission-control] recent_html: {len(recent_html)} 件")
    static_links = get_static_links()
    print(f"[mission-control] static_links: {sum(len(g['links']) for g in static_links.get('work', []))} (work)")

    data = {
        "date": today_str,
        "weather": weather,
        "letter": letter,
        "ai": {"summary": "X AIトレンド本日のレポート（HTMLで全10件解説）"},
        "fashion": {"summary": "日本・韓国・世界のトレンド計6本（HTMLで全件解説）"},
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
        "oshi": oshi,
        "collection_stats": coll_stats,
        "tonight": tonight,
        "schedule": schedule,
        "daily_photo": None,
        "library": library,
        # Mission Control（2026-05-30 追加）
        "active_projects": active_projects,
        "recent_html": recent_html,
        "static_links": static_links,
    }

    output = DASHBOARD_ROOT / "data.js"
    output.write_text(
        f"window.CORIN_DATA = {json.dumps(data, ensure_ascii=False, indent=2)};\n",
        encoding="utf-8"
    )
    print(f"✅ data.js generated: {output}")

    if os.environ.get("DASHBOARD_AUTO_PUSH", "1") == "1":
        git_push()

if __name__ == "__main__":
    main()
