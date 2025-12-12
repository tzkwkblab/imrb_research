#!/usr/bin/env python3
"""
Few-shot実験結果収集スクリプト

実験結果を収集し、fewshot専用の構造に整理する。
"""

import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict
from datetime import datetime
import shutil


def load_results_from_batch_json(batch_json: Path) -> List[Dict[str, Any]]:
    """batch_results.jsonから結果を読み込み"""
    with open(batch_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('results', [])


def extract_experiment_info(result: Dict[str, Any]) -> Dict[str, Any]:
    """実験結果から基本情報を抽出"""
    exp_info = result.get('experiment_info', {})
    
    bert_score = None
    bleu_score = None
    
    if 'evaluation' in result:
        eval_data = result['evaluation']
        if 'bert_score' in eval_data and eval_data['bert_score'] is not None:
            if isinstance(eval_data['bert_score'], dict):
                bert_score = eval_data['bert_score'].get('f1', 0)
            else:
                bert_score = float(eval_data['bert_score'])
        
        if 'bleu_score' in eval_data and eval_data['bleu_score'] is not None:
            bleu_score = float(eval_data['bleu_score'])
    
    return {
        'experiment_id': exp_info.get('experiment_id', 'unknown'),
        'dataset': exp_info.get('dataset', 'unknown'),
        'aspect': exp_info.get('aspect', 'unknown'),
        'few_shot': exp_info.get('few_shot', 0),
        'gpt_model': exp_info.get('gpt_model', 'unknown'),
        'success': result.get('success', False),
        'bert_score': bert_score,
        'bleu_score': bleu_score,
        'llm_response': result.get('process', {}).get('llm_response', ''),
        'error': exp_info.get('error')
    }


def create_fewshot_comparison_table(results: List[Dict[str, Any]]) -> str:
    """Few-shot比較表を作成"""
    lines = ["## Few-shot影響分析表", ""]
    lines.append("| アスペクト | 0-shot BERT | 1-shot BERT | 3-shot BERT | 0-shot BLEU | 1-shot BLEU | 3-shot BLEU |")
    lines.append("|----------|-------------|-------------|-------------|-------------|-------------|-------------|")
    
    successful_results = [r for r in results if extract_experiment_info(r).get('success', False)]
    
    grouped = defaultdict(lambda: {0: {}, 1: {}, 3: {}})
    
    for result in successful_results:
        info = extract_experiment_info(result)
        aspect = info['aspect']
        few_shot = info['few_shot']
        
        if few_shot in [0, 1, 3]:
            grouped[aspect][few_shot] = info
    
    for aspect in sorted(grouped.keys()):
        group = grouped[aspect]
        
        def get_score(few_shot, score_type):
            info = group.get(few_shot, {})
            score = info.get(score_type)
            return f"{score:.4f}" if score is not None else "N/A"
        
        bert_0 = get_score(0, 'bert_score')
        bert_1 = get_score(1, 'bert_score')
        bert_3 = get_score(3, 'bert_score')
        bleu_0 = get_score(0, 'bleu_score')
        bleu_1 = get_score(1, 'bleu_score')
        bleu_3 = get_score(3, 'bleu_score')
        
        lines.append(f"| {aspect} | {bert_0} | {bert_1} | {bert_3} | {bleu_0} | {bleu_1} | {bleu_3} |")
    
    lines.append("")
    return "\n".join(lines)


def create_detailed_results_table(results: List[Dict[str, Any]]) -> str:
    """詳細結果表を作成"""
    lines = ["## 詳細結果表", ""]
    lines.append("| 実験ID | アスペクト | Few-shot | BERT | BLEU | ステータス |")
    lines.append("|--------|----------|----------|------|------|----------|")
    
    successful_results = [r for r in results if extract_experiment_info(r).get('success', False)]
    failed_results = [r for r in results if not extract_experiment_info(r).get('success', False)]
    
    for result in successful_results:
        info = extract_experiment_info(result)
        exp_id = info['experiment_id']
        aspect = info['aspect']
        few_shot = info['few_shot']
        bert = info['bert_score']
        bleu = info['bleu_score']
        
        bert_str = f"{bert:.4f}" if bert is not None else "N/A"
        bleu_str = f"{bleu:.4f}" if bleu is not None else "N/A"
        
        lines.append(f"| {exp_id} | {aspect} | {few_shot} | {bert_str} | {bleu_str} | 成功 |")
    
    for result in failed_results:
        info = extract_experiment_info(result)
        exp_id = info['experiment_id']
        aspect = info['aspect']
        few_shot = info['few_shot']
        error = info.get('error', 'Unknown error')
        
        lines.append(f"| {exp_id} | {aspect} | {few_shot} | N/A | N/A | 失敗: {error} |")
    
    lines.append("")
    return "\n".join(lines)


def calculate_statistics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """統計情報を計算"""
    stats = {
        'total_experiments': len(results),
        'successful': 0,
        'failed': 0,
        'few_shot_stats': defaultdict(lambda: {'count': 0, 'bert_scores': [], 'bleu_scores': []}),
        'aspect_stats': defaultdict(lambda: {'count': 0, 'bert_scores': [], 'bleu_scores': []}),
    }
    
    for result in results:
        info = extract_experiment_info(result)
        
        if info['success']:
            stats['successful'] += 1
        else:
            stats['failed'] += 1
        
        few_shot = info['few_shot']
        aspect = info['aspect']
        
        stats['few_shot_stats'][few_shot]['count'] += 1
        stats['aspect_stats'][aspect]['count'] += 1
        
        if info['bert_score'] is not None:
            stats['few_shot_stats'][few_shot]['bert_scores'].append(info['bert_score'])
            stats['aspect_stats'][aspect]['bert_scores'].append(info['bert_score'])
        
        if info['bleu_score'] is not None:
            stats['few_shot_stats'][few_shot]['bleu_scores'].append(info['bleu_score'])
            stats['aspect_stats'][aspect]['bleu_scores'].append(info['bleu_score'])
    
    for key in ['few_shot_stats', 'aspect_stats']:
        for k, v in stats[key].items():
            if v['bert_scores']:
                v['avg_bert_score'] = sum(v['bert_scores']) / len(v['bert_scores'])
                v['min_bert_score'] = min(v['bert_scores'])
                v['max_bert_score'] = max(v['bert_scores'])
            if v['bleu_scores']:
                v['avg_bleu_score'] = sum(v['bleu_scores']) / len(v['bleu_scores'])
                v['min_bleu_score'] = min(v['bleu_scores'])
                v['max_bleu_score'] = max(v['bleu_scores'])
    
    return stats


def generate_report(results: List[Dict[str, Any]], stats: Dict[str, Any], output_path: Path) -> None:
    """レポートを生成"""
    lines = []
    
    lines.append("# Steam Few-shot実験結果レポート")
    lines.append("")
    lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    lines.append("## 実行統計")
    lines.append("")
    lines.append(f"- 総実験数: {stats['total_experiments']}")
    lines.append(f"- 成功: {stats['successful']}")
    lines.append(f"- 失敗: {stats['failed']}")
    lines.append("")
    
    lines.append("## Few-shot別統計")
    lines.append("")
    lines.append("| Few-shot | 実験数 | 平均BERT | 最小BERT | 最大BERT | 平均BLEU | 最小BLEU | 最大BLEU |")
    lines.append("|----------|--------|----------|----------|----------|----------|----------|----------|")
    
    for few_shot in sorted(stats['few_shot_stats'].keys()):
        s = stats['few_shot_stats'][few_shot]
        count = s['count']
        avg_bert = f"{s.get('avg_bert_score', 0):.4f}" if s.get('avg_bert_score') else "N/A"
        min_bert = f"{s.get('min_bert_score', 0):.4f}" if s.get('min_bert_score') else "N/A"
        max_bert = f"{s.get('max_bert_score', 0):.4f}" if s.get('max_bert_score') else "N/A"
        avg_bleu = f"{s.get('avg_bleu_score', 0):.4f}" if s.get('avg_bleu_score') else "N/A"
        min_bleu = f"{s.get('min_bleu_score', 0):.4f}" if s.get('min_bleu_score') else "N/A"
        max_bleu = f"{s.get('max_bleu_score', 0):.4f}" if s.get('max_bleu_score') else "N/A"
        
        lines.append(f"| {few_shot} | {count} | {avg_bert} | {min_bert} | {max_bert} | {avg_bleu} | {min_bleu} | {max_bleu} |")
    
    lines.append("")
    
    lines.append(create_fewshot_comparison_table(results))
    lines.append(create_detailed_results_table(results))
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    logging.info(f"レポートを保存: {output_path}")


def copy_results_to_fewshot_dir(results_dir: Path, fewshot_dir: Path) -> None:
    """結果をfewshot専用ディレクトリにコピー"""
    fewshot_results_dir = fewshot_dir / "結果"
    fewshot_results_dir.mkdir(parents=True, exist_ok=True)
    
    batch_json = results_dir / "batch_results.json"
    if batch_json.exists():
        shutil.copy2(batch_json, fewshot_results_dir / "batch_results.json")
        logging.info(f"batch_results.jsonをコピー: {fewshot_results_dir}")
    
    individual_dir = results_dir / "individual"
    if individual_dir.exists():
        target_individual = fewshot_results_dir / "individual"
        if target_individual.exists():
            shutil.rmtree(target_individual)
        shutil.copytree(individual_dir, target_individual)
        logging.info(f"individualディレクトリをコピー: {target_individual}")


def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(
        description="Few-shot実験結果を収集・整理",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--results-dir', '-r',
        type=str,
        required=True,
        help='実験結果ディレクトリのパス'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default=None,
        help='出力ディレクトリ (default: 論文/結果/追加実験/fewshot/steam/)'
    )
    
    parser.add_argument(
        '--copy-results',
        action='store_true',
        help='結果ファイルをfewshotディレクトリにコピー'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='デバッグモード'
    )
    
    args = parser.parse_args()
    
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        results_dir = Path(args.results_dir)
        batch_json = results_dir / "batch_results.json"
        
        if not batch_json.exists():
            logger.error(f"結果ファイルが見つかりません: {batch_json}")
            return 1
        
        logger.info(f"結果を読み込み: {batch_json}")
        results = load_results_from_batch_json(batch_json)
        logger.info(f"読み込んだ結果数: {len(results)}")
        
        stats = calculate_statistics(results)
        logger.info(f"統計情報を計算完了")
        
        if args.output_dir:
            output_dir = Path(args.output_dir)
        else:
            script_dir = Path(__file__).parent
            output_dir = script_dir.parent
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = output_dir / "fewshot_results_report.md"
        logger.info("レポートを生成中...")
        generate_report(results, stats, report_path)
        
        stats_json_path = output_dir / "fewshot_statistics.json"
        with open(stats_json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'statistics': stats,
                'generated_at': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        logger.info(f"統計情報を保存: {stats_json_path}")
        
        if args.copy_results:
            logger.info("結果ファイルをコピー中...")
            copy_results_to_fewshot_dir(results_dir, output_dir)
        
        logger.info("=" * 60)
        logger.info("結果収集完了")
        logger.info(f"レポート: {report_path}")
        logger.info(f"統計情報: {stats_json_path}")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())














