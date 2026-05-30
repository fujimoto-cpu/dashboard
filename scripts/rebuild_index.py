#!/usr/bin/env python3
"""
rebuild_index.py — secretary/outputs/INDEX.md を全件補修・再生成

Vault内のコリン作HTML（ホワイトリスト方式）を検出し、
カテゴリ別 H2 折りたたみ構造で INDEX.md を再生成する。

使い方:
  python3 rebuild_index.py              # 本実行（INDEX.md 上書き）
  python3 rebuild_index.py --dry-run    # 標準出力にプレビューのみ
"""

import argparse
import os
import re
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

VAULT = Path("/Users/yuriko/Documents/corin")
INDEX_PATH = VAULT / "00_🏢 company/secretary/outputs/INDEX.md"

# ホワイトリスト：ここの直下/再帰下に HTML があれば対象
WHITELIST = [
    "00_🏢 company/secretary/outputs",
    "00_🏢 company/secretary/notes",
    "00_🏢 company/ai",
    "30_🧠 context/_plans",
    "01_🏠 private/meadow",
]
# projects/*/_ai-drafts/ は別途処理（ワイルドカード）

# 除外パターン（パス文字列に含まれてたら除外）
EXCLUDE_FRAGMENTS = [
    "/bk/",
    "/_templates/",
    "/dist/",
    "/.claude/",
    "/99_🗄️ archive/",
    "/instagram-",
    "/threads-",
    "/x-",
    "/yt-",
    "/Trash/",
]

# カテゴリ判定：パスの一部にマッチしたらこのカテゴリに分類
CATEGORIES = [
    ("🤖 CORIN出力（outputs/）", "/secretary/outputs/"),
    ("🎨 ブランド分析・トレンド（notes/）", "/secretary/notes/"),
    ("🤖 AI推進資料（ai/）", "/ai/"),
    ("📁 案件ドラフト（_ai-drafts/）", "/_ai-drafts/"),
    ("📋 プラン・設計書（_plans/）", "/_plans/"),
    ("🦋 MEADOW.（private/meadow/）", "/01_🏠 private/meadow/"),
]


class TitleExtractor(HTMLParser):
    """HTMLから <title> と最初の <h1> を抽出"""

    def __init__(self):
        super().__init__()
        self.title = None
        self.h1 = None
        self._in_title = False
        self._in_h1 = False
        self._title_buf = []
        self._h1_buf = []

    def handle_starttag(self, tag, attrs):
        if tag == "title" and self.title is None:
            self._in_title = True
        elif tag == "h1" and self.h1 is None:
            self._in_h1 = True

    def handle_endtag(self, tag):
        if tag == "title" and self._in_title:
            self._in_title = False
            self.title = "".join(self._title_buf).strip()
        elif tag == "h1" and self._in_h1:
            self._in_h1 = False
            self.h1 = "".join(self._h1_buf).strip()

    def handle_data(self, data):
        if self._in_title:
            self._title_buf.append(data)
        elif self._in_h1:
            self._h1_buf.append(data)


def is_excluded(path_str: str) -> bool:
    return any(frag in path_str for frag in EXCLUDE_FRAGMENTS)


def extract_title(html_path: Path) -> str:
    """<title> → <h1> → ファイル名(拡張子なし) の順で fallback"""
    try:
        content = html_path.read_text(encoding="utf-8", errors="ignore")
        parser = TitleExtractor()
        parser.feed(content[:50000])  # 先頭50KBで十分
        title = parser.title or parser.h1
        if title:
            # 改行・連続空白を整理
            title = re.sub(r"\s+", " ", title).strip()
            return title
    except Exception:
        pass
    return html_path.stem


def extract_date(html_path: Path) -> str:
    """ファイル名のYYYY-MM-DD → mtime の順"""
    # YYYY-MM-DD
    m = re.match(r"(\d{4}-\d{2}-\d{2})", html_path.stem)
    if m:
        return m.group(1)
    # YYYYMMDD
    m = re.match(r"(\d{4})(\d{2})(\d{2})", html_path.stem)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # mtime fallback
    return datetime.fromtimestamp(html_path.stat().st_mtime).strftime("%Y-%m-%d")


def categorize(path_str: str) -> str:
    for name, frag in CATEGORIES:
        if frag in path_str:
            return name
    return "📂 その他"


def collect_html_files() -> list[Path]:
    files = []
    # ホワイトリスト直下
    for rel in WHITELIST:
        base = VAULT / rel
        if not base.exists():
            continue
        files.extend(base.rglob("*.html"))
    # projects/*/_ai-drafts/
    projects_dir = VAULT / "00_🏢 company/projects"
    if projects_dir.exists():
        files.extend(projects_dir.glob("*/_ai-drafts/**/*.html"))
        files.extend(projects_dir.glob("*/*/_ai-drafts/**/*.html"))
    # 除外フィルタ
    filtered = []
    seen = set()
    for f in files:
        s = str(f)
        if is_excluded(s):
            continue
        if s in seen:
            continue
        seen.add(s)
        filtered.append(f)
    return sorted(filtered)


def make_obsidian_link(html_path: Path) -> str:
    """ファイル名（拡張子なし）の wiki-link を生成"""
    stem = html_path.stem
    return f"[[{stem}]]"


def make_md_link(html_path: Path) -> str:
    """同名 MD が存在するか確認・wiki-link or ⚠ を返す"""
    md_path = html_path.with_suffix(".md")
    if md_path.exists():
        return f"[[{md_path.stem}|📝 MD]]"
    return "⚠️"


def make_html_open_link(html_path: Path) -> str:
    """ローカルHTMLへの直接openリンク（Markdownリンク形式）"""
    # スペース・絵文字含むパスをそのまま [text](path) で渡す（Obsidianはこれを許容）
    return f"[📄 HTML]({html_path})"


def build_index_md(files: list[Path]) -> str:
    # カテゴリ別に分類
    buckets = {name: [] for name, _ in CATEGORIES}
    buckets["📂 その他"] = []
    for f in files:
        cat = categorize(str(f))
        entry = {
            "path": f,
            "date": extract_date(f),
            "title": extract_title(f),
            "wiki": make_obsidian_link(f),
            "md_link": make_md_link(f),
            "html_link": make_html_open_link(f),
        }
        buckets[cat].append(entry)
    # 各カテゴリ内で新しい順
    for k in buckets:
        buckets[k].sort(key=lambda e: e["date"], reverse=True)

    total = sum(len(v) for v in buckets.values())
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    out = []
    out.append("---")
    out.append("type: index")
    out.append("title: Vault HTML インデックス（自動生成）")
    out.append(f"last_updated: {now}")
    out.append(f"total: {total}")
    out.append("auto_generated: true")
    out.append("---")
    out.append("")
    out.append("# 📁 Vault HTML インデックス")
    out.append("")
    out.append("> [!info] 自動生成（手動編集禁止）")
    out.append(f"> `~/Documents/dashboard/scripts/rebuild_index.py` が生成。最終更新: {now}")
    out.append(f"> 総ファイル数: **{total}本**（コリン作HTML・IGダウンロード/bk/archive/dist/.claude/skills は除外）")
    out.append("> 手動編集しても次回再生成で消えるので、追加リンクは案件ハブmd等に記入を。")
    out.append("")
    out.append("---")
    out.append("")

    for cat, _ in CATEGORIES + [("📂 その他", "")]:
        entries = buckets.get(cat, [])
        if not entries:
            continue
        out.append(f"## {cat} {len(entries)}本")
        out.append("")
        out.append("| 日付 | タイトル | HTML | MD |")
        out.append("|---|---|---|---|")
        for e in entries:
            # タイトルにパイプ含まれてたらエスケープ
            safe_title = e["title"].replace("|", "\\|")
            out.append(
                f"| {e['date']} | {e['wiki']} {safe_title[:60]} | {e['html_link']} | {e['md_link']} |"
            )
        out.append("")
        out.append("---")
        out.append("")

    out.append("## 📝 運用メモ")
    out.append("")
    out.append("- このINDEXは自動生成。手動編集禁止")
    out.append("- 新規HTML作成時は `~/Documents/dashboard/aggregate.py` 経由で自動再生成される")
    out.append("- ⚠️ がついているHTMLは同名MD骨子が未生成（Obsidian全文検索でヒットしない）")
    out.append("- ファイル削除は禁止（critical-mistakes #4.6 準拠）")

    return "\n".join(out) + "\n"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="標準出力にプレビューのみ")
    args = p.parse_args()

    files = collect_html_files()
    print(f"📊 検出HTML数: {len(files)}本", file=sys.stderr)

    md = build_index_md(files)

    if args.dry_run:
        print(md)
        print(f"\n--- DRY RUN: {len(files)}本検出 ---", file=sys.stderr)
        return

    INDEX_PATH.write_text(md, encoding="utf-8")
    print(f"✅ INDEX.md 更新完了: {len(files)}本登録", file=sys.stderr)
    print(f"📍 {INDEX_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
