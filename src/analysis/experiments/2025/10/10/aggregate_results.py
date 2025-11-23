#!/usr/bin/env python3
"""
実験結果集計スクリプト

実行結果を集計し、実験計画書の表形式テンプレートに合わせてMarkdown表を生成する。
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict
from datetime import datetime


def load_all_results(results_dir: str) -> List[Dict[str, Any]]:
    """
    全結果JSONを読み込み
    
    Args:
        results_dir: 結果ディレクトリのパス
        
    Returns:
        実験結果のリスト
    """
    results_path = Path(results_dir)
    
    # batch_results.jsonを優先的に読み込み
    batch_json = results_path / "batch_results.json"
    if batch_json.exists():
        with open(batch_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('results', [])
    
    # 個別結果JSONを読み込み
    individual_dir = results_path / "individual"
    if individual_dir.exists():
        results = []
        for json_file in individual_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                    results.append(result)
            except Exception as e:
                logging.warning(f"結果ファイル読み込みエラー ({json_file}): {e}")
        return results
    
    # experimentsディレクトリから直接読み込み
    experiments_dir = results_path / "experiments"
    if experiments_dir.exists():
        results = []
        for exp_dir in experiments_dir.iterdir():
            if exp_dir.is_dir():
                # 実験結果JSONを検索
                for json_file in exp_dir.glob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            result = json.load(f)
                            results.append(result)
                    except Exception:
                        pass
        return results
    
    raise FileNotFoundError(f"結果ファイルが見つかりません: {results_dir}")


def extract_experiment_info(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    実験結果から基本情報を抽出
    
    Args:
        result: 実験結果辞書
        
    Returns:
        基本情報辞書
    """
    exp_info = result.get('experiment_info', {})
    
    return {
        'experiment_id': exp_info.get('experiment_id', 'unknown'),
        'dataset': exp_info.get('dataset', 'unknown'),
        'aspect': exp_info.get('aspect', 'unknown'),
        'domain': exp_info.get('domain'),
        'few_shot': exp_info.get('few_shot', 0),
        'gpt_model': exp_info.get('gpt_model', 'unknown'),
        'success': result.get('success', False),
        'bert_score': result.get('evaluation', {}).get('bert_score'),
        'bleu_score': result.get('evaluation', {}).get('bleu_score'),
        'llm_score': result.get('evaluation', {}).get('llm_score'),
        'llm_response': result.get('process', {}).get('llm_response', ''),
        'error': exp_info.get('error')
    }


def create_dataset_comparison_table(results: List[Dict[str, Any]]) -> str:
    """
    データセット別スコア比較表を作成
    
    Args:
        results: 実験結果のリスト
        
    Returns:
        Markdown形式の表
    """
    lines = ["## データセット別スコア比較表", ""]
    lines.append("| データセット | アスペクト | Few-shot | GPTモデル | BERT | BLEU | LLM |")
    lines.append("|------------|----------|----------|-----------|------|------|-----|")
    
    # 成功した実験のみをフィルタ
    successful_results = [r for r in results if extract_experiment_info(r).get('success', False)]
    
    # ソート: データセット > アスペクト > Few-shot > GPTモデル
    successful_results.sort(key=lambda r: (
        extract_experiment_info(r).get('dataset', ''),
        extract_experiment_info(r).get('aspect', ''),
        extract_experiment_info(r).get('few_shot', 0),
        extract_experiment_info(r).get('gpt_model', '')
    ))
    
    for result in successful_results:
        info = extract_experiment_info(result)
        
        dataset = info['dataset']
        aspect = info['aspect']
        few_shot = info['few_shot']
        gpt_model = info['gpt_model']
        bert = info['bert_score']
        bleu = info['bleu_score']
        llm = info['llm_score']
        
        bert_str = f"{bert:.4f}" if bert is not None else "N/A"
        bleu_str = f"{bleu:.4f}" if bleu is not None else "N/A"
        llm_str = f"{llm:.4f}" if llm is not None else "N/A"
        
        lines.append(f"| {dataset} | {aspect} | {few_shot} | {gpt_model} | {bert_str} | {bleu_str} | {llm_str} |")
    
    lines.append("")
    return "\n".join(lines)


def create_fewshot_analysis_table(results: List[Dict[str, Any]]) -> str:
    """
    Few-shot影響分析表を作成
    
    Args:
        results: 実験結果のリスト
        
    Returns:
        Markdown形式の表
    """
    lines = ["## Few-shot影響分析表", ""]
    lines.append("| データセット | アスペクト | GPTモデル | 0-shot BERT | 1-shot BERT | 3-shot BERT | 0-shot BLEU | 1-shot BLEU | 3-shot BLEU | 0-shot LLM | 1-shot LLM | 3-shot LLM |")
    lines.append("|------------|----------|-----------|-------------|-------------|-------------|-------------|-------------|-------------|------------|------------|------------|")
    
    # 成功した実験のみをフィルタ
    successful_results = [r for r in results if extract_experiment_info(r).get('success', False)]
    
    # データセット×アスペクト×GPTモデルでグループ化
    grouped = defaultdict(lambda: {0: {}, 1: {}, 3: {}})
    
    for result in successful_results:
        info = extract_experiment_info(result)
        key = (info['dataset'], info['aspect'], info['gpt_model'])
        few_shot = info['few_shot']
        
        if few_shot in [0, 1, 3]:
            grouped[key][few_shot] = info
    
    # ソート
    sorted_keys = sorted(grouped.keys())
    
    for dataset, aspect, gpt_model in sorted_keys:
        group = grouped[(dataset, aspect, gpt_model)]
        
        def get_score(few_shot, score_type):
            info = group.get(few_shot, {})
            score = info.get(score_type)
            return f"{score:.4f}" if score is not None else "N/A"
        
        bert_0 = get_score(0, 'bert_score')
        bert_1 = get_score(1, 'bert_score')
        bert_3 = get_score(3, 'bert_score')
        bleu_0 = get_score(0, 'bleu_score')
        bleu_1 = get_score(1, 'bleu_score')
        bleu_3 = get_score(3, 'bleu_score')
        llm_0 = get_score(0, 'llm_score')
        llm_1 = get_score(1, 'llm_score')
        llm_3 = get_score(3, 'llm_score')
        
        lines.append(f"| {dataset} | {aspect} | {gpt_model} | {bert_0} | {bert_1} | {bert_3} | {bleu_0} | {bleu_1} | {bleu_3} | {llm_0} | {llm_1} | {llm_3} |")
    
    lines.append("")
    return "\n".join(lines)


def create_model_comparison_table(results: List[Dict[str, Any]]) -> str:
    """
    GPTモデル性能差比較表を作成
    
    Args:
        results: 実験結果のリスト
        
    Returns:
        Markdown形式の表
    """
    lines = ["## GPTモデル性能差比較表", ""]
    lines.append("| データセット | アスペクト | Few-shot | gpt-4o-mini BERT | gpt-5.1 BERT | gpt-4o-mini BLEU | gpt-5.1 BLEU | gpt-4o-mini LLM | gpt-5.1 LLM |")
    lines.append("|------------|----------|----------|------------------|--------------|------------------|--------------|-----------------|-------------|")
    
    # 成功した実験のみをフィルタ
    successful_results = [r for r in results if extract_experiment_info(r).get('success', False)]
    
    # データセット×アスペクト×Few-shotでグループ化
    grouped = defaultdict(lambda: {'gpt-4o-mini': {}, 'gpt-5.1': {}})
    
    for result in successful_results:
        info = extract_experiment_info(result)
        key = (info['dataset'], info['aspect'], info['few_shot'])
        gpt_model = info['gpt_model']
        
        if gpt_model in ['gpt-4o-mini', 'gpt-5.1']:
            grouped[key][gpt_model] = info
    
    # ソート
    sorted_keys = sorted(grouped.keys())
    
    for dataset, aspect, few_shot in sorted_keys:
        group = grouped[(dataset, aspect, few_shot)]
        
        mini_info = group.get('gpt-4o-mini', {})
        gpt51_info = group.get('gpt-5.1', {})
        
        def get_score(info, score_type):
            score = info.get(score_type) if info else None
            return f"{score:.4f}" if score is not None else "N/A"
        
        mini_bert = get_score(mini_info, 'bert_score')
        gpt51_bert = get_score(gpt51_info, 'bert_score')
        mini_bleu = get_score(mini_info, 'bleu_score')
        gpt51_bleu = get_score(gpt51_info, 'bleu_score')
        mini_llm = get_score(mini_info, 'llm_score')
        gpt51_llm = get_score(gpt51_info, 'llm_score')
        
        lines.append(f"| {dataset} | {aspect} | {few_shot} | {mini_bert} | {gpt51_bert} | {mini_bleu} | {gpt51_bleu} | {mini_llm} | {gpt51_llm} |")
    
    lines.append("")
    return "\n".join(lines)


def create_coco_interpretation_report(results: List[Dict[str, Any]]) -> str:
    """
    COCO実験結果の解釈レポートを作成
    
    Args:
        results: 実験結果のリスト
        
    Returns:
        Markdown形式のレポート
    """
    lines = ["## COCO実験結果", ""]
    
    # retrieved_conceptsデータセットの実験のみをフィルタ
    coco_results = [
        r for r in results
        if extract_experiment_info(r).get('dataset') == 'retrieved_concepts'
        and extract_experiment_info(r).get('success', False)
    ]
    
    if not coco_results:
        lines.append("COCO実験結果が見つかりませんでした。")
        lines.append("")
        return "\n".join(lines)
    
    # コンセプト別にグループ化
    grouped = defaultdict(list)
    for result in coco_results:
        info = extract_experiment_info(result)
        concept = info.get('aspect', 'unknown')
        grouped[concept].append(info)
    
    # コンセプトごとにレポート作成
    for concept in sorted(grouped.keys()):
        concept_results = grouped[concept]
        lines.append(f"### {concept}", "")
        
        for info in concept_results:
            few_shot = info['few_shot']
            gpt_model = info['gpt_model']
            llm_response = info.get('llm_response', '')
            bert = info.get('bert_score')
            bleu = info.get('bleu_score')
            llm = info.get('llm_score')
            
            lines.append(f"#### Few-shot: {few_shot}, GPTモデル: {gpt_model}", "")
            lines.append(f"**LLM出力**: {llm_response}", "")
            
            if bert is not None:
                lines.append(f"- BERTスコア: {bert:.4f} (参考値)")
            if bleu is not None:
                lines.append(f"- BLEUスコア: {bleu:.4f} (参考値)")
            if llm is not None:
                lines.append(f"- LLMスコア: {llm:.4f}")
            
            lines.append("")
            lines.append("**解釈**: (手動で記入してください)")
            lines.append("")
    
    return "\n".join(lines)


def generate_summary_report(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    統合レポートを生成
    
    Args:
        results: 実験結果のリスト
        output_path: 出力ファイルパス
    """
    lines = []
    
    # ヘッダー
    lines.append("# 実験結果集計レポート")
    lines.append("")
    lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # 統計情報
    total = len(results)
    successful = sum(1 for r in results if extract_experiment_info(r).get('success', False))
    failed = total - successful
    
    lines.append("## 実行統計")
    lines.append("")
    lines.append(f"- 総実験数: {total}")
    lines.append(f"- 成功: {successful}")
    lines.append(f"- 失敗: {failed}")
    lines.append("")
    
    # 各表を生成
    lines.append(create_dataset_comparison_table(results))
    lines.append(create_fewshot_analysis_table(results))
    lines.append(create_model_comparison_table(results))
    lines.append(create_coco_interpretation_report(results))
    
    # 失敗した実験のリスト
    failed_results = [r for r in results if not extract_experiment_info(r).get('success', False)]
    if failed_results:
        lines.append("## 失敗した実験")
        lines.append("")
        for result in failed_results:
            info = extract_experiment_info(result)
            exp_id = info['experiment_id']
            error = info.get('error', 'Unknown error')
            lines.append(f"- **{exp_id}**: {error}")
        lines.append("")
    
    # ファイルに保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    logging.info(f"集計レポートを保存: {output_path}")


def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(
        description="実験結果を集計してレポートを生成",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--results-dir', '-r',
        type=str,
        required=True,
        help='結果ディレクトリのパス'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='出力ファイルパス (default: {results_dir}/summary_report.md)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='デバッグモード'
    )
    
    args = parser.parse_args()
    
    # ログ設定
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        # 結果を読み込み
        logger.info(f"結果を読み込み: {args.results_dir}")
        results = load_all_results(args.results_dir)
        logger.info(f"読み込んだ結果数: {len(results)}")
        
        # 出力パスを設定
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = Path(args.results_dir) / "summary_report.md"
        
        # レポートを生成
        logger.info("レポートを生成中...")
        generate_summary_report(results, output_path)
        
        logger.info("=" * 60)
        logger.info("集計完了")
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



