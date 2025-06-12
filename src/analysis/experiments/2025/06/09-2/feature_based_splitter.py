#!/usr/bin/env python3
"""
Feature-Based Review Splitter
ABSAデータセットから特定の特徴を含むレビュー群と含まないレビュー群を作成
"""

import os
import json
import pandas as pd
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set
import argparse
from datetime import datetime

class FeatureBasedSplitter:
    def __init__(self, dataset_path: str = None):
        if dataset_path is None:
            self.dataset_path = Path("data/external/absa-review-dataset/pyabsa-integrated/current/ABSADatasets/datasets")
        else:
            self.dataset_path = Path(dataset_path)
        
        self.results_dir = Path("src/analysis/experiments/2025/06/09-2/results")
        self.results_dir.mkdir(exist_ok=True)
        
    def load_apc_dataset(self, dataset_name: str = "119.Yelp") -> List[Dict]:
        """APCデータセットを読み込み"""
        dataset_path = self.dataset_path / "apc_datasets" / dataset_name
        train_file = dataset_path / "yelp.train.txt"
        test_file = dataset_path / "yelp.test.txt"
        
        samples = []
        
        for file_path in [train_file, test_file]:
            if not file_path.exists():
                print(f"⚠️ File not found: {file_path}")
                continue
                
            print(f"📖 Loading: {file_path.name}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # APCフォーマット: レビューテキスト、アスペクト、センチメントの3行セット
            for i in range(0, len(lines), 3):
                if i + 2 < len(lines):
                    review_text = lines[i].strip()
                    aspect = lines[i + 1].strip()
                    sentiment = lines[i + 2].strip()
                    
                    samples.append({
                        'review_text': review_text,
                        'aspect': aspect,
                        'sentiment': sentiment,
                        'source_file': file_path.name,
                        'sample_id': len(samples)
                    })
        
        print(f"✅ Loaded {len(samples)} samples")
        return samples
    
    def analyze_features(self, samples: List[Dict]) -> Dict:
        """特徴（アスペクト）の分析"""
        print(f"\n🔍 Feature Analysis")
        print("-" * 30)
        
        aspect_counts = Counter([sample['aspect'] for sample in samples])
        sentiment_by_aspect = defaultdict(list)
        
        for sample in samples:
            sentiment_by_aspect[sample['aspect']].append(sample['sentiment'])
        
        # 頻出アスペクトの特徴分析
        frequent_aspects = {k: v for k, v in aspect_counts.items() if v >= 10}
        
        feature_analysis = {}
        for aspect, count in frequent_aspects.items():
            sentiments = sentiment_by_aspect[aspect]
            sentiment_dist = Counter(sentiments)
            
            feature_analysis[aspect] = {
                'total_count': count,
                'sentiment_distribution': dict(sentiment_dist),
                'positive_ratio': sentiment_dist.get('Positive', 0) / count,
                'negative_ratio': sentiment_dist.get('Negative', 0) / count,
                'neutral_ratio': sentiment_dist.get('Neutral', 0) / count
            }
        
        # 結果表示
        print(f"📊 Frequent Aspects (≥10 samples):")
        for aspect, analysis in sorted(feature_analysis.items(), key=lambda x: x[1]['total_count'], reverse=True):
            print(f"  - {aspect}: {analysis['total_count']} samples")
            print(f"    Positive: {analysis['positive_ratio']:.1%}, Negative: {analysis['negative_ratio']:.1%}, Neutral: {analysis['neutral_ratio']:.1%}")
        
        return feature_analysis
    
    def create_feature_based_splits(self, samples: List[Dict], target_features: List[str]) -> Dict:
        """特徴ベースでデータを分割"""
        print(f"\n✂️ Creating Feature-Based Splits")
        print("-" * 40)
        
        splits = {}
        
        for feature in target_features:
            print(f"\n🎯 Processing feature: '{feature}'")
            
            # 特徴を含むグループ（Group A）
            group_a = [sample for sample in samples if sample['aspect'].lower() == feature.lower()]
            
            # 特徴を含まないグループ（Group B）
            group_b = [sample for sample in samples if sample['aspect'].lower() != feature.lower()]
            
            print(f"  📊 Group A (contains '{feature}'): {len(group_a)} samples")
            print(f"  📊 Group B (does not contain '{feature}'): {len(group_b)} samples")
            
            # センチメント分布の確認
            sentiment_a = Counter([s['sentiment'] for s in group_a])
            sentiment_b = Counter([s['sentiment'] for s in group_b])
            
            print(f"  😊 Group A sentiment: {dict(sentiment_a)}")
            print(f"  😊 Group B sentiment: {dict(sentiment_b)}")
            
            splits[feature] = {
                'group_a': group_a,
                'group_b': group_b,
                'group_a_sentiment': dict(sentiment_a),
                'group_b_sentiment': dict(sentiment_b),
                'feature_name': feature
            }
        
        return splits
    
    def save_splits_to_files(self, splits: Dict, output_format: str = 'json'):
        """分割結果をファイルに保存"""
        print(f"\n💾 Saving splits to files")
        print("-" * 30)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for feature, split_data in splits.items():
            feature_safe = feature.replace(' ', '_').replace('/', '_')
            
            # Group A の保存
            group_a_file = self.results_dir / f"group_a_{feature_safe}_{timestamp}.{output_format}"
            group_b_file = self.results_dir / f"group_b_{feature_safe}_{timestamp}.{output_format}"
            
            if output_format == 'json':
                with open(group_a_file, 'w', encoding='utf-8') as f:
                    json.dump(split_data['group_a'], f, indent=2, ensure_ascii=False)
                
                with open(group_b_file, 'w', encoding='utf-8') as f:
                    json.dump(split_data['group_b'], f, indent=2, ensure_ascii=False)
            
            elif output_format == 'csv':
                # Group A
                df_a = pd.DataFrame(split_data['group_a'])
                df_a.to_csv(group_a_file, index=False, encoding='utf-8')
                
                # Group B
                df_b = pd.DataFrame(split_data['group_b'])
                df_b.to_csv(group_b_file, index=False, encoding='utf-8')
            
            print(f"  ✅ {feature}:")
            print(f"    - Group A: {group_a_file}")
            print(f"    - Group B: {group_b_file}")
        
        # 分割統計の保存
        stats_file = self.results_dir / f"split_statistics_{timestamp}.json"
        statistics = {}
        
        for feature, split_data in splits.items():
            statistics[feature] = {
                'group_a_count': len(split_data['group_a']),
                'group_b_count': len(split_data['group_b']),
                'group_a_sentiment': split_data['group_a_sentiment'],
                'group_b_sentiment': split_data['group_b_sentiment'],
                'feature_name': feature
            }
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(statistics, f, indent=2, ensure_ascii=False)
        
        print(f"  📊 Statistics: {stats_file}")
        
        return statistics
    
    def create_comparative_analysis(self, splits: Dict) -> Dict:
        """比較分析の実行"""
        print(f"\n📈 Comparative Analysis")
        print("-" * 30)
        
        analysis = {}
        
        for feature, split_data in splits.items():
            group_a = split_data['group_a']
            group_b = split_data['group_b']
            
            # レビュー長の比較
            len_a = [len(sample['review_text'].split()) for sample in group_a]
            len_b = [len(sample['review_text'].split()) for sample in group_b]
            
            avg_len_a = sum(len_a) / len(len_a) if len_a else 0
            avg_len_b = sum(len_b) / len(len_b) if len_b else 0
            
            # センチメント比率の比較
            total_a = len(group_a)
            total_b = len(group_b)
            
            pos_ratio_a = split_data['group_a_sentiment'].get('Positive', 0) / total_a if total_a > 0 else 0
            pos_ratio_b = split_data['group_b_sentiment'].get('Positive', 0) / total_b if total_b > 0 else 0
            
            neg_ratio_a = split_data['group_a_sentiment'].get('Negative', 0) / total_a if total_a > 0 else 0
            neg_ratio_b = split_data['group_b_sentiment'].get('Negative', 0) / total_b if total_b > 0 else 0
            
            analysis[feature] = {
                'avg_review_length_a': avg_len_a,
                'avg_review_length_b': avg_len_b,
                'length_difference': avg_len_a - avg_len_b,
                'positive_ratio_a': pos_ratio_a,
                'positive_ratio_b': pos_ratio_b,
                'positive_ratio_difference': pos_ratio_a - pos_ratio_b,
                'negative_ratio_a': neg_ratio_a,
                'negative_ratio_b': neg_ratio_b,
                'negative_ratio_difference': neg_ratio_a - neg_ratio_b
            }
            
            print(f"\n🎯 Feature: {feature}")
            print(f"  📏 Average review length:")
            print(f"    - Group A: {avg_len_a:.1f} words")
            print(f"    - Group B: {avg_len_b:.1f} words")
            print(f"    - Difference: {avg_len_a - avg_len_b:+.1f} words")
            
            print(f"  😊 Positive sentiment ratio:")
            print(f"    - Group A: {pos_ratio_a:.1%}")
            print(f"    - Group B: {pos_ratio_b:.1%}")
            print(f"    - Difference: {pos_ratio_a - pos_ratio_b:+.1%}")
            
            print(f"  😞 Negative sentiment ratio:")
            print(f"    - Group A: {neg_ratio_a:.1%}")
            print(f"    - Group B: {neg_ratio_b:.1%}")
            print(f"    - Difference: {neg_ratio_a - neg_ratio_b:+.1%}")
        
        return analysis
    
    def run_feature_splitting(self, target_features: List[str] = None, output_format: str = 'json'):
        """特徴ベース分割の完全実行"""
        print("=" * 60)
        print("Feature-Based Review Splitting")
        print("=" * 60)
        
        # デフォルトの特徴設定
        if target_features is None:
            target_features = ['food', 'service', 'staff', 'atmosphere']
        
        print(f"🎯 Target features: {target_features}")
        
        # 1. データ読み込み
        samples = self.load_apc_dataset()
        
        # 2. 特徴分析
        feature_analysis = self.analyze_features(samples)
        
        # 3. 特徴ベース分割
        splits = self.create_feature_based_splits(samples, target_features)
        
        # 4. ファイル保存
        statistics = self.save_splits_to_files(splits, output_format)
        
        # 5. 比較分析
        comparative_analysis = self.create_comparative_analysis(splits)
        
        # 6. 最終結果の保存
        final_results = {
            'timestamp': datetime.now().isoformat(),
            'target_features': target_features,
            'feature_analysis': feature_analysis,
            'split_statistics': statistics,
            'comparative_analysis': comparative_analysis,
            'total_samples': len(samples)
        }
        
        results_file = self.results_dir / f"feature_splitting_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 Feature-based splitting completed!")
        print(f"📊 Final results saved to: {results_file}")
        
        return final_results

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Feature-based review splitting")
    parser.add_argument('--features', nargs='+', default=['food', 'service', 'staff', 'atmosphere'],
                       help='Target features for splitting')
    parser.add_argument('--format', choices=['json', 'csv'], default='json',
                       help='Output format')
    parser.add_argument('--dataset-path', type=str, default=None,
                       help='Path to dataset directory')
    
    args = parser.parse_args()
    
    splitter = FeatureBasedSplitter(args.dataset_path)
    results = splitter.run_feature_splitting(args.features, args.format)
    
    print(f"\n📋 Summary:")
    print(f"  - Total samples processed: {results['total_samples']}")
    print(f"  - Features analyzed: {len(results['target_features'])}")
    print(f"  - Output format: {args.format}")

if __name__ == "__main__":
    main() 