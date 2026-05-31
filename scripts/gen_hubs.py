#!/usr/bin/env python3
"""
gen_hubs.py — ハブmd 一括生成（2026-05-31）

ゆりこ承認プラン準拠。フル版/軽量版2テンプレで案件ハブmdを生成。
status は active/archived/cancelled の3値のみ。📊結果KPIセクション付き。
新規フォルダも作成。既存ハブmd（AM_26SS/AM_26AW/kemio抹茶/LDH/BIGBANG/ONE）は触らない。

使い方:
  python3 gen_hubs.py --dry-run
  python3 gen_hubs.py
"""
import argparse
import sys
from pathlib import Path

PROJ = Path("/Users/yuriko/Documents/corin/00_🏢 company/projects")
TODAY = "2026-05-31"


def full_template(d):
    """フル版テンプレ（status: active）"""
    stk = "\n".join(f">   {s}" for s in d.get("stakeholders_rows", []))
    sched = "\n".join(d.get("schedule_rows", []))
    links = "\n".join(d.get("link_rows", []))
    files = "\n".join(d.get("file_rows", []))
    meetings = "\n".join(d.get("meeting_rows", ["> - ⚠ 議事録があれば wiki-link 追記"]))
    tags = ", ".join(["project-board"] + d["tags"])
    return f"""---
type: project
案件: {d['key']}
client: {d['client']}
担当: ゆりこ
status: active
priority: {d['priority']}
start: {d.get('start', 'null')}
deadline: {d.get('deadline', 'null')}
stakeholders:
{chr(10).join(f'  - {s}' for s in d.get('stakeholders_yaml', ['[]'])) if d.get('stakeholders_yaml') else '  []'}
tags: [{tags}]
created: {TODAY}
last_updated: {TODAY}
---

# 🎯 {d['title']}

> [!info] 📌 ひと目で
> **🔄 active（進行中）** ｜ {d.get('oneliner', '')}
> 👤 担当：ゆりこ{d.get('owner_suffix', '')}

> [!tip] 🔗 すぐ飛ぶ
> {d.get('quick_links', '⚠ 関連リンク要追加')}

---

> [!info]- 📋 案件の背景（クリックで展開）
> | 項目 | 内容 |
> |---|---|
> | **クライアント** | {d['client']} |
> | **テーマ** | {d.get('theme', '⚠ 要記入')} |
> | **納品形式** | {d.get('deliverable', '⚠ 要記入')} |
> | **設計思想** | {d.get('concept', '⚠ 要記入')} |

> [!important]- 🗓 スケジュール
> | 日付 | マイルストーン | 状態 |
> |---|---|---|
{sched if sched else '> | ⚠ | 要記入 | ⬜ |'}

> [!tip]- 👥 ステークホルダー
> | 役割 | 人物 | 連絡手段 |
> |---|---|---|
{stk if stk else '> | 担当 | ゆりこ | — |'}

> [!note]- 📁 ファイル構成（クリックで展開）
> | パス | 用途 |
> |---|---|
{files if files else '> | `_ai-drafts/` | CORIN出力着地 |'}

> [!warning]- ⚠ 注意・ファクトチェック必須
{d.get('warnings', '> - ⚠ 案件特有の注意事項を記入')}

---

## 📝 議事録

> [!note] 🗒 議事録一覧（新しい順・クリックで直接開く）
{meetings}

## 📜 意思決定ログ

> [!success]- ✅ 決まったこと（時系列）
> | 日付 | 決定事項 | 理由 | 決定者 |
> |---|---|---|---|
{d.get('decision_rows', '> | ⚠ | 要記入 | | ゆりこ |')}

## ✅ アクティブタスク

```base
filters:
  and:
    - file.path.startsWith("00_🏢 company/tasks/active/")
    - project == "{d['task_project']}"
order:
  - priority
  - due
```

## 🏆 直近完了タスク

```base
filters:
  and:
    - file.path.contains("00_🏢 company/tasks/done/")
    - project == "{d['task_project']}"
    - completed >= date(today) - dur(14 days)
order:
  - completed desc
```

## 📊 結果KPI（納品/完了時に記入）

> [!success] 🎯 数値・結果
> | 指標 | 結果 |
> |---|---|
> | 売上 | ⚠ 要記入（送料・税抜きで集計） |
> | 制作期間 | {d.get('start', '⚠')} ～ {d.get('deadline', '進行中')} |
> | 結果評価 | ⚠ 要記入 |

> [!tip] 💡 学び3つ
> 1. ⚠ 要記入
> 2. ⚠ 要記入
> 3. ⚠ 要記入

> [!warning] 🔄 次回申し送り
> - ⚠ 要記入

## 💭 メモ・気づき

> [!question] 🩷 未解決・要確認
{d.get('todo_rows', '> - [ ] ⚠ 要確認事項')}

> [!note] 📝 雑記
{d.get('notes_rows', '> - ')}
"""


def light_template(d):
    """軽量版テンプレ（status: archived）"""
    links = d.get('quick_links', '⚠ 関連リンク要追加')
    files = "\n".join(d.get("file_rows", ['> | `_ai-drafts/` | CORIN出力着地 |']))
    tags = ", ".join(["project-board", "archived"] + d["tags"])
    return f"""---
type: project
案件: {d['key']}
client: {d['client']}
担当: ゆりこ
status: archived
priority: P3
start: {d.get('start', 'null')}
deadline: {d.get('deadline', 'null')}
tags: [{tags}]
created: {TODAY}
last_updated: {TODAY}
---

# 📦 {d['title']}

> [!info] 📌 ひと目で
> **📦 archived（完了・参照のみ）** ｜ {d.get('oneliner', '')}
> 👤 担当：ゆりこ{d.get('owner_suffix', '')}

> [!tip] 🔗 すぐ飛ぶ
> {links}

---

> [!info]- 📋 案件の背景
> | 項目 | 内容 |
> |---|---|
> | **クライアント** | {d['client']} |
> | **テーマ** | {d.get('theme', '⚠ 要記入')} |
> | **納品形式** | {d.get('deliverable', '⚠ 要記入')} |

> [!note]- 📁 ファイル構成
> | パス | 用途 |
> |---|---|
{files}

## 📊 結果KPI

> [!success] 🎯 数値・結果
> | 指標 | 結果 |
> |---|---|
> | 売上 | {d.get('kpi_sales', '⚠ 要記入（送料・税抜き）')} |
> | 制作期間 | {d.get('start', '⚠')} ～ {d.get('deadline', '⚠')} |
> | 結果評価 | ⚠ 要記入 |

> [!note] 📝 メモ
{d.get('notes_rows', '> - ')}
"""


# === 案件データ定義 ===
HUBS = [
    # ---- フル版（active）----
    {
        "tmpl": "full", "path": "LAVANDA/20260513_ボンドロシール", "file": "LAVANDA_ボンドロシール.md",
        "key": "LAVANDA_ボンドロシール", "task_project": "LAVANDA", "client": "LAVANDA（イエロー株式会社）",
        "title": "LAVANDA ボンドロシール", "priority": "P1", "start": "2026-05-13", "deadline": "2026-06-30",
        "tags": ["LAVANDA", "シール", "制作物"],
        "oneliner": "ボンドロシール制作・6末FIX→7頭発注",
        "theme": "LAVANDAブランドのボンドロシール", "deliverable": "シール版下（Illustrator）",
        "stakeholders_yaml": ['"[[菊田舞]]"'],
        "stakeholders_rows": [],
        "quick_links": "⚠ Notion/Drive/Slack 要追加",
        "warnings": "> - ダイカットのカット線オフセット確認（reference_illustrator_diecut_offset）",
        "file_rows": ["> | `受領データ/` | クライアント受領素材 |", "> | `_ai-drafts/` | CORIN出力着地 |"],
        "meeting_rows": ["> - ドロップシール議事メモは [[LAVANDA_ドロップシール]] 側 comms/ 参照"],
        "todo_rows": "> - [ ] 6末FIXに向けた最終確認\n> - [ ] Notion/Drive/Slack リンク",
        "notes_rows": "> - 姉妹案件：[[LAVANDA_ドロップシール]]",
    },
    {
        "tmpl": "full", "path": "小山/20260405_father-brand", "file": "小山_father-brand.md",
        "key": "小山_father-brand", "task_project": "小山新規", "client": "小山慶一郎（NEWS）／Starto",
        "title": "小山 Father Brand", "priority": "P1", "start": "2026-04-05", "deadline": "null",
        "tags": ["小山", "IP", "ブランド提案", "D2C"],
        "oneliner": "NEWS小山慶一郎さんライフスタイルIPブランド提案・Starto承認済み",
        "theme": "小山慶一郎さんのライフスタイルD2Cブランド立ち上げ提案",
        "deliverable": "ブランド提案資料（PPTX）", "concept": "Father Brand コンセプト",
        "stakeholders_yaml": ['"[[小山慶一郎]]"'],
        "quick_links": "[📄 提案v4](proposal_v4.md) ・ [📊 提案資料PDF](提案資料/koyama_d2c_brand_proposal_v2.pptx.pdf)",
        "warnings": "> - Starto承認フロー遵守・本人IP表現の確認必須",
        "file_rows": ["> | `proposal_v4.md` | 最新提案 |", "> | `提案資料/` | PPTX提案版 |", "> | `market_analysis_v1.md` | 市場分析 |", "> | `critic_review_v3.md` | レビュー |"],
        "meeting_rows": ["> - [[feedback_log|📝 feedback_log]] — 提案フィードバック履歴"],
        "todo_rows": "> - [ ] 提案先の次アクション確認",
        "notes_rows": "> - proposal_v4 が最新版",
    },
    {
        "tmpl": "full", "path": "20260413_ZOAxI'm_donut", "file": "ZOAxIm_donut.md",
        "key": "ZOAxIm_donut", "task_project": "imdonut", "client": "ZO_FRIENDS × I'm donut?",
        "title": "ZOA × I'm donut コラボ", "priority": "P2", "start": "2026-04-13", "deadline": "null",
        "tags": ["imdonut", "ZOA", "グッズ", "コラボ", "シール"],
        "oneliner": "ZOA × I'm donut? コラボグッズ（ぷっくりシール・前髪クリップ）",
        "theme": "ZO_FRIENDS × I'm donut? コラボグッズ制作",
        "deliverable": "グッズ版下（シール・前髪クリップ）",
        "quick_links": "[📊 ZOグッズ案PPTX](ZOグッズ_0330.pptx) ・ 受領データ：ZO_FRIENDS Communication Guide",
        "warnings": "> - ZO_FRIENDS Partner Communication Guide のレギュレーション遵守",
        "file_rows": ["> | `受領データ/` | ZO_FRIENDSガイドライン・pkg |", "> | `シール/` | ぷっくりシール版下 |", "> | `前髪クリップ/` | 前髪クリップ |", "> | `素材/` | 制作素材 |"],
        "todo_rows": "> - [ ] ぷっくりシール確認",
        "notes_rows": "> - 別名：imdonut",
    },
    {
        "tmpl": "full", "path": "81fes/20260318_81", "file": "81fes_20260318.md",
        "key": "81fes_20260318", "task_project": "81fes", "client": "81 Produce / 81fes",
        "title": "81fes グッズ制作", "priority": "P2", "start": "2026-03-18", "deadline": "null",
        "tags": ["81fes", "グッズ", "イベント", "制作物"],
        "oneliner": "81fes ロックT位置指示・タオル版下・バナー制作",
        "theme": "81fes イベントグッズ（ロックT・タオル・バナー）",
        "deliverable": "グッズ版下・バナー",
        "quick_links": "[📄 README](README.md) ・ [📝 バナー依頼](comms/2026-05-18_ちからさん依頼_バナーイメージ集め.md)",
        "file_rows": ["> | `入稿データ/` | ロックT入稿データ |", "> | `受領データ/` | 受領素材 |", "> | `AIリンク用/` | AI素材 |", "> | `comms/` | 依頼ログ |"],
        "meeting_rows": ["> - [[2026-05-18_ちからさん依頼_バナーイメージ集め|📝 バナーイメージ依頼]]"],
        "todo_rows": "> - [ ] ロックT位置指示",
        "notes_rows": "> - ",
    },
    {
        "tmpl": "full", "path": "GOK/20260426_カット編集", "file": "GOK_20260426_カット編集.md",
        "key": "GOK_20260426_カット編集", "task_project": "GOK", "client": "GOK",
        "title": "GOK カット編集・レタッチ", "priority": "P2", "start": "2026-04-26", "deadline": "null",
        "tags": ["GOK", "レタッチ", "動画編集", "制作物"],
        "oneliner": "GOK 物撮り＆LOOKレタッチ・カット編集",
        "theme": "GOK 物撮り・LOOKレタッチ・動画カット編集",
        "deliverable": "レタッチ画像・編集動画",
        "stakeholders_yaml": ['"[[福島]]"', '"[[ちからさん]]"'],
        "quick_links": "⚠ Drive/Slack 要追加",
        "file_rows": ["> | `受領データ/` | 物撮り・LOOK素材 |", "> | `Adobe Premiere Pro Auto-Save/` | 編集データ |"],
        "todo_rows": "> - [ ] レタッチ納品確認",
        "notes_rows": "> - 関連：GOK_20260225 / GOK_20260227（過去案件）",
    },
    {
        "tmpl": "full", "path": "20260507_Dole_coconut", "file": "Dole_coconut.md",
        "key": "Dole_coconut", "task_project": "Dole", "client": "Dole / CityCamp",
        "title": "Dole coconut（ココナッツの湯）", "priority": "P2", "start": "2026-05-07", "deadline": "null",
        "tags": ["Dole", "ブランディング", "制作物"],
        "oneliner": "Dole coconut（CityCamp様・ココナッツの湯）",
        "theme": "Dole coconut ブランディング制作",
        "deliverable": "⚠ 要記入",
        "quick_links": "[📄 請求書PDF](請求書_CityCamp様_ココナッツの湯.pdf)",
        "file_rows": ["> | `請求書_CityCamp様_ココナッツの湯.pdf` | 請求書 |", "> | `_ai-drafts/` | CORIN出力着地 |"],
        "todo_rows": "> - [ ] 案件概要・納品物の確認",
        "notes_rows": "> - CityCamp様 ココナッツの湯 案件",
    },
    {
        "tmpl": "full", "path": "20260519_品質表示スキル", "file": "品質表示スキル.md",
        "key": "品質表示スキル", "task_project": "AI推進", "client": "社内（青木さん依頼）",
        "title": "品質表示タグ生成ツール", "priority": "P1", "start": "2026-05-19", "deadline": "2026-05-28",
        "tags": ["AI推進", "ツール", "品質表示", "社内"],
        "oneliner": "品質表示タグ生成ツール v6・7軸独立判定方式（青木さん依頼）",
        "theme": "洗濯絵表示カケンコード自動判定ツール（/quality-label スキル）",
        "deliverable": "VEST向けXLSMテンプレ・スキル化",
        "concept": "7軸独立判定方式",
        "stakeholders_yaml": ['"[[青木]]"'],
        "quick_links": "[📄 requirements](requirements.md) ・ [📄 README](README.md) ・ [📝 青木さんヒアリング](aoki_hearing.md)",
        "warnings": "> - カケンコード判定の正確性・付記用語コード（F-1〜F-59）の照合",
        "file_rows": ["> | `requirements.md` | 要件定義 |", "> | `aoki_hearing.md` | 青木さんヒアリング |", "> | `templates/` | XLSMテンプレ |", "> | `test/` | 判定レポート |"],
        "todo_rows": "> - [ ] v6 完成確認",
        "notes_rows": "> - /quality-label スキルとして実装済み",
    },
    {
        "tmpl": "full", "path": "kemio/kemio-store", "file": "kemio-store.md",
        "key": "kemio-store", "task_project": "kemio", "client": "kemio",
        "title": "kemio store", "priority": "P2", "start": "null", "deadline": "null",
        "tags": ["kemio", "グッズ", "EC", "制作物"],
        "oneliner": "kemio store グッズ（7th・8th）・インスタライブ原稿",
        "theme": "kemio store グッズ制作・販売運用",
        "deliverable": "グッズ案・インスタライブ原稿",
        "quick_links": "[📄 7thグッズ案](💙 kemio store_7th.md) ・ [📄 8thグッズ案](💙 kemio store_8thグッズ案.md)",
        "file_rows": ["> | `💙 kemio store_7th.md` | 7thグッズ案 |", "> | `💙 kemio store_8thグッズ案.md` | 8thグッズ案 |", "> | `kemio storeの参考サイト集.md` | 参考サイト |"],
        "todo_rows": "> - [ ] 8thグッズ案の進行確認",
        "notes_rows": "> - 関連：[[kemio抹茶ブランド]]（別案件・human lounge）",
    },
    # ---- 新規フォルダ＋フル版 ----
    {
        "tmpl": "full", "path": "LAVANDA/20260531_ドロップシール", "file": "LAVANDA_ドロップシール.md",
        "key": "LAVANDA_ドロップシール", "task_project": "LAVANDA", "client": "LAVANDA（イエロー株式会社）",
        "title": "LAVANDA ドロップシール", "priority": "P1", "start": "2026-05-26", "deadline": "null",
        "tags": ["LAVANDA", "シール", "制作物"],
        "oneliner": "ドロップシール・5/26菊田さん提出・イエロー株西上原様",
        "theme": "LAVANDAブランドのドロップシール", "deliverable": "シール版下（Illustrator）",
        "stakeholders_yaml": ['"[[菊田舞]]"'],
        "quick_links": "[📝 イエロー仕様確認議事メモ](../20260513_ボンドロシール/comms/2026-05-25_LAVANDAドロップシール_イエロー仕様確認_議事メモ.md)",
        "warnings": "> - イエロー株式会社 西上原様 仕様確認済み内容を遵守",
        "file_rows": ["> | `_ai-drafts/` | CORIN出力着地 |"],
        "meeting_rows": ["> - [[2026-05-25_LAVANDAドロップシール_イエロー仕様確認_議事メモ|📝 2026-05-25 イエロー仕様確認]]"],
        "todo_rows": "> - [ ] 菊田さん提出フォロー",
        "notes_rows": "> - 姉妹案件：[[LAVANDA_ボンドロシール]]\n> - 議事メモは現状ボンドロシール comms/ に格納",
    },
    {
        "tmpl": "full", "path": "Konnekted_UX改善/20260507_ちからさんUX調査", "file": "ちからさんUX調査.md",
        "key": "ちからさんUX調査", "task_project": "ちからさんUX調査", "client": "社内（Konnekted）",
        "title": "Konnekted UX改善・ちからさんUX調査", "priority": "P2", "start": "2026-05-07", "deadline": "null",
        "tags": ["Konnekted", "UX調査", "リサーチ", "社内"],
        "oneliner": "Onlymaker競合4サービスのUX調査（ちからさん依頼）",
        "theme": "Onlymaker 競合4サービスのカスタマイズサービス UX調査",
        "deliverable": "UX調査レポート",
        "stakeholders_yaml": ['"[[ちからさん]]"'],
        "quick_links": "⚠ 調査資料 要追加",
        "file_rows": ["> | `_ai-drafts/` | CORIN出力着地 |"],
        "todo_rows": "> - [ ] Onlymaker競合UX調査の進行",
        "notes_rows": "> - 親フォルダ Konnekted_UX改善 は今後のUX改善案件の受け皿",
    },
    # ---- 軽量版（archived）----
    {
        "tmpl": "light", "path": "AM/20251211_AM_HAPPYBOX", "file": "AM_HAPPYBOX.md",
        "key": "AM_HAPPYBOX", "task_project": "Armillary.", "client": "Armillary.",
        "title": "Armillary. HAPPYBOX", "start": "2025-12-11", "deadline": "null",
        "tags": ["Armillary", "グッズ", "HAPPYBOX"],
        "oneliner": "Armillary. HAPPYBOX 企画（過去案件）",
        "theme": "Armillary. HAPPYBOX", "deliverable": "福袋企画",
        "quick_links": "⚠ 素材なし・概要要確認",
        "file_rows": ["> | `AIリンク用/` `SNS/` `ブツ画像/` `撮影素材/` `AMIさん作成/` | 各種素材 |"],
        "notes_rows": "> - 関連：[[AM_26SS]] [[AM_26AW]]",
    },
    {
        "tmpl": "light", "path": "GOK/20260225_GOK", "file": "GOK_20260225.md",
        "key": "GOK_20260225", "task_project": "GOK", "client": "GOK",
        "title": "GOK new character（2/25）", "start": "2026-02-25", "deadline": "null",
        "tags": ["GOK", "キャラクター", "制作物"],
        "oneliner": "GOK new character 制作（過去案件）",
        "theme": "GOK new character デザイン", "deliverable": "キャラクター版下",
        "quick_links": "[📄 new character PDF](GOK_new character_20260305.pdf)",
        "file_rows": ["> | `GOK_new character_20260305.pdf` | キャラ版下 |", "> | `受領データ/` | 受領素材 |"],
        "notes_rows": "> - 関連：[[GOK_20260227]] [[GOK_20260426_カット編集]]",
    },
    {
        "tmpl": "light", "path": "GOK/20260227_GOK", "file": "GOK_20260227.md",
        "key": "GOK_20260227", "task_project": "GOK", "client": "GOK",
        "title": "GOK store tee（2/27）", "start": "2026-02-27", "deadline": "null",
        "tags": ["GOK", "Tシャツ", "制作物"],
        "oneliner": "GOK store tee 版下制作（過去案件）",
        "theme": "GOK store tee デザイン・版下", "deliverable": "Tシャツ版下",
        "quick_links": "[📄 tee1版下](GOK_store tee1_版下_20260408.pdf)",
        "file_rows": ["> | `GOK_store tee1_版下_20260408.pdf` | tee1版下 |", "> | `GOK_store tee2_グランジ修正_版下_20260408/` | tee2版下 |", "> | `ちからさんから受領/` | 受領素材 |"],
        "notes_rows": "> - 関連：[[GOK_20260225]] [[GOK_20260426_カット編集]]",
    },
    {
        "tmpl": "light", "path": "AAA/20260507_売上分析", "file": "AAA_20260507_売上分析.md",
        "key": "AAA_20260507_売上分析", "task_project": "AAA", "client": "AAA",
        "title": "AAA 20th 売上分析", "start": "2026-05-07", "deadline": "null",
        "tags": ["AAA", "分析", "売上分析"],
        "oneliner": "AAA 20th 売上分析レポート",
        "theme": "AAA 20周年 売上分析", "deliverable": "売上分析レポート（PPTX）",
        "quick_links": "[📊 売上分析レポートv1](AAA_20th_売上分析レポート_v1.pptx)",
        "kpi_sales": "⚠ レポート内参照（AAA_20th_売上分析レポート_v1.pptx）",
        "file_rows": ["> | `AAA_20th_売上分析レポート_v1.pptx` | 分析レポート |"],
        "notes_rows": "> - 20周年関連の売上分析",
    },
    # ---- 新規フォルダ＋軽量版 ----
    {
        "tmpl": "light", "path": "20260521_avex往訪", "file": "avex往訪.md",
        "key": "avex往訪", "task_project": "avex", "client": "avex",
        "title": "avex 往訪", "start": "2026-05-21", "deadline": "null",
        "tags": ["avex", "往訪", "議事録"],
        "oneliner": "avex 往訪 5/21実施済（議事録分析待ち）",
        "theme": "avex 往訪・打ち合わせ", "deliverable": "議事録・議事録分析",
        "quick_links": "⚠ 議事録分析 要追加",
        "file_rows": ["> | `_ai-drafts/` | CORIN出力着地 |"],
        "notes_rows": "> - 5/21実施済・議事録分析待ち",
    },
]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    ok, skip = 0, 0
    for d in HUBS:
        folder = PROJ / d["path"]
        dest = folder / d["file"]
        if dest.exists():
            print(f"⚠ SKIP（既存）: {d['file']}", file=sys.stderr)
            skip += 1
            continue
        content = full_template(d) if d["tmpl"] == "full" else light_template(d)
        if args.dry_run:
            print(f"[DRY] {d['tmpl']:5s} → {d['path']}/{d['file']}")
            ok += 1
            continue
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "_ai-drafts").mkdir(exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        print(f"✅ {d['tmpl']:5s} {d['file']}", file=sys.stderr)
        ok += 1
    print(f"\n--- 生成 {ok}件 / スキップ {skip}件 ---", file=sys.stderr)


if __name__ == "__main__":
    main()
