#!/usr/bin/env python3
"""
モデル比較実験（temperature=0版）結果の統計レポート生成スクリプト
"""

import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


def load_statistics(statistics_path: Path) -> Dict[str, Any]:
    """統計情報を読み込み"""
    with open(statistics_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('statistics', {})


def generate_report(stats: Dict[str, Any], output_path: Path) -> None:
    """レポートを生成"""
    lines = []
    
    lines.append("# Steamモデル比較実験結果レポート（temperature=0版）")
    lines.append("")
    lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    lines.append("## 実行統計")
    lines.append("")
    lines.append(f"- 総実験数: {stats['total_experiments']}")
    lines.append(f"- 成功: {stats['successful']}")
    lines.append(f"- 失敗: {stats['failed']}")
    lines.append("")
    
    lines.append("## モデル別統計")
    lines.append("")
    lines.append("| モデル | 実験数 | 平均BERT | 最小BERT | 最大BERT | 平均BLEU | 平均LLM | 最小LLM | 最大LLM |")
    lines.append("|--------|--------|----------|----------|----------|----------|---------|---------|---------|")
    
    for model in sorted(stats['model_stats'].keys()):
        s = stats['model_stats'][model]
        count = s['count']
        avg_bert = f"{s.get('avg_bert_score', 0):.4f}" if s.get('avg_bert_score') is not None else "N/A"
        min_bert = f"{s.get('min_bert_score', 0):.4f}" if s.get('min_bert_score') is not None else "N/A"
        max_bert = f"{s.get('max_bert_score', 0):.4f}" if s.get('max_bert_score') is not None else "N/A"
        avg_bleu = f"{s.get('avg_bleu_score', 0):.4f}" if s.get('avg_bleu_score') is not None else "N/A"
        avg_llm = f"{s.get('avg_llm_score', 0):.4f}" if s.get('avg_llm_score') is not None else "N/A"
        min_llm = f"{s.get('min_llm_score', 0):.4f}" if s.get('min_llm_score') is not None else "N/A"
        max_llm = f"{s.get('max_llm_score', 0):.4f}" if s.get('max_llm_score') is not None else "N/A"
        
        lines.append(f"| {model} | {count} | {avg_bert} | {min_bert} | {max_bert} | {avg_bleu} | {avg_llm} | {min_llm} | {max_llm} |")
    
    lines.append("")
    
    lines.append("## アスペクト別統計")
    lines.append("")
    lines.append("| アスペクト | 実験数 | 平均BERT | 最小BERT | 最大BERT | 平均BLEU | 平均LLM | 最小LLM | 最大LLM |")
    lines.append("|----------|--------|----------|----------|----------|----------|---------|---------|---------|")
    
    for aspect in sorted(stats['aspect_stats'].keys()):
        s = stats['aspect_stats'][aspect]
        count = s['count']
        avg_bert = f"{s.get('avg_bert_score', 0):.4f}" if s.get('avg_bert_score') else "N/A"
        min_bert = f"{s.get('min_bert_score', 0):.4f}" if s.get('min_bert_score') else "N/A"
        max_bert = f"{s.get('max_bert_score', 0):.4f}" if s.get('max_bert_score') else "N/A"
        avg_bleu = f"{s.get('avg_bleu_score', 0):.4f}" if s.get('avg_bleu_score') else "N/A"
        avg_llm = f"{s.get('avg_llm_score', 0):.4f}" if s.get('avg_llm_score') else "N/A"
        min_llm = f"{s.get('min_llm_score', 0):.4f}" if s.get('min_llm_score') else "N/A"
        max_llm = f"{s.get('max_llm_score', 0):.4f}" if s.get('max_llm_score') else "N/A"
        
        lines.append(f"| {aspect} | {count} | {avg_bert} | {min_bert} | {max_bert} | {avg_bleu} | {avg_llm} | {min_llm} | {max_llm} |")
    
    lines.append("")
    
    lines.append("## アスペクト別モデル比較")
    lines.append("")
    lines.append("| アスペクト | gpt-4o-mini (BERT) | gpt-5.1 (BERT) | 差 | gpt-4o-mini (LLM) | gpt-5.1 (LLM) | 差 |")
    lines.append("|----------|-------------------|---------------|-----|------------------|--------------|-----|")
    
    for aspect in sorted(stats['aspect_stats'].keys()):
        mini_key = f"{aspect}_gpt-4o-mini"
        gpt51_key = f"{aspect}_gpt-5.1"
        
        mini_bert = stats['aspect_model_stats'].get(mini_key, {}).get('avg_bert_score', 0)
        gpt51_bert = stats['aspect_model_stats'].get(gpt51_key, {}).get('avg_bert_score', 0)
        bert_diff = mini_bert - gpt51_bert
        
        mini_llm = stats['aspect_model_stats'].get(mini_key, {}).get('avg_llm_score', 0)
        gpt51_llm = stats['aspect_model_stats'].get(gpt51_key, {}).get('avg_llm_score', 0)
        llm_diff = mini_llm - gpt51_llm
        
        lines.append(f"| {aspect} | {mini_bert:.4f} | {gpt51_bert:.4f} | {bert_diff:+.4f} | {mini_llm:.4f} | {gpt51_llm:.4f} | {llm_diff:+.4f} |")
    
    lines.append("")
    
    lines.append("## 主要な発見")
    lines.append("")
    
    mini_stats = stats['model_stats'].get('gpt-4o-mini', {})
    gpt51_stats = stats['model_stats'].get('gpt-5.1', {})
    
    mini_bert = mini_stats.get('avg_bert_score', 0)
    gpt51_bert = gpt51_stats.get('avg_bert_score', 0)
    mini_llm = mini_stats.get('avg_llm_score', 0)
    gpt51_llm = gpt51_stats.get('avg_llm_score', 0)
    
    lines.append("### モデル別の平均スコア")
    lines.append("")
    lines.append(f"- **gpt-4o-mini**: BERT={mini_bert:.4f}, LLM={mini_llm:.4f}")
    lines.append(f"- **gpt-5.1**: BERT={gpt51_bert:.4f}, LLM={gpt51_llm:.4f}")
    lines.append(f"- **差**: BERT={mini_bert-gpt51_bert:+.4f}, LLM={mini_llm-gpt51_llm:+.4f}")
    lines.append("")
    
    lines.append("### アスペクト別の最高BERTスコア")
    lines.append("")
    for aspect in sorted(stats['aspect_stats'].keys()):
        max_bert = stats['aspect_stats'][aspect].get('max_bert_score', 0)
        avg_llm = stats['aspect_stats'][aspect].get('avg_llm_score', 0)
        lines.append(f"- **{aspect}**: BERT={max_bert:.4f}, LLM={avg_llm:.4f}")
    lines.append("")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    logging.info(f"レポートを保存: {output_path}")


def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(
        description="モデル比較実験（temperature=0版）結果の統計レポートを生成",
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
        
        statistics_path = Path(args.statistics) if args.statistics else experiment_dir / "実験設定" / "model_comparison_temperature0_statistics.json"
        output_path = Path(args.output) if args.output else experiment_dir / "分析レポート" / "model_comparison_temperature0_results_report.md"
        
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


















