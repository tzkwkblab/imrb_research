#!/usr/bin/env python3
"""
論文執筆データを収集し、paper_data/ディレクトリにコピーするスクリプト
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List
import sys

PROJECT_ROOT = Path(__file__).parent
PATHS_FILE = PROJECT_ROOT / "paper_data_paths.json"
OUTPUT_DIR = PROJECT_ROOT / "paper_data"

# 大きなファイルのサイズ閾値（MB）
LARGE_FILE_THRESHOLD_MB = 10


def create_summary_for_json(json_path: Path, output_path: Path) -> None:
    """大きなJSONファイルの要約版を作成"""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        summary = {}
        
        # 実験計画情報を抽出
        if "experiment_plan" in data:
            summary["experiment_plan"] = data["experiment_plan"]
        
        # 実行情報を抽出
        if "execution_info" in data:
            summary["execution_info"] = data["execution_info"]
        
        # 結果の統計情報のみ抽出（最初の数件のサンプル）
        if "results" in data and isinstance(data["results"], list):
            summary["results_count"] = len(data["results"])
            summary["results_sample"] = data["results"][:5]  # 最初の5件のみ
        
        # メタデータ
        summary["_metadata"] = {
            "original_file": str(json_path.relative_to(PROJECT_ROOT)),
            "original_size_mb": round(json_path.stat().st_size / (1024 * 1024), 2),
            "note": "This is a summary version. Full data available in the original file."
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"  要約版を作成: {output_path.relative_to(PROJECT_ROOT)}")
    except Exception as e:
        print(f"  警告: JSON要約の作成に失敗しました ({json_path}): {e}")


def copy_file_with_structure(source_path: Path, target_base: Path, relative_path: str) -> bool:
    """ファイルをディレクトリ構造を維持してコピー"""
    if not source_path.exists():
        print(f"  スキップ（存在しない）: {relative_path}")
        return False
    
    target_path = target_base / relative_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_size_mb = source_path.stat().st_size / (1024 * 1024)
    
    # 大きなファイルの場合は要約版も作成
    if file_size_mb > LARGE_FILE_THRESHOLD_MB and source_path.suffix == ".json":
        # 元のファイルもコピー
        shutil.copy2(source_path, target_path)
        print(f"  コピー完了: {relative_path} ({file_size_mb:.2f} MB)")
        
        # 要約版を作成
        summary_path = target_path.with_suffix(".summary.json")
        create_summary_for_json(source_path, summary_path)
    else:
        shutil.copy2(source_path, target_path)
        print(f"  コピー完了: {relative_path} ({file_size_mb:.2f} MB)")
    
    return True


def collect_files_from_section(section_data: Any, target_base: Path, copied_count: List[int]) -> None:
    """セクション内のファイルを再帰的に収集"""
    if isinstance(section_data, list):
        for item in section_data:
            if isinstance(item, dict) and "relative_path" in item and item.get("exists"):
                if copy_file_with_structure(
                    PROJECT_ROOT / item["relative_path"],
                    target_base,
                    item["relative_path"]
                ):
                    copied_count[0] += 1
    elif isinstance(section_data, dict):
        for value in section_data.values():
            collect_files_from_section(value, target_base, copied_count)


def main():
    """メイン処理"""
    if not PATHS_FILE.exists():
        print(f"エラー: {PATHS_FILE} が見つかりません。")
        print("先に generate_paper_data_paths.py を実行してください。")
        sys.exit(1)
    
    print("論文執筆データを収集中...")
    print(f"出力先: {OUTPUT_DIR}")
    
    # パス情報を読み込み
    with open(PATHS_FILE, "r", encoding="utf-8") as f:
        paths_data = json.load(f)
    
    # 出力ディレクトリを作成
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # 統計情報
    copied_count = [0]
    total_size = 0
    
    # 各セクションのファイルをコピー
    print("\n【手法セクション】")
    print("-" * 50)
    for category, files in paths_data["sections"]["methodology"].items():
        print(f"\n{category}:")
        collect_files_from_section(files, OUTPUT_DIR, copied_count)
    
    print("\n【実験セクション】")
    print("-" * 50)
    for category, files in paths_data["sections"]["experiment"].items():
        print(f"\n{category}:")
        collect_files_from_section(files, OUTPUT_DIR, copied_count)
    
    print("\n【結果と考察セクション】")
    print("-" * 50)
    for category, files in paths_data["sections"]["results_and_discussion"].items():
        print(f"\n{category}:")
        collect_files_from_section(files, OUTPUT_DIR, copied_count)
    
    # 統計情報を計算
    for root, dirs, files in os.walk(OUTPUT_DIR):
        for file in files:
            file_path = Path(root) / file
            total_size += file_path.stat().st_size
    
    print("\n" + "=" * 50)
    print("収集完了")
    print(f"  コピーしたファイル数: {copied_count[0]}")
    print(f"  総サイズ: {round(total_size / (1024 * 1024), 2)} MB")
    print(f"  出力先: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

