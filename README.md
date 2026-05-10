# CORIN Dashboard

ゆりこ専用の朝の3分ダッシュボード。

## URL
https://fujimoto-cpu.github.io/dashboard/

## 構成
- `index.html` — ダッシュボード本体
- `style.css` — グラスモーフィズム＋色テーマ自動変化
- `theme.js` — 曜日・季節・特別日で色テーマ切替＋当日URL組み立て＋data.js流し込み
- `aggregate.py` — 毎朝7:25 JSTにGitHub Actionsで起動。CORIN手紙生成・既存レポート集約・brand-analysisランダム抽出 → `data.js` を出力
- `.github/workflows/aggregate.yml` — スケジュール定義

## 設計思想
- **pull型**：Slack DM配信を停止し、ゆりこが読みたい時に取りに行く
- **朝の儀式**：CORINからの手紙＋色テーマ自動変化で「毎朝開きたくなる」体験
- **集中時間優先**：通知ゼロ・1日1ページで全カテゴリ把握

## ロールバック
- `data.js` が無くても `index.html` は静的プレースホルダーで動く
- 既存スキルのSlack配信停止箇所はコメントアウト保持・1行で復活可能
