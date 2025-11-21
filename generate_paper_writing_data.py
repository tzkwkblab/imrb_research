#!/usr/bin/env python3
"""
論文執筆用の統合マークダウンファイルを生成するスクリプト
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
PATHS_FILE = PROJECT_ROOT / "paper_data_paths.json"
PAPER_DATA_DIR = PROJECT_ROOT / "paper_data"
OUTPUT_FILE = PROJECT_ROOT / "paper_writing_data.md"


def read_file_content(file_path: Path, max_lines: int = None) -> str:
    """ファイルの内容を読み込む（最大行数制限あり）"""
    if not file_path.exists():
        return f"[ファイルが見つかりません: {file_path}]"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if max_lines and len(lines) > max_lines:
                content = "".join(lines[:max_lines])
                content += f"\n\n... (残り {len(lines) - max_lines} 行は省略) ...\n"
                return content
            return "".join(lines)
    except Exception as e:
        return f"[ファイル読み込みエラー: {e}]"


def get_file_summary(file_path: Path) -> str:
    """ファイルの要約情報を取得"""
    if not file_path.exists():
        return "ファイルが見つかりません"
    
    stat = file_path.stat()
    size_mb = stat.st_size / (1024 * 1024)
    
    if file_path.suffix == ".json":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    keys = list(data.keys())[:10]
                    return f"JSONファイル ({size_mb:.2f} MB), キー: {', '.join(keys)}"
                elif isinstance(data, list):
                    return f"JSONファイル ({size_mb:.2f} MB), {len(data)} 要素"
        except:
            pass
    
    return f"{file_path.suffix[1:].upper()}ファイル ({size_mb:.2f} MB)"


def generate_methodology_section(paths_data: Dict[str, Any]) -> str:
    """手法セクションを生成"""
    lines = []
    lines.append("# 手法（アプローチ）セクション\n")
    
    # 中間発表資料
    lines.append("## 中間発表資料\n")
    presentation_files = paths_data["sections"]["methodology"]["presentation_slides"]
    for item in presentation_files:
        if item.get("exists"):
            rel_path = item["relative_path"]
            file_path = PAPER_DATA_DIR / rel_path
            lines.append(f"### {Path(rel_path).name}\n")
            lines.append(f"**パス**: `{rel_path}`\n\n")
            content = read_file_content(file_path, max_lines=200)
            lines.append("```markdown\n")
            lines.append(content)
            lines.append("\n```\n\n")
    
    # 研究背景・関連研究
    lines.append("## 研究背景・関連研究\n")
    research_files = paths_data["sections"]["methodology"]["research_background"]
    for item in research_files:
        if item.get("exists"):
            rel_path = item["relative_path"]
            file_path = PAPER_DATA_DIR / rel_path
            lines.append(f"### {Path(rel_path).name}\n")
            lines.append(f"**パス**: `{rel_path}`\n\n")
            
            if rel_path.endswith(".tex"):
                # LaTeXファイルは要約のみ
                lines.append(f"**要約**: {get_file_summary(file_path)}\n\n")
                lines.append("```latex\n")
                content = read_file_content(file_path, max_lines=100)
                lines.append(content)
                lines.append("\n```\n\n")
            else:
                content = read_file_content(file_path, max_lines=300)
                lines.append("```markdown\n")
                lines.append(content)
                lines.append("\n```\n\n")
    
    return "".join(lines)


def generate_experiment_section(paths_data: Dict[str, Any]) -> str:
    """実験セクションを生成"""
    lines = []
    lines.append("# 実験セクション\n")
    
    # プロンプト設定
    lines.append("## プロンプト設定\n")
    prompt_files = paths_data["sections"]["experiment"]["prompt_configs"]
    for item in prompt_files:
        if item.get("exists"):
            rel_path = item["relative_path"]
            file_path = PAPER_DATA_DIR / rel_path
            lines.append(f"### {Path(rel_path).name}\n")
            lines.append(f"**パス**: `{rel_path}`\n\n")
            
            if rel_path.endswith(".yml"):
                content = read_file_content(file_path)
                lines.append("```yaml\n")
                lines.append(content)
                lines.append("\n```\n\n")
            else:
                content = read_file_content(file_path, max_lines=200)
                lines.append("```markdown\n")
                lines.append(content)
                lines.append("\n```\n\n")
    
    # 実験設定・計画
    lines.append("## 実験設定・計画\n")
    setting_files = paths_data["sections"]["experiment"]["experiment_settings"]
    for item in setting_files:
        if item.get("exists"):
            rel_path = item["relative_path"]
            file_path = PAPER_DATA_DIR / rel_path
            lines.append(f"### {Path(rel_path).name}\n")
            lines.append(f"**パス**: `{rel_path}`\n\n")
            
            if rel_path.endswith("batch_results.json"):
                # 大きなJSONファイルは要約版を使用
                summary_path = file_path.with_suffix(".summary.json")
                if summary_path.exists():
                    lines.append("**注意**: このファイルは大きいため、要約版を表示しています。\n\n")
                    content = read_file_content(summary_path)
                    lines.append("```json\n")
                    lines.append(content)
                    lines.append("\n```\n\n")
                else:
                    lines.append(f"**要約**: {get_file_summary(file_path)}\n\n")
            else:
                content = read_file_content(file_path, max_lines=100)
                lines.append("```json\n")
                lines.append(content)
                lines.append("\n```\n\n")
    
    return "".join(lines)


def generate_results_section(paths_data: Dict[str, Any]) -> str:
    """結果と考察セクションを生成"""
    lines = []
    lines.append("# 結果と考察セクション\n")
    
    # 実験結果データ
    lines.append("## 実験結果データ\n")
    result_files = paths_data["sections"]["results_and_discussion"]["experiment_results"]
    
    # 統計情報
    existing_results = [f for f in result_files if f.get("exists")]
    lines.append(f"**総ファイル数**: {len(existing_results)}\n\n")
    
    # 代表的なファイルを詳細に表示
    lines.append("### 代表的な実験結果（サンプル）\n\n")
    sample_count = 0
    for item in existing_results[:5]:  # 最初の5件
        rel_path = item["relative_path"]
        file_path = PAPER_DATA_DIR / rel_path
        lines.append(f"#### {Path(rel_path).name}\n")
        lines.append(f"**パス**: `{rel_path}`\n\n")
        content = read_file_content(file_path, max_lines=50)
        lines.append("```json\n")
        lines.append(content)
        lines.append("\n```\n\n")
        sample_count += 1
    
    if len(existing_results) > sample_count:
        lines.append(f"**その他の実験結果ファイル**: {len(existing_results) - sample_count} ファイル\n")
        lines.append("`paper_data/results/20251119_153853/individual/` および `experiments/` ディレクトリを参照\n\n")
    
    # 考察レポート
    lines.append("## 考察レポート\n")
    report_files = paths_data["sections"]["results_and_discussion"]["discussion_reports"]
    existing_reports = [f for f in report_files if f.get("exists")]
    lines.append(f"**総レポート数**: {len(existing_reports)}\n\n")
    
    # 代表的なレポートを詳細に表示
    lines.append("### 代表的な考察レポート（サンプル）\n\n")
    sample_count = 0
    for item in existing_reports[:10]:  # 最初の10件
        rel_path = item["relative_path"]
        file_path = PAPER_DATA_DIR / rel_path
        lines.append(f"#### {Path(rel_path).name}\n")
        lines.append(f"**パス**: `{rel_path}`\n\n")
        content = read_file_content(file_path, max_lines=100)
        lines.append("```markdown\n")
        lines.append(content)
        lines.append("\n```\n\n")
        sample_count += 1
    
    if len(existing_reports) > sample_count:
        lines.append(f"**その他の考察レポート**: {len(existing_reports) - sample_count} ファイル\n")
        lines.append("`paper_data/results/20251119_153853/analysis_workspace/reports/` ディレクトリを参照\n\n")
    
    # 集計・分析結果
    lines.append("## 集計・分析結果\n")
    analysis_files = paths_data["sections"]["results_and_discussion"]["analysis_results"]
    for item in analysis_files:
        if item.get("exists"):
            rel_path = item["relative_path"]
            file_path = PAPER_DATA_DIR / rel_path
            lines.append(f"### {Path(rel_path).name}\n")
            lines.append(f"**パス**: `{rel_path}`\n\n")
            
            if rel_path.endswith(".py"):
                content = read_file_content(file_path, max_lines=200)
                lines.append("```python\n")
                lines.append(content)
                lines.append("\n```\n\n")
            else:
                content = read_file_content(file_path, max_lines=200)
                lines.append("```\n")
                lines.append(content)
                lines.append("\n```\n\n")
    
    return "".join(lines)


def main():
    """メイン処理"""
    if not PATHS_FILE.exists():
        print(f"エラー: {PATHS_FILE} が見つかりません。")
        print("先に generate_paper_data_paths.py を実行してください。")
        return
    
    if not PAPER_DATA_DIR.exists():
        print(f"エラー: {PAPER_DATA_DIR} が見つかりません。")
        print("先に collect_paper_data.py を実行してください。")
        return
    
    print("論文執筆用の統合マークダウンファイルを生成中...")
    
    # パス情報を読み込み
    with open(PATHS_FILE, "r", encoding="utf-8") as f:
        paths_data = json.load(f)
    
    # マークダウンを生成
    markdown_content = []
    markdown_content.append("# 論文執筆データ統合ファイル\n\n")
    markdown_content.append(f"**生成日時**: {datetime.now().isoformat()}\n\n")
    markdown_content.append("このファイルは、Notebook LMに投入するための論文執筆データを統合したものです。\n\n")
    markdown_content.append("---\n\n")
    
    markdown_content.append(generate_methodology_section(paths_data))
    markdown_content.append("\n---\n\n")
    markdown_content.append(generate_experiment_section(paths_data))
    markdown_content.append("\n---\n\n")
    markdown_content.append(generate_results_section(paths_data))
    
    # ファイルに出力
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("".join(markdown_content))
    
    print(f"統合マークダウンファイルを生成しました: {OUTPUT_FILE}")
    print(f"ファイルサイズ: {round(OUTPUT_FILE.stat().st_size / (1024 * 1024), 2)} MB")


if __name__ == "__main__":
    main()

