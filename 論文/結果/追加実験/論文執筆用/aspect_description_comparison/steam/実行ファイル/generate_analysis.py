#!/usr/bin/env python3
"""
アスペクト説明文比較実験結果のLLM分析スクリプト

実験結果をgpt-5.1に問い合わせて考察を取得する。
"""

import json
import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# プロジェクトルートをパスに追加
script_dir = Path(__file__).parent
# aspect_description_comparison/steam/実行ファイル から プロジェクトルートまで
project_root = script_dir.parent.parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src" / "analysis" / "experiments" / "utils"))

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
    lines.append("- データセット: Steam")
    lines.append("- アスペクト: gameplay, visual, story, audio（4アスペクト）")
    lines.append("- GPTモデル: gpt-4o")
    lines.append("- group_size: 100")
    lines.append("- temperature: 0.0")
    lines.append("- Few-shot: 0-shot（固定）")
    lines.append("- 評価指標: BERTスコア、BLEUスコア、LLMスコア")
    lines.append("")
    
    lines.append("## 説明文あり/なし別の平均スコア")
    for desc_key in ['no_desc', 'with_desc']:
        stats = statistics.get('description_stats', {}).get(desc_key, {})
        avg_bert = stats.get('avg_bert_score', 0)
        avg_llm = stats.get('avg_llm_score', 0)
        desc_label = "説明文あり" if desc_key == 'with_desc' else "説明文なし"
        lines.append(f"- **{desc_label}**: BERT平均={avg_bert:.4f}, LLM平均={avg_llm:.4f}")
    lines.append("")
    
    lines.append("## アスペクト別の統計（説明文あり/なし対比）")
    aspects = ['gameplay', 'visual', 'story', 'audio']
    for aspect in aspects:
        no_desc_key = f"{aspect}_no_desc"
        with_desc_key = f"{aspect}_with_desc"
        no_desc_stats = statistics.get('aspect_description_stats', {}).get(no_desc_key, {})
        with_desc_stats = statistics.get('aspect_description_stats', {}).get(with_desc_key, {})
        no_desc_bert = no_desc_stats.get('avg_bert_score', 0)
        with_desc_bert = with_desc_stats.get('avg_bert_score', 0)
        diff = with_desc_bert - no_desc_bert
        lines.append(f"- **{aspect}**: 説明文なし={no_desc_bert:.4f}, 説明文あり={with_desc_bert:.4f}, 差分={diff:+.4f}")
    lines.append("")
    
    return "\n".join(lines)


def format_detailed_results_for_prompt(results: List[Dict[str, Any]]) -> str:
    """詳細結果をプロンプト用にフォーマット"""
    lines = []
    lines.append("## 詳細結果（アスペクト × 説明文あり/なし別）")
    lines.append("")
    
    # アスペクト × 説明文あり/なしでグループ化
    grouped = {}
    for result in results:
        exp_info = result.get('experiment_info', {})
        aspect = exp_info.get('aspect', 'unknown')
        use_desc = exp_info.get('use_aspect_descriptions', False)
        desc_key = 'with_desc' if use_desc else 'no_desc'
        
        key = f"{aspect}_{desc_key}"
        if key not in grouped:
            grouped[key] = {
                'aspect': aspect,
                'use_desc': use_desc,
                'bert_score': None,
                'bleu_score': None,
                'llm_score': None,
                'llm_response': ''
            }
        
        eval_data = result.get('evaluation', {})
        if 'bert_score' in eval_data and eval_data['bert_score'] is not None:
            if isinstance(eval_data['bert_score'], dict):
                grouped[key]['bert_score'] = eval_data['bert_score'].get('f1', 0)
            else:
                grouped[key]['bert_score'] = float(eval_data['bert_score'])
        
        if 'bleu_score' in eval_data and eval_data['bleu_score'] is not None:
            grouped[key]['bleu_score'] = float(eval_data['bleu_score'])
        
        if 'llm_score' in eval_data and eval_data['llm_score'] is not None:
            grouped[key]['llm_score'] = float(eval_data['llm_score'])
        
        process_data = result.get('process', {})
        if 'llm_response' in process_data:
            grouped[key]['llm_response'] = process_data['llm_response']
    
    # ソートして表示
    for key in sorted(grouped.keys()):
        data = grouped[key]
        desc_label = "説明文あり" if data['use_desc'] else "説明文なし"
        lines.append(f"### {data['aspect']} - {desc_label}")
        lines.append(f"- BERTスコア: {data['bert_score']:.4f}" if data['bert_score'] is not None else "- BERTスコア: N/A")
        lines.append(f"- BLEUスコア: {data['bleu_score']:.4f}" if data['bleu_score'] is not None else "- BLEUスコア: N/A")
        lines.append(f"- LLMスコア: {data['llm_score']:.4f}" if data['llm_score'] is not None else "- LLMスコア: N/A")
        if data['llm_response']:
            lines.append(f"- LLM出力: {data['llm_response'][:200]}...")
        lines.append("")
    
    return "\n".join(lines)


def generate_analysis_prompt(
    research_context: str,
    statistics: Dict[str, Any],
    results: List[Dict[str, Any]]
) -> str:
    """分析プロンプトを生成"""
    stats_text = format_statistics_for_prompt(statistics)
    results_text = format_detailed_results_for_prompt(results)
    
    prompt = f"""あなたは説明可能AIの研究における実験結果の分析専門家です。以下の研究背景と実験結果を詳細に考察してください。

# 研究背景

{research_context}

# 実験結果

{stats_text}

{results_text}

# 考察指示

この実験結果から言えることを1000文字程度で考察してください。以下の観点を含めてください：

1. **アスペクト説明文の効果**
   - 説明文ありとなしでBERTスコアやLLMスコアがどのように変化しているか
   - 説明文が対比因子抽出の性能に与える影響

2. **アスペクトによる説明文効果の違い**
   - 各アスペクト（gameplay, visual, story, audio）で説明文の効果が異なる理由
   - どのアスペクトで説明文が特に有効か、または無効か

3. **評価指標間の関係性**
   - BERTスコア、BLEUスコア、LLMスコアの関係性
   - 説明文の有無が各指標に与える影響の違い

4. **本研究における対比因子抽出への示唆**
   - この実験結果が、LLMによる対比因子ラベル自動生成の実現可能性に与える示唆
   - アスペクト説明文の活用方法と限界

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
    
    lines.append("# Steamアスペクト説明文比較実験結果のLLM分析")
    lines.append("")
    lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    lines.append("## 実験概要")
    lines.append("")
    lines.append("- **データセット**: Steam")
    lines.append("- **アスペクト**: gameplay, visual, story, audio（4アスペクト）")
    lines.append("- **GPTモデル**: gpt-4o")
    lines.append("- **group_size**: 100")
    lines.append("- **temperature**: 0.0")
    lines.append("- **Few-shot**: 0-shot（固定）")
    lines.append("- **総実験数**: 8実験（4アスペクト × 説明文あり/なし）")
    lines.append("")
    
    desc_stats = statistics.get('description_stats', {})
    no_desc_stats = desc_stats.get('no_desc', {})
    with_desc_stats = desc_stats.get('with_desc', {})
    
    lines.append("## 主要結果")
    lines.append("")
    lines.append("### 説明文あり/なし別の平均スコア")
    lines.append(f"- **説明文なし**: BERT平均={no_desc_stats.get('avg_bert_score', 0):.4f}, LLM平均={no_desc_stats.get('avg_llm_score', 0):.4f}")
    lines.append(f"- **説明文あり**: BERT平均={with_desc_stats.get('avg_bert_score', 0):.4f}, LLM平均={with_desc_stats.get('avg_llm_score', 0):.4f}")
    lines.append("")
    
    lines.append("### アスペクト別の対比（説明文あり - なし）")
    aspects = ['gameplay', 'visual', 'story', 'audio']
    for aspect in aspects:
        no_desc_key = f"{aspect}_no_desc"
        with_desc_key = f"{aspect}_with_desc"
        no_desc_stats = statistics.get('aspect_description_stats', {}).get(no_desc_key, {})
        with_desc_stats = statistics.get('aspect_description_stats', {}).get(with_desc_key, {})
        no_desc_bert = no_desc_stats.get('avg_bert_score', 0)
        with_desc_bert = with_desc_stats.get('avg_bert_score', 0)
        diff = with_desc_bert - no_desc_bert
        lines.append(f"- **{aspect}**: {diff:+.4f} (なし={no_desc_bert:.4f} → あり={with_desc_bert:.4f})")
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
        description="アスペクト説明文比較実験結果をLLMで分析",
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
        # パスを解決
        script_dir = Path(__file__).parent
        steam_dir = script_dir.parent
        
        statistics_path = Path(args.statistics) if args.statistics else steam_dir / "実験設定" / "aspect_description_comparison_statistics.json"
        batch_results_path = Path(args.batch_results) if args.batch_results else steam_dir / "実験結果" / "batch_results.json"
        research_context_path = Path(args.research_context) if args.research_context else steam_dir / "research_context.md"
        output_path = Path(args.output) if args.output else steam_dir / "分析レポート" / "aspect_description_comparison_analysis.md"
        
        # ファイル存在確認
        if not statistics_path.exists():
            logger.error(f"統計情報ファイルが見つかりません: {statistics_path}")
            return 1
        
        if not batch_results_path.exists():
            logger.error(f"バッチ結果ファイルが見つかりません: {batch_results_path}")
            return 1
        
        if not research_context_path.exists():
            logger.error(f"研究コンテキストファイルが見つかりません: {research_context_path}")
            logger.info("既存のresearch_context.mdをコピーしてください")
            return 1
        
        # データ読み込み
        logger.info("データを読み込み中...")
        research_context = load_research_context(research_context_path)
        statistics = load_statistics(statistics_path)
        results = load_batch_results(batch_results_path)
        
        logger.info(f"読み込み完了: 統計情報、{len(results)}件の結果")
        
        # プロンプト生成
        logger.info("分析プロンプトを生成中...")
        prompt = generate_analysis_prompt(research_context, statistics, results)
        
        # LLM問い合わせ
        logger.info(f"LLMに問い合わせ中（モデル: {args.model}）...")
        analysis = analyze_with_llm(prompt, model_name=args.model)
        
        if not analysis:
            logger.error("LLM考察の取得に失敗しました")
            return 1
        
        # レポート生成
        logger.info("分析レポートを生成中...")
        generate_analysis_report(research_context, statistics, results, analysis, output_path)
        
        logger.info("=" * 60)
        logger.info("分析完了")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

