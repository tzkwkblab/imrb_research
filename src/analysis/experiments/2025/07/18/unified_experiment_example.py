#!/usr/bin/env python3
"""
統一データセット管理インターフェース実験例

DatasetManagerを使った簡潔な実験実装例
各データセットを統一的に扱い、最小限のコードで実験実行
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Utils統合
utils_dir = Path(__file__).parent.parent.parent.parent / "utils"
sys.path.append(str(utils_dir))

from dataset_manager import DatasetManager
from contrast_factor_analyzer import ContrastFactorAnalyzer


class UnifiedExperimentExample:
    """統一インターフェース使用の実験例"""
    
    def __init__(self):
        """初期化"""
        self.dataset_manager = DatasetManager()
        self.analyzer = ContrastFactorAnalyzer(debug=True)  # デバッグモード有効
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        print("📊 統一実験インターフェース初期化完了")
    
    def demo_quick_experiment(self):
        """1行で実験実行デモ"""
        print("\n🚀 クイック実験デモ")
        print("=" * 50)
        
        # 利用可能データセット確認
        datasets = self.dataset_manager.list_available_datasets()
        print(f"📊 利用可能データセット: {list(datasets.keys())}")
        
        # 各データセットで簡単な実験
        results = []
        
        for dataset_id in ["steam", "semeval"]:  # 実際に利用可能なデータセットのみ
            print(f"\n🔍 {dataset_id}データセット実験")
            
            try:
                # 実験設定を取得
                config = self.dataset_manager.get_experiment_config(dataset_id)
                print(f"  利用可能アスペクト: {config['aspects'][:3]}...")  # 最初の3つのみ表示
                
                # 最初のアスペクトで実験
                first_aspect = config['aspects'][0]
                print(f"  🎯 {first_aspect}アスペクトで実験実行")
                
                # 1行でデータ分割取得
                if dataset_id == "steam":
                    splits = self.dataset_manager.get_binary_splits(
                        dataset_id, aspect=first_aspect, group_size=50, split_type="binary_label"
                    )
                else:
                    splits = self.dataset_manager.get_binary_splits(
                        dataset_id, aspect=first_aspect, group_size=50, split_type="aspect_vs_others"
                    )
                
                # Few-shot例題取得
                examples = self.dataset_manager.create_examples(dataset_id, first_aspect, shot_count=1)
                
                print(f"    データ分割: A={len(splits.group_a)}, B={len(splits.group_b)}")
                print(f"    例題数: {len(examples)}")
                print(f"    正解文: {splits.correct_answer}")  # 正解文表示
                
                # 対比因子分析実行
                result = self.analyzer.analyze(
                    group_a=splits.group_a,
                    group_b=splits.group_b,
                    correct_answer=splits.correct_answer,
                    examples=examples,
                    output_dir=str(self.results_dir)
                )
                
                # メタデータ追加
                if result:
                    result.update(splits.metadata)
                    result['examples_count'] = len(examples)
                    results.append(result)
                    
                    # 詳細な結果表示
                    bert_score = result.get('evaluation', {}).get('bert_score', 0)
                    bleu_score = result.get('evaluation', {}).get('bleu_score', 0)
                    llm_response = result.get('process', {}).get('llm_response', 'N/A')
                    print(f"    LLM応答: {llm_response}")
                    print(f"    ✅ BERT: {bert_score:.6f}")
                    print(f"    ✅ BLEU: {bleu_score:.6f}")
                else:
                    print(f"    ❌ 実験失敗")
                    
            except Exception as e:
                print(f"    ❌ エラー: {e}")
                import traceback
                traceback.print_exc()  # 詳細なエラー情報
        
        return results
    
    def demo_multi_aspect_experiment(self, dataset_id: str = "steam", max_aspects: int = 3):
        """複数アスペクト実験デモ"""
        print(f"\n🎮 {dataset_id}複数アスペクト実験デモ")
        print("=" * 50)
        
        try:
            # 実験設定取得
            config = self.dataset_manager.get_experiment_config(dataset_id)
            aspects = config['aspects'][:max_aspects]  # 最初のN個のアスペクト
            
            print(f"対象アスペクト: {aspects}")
            print(f"予想実験数: {len(aspects)} × {len(config['shot_settings'])} = {len(aspects) * len(config['shot_settings'])}")
            
            all_results = []
            
            for aspect in aspects:
                for shot_count in config['shot_settings']:
                    print(f"  🎯 {aspect} - {shot_count}shot")
                    
                    # データ分割取得
                    split_type = "binary_label" if dataset_id == "steam" else "aspect_vs_others"
                    splits = self.dataset_manager.get_binary_splits(
                        dataset_id, aspect=aspect, group_size=30, split_type=split_type  # 小さなサイズでテスト
                    )
                    
                    # Few-shot例題取得
                    examples = self.dataset_manager.create_examples(dataset_id, aspect, shot_count)
                    
                    # 実験実行
                    result = self.analyzer.analyze(
                        group_a=splits.group_a,
                        group_b=splits.group_b,
                        correct_answer=splits.correct_answer,
                        examples=examples,
                        output_dir=str(self.results_dir),
                        experiment_name=f"{dataset_id}_{aspect}_{shot_count}shot"
                    )
                    
                    # 結果記録
                    if result:
                        result.update(splits.metadata)
                        result['shot_count'] = shot_count
                        all_results.append(result)
                        
                        bert_score = result.get('evaluation', {}).get('bert_score', 0)
                        print(f"    ✅ BERT: {bert_score:.3f}")
                    else:
                        print(f"    ❌ 失敗")
            
            # 結果保存
            if all_results:
                self._save_experiment_results(all_results, f"{dataset_id}_multi_aspect")
                print(f"\n📈 実験完了: {len(all_results)}結果")
            
            return all_results
            
        except Exception as e:
            print(f"❌ エラー: {e}")
            return []
    
    def demo_cross_dataset_comparison(self):
        """クロスデータセット比較デモ"""
        print(f"\n🔄 クロスデータセット比較デモ")
        print("=" * 50)
        
        # 共通アスペクトでの比較（価格関連）
        comparison_configs = [
            {"dataset": "steam", "aspect": "price", "split_type": "binary_label"},
            {"dataset": "semeval", "aspect": "price", "split_type": "aspect_vs_others"},
            {"dataset": "amazon", "aspect": "price", "split_type": "aspect_vs_others"}
        ]
        
        comparison_results = []
        
        for config in comparison_configs:
            dataset_id = config["dataset"]
            aspect = config["aspect"]
            split_type = config["split_type"]
            
            print(f"  🎯 {dataset_id} - {aspect}")
            
            try:
                # データ分割取得
                splits = self.dataset_manager.get_binary_splits(
                    dataset_id, aspect=aspect, group_size=50, split_type=split_type
                )
                
                # 1-shot例題
                examples = self.dataset_manager.create_examples(dataset_id, aspect, shot_count=1)
                
                # 実験実行
                result = self.analyzer.analyze(
                    group_a=splits.group_a,
                    group_b=splits.group_b,
                    correct_answer=splits.correct_answer,
                    examples=examples,
                    output_dir=str(self.results_dir),
                    experiment_name=f"cross_{dataset_id}_{aspect}"
                )
                
                if result:
                    result.update(splits.metadata)
                    result['comparison_type'] = 'cross_dataset_price'
                    comparison_results.append(result)
                    
                    bert_score = result.get('evaluation', {}).get('bert_score', 0)
                    bleu_score = result.get('evaluation', {}).get('bleu_score', 0)
                    print(f"    ✅ BERT: {bert_score:.3f}, BLEU: {bleu_score:.3f}")
                else:
                    print(f"    ❌ 失敗")
                    
            except Exception as e:
                print(f"    ❌ エラー: {e}")
        
        # 比較結果保存
        if comparison_results:
            self._save_experiment_results(comparison_results, "cross_dataset_comparison")
            
            # 簡単な比較分析
            print(f"\n📊 クロスデータセット比較結果:")
            print("| データセット | BERTスコア | BLEUスコア |")
            print("|------------|-----------|----------|")
            for result in comparison_results:
                dataset = result.get('dataset_id', 'N/A')
                bert = result.get('bert_score', 0)
                bleu = result.get('bleu_score', 0)
                print(f"| {dataset} | {bert:.3f} | {bleu:.3f} |")
        
        return comparison_results
    
    def _save_experiment_results(self, results, experiment_name):
        """実験結果保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{experiment_name}_results_{timestamp}.json"
        output_path = self.results_dir / filename
        
        summary = {
            "experiment_name": experiment_name,
            "timestamp": timestamp,
            "total_experiments": len(results),
            "results": results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"💾 結果保存: {filename}")
    
    def run_all_demos(self):
        """全デモ実行"""
        print("🎪 統一インターフェース全デモ実行")
        print("=" * 60)
        
        # デモ1: クイック実験
        quick_results = self.demo_quick_experiment()
        
        # デモ2: 複数アスペクト実験
        multi_results = self.demo_multi_aspect_experiment("steam", max_aspects=2)
        
        # デモ3: クロスデータセット比較
        cross_results = self.demo_cross_dataset_comparison()
        
        # 総合結果
        total_experiments = len(quick_results) + len(multi_results) + len(cross_results)
        print(f"\n🎉 全デモ完了!")
        print(f"総実験数: {total_experiments}")
        print(f"結果ディレクトリ: {self.results_dir}")
        
        return {
            "quick_results": quick_results,
            "multi_results": multi_results,
            "cross_results": cross_results
        }


def main():
    """メイン関数"""
    print("🚀 統一データセット管理インターフェース デモ")
    
    experiment = UnifiedExperimentExample()
    results = experiment.run_all_demos()
    
    return results


if __name__ == "__main__":
    main() 