#!/usr/bin/env python3
"""
論文執筆データのパスを自動収集し、JSON形式で出力するスクリプト
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

PROJECT_ROOT = Path(__file__).parent


def get_file_info(file_path: Path) -> Dict[str, Any]:
    """ファイルのメタデータを取得"""
    if not file_path.exists():
        return {
            "exists": False,
            "size": 0,
            "modified": None
        }
    
    stat = file_path.stat()
    return {
        "exists": True,
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "relative_path": str(file_path.relative_to(PROJECT_ROOT)),
        "absolute_path": str(file_path.absolute())
    }


def collect_directory_files(dir_path: Path, pattern: str = "*") -> List[Dict[str, Any]]:
    """ディレクトリ内のファイルを収集"""
    files = []
    if not dir_path.exists():
        return files
    
    for file_path in dir_path.glob(pattern):
        if file_path.is_file():
            files.append(get_file_info(file_path))
    
    return sorted(files, key=lambda x: x.get("relative_path", ""))


def collect_paper_data_paths() -> Dict[str, Any]:
    """論文執筆に必要なファイルパスを収集"""
    
    paths = {
        "generated_at": datetime.now().isoformat(),
        "project_root": str(PROJECT_ROOT),
        "sections": {
            "methodology": {
                "presentation_slides": [],
                "research_background": []
            },
            "experiment": {
                "prompt_configs": [],
                "experiment_settings": []
            },
            "results_and_discussion": {
                "experiment_results": [],
                "discussion_reports": [],
                "analysis_results": []
            }
        }
    }
    
    # 1. 手法（アプローチ）セクション
    
    # 中間発表資料
    presentation_dir = PROJECT_ROOT / "slide" / "中間発表"
    paths["sections"]["methodology"]["presentation_slides"].append(
        get_file_info(presentation_dir / "contrastive_label_xai_slide.md")
    )
    
    backup_dir = presentation_dir / "backup"
    backup_files = collect_directory_files(backup_dir, "*.md")
    paths["sections"]["methodology"]["presentation_slides"].extend(backup_files)
    
    # 研究背景・関連研究
    paths["sections"]["methodology"]["research_background"].append(
        get_file_info(PROJECT_ROOT / "論文" / "masterThesisJaSample.tex")
    )
    paths["sections"]["methodology"]["research_background"].append(
        get_file_info(PROJECT_ROOT / "results" / "20251119_153853" / "analysis_workspace" / "research_context.md")
    )
    paths["sections"]["methodology"]["research_background"].append(
        get_file_info(PROJECT_ROOT / ".cursor" / "rules" / "research-overview.mdc")
    )
    
    # 2. 実験セクション
    
    # プロンプト設定
    paths["sections"]["experiment"]["prompt_configs"].append(
        get_file_info(PROJECT_ROOT / "src" / "analysis" / "experiments" / "utils" / "config" / "paramaters.yml")
    )
    paths["sections"]["experiment"]["prompt_configs"].append(
        get_file_info(PROJECT_ROOT / "experiment_execution_prompt.md")
    )
    paths["sections"]["experiment"]["prompt_configs"].append(
        get_file_info(PROJECT_ROOT / "LLMエージェント実行プロンプト.md")
    )
    
    # 実験設定・計画
    paths["sections"]["experiment"]["experiment_settings"].append(
        get_file_info(PROJECT_ROOT / "実験マトリックス.json")
    )
    paths["sections"]["experiment"]["experiment_settings"].append(
        get_file_info(PROJECT_ROOT / "results" / "20251119_153853" / "batch_results.json")
    )
    
    # 3. 結果と考察セクション
    
    results_base = PROJECT_ROOT / "results" / "20251119_153853"
    
    # 実験結果データ
    paths["sections"]["results_and_discussion"]["experiment_results"].append(
        get_file_info(results_base / "batch_results.json")
    )
    
    individual_dir = results_base / "individual"
    individual_files = collect_directory_files(individual_dir, "*.json")
    paths["sections"]["results_and_discussion"]["experiment_results"].extend(individual_files)
    
    experiments_dir = results_base / "experiments"
    experiment_dirs = []
    if experiments_dir.exists():
        for exp_dir in experiments_dir.iterdir():
            if exp_dir.is_dir():
                exp_files = collect_directory_files(exp_dir, "*.json")
                experiment_dirs.extend(exp_files)
    paths["sections"]["results_and_discussion"]["experiment_results"].extend(experiment_dirs)
    
    # 考察レポート
    reports_dir = results_base / "analysis_workspace" / "reports"
    report_files = collect_directory_files(reports_dir, "*.md")
    paths["sections"]["results_and_discussion"]["discussion_reports"].extend(report_files)
    
    # 集計・分析結果
    paths["sections"]["results_and_discussion"]["analysis_results"].append(
        get_file_info(PROJECT_ROOT / "src" / "analysis" / "experiments" / "2025" / "10" / "10" / "aggregate_results.py")
    )
    paths["sections"]["results_and_discussion"]["analysis_results"].append(
        get_file_info(results_base / "analysis_workspace" / "analysis.log")
    )
    
    # 統計情報を追加
    total_files = 0
    total_size = 0
    existing_files = 0
    
    def count_files(section_data):
        nonlocal total_files, total_size, existing_files
        if isinstance(section_data, list):
            for item in section_data:
                if isinstance(item, dict) and "exists" in item:
                    total_files += 1
                    if item["exists"]:
                        existing_files += 1
                        total_size += item.get("size", 0)
        elif isinstance(section_data, dict):
            for value in section_data.values():
                count_files(value)
    
    count_files(paths["sections"])
    paths["statistics"] = {
        "total_files": total_files,
        "existing_files": existing_files,
        "missing_files": total_files - existing_files,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2)
    }
    
    return paths


def main():
    """メイン処理"""
    print("論文執筆データのパスを収集中...")
    
    paths_data = collect_paper_data_paths()
    
    # JSONファイルに出力
    output_path = PROJECT_ROOT / "paper_data_paths.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(paths_data, f, ensure_ascii=False, indent=2)
    
    print(f"パス情報を保存しました: {output_path}")
    print(f"\n統計情報:")
    print(f"  総ファイル数: {paths_data['statistics']['total_files']}")
    print(f"  存在するファイル: {paths_data['statistics']['existing_files']}")
    print(f"  存在しないファイル: {paths_data['statistics']['missing_files']}")
    print(f"  総サイズ: {paths_data['statistics']['total_size_mb']} MB")
    
    # テキストファイルにも出力（簡易版）
    txt_output_path = PROJECT_ROOT / "paper_data_paths.txt"
    with open(txt_output_path, "w", encoding="utf-8") as f:
        f.write("論文執筆データ ファイルパス一覧\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"生成日時: {paths_data['generated_at']}\n")
        f.write(f"プロジェクトルート: {paths_data['project_root']}\n\n")
        
        f.write("【手法セクション】\n")
        f.write("-" * 30 + "\n")
        f.write("中間発表資料:\n")
        for item in paths_data["sections"]["methodology"]["presentation_slides"]:
            if item.get("exists"):
                f.write(f"  {item['relative_path']}\n")
        f.write("\n研究背景・関連研究:\n")
        for item in paths_data["sections"]["methodology"]["research_background"]:
            if item.get("exists"):
                f.write(f"  {item['relative_path']}\n")
        
        f.write("\n【実験セクション】\n")
        f.write("-" * 30 + "\n")
        f.write("プロンプト設定:\n")
        for item in paths_data["sections"]["experiment"]["prompt_configs"]:
            if item.get("exists"):
                f.write(f"  {item['relative_path']}\n")
        f.write("\n実験設定・計画:\n")
        for item in paths_data["sections"]["experiment"]["experiment_settings"]:
            if item.get("exists"):
                f.write(f"  {item['relative_path']}\n")
        
        f.write("\n【結果と考察セクション】\n")
        f.write("-" * 30 + "\n")
        f.write(f"実験結果データ: {len([x for x in paths_data['sections']['results_and_discussion']['experiment_results'] if x.get('exists')])} ファイル\n")
        f.write(f"考察レポート: {len([x for x in paths_data['sections']['results_and_discussion']['discussion_reports'] if x.get('exists')])} ファイル\n")
        f.write("集計・分析結果:\n")
        for item in paths_data["sections"]["results_and_discussion"]["analysis_results"]:
            if item.get("exists"):
                f.write(f"  {item['relative_path']}\n")
    
    print(f"\nテキスト形式のパスリストも保存しました: {txt_output_path}")


if __name__ == "__main__":
    main()

