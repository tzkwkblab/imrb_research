#!/usr/bin/env python3
"""
データセット分割最適化スクリプト

訓練セットを少なくし、テストセットを増やすための
最適な分割比率を検討・実装します。
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
from typing import List, Dict, Tuple


class DatasetSplitOptimizer:
    """データセット分割最適化クラス"""
    
    def __init__(self, csv_path: str):
        """
        初期化
        
        Args:
            csv_path (str): 特徴記述CSVファイルのパス
        """
        self.csv_path = Path(csv_path)
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
    
    def analyze_split_options(self) -> Dict:
        """
        様々な分割比率を分析
        
        Returns:
            Dict: 分割オプションの分析結果
        """
        total_features = len(self.features)
        
        # 様々な分割比率を検討
        split_options = [
            {"train_ratio": 0.2, "test_ratio": 0.8},  # 訓練20%, テスト80%
            {"train_ratio": 0.3, "test_ratio": 0.7},  # 訓練30%, テスト70%
            {"train_ratio": 0.4, "test_ratio": 0.6},  # 訓練40%, テスト60%
            {"train_ratio": 0.5, "test_ratio": 0.5},  # 訓練50%, テスト50%
            {"train_ratio": 0.6, "test_ratio": 0.4},  # 訓練60%, テスト40%
            {"train_ratio": 0.8, "test_ratio": 0.2},  # 現在の設定（参考）
        ]
        
        analysis_results = []
        
        print("\\n" + "="*60)
        print("データセット分割オプション分析")
        print("="*60)
        
        for option in split_options:
            train_size = int(total_features * option["train_ratio"])
            test_size = total_features - train_size
            
            # 最小限必要な訓練データサイズの検討
            min_train_needed = 4  # 現在評価している特徴数
            
            analysis = {
                "train_ratio": option["train_ratio"],
                "test_ratio": option["test_ratio"],
                "train_size": train_size,
                "test_size": test_size,
                "is_feasible": train_size >= min_train_needed,
                "evaluation_power": test_size,  # テストセットが大きいほど評価力が高い
                "efficiency_score": test_size / max(train_size, 1)  # 効率性スコア
            }
            
            analysis_results.append(analysis)
            
            print(f"\\n訓練{option['train_ratio']*100:.0f}% / テスト{option['test_ratio']*100:.0f}%:")
            print(f"  訓練セット: {train_size}件")
            print(f"  テストセット: {test_size}件")
            print(f"  実行可能性: {'✅' if analysis['is_feasible'] else '❌'}")
            print(f"  効率性スコア: {analysis['efficiency_score']:.2f}")
        
        return {
            "total_features": total_features,
            "split_options": analysis_results,
            "recommendation": self._get_recommendation(analysis_results)
        }
    
    def _get_recommendation(self, analysis_results: List[Dict]) -> Dict:
        """
        推奨分割比率の決定
        
        Args:
            analysis_results (List[Dict]): 分析結果
            
        Returns:
            Dict: 推奨設定
        """
        # 実行可能なオプションのみを考慮
        feasible_options = [opt for opt in analysis_results if opt["is_feasible"]]
        
        if not feasible_options:
            return {"error": "実行可能な分割オプションがありません"}
        
        # 効率性スコアが最も高いオプションを推奨
        best_option = max(feasible_options, key=lambda x: x["efficiency_score"])
        
        return {
            "recommended_train_ratio": best_option["train_ratio"],
            "recommended_test_ratio": best_option["test_ratio"],
            "recommended_train_size": best_option["train_size"],
            "recommended_test_size": best_option["test_size"],
            "efficiency_score": best_option["efficiency_score"],
            "reasoning": f"テストセット{best_option['test_size']}件で最大の評価力を確保"
        }
    
    def create_optimized_splits(self, train_ratio: float = 0.3) -> Dict:
        """
        最適化された分割を作成
        
        Args:
            train_ratio (float): 訓練データの比率
            
        Returns:
            Dict: 分割結果
        """
        total_features = len(self.features)
        train_size = int(total_features * train_ratio)
        
        # ランダムに分割（再現性のためにseedを設定）
        np.random.seed(42)
        indices = np.random.permutation(total_features)
        
        train_indices = indices[:train_size]
        test_indices = indices[train_size:]
        
        train_features = [self.features[i] for i in train_indices]
        test_features = [self.features[i] for i in test_indices]
        
        split_result = {
            "train_ratio": train_ratio,
            "test_ratio": 1 - train_ratio,
            "train_size": len(train_features),
            "test_size": len(test_features),
            "train_features": train_features,
            "test_features": test_features,
            "train_feature_ids": [f["id"] for f in train_features],
            "test_feature_ids": [f["id"] for f in test_features],
            "split_timestamp": datetime.now().isoformat()
        }
        
        print(f"\\n最適化された分割を作成しました:")
        print(f"訓練セット: {len(train_features)}件 (ID: {sorted(split_result['train_feature_ids'])})")
        print(f"テストセット: {len(test_features)}件 (ID: {sorted(split_result['test_feature_ids'])})")
        
        return split_result
    
    def compare_current_vs_optimized(self, current_train_ids: List[int] = [2, 3, 4, 5]):
        """
        現在の分割と最適化案の比較
        
        Args:
            current_train_ids (List[int]): 現在の訓練用特徴ID
        """
        total_features = len(self.features)
        current_train_size = len(current_train_ids)
        current_test_size = total_features - current_train_size
        
        print("\\n" + "="*60)
        print("現在の分割 vs 最適化案の比較")
        print("="*60)
        
        print("\\n### 現在の分割")
        print(f"訓練セット: {current_train_size}件 ({current_train_size/total_features*100:.1f}%)")
        print(f"テストセット: {current_test_size}件 ({current_test_size/total_features*100:.1f}%)")
        print(f"訓練用特徴ID: {sorted(current_train_ids)}")
        
        # 推奨分割の作成
        recommended_split = self.create_optimized_splits(train_ratio=0.3)
        
        print("\\n### 推奨分割 (30%/70%)")
        print(f"訓練セット: {recommended_split['train_size']}件 ({recommended_split['train_ratio']*100:.1f}%)")
        print(f"テストセット: {recommended_split['test_size']}件 ({recommended_split['test_ratio']*100:.1f}%)")
        print(f"訓練用特徴ID: {sorted(recommended_split['train_feature_ids'])}")
        
        print("\\n### 改善効果")
        test_increase = recommended_split['test_size'] - current_test_size
        print(f"テストセット増加: +{test_increase}件")
        print(f"評価力向上: {test_increase/current_test_size*100:+.1f}%")
        
        return recommended_split


def main():
    """メイン実行関数"""
    print("=== データセット分割最適化プログラム ===")
    
    # ファイルパス設定
    base_path = "/Users/seinoshun/imrb_research"
    csv_path = f"{base_path}/src/analysis/experiments/review_features.csv"
    output_dir = Path(f"{base_path}/src/analysis/experiments/2025/05/27")
    
    # 最適化器の初期化
    optimizer = DatasetSplitOptimizer(csv_path)
    
    # 分割オプションの分析
    analysis = optimizer.analyze_split_options()
    
    # 推奨設定の表示
    if "recommendation" in analysis and "error" not in analysis["recommendation"]:
        rec = analysis["recommendation"]
        print("\\n" + "="*60)
        print("推奨設定")
        print("="*60)
        print(f"推奨分割比率: 訓練{rec['recommended_train_ratio']*100:.0f}% / テスト{rec['recommended_test_ratio']*100:.0f}%")
        print(f"推奨サイズ: 訓練{rec['recommended_train_size']}件 / テスト{rec['recommended_test_size']}件")
        print(f"理由: {rec['reasoning']}")
    
    # 現在との比較
    optimized_split = optimizer.compare_current_vs_optimized()
    
    # 結果の保存
    output_file = output_dir / "dataset_split_analysis.json"
    try:
        combined_results = {
            "analysis": analysis,
            "optimized_split": optimized_split
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(combined_results, f, ensure_ascii=False, indent=2)
        print(f"\\n結果を保存しました: {output_file}")
    except Exception as e:
        print(f"結果保存エラー: {e}")


if __name__ == "__main__":
    main()