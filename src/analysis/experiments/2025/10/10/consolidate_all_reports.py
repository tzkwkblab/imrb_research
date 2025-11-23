#!/usr/bin/env python3
"""
全実験結果と考察レポートを統合して3つのMDファイルを生成するスクリプト

1. 実験結果統合MD: 全実験結果をまとめたもの
2. 考察統合MD: 全考察レポートをまとめたもの
3. 目次MD: 参照しやすい目次
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from datetime import datetime
import glob


def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def load_results_from_batch_json(file_path: Path) -> List[Dict[str, Any]]:
    """batch_results.jsonから結果を読み込み"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            results = data.get('results', [])
            return results
    except Exception as e:
        logging.warning(f"batch_results.json読み込みエラー ({file_path}): {e}")
        return []


def load_results_from_batch_experiment_json(file_path: Path) -> List[Dict[str, Any]]:
    """batch_experiment_*.jsonから結果を読み込み"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            results = data.get('results', [])
            return results
    except Exception as e:
        logging.warning(f"batch_experiment_*.json読み込みエラー ({file_path}): {e}")
        return []


def load_results_from_individual_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """個別結果JSONから結果を読み込み"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.warning(f"個別結果JSON読み込みエラー ({file_path}): {e}")
        return None


def collect_all_experiment_results(project_root: Path) -> List[Dict[str, Any]]:
    """
    全ディレクトリから実験結果を収集
    
    Returns:
        実験結果のリスト（重複あり）
    """
    all_results = []
    seen_ids = set()
    
    # A. results/ 配下
    results_dirs = list(project_root.glob("results/*/"))
    for result_dir in results_dirs:
        if not result_dir.is_dir():
            continue
        
        # batch_results.json
        batch_json = result_dir / "batch_results.json"
        if batch_json.exists():
            results = load_results_from_batch_json(batch_json)
            for r in results:
                exp_id = extract_experiment_id(r)
                if exp_id:
                    all_results.append({
                        'result': r,
                        'source_dir': str(result_dir),
                        'source_type': 'results/batch_results.json',
                        'timestamp': extract_timestamp_from_dir(result_dir.name)
                    })
        
        # individual/ ディレクトリ
        individual_dir = result_dir / "individual"
        if individual_dir.exists():
            for json_file in individual_dir.glob("*.json"):
                result = load_results_from_individual_json(json_file)
                if result:
                    exp_id = extract_experiment_id(result)
                    if exp_id:
                        all_results.append({
                            'result': result,
                            'source_dir': str(result_dir),
                            'source_type': 'results/individual',
                            'timestamp': extract_timestamp_from_dir(result_dir.name)
                        })
    
    # B. paper_data/results/ 配下
    paper_results_dirs = list(project_root.glob("paper_data/results/*/"))
    for result_dir in paper_results_dirs:
        if not result_dir.is_dir():
            continue
        
        batch_json = result_dir / "batch_results.json"
        if batch_json.exists():
            results = load_results_from_batch_json(batch_json)
            for r in results:
                exp_id = extract_experiment_id(r)
                if exp_id:
                    all_results.append({
                        'result': r,
                        'source_dir': str(result_dir),
                        'source_type': 'paper_data/results/batch_results.json',
                        'timestamp': extract_timestamp_from_dir(result_dir.name)
                    })
    
    # C. src/analysis/experiments/**/results/ 配下
    experiment_results_dirs = list(project_root.glob("src/analysis/experiments/**/results/*/"))
    for result_dir in experiment_results_dirs:
        if not result_dir.is_dir():
            continue
        
        # batch_experiment_*.json
        for batch_file in result_dir.glob("batch_experiment_*.json"):
            results = load_results_from_batch_experiment_json(batch_file)
            for r in results:
                exp_id = extract_experiment_id(r)
                if exp_id:
                    all_results.append({
                        'result': r,
                        'source_dir': str(result_dir),
                        'source_type': f'src/analysis/experiments/results/{batch_file.name}',
                        'timestamp': extract_timestamp_from_dir(result_dir.name)
                    })
        
        # 個別実験JSON（{experiment_name}_{timestamp}.json形式）
        for json_file in result_dir.glob("*_*.json"):
            if json_file.name.startswith("batch_experiment_"):
                continue
            result = load_results_from_individual_json(json_file)
            if result:
                exp_id = extract_experiment_id(result)
                if exp_id:
                    all_results.append({
                        'result': result,
                        'source_dir': str(result_dir),
                        'source_type': f'src/analysis/experiments/results/{json_file.name}',
                        'timestamp': extract_timestamp_from_dir(result_dir.name)
                    })
    
    logging.info(f"収集した実験結果数: {len(all_results)}")
    return all_results


def extract_experiment_id(result: Dict[str, Any]) -> Optional[str]:
    """実験結果からexperiment_idを抽出"""
    exp_info = result.get('experiment_info', {})
    exp_id = exp_info.get('experiment_id') or exp_info.get('experiment_name')
    return exp_id


def extract_timestamp_from_dir(dir_name: str) -> Optional[str]:
    """ディレクトリ名からタイムスタンプを抽出"""
    # YYYYMMDD_HHMMSS形式を想定
    if len(dir_name) >= 15 and dir_name.replace('_', '').replace('-', '').isdigit():
        return dir_name
    return None


def deduplicate_results(all_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    重複を排除（experiment_id + timestampで最新を優先）
    
    Returns:
        重複排除された実験結果のリスト
    """
    grouped = defaultdict(list)
    
    for item in all_results:
        exp_id = extract_experiment_id(item['result'])
        if exp_id:
            grouped[exp_id].append(item)
    
    deduplicated = []
    for exp_id, items in grouped.items():
        # タイムスタンプでソート（最新を優先、Noneは最後に）
        items.sort(key=lambda x: x.get('timestamp') or '', reverse=True)
        deduplicated.append(items[0])
    
    logging.info(f"重複排除後: {len(deduplicated)}件")
    return deduplicated


def collect_all_analysis_reports(project_root: Path) -> List[Dict[str, Any]]:
    """
    全考察レポートを収集
    
    Returns:
        考察レポートのリスト
    """
    all_reports = []
    
    # results/*/analysis_workspace/reports/
    for reports_dir in project_root.glob("results/*/analysis_workspace/reports/"):
        if not reports_dir.is_dir():
            continue
        
        for md_file in reports_dir.glob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                exp_id = md_file.stem
                all_reports.append({
                    'experiment_id': exp_id,
                    'content': content,
                    'source_path': str(md_file),
                    'source_dir': str(reports_dir.parent.parent),
                    'timestamp': extract_timestamp_from_dir(reports_dir.parent.parent.name)
                })
            except Exception as e:
                logging.warning(f"考察レポート読み込みエラー ({md_file}): {e}")
    
    # paper_data/results/*/analysis_workspace/reports/
    for reports_dir in project_root.glob("paper_data/results/*/analysis_workspace/reports/"):
        if not reports_dir.is_dir():
            continue
        
        for md_file in reports_dir.glob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                exp_id = md_file.stem
                all_reports.append({
                    'experiment_id': exp_id,
                    'content': content,
                    'source_path': str(md_file),
                    'source_dir': str(reports_dir.parent.parent),
                    'timestamp': extract_timestamp_from_dir(reports_dir.parent.parent.name)
                })
            except Exception as e:
                logging.warning(f"考察レポート読み込みエラー ({md_file}): {e}")
    
    # 重複排除（experiment_idで最新を優先）
    grouped = defaultdict(list)
    for report in all_reports:
        grouped[report['experiment_id']].append(report)
    
    deduplicated = []
    for exp_id, reports in grouped.items():
        reports.sort(key=lambda x: x.get('timestamp') or '', reverse=True)
        deduplicated.append(reports[0])
    
    logging.info(f"収集した考察レポート数: {len(deduplicated)}")
    return deduplicated


def extract_experiment_info(result: Dict[str, Any]) -> Dict[str, Any]:
    """実験結果から基本情報を抽出"""
    exp_info = result.get('experiment_info', {})
    
    return {
        'experiment_id': exp_info.get('experiment_id') or exp_info.get('experiment_name', 'unknown'),
        'dataset': exp_info.get('dataset', 'unknown'),
        'aspect': exp_info.get('aspect', 'unknown'),
        'domain': exp_info.get('domain'),
        'few_shot': exp_info.get('few_shot', 0),
        'gpt_model': exp_info.get('gpt_model', 'unknown'),
        'success': result.get('summary', {}).get('success', False) if 'summary' in result else result.get('success', False),
        'bert_score': result.get('evaluation', {}).get('bert_score'),
        'bleu_score': result.get('evaluation', {}).get('bleu_score'),
        'llm_score': result.get('evaluation', {}).get('llm_score'),
        'llm_response': result.get('process', {}).get('llm_response', ''),
        'error': exp_info.get('error')
    }


def generate_results_md(deduplicated_results: List[Dict[str, Any]], output_path: Path) -> None:
    """実験結果統合MDファイルを生成"""
    lines = []
    
    lines.append("# 全実験結果統合レポート")
    lines.append("")
    lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"総実験数: {len(deduplicated_results)}")
    lines.append("")
    
    # 統計情報
    successful = sum(1 for item in deduplicated_results 
                     if extract_experiment_info(item['result']).get('success', False))
    failed = len(deduplicated_results) - successful
    
    lines.append("## 実行統計")
    lines.append("")
    lines.append(f"- 総実験数: {len(deduplicated_results)}")
    lines.append(f"- 成功: {successful}")
    lines.append(f"- 失敗: {failed}")
    lines.append("")
    
    # データセット別にグループ化
    dataset_groups = defaultdict(list)
    for item in deduplicated_results:
        info = extract_experiment_info(item['result'])
        dataset = info['dataset']
        dataset_groups[dataset].append((item, info))
    
    # データセット別セクション
    for dataset in sorted(dataset_groups.keys()):
        lines.append(f"## データセット: {dataset}")
        lines.append("")
        
        # アスペクト別にさらにグループ化
        aspect_groups = defaultdict(list)
        for item, info in dataset_groups[dataset]:
            aspect = info['aspect']
            aspect_groups[aspect].append((item, info))
        
        for aspect in sorted(aspect_groups.keys()):
            lines.append(f"### アスペクト: {aspect}")
            lines.append("")
            
            # テーブルヘッダー
            lines.append("| 実験ID | Few-shot | GPTモデル | BERT | BLEU | LLM | 成功 | ソース |")
            lines.append("|--------|----------|-----------|------|------|-----|------|--------|")
            
            for item, info in sorted(aspect_groups[aspect], 
                                    key=lambda x: (x[1]['few_shot'], x[1]['gpt_model'])):
                exp_id = info['experiment_id']
                few_shot = info['few_shot']
                gpt_model = info['gpt_model']
                bert = info['bert_score']
                bleu = info['bleu_score']
                llm = info['llm_score']
                success = "✓" if info['success'] else "✗"
                source = item['source_type']
                
                bert_str = f"{bert:.4f}" if bert is not None else "N/A"
                bleu_str = f"{bleu:.4f}" if bleu is not None else "N/A"
                llm_str = f"{llm:.4f}" if llm is not None else "N/A"
                
                lines.append(f"| {exp_id} | {few_shot} | {gpt_model} | {bert_str} | {bleu_str} | {llm_str} | {success} | {source} |")
            
            lines.append("")
    
    # 失敗した実験
    failed_items = [item for item in deduplicated_results 
                   if not extract_experiment_info(item['result']).get('success', False)]
    if failed_items:
        lines.append("## 失敗した実験")
        lines.append("")
        for item in failed_items:
            info = extract_experiment_info(item['result'])
            exp_id = info['experiment_id']
            error = info.get('error', 'Unknown error')
            source = item['source_type']
            lines.append(f"- **{exp_id}**: {error} (ソース: {source})")
        lines.append("")
    
    # ファイルに保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    logging.info(f"実験結果統合MDを保存: {output_path}")


def generate_analysis_md(deduplicated_reports: List[Dict[str, Any]], output_path: Path) -> None:
    """考察統合MDファイルを生成"""
    lines = []
    
    lines.append("# 全考察レポート統合")
    lines.append("")
    lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"総レポート数: {len(deduplicated_reports)}")
    lines.append("")
    
    # 実験IDでソート
    sorted_reports = sorted(deduplicated_reports, key=lambda x: x['experiment_id'])
    
    for report in sorted_reports:
        exp_id = report['experiment_id']
        content = report['content']
        source_path = report['source_path']
        
        lines.append(f"## 実験ID: {exp_id}")
        lines.append("")
        lines.append(f"**ソース**: `{source_path}`")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(content)
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # ファイルに保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    logging.info(f"考察統合MDを保存: {output_path}")


def generate_index_md(
    deduplicated_results: List[Dict[str, Any]],
    deduplicated_reports: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """目次MDファイルを生成"""
    lines = []
    
    lines.append("# 実験結果・考察レポート目次")
    lines.append("")
    lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append(f"- 実験結果数: {len(deduplicated_results)}")
    lines.append(f"- 考察レポート数: {len(deduplicated_reports)}")
    lines.append("")
    
    # 実験結果の目次
    lines.append("## 実験結果一覧")
    lines.append("")
    
    # データセット別にグループ化
    dataset_groups = defaultdict(list)
    for item in deduplicated_results:
        info = extract_experiment_info(item['result'])
        dataset = info['dataset']
        dataset_groups[dataset].append((item, info))
    
    for dataset in sorted(dataset_groups.keys()):
        lines.append(f"### {dataset}")
        lines.append("")
        
        for item, info in sorted(dataset_groups[dataset], key=lambda x: x[1]['experiment_id']):
            exp_id = info['experiment_id']
            aspect = info['aspect']
            few_shot = info['few_shot']
            gpt_model = info['gpt_model']
            source = item['source_type']
            
            lines.append(f"- **{exp_id}**")
            lines.append(f"  - アスペクト: {aspect}")
            lines.append(f"  - Few-shot: {few_shot}, GPTモデル: {gpt_model}")
            lines.append(f"  - ソース: {source}")
            lines.append("")
    
    # 考察レポートの目次
    lines.append("## 考察レポート一覧")
    lines.append("")
    
    # 実験IDでソート
    sorted_reports = sorted(deduplicated_reports, key=lambda x: x['experiment_id'])
    
    for report in sorted_reports:
        exp_id = report['experiment_id']
        source_path = report['source_path']
        
        lines.append(f"- **{exp_id}**")
        lines.append(f"  - ソース: `{source_path}`")
        lines.append("")
    
    # 参照リンク
    lines.append("## 参照")
    lines.append("")
    lines.append("- [実験結果統合レポート](./consolidated_results.md)")
    lines.append("- [考察統合レポート](./consolidated_analysis.md)")
    lines.append("")
    
    # ファイルに保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    logging.info(f"目次MDを保存: {output_path}")


def main():
    """メイン実行"""
    logger = setup_logging()
    
    # プロジェクトルートを取得（このファイルから7階層上がプロジェクトルート）
    # src/analysis/experiments/2025/10/10/consolidate_all_reports.py
    # -> src/analysis/experiments/2025/10/10/ (parent)
    # -> src/analysis/experiments/2025/10/ (parent.parent)
    # -> src/analysis/experiments/2025/ (parent.parent.parent)
    # -> src/analysis/experiments/ (parent.parent.parent.parent)
    # -> src/analysis/ (parent.parent.parent.parent.parent)
    # -> src/ (parent.parent.parent.parent.parent.parent)
    # -> / (parent.parent.parent.parent.parent.parent.parent = プロジェクトルート)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent.parent.parent.parent
    
    # プロジェクトルートが見つからない場合は、resultsディレクトリがあるか確認
    if not (project_root / "results").exists():
        # 別の方法: 現在のディレクトリから探す
        cwd = Path.cwd()
        if (cwd / "results").exists():
            project_root = cwd
        else:
            # 環境変数から取得を試みる
            import os
            workspace = os.getenv("WORKSPACE_PATH") or os.getenv("PWD")
            if workspace and Path(workspace).exists():
                project_root = Path(workspace)
            else:
                raise FileNotFoundError("プロジェクトルートが見つかりません")
    
    output_dir = project_root / "paper_data" / "consolidated_reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"プロジェクトルート: {project_root}")
    logger.info(f"出力ディレクトリ: {output_dir}")
    
    logger.info("=" * 60)
    logger.info("全実験結果と考察レポートの統合を開始")
    logger.info("=" * 60)
    
    # 1. 全実験結果を収集
    logger.info("実験結果を収集中...")
    all_results = collect_all_experiment_results(project_root)
    
    # 2. 重複排除
    logger.info("重複を排除中...")
    deduplicated_results = deduplicate_results(all_results)
    
    # 3. 全考察レポートを収集
    logger.info("考察レポートを収集中...")
    deduplicated_reports = collect_all_analysis_reports(project_root)
    
    # 4. MDファイルを生成
    logger.info("MDファイルを生成中...")
    
    results_md_path = output_dir / "consolidated_results.md"
    generate_results_md(deduplicated_results, results_md_path)
    
    analysis_md_path = output_dir / "consolidated_analysis.md"
    generate_analysis_md(deduplicated_reports, analysis_md_path)
    
    index_md_path = output_dir / "index.md"
    generate_index_md(deduplicated_results, deduplicated_reports, index_md_path)
    
    logger.info("=" * 60)
    logger.info("統合完了")
    logger.info(f"出力ディレクトリ: {output_dir}")
    logger.info(f"- 実験結果統合: {results_md_path}")
    logger.info(f"- 考察統合: {analysis_md_path}")
    logger.info(f"- 目次: {index_md_path}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

