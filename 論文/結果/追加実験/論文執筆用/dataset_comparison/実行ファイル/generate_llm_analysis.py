#!/usr/bin/env python3
"""
データセット別性能比較実験結果のLLM分析スクリプト
"""

import json
import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent.parent.parent.parent.parent.parent
utils_path = project_root / "src" / "analysis" / "experiments" / "utils"
if not utils_path.exists():
    project_root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent.parent.parent
    utils_path = project_root / "src" / "analysis" / "experiments" / "utils"
sys.path.insert(0, str(utils_path))

from LLM.llm_factory import LLMFactory

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_research_context(context_path: Path) -> str:
    """研究コンテキストを読み込み"""
    if not context_path.exists():
        logger.warning(f"研究背景ファイルが見つかりません: {context_path}")
        return ""
    
    with open(context_path, 'r', encoding='utf-8') as f:
        return f.read()


def load_statistics(statistics_path: Path) -> Dict[str, Any]:
    """統計情報を読み込み"""
    if not statistics_path.exists():
        raise FileNotFoundError(f"統計情報ファイルが見つかりません: {statistics_path}")
    
    with open(statistics_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('statistics', {})


def load_batch_results(batch_results_path: Path) -> List[Dict[str, Any]]:
    """バッチ結果を読み込み"""
    if not batch_results_path.exists():
        raise FileNotFoundError(f"バッチ結果ファイルが見つかりません: {batch_results_path}")
    
    with open(batch_results_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('results', [])


def format_statistics_for_prompt(statistics: Dict[str, Any]) -> str:
    """統計情報をプロンプト用にフォーマット"""
    lines = []
    
    lines.append("## 実験設定")
    lines.append("- データセット: Steam (4アスペクト), SemEval (4アスペクト), GoEmotions (28アスペクト)")
    lines.append("- Few-shot設定: 0-shot（固定）")
    lines.append("- 評価指標: BERTスコア、BLEUスコア、LLMスコア（gpt-4o-miniによる意味的類似度評価）")
    lines.append("- LLM評価: 有効")
    lines.append("- 総実験数: 36実験")
    lines.append("")
    
    lines.append("## データセット別の平均スコア")
    for dataset in sorted(statistics.get('dataset_stats', {}).keys()):
        stats = statistics['dataset_stats'][dataset]
        avg_bert = stats.get('avg_bert_score', 0)
        avg_llm = stats.get('avg_llm_score', 0)
        count = stats.get('count', 0)
        lines.append(f"- {dataset}: BERT={avg_bert:.4f}, LLM={avg_llm:.4f} (実験数: {count})")
    lines.append("")
    
    lines.append("## データセット別の最高BERTスコア")
    for dataset in sorted(statistics.get('dataset_stats', {}).keys()):
        stats = statistics['dataset_stats'][dataset]
        max_bert = stats.get('max_bert_score', 0)
        lines.append(f"- {dataset}: {max_bert:.4f}")
    lines.append("")
    
    lines.append("## データセット別の最高LLMスコア")
    for dataset in sorted(statistics.get('dataset_stats', {}).keys()):
        stats = statistics['dataset_stats'][dataset]
        max_llm = stats.get('max_llm_score', 0)
        lines.append(f"- {dataset}: {max_llm:.4f}")
    lines.append("")
    
    lines.append("## アスペクト別の統計（上位10件）")
    aspect_list = []
    for aspect_key, stats in statistics.get('aspect_stats', {}).items():
        dataset = stats.get('dataset', 'unknown')
        aspect = aspect_key.replace(f"{dataset}_", "")
        bert = stats.get('avg_bert_score', 0) if stats.get('avg_bert_score') is not None else 0
        llm = stats.get('avg_llm_score', 0) if stats.get('avg_llm_score') is not None else 0
        aspect_list.append((dataset, aspect, bert, llm))
    
    aspect_list.sort(key=lambda x: x[2], reverse=True)
    
    for dataset, aspect, bert, llm in aspect_list[:10]:
        lines.append(f"- {dataset}_{aspect}: BERT={bert:.4f}, LLM={llm:.4f}")
    lines.append("")
    
    return "\n".join(lines)


def generate_analysis_prompt(
    research_context: str,
    statistics: Dict[str, Any],
    results: List[Dict[str, Any]]
) -> str:
    """分析プロンプトを生成"""
    stats_text = format_statistics_for_prompt(statistics)
    
    prompt = f"""あなたは説明可能AIの研究における実験結果の分析専門家です。以下の研究背景と実験結果を詳細に考察してください。

# 研究背景

{research_context}

# 実験結果

{stats_text}

# 考察指示

この実験結果から言えることを1000文字程度で考察してください。以下の観点を含めてください：

1. **データセット間の性能差の要因**
   - Steam、SemEval、GoEmotionsの3つのデータセット間でBERTスコアとLLMスコアがどのように異なるか
   - データセットの特性（ドメイン、アスペクト数、データの性質）が性能に与える影響
   - 各データセットでの対比因子抽出の難易度

2. **LLM評価指標の妥当性**
   - LLMスコアがBERTスコアとどの程度一致しているか
   - データセット間でLLM評価の傾向が異なる理由
   - 自動評価指標としてのLLM評価の有用性

3. **アスペクトによる性能差の要因**
   - アスペクトによって性能が異なる理由
   - データセット内でのアスペクト間の性能差
   - 対比因子抽出の難易度がアスペクトによって異なる理由

4. **本研究における対比因子抽出への示唆**
   - この実験結果が、LLMによる対比因子ラベル自動生成の実現可能性に与える示唆
   - データセット特性を考慮した対比因子抽出の重要性
   - 0-shot設定での性能限界と改善の余地

考察は日本語で、具体的かつ詳細に記述してください。統計データを引用しながら、定量的な根拠に基づいた分析を行ってください。
"""
    
    return prompt


def analyze_with_llm(prompt: str, model_name: str = "gpt-5.1") -> Optional[str]:
    """LLMに問い合わせて考察を取得"""
    logger.info(f"LLMクライアントを作成: {model_name}")
    client = LLMFactory.create_client(model_name=model_name, debug=False)
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"LLM問い合わせ中（試行 {attempt+1}/{max_retries}）...")
            response = client.ask(
                prompt,
                max_tokens=2000,
                temperature=0.7
            )
            
            if response and response.strip():
                logger.info("LLM応答を取得しました")
                return response.strip()
            else:
                logger.warning(f"LLM応答が空です（試行 {attempt+1}/{max_retries}）")
                
        except Exception as e:
            logger.warning(f"LLM問い合わせエラー（試行 {attempt+1}/{max_retries}）: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"{wait_time}秒待機してからリトライ...")
                time.sleep(wait_time)
    
    logger.error("LLM問い合わせに失敗しました")
    return None


def generate_analysis_report(
    research_context: str,
    statistics: Dict[str, Any],
    results: List[Dict[str, Any]],
    analysis: str,
    output_path: Path
) -> None:
    """分析レポートを生成"""
    lines = []
    
    lines.append("# データセット別性能比較実験結果のLLM分析")
    lines.append("")
    lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    lines.append("## 実験概要")
    lines.append("")
    lines.append("- **データセット**: Steam (4アスペクト), SemEval (4アスペクト), GoEmotions (28アスペクト)")
    lines.append("- **Few-shot設定**: 0-shot（固定）")
    lines.append("- **総実験数**: 36実験")
    lines.append(f"- **成功**: {statistics.get('successful', 0)}実験")
    lines.append(f"- **失敗**: {statistics.get('failed', 0)}実験")
    lines.append("- **LLM評価**: 有効（gpt-4o-mini）")
    lines.append("")
    
    lines.append("## 主要結果")
    lines.append("")
    lines.append("### データセット別の平均スコア")
    for dataset in sorted(statistics.get('dataset_stats', {}).keys()):
        stats = statistics['dataset_stats'][dataset]
        avg_bert = stats.get('avg_bert_score', 0)
        avg_llm = stats.get('avg_llm_score', 0)
        lines.append(f"- **{dataset}**: BERT={avg_bert:.4f}, LLM={avg_llm:.4f}")
    lines.append("")
    
    lines.append("### データセット別の最高BERTスコア")
    for dataset in sorted(statistics.get('dataset_stats', {}).keys()):
        stats = statistics['dataset_stats'][dataset]
        max_bert = stats.get('max_bert_score', 0)
        lines.append(f"- **{dataset}**: {max_bert:.4f}")
    lines.append("")
    
    lines.append("## LLMによる考察")
    lines.append("")
    lines.append(analysis)
    lines.append("")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    logger.info(f"分析レポートを保存: {output_path}")


def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(
        description="データセット別性能比較実験結果をLLMで分析",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--statistics', '-s',
        type=str,
        default=None,
        help='統計情報JSONファイルのパス'
    )
    
    parser.add_argument(
        '--batch-results', '-b',
        type=str,
        default=None,
        help='バッチ結果JSONファイルのパス'
    )
    
    parser.add_argument(
        '--research-context', '-r',
        type=str,
        default=None,
        help='研究コンテキストMDファイルのパス'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='出力MDファイルのパス'
    )
    
    parser.add_argument(
        '--model', '-m',
        type=str,
        default='gpt-5.1',
        help='使用するLLMモデル (default: gpt-5.1)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='デバッグモード'
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        script_dir = Path(__file__).parent
        experiment_dir = script_dir.parent
        
        statistics_path = Path(args.statistics) if args.statistics else experiment_dir / "dataset_comparison_statistics.json"
        batch_results_path = Path(args.batch_results) if args.batch_results else Path("results/20251127_120938/batch_results.json")
        research_context_path = Path(args.research_context) if args.research_context else experiment_dir / "research_context.md"
        output_path = Path(args.output) if args.output else experiment_dir / "分析レポート" / "dataset_comparison_analysis.md"
        
        if not statistics_path.exists():
            logger.error(f"統計情報ファイルが見つかりません: {statistics_path}")
            return 1
        
        if not batch_results_path.exists():
            logger.error(f"バッチ結果ファイルが見つかりません: {batch_results_path}")
            return 1
        
        if not research_context_path.exists():
            logger.error(f"研究コンテキストファイルが見つかりません: {research_context_path}")
            return 1
        
        logger.info("データを読み込み中...")
        research_context = load_research_context(research_context_path)
        if not research_context:
            logger.error("研究コンテキストが空です")
            return 1
        
        statistics = load_statistics(statistics_path)
        results = load_batch_results(batch_results_path)
        
        logger.info(f"統計情報を読み込み: {len(statistics)}項目")
        logger.info(f"実験結果を読み込み: {len(results)}件")
        
        logger.info("分析プロンプトを生成中...")
        prompt = generate_analysis_prompt(research_context, statistics, results)
        
        if args.debug:
            logger.debug(f"プロンプト長: {len(prompt)}文字")
            logger.debug("プロンプトの最初の500文字:")
            logger.debug(prompt[:500])
        
        logger.info(f"LLM（{args.model}）に問い合わせ中...")
        analysis = analyze_with_llm(prompt, model_name=args.model)
        
        if not analysis:
            logger.error("LLM分析の取得に失敗しました")
            return 1
        
        logger.info("分析レポートを生成中...")
        generate_analysis_report(
            research_context,
            statistics,
            results,
            analysis,
            output_path
        )
        
        logger.info("=" * 60)
        logger.info("分析完了")
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

