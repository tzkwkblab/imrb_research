#!/usr/bin/env python3
"""
モデル比較実験結果のLLM分析スクリプト（temperature=0版）

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
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent.parent.parent.parent
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
        content = f.read()
        # .mdcファイルの場合はフロントマターを除去
        if content.startswith('---'):
            lines = content.split('\n')
            in_frontmatter = True
            result_lines = []
            for line in lines:
                if in_frontmatter and line.strip() == '---':
                    in_frontmatter = False
                    continue
                if not in_frontmatter:
                    result_lines.append(line)
            return '\n'.join(result_lines)
        return content


def load_batch_results(batch_results_path: Path) -> Dict[str, Any]:
    """バッチ結果を読み込み"""
    if not batch_results_path.exists():
        raise FileNotFoundError(f"バッチ結果ファイルが見つかりません: {batch_results_path}")
    
    with open(batch_results_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_statistics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """統計情報を計算"""
    model_stats = {}
    aspect_stats = {}
    
    for result in results:
        exp_info = result.get('experiment_info', {})
        model = exp_info.get('gpt_model', 'unknown')
        aspect = exp_info.get('aspect', 'unknown')
        
        eval_data = result.get('evaluation', {})
        bert_score = None
        if 'bert_score' in eval_data and eval_data['bert_score'] is not None:
            if isinstance(eval_data['bert_score'], dict):
                bert_score = eval_data['bert_score'].get('f1', 0)
            else:
                bert_score = float(eval_data['bert_score'])
        
        bleu_score = None
        if 'bleu_score' in eval_data and eval_data['bleu_score'] is not None:
            bleu_score = float(eval_data['bleu_score'])
        
        llm_score = None
        if 'llm_score' in eval_data and eval_data['llm_score'] is not None:
            llm_score = float(eval_data['llm_score'])
        
        # モデル別統計
        if model not in model_stats:
            model_stats[model] = {
                'bert_scores': [],
                'bleu_scores': [],
                'llm_scores': [],
                'count': 0
            }
        
        if bert_score is not None:
            model_stats[model]['bert_scores'].append(bert_score)
        if bleu_score is not None:
            model_stats[model]['bleu_scores'].append(bleu_score)
        if llm_score is not None:
            model_stats[model]['llm_scores'].append(llm_score)
        model_stats[model]['count'] += 1
        
        # アスペクト別統計
        key = f"{aspect}_{model}"
        if key not in aspect_stats:
            aspect_stats[key] = {
                'aspect': aspect,
                'model': model,
                'bert_score': bert_score,
                'bleu_score': bleu_score,
                'llm_score': llm_score
            }
    
    # 統計を集計
    statistics = {
        'model_stats': {},
        'aspect_comparison': {}
    }
    
    for model, stats in model_stats.items():
        bert_scores = stats['bert_scores']
        llm_scores = stats['llm_scores']
        if bert_scores:
            stat_dict = {
                'avg_bert_score': sum(bert_scores) / len(bert_scores),
                'min_bert_score': min(bert_scores),
                'max_bert_score': max(bert_scores),
                'count': stats['count']
            }
            if llm_scores:
                stat_dict['avg_llm_score'] = sum(llm_scores) / len(llm_scores)
                stat_dict['min_llm_score'] = min(llm_scores)
                stat_dict['max_llm_score'] = max(llm_scores)
            statistics['model_stats'][model] = stat_dict
    
    # アスペクト別比較
    aspects = set()
    for key in aspect_stats.keys():
        aspects.add(aspect_stats[key]['aspect'])
    
    for aspect in sorted(aspects):
        aspect_comparison = {}
        for key, data in aspect_stats.items():
            if data['aspect'] == aspect:
                aspect_comparison[data['model']] = {
                    'bert_score': data['bert_score'],
                    'llm_score': data['llm_score']
                }
        statistics['aspect_comparison'][aspect] = aspect_comparison
    
    return statistics


def format_statistics_for_prompt(statistics: Dict[str, Any], experiment_plan: Dict[str, Any]) -> str:
    """統計情報をプロンプト用にフォーマット"""
    lines = []
    
    lines.append("## 実験設定")
    settings = experiment_plan.get('settings', {})
    lines.append(f"- データセット: {settings.get('dataset', 'unknown')}")
    lines.append(f"- アスペクト: {', '.join(settings.get('aspects', []))}")
    lines.append(f"- GPTモデル: {', '.join(settings.get('gpt_models', []))}")
    lines.append(f"- group_size: {settings.get('group_size', 'unknown')}")
    lines.append(f"- few_shot: {settings.get('few_shot', 'unknown')}")
    lines.append(f"- temperature: {settings.get('temperature', 'unknown')}")
    lines.append(f"- use_llm_evaluation: {settings.get('use_llm_evaluation', False)}")
    if settings.get('use_llm_evaluation'):
        lines.append(f"- llm_evaluation_model: {settings.get('llm_evaluation_model', 'unknown')}")
    lines.append("")
    
    lines.append("## モデル別統計")
    for model, stats in statistics.get('model_stats', {}).items():
        avg_bert = stats.get('avg_bert_score', 0)
        min_bert = stats.get('min_bert_score', 0)
        max_bert = stats.get('max_bert_score', 0)
        line = f"- **{model}**: BERT平均={avg_bert:.4f}, 最小={min_bert:.4f}, 最大={max_bert:.4f}"
        if 'avg_llm_score' in stats:
            avg_llm = stats.get('avg_llm_score', 0)
            line += f", LLM平均={avg_llm:.4f}"
        lines.append(line)
    lines.append("")
    
    lines.append("## アスペクト別比較")
    for aspect, comparison in statistics.get('aspect_comparison', {}).items():
        lines.append(f"### {aspect}")
        for model, scores in comparison.items():
            bert_score = scores.get('bert_score')
            llm_score = scores.get('llm_score')
            line = f"- **{model}**: BERT={bert_score:.4f}" if bert_score is not None else f"- **{model}**: BERT=N/A"
            if llm_score is not None:
                line += f", LLM={llm_score:.4f}"
            lines.append(line)
        lines.append("")
    
    return "\n".join(lines)


def format_detailed_results_for_prompt(results: List[Dict[str, Any]]) -> str:
    """詳細結果をプロンプト用にフォーマット"""
    lines = []
    lines.append("## 詳細結果（アスペクト × モデル別）")
    lines.append("")
    
    # アスペクト × モデルでグループ化
    grouped = {}
    for result in results:
        exp_info = result.get('experiment_info', {})
        aspect = exp_info.get('aspect', 'unknown')
        model = exp_info.get('gpt_model', 'unknown')
        
        key = f"{aspect}_{model}"
        if key not in grouped:
            grouped[key] = {
                'aspect': aspect,
                'model': model,
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
        lines.append(f"### {data['aspect']} - {data['model']}")
        lines.append(f"- BERTスコア: {data['bert_score']:.4f}" if data['bert_score'] is not None else "- BERTスコア: N/A")
        lines.append(f"- BLEUスコア: {data['bleu_score']:.4f}" if data['bleu_score'] is not None else "- BLEUスコア: N/A")
        if data['llm_score'] is not None:
            lines.append(f"- LLMスコア: {data['llm_score']:.4f}")
        if data['llm_response']:
            lines.append(f"- LLM出力: {data['llm_response'][:200]}...")
        lines.append("")
    
    return "\n".join(lines)


def generate_analysis_prompt(
    research_context: str,
    statistics: Dict[str, Any],
    experiment_plan: Dict[str, Any],
    results: List[Dict[str, Any]]
) -> str:
    """分析プロンプトを生成"""
    stats_text = format_statistics_for_prompt(statistics, experiment_plan)
    results_text = format_detailed_results_for_prompt(results)
    
    prompt = f"""あなたは説明可能AIの研究における実験結果の分析専門家です。以下の研究背景と実験結果を詳細に考察してください。

# 研究背景

{research_context}

# 実験のコンテキスト

- **実験タイプ**: 追加実験（モデル比較、temperature=0版）
- **実験の役割**: Steamデータセットでのgpt-4o-miniとgpt-5.1の性能比較
- **実験計画での位置づけ**: temperature=0、group_size=100、few_shot=0、LLM評価有効での公平なモデル比較
- **評価指標**: BERTスコア（意味類似度）、BLEUスコア（表層一致率）、LLMスコア（gpt-4oによる意味的類似度評価）

# 実験結果

{stats_text}

{results_text}

# 考察指示

この実験結果から言えることを1000文字程度で考察してください。以下の観点を含めてください：

1. **モデル間の性能差の意味**
   - temperature=0設定での平均性能の比較
   - アスペクトによる性能差の要因
   - LLM評価スコアを含めた多角的な評価
   - モデル選択の実用的な示唆

2. **temperature=0設定での結果の解釈**
   - 決定論的な出力設定での対比因子抽出の特性
   - BERTスコアとLLMスコアの関係性
   - 0-shot設定での対比因子抽出の特性

3. **アスペクト特性とモデル性能**
   - アスペクトによって優劣が異なる理由
   - 具体的なアスペクト（gameplay, visual）と抽象的なアスペクト（story, audio）での性能差
   - LLM評価スコアが低いアスペクトの特徴
   - 実用的なモデル選択の示唆

4. **研究への貢献**
   - この実験結果が対比因子生成研究に与える示唆
   - temperature=0設定での対比因子抽出の実現可能性
   - LLM評価指標の有用性
   - 今後の研究への示唆

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
    experiment_plan: Dict[str, Any],
    results: List[Dict[str, Any]],
    analysis: str,
    output_path: Path
) -> None:
    """分析レポートを生成"""
    lines = []
    
    lines.append("# Steamモデル比較実験結果のLLM分析（temperature=0版）")
    lines.append("")
    lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    lines.append("## 実験概要")
    lines.append("")
    settings = experiment_plan.get('settings', {})
    lines.append(f"- **データセット**: {settings.get('dataset', 'unknown')}")
    lines.append(f"- **アスペクト**: {', '.join(settings.get('aspects', []))}")
    lines.append(f"- **GPTモデル**: {', '.join(settings.get('gpt_models', []))}")
    lines.append(f"- **総実験数**: {experiment_plan.get('total_experiments', 0)}実験")
    exec_info = experiment_plan.get('execution_info', {})
    lines.append(f"- **成功**: {exec_info.get('successful_experiments', 0)}実験")
    lines.append(f"- **失敗**: {exec_info.get('failed_experiments', 0)}実験")
    lines.append(f"- **temperature**: {settings.get('temperature', 'unknown')}")
    lines.append(f"- **LLM評価**: {settings.get('use_llm_evaluation', False)}")
    lines.append("")
    
    lines.append("## 主要結果")
    lines.append("")
    lines.append("### モデル別の平均スコア")
    for model, stats in statistics.get('model_stats', {}).items():
        avg_bert = stats.get('avg_bert_score', 0)
        line = f"- **{model}**: BERT={avg_bert:.4f}"
        if 'avg_llm_score' in stats:
            avg_llm = stats.get('avg_llm_score', 0)
            line += f", LLM={avg_llm:.4f}"
        lines.append(line)
    lines.append("")
    
    lines.append("### アスペクト別の比較")
    for aspect, comparison in statistics.get('aspect_comparison', {}).items():
        lines.append(f"#### {aspect}")
        for model, scores in comparison.items():
            bert_score = scores.get('bert_score')
            llm_score = scores.get('llm_score')
            line = f"- **{model}**: BERT={bert_score:.4f}" if bert_score is not None else f"- **{model}**: BERT=N/A"
            if llm_score is not None:
                line += f", LLM={llm_score:.4f}"
            lines.append(line)
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
        description="モデル比較実験結果をLLMで分析（temperature=0版）",
        formatter_class=argparse.RawDescriptionHelpFormatter
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
        experiment_dir = script_dir.parent
        
        batch_results_path = Path(args.batch_results) if args.batch_results else experiment_dir / "実験結果" / "batch_results.json"
        
        if args.research_context:
            research_context_path = Path(args.research_context)
        else:
            research_context_path = project_root / ".cursor" / "rules" / "research-overview.mdc"
        
        output_path = Path(args.output) if args.output else experiment_dir / "分析レポート" / "model_comparison_temperature0_analysis.md"
        
        # ファイル存在確認
        if not batch_results_path.exists():
            logger.error(f"バッチ結果ファイルが見つかりません: {batch_results_path}")
            return 1
        
        if not research_context_path.exists():
            logger.warning(f"研究コンテキストファイルが見つかりません: {research_context_path}")
            logger.info("研究コンテキストなしで続行します...")
            research_context = ""
        else:
            # データ読み込み
            logger.info("データを読み込み中...")
            research_context = load_research_context(research_context_path)
            if not research_context:
                logger.warning("研究コンテキストが空です。続行します...")
        
        batch_data = load_batch_results(batch_results_path)
        experiment_plan = batch_data.get('experiment_plan', {})
        results = batch_data.get('results', [])
        
        logger.info(f"実験結果を読み込み: {len(results)}件")
        
        # 統計情報を計算
        logger.info("統計情報を計算中...")
        statistics = calculate_statistics(results)
        
        # プロンプト生成
        logger.info("分析プロンプトを生成中...")
        prompt = generate_analysis_prompt(research_context, statistics, experiment_plan, results)
        
        if args.debug:
            logger.debug(f"プロンプト長: {len(prompt)}文字")
            logger.debug("プロンプトの最初の500文字:")
            logger.debug(prompt[:500])
        
        # LLM問い合わせ
        logger.info(f"LLM（{args.model}）に問い合わせ中...")
        analysis = analyze_with_llm(prompt, model_name=args.model)
        
        if not analysis:
            logger.error("LLM分析の取得に失敗しました")
            return 1
        
        # レポート生成
        logger.info("分析レポートを生成中...")
        generate_analysis_report(
            research_context,
            statistics,
            experiment_plan,
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

