#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""実験結果から統計情報を抽出するスクリプト"""

import json
from collections import defaultdict
from pathlib import Path

def extract_statistics():
    # 実験マトリックス読み込み
    with open('実験マトリックス.json', 'r', encoding='utf-8') as f:
        matrix = json.load(f)

    # 結果ファイル読み込み
    with open('results/20251119_153853/batch_results.json', 'r', encoding='utf-8') as f:
        results = json.load(f)

    # 統計情報抽出
    stats = {
        'total_experiments': len(results['results']),
        'datasets': defaultdict(lambda: {'count': 0, 'aspects': set(), 'bert_scores': [], 'bleu_scores': [], 'llm_scores': []}),
        'few_shot_stats': defaultdict(lambda: {'count': 0, 'bert_scores': [], 'bleu_scores': [], 'llm_scores': []}),
        'group_size_stats': defaultdict(lambda: {'count': 0, 'bert_scores': [], 'bleu_scores': [], 'llm_scores': []}),
        'model_stats': defaultdict(lambda: {'count': 0, 'bert_scores': [], 'bleu_scores': [], 'llm_scores': []}),
        'domain_stats': defaultdict(lambda: {'count': 0, 'aspects': set(), 'bert_scores': [], 'bleu_scores': [], 'llm_scores': []}),
    }

    for result in results['results']:
        exp_info = result['experiment_info']
        dataset = exp_info['dataset']
        aspect = exp_info.get('aspect', 'N/A')
        few_shot = exp_info.get('few_shot', 0)
        group_size = exp_info.get('group_size', 0)
        gpt_model = exp_info.get('gpt_model', 'N/A')
        domain = exp_info.get('domain', 'N/A')
        
        stats['datasets'][dataset]['count'] += 1
        stats['datasets'][dataset]['aspects'].add(aspect)
        
        stats['few_shot_stats'][few_shot]['count'] += 1
        stats['group_size_stats'][group_size]['count'] += 1
        stats['model_stats'][gpt_model]['count'] += 1
        
        if domain != 'N/A' and domain is not None:
            stats['domain_stats'][f"{dataset}_{domain}"]['count'] += 1
            stats['domain_stats'][f"{dataset}_{domain}"]['aspects'].add(aspect)
        
        # スコア抽出
        if 'evaluation' in result:
            eval_data = result['evaluation']
            
            # BERTスコア
            if 'bert_score' in eval_data and eval_data['bert_score'] is not None:
                if isinstance(eval_data['bert_score'], dict):
                    bert_score = eval_data['bert_score'].get('f1', 0)
                else:
                    bert_score = float(eval_data['bert_score'])
                stats['datasets'][dataset]['bert_scores'].append(bert_score)
                stats['few_shot_stats'][few_shot]['bert_scores'].append(bert_score)
                stats['group_size_stats'][group_size]['bert_scores'].append(bert_score)
                stats['model_stats'][gpt_model]['bert_scores'].append(bert_score)
                if domain != 'N/A' and domain is not None:
                    stats['domain_stats'][f"{dataset}_{domain}"]['bert_scores'].append(bert_score)
            
            # BLEUスコア
            if 'bleu_score' in eval_data and eval_data['bleu_score'] is not None:
                bleu_score = float(eval_data['bleu_score'])
                stats['datasets'][dataset]['bleu_scores'].append(bleu_score)
                stats['few_shot_stats'][few_shot]['bleu_scores'].append(bleu_score)
                stats['group_size_stats'][group_size]['bleu_scores'].append(bleu_score)
                stats['model_stats'][gpt_model]['bleu_scores'].append(bleu_score)
                if domain != 'N/A' and domain is not None:
                    stats['domain_stats'][f"{dataset}_{domain}"]['bleu_scores'].append(bleu_score)
            
            # LLMスコア
            if 'llm_score' in eval_data and eval_data['llm_score'] is not None:
                llm_score = float(eval_data['llm_score'])
                stats['datasets'][dataset]['llm_scores'].append(llm_score)
                stats['few_shot_stats'][few_shot]['llm_scores'].append(llm_score)
                stats['group_size_stats'][group_size]['llm_scores'].append(llm_score)
                stats['model_stats'][gpt_model]['llm_scores'].append(llm_score)
                if domain != 'N/A' and domain is not None:
                    stats['domain_stats'][f"{dataset}_{domain}"]['llm_scores'].append(llm_score)

    # 平均値計算
    for key in ['datasets', 'few_shot_stats', 'group_size_stats', 'model_stats', 'domain_stats']:
        for k, v in stats[key].items():
            if v['bert_scores']:
                v['avg_bert_score'] = sum(v['bert_scores']) / len(v['bert_scores'])
                v['min_bert_score'] = min(v['bert_scores'])
                v['max_bert_score'] = max(v['bert_scores'])
            if v['bleu_scores']:
                v['avg_bleu_score'] = sum(v['bleu_scores']) / len(v['bleu_scores'])
                v['min_bleu_score'] = min(v['bleu_scores'])
                v['max_bleu_score'] = max(v['bleu_scores'])
            if v['llm_scores']:
                v['avg_llm_score'] = sum(v['llm_scores']) / len(v['llm_scores'])
                v['min_llm_score'] = min(v['llm_scores'])
                v['max_llm_score'] = max(v['llm_scores'])
            if isinstance(v.get('aspects'), set):
                v['aspects'] = sorted(list(v['aspects']))

    return stats, matrix

if __name__ == '__main__':
    stats, matrix = extract_statistics()
    
    # JSON出力
    output_file = Path(__file__).parent / 'experiment_statistics.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'statistics': stats,
            'experiment_matrix': matrix
        }, f, ensure_ascii=False, indent=2)
    
    print(f'統計情報を {output_file} に保存しました')

