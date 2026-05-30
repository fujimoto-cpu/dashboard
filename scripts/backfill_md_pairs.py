#!/usr/bin/env python3
"""
backfill_md_pairs.py — MD骨子が無いHTMLに同名MD骨子を後付け生成

Obsidian全文検索でHTMLがヒットしない問題を解消する。
HTMLからタイトル・要約・キーワードを抽出して frontmatter付き MD を生成。

使い方:
  python3 backfill_md_pairs.py --dry-run    # 標準出力にプレビュー
  python3 backfill_md_pairs.py              # 本実行（同名MD生成）
"""

import argparse
import os
import re
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

VAULT = Path("/Users/yuriko/Documents/corin")

# rebuild_index.py と同じ対象範囲
WHITELIST = [
    "00_🏢 company/secretary/outputs",
    "00_🏢 company/secretary/notes",
    "00_🏢 company/ai",
    "30_🧠 context/_plans",
    "01_🏠 private/meadow",
]
EXCLUDE_FRAGMENTS = [
    "/bk/", "/_templates/", "/dist/", "/.claude/",
    "/99_🗄️ archive/", "/instagram-", "/threads-",
    "/x-", "/yt-", "/Trash/",
]

# カテゴリ判定（タグ用）
CATEGORY_TAGS = [
    ("/secretary/outputs/", ["output", "corin-output"]),
    ("/secretary/notes/", ["output", "research"]),
    ("/ai/", ["output", "ai-knowledge"]),
    ("/_ai-drafts/", ["output", "draft"]),
    ("/_plans/", ["output", "plan"]),
    ("/01_🏠 private/meadow/", ["output", "meadow"]),
]


class HTMLContentExtractor(HTMLParser):
    """HTMLから title / h1 / 本文テキストを抽出"""

    SKIP_TAGS = {"script", "style", "noscript", "svg"}

    def __init__(self):
        super().__init__()
        self.title = None
        self.h1 = None
        self.h2s = []
        self.paragraphs = []
        self._in_title = False
        self._in_h1 = False
        self._in_h2 = False
        self._in_p = False
        self._skip = False
        self._title_buf = []
        self._h1_buf = []
        self._h2_buf = []
        self._p_buf = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self._skip = True
            return
        if self._skip:
            return
        if tag == "title" and self.title is None:
            self._in_title = True
        elif tag == "h1" and self.h1 is None:
            self._in_h1 = True
        elif tag == "h2":
            self._in_h2 = True
            self._h2_buf = []
        elif tag == "p":
            self._in_p = True
            self._p_buf = []

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS:
            self._skip = False
            return
        if self._skip:
            return
        if tag == "title" and self._in_title:
            self._in_title = False
            self.title = "".join(self._title_buf).strip()
        elif tag == "h1" and self._in_h1:
            self._in_h1 = False
            self.h1 = "".join(self._h1_buf).strip()
        elif tag == "h2" and self._in_h2:
            self._in_h2 = False
            t = "".join(self._h2_buf).strip()
            if t:
                self.h2s.append(t)
        elif tag == "p" and self._in_p:
            self._in_p = False
            t = "".join(self._p_buf).strip()
            if t and len(t) > 10:  # 短すぎるpは捨てる
                self.paragraphs.append(t)

    def handle_data(self, data):
        if self._skip:
            return
        if self._in_title:
            self._title_buf.append(data)
        elif self._in_h1:
            self._h1_buf.append(data)
        elif self._in_h2:
            self._h2_buf.append(data)
        elif self._in_p:
            self._p_buf.append(data)


def is_excluded(path_str: str) -> bool:
    return any(frag in path_str for frag in EXCLUDE_FRAGMENTS)


def get_tags(path_str: str) -> list[str]:
    for frag, tags in CATEGORY_TAGS:
        if frag in path_str:
            return tags
    return ["output"]


def extract_date(html_path: Path) -> str:
    m = re.match(r"(\d{4}-\d{2}-\d{2})", html_path.stem)
    if m:
        return m.group(1)
    m = re.match(r"(\d{4})(\d{2})(\d{2})", html_path.stem)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return datetime.fromtimestamp(html_path.stat().st_mtime).strftime("%Y-%m-%d")


def extract_keywords(text: str, limit: int = 12) -> list[str]:
    """頻出する日本語名詞・英単語っぽいものを抽出"""
    # カタカナ語（2文字以上）
    katakana = re.findall(r"[ァ-ヴー]{2,}", text)
    # 漢字熟語（2文字以上）
    kanji = re.findall(r"[一-龥]{2,}", text)
    # 英大文字始まりの単語（ブランド名等）
    english = re.findall(r"\b[A-Z][a-zA-Z]{2,}\b", text)

    candidates = katakana + kanji + english

    # ストップワード
    stopwords = {
        "について", "ために", "という", "こと", "もの", "など", "から", "までに",
        "this", "that", "have", "this", "have", "with",
        "コリン", "CORIN", "ゆりこ",
        "前回", "今回", "次回", "今日", "昨日", "明日",
    }

    # 頻度カウント
    counts = {}
    for w in candidates:
        if w in stopwords:
            continue
        if len(w) < 2:
            continue
        counts[w] = counts.get(w, 0) + 1

    # 頻度順
    sorted_words = sorted(counts.items(), key=lambda x: -x[1])
    return [w for w, _ in sorted_words[:limit]]


def make_summary(extractor: HTMLContentExtractor) -> list[str]:
    """3行要約: 最初のH2 + 最初のpargraph 2-3つ"""
    out = []
    # 最初の意味あるパラグラフを優先
    for p in extractor.paragraphs[:5]:
        clean = re.sub(r"\s+", " ", p).strip()
        if len(clean) < 20:
            continue
        if len(clean) > 200:
            clean = clean[:200] + "..."
        out.append(clean)
        if len(out) >= 3:
            break
    if not out:
        out.append("（HTMLから要約抽出できず）")
    return out


def build_md(html_path: Path, extractor: HTMLContentExtractor) -> str:
    title = extractor.title or extractor.h1 or html_path.stem
    title = re.sub(r"\s+", " ", title).strip()

    date = extract_date(html_path)
    tags = get_tags(str(html_path))
    today = datetime.now().strftime("%Y-%m-%d")

    # 全テキスト（キーワード抽出用）
    full_text = "\n".join(extractor.paragraphs) + "\n" + "\n".join(extractor.h2s)
    keywords = extract_keywords(full_text)

    summary = make_summary(extractor)

    # HTML パス（URL エンコードは Obsidian Markdown link が処理）
    html_rel = html_path.name

    lines = []
    lines.append("---")
    lines.append("type: structureNote")
    lines.append(f"date: {date}")
    lines.append(f"tags: [{', '.join(tags)}]")
    lines.append(f'html_file: "{html_rel}"')
    lines.append("auto_generated: true")
    lines.append(f"backfilled: {today}")
    lines.append("related: []")
    lines.append("---")
    lines.append("")
    lines.append(f"# {title}")
    lines.append("")
    lines.append("> [!info] 📄 この資料について")
    lines.append(f"> - **作成日**: {date}")
    lines.append(f"> - **HTML**: [📄 HTMLで見る]({html_rel})")
    lines.append(f"> - ⚙️ この骨子は後付け自動生成（HTMLから抽出・{today}）")
    lines.append("")
    lines.append("## 🎯 3行要約")
    lines.append("")
    for s in summary:
        lines.append(f"- {s}")
    lines.append("")
    if keywords:
        lines.append("## 🔑 主要キーワード")
        lines.append("")
        lines.append(" ".join(f"`{w}`" for w in keywords))
        lines.append("")
    if extractor.h2s:
        lines.append("## 📌 構成（HTMLのH2見出し）")
        lines.append("")
        for h in extractor.h2s[:15]:
            clean = re.sub(r"\s+", " ", h).strip()
            lines.append(f"- {clean}")
        lines.append("")

    return "\n".join(lines) + "\n"


def collect_html_without_md() -> list[Path]:
    files = []
    for rel in WHITELIST:
        base = VAULT / rel
        if not base.exists():
            continue
        files.extend(base.rglob("*.html"))
    projects_dir = VAULT / "00_🏢 company/projects"
    if projects_dir.exists():
        files.extend(projects_dir.glob("*/_ai-drafts/**/*.html"))
        files.extend(projects_dir.glob("*/*/_ai-drafts/**/*.html"))

    # 重複除去・除外パターン適用
    seen = set()
    target = []
    for f in files:
        s = str(f)
        if is_excluded(s):
            continue
        if s in seen:
            continue
        seen.add(s)
        md = f.with_suffix(".md")
        if md.exists():
            continue
        target.append(f)
    return sorted(target)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--limit", type=int, default=0, help="最大何件処理するか（0=制限なし）")
    args = p.parse_args()

    targets = collect_html_without_md()
    if args.limit:
        targets = targets[: args.limit]

    print(f"📊 MD骨子未生成HTML: {len(targets)}本", file=sys.stderr)

    success, failed = 0, 0
    for i, html_path in enumerate(targets, 1):
        try:
            content = html_path.read_text(encoding="utf-8", errors="ignore")
            extractor = HTMLContentExtractor()
            extractor.feed(content[:200000])  # 先頭200KB処理
            md_text = build_md(html_path, extractor)

            md_path = html_path.with_suffix(".md")
            if args.dry_run:
                if i <= 2:  # 最初の2件だけプレビュー表示
                    print(f"\n--- [{i}/{len(targets)}] {md_path} ---")
                    print(md_text)
                else:
                    print(f"[{i}/{len(targets)}] {md_path.name} → 生成予定", file=sys.stderr)
            else:
                md_path.write_text(md_text, encoding="utf-8")
                print(f"✅ [{i}/{len(targets)}] {md_path.name}", file=sys.stderr)
            success += 1
        except Exception as e:
            failed += 1
            print(f"❌ [{i}/{len(targets)}] {html_path.name}: {e}", file=sys.stderr)

    print(f"\n--- 完了: 成功 {success}件 / 失敗 {failed}件 ---", file=sys.stderr)


if __name__ == "__main__":
    main()
