#!/usr/bin/env python3
"""
Few-shot実験（LLM評価有効）結果の統計情報生成スクリプト
"""

import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
from datetime import datetime


def load_batch_results(batch_json: Path) -> List[Dict[str, Any]]:
    """batch_results.jsonから結果を読み込み"""
    with open(batch_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('results', [])


def extract_experiment_info(result: Dict[str, Any]) -> Dict[str, Any]:
    """実験結果から基本情報を抽出"""
    exp_info = result.get('experiment_info', {})
    
    bert_score = None
    bleu_score = None
    llm_score = None
    
    if 'evaluation' in result:
        eval_data = result['evaluation']
        if 'bert_score' in eval_data and eval_data['bert_score'] is not None:
            if isinstance(eval_data['bert_score'], dict):
                bert_score = eval_data['bert_score'].get('f1', 0)
            else:
                bert_score = float(eval_data['bert_score'])
        
        if 'bleu_score' in eval_data and eval_data['bleu_score'] is not None:
            bleu_score = float(eval_data['bleu_score'])
        
        if 'llm_score' in eval_data and eval_data['llm_score'] is not None:
            llm_score = float(eval_data['llm_score'])
    
    return {
        'experiment_id': exp_info.get('experiment_id', 'unknown'),
        'dataset': exp_info.get('dataset', 'unknown'),
        'aspect': exp_info.get('aspect', 'unknown'),
        'few_shot': exp_info.get('few_shot', 0),
        'gpt_model': exp_info.get('gpt_model', 'unknown'),
        'success': result.get('success', False),
        'bert_score': bert_score,
        'bleu_score': bleu_score,
        'llm_score': llm_score,
        'llm_response': result.get('process', {}).get('llm_response', ''),
        'error': exp_info.get('error')
    }


def calculate_statistics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """統計情報を計算（LLM評価含む）"""
    stats = {
        'total_experiments': len(results),
        'successful': 0,
        'failed': 0,
        'few_shot_stats': defaultdict(lambda: {'count': 0, 'bert_scores': [], 'bleu_scores': [], 'llm_scores': []}),
        'aspect_stats': defaultdict(lambda: {'count': 0, 'bert_scores': [], 'bleu_scores': [], 'llm_scores': []}),
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
        
        if info['llm_score'] is not None:
            stats['few_shot_stats'][few_shot]['llm_scores'].append(info['llm_score'])
            stats['aspect_stats'][aspect]['llm_scores'].append(info['llm_score'])
    
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
            if v['llm_scores']:
                v['avg_llm_score'] = sum(v['llm_scores']) / len(v['llm_scores'])
                v['min_llm_score'] = min(v['llm_scores'])
                v['max_llm_score'] = max(v['llm_scores'])
    
    return stats


def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(
        description="Few-shot実験（LLM評価有効）結果の統計情報を生成",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--batch-results', '-b',
        type=str,
        default=None,
        help='バッチ結果JSONファイルのパス'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='出力JSONファイルのパス'
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
        script_dir = Path(__file__).parent
        steam_dir = script_dir.parent
        
        batch_results_path = Path(args.batch_results) if args.batch_results else Path("results/fewshot_steam_llm_eval_20251127_114838/batch_results.json")
        output_path = Path(args.output) if args.output else steam_dir / "実験設定" / "fewshot_llm_eval_statistics.json"
        
        if not batch_results_path.exists():
            logger.error(f"バッチ結果ファイルが見つかりません: {batch_results_path}")
            return 1
        
        logger.info(f"結果を読み込み: {batch_results_path}")
        results = load_batch_results(batch_results_path)
        logger.info(f"読み込んだ結果数: {len(results)}")
        
        stats = calculate_statistics(results)
        logger.info("統計情報を計算完了")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'statistics': stats,
                'generated_at': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"統計情報を保存: {output_path}")
        logger.info("=" * 60)
        logger.info("統計情報生成完了")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())


















