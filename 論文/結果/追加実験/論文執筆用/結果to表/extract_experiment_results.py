#!/usr/bin/env python3
"""
追加実験結果抽出スクリプト
各追加実験のbatch_results.jsonから統計情報を抽出し、論文執筆用のMarkdown形式の表として出力する
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
from statistics import mean


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_batch_results(experiment_path: Path) -> Dict[str, Any]:
    """JSONファイルを読み込み、構造を返す"""
    try:
        with open(experiment_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        logger.warning(f"ファイルが見つかりません: {experiment_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"JSONパースエラー: {experiment_path} - {e}")
        return {}


def extract_bert_score(evaluation: Dict[str, Any]) -> Optional[float]:
    """evaluationからBERTスコアを抽出"""
    if 'bert_score' not in evaluation or evaluation['bert_score'] is None:
        return None
    bert_score = evaluation['bert_score']
    if isinstance(bert_score, dict):
        return bert_score.get('f1', None)
    return float(bert_score)


def extract_llm_score(evaluation: Dict[str, Any]) -> Optional[float]:
    """evaluationからLLMスコアを抽出"""
    if 'llm_score' not in evaluation or evaluation['llm_score'] is None:
        return None
    return float(evaluation['llm_score'])


def extract_model_comparison(data: Dict[str, Any]) -> Dict[str, Any]:
    """モデル比較実験の結果抽出"""
    results = data.get('results', [])
    
    model_stats = defaultdict(lambda: {'bert_scores': [], 'count': 0})
    aspect_model_stats = defaultdict(lambda: {'bert_scores': [], 'count': 0})
    
    for result in results:
        exp_info = result.get('experiment_info', {})
        evaluation = result.get('evaluation', {})
        
        model = exp_info.get('gpt_model', 'unknown')
        aspect = exp_info.get('aspect', 'unknown')
        
        bert_score = extract_bert_score(evaluation)
        
        if bert_score is not None:
            model_stats[model]['bert_scores'].append(bert_score)
            model_stats[model]['count'] += 1
            
            aspect_model_stats[f"{aspect}_{model}"]['bert_scores'].append(bert_score)
            aspect_model_stats[f"{aspect}_{model}"]['count'] += 1
    
    model_averages = {}
    for model, stats in model_stats.items():
        if stats['bert_scores']:
            model_averages[model] = {
                'mean': mean(stats['bert_scores']),
                'min': min(stats['bert_scores']),
                'max': max(stats['bert_scores']),
                'count': stats['count']
            }
    
    aspect_comparison = defaultdict(lambda: {})
    for key, stats in aspect_model_stats.items():
        if stats['bert_scores']:
            aspect, model = key.rsplit('_', 1)
            if aspect not in aspect_comparison:
                aspect_comparison[aspect] = {}
            aspect_comparison[aspect][model] = mean(stats['bert_scores'])
    
    return {
        'model_averages': model_averages,
        'aspect_comparison': dict(aspect_comparison)
    }


def extract_fewshot_with_llm_results(data: Dict[str, Any]) -> Dict[str, Any]:
    """Few-shot実験（LLM評価有効）の結果抽出"""
    results = data.get('results', [])
    
    fewshot_stats = defaultdict(lambda: {'bert_scores': [], 'llm_scores': [], 'count': 0})
    aspect_fewshot_stats = defaultdict(lambda: defaultdict(lambda: {'bert_scores': [], 'llm_scores': [], 'count': 0}))
    
    for result in results:
        exp_info = result.get('experiment_info', {})
        evaluation = result.get('evaluation', {})
        
        few_shot = exp_info.get('few_shot', 0)
        aspect = exp_info.get('aspect', 'unknown')
        
        bert_score = extract_bert_score(evaluation)
        llm_score = extract_llm_score(evaluation)
        
        if bert_score is not None:
            fewshot_stats[few_shot]['bert_scores'].append(bert_score)
            fewshot_stats[few_shot]['count'] += 1
            aspect_fewshot_stats[aspect][few_shot]['bert_scores'].append(bert_score)
            aspect_fewshot_stats[aspect][few_shot]['count'] += 1
        
        if llm_score is not None:
            fewshot_stats[few_shot]['llm_scores'].append(llm_score)
            aspect_fewshot_stats[aspect][few_shot]['llm_scores'].append(llm_score)
    
    fewshot_averages = {}
    for few_shot, stats in fewshot_stats.items():
        fewshot_averages[few_shot] = {}
        if stats['bert_scores']:
            fewshot_averages[few_shot]['bert_mean'] = mean(stats['bert_scores'])
        if stats['llm_scores']:
            fewshot_averages[few_shot]['llm_mean'] = mean(stats['llm_scores'])
    
    aspect_stats = {}
    for aspect, fewshot_dict in aspect_fewshot_stats.items():
        aspect_stats[aspect] = {}
        for few_shot, stats in fewshot_dict.items():
            if stats['bert_scores']:
                aspect_stats[aspect][few_shot] = {
                    'bert_mean': mean(stats['bert_scores']),
                    'llm_mean': mean(stats['llm_scores']) if stats['llm_scores'] else None
                }
    
    return {
        'fewshot_averages': fewshot_averages,
        'aspect_stats': aspect_stats
    }


def extract_group_size_results(data: Dict[str, Any]) -> Dict[str, Any]:
    """Group Size比較実験の結果抽出"""
    results = data.get('results', [])
    
    group_size_stats = defaultdict(lambda: {'bert_scores': [], 'llm_scores': [], 'count': 0})
    aspect_group_size_stats = defaultdict(lambda: defaultdict(lambda: {'bert_scores': [], 'llm_scores': [], 'count': 0}))
    
    for result in results:
        exp_info = result.get('experiment_info', {})
        evaluation = result.get('evaluation', {})
        
        group_size = exp_info.get('group_size', 0)
        aspect = exp_info.get('aspect', 'unknown')
        
        bert_score = extract_bert_score(evaluation)
        llm_score = extract_llm_score(evaluation)
        
        if bert_score is not None:
            group_size_stats[group_size]['bert_scores'].append(bert_score)
            group_size_stats[group_size]['count'] += 1
            aspect_group_size_stats[aspect][group_size]['bert_scores'].append(bert_score)
            aspect_group_size_stats[aspect][group_size]['count'] += 1
        
        if llm_score is not None:
            group_size_stats[group_size]['llm_scores'].append(llm_score)
            aspect_group_size_stats[aspect][group_size]['llm_scores'].append(llm_score)
    
    group_size_averages = {}
    for group_size, stats in group_size_stats.items():
        group_size_averages[group_size] = {}
        if stats['bert_scores']:
            group_size_averages[group_size]['bert_mean'] = mean(stats['bert_scores'])
        if stats['llm_scores']:
            group_size_averages[group_size]['llm_mean'] = mean(stats['llm_scores'])
    
    aspect_stats = {}
    for aspect, group_size_dict in aspect_group_size_stats.items():
        aspect_stats[aspect] = {}
        for group_size, stats in group_size_dict.items():
            if stats['bert_scores']:
                aspect_stats[aspect][group_size] = {
                    'bert_mean': mean(stats['bert_scores']),
                    'llm_mean': mean(stats['llm_scores']) if stats['llm_scores'] else None
                }
    
    return {
        'group_size_averages': group_size_averages,
        'aspect_stats': aspect_stats
    }


def extract_aspect_description_results(data: Dict[str, Any]) -> Dict[str, Any]:
    """アスペクト説明文比較実験の結果抽出"""
    results = data.get('results', [])
    
    desc_stats = defaultdict(lambda: {'bert_scores': [], 'llm_scores': [], 'count': 0})
    aspect_desc_stats = defaultdict(lambda: defaultdict(lambda: {'bert_scores': [], 'llm_scores': [], 'count': 0}))
    
    for result in results:
        exp_info = result.get('experiment_info', {})
        evaluation = result.get('evaluation', {})
        
        use_desc = exp_info.get('use_aspect_descriptions', False)
        aspect = exp_info.get('aspect', 'unknown')
        desc_key = 'with_desc' if use_desc else 'no_desc'
        
        bert_score = extract_bert_score(evaluation)
        llm_score = extract_llm_score(evaluation)
        
        if bert_score is not None:
            desc_stats[desc_key]['bert_scores'].append(bert_score)
            desc_stats[desc_key]['count'] += 1
            aspect_desc_stats[aspect][desc_key]['bert_scores'].append(bert_score)
            aspect_desc_stats[aspect][desc_key]['count'] += 1
        
        if llm_score is not None:
            desc_stats[desc_key]['llm_scores'].append(llm_score)
            aspect_desc_stats[aspect][desc_key]['llm_scores'].append(llm_score)
    
    desc_averages = {}
    for desc_key, stats in desc_stats.items():
        desc_averages[desc_key] = {}
        if stats['bert_scores']:
            desc_averages[desc_key]['bert_mean'] = mean(stats['bert_scores'])
        if stats['llm_scores']:
            desc_averages[desc_key]['llm_mean'] = mean(stats['llm_scores'])
    
    aspect_comparison = {}
    for aspect, desc_dict in aspect_desc_stats.items():
        aspect_comparison[aspect] = {}
        for desc_key, stats in desc_dict.items():
            if stats['bert_scores']:
                aspect_comparison[aspect][desc_key] = {
                    'bert_mean': mean(stats['bert_scores']),
                    'llm_mean': mean(stats['llm_scores']) if stats['llm_scores'] else None
                }
    
    return {
        'desc_averages': desc_averages,
        'aspect_comparison': aspect_comparison
    }


def extract_coco_results(data: Dict[str, Any]) -> Dict[str, Any]:
    """COCO Retrieved Concepts実験の結果抽出"""
    results = data.get('results', [])
    
    concept_stats = defaultdict(lambda: {'bert_scores': [], 'count': 0})
    
    for result in results:
        exp_info = result.get('experiment_info', {})
        evaluation = result.get('evaluation', {})
        
        aspect = exp_info.get('aspect', 'unknown')
        concept = aspect if aspect.startswith('concept_') else aspect
        bert_score = extract_bert_score(evaluation)
        
        if bert_score is not None:
            concept_stats[concept]['bert_scores'].append(bert_score)
            concept_stats[concept]['count'] += 1
    
    concept_averages = {}
    all_bert_scores = []
    for concept, stats in concept_stats.items():
        if stats['bert_scores']:
            concept_averages[concept] = {
                'mean': mean(stats['bert_scores']),
                'count': stats['count']
            }
            all_bert_scores.extend(stats['bert_scores'])
    
    overall_mean = mean(all_bert_scores) if all_bert_scores else None
    
    return {
        'concept_averages': concept_averages,
        'overall_mean': overall_mean
    }


def generate_markdown_table(data: Dict[str, Any], table_type: str) -> str:
    """抽出したデータをMarkdown形式の表に変換"""
    if table_type == 'model_comparison':
        return generate_model_comparison_table(data)
    elif table_type == 'fewshot_llm':
        return generate_fewshot_llm_table(data)
    elif table_type == 'group_size':
        return generate_group_size_table(data)
    elif table_type == 'aspect_desc':
        return generate_aspect_desc_table(data)
    elif table_type == 'coco':
        return generate_coco_table(data)
    else:
        return ""


def generate_model_comparison_table(data: Dict[str, Any]) -> str:
    """モデル比較実験の表を生成"""
    lines = []
    lines.append("### モデル別平均BERTスコア")
    lines.append("")
    lines.append("| モデル | 平均BERTスコア | 最小BERTスコア | 最大BERTスコア |")
    lines.append("|--------|----------------|----------------|----------------|")
    
    model_averages = data.get('model_averages', {})
    for model in sorted(model_averages.keys()):
        stats = model_averages[model]
        lines.append(f"| {model} | {stats['mean']:.4f} | {stats['min']:.4f} | {stats['max']:.4f} |")
    
    lines.append("")
    lines.append("### アスペクト別比較")
    lines.append("")
    lines.append("| アスペクト | gpt-4o-mini | gpt-5.1 | 差 (4o-mini - 5.1) |")
    lines.append("|-----------|-------------|---------|-----|")
    
    aspect_comparison = data.get('aspect_comparison', {})
    for aspect in sorted(aspect_comparison.keys()):
        models = aspect_comparison[aspect]
        mini_score = models.get('gpt-4o-mini', None)
        gpt51_score = models.get('gpt-5.1', None)
        
        if mini_score is not None and gpt51_score is not None:
            diff = mini_score - gpt51_score
            diff_str = f"{diff:+.4f}" if diff >= 0 else f"{diff:.4f}"
            lines.append(f"| {aspect} | {mini_score:.4f} | {gpt51_score:.4f} | {diff_str} |")
        elif mini_score is not None:
            lines.append(f"| {aspect} | {mini_score:.4f} | - | - |")
        elif gpt51_score is not None:
            lines.append(f"| {aspect} | - | {gpt51_score:.4f} | - |")
    
    return "\n".join(lines)


def generate_fewshot_llm_table(data: Dict[str, Any]) -> str:
    """Few-shot実験の表を生成"""
    lines = []
    lines.append("### Few-shot別平均スコア")
    lines.append("")
    lines.append("| Few-shot | 平均BERTスコア | 平均LLMスコア |")
    lines.append("|----------|----------------|---------------|")
    
    fewshot_averages = data.get('fewshot_averages', {})
    for few_shot in sorted(fewshot_averages.keys()):
        stats = fewshot_averages[few_shot]
        bert_mean = stats.get('bert_mean', None)
        llm_mean = stats.get('llm_mean', None)
        bert_str = f"{bert_mean:.4f}" if bert_mean is not None else "-"
        llm_str = f"{llm_mean:.4f}" if llm_mean is not None else "-"
        lines.append(f"| {few_shot} | {bert_str} | {llm_str} |")
    
    lines.append("")
    lines.append("### アスペクト別統計")
    lines.append("")
    lines.append("| アスペクト | Few-shot | BERTスコア | LLMスコア |")
    lines.append("|-----------|----------|------------|-----------|")
    
    aspect_stats = data.get('aspect_stats', {})
    for aspect in sorted(aspect_stats.keys()):
        fewshot_dict = aspect_stats[aspect]
        for few_shot in sorted(fewshot_dict.keys()):
            stats = fewshot_dict[few_shot]
            bert_mean = stats.get('bert_mean', None)
            llm_mean = stats.get('llm_mean', None)
            bert_str = f"{bert_mean:.4f}" if bert_mean is not None else "-"
            llm_str = f"{llm_mean:.4f}" if llm_mean is not None else "-"
            lines.append(f"| {aspect} | {few_shot} | {bert_str} | {llm_str} |")
    
    return "\n".join(lines)


def generate_group_size_table(data: Dict[str, Any]) -> str:
    """Group Size比較実験の表を生成"""
    lines = []
    lines.append("### Group Size別平均スコア")
    lines.append("")
    lines.append("| Group Size | 平均BERTスコア | 平均LLMスコア |")
    lines.append("|------------|----------------|---------------|")
    
    group_size_averages = data.get('group_size_averages', {})
    for group_size in sorted(group_size_averages.keys()):
        stats = group_size_averages[group_size]
        bert_mean = stats.get('bert_mean', None)
        llm_mean = stats.get('llm_mean', None)
        bert_str = f"{bert_mean:.4f}" if bert_mean is not None else "-"
        llm_str = f"{llm_mean:.4f}" if llm_mean is not None else "-"
        lines.append(f"| {group_size} | {bert_str} | {llm_str} |")
    
    lines.append("")
    lines.append("### アスペクト別統計")
    lines.append("")
    lines.append("| アスペクト | Group Size | BERTスコア | LLMスコア |")
    lines.append("|-----------|------------|------------|-----------|")
    
    aspect_stats = data.get('aspect_stats', {})
    for aspect in sorted(aspect_stats.keys()):
        group_size_dict = aspect_stats[aspect]
        for group_size in sorted(group_size_dict.keys()):
            stats = group_size_dict[group_size]
            bert_mean = stats.get('bert_mean', None)
            llm_mean = stats.get('llm_mean', None)
            bert_str = f"{bert_mean:.4f}" if bert_mean is not None else "-"
            llm_str = f"{llm_mean:.4f}" if llm_mean is not None else "-"
            lines.append(f"| {aspect} | {group_size} | {bert_str} | {llm_str} |")
    
    return "\n".join(lines)


def generate_aspect_desc_table(data: Dict[str, Any]) -> str:
    """アスペクト説明文比較実験の表を生成"""
    lines = []
    lines.append("### 説明文あり/なし別平均スコア")
    lines.append("")
    lines.append("| 説明文 | 平均BERTスコア | 平均LLMスコア |")
    lines.append("|--------|----------------|---------------|")
    
    desc_averages = data.get('desc_averages', {})
    desc_labels = {'with_desc': 'あり', 'no_desc': 'なし'}
    for desc_key in ['no_desc', 'with_desc']:
        if desc_key in desc_averages:
            stats = desc_averages[desc_key]
            bert_mean = stats.get('bert_mean', None)
            llm_mean = stats.get('llm_mean', None)
            bert_str = f"{bert_mean:.4f}" if bert_mean is not None else "-"
            llm_str = f"{llm_mean:.4f}" if llm_mean is not None else "-"
            lines.append(f"| {desc_labels[desc_key]} | {bert_str} | {llm_str} |")
    
    lines.append("")
    lines.append("### アスペクト別対比表")
    lines.append("")
    lines.append("| アスペクト | 説明文なしBERT | 説明文ありBERT | 差 | 説明文なしLLM | 説明文ありLLM | 差 |")
    lines.append("|-----------|----------------|----------------|-----|----------------|----------------|-----|")
    
    aspect_comparison = data.get('aspect_comparison', {})
    for aspect in sorted(aspect_comparison.keys()):
        desc_dict = aspect_comparison[aspect]
        no_desc = desc_dict.get('no_desc', {})
        with_desc = desc_dict.get('with_desc', {})
        
        no_desc_bert = no_desc.get('bert_mean', None)
        with_desc_bert = with_desc.get('bert_mean', None)
        no_desc_llm = no_desc.get('llm_mean', None)
        with_desc_llm = with_desc.get('llm_mean', None)
        
        bert_diff = None
        llm_diff = None
        if no_desc_bert is not None and with_desc_bert is not None:
            bert_diff = with_desc_bert - no_desc_bert
        if no_desc_llm is not None and with_desc_llm is not None:
            llm_diff = with_desc_llm - no_desc_llm
        
        no_desc_bert_str = f"{no_desc_bert:.4f}" if no_desc_bert is not None else "-"
        with_desc_bert_str = f"{with_desc_bert:.4f}" if with_desc_bert is not None else "-"
        bert_diff_str = f"{bert_diff:+.4f}" if bert_diff is not None else "-"
        no_desc_llm_str = f"{no_desc_llm:.4f}" if no_desc_llm is not None else "-"
        with_desc_llm_str = f"{with_desc_llm:.4f}" if with_desc_llm is not None else "-"
        llm_diff_str = f"{llm_diff:+.4f}" if llm_diff is not None else "-"
        
        lines.append(f"| {aspect} | {no_desc_bert_str} | {with_desc_bert_str} | {bert_diff_str} | {no_desc_llm_str} | {with_desc_llm_str} | {llm_diff_str} |")
    
    return "\n".join(lines)


def generate_coco_table(data: Dict[str, Any]) -> str:
    """COCO実験の表を生成"""
    def concept_sort_key(concept: str):
        if concept.startswith("concept_"):
            tail = concept[len("concept_"):]
            if tail.isdigit():
                return (0, int(tail))
        return (1, concept)

    lines = []
    lines.append("### コンセプト別BERTスコア")
    lines.append("")
    lines.append("| コンセプト | 平均BERTスコア | 実験数 |")
    lines.append("|------------|----------------|--------|")
    
    concept_averages = data.get('concept_averages', {})
    for concept in sorted(concept_averages.keys(), key=concept_sort_key):
        stats = concept_averages[concept]
        lines.append(f"| {concept} | {stats['mean']:.4f} | {stats['count']} |")
    
    overall_mean = data.get('overall_mean', None)
    if overall_mean is not None:
        lines.append("")
        lines.append("### 全体平均")
        lines.append("")
        lines.append(f"**平均BERTスコア**: {overall_mean:.4f}")
    
    return "\n".join(lines)


def main() -> None:
    """メイン関数"""
    base_dir = Path(__file__).parent.parent
    project_root = Path(__file__).resolve().parents[5]
    
    experiment_paths = {
        'model_comparison': base_dir / 'model_comparison_temperature0' / '実験結果' / 'batch_results.json',
        'fewshot_llm': base_dir / 'fewshot_llm_eval' / 'steam' / '実験結果' / 'batch_results.json',
        'group_size': base_dir / 'group_size_comparison' / 'steam' / '実験結果' / 'batch_results.json',
        'aspect_desc': base_dir / 'aspect_description_comparison' / 'steam' / '実験結果' / 'batch_results.json',
        'coco': project_root / 'results' / '20251127_140836' / 'batch_results.json'
    }
    
    results = {}
    
    for exp_name, exp_path in experiment_paths.items():
        logger.info(f"処理中: {exp_name}")
        data = load_batch_results(exp_path)
        
        if not data:
            logger.warning(f"データが見つかりません: {exp_name}")
            continue
        
        if exp_name == 'model_comparison':
            results[exp_name] = extract_model_comparison(data)
        elif exp_name == 'fewshot_llm':
            results[exp_name] = extract_fewshot_with_llm_results(data)
        elif exp_name == 'group_size':
            results[exp_name] = extract_group_size_results(data)
        elif exp_name == 'aspect_desc':
            results[exp_name] = extract_aspect_description_results(data)
        elif exp_name == 'coco':
            results[exp_name] = extract_coco_results(data)
    
    output_lines = []
    output_lines.append("# 追加実験結果統計表")
    output_lines.append("")
    
    exp_titles = {
        'model_comparison': '1. モデル比較実験',
        'fewshot_llm': '2. Few-shot実験（LLM評価有効）',
        'group_size': '3. Group Size比較実験',
        'aspect_desc': '4. アスペクト説明文比較実験',
        'coco': '5. COCO Retrieved Concepts実験'
    }
    
    table_types = {
        'model_comparison': 'model_comparison',
        'fewshot_llm': 'fewshot_llm',
        'group_size': 'group_size',
        'aspect_desc': 'aspect_desc',
        'coco': 'coco'
    }
    
    for exp_name in ['model_comparison', 'fewshot_llm', 'group_size', 'aspect_desc', 'coco']:
        if exp_name in results:
            output_lines.append(f"## {exp_titles[exp_name]}")
            output_lines.append("")
            table = generate_markdown_table(results[exp_name], table_types[exp_name])
            output_lines.append(table)
            output_lines.append("")
    
    output_path = Path(__file__).parent / 'experiment_results_tables.md'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    logger.info(f"結果を出力しました: {output_path}")


if __name__ == '__main__':
    main()

