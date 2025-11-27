#!/usr/bin/env python3
"""
Group Size比較実験結果のLLM分析スクリプト

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
# 論文/結果/追加実験/論文執筆用/group_size_comparison/steam/実行ファイル から6階層上がってプロジェクトルート
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
    lines.append("- Group Size設定: 50, 100, 150, 200, 300（5段階）")
    lines.append("- Few-shot: 0")
    lines.append("- Temperature: 0.0")
    lines.append("- Max tokens: 2000")
    lines.append("- 評価指標: BERTスコア、BLEUスコア、LLMスコア")
    lines.append("")
    
    # Group Size別統計
    if 'group_size_stats' in statistics:
        lines.append("## Group Size別の平均スコア")
        for group_size in ['50', '100', '150', '200', '300']:
            stats = statistics.get('group_size_stats', {}).get(group_size, {})
            bert_stats = stats.get('bert_score', {})
            llm_stats = stats.get('llm_score', {})
            avg_bert = bert_stats.get('avg', 0)
            min_bert = bert_stats.get('min', 0)
            max_bert = bert_stats.get('max', 0)
            avg_llm = llm_stats.get('avg', 0)
            lines.append(f"- Group Size {group_size}: BERT平均={avg_bert:.4f}, 最小={min_bert:.4f}, 最大={max_bert:.4f}, LLM平均={avg_llm:.4f}")
        lines.append("")
    
    # アスペクト別統計
    if 'aspect_stats' in statistics:
        lines.append("## アスペクト別の統計")
        for aspect, stats in sorted(statistics.get('aspect_stats', {}).items()):
            bert_stats = stats.get('bert_score', {})
            llm_stats = stats.get('llm_score', {})
            avg_bert = bert_stats.get('avg', 0)
            min_bert = bert_stats.get('min', 0)
            max_bert = bert_stats.get('max', 0)
            avg_llm = llm_stats.get('avg', 0)
            lines.append(f"- {aspect}: BERT平均={avg_bert:.4f}, 最小={min_bert:.4f}, 最大={max_bert:.4f}, LLM平均={avg_llm:.4f}")
        lines.append("")
    
    # 全体統計
    if 'overall_stats' in statistics:
        overall = statistics.get('overall_stats', {})
        bert_stats = overall.get('bert_score', {})
        llm_stats = overall.get('llm_score', {})
        lines.append("## 全体統計")
        lines.append(f"- BERT平均={bert_stats.get('avg', 0):.4f}, 最小={bert_stats.get('min', 0):.4f}, 最大={bert_stats.get('max', 0):.4f}")
        lines.append(f"- LLM平均={llm_stats.get('avg', 0):.4f}, 最小={llm_stats.get('min', 0):.4f}, 最大={llm_stats.get('max', 0):.4f}")
        lines.append("")
    
    return "\n".join(lines)


def format_detailed_results_for_prompt(results: List[Dict[str, Any]]) -> str:
    """詳細結果をプロンプト用にフォーマット"""
    lines = []
    lines.append("## 詳細結果（アスペクト × Group Size別）")
    lines.append("")
    
    # アスペクト × Group Sizeでグループ化
    grouped = {}
    for result in results:
        exp_info = result.get('experiment_info', {})
        aspect = exp_info.get('aspect', 'unknown')
        group_size = exp_info.get('group_size', None)
        
        if group_size is None:
            # experiment_idからgroup_sizeを抽出
            exp_id = exp_info.get('experiment_id', '')
            for size in [50, 100, 150, 200, 300]:
                if f'group_size_{size}' in exp_id:
                    group_size = size
                    break
        
        if group_size is None:
            continue
        
        key = f"{aspect}_{group_size}"
        if key not in grouped:
            grouped[key] = {
                'aspect': aspect,
                'group_size': group_size,
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
            if isinstance(eval_data['llm_score'], dict):
                grouped[key]['llm_score'] = eval_data['llm_score'].get('normalized_score', 0)
            else:
                grouped[key]['llm_score'] = float(eval_data['llm_score'])
        
        process_data = result.get('process', {})
        if 'llm_response' in process_data:
            grouped[key]['llm_response'] = process_data['llm_response']
        elif 'output' in result:
            grouped[key]['llm_response'] = result['output']
    
    # ソートして表示
    for key in sorted(grouped.keys()):
        data = grouped[key]
        lines.append(f"### {data['aspect']} - Group Size {data['group_size']}")
        lines.append(f"- BERTスコア: {data['bert_score']:.4f}" if data['bert_score'] is not None else "- BERTスコア: N/A")
        lines.append(f"- BLEUスコア: {data['bleu_score']:.4f}" if data['bleu_score'] is not None else "- BLEUスコア: N/A")
        lines.append(f"- LLMスコア: {data['llm_score']:.4f}" if data['llm_score'] is not None else "- LLMスコア: N/A")
        if data['llm_response']:
            response_text = str(data['llm_response'])
            lines.append(f"- LLM出力: {response_text[:200]}...")
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
    
    # BLEUスコアが全て0かチェック
    all_bleu_zero = True
    for result in results:
        eval_data = result.get('evaluation', {})
        if 'bleu_score' in eval_data and eval_data.get('bleu_score', 0) != 0:
            all_bleu_zero = False
            break
    
    bleu_note = ""
    if all_bleu_zero:
        bleu_note = "\n**注意**: 全実験でBLEUスコアは0.0000であり、表層的な語彙一致はほとんど見られない。\n"
    
    prompt = f"""あなたは説明可能AIの研究における実験結果の分析専門家です。以下の研究背景と実験結果を詳細に考察してください。

# 研究背景

{research_context}

# 実験のコンテキスト

- **実験タイプ**: 追加実験（Group Size影響調査）
- **実験の役割**: Steamデータセットでのグループサイズ（50/100/150/200/300）が対比因子生成性能に与える影響の調査
- **実験計画での位置づけ**: few_shot=0、temperature=0.0、max_tokens=2000での公平なグループサイズ比較
- **評価指標**: BERTスコア（意味類似度）、BLEUスコア（表層一致率）、LLMスコア（GPT-4o-miniによる意味的類似度評価）
{bleu_note}
# 実験結果

{stats_text}

{results_text}

# 考察指示

この実験結果から言えることを1000文字程度で考察してください。以下の観点を含めてください：

1. **Group Sizeによる性能変化の傾向**
   - グループサイズ（50/100/150/200/300）の間でBERTスコア、LLMスコアがどのように変化しているか
   - 最適なグループサイズの存在とその理由
   - グループサイズが対比因子抽出の性能に与える影響

2. **アスペクトによる性能差の要因**
   - 各アスペクト（gameplay, visual, story, audio）で性能が異なる理由
   - グループサイズの影響がアスペクトによって異なる理由
   - 具体的なアスペクトと抽象的なアスペクトでの性能差

3. **評価指標間の関係性**
   - BERTスコア、BLEUスコア、LLMスコアの相関関係
   - 各評価指標が示す意味の違い
   - グループサイズが評価指標に与える影響の違い

4. **研究への貢献**
   - この実験結果が対比因子生成研究に与える示唆
   - LLMによる対比因子ラベル自動生成の実現可能性への示唆
   - 実用的なグループサイズ選択の指針

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
    
    lines.append("# Steam Group Size比較実験結果のLLM分析")
    lines.append("")
    lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    lines.append("## 実験概要")
    lines.append("")
    lines.append("- **データセット**: Steam")
    lines.append("- **アスペクト**: gameplay, visual, story, audio（4アスペクト）")
    lines.append("- **Group Size設定**: 50, 100, 150, 200, 300（5段階）")
    lines.append("- **Few-shot**: 0")
    lines.append("- **Temperature**: 0.0")
    lines.append("- **Max tokens**: 2000")
    lines.append("- **総実験数**: 20実験")
    lines.append("- **成功**: 20実験")
    lines.append("- **失敗**: 0実験")
    lines.append("")
    
    lines.append("## 主要結果")
    lines.append("")
    if 'group_size_stats' in statistics:
        lines.append("### Group Size別の平均スコア")
        for group_size in ['50', '100', '150', '200', '300']:
            stats = statistics.get('group_size_stats', {}).get(group_size, {})
            bert_stats = stats.get('bert_score', {})
            llm_stats = stats.get('llm_score', {})
            avg_bert = bert_stats.get('avg', 0)
            avg_llm = llm_stats.get('avg', 0)
            lines.append(f"- **Group Size {group_size}**: BERT={avg_bert:.4f}, LLM={avg_llm:.4f}")
        lines.append("")
    
    if 'aspect_stats' in statistics:
        lines.append("### アスペクト別の平均スコア")
        for aspect, stats in sorted(statistics.get('aspect_stats', {}).items()):
            bert_stats = stats.get('bert_score', {})
            llm_stats = stats.get('llm_score', {})
            avg_bert = bert_stats.get('avg', 0)
            avg_llm = llm_stats.get('avg', 0)
            lines.append(f"- **{aspect}**: BERT={avg_bert:.4f}, LLM={avg_llm:.4f}")
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
        description="Group Size比較実験結果をLLMで分析",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    script_dir = Path(__file__).resolve().parent
    group_size_dir = script_dir.parent
    
    parser.add_argument(
        '--statistics', '-s',
        type=str,
        default=str(group_size_dir / "実験設定" / "group_size_comparison_statistics.json"),
        help='統計情報JSONファイルのパス'
    )
    
    parser.add_argument(
        '--batch-results', '-b',
        type=str,
        default=str(group_size_dir / "実験結果" / "batch_results.json"),
        help='バッチ結果JSONファイルのパス'
    )
    
    parser.add_argument(
        '--research-context', '-r',
        type=str,
        default=str(group_size_dir / "research_context.md"),
        help='研究コンテキストMDファイルのパス'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=str(group_size_dir / "分析レポート" / "group_size_comparison_analysis.md"),
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
        statistics_path = Path(args.statistics)
        batch_results_path = Path(args.batch_results)
        research_context_path = Path(args.research_context)
        output_path = Path(args.output)
        
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
        if not research_context:
            logger.error("研究コンテキストが空です")
            return 1
        
        statistics = load_statistics(statistics_path)
        results = load_batch_results(batch_results_path)
        
        logger.info(f"統計情報を読み込み: {len(statistics)}項目")
        logger.info(f"実験結果を読み込み: {len(results)}件")
        
        # プロンプト生成
        logger.info("分析プロンプトを生成中...")
        prompt = generate_analysis_prompt(research_context, statistics, results)
        
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

