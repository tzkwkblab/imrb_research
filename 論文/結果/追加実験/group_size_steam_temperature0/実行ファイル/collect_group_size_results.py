#!/usr/bin/env python3
"""
Group Size実験結果収集スクリプト

実験結果を収集し、group_size専用の構造に整理する。
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
    
    # experiment_idからgroup_sizeを抽出
    exp_id = exp_info.get('experiment_name', '')
    group_size = None
    for size in ['50', '100', '150', '200', '300']:
        if f'group_size_{size}' in exp_id:
            group_size = int(size)
            break
    
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
            if isinstance(eval_data['llm_score'], dict):
                llm_score = eval_data['llm_score'].get('normalized_score', 0)
            else:
                llm_score = float(eval_data['llm_score'])
    
    return {
        'experiment_id': exp_info.get('experiment_id', 'unknown'),
        'experiment_name': exp_info.get('experiment_name', 'unknown'),
        'dataset': exp_info.get('dataset', 'unknown'),
        'aspect': exp_info.get('aspect', 'unknown'),
        'group_size': group_size,
        'gpt_model': exp_info.get('gpt_model', 'unknown'),
        'success': result.get('success', False),
        'bert_score': bert_score,
        'bleu_score': bleu_score,
        'llm_score': llm_score,
        'llm_response': result.get('process', {}).get('llm_response', ''),
        'error': exp_info.get('error')
    }


def calculate_statistics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """統計情報を計算"""
    stats = {
        'total_experiments': len(results),
        'successful': 0,
        'failed': 0,
        'group_size_stats': defaultdict(lambda: {'count': 0, 'bert_scores': [], 'bleu_scores': [], 'llm_scores': []}),
        'aspect_stats': defaultdict(lambda: {'count': 0, 'bert_scores': [], 'bleu_scores': [], 'llm_scores': []}),
    }
    
    for result in results:
        info = extract_experiment_info(result)
        
        if info['success']:
            stats['successful'] += 1
        else:
            stats['failed'] += 1
        
        group_size = info['group_size']
        aspect = info['aspect']
        
        if group_size is not None:
            stats['group_size_stats'][group_size]['count'] += 1
            if info['bert_score'] is not None:
                stats['group_size_stats'][group_size]['bert_scores'].append(info['bert_score'])
            if info['bleu_score'] is not None:
                stats['group_size_stats'][group_size]['bleu_scores'].append(info['bleu_score'])
            if info['llm_score'] is not None:
                stats['group_size_stats'][group_size]['llm_scores'].append(info['llm_score'])
        
        stats['aspect_stats'][aspect]['count'] += 1
        if info['bert_score'] is not None:
            stats['aspect_stats'][aspect]['bert_scores'].append(info['bert_score'])
        if info['bleu_score'] is not None:
            stats['aspect_stats'][aspect]['bleu_scores'].append(info['bleu_score'])
        if info['llm_score'] is not None:
            stats['aspect_stats'][aspect]['llm_scores'].append(info['llm_score'])
    
    # 平均値・最小値・最大値を計算
    for group_size, v in stats['group_size_stats'].items():
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
    
    for aspect, v in stats['aspect_stats'].items():
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
        description="Group Size実験結果を収集し、統計情報を生成",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--batch-results', '-b',
        type=str,
        default=None,
        help='バッチ結果JSONファイルのパス (default: 論文/結果/追加実験/group_size_steam_temperature0/結果/batch_results.json)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='出力JSONファイルのパス (default: 論文/結果/追加実験/group_size_steam_temperature0/group_size_statistics.json)'
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        script_dir = Path(__file__).parent
        group_size_dir = script_dir.parent
        
        batch_results_path = Path(args.batch_results) if args.batch_results else group_size_dir / "結果" / "batch_results.json"
        output_path = Path(args.output) if args.output else group_size_dir / "group_size_statistics.json"
        
        if not batch_results_path.exists():
            logger.error(f"バッチ結果ファイルが見つかりません: {batch_results_path}")
            return 1
        
        logger.info(f"バッチ結果を読み込み: {batch_results_path}")
        results = load_results_from_batch_json(batch_results_path)
        
        logger.info(f"実験結果数: {len(results)}")
        
        logger.info("統計情報を計算中...")
        statistics = calculate_statistics(results)
        
        output_data = {
            'statistics': statistics
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"統計情報を保存: {output_path}")
        logger.info(f"成功: {statistics['successful']}件, 失敗: {statistics['failed']}件")
        
        return 0
        
    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())












