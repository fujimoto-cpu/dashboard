#!/usr/bin/env python3
"""
folder_reorg.py — projects/ フォルダ整理（移動・リネーム）

ゆりこ承認プラン（2026-05-31）に従い、projects/ 配下のフォルダを再構成。

使い方:
  python3 folder_reorg.py --dry-run   # 何が起きるか確認のみ
  python3 folder_reorg.py             # 実行
"""

import argparse
import shutil
import sys
from pathlib import Path

PROJECTS = Path("/Users/yuriko/Documents/corin/00_🏢 company/projects")

# (source, dest) のペアリスト
OPERATIONS = [
    # A. 終了した案件/ へ移動 3件
    (PROJECTS / "kemio/kemio_旧", PROJECTS / "終了した案件/kemio_旧"),
    (PROJECTS / "kemio/podcast書き起こし", PROJECTS / "終了した案件/kemio_podcast書き起こし"),
    (PROJECTS / "armillary/20260319_ドリームワークス顛末書", PROJECTS / "終了した案件/armillary_20260319_ドリームワークス顛末書"),
    # B. ★削除リネーム
    (PROJECTS / "AM/★AM_26SS", PROJECTS / "AM/20251125_AM_26SS"),
    (PROJECTS / "AM/★AM_26AW", PROJECTS / "AM/20260519_AM_26AW"),
    # C. クライアントフォルダ化 or 単発リネーム
    # LAVANDA: フォルダ階層化
    (PROJECTS / "LAVANDA_ボンドロシール", PROJECTS / "LAVANDA/20260513_ボンドロシール"),
    # 小山: 「koyama」→「小山」変更＋階層化
    (PROJECTS / "koyama-father-brand", PROJECTS / "小山/20260405_father-brand"),
    # Dole: 正しい表記「Dole_coconut」＋日付プレフィクス
    (PROJECTS / "Dole_ococonatsu", PROJECTS / "20260507_Dole_coconut"),
    # ZOAxI'm donut: 正しい表記＋日付プレフィクス（アポストロフィはファイルパスに含む）
    (PROJECTS / "ZOAxI'mドーナツ", PROJECTS / "20260413_ZOAxI'm_donut"),
]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    success, skipped, failed = 0, 0, 0
    for src, dst in OPERATIONS:
        if not src.exists():
            print(f"⚠ SKIP（元なし）: {src.name}", file=sys.stderr)
            skipped += 1
            continue
        if dst.exists():
            print(f"⚠ SKIP（先既存）: {dst}", file=sys.stderr)
            skipped += 1
            continue
        if args.dry_run:
            print(f"[DRY] {src} → {dst}")
            success += 1
            continue
        try:
            # 親ディレクトリが必要な場合は作成
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            print(f"✅ {src.name} → {dst.parent.name}/{dst.name}")
            success += 1
        except Exception as e:
            print(f"❌ FAIL: {src} → {dst}: {e}", file=sys.stderr)
            failed += 1

    print(f"\n--- 完了: 成功 {success}件 / スキップ {skipped}件 / 失敗 {failed}件 ---", file=sys.stderr)

    if not args.dry_run and success > 0:
        # 空になった armillary/ 削除
        armillary = PROJECTS / "armillary"
        if armillary.exists() and not any(armillary.iterdir()):
            armillary.rmdir()
            print(f"✅ 空になった armillary/ 削除", file=sys.stderr)


if __name__ == "__main__":
    main()
