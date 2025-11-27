#!/usr/bin/env python3
"""
メイン実験結果の統計情報生成スクリプト
"""

import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_batch_results(batch_results_path: Path) -> Dict[str, Any]:
    """バッチ結果を読み込み"""
    if not batch_results_path.exists():
        raise FileNotFoundError(f"バッチ結果ファイルが見つかりません: {batch_results_path}")
    
    with open(batch_results_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_statistics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """統計情報を計算"""
    statistics = {
        'total_experiments': len(results),
        'successful': 0,
        'failed': 0,
        'dataset_stats': defaultdict(lambda: {
            'count': 0,
            'bert_scores': [],
            'bleu_scores': [],
            'llm_scores': []
        }),
        'aspect_stats': defaultdict(lambda: {
            'count': 0,
            'bert_scores': [],
            'bleu_scores': [],
            'llm_scores': []
        })
    }
    
    for result in results:
        exp_info = result.get('experiment_info', {})
        dataset = exp_info.get('dataset', 'unknown')
        aspect = exp_info.get('aspect', 'unknown')
        
        eval_data = result.get('evaluation', {})
        
        # BERTスコア
        bert_score = None
        if 'bert_score' in eval_data and eval_data['bert_score'] is not None:
            if isinstance(eval_data['bert_score'], dict):
                bert_score = eval_data['bert_score'].get('f1', 0)
            else:
                bert_score = float(eval_data['bert_score'])
        
        # BLEUスコア
        bleu_score = None
        if 'bleu_score' in eval_data and eval_data['bleu_score'] is not None:
            bleu_score = float(eval_data['bleu_score'])
        
        # LLMスコア
        llm_score = None
        if 'llm_score' in eval_data and eval_data['llm_score'] is not None:
            if isinstance(eval_data['llm_score'], dict):
                llm_score = eval_data['llm_score'].get('score', 0)
            else:
                llm_score = float(eval_data['llm_score'])
        
        if bert_score is not None or bleu_score is not None:
            statistics['successful'] += 1
            
            # データセット別統計
            if bert_score is not None:
                statistics['dataset_stats'][dataset]['bert_scores'].append(bert_score)
            if bleu_score is not None:
                statistics['dataset_stats'][dataset]['bleu_scores'].append(bleu_score)
            if llm_score is not None:
                statistics['dataset_stats'][dataset]['llm_scores'].append(llm_score)
            statistics['dataset_stats'][dataset]['count'] += 1
            
            # アスペクト別統計
            if bert_score is not None:
                statistics['aspect_stats'][aspect]['bert_scores'].append(bert_score)
            if bleu_score is not None:
                statistics['aspect_stats'][aspect]['bleu_scores'].append(bleu_score)
            if llm_score is not None:
                statistics['aspect_stats'][aspect]['llm_scores'].append(llm_score)
            statistics['aspect_stats'][aspect]['count'] += 1
        else:
            statistics['failed'] += 1
    
    # 平均値・最小値・最大値を計算
    for dataset, stats in statistics['dataset_stats'].items():
        if stats['bert_scores']:
            stats['avg_bert_score'] = sum(stats['bert_scores']) / len(stats['bert_scores'])
            stats['min_bert_score'] = min(stats['bert_scores'])
            stats['max_bert_score'] = max(stats['bert_scores'])
        if stats['bleu_scores']:
            stats['avg_bleu_score'] = sum(stats['bleu_scores']) / len(stats['bleu_scores'])
            stats['min_bleu_score'] = min(stats['bleu_scores'])
            stats['max_bleu_score'] = max(stats['bleu_scores'])
        if stats['llm_scores']:
            stats['avg_llm_score'] = sum(stats['llm_scores']) / len(stats['llm_scores'])
            stats['min_llm_score'] = min(stats['llm_scores'])
            stats['max_llm_score'] = max(stats['llm_scores'])
    
    for aspect, stats in statistics['aspect_stats'].items():
        if stats['bert_scores']:
            stats['avg_bert_score'] = sum(stats['bert_scores']) / len(stats['bert_scores'])
            stats['min_bert_score'] = min(stats['bert_scores'])
            stats['max_bert_score'] = max(stats['bert_scores'])
        if stats['bleu_scores']:
            stats['avg_bleu_score'] = sum(stats['bleu_scores']) / len(stats['bleu_scores'])
            stats['min_bleu_score'] = min(stats['bleu_scores'])
            stats['max_bleu_score'] = max(stats['bleu_scores'])
        if stats['llm_scores']:
            stats['avg_llm_score'] = sum(stats['llm_scores']) / len(stats['llm_scores'])
            stats['min_llm_score'] = min(stats['llm_scores'])
            stats['max_llm_score'] = max(stats['llm_scores'])
    
    # defaultdictを通常のdictに変換
    statistics['dataset_stats'] = dict(statistics['dataset_stats'])
    statistics['aspect_stats'] = dict(statistics['aspect_stats'])
    
    return statistics


def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(
        description="メイン実験結果の統計情報を生成",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--batch-results', '-b',
        type=str,
        default=None,
        help='バッチ結果JSONファイルのパス (default: 論文/結果/追加実験/main_experiment_rerun_temperature0/results/batch_results.json)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='出力JSONファイルのパス (default: 論文/結果/追加実験/main_experiment_rerun_temperature0/main_experiment_statistics.json)'
    )
    
    args = parser.parse_args()
    
    try:
        script_dir = Path(__file__).parent
        experiment_dir = script_dir.parent
        
        batch_results_path = Path(args.batch_results) if args.batch_results else experiment_dir / "results" / "batch_results.json"
        output_path = Path(args.output) if args.output else experiment_dir / "main_experiment_statistics.json"
        
        if not batch_results_path.exists():
            logger.error(f"バッチ結果ファイルが見つかりません: {batch_results_path}")
            return 1
        
        logger.info(f"バッチ結果を読み込み: {batch_results_path}")
        data = load_batch_results(batch_results_path)
        results = data.get('results', [])
        
        logger.info(f"実験結果数: {len(results)}")
        
        logger.info("統計情報を計算中...")
        statistics = calculate_statistics(results)
        
        output_data = {
            'statistics': statistics,
            'experiment_plan': data.get('experiment_plan', {})
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"統計情報を保存: {output_path}")
        logger.info(f"総実験数: {statistics['total_experiments']}")
        logger.info(f"成功: {statistics['successful']}")
        logger.info(f"失敗: {statistics['failed']}")
        logger.info(f"データセット数: {len(statistics['dataset_stats'])}")
        logger.info(f"アスペクト数: {len(statistics['aspect_stats'])}")
        
        return 0
        
    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

