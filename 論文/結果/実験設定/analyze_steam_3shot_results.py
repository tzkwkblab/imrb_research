#!/usr/bin/env python3
"""
Steam 3-shot実験結果分析スクリプト

Steamデータセットの0-shot, 1-shot, 3-shot実験結果を分析し、Markdownファイルにまとめる。
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
    
    # Few-shot別統計
    fewshot_stats = defaultdict(lambda: {
        'count': 0,
        'bert_scores': [],
        'bleu_scores': [],
        'experiments': []
    })
    
    # アスペクト別統計
    aspect_stats = defaultdict(lambda: {
        '0-shot': {'bert': [], 'bleu': []},
        '1-shot': {'bert': [], 'bleu': []},
        '3-shot': {'bert': [], 'bleu': []}
    })
    
    for exp_result in experiments:
        exp_info = exp_result.get('experiment_info', {})
        few_shot = exp_info.get('few_shot', 0)
        aspect = exp_info.get('aspect', '')
        
        bert_score = exp_result.get('bert_score', 0)
        bleu_score = exp_result.get('bleu_score', 0)
        
        # Few-shot別統計
        fewshot_key = f"{few_shot}-shot"
        fewshot_stats[fewshot_key]['count'] += 1
        if bert_score:
            fewshot_stats[fewshot_key]['bert_scores'].append(bert_score)
        if bleu_score:
            fewshot_stats[fewshot_key]['bleu_scores'].append(bleu_score)
        fewshot_stats[fewshot_key]['experiments'].append({
            'experiment_id': exp_info.get('experiment_id', ''),
            'aspect': aspect,
            'bert_score': bert_score,
            'bleu_score': bleu_score
        })
        
        # アスペクト別統計
        if aspect:
            aspect_stats[aspect][f'{few_shot}-shot']['bert'].append(bert_score)
            aspect_stats[aspect][f'{few_shot}-shot']['bleu'].append(bleu_score)
    
    # 平均値計算
    for stats in fewshot_stats.values():
        stats['avg_bert'] = sum(stats['bert_scores']) / len(stats['bert_scores']) if stats['bert_scores'] else 0
        stats['avg_bleu'] = sum(stats['bleu_scores']) / len(stats['bleu_scores']) if stats['bleu_scores'] else 0
    
    for aspect_data in aspect_stats.values():
        for shot_data in aspect_data.values():
            shot_data['avg_bert'] = sum(shot_data['bert']) / len(shot_data['bert']) if shot_data['bert'] else 0
            shot_data['avg_bleu'] = sum(shot_data['bleu']) / len(shot_data['bleu']) if shot_data['bleu'] else 0
    
    return {
        'fewshot_stats': dict(fewshot_stats),
        'aspect_stats': dict(aspect_stats),
        'total_experiments': len(experiments)
    }

def generate_markdown_report(analysis: Dict[str, Any], output_path: str):
    """Markdownレポートを生成"""
    
    lines = []
    lines.append("# Steam 3-shot実験結果レポート")
    lines.append("")
    lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append(f"## 実験概要")
    lines.append("")
    lines.append(f"- **総実験数**: {analysis['total_experiments']}実験")
    lines.append(f"- **データセット**: Steam")
    lines.append(f"- **Few-shot設定**: 0-shot, 1-shot, 3-shot")
    lines.append(f"- **group_size**: 100")
    lines.append(f"- **LLM評価**: 無効")
    lines.append("")
    
    # Few-shot別統計
    lines.append("## Few-shot別統計")
    lines.append("")
    lines.append("| Few-shot | 実験数 | 平均BERTスコア | 平均BLEUスコア |")
    lines.append("|----------|--------|---------------|---------------|")
    
    for fewshot_key in ['0-shot', '1-shot', '3-shot']:
        if fewshot_key in analysis['fewshot_stats']:
            stats = analysis['fewshot_stats'][fewshot_key]
            lines.append(
                f"| {fewshot_key} | {stats['count']} | "
                f"{stats['avg_bert']:.4f} | {stats['avg_bleu']:.4f} |"
            )
    
    lines.append("")
    
    # アスペクト別統計
    lines.append("## アスペクト別統計")
    lines.append("")
    lines.append("| アスペクト | 0-shot BERT | 0-shot BLEU | 1-shot BERT | 1-shot BLEU | 3-shot BERT | 3-shot BLEU |")
    lines.append("|----------|------------|------------|------------|------------|------------|------------|")
    
    for aspect in sorted(analysis['aspect_stats'].keys()):
        stats = analysis['aspect_stats'][aspect]
        lines.append(
            f"| {aspect} | "
            f"{stats['0-shot']['avg_bert']:.4f} | {stats['0-shot']['avg_bleu']:.4f} | "
            f"{stats['1-shot']['avg_bert']:.4f} | {stats['1-shot']['avg_bleu']:.4f} | "
            f"{stats['3-shot']['avg_bert']:.4f} | {stats['3-shot']['avg_bleu']:.4f} |"
        )
    
    lines.append("")
    
    # 実験詳細
    lines.append("## 実験詳細")
    lines.append("")
    lines.append("| 実験ID | アスペクト | Few-shot | BERTスコア | BLEUスコア |")
    lines.append("|--------|----------|----------|-----------|-----------|")
    
    for fewshot_key in ['0-shot', '1-shot', '3-shot']:
        if fewshot_key in analysis['fewshot_stats']:
            for exp in analysis['fewshot_stats'][fewshot_key]['experiments']:
                lines.append(
                    f"| {exp['experiment_id']} | {exp['aspect']} | {fewshot_key} | "
                    f"{exp['bert_score']:.4f} | {exp['bleu_score']:.4f} |"
                )
    
    lines.append("")
    
    # ファイルに保存
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"Markdownレポートを生成しました: {output_path}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Steam 3-shot実験結果を分析")
    parser.add_argument('--results-dir', type=str, required=True, help='結果ディレクトリ')
    parser.add_argument('--output', type=str, default=None, help='出力ファイルパス')
    
    args = parser.parse_args()
    
    # 結果を読み込み
    results = load_results(args.results_dir)
    
    # 分析
    analysis = analyze_results(results)
    
    # 出力パス決定
    if args.output is None:
        output_path = Path(args.results_dir) / "steam_3shot_results_report.md"
    else:
        output_path = Path(args.output)
    
    # Markdownレポート生成
    generate_markdown_report(analysis, str(output_path))

if __name__ == "__main__":
    main()


