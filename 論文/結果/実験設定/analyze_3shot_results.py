#!/usr/bin/env python3
"""
3-shot実験結果分析スクリプト

3-shot実験の結果を分析し、Markdownファイルにまとめる。
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

def load_results(results_dir: str) -> Dict[str, Any]:
    """結果ファイルを読み込む"""
    results_path = Path(results_dir) / "batch_results.json"
    
    if not results_path.exists():
        raise FileNotFoundError(f"結果ファイルが見つかりません: {results_path}")
    
    with open(results_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """結果を分析"""
    experiments = results.get('results', [])
    
    # データセット別統計
    dataset_stats = defaultdict(lambda: {
        'count': 0,
        'bert_scores': [],
        'bleu_scores': [],
        'llm_scores': []
    })
    
    # アスペクト別統計
    aspect_stats = defaultdict(lambda: {
        'count': 0,
        'bert_scores': [],
        'bleu_scores': [],
        'llm_scores': []
    })
    
    # 実験詳細
    experiment_details = []
    
    for exp_result in experiments:
        exp_info = exp_result.get('experiment_info', {})
        dataset = exp_info.get('dataset')
        aspect = exp_info.get('aspect')
        
        # スコア取得
        bert_score = exp_result.get('bert_score', 0)
        bleu_score = exp_result.get('bleu_score', 0)
        llm_score = exp_result.get('llm_score', 0)
        
        # データセット別統計
        if dataset:
            dataset_stats[dataset]['count'] += 1
            if bert_score:
                dataset_stats[dataset]['bert_scores'].append(bert_score)
            if bleu_score:
                dataset_stats[dataset]['bleu_scores'].append(bleu_score)
            if llm_score:
                dataset_stats[dataset]['llm_scores'].append(llm_score)
        
        # アスペクト別統計
        if aspect:
            key = f"{dataset}_{aspect}"
            aspect_stats[key]['count'] += 1
            if bert_score:
                aspect_stats[key]['bert_scores'].append(bert_score)
            if bleu_score:
                aspect_stats[key]['bleu_scores'].append(bleu_score)
            if llm_score:
                aspect_stats[key]['llm_scores'].append(llm_score)
        
        # 実験詳細
        experiment_details.append({
            'experiment_id': exp_info.get('experiment_id', ''),
            'dataset': dataset,
            'aspect': aspect,
            'bert_score': bert_score,
            'bleu_score': bleu_score,
            'llm_score': llm_score
        })
    
    # 平均値計算
    for stats in dataset_stats.values():
        stats['avg_bert'] = sum(stats['bert_scores']) / len(stats['bert_scores']) if stats['bert_scores'] else 0
        stats['avg_bleu'] = sum(stats['bleu_scores']) / len(stats['bleu_scores']) if stats['bleu_scores'] else 0
        stats['avg_llm'] = sum(stats['llm_scores']) / len(stats['llm_scores']) if stats['llm_scores'] else 0
    
    for stats in aspect_stats.values():
        stats['avg_bert'] = sum(stats['bert_scores']) / len(stats['bert_scores']) if stats['bert_scores'] else 0
        stats['avg_bleu'] = sum(stats['bleu_scores']) / len(stats['bleu_scores']) if stats['bleu_scores'] else 0
        stats['avg_llm'] = sum(stats['llm_scores']) / len(stats['llm_scores']) if stats['llm_scores'] else 0
    
    return {
        'dataset_stats': dict(dataset_stats),
        'aspect_stats': dict(aspect_stats),
        'experiment_details': experiment_details,
        'total_experiments': len(experiments)
    }

def generate_markdown_report(analysis: Dict[str, Any], output_path: str):
    """Markdownレポートを生成"""
    
    lines = []
    lines.append("# 3-shot実験結果レポート")
    lines.append("")
    lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append(f"## 実験概要")
    lines.append("")
    lines.append(f"- **総実験数**: {analysis['total_experiments']}実験")
    lines.append(f"- **Few-shot設定**: 3-shot")
    lines.append("")
    
    # データセット別統計
    lines.append("## データセット別統計")
    lines.append("")
    lines.append("| データセット | 実験数 | 平均BERTスコア | 平均BLEUスコア | 平均LLMスコア |")
    lines.append("|------------|--------|---------------|---------------|---------------|")
    
    for dataset, stats in sorted(analysis['dataset_stats'].items()):
        lines.append(
            f"| {dataset} | {stats['count']} | "
            f"{stats['avg_bert']:.4f} | {stats['avg_bleu']:.4f} | {stats['avg_llm']:.4f} |"
        )
    
    lines.append("")
    
    # アスペクト別統計（上位10件）
    lines.append("## アスペクト別統計（上位10件）")
    lines.append("")
    lines.append("| データセット_アスペクト | 実験数 | 平均BERTスコア | 平均BLEUスコア | 平均LLMスコア |")
    lines.append("|----------------------|--------|---------------|---------------|---------------|")
    
    sorted_aspects = sorted(
        analysis['aspect_stats'].items(),
        key=lambda x: x[1]['avg_bert'],
        reverse=True
    )[:10]
    
    for aspect_key, stats in sorted_aspects:
        lines.append(
            f"| {aspect_key} | {stats['count']} | "
            f"{stats['avg_bert']:.4f} | {stats['avg_bleu']:.4f} | {stats['avg_llm']:.4f} |"
        )
    
    lines.append("")
    
    # 実験詳細（サンプル）
    lines.append("## 実験詳細（サンプル: 上位5件）")
    lines.append("")
    lines.append("| 実験ID | データセット | アスペクト | BERTスコア | BLEUスコア | LLMスコア |")
    lines.append("|--------|------------|----------|-----------|-----------|-----------|")
    
    sorted_experiments = sorted(
        analysis['experiment_details'],
        key=lambda x: x['bert_score'],
        reverse=True
    )[:5]
    
    for exp in sorted_experiments:
        lines.append(
            f"| {exp['experiment_id']} | {exp['dataset']} | {exp['aspect']} | "
            f"{exp['bert_score']:.4f} | {exp['bleu_score']:.4f} | {exp['llm_score']:.4f} |"
        )
    
    lines.append("")
    
    # ファイルに保存
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"Markdownレポートを生成しました: {output_path}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="3-shot実験結果を分析")
    parser.add_argument('--results-dir', type=str, required=True, help='結果ディレクトリ')
    parser.add_argument('--output', type=str, default=None, help='出力ファイルパス')
    
    args = parser.parse_args()
    
    # 結果を読み込み
    results = load_results(args.results_dir)
    
    # 分析
    analysis = analyze_results(results)
    
    # 出力パス決定
    if args.output is None:
        output_path = Path(args.results_dir) / "3shot_results_report.md"
    else:
        output_path = Path(args.output)
    
    # Markdownレポート生成
    generate_markdown_report(analysis, str(output_path))

if __name__ == "__main__":
    main()












