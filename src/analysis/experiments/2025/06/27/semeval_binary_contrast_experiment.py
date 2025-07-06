#!/usr/bin/env python3
"""
SemEval ABSA 二項対比因子抽出実験

PyABSA統合データセットのSemEvalデータを使用して、特定アスペクト含む vs 含まないレビューの
対比因子抽出実験を実行
"""

import sys
import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
import numpy as np
import random

# Utils統合（絶対パス）
utils_dir = Path("/Users/seinoshun/imrb_research/src/analysis/experiments/utils")
sys.path.append(str(utils_dir))

# PyABSAデータセットローダー
sys.path.append("/Users/seinoshun/imrb_research/src/analysis/experiments/2025/06/27")
from dataset_comparison_framework import PyABSADatasetLoader

from contrast_factor_analyzer import ContrastFactorAnalyzer

# 設定
load_dotenv()
RANDOM_SEED = 42
TARGET_SAMPLE_SIZE = 300
MAX_RETRIES = 3

class SemEvalBinaryContrastExperiment:
    """SemEval ABSA二項対比因子抽出実験クラス"""
    
    def __init__(self):
        """初期化"""
        # 結果ディレクトリ設定
        current_dir = Path(__file__).parent
        self.results_dir = current_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        # PyABSAデータセットローダー初期化
        self.loader = PyABSADatasetLoader()
        
        # 対比因子アナライザー初期化
        self.analyzer = ContrastFactorAnalyzer()
        
        # 実験設定 - SemEvalデータセットに特化
        self.target_datasets = [
            '110.112.arts_restaurant14',
            '110.112.arts_laptop14'
        ]
        self.domain_aspects = {
            'restaurant': ['food', 'service', 'atmosphere', 'price'],
            'laptop': ['battery', 'screen', 'keyboard', 'performance']
        }
        self.shot_settings = [0, 1, 3]
        
        # ランダムシード設定
        random.seed(RANDOM_SEED)
        np.random.seed(RANDOM_SEED)
        
        print(f"SemEval二項対比実験初期化完了")
        print(f"対象データセット: {self.target_datasets}")
        print(f"結果ディレクトリ: {self.results_dir}")
    
    def load_semeval_datasets(self) -> Dict[str, List]:
        """SemEvalデータセット読み込み"""
        print("📊 SemEvalデータセット読み込み開始...")
        
        # 利用可能データセット確認
        available_datasets = self.loader.list_available_datasets()
        
        dataset_data = {}
        
        for target_id in self.target_datasets:
            print(f"  {target_id}読み込み中...")
            
            # データセット存在確認
            found_dataset = None
            for dataset in available_datasets:
                if target_id in dataset.dataset_id:
                    found_dataset = dataset
                    break
            
            if not found_dataset:
                print(f"⚠️ データセット{target_id}が見つかりません")
                continue
            
            # データ読み込み
            try:
                records = self.loader.load_dataset(found_dataset.dataset_id)
                if records:
                    dataset_data[target_id] = records
                    print(f"  ✅ {target_id}: {len(records)}件")
                else:
                    print(f"  ❌ {target_id}: データなし")
            except Exception as e:
                print(f"  ❌ {target_id}: 読み込みエラー - {e}")
        
        return dataset_data
    
    def create_binary_splits(self, dataset_data: Dict[str, List]) -> Dict[str, Dict]:
        """二項分割データ作成"""
        print("🔄 二項分割データ作成開始...")
        
        binary_splits = {}
        
        for dataset_id, records in dataset_data.items():
            print(f"\n📊 {dataset_id}データセット分割処理")
            
            # ドメイン判定
            domain = 'restaurant' if 'restaurant' in dataset_id else 'laptop' if 'laptop' in dataset_id else 'unknown'
            if domain == 'unknown':
                print(f"⚠️ {dataset_id}: ドメイン判定不可")
                continue
            
            dataset_splits = {}
            target_aspects = self.domain_aspects.get(domain, [])
            
            for aspect in target_aspects:
                print(f"  {aspect}アスペクト分割中...")
                
                # アスペクト含む/含まないでグループ分割
                group_a = []  # アスペクト含む
                group_b = []  # アスペクト含まない
                
                for record in records:
                    # アスペクトマッチング（部分一致）
                    record_aspect = record.aspect.lower()
                    if aspect.lower() in record_aspect or record_aspect in aspect.lower():
                        group_a.append({
                            'text': record.text,
                            'aspect': record.aspect,
                            'sentiment': record.sentiment
                        })
                    else:
                        group_b.append({
                            'text': record.text,
                            'aspect': record.aspect,
                            'sentiment': record.sentiment
                        })
                
                # サンプル数調整
                adjusted_group_a = self._adjust_sample_size(group_a, TARGET_SAMPLE_SIZE)
                adjusted_group_b = self._adjust_sample_size(group_b, TARGET_SAMPLE_SIZE)
                
                if len(adjusted_group_a) >= TARGET_SAMPLE_SIZE and len(adjusted_group_b) >= TARGET_SAMPLE_SIZE:
                    dataset_splits[aspect] = {
                        'group_a': adjusted_group_a,
                        'group_b': adjusted_group_b,
                        'aspect': aspect,
                        'domain': domain,
                        'dataset_id': dataset_id
                    }
                    print(f"    ✅ {aspect}: A={len(adjusted_group_a)}, B={len(adjusted_group_b)}")
                else:
                    print(f"    ❌ {aspect}: サンプル不足 A={len(adjusted_group_a)}, B={len(adjusted_group_b)}")
            
            if dataset_splits:
                binary_splits[dataset_id] = dataset_splits
        
        return binary_splits
    
    def _adjust_sample_size(self, samples: List[Dict], target_size: int) -> List[Dict]:
        """サンプル数調整"""
        if len(samples) >= target_size:
            return random.sample(samples, target_size)
        elif len(samples) > 0:
            # 重複サンプリングで補完
            return samples + random.choices(samples, k=target_size - len(samples))
        else:
            return samples
    
    def _create_examples(self, domain: str, aspect: str, shot_count: int) -> List[Dict]:
        """Few-shot用例題作成"""
        if shot_count == 0:
            return []
        
        # ドメイン・アスペクト別例題
        domain_examples = {
            'restaurant': {
                'food': [
                    {
                        'group_a': ["The pasta was perfectly cooked and the sauce was amazing."],
                        'group_b': ["The service was excellent but the atmosphere was too noisy."],
                        'answer': "specific food item descriptions and taste evaluations"
                    }
                ],
                'service': [
                    {
                        'group_a': ["The waiter was attentive and friendly throughout our meal."],
                        'group_b': ["The food was delicious but overpriced for the portion size."],
                        'answer': "staff interaction and service quality descriptions"
                    }
                ],
                'atmosphere': [
                    {
                        'group_a': ["The ambiance was romantic with soft lighting and quiet music."],
                        'group_b': ["The food was excellent but the prices were too high."],
                        'answer': "environmental and mood descriptions"
                    }
                ],
                'price': [
                    {
                        'group_a': ["Great value for money, very affordable prices."],
                        'group_b': ["The atmosphere was cozy and the service was fast."],
                        'answer': "cost and value evaluations"
                    }
                ]
            },
            'laptop': {
                'battery': [
                    {
                        'group_a': ["Battery life lasts all day for normal usage."],
                        'group_b': ["The screen quality is excellent but keyboard feels cheap."],
                        'answer': "power consumption and battery duration mentions"
                    }
                ],
                'screen': [
                    {
                        'group_a': ["The display is crisp and colors are vibrant."],
                        'group_b': ["Performance is fast but battery drains quickly."],
                        'answer': "visual quality and display characteristics"
                    }
                ],
                'keyboard': [
                    {
                        'group_a': ["The keyboard is comfortable for long typing sessions."],
                        'group_b': ["The screen is beautiful but performance is slow."],
                        'answer': "typing experience and key responsiveness"
                    }
                ],
                'performance': [
                    {
                        'group_a': ["Fast processing speed and smooth multitasking."],
                        'group_b': ["Great battery life but the screen is dim."],
                        'answer': "speed and computational capability descriptions"
                    }
                ]
            }
        }
        
        # 例題取得
        if domain in domain_examples and aspect in domain_examples[domain]:
            examples = domain_examples[domain][aspect]
            return examples[:shot_count]
        
        return []
    
    def run_binary_contrast_experiments(self, binary_splits: Dict[str, Dict]) -> List[Dict]:
        """二項対比実験実行"""
        print(f"\n🚀 二項対比実験開始...")
        
        all_results = []
        experiment_count = 0
        
        for dataset_id, dataset_splits in binary_splits.items():
            print(f"\n📊 {dataset_id}データセット実験")
            
            for aspect, split_data in dataset_splits.items():
                print(f"  🎯 {aspect}アスペクト")
                
                for shot_count in self.shot_settings:
                    experiment_count += 1
                    print(f"    実験{experiment_count}: {shot_count}-shot")
                    
                    # Few-shot例題作成
                    examples = self._create_examples(split_data['domain'], aspect, shot_count)
                    
                    # データをテキストリストに変換
                    group_a_texts = [item['text'] for item in split_data['group_a']]
                    group_b_texts = [item['text'] for item in split_data['group_b']]
                    
                    # 対比因子分析実行
                    result = self.analyzer.analyze(
                        group_a=group_a_texts,
                        group_b=group_b_texts,
                        correct_answer=f"{aspect} specific characteristics",
                        examples=examples,
                        output_dir=str(self.results_dir)
                    )
                    
                    if result:
                        # メタデータ追加
                        result.update({
                            "experiment_id": experiment_count,
                            "dataset_id": dataset_id,
                            "domain": split_data['domain'],
                            "aspect": aspect,
                            "shot_count": shot_count,
                            "group_a_size": len(split_data['group_a']),
                            "group_b_size": len(split_data['group_b']),
                            "dataset": "SemEval_ABSA_PyABSA",
                            "experiment_type": "binary_contrast_factor"
                        })
                        
                        all_results.append(result)
                        print(f"      ✅ BERT: {result.get('bert_score', 0):.3f}, BLEU: {result.get('bleu_score', 0):.3f}")
                    else:
                        print(f"      ❌ 実験失敗")
        
        return all_results
    
    def save_results(self, results: List[Dict]) -> str:
        """結果保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.results_dir / f"semeval_binary_contrast_experiment_results_{timestamp}.json"
        
        # 統計計算
        bert_scores = [r.get('bert_score', 0) for r in results if r.get('bert_score')]
        bleu_scores = [r.get('bleu_score', 0) for r in results if r.get('bleu_score')]
        
        summary = {
            "experiment_info": {
                "experiment_name": "SemEval ABSA Binary Contrast Factor Extraction",
                "dataset": "SemEval ABSA (PyABSA Integrated)",
                "experiment_type": "binary_contrast_factor",
                "target_datasets": self.target_datasets,
                "domain_aspects": self.domain_aspects,
                "shot_settings": self.shot_settings,
                "target_sample_size": TARGET_SAMPLE_SIZE,
                "total_experiments": len(results),
                "timestamp": timestamp,
                "statistics": {
                    "average_bert_score": np.mean(bert_scores) if bert_scores else 0,
                    "average_bleu_score": np.mean(bleu_scores) if bleu_scores else 0,
                    "bert_std": np.std(bert_scores) if bert_scores else 0,
                    "bleu_std": np.std(bleu_scores) if bleu_scores else 0
                }
            },
            "results": results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 結果保存完了: {output_file}")
        return str(output_file)
    
    def generate_report(self, results: List[Dict], output_file: str):
        """実験レポート生成"""
        timestamp = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        
        # 統計計算
        bert_scores = [r.get('bert_score', 0) for r in results if r.get('bert_score')]
        bleu_scores = [r.get('bleu_score', 0) for r in results if r.get('bleu_score')]
        
        # データセット別統計
        dataset_stats = {}
        for result in results:
            dataset_id = result.get('dataset_id', 'unknown')
            if dataset_id not in dataset_stats:
                dataset_stats[dataset_id] = {'results': [], 'aspects': set(), 'domain': result.get('domain', 'unknown')}
            dataset_stats[dataset_id]['results'].append(result)
            dataset_stats[dataset_id]['aspects'].add(result.get('aspect', 'unknown'))
        
        # レポート作成
        report = f"""# SemEval ABSA 二項対比因子抽出実験レポート

**実験日時**: {timestamp}  
**データセット**: SemEval ABSA (PyABSA統合)  
**総実験数**: {len(results)}回

---

## 🎯 実験概要

### 実験設計
- **タイプ**: 二項対比因子抽出（特定アスペクト含む vs 含まない）
- **データセット数**: {len(self.target_datasets)}種類
- **Few-shot設定**: {', '.join(map(str, self.shot_settings))}
- **各グループサイズ**: {TARGET_SAMPLE_SIZE}レビュー
- **総実験回数**: {len(results)}回

### 対象データセット・アスペクト
"""
        
        for dataset_id in self.target_datasets:
            domain = 'restaurant' if 'restaurant' in dataset_id else 'laptop' if 'laptop' in dataset_id else 'unknown'
            aspects = self.domain_aspects.get(domain, [])
            report += f"- **{dataset_id}** ({domain}): {', '.join(aspects)}\n"
        
        report += f"""
---

## 📊 総合結果

| 指標 | 平均スコア |
|------|-----------|
| **BERTスコア** | {np.mean(bert_scores):.4f} |
| **BLEUスコア** | {np.mean(bleu_scores):.4f} |

---

## 🔍 データセット別詳細結果

"""
        
        for dataset_id, stats in dataset_stats.items():
            dataset_results = stats['results']
            dataset_bert = [r.get('bert_score', 0) for r in dataset_results]
            dataset_bleu = [r.get('bleu_score', 0) for r in dataset_results]
            
            report += f"""### {dataset_id} ({stats['domain']})

**平均スコア**: BERT={np.mean(dataset_bert):.3f}, BLEU={np.mean(dataset_bleu):.3f}  
**実験数**: {len(dataset_results)}回

"""
            
            # アスペクト別結果
            for aspect in sorted(stats['aspects']):
                aspect_results = [r for r in dataset_results if r.get('aspect') == aspect]
                
                report += f"#### {aspect}\n\n"
                report += "| Shot設定 | BERTスコア | BLEUスコア | LLM応答 | データ分割 |\n"
                report += "|----------|------------|------------|---------|------------|\n"
                
                for result in aspect_results:
                    shot = result.get('shot_count', 0)
                    bert = result.get('bert_score', 0)
                    bleu = result.get('bleu_score', 0)
                    response = result.get('llm_response', 'N/A')[:50] + "..." if len(result.get('llm_response', '')) > 50 else result.get('llm_response', 'N/A')
                    group_a_size = result.get('group_a_size', 0)
                    group_b_size = result.get('group_b_size', 0)
                    
                    report += f"| {shot}-shot | {bert:.3f} | {bleu:.3f} | {response} | {group_a_size}件 vs {group_b_size}件 |\n"
                
                report += "\n"
        
        # Shot設定別統計
        shot_stats = {}
        for shot in self.shot_settings:
            shot_results = [r for r in results if r.get('shot_count') == shot]
            if shot_results:
                shot_bert = [r.get('bert_score', 0) for r in shot_results]
                shot_bleu = [r.get('bleu_score', 0) for r in shot_results]
                shot_stats[shot] = {
                    'bert': np.mean(shot_bert),
                    'bleu': np.mean(shot_bleu),
                    'count': len(shot_results)
                }
        
        report += """---

## 🔍 統計分析

### Shot設定別平均スコア
"""
        
        for shot, stats in shot_stats.items():
            report += f"- **{shot}-shot**: BERT={stats['bert']:.4f}, BLEU={stats['bleu']:.4f}\n"
        
        report += f"""

### 主要な発見
1. **最高性能アスペクト**: {"未分析" if not results else "分析中"}
2. **Few-shot学習効果**: {"未分析" if not results else "分析中"}
3. **データセット間比較**: {"未分析" if not results else "分析中"}

---

## ✅ 実験成果

📊 **SemEvalデータセットでの二項対比実験フレームワーク構築完了**  
🎯 **{len(self.target_datasets)}データセット × {sum(len(aspects) for aspects in self.domain_aspects.values())}アスペクト × {len(self.shot_settings)}-shot設定での包括的評価実現**  
🔬 **Few-shot学習による性能向上評価**  
📈 **アスペクト別抽出性能の定量的比較**

---

**結果ファイル**: `{Path(output_file).name}`  
**実験完了時刻**: {timestamp}
"""
        
        # レポート保存
        report_file = self.results_dir / f"SemEval_ABSA二項対比因子抽出実験レポート.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📋 レポート生成完了: {report_file}")
    
    def run_full_experiment(self):
        """完全実験実行"""
        print("🚀 SemEval ABSA二項対比因子抽出実験開始")
        print(f"対象データセット: {', '.join(self.target_datasets)}")
        print(f"Few-shot設定: {self.shot_settings}")
        
        # Phase 1: データセット読み込み
        dataset_data = self.load_semeval_datasets()
        if not dataset_data:
            print("❌ データセット読み込み失敗")
            return
        
        # Phase 2: 二項分割作成
        binary_splits = self.create_binary_splits(dataset_data)
        if not binary_splits:
            print("❌ 二項分割作成失敗")
            return
        
        # Phase 3: 対比実験実行
        results = self.run_binary_contrast_experiments(binary_splits)
        if not results:
            print("❌ 実験実行失敗")
            return
        
        # Phase 4: 結果保存・レポート生成
        output_file = self.save_results(results)
        self.generate_report(results, output_file)
        
        print(f"\n🎉 SemEval ABSA二項対比実験完了!")
        print(f"総実験数: {len(results)}")
        print(f"結果ファイル: {output_file}")
        
        return results


def main():
    """メイン関数"""
    experiment = SemEvalBinaryContrastExperiment()
    results = experiment.run_full_experiment()
    return results


if __name__ == "__main__":
    main() 