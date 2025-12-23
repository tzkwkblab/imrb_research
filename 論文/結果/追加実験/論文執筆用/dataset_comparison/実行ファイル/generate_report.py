#!/usr/bin/env python3
"""
データセット別性能比較実験結果の統計レポート生成スクリプト
"""

import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
from datetime import datetime


def load_statistics(statistics_path: Path) -> Dict[str, Any]:
    """統計情報を読み込み"""
    with open(statistics_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('statistics', {})


def generate_report(stats: Dict[str, Any], output_path: Path) -> None:
    """レポートを生成"""
    lines = []
    
    lines.append("# データセット別性能比較実験結果レポート")
    lines.append("")
    lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    lines.append("## 実行統計")
    lines.append("")
    lines.append(f"- 総実験数: {stats['total_experiments']}")
    lines.append(f"- 成功: {stats['successful']}")
    lines.append(f"- 失敗: {stats['failed']}")
    lines.append("")
    
    lines.append("## データセット別統計")
    lines.append("")
    lines.append("| データセット | 実験数 | アスペクト数 | 平均BERT | 最小BERT | 最大BERT | 平均BLEU | 平均LLM | 最小LLM | 最大LLM |")
    lines.append("|-------------|--------|-------------|----------|----------|----------|----------|---------|---------|---------|")
    
    for dataset in sorted(stats['dataset_stats'].keys()):
        s = stats['dataset_stats'][dataset]
        count = s['count']
        aspect_count = len(s['aspects'])
        avg_bert = f"{s.get('avg_bert_score', 0):.4f}" if s.get('avg_bert_score') is not None else "N/A"
        min_bert = f"{s.get('min_bert_score', 0):.4f}" if s.get('min_bert_score') is not None else "N/A"
        max_bert = f"{s.get('max_bert_score', 0):.4f}" if s.get('max_bert_score') is not None else "N/A"
        avg_bleu = f"{s.get('avg_bleu_score', 0):.4f}" if s.get('avg_bleu_score') is not None else "N/A"
        avg_llm = f"{s.get('avg_llm_score', 0):.4f}" if s.get('avg_llm_score') is not None else "N/A"
        min_llm = f"{s.get('min_llm_score', 0):.4f}" if s.get('min_llm_score') is not None else "N/A"
        max_llm = f"{s.get('max_llm_score', 0):.4f}" if s.get('max_llm_score') is not None else "N/A"
        
        lines.append(f"| {dataset} | {count} | {aspect_count} | {avg_bert} | {min_bert} | {max_bert} | {avg_bleu} | {avg_llm} | {min_llm} | {max_llm} |")
    
    lines.append("")
    
    lines.append("## アスペクト別統計（上位10件）")
    lines.append("")
    lines.append("| データセット | アスペクト | BERT | BLEU | LLM |")
    lines.append("|-------------|----------|------|------|-----|")
    
    aspect_list = []
    for aspect_key, s in stats['aspect_stats'].items():
        dataset = s.get('dataset', 'unknown')
        aspect = aspect_key.replace(f"{dataset}_", "")
        bert = s.get('avg_bert_score', 0) if s.get('avg_bert_score') is not None else 0
        bleu = s.get('avg_bleu_score', 0) if s.get('avg_bleu_score') is not None else 0
        llm = s.get('avg_llm_score', 0) if s.get('avg_llm_score') is not None else 0
        aspect_list.append((dataset, aspect, bert, bleu, llm))
    
    aspect_list.sort(key=lambda x: x[2], reverse=True)
    
    for dataset, aspect, bert, bleu, llm in aspect_list[:10]:
        lines.append(f"| {dataset} | {aspect} | {bert:.4f} | {bleu:.4f} | {llm:.4f} |")
    
    lines.append("")
    
    lines.append("## 主要な発見")
    lines.append("")
    
    dataset_stats = stats['dataset_stats']
    
    lines.append("### データセット別の平均スコア")
    lines.append("")
    for dataset in sorted(dataset_stats.keys()):
        s = dataset_stats[dataset]
        avg_bert = s.get('avg_bert_score', 0)
        avg_llm = s.get('avg_llm_score', 0)
        lines.append(f"- **{dataset}**: BERT={avg_bert:.4f}, LLM={avg_llm:.4f}")
    lines.append("")
    
    lines.append("### データセット別の最高BERTスコア")
    lines.append("")
    for dataset in sorted(dataset_stats.keys()):
        s = dataset_stats[dataset]
        max_bert = s.get('max_bert_score', 0)
        lines.append(f"- **{dataset}**: {max_bert:.4f}")
    lines.append("")
    
    lines.append("### データセット別の最高LLMスコア")
    lines.append("")
    for dataset in sorted(dataset_stats.keys()):
        s = dataset_stats[dataset]
        max_llm = s.get('max_llm_score', 0)
        lines.append(f"- **{dataset}**: {max_llm:.4f}")
    lines.append("")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    logging.info(f"レポートを保存: {output_path}")


def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(
        description="データセット別性能比較実験結果の統計レポートを生成",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--statistics', '-s',
        type=str,
        default=None,
        help='統計情報JSONファイルのパス'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='出力MDファイルのパス'
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
        experiment_dir = script_dir.parent
        
        statistics_path = Path(args.statistics) if args.statistics else experiment_dir / "dataset_comparison_statistics.json"
        output_path = Path(args.output) if args.output else experiment_dir / "分析レポート" / "dataset_comparison_results_report.md"
        
        if not statistics_path.exists():
            logger.error(f"統計情報ファイルが見つかりません: {statistics_path}")
            return 1
        
        logger.info(f"統計情報を読み込み: {statistics_path}")
        stats = load_statistics(statistics_path)
        
        logger.info("レポートを生成中...")
        generate_report(stats, output_path)
        
        logger.info("=" * 60)
        logger.info("レポート生成完了")
        logger.info(f"レポート: {output_path}")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())


















