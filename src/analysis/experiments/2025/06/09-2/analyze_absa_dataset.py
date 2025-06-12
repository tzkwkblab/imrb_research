#!/usr/bin/env python3
"""
ABSA Dataset Analyzer
ダウンロードしたABSAデータセットの構造を分析し、特徴ベースの分割可能性を検討
"""

import os
import json
from pathlib import Path
from collections import Counter, defaultdict
import pandas as pd
from typing import Dict, List, Tuple, Set

class ABSADatasetAnalyzer:
    def __init__(self):
        self.base_path = Path("data/external/absa-review-dataset/pyabsa-integrated/current/ABSADatasets/datasets")
        self.analysis_results = {}
        
    def analyze_dataset_structure(self):
        """データセット全体の構造を分析"""
        print("=" * 60)
        print("ABSA Dataset Structure Analysis")
        print("=" * 60)
        
        # 各タスクタイプのデータセットを確認
        task_types = ['apc_datasets', 'atepc_datasets', 'aste_datasets', 'acos_datasets']
        
        for task_type in task_types:
            task_path = self.base_path / task_type
            if task_path.exists():
                print(f"\n📁 {task_type.upper()}:")
                datasets = [d.name for d in task_path.iterdir() if d.is_dir()]
                for dataset in sorted(datasets):
                    print(f"  - {dataset}")
                    
        return task_types
    
    def analyze_apc_dataset(self, dataset_name: str = "119.Yelp") -> Dict:
        """APCデータセットの詳細分析"""
        print(f"\n🔍 APC Dataset Analysis: {dataset_name}")
        print("-" * 40)
        
        dataset_path = self.base_path / "apc_datasets" / dataset_name
        if not dataset_path.exists():
            print(f"❌ Dataset not found: {dataset_path}")
            return {}
        
        # ファイル一覧
        files = list(dataset_path.glob("*.txt"))
        train_files = [f for f in files if 'train' in f.name.lower()]
        test_files = [f for f in files if 'test' in f.name.lower()]
        
        print(f"📄 Files found:")
        print(f"  - Training files: {len(train_files)}")
        print(f"  - Test files: {len(test_files)}")
        
        # 主要なトレーニングファイルを分析
        main_train_file = None
        for f in train_files:
            if not any(x in f.name for x in ['augment', 'boost']):
                main_train_file = f
                break
        
        if not main_train_file and train_files:
            main_train_file = train_files[0]
            
        if main_train_file:
            return self._analyze_apc_file(main_train_file)
        
        return {}
    
    def _analyze_apc_file(self, file_path: Path) -> Dict:
        """APCファイルの内容分析"""
        print(f"📖 Analyzing file: {file_path.name}")
        
        aspects = []
        sentiments = []
        review_lengths = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # APCフォーマット: レビューテキスト、アスペクト、センチメントの3行セット
            for i in range(0, len(lines), 3):
                if i + 2 < len(lines):
                    review_text = lines[i].strip()
                    aspect = lines[i + 1].strip()
                    sentiment = lines[i + 2].strip()
                    
                    aspects.append(aspect)
                    sentiments.append(sentiment)
                    review_lengths.append(len(review_text.split()))
        
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return {}
        
        # 統計情報
        aspect_counts = Counter(aspects)
        sentiment_counts = Counter(sentiments)
        
        print(f"📊 Statistics:")
        print(f"  - Total samples: {len(aspects)}")
        print(f"  - Unique aspects: {len(aspect_counts)}")
        print(f"  - Average review length: {sum(review_lengths)/len(review_lengths):.1f} words")
        
        print(f"\n🎯 Top 10 Aspects:")
        for aspect, count in aspect_counts.most_common(10):
            print(f"  - {aspect}: {count}")
        
        print(f"\n😊 Sentiment Distribution:")
        for sentiment, count in sentiment_counts.most_common():
            percentage = count / len(sentiments) * 100
            print(f"  - {sentiment}: {count} ({percentage:.1f}%)")
        
        return {
            'total_samples': len(aspects),
            'unique_aspects': len(aspect_counts),
            'aspect_counts': dict(aspect_counts),
            'sentiment_counts': dict(sentiment_counts),
            'avg_review_length': sum(review_lengths)/len(review_lengths),
            'file_path': str(file_path)
        }
    
    def analyze_atepc_dataset(self, dataset_name: str = "119.Yelp") -> Dict:
        """ATEPCデータセットの詳細分析"""
        print(f"\n🔍 ATEPC Dataset Analysis: {dataset_name}")
        print("-" * 40)
        
        dataset_path = self.base_path / "atepc_datasets" / dataset_name
        if not dataset_path.exists():
            print(f"❌ Dataset not found: {dataset_path}")
            return {}
        
        # ファイル一覧
        files = list(dataset_path.glob("*.atepc"))
        train_files = [f for f in files if 'train' in f.name.lower()]
        test_files = [f for f in files if 'test' in f.name.lower()]
        
        print(f"📄 Files found:")
        print(f"  - Training files: {len(train_files)}")
        print(f"  - Test files: {len(test_files)}")
        
        # 主要なトレーニングファイルを分析
        main_train_file = None
        for f in train_files:
            if not any(x in f.name for x in ['augment', 'boost']):
                main_train_file = f
                break
        
        if not main_train_file and train_files:
            main_train_file = train_files[0]
            
        if main_train_file:
            return self._analyze_atepc_file(main_train_file)
        
        return {}
    
    def _analyze_atepc_file(self, file_path: Path) -> Dict:
        """ATEPCファイルの内容分析"""
        print(f"📖 Analyzing file: {file_path.name}")
        
        sentences = []
        current_sentence = []
        aspect_terms = []
        sentiments = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:  # 空行は文の区切り
                        if current_sentence:
                            sentences.append(current_sentence)
                            current_sentence = []
                        continue
                    
                    parts = line.split()
                    if len(parts) >= 3:
                        word = parts[0]
                        bio_tag = parts[1]
                        sentiment = parts[2]
                        
                        current_sentence.append((word, bio_tag, sentiment))
                        
                        # アスペクト用語の抽出
                        if bio_tag == 'B-ASP':
                            aspect_terms.append(word)
                            if sentiment != '-100':
                                sentiments.append(sentiment)
                
                # 最後の文を追加
                if current_sentence:
                    sentences.append(current_sentence)
        
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return {}
        
        # 統計情報
        aspect_counts = Counter(aspect_terms)
        sentiment_counts = Counter(sentiments)
        sentence_lengths = [len(sent) for sent in sentences]
        
        print(f"📊 Statistics:")
        print(f"  - Total sentences: {len(sentences)}")
        print(f"  - Total aspect terms: {len(aspect_terms)}")
        print(f"  - Unique aspect terms: {len(aspect_counts)}")
        print(f"  - Average sentence length: {sum(sentence_lengths)/len(sentence_lengths):.1f} words")
        
        print(f"\n🎯 Top 10 Aspect Terms:")
        for aspect, count in aspect_counts.most_common(10):
            print(f"  - {aspect}: {count}")
        
        print(f"\n😊 Sentiment Distribution:")
        for sentiment, count in sentiment_counts.most_common():
            percentage = count / len(sentiments) * 100 if sentiments else 0
            print(f"  - {sentiment}: {count} ({percentage:.1f}%)")
        
        return {
            'total_sentences': len(sentences),
            'total_aspect_terms': len(aspect_terms),
            'unique_aspect_terms': len(aspect_counts),
            'aspect_counts': dict(aspect_counts),
            'sentiment_counts': dict(sentiment_counts),
            'avg_sentence_length': sum(sentence_lengths)/len(sentence_lengths) if sentence_lengths else 0,
            'file_path': str(file_path)
        }
    
    def assess_feature_based_splitting(self, apc_analysis: Dict, atepc_analysis: Dict):
        """特徴ベース分割の可能性を評価"""
        print(f"\n🤔 Feature-Based Splitting Assessment")
        print("=" * 50)
        
        # APCデータセットでの評価
        if apc_analysis:
            print(f"📋 APC Dataset Suitability:")
            aspect_counts = apc_analysis.get('aspect_counts', {})
            
            # 頻出アスペクトを特徴として使用可能
            frequent_aspects = {k: v for k, v in aspect_counts.items() if v >= 10}
            print(f"  - Aspects with ≥10 samples: {len(frequent_aspects)}")
            
            # 特徴例の提示
            if frequent_aspects:
                print(f"  - Potential features (top 5):")
                for aspect, count in list(frequent_aspects.items())[:5]:
                    print(f"    * '{aspect}' feature: {count} samples")
        
        # ATEPCデータセットでの評価
        if atepc_analysis:
            print(f"\n📋 ATEPC Dataset Suitability:")
            aspect_counts = atepc_analysis.get('aspect_counts', {})
            
            # 頻出アスペクト用語を特徴として使用可能
            frequent_terms = {k: v for k, v in aspect_counts.items() if v >= 5}
            print(f"  - Aspect terms with ≥5 occurrences: {len(frequent_terms)}")
            
            # 特徴例の提示
            if frequent_terms:
                print(f"  - Potential features (top 5):")
                for term, count in list(frequent_terms.items())[:5]:
                    print(f"    * '{term}' feature: {count} occurrences")
        
        # 推奨事項
        print(f"\n💡 Recommendations:")
        print(f"  ✅ Both APC and ATEPC datasets are suitable for feature-based splitting")
        print(f"  ✅ APC format is simpler and better for aspect-level analysis")
        print(f"  ✅ ATEPC format provides word-level annotations for detailed analysis")
        print(f"  📝 Suggested approach: Use APC dataset for initial experiments")
        
        return True
    
    def create_tree_structure(self):
        """データセットのツリー構造を表示"""
        print(f"\n🌳 Dataset Tree Structure:")
        print("=" * 40)
        
        def print_tree(path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0):
            if current_depth >= max_depth:
                return
                
            items = sorted([item for item in path.iterdir() if item.is_dir() or item.suffix in ['.txt', '.atepc', '.seg']])
            
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                print(f"{prefix}{current_prefix}{item.name}")
                
                if item.is_dir() and current_depth < max_depth - 1:
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    print_tree(item, next_prefix, max_depth, current_depth + 1)
        
        print_tree(self.base_path)
    
    def run_analysis(self):
        """完全な分析を実行"""
        # 1. 構造分析
        self.analyze_dataset_structure()
        
        # 2. ツリー構造表示
        self.create_tree_structure()
        
        # 3. 詳細分析
        apc_analysis = self.analyze_apc_dataset("119.Yelp")
        atepc_analysis = self.analyze_atepc_dataset("119.Yelp")
        
        # 4. 特徴ベース分割の評価
        self.assess_feature_based_splitting(apc_analysis, atepc_analysis)
        
        # 5. 結果の保存
        self.save_analysis_results(apc_analysis, atepc_analysis)
        
        return apc_analysis, atepc_analysis
    
    def save_analysis_results(self, apc_analysis: Dict, atepc_analysis: Dict):
        """分析結果をJSONファイルに保存"""
        results = {
            'analysis_date': pd.Timestamp.now().isoformat(),
            'apc_analysis': apc_analysis,
            'atepc_analysis': atepc_analysis,
            'dataset_path': str(self.base_path)
        }
        
        output_file = Path("src/analysis/experiments/2025/06/09-2/absa_dataset_analysis.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Analysis results saved to: {output_file}")

def main():
    """メイン関数"""
    analyzer = ABSADatasetAnalyzer()
    apc_analysis, atepc_analysis = analyzer.run_analysis()
    
    print(f"\n🎉 Analysis completed!")
    print(f"📊 Summary:")
    if apc_analysis:
        print(f"  - APC samples: {apc_analysis.get('total_samples', 0)}")
        print(f"  - APC unique aspects: {apc_analysis.get('unique_aspects', 0)}")
    if atepc_analysis:
        print(f"  - ATEPC sentences: {atepc_analysis.get('total_sentences', 0)}")
        print(f"  - ATEPC aspect terms: {atepc_analysis.get('total_aspect_terms', 0)}")

if __name__ == "__main__":
    main() 