#!/usr/bin/env python3
"""
ベースライン類似度計算スクリプト

20個の特徴記述間の相互類似度を計算し、
現在の結果が良いのか悪いのかを評価するためのベースラインを設定します。
"""

import pandas as pd
import numpy as np
from pathlib import Path
from itertools import combinations
import json
from datetime import datetime

# 既存の類似度評価クラスを再利用
from text_similarity_evaluator import TextSimilarityEvaluator


class BaselineSimilarityCalculator:
    """ベースライン類似度計算クラス"""
    
    def __init__(self, csv_path: str):
        """
        初期化
        
        Args:
            csv_path (str): 特徴記述CSVファイルのパス
        """
        self.csv_path = Path(csv_path)
        self.evaluator = TextSimilarityEvaluator()
        self.features = []
        self._load_features()
        
    def _load_features(self):
        """特徴記述の読み込み"""
        try:
            df = pd.read_csv(self.csv_path)
            self.features = []
            for _, row in df.iterrows():
                self.features.append({
                    'id': row['feature_id'],
                    'description': row['feature_description']
                })
            print(f"特徴記述を読み込みました: {len(self.features)}件")
        except Exception as e:
            print(f"CSVファイル読み込みエラー: {e}")
    
    def calculate_pairwise_similarities(self):
        """
        全ての特徴記述ペア間の類似度を計算
        
        Returns:
            Dict: 計算結果を含む辞書
        """
        if len(self.features) < 2:
            print("特徴記述が不足しています")
            return {}
        
        print(f"\\n{len(self.features)}個の特徴記述間の相互類似度を計算中...")
        
        results = []
        bert_scores = []
        bleu_scores = []
        
        # 全ペアの組み合わせを生成
        total_pairs = len(list(combinations(range(len(self.features)), 2)))
        print(f"計算対象ペア数: {total_pairs}")
        
        for i, (idx1, idx2) in enumerate(combinations(range(len(self.features)), 2)):
            feature1 = self.features[idx1]
            feature2 = self.features[idx2]
            
            # 類似度計算
            bert_sim, bleu_sim = self.evaluator.evaluate_similarity(
                feature1['description'], 
                feature2['description']
            )
            
            bert_scores.append(bert_sim)
            bleu_scores.append(bleu_sim)
            
            results.append({
                'feature1_id': feature1['id'],
                'feature1_desc': feature1['description'],
                'feature2_id': feature2['id'],
                'feature2_desc': feature2['description'],
                'bert_similarity': bert_sim,
                'bleu_similarity': bleu_sim
            })
            
            # 進捗表示
            if (i + 1) % 50 == 0 or (i + 1) == total_pairs:
                print(f"進捗: {i + 1}/{total_pairs} ({(i + 1)/total_pairs*100:.1f}%)")
        
        # 統計情報の計算
        stats = {
            'total_pairs': total_pairs,
            'bert_mean': np.mean(bert_scores),
            'bert_std': np.std(bert_scores),
            'bert_min': np.min(bert_scores),
            'bert_max': np.max(bert_scores),
            'bert_median': np.median(bert_scores),
            'bleu_mean': np.mean(bleu_scores),
            'bleu_std': np.std(bleu_scores),
            'bleu_min': np.min(bleu_scores),
            'bleu_max': np.max(bleu_scores),
            'bleu_median': np.median(bleu_scores),
            'calculation_timestamp': datetime.now().isoformat()
        }
        
        return {
            'statistics': stats,
            'pairwise_results': results,
            'bert_scores': bert_scores,
            'bleu_scores': bleu_scores
        }
    
    def analyze_similarity_distribution(self, results: dict):
        """
        類似度分布の分析
        
        Args:
            results (dict): calculate_pairwise_similarities()の結果
        """
        if not results:
            return
            
        stats = results['statistics']
        bert_scores = results['bert_scores']
        bleu_scores = results['bleu_scores']
        
        print("\\n" + "="*60)
        print("ベースライン類似度分析結果")
        print("="*60)
        
        print("\\n### BERT類似度統計")
        print(f"平均値: {stats['bert_mean']:.4f}")
        print(f"中央値: {stats['bert_median']:.4f}")
        print(f"標準偏差: {stats['bert_std']:.4f}")
        print(f"最小値: {stats['bert_min']:.4f}")
        print(f"最大値: {stats['bert_max']:.4f}")
        
        print("\\n### BLEU類似度統計")
        print(f"平均値: {stats['bleu_mean']:.4f}")
        print(f"中央値: {stats['bleu_median']:.4f}")
        print(f"標準偏差: {stats['bleu_std']:.4f}")
        print(f"最小値: {stats['bleu_min']:.4f}")
        print(f"最大値: {stats['bleu_max']:.4f}")
        
        # 分布の分析
        print("\\n### 分布分析")
        
        # BERT類似度の分布
        bert_high = sum(1 for s in bert_scores if s >= 0.8)
        bert_medium = sum(1 for s in bert_scores if 0.6 <= s < 0.8)
        bert_low = sum(1 for s in bert_scores if s < 0.6)
        
        print(f"BERT類似度分布:")
        print(f"  高類似度 (≥0.8): {bert_high}ペア ({bert_high/len(bert_scores)*100:.1f}%)")
        print(f"  中類似度 (0.6-0.8): {bert_medium}ペア ({bert_medium/len(bert_scores)*100:.1f}%)")
        print(f"  低類似度 (<0.6): {bert_low}ペア ({bert_low/len(bert_scores)*100:.1f}%)")
        
        # BLEU類似度の分布
        bleu_high = sum(1 for s in bleu_scores if s >= 0.3)
        bleu_medium = sum(1 for s in bleu_scores if 0.1 <= s < 0.3)
        bleu_low = sum(1 for s in bleu_scores if s < 0.1)
        
        print(f"\\nBLEU類似度分布:")
        print(f"  高類似度 (≥0.3): {bleu_high}ペア ({bleu_high/len(bleu_scores)*100:.1f}%)")
        print(f"  中類似度 (0.1-0.3): {bleu_medium}ペア ({bleu_medium/len(bleu_scores)*100:.1f}%)")
        print(f"  低類似度 (<0.1): {bleu_low}ペア ({bleu_low/len(bleu_scores)*100:.1f}%)")
    
    def compare_with_gpt_results(self, results: dict, gpt_bert_avg: float = 0.7593, gpt_bleu_avg: float = 0.0291):
        """
        GPT結果との比較分析
        
        Args:
            results (dict): ベースライン計算結果
            gpt_bert_avg (float): GPTのBERT類似度平均
            gpt_bleu_avg (float): GPTのBLEU類似度平均
        """
        if not results:
            return
            
        stats = results['statistics']
        
        print("\\n" + "="*60)
        print("GPT結果との比較分析")
        print("="*60)
        
        print("\\n### BERT類似度比較")
        print(f"ベースライン平均: {stats['bert_mean']:.4f}")
        print(f"GPT結果平均: {gpt_bert_avg:.4f}")
        bert_diff = gpt_bert_avg - stats['bert_mean']
        print(f"差分: {bert_diff:+.4f}")
        
        if bert_diff > 0:
            print("→ GPTの結果はベースラインより高い類似度を示している")
        else:
            print("→ GPTの結果はベースライン以下の類似度")
            
        # 統計的な位置づけ
        bert_scores = results['bert_scores']
        gpt_percentile = (sum(1 for s in bert_scores if s <= gpt_bert_avg) / len(bert_scores)) * 100
        print(f"→ GPT結果は全ペアの{gpt_percentile:.1f}パーセンタイル位置")
        
        print("\\n### BLEU類似度比較")
        print(f"ベースライン平均: {stats['bleu_mean']:.4f}")
        print(f"GPT結果平均: {gpt_bleu_avg:.4f}")
        bleu_diff = gpt_bleu_avg - stats['bleu_mean']
        print(f"差分: {bleu_diff:+.4f}")
        
        if bleu_diff > 0:
            print("→ GPTの結果はベースラインより高い類似度を示している")
        else:
            print("→ GPTの結果はベースライン以下の類似度")
            
        # 統計的な位置づけ
        bleu_scores = results['bleu_scores']
        gpt_bleu_percentile = (sum(1 for s in bleu_scores if s <= gpt_bleu_avg) / len(bleu_scores)) * 100
        print(f"→ GPT結果は全ペアの{gpt_bleu_percentile:.1f}パーセンタイル位置")
        
        print("\\n### 総合評価")
        if bert_diff > 0 and gpt_percentile > 50:
            print("✅ GPTは意味的に適切な特徴説明を生成している")
        else:
            print("⚠️ GPTの意味的類似度に改善の余地がある")
            
        if bleu_diff < 0 and gpt_bleu_percentile < 50:
            print("✅ GPTは独自の表現で説明を生成している（多様性がある）")
        else:
            print("ℹ️ GPTの表現は比較的類似している")


def main():
    """メイン実行関数"""
    print("=== ベースライン類似度計算プログラム ===")
    
    # ファイルパス設定
    base_path = "/Users/seinoshun/imrb_research"
    csv_path = f"{base_path}/src/analysis/experiments/review_features.csv"
    output_dir = Path(f"{base_path}/src/analysis/experiments/2025/05/27")
    
    # 計算器の初期化
    calculator = BaselineSimilarityCalculator(csv_path)
    
    # 相互類似度の計算
    results = calculator.calculate_pairwise_similarities()
    
    if not results:
        print("計算に失敗しました")
        return
    
    # 結果の分析
    calculator.analyze_similarity_distribution(results)
    
    # GPT結果との比較
    calculator.compare_with_gpt_results(results)
    
    # 結果の保存
    output_file = output_dir / "baseline_similarity_results.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\\n結果を保存しました: {output_file}")
    except Exception as e:
        print(f"結果保存エラー: {e}")
    
    # CSV形式でも保存
    csv_file = output_dir / "baseline_pairwise_similarities.csv"
    try:
        df = pd.DataFrame(results['pairwise_results'])
        df.to_csv(csv_file, index=False, encoding='utf-8')
        print(f"CSV結果を保存しました: {csv_file}")
    except Exception as e:
        print(f"CSV保存エラー: {e}")


if __name__ == "__main__":
    main()