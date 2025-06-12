#!/usr/bin/env python3
"""
Domain-Aware Feature-Based Review Splitter
ドメインごとにABSAデータセットから特定の特徴を含むレビュー群と含まないレビュー群を作成
"""

import os
import json
import pandas as pd
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set, Optional
import argparse
from datetime import datetime
import glob

class DomainAwareFeatureSplitter:
    def __init__(self, dataset_path: str = None):
        if dataset_path is None:
            self.dataset_path = Path("data/external/absa-review-dataset/pyabsa-integrated/current/ABSADatasets/datasets")
        else:
            self.dataset_path = Path(dataset_path)
        
        self.results_dir = Path("src/analysis/experiments/2025/06/09-2/domain_results")
        self.results_dir.mkdir(exist_ok=True)
        
        # ドメインマッピング（ディレクトリ名 -> ドメイン名）
        self.domain_mapping = {
            'restaurant14': 'restaurant',
            'restaurant15': 'restaurant', 
            'restaurant16': 'restaurant',
            'laptop14': 'laptop',
            'laptop15': 'laptop',
            'laptop16': 'laptop',
            'yelp': 'restaurant',  # Yelpはレストランとして扱う
            'arts_laptop14': 'laptop',
            'arts_restaurant14': 'restaurant'
        }
        
        # ドメインごとの推奨特徴
        self.domain_features = {
            'restaurant': ['food', 'service', 'staff', 'atmosphere', 'menu', 'price', 'ambience', 'location'],
            'laptop': ['battery', 'screen', 'keyboard', 'performance', 'price', 'design', 'portability', 'software'],
            'television': ['picture', 'sound', 'remote', 'price', 'size', 'connectivity', 'interface'],
            'car': ['comfort', 'performance', 'price', 'safety', 'design', 'fuel'],
            'camera': ['image quality', 'zoom', 'battery', 'price', 'design', 'interface']
        }
    
    def discover_domains(self) -> Dict[str, List[Path]]:
        """利用可能なドメインとそのデータファイルを自動発見"""
        print("🔍 Discovering available domains...")
        
        domains = defaultdict(list)
        
        # APCデータセットの探索
        apc_path = self.dataset_path / "apc_datasets"
        if apc_path.exists():
            for dataset_dir in apc_path.iterdir():
                if dataset_dir.is_dir():
                    # SemEvalのような構造（サブディレクトリあり）
                    for subdomain_dir in dataset_dir.iterdir():
                        if subdomain_dir.is_dir():
                            domain_name = self._extract_domain_name(subdomain_dir.name)
                            data_files = self._find_data_files(subdomain_dir)
                            if data_files:
                                domains[domain_name].extend(data_files)
                    
                    # Yelpのような構造（直接ファイル）
                    data_files = self._find_data_files(dataset_dir)
                    if data_files:
                        domain_name = self._extract_domain_name(dataset_dir.name)
                        domains[domain_name].extend(data_files)
        
        print(f"📊 Found {len(domains)} domains:")
        for domain, files in domains.items():
            print(f"  - {domain}: {len(files)} data files")
        
        return domains
    
    def _extract_domain_name(self, dir_name: str) -> str:
        """ディレクトリ名からドメイン名を抽出"""
        dir_lower = dir_name.lower()
        
        # 直接マッピングのチェック
        for key, domain in self.domain_mapping.items():
            if key in dir_lower:
                return domain
        
        # 部分マッチングでの推定
        if 'restaurant' in dir_lower or 'yelp' in dir_lower:
            return 'restaurant'
        elif 'laptop' in dir_lower:
            return 'laptop'
        elif 'television' in dir_lower or 'tv' in dir_lower:
            return 'television'
        elif 'car' in dir_lower:
            return 'car'
        elif 'camera' in dir_lower:
            return 'camera'
        else:
            return 'unknown'
    
    def _find_data_files(self, directory: Path) -> List[Path]:
        """ディレクトリ内のデータファイルを検索"""
        data_files = []
        
        # 一般的なファイルパターン
        patterns = [
            "*.train.txt", "*.test.txt", "*.dev.txt",
            "*Train*.seg", "*Test*.seg", "*Dev*.seg",
            "*.xml.seg", "*.txt.atepc"
        ]
        
        for pattern in patterns:
            files = list(directory.glob(pattern))
            data_files.extend(files)
        
        return data_files
    
    def load_domain_data(self, domain_files: List[Path]) -> List[Dict]:
        """ドメインのデータファイルを読み込み"""
        samples = []
        
        for file_path in domain_files:
            print(f"📖 Loading: {file_path.name}")
            
            try:
                if file_path.suffix == '.seg' or 'xml.seg' in file_path.name:
                    # SemEval形式（3行セット）
                    samples.extend(self._load_apc_format(file_path))
                elif file_path.suffix == '.txt' and 'yelp' in str(file_path):
                    # Yelp形式（3行セット）
                    samples.extend(self._load_apc_format(file_path))
                elif '.atepc' in file_path.name:
                    # ATEPC形式（BIOタグ）
                    samples.extend(self._load_atepc_format(file_path))
                else:
                    print(f"⚠️ Unknown format: {file_path}")
                    
            except Exception as e:
                print(f"❌ Error loading {file_path}: {e}")
        
        print(f"✅ Loaded {len(samples)} samples for domain")
        return samples
    
    def _load_apc_format(self, file_path: Path) -> List[Dict]:
        """APC形式（3行セット）のデータを読み込み"""
        samples = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
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
                    'sample_id': len(samples),
                    'format': 'apc'
                })
        
        return samples
    
    def _load_atepc_format(self, file_path: Path) -> List[Dict]:
        """ATEPC形式（BIOタグ）のデータを読み込み"""
        samples = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_sentence = []
        current_aspects = []
        current_sentiments = []
        
        for line in lines:
            line = line.strip()
            if not line:  # 空行で文の区切り
                if current_sentence:
                    # 文とアスペクトの組み合わせを作成
                    sentence_text = " ".join(current_sentence)
                    aspects = list(set(current_aspects))  # 重複除去
                    sentiments = list(set(current_sentiments))  # 重複除去
                    
                    for aspect in aspects:
                        for sentiment in sentiments:
                            if sentiment != '-100':
                                samples.append({
                                    'review_text': sentence_text,
                                    'aspect': aspect,
                                    'sentiment': sentiment,
                                    'source_file': file_path.name,
                                    'sample_id': len(samples),
                                    'format': 'atepc'
                                })
                    
                    current_sentence = []
                    current_aspects = []
                    current_sentiments = []
            else:
                parts = line.split('\t')
                if len(parts) >= 3:
                    word = parts[0]
                    bio_tag = parts[1]
                    sentiment = parts[2]
                    
                    current_sentence.append(word)
                    if bio_tag.startswith('B-'):
                        current_aspects.append(bio_tag[2:])
                    if sentiment != '-100':
                        current_sentiments.append(sentiment)
        
        return samples
    
    def analyze_domain_features(self, domain: str, samples: List[Dict]) -> Dict:
        """ドメイン内の特徴（アスペクト）を分析"""
        print(f"\n🔍 Feature Analysis for {domain.upper()} domain")
        print("-" * 40)
        
        aspect_counts = Counter([sample['aspect'] for sample in samples])
        sentiment_by_aspect = defaultdict(list)
        
        for sample in samples:
            sentiment_by_aspect[sample['aspect']].append(sample['sentiment'])
        
        # 頻出アスペクトの特徴分析（最低5件以上）
        frequent_aspects = {k: v for k, v in aspect_counts.items() if v >= 5}
        
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
        print(f"📊 Frequent Aspects in {domain} (≥5 samples):")
        for aspect, analysis in sorted(feature_analysis.items(), key=lambda x: x[1]['total_count'], reverse=True):
            print(f"  - {aspect}: {analysis['total_count']} samples")
            print(f"    Pos: {analysis['positive_ratio']:.1%}, Neg: {analysis['negative_ratio']:.1%}, Neu: {analysis['neutral_ratio']:.1%}")
        
        return feature_analysis
    
    def create_domain_feature_splits(self, domain: str, samples: List[Dict], target_features: List[str]) -> Dict:
        """ドメイン内で特徴ベースでデータを分割"""
        print(f"\n✂️ Creating Feature-Based Splits for {domain.upper()} domain")
        print("-" * 50)
        
        splits = {}
        available_aspects = set([sample['aspect'].lower() for sample in samples])
        
        for feature in target_features:
            feature_lower = feature.lower()
            
            # 厳密マッチまたは部分マッチで検索
            matching_aspects = [asp for asp in available_aspects if feature_lower in asp.lower() or asp.lower() in feature_lower]
            
            if not matching_aspects:
                print(f"⚠️ Feature '{feature}' not found in {domain} domain, skipping...")
                continue
            
            print(f"\n🎯 Processing feature: '{feature}' (matching: {matching_aspects})")
            
            # 特徴を含むグループ（Group A）
            group_a = [sample for sample in samples if any(match in sample['aspect'].lower() for match in matching_aspects)]
            
            # 特徴を含まないグループ（Group B）
            group_b = [sample for sample in samples if not any(match in sample['aspect'].lower() for match in matching_aspects)]
            
            print(f"  📊 Group A (contains '{feature}'): {len(group_a)} samples")
            print(f"  📊 Group B (does not contain '{feature}'): {len(group_b)} samples")
            
            if len(group_a) == 0:
                print(f"⚠️ No samples found for feature '{feature}' in {domain}, skipping...")
                continue
            
            # センチメント分布の確認
            sentiment_a = Counter([s['sentiment'] for s in group_a])
            sentiment_b = Counter([s['sentiment'] for s in group_b])
            
            print(f"  😊 Group A sentiment: {dict(sentiment_a)}")
            print(f"  😊 Group B sentiment: {dict(sentiment_b)}")
            
            splits[feature] = {
                'domain': domain,
                'group_a': group_a,
                'group_b': group_b,
                'group_a_sentiment': dict(sentiment_a),
                'group_b_sentiment': dict(sentiment_b),
                'feature_name': feature,
                'matching_aspects': matching_aspects
            }
        
        return splits
    
    def save_domain_splits_to_files(self, domain: str, splits: Dict, output_format: str = 'json'):
        """ドメインごとの分割結果をファイルに保存"""
        print(f"\n💾 Saving {domain} domain splits to files")
        print("-" * 40)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain_dir = self.results_dir / domain
        domain_dir.mkdir(exist_ok=True)
        
        for feature, split_data in splits.items():
            feature_safe = feature.replace(' ', '_').replace('/', '_')
            
            # Group A の保存
            group_a_file = domain_dir / f"group_a_{feature_safe}_{timestamp}.{output_format}"
            group_b_file = domain_dir / f"group_b_{feature_safe}_{timestamp}.{output_format}"
            
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
        
        # ドメイン別統計の保存
        domain_stats_file = domain_dir / f"domain_statistics_{timestamp}.json"
        statistics = {
            'domain': domain,
            'timestamp': timestamp,
            'features': {}
        }
        
        for feature, split_data in splits.items():
            statistics['features'][feature] = {
                'group_a_count': len(split_data['group_a']),
                'group_b_count': len(split_data['group_b']),
                'group_a_sentiment': split_data['group_a_sentiment'],
                'group_b_sentiment': split_data['group_b_sentiment'],
                'feature_name': feature,
                'matching_aspects': split_data['matching_aspects']
            }
        
        with open(domain_stats_file, 'w', encoding='utf-8') as f:
            json.dump(statistics, f, indent=2, ensure_ascii=False)
        
        print(f"  📊 Domain Statistics: {domain_stats_file}")
        
        return statistics
    
    def create_domain_comparative_analysis(self, domain: str, splits: Dict) -> Dict:
        """ドメイン内での比較分析"""
        print(f"\n📈 Comparative Analysis for {domain.upper()} domain")
        print("-" * 50)
        
        analysis = {'domain': domain, 'features': {}}
        
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
            
            analysis['features'][feature] = {
                'avg_review_length_a': avg_len_a,
                'avg_review_length_b': avg_len_b,
                'length_difference': avg_len_a - avg_len_b,
                'positive_ratio_a': pos_ratio_a,
                'positive_ratio_b': pos_ratio_b,
                'positive_ratio_difference': pos_ratio_a - pos_ratio_b,
                'negative_ratio_a': neg_ratio_a,
                'negative_ratio_b': neg_ratio_b,
                'negative_ratio_difference': neg_ratio_a - neg_ratio_b,
                'sample_count_a': total_a,
                'sample_count_b': total_b,
                'balance_ratio': total_a / (total_a + total_b) if (total_a + total_b) > 0 else 0
            }
            
            print(f"\n🎯 Feature: {feature}")
            print(f"  📏 Average review length:")
            print(f"    - Group A: {avg_len_a:.1f} words")
            print(f"    - Group B: {avg_len_b:.1f} words")
            print(f"    - Difference: {avg_len_a - avg_len_b:+.1f} words")
            
            print(f"  📊 Sample balance:")
            print(f"    - Group A: {total_a} samples ({total_a/(total_a+total_b):.1%})")
            print(f"    - Group B: {total_b} samples ({total_b/(total_a+total_b):.1%})")
            
            print(f"  😊 Positive sentiment ratio:")
            print(f"    - Group A: {pos_ratio_a:.1%}")
            print(f"    - Group B: {pos_ratio_b:.1%}")
            print(f"    - Difference: {pos_ratio_a - pos_ratio_b:+.1%}")
        
        return analysis
    
    def run_domain_aware_splitting(self, target_domains: List[str] = None, target_features: Dict[str, List[str]] = None, output_format: str = 'json'):
        """ドメイン対応特徴ベース分割の完全実行"""
        print("=" * 70)
        print("Domain-Aware Feature-Based Review Splitting")
        print("=" * 70)
        
        # 1. ドメインとデータファイルの自動発見
        available_domains = self.discover_domains()
        
        # 対象ドメインの決定
        if target_domains is None:
            target_domains = list(available_domains.keys())
        else:
            # 指定されたドメインが利用可能かチェック
            target_domains = [d for d in target_domains if d in available_domains]
        
        print(f"\n🎯 Target domains: {target_domains}")
        
        # 特徴の決定
        if target_features is None:
            target_features = {domain: self.domain_features.get(domain, ['service', 'quality', 'price']) 
                              for domain in target_domains}
        
        all_results = {}
        
        # 2. ドメインごとの処理
        for domain in target_domains:
            if domain not in available_domains:
                print(f"⚠️ Domain '{domain}' not found, skipping...")
                continue
            
            print(f"\n{'='*20} Processing {domain.upper()} Domain {'='*20}")
            
            # 2.1. ドメインデータの読み込み
            domain_files = available_domains[domain]
            samples = self.load_domain_data(domain_files)
            
            if not samples:
                print(f"⚠️ No samples loaded for {domain}, skipping...")
                continue
            
            # 2.2. ドメイン内特徴分析
            feature_analysis = self.analyze_domain_features(domain, samples)
            
            # 2.3. 特徴ベース分割
            domain_features = target_features.get(domain, [])
            splits = self.create_domain_feature_splits(domain, samples, domain_features)
            
            if not splits:
                print(f"⚠️ No valid splits created for {domain}, skipping...")
                continue
            
            # 2.4. ファイル保存
            statistics = self.save_domain_splits_to_files(domain, splits, output_format)
            
            # 2.5. 比較分析
            comparative_analysis = self.create_domain_comparative_analysis(domain, splits)
            
            # 2.6. ドメイン結果の記録
            all_results[domain] = {
                'domain': domain,
                'total_samples': len(samples),
                'feature_analysis': feature_analysis,
                'split_statistics': statistics,
                'comparative_analysis': comparative_analysis,
                'target_features': domain_features
            }
        
        # 3. 全体結果の保存
        final_results = {
            'timestamp': datetime.now().isoformat(),
            'target_domains': target_domains,
            'target_features': target_features,
            'domain_results': all_results,
            'summary': {
                'total_domains_processed': len(all_results),
                'total_samples_across_domains': sum(r['total_samples'] for r in all_results.values())
            }
        }
        
        final_results_file = self.results_dir / f"domain_aware_splitting_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(final_results_file, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 Domain-aware feature-based splitting completed!")
        print(f"📊 Final results saved to: {final_results_file}")
        print(f"\n📋 Summary:")
        print(f"  - Domains processed: {len(all_results)}")
        print(f"  - Total samples: {sum(r['total_samples'] for r in all_results.values())}")
        
        return final_results

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Domain-aware feature-based review splitting")
    parser.add_argument('--domains', nargs='+', default=None,
                       help='Target domains (e.g., restaurant laptop)')
    parser.add_argument('--restaurant-features', nargs='+', 
                       default=['food', 'service', 'staff', 'atmosphere'],
                       help='Features for restaurant domain')
    parser.add_argument('--laptop-features', nargs='+',
                       default=['battery', 'screen', 'keyboard', 'performance'],
                       help='Features for laptop domain')
    parser.add_argument('--format', choices=['json', 'csv'], default='json',
                       help='Output format')
    parser.add_argument('--dataset-path', type=str, default=None,
                       help='Path to dataset directory')
    
    args = parser.parse_args()
    
    # 特徴の設定
    target_features = {}
    if 'restaurant' in (args.domains or []):
        target_features['restaurant'] = args.restaurant_features
    if 'laptop' in (args.domains or []):
        target_features['laptop'] = args.laptop_features
    
    splitter = DomainAwareFeatureSplitter(args.dataset_path)
    results = splitter.run_domain_aware_splitting(args.domains, target_features, args.format)
    
    # 結果サマリー表示
    for domain, domain_results in results['domain_results'].items():
        print(f"\n📊 {domain.upper()} Domain Summary:")
        print(f"  - Total samples: {domain_results['total_samples']}")
        print(f"  - Features processed: {len(domain_results['target_features'])}")
        for feature in domain_results['target_features']:
            if feature in domain_results['split_statistics']['features']:
                stats = domain_results['split_statistics']['features'][feature]
                print(f"    • {feature}: A={stats['group_a_count']}, B={stats['group_b_count']}")

if __name__ == "__main__":
    main() 