#!/usr/bin/env python3
"""
Steam Review Dataset 二項対比因子抽出実験

特定アスペクトを含むレビュー vs 含まないレビューでの対比因子抽出とスコア評価
例: "gameplay"を含むレビュー vs "gameplay"を含まないレビュー → 正解: "gameplay"
"""

import os
import sys
import json
import random
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
import logging

# ディレクトリ設定
current_dir = Path(__file__).parent
experiments_dir = current_dir.parent.parent.parent
utils_dir = experiments_dir / "utils"
sys.path.append(str(utils_dir))
sys.path.append(str(utils_dir / "LLM"))

# 必要なモジュールをインポート
from contrast_factor_analyzer import ContrastFactorAnalyzer

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 環境変数設定
from dotenv import load_dotenv
load_dotenv()

class SteamBinaryContrastExperiment:
    """Steam二項対比因子抽出実験クラス"""
    
    def __init__(self, dataset_path: str = None):
        """
        初期化
        Args:
            dataset_path: データセットのパス
        """
        if dataset_path is None:
            dataset_path = "/Users/seinoshun/imrb_research/data/external/steam-review-aspect-dataset/current"
        
        self.dataset_path = Path(dataset_path)
        self.results_dir = current_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Steam アスペクト設定
        self.aspects = [
            'recommended', 'story', 'gameplay', 'visual', 
            'audio', 'technical', 'price', 'suggestion'
        ]
        
        self.shot_counts = [0, 1, 3]
        self.target_group_size = 50  # コンテキスト長制限対応
        self.random_seed = 42
        
        # アナライザー初期化
        self.analyzer = ContrastFactorAnalyzer()
        
        # ランダムシード設定
        random.seed(self.random_seed)
        
        logger.info("Steam二項対比因子抽出実験を初期化")
    
    def load_steam_data(self) -> pd.DataFrame:
        """Steam Review Datasetを読み込み"""
        train_path = self.dataset_path / "train.csv"
        test_path = self.dataset_path / "test.csv"
        
        logger.info(f"データ読み込み: {train_path}")
        
        if not train_path.exists() or not test_path.exists():
            raise FileNotFoundError(f"Steamデータセットが見つかりません: {self.dataset_path}")
        
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)
        
        # 訓練データとテストデータを結合
        full_df = pd.concat([train_df, test_df], ignore_index=True)
        logger.info(f"総データ数: {len(full_df)}件")
        
        return full_df
    
    def create_binary_splits(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """
        各アスペクトで二項分割を作成
        Args:
            df: Steamレビューデータ
        Returns:
            アスペクト別分割データ
        """
        logger.info("アスペクト別二項グループ分割を開始...")
        
        splits = {}
        
        for aspect in self.aspects:
            aspect_col = f'label_{aspect}'
            
            if aspect_col not in df.columns:
                logger.warning(f"カラム'{aspect_col}'が見つかりません。スキップします。")
                continue
            
            # グループA（アスペクト該当）とグループB（非該当）を分割
            group_a = df[df[aspect_col] == 1].copy()
            group_b = df[df[aspect_col] == 0].copy()
            
            logger.info(f"{aspect}: A={len(group_a)}, B={len(group_b)}")
            
            # 最小データ数チェック
            if len(group_a) < 50 or len(group_b) < 50:
                logger.warning(f"{aspect}でデータ数が不足。A: {len(group_a)}, B: {len(group_b)}")
                continue
            
            # サンプル数調整
            adjusted_group_a = self._adjust_sample_size(group_a, self.target_group_size)
            adjusted_group_b = self._adjust_sample_size(group_b, self.target_group_size)
            
            splits[aspect] = {
                'aspect': aspect,
                'group_a': adjusted_group_a,
                'group_b': adjusted_group_b,
                'group_a_size': len(adjusted_group_a),
                'group_b_size': len(adjusted_group_b),
                'ground_truth': aspect
            }
            
            logger.info(f"✅ {aspect}: A={len(adjusted_group_a)}, B={len(adjusted_group_b)}")
        
        return splits
    
    def _adjust_sample_size(self, samples: pd.DataFrame, target_size: int) -> pd.DataFrame:
        """サンプル数を目標サイズに調整"""
        if len(samples) >= target_size:
            return samples.sample(n=target_size, random_state=self.random_seed)
        else:
            # 重複サンプリングで補完
            additional_needed = target_size - len(samples)
            if additional_needed > 0:
                additional = samples.sample(n=additional_needed, replace=True, random_state=self.random_seed)
                return pd.concat([samples, additional], ignore_index=True)
            return samples
    
    def format_group_for_analysis(self, group_df: pd.DataFrame) -> List[str]:
        """DataFrameをcontrastAnalyzer用のリスト形式に変換"""
        return group_df['review'].tolist()
    
    def _create_examples(self, shot_count: int, aspect: str) -> List[Dict]:
        """Few-shot用例題を作成"""
        # Steamアスペクト用の簡単な例題
        steam_examples = {
            'recommended': {
                'group_a': ["I highly recommend this game!", "This is a must-buy game"],
                'group_b': ["The story was confusing", "Graphics are outdated"],
                'answer': "recommendation expressions"
            },
            'gameplay': {
                'group_a': ["The gameplay is amazing", "Great mechanics and controls"],
                'group_b': ["Beautiful graphics", "Great soundtrack"],
                'answer': "gameplay mechanics"
            },
            'story': {
                'group_a': ["Amazing storyline", "The plot is engaging"],
                'group_b': ["Good graphics", "Nice sound effects"],
                'answer': "story and narrative"
            }
        }
        
        # デフォルト例題
        default_example = {
            'group_a': ["Positive aspect example", "Another positive example"],
            'group_b': ["Different aspect example", "Another different example"],
            'answer': aspect
        }
        
        base_example = steam_examples.get(aspect, default_example)
        
        # shot_countに基づいて例題数を調整
        examples = []
        for i in range(shot_count):
            example = {
                'group_a': base_example['group_a'],
                'group_b': base_example['group_b'],
                'answer': base_example['answer']
            }
            examples.append(example)
        
        return examples
    
    def run_binary_contrast_experiments(self, splits: Dict[str, Dict]) -> List[Dict]:
        """
        二項対比因子抽出実験を実行
        Args:
            splits: アスペクト別分割データ
        Returns:
            実験結果リスト
        """
        logger.info("二項対比因子抽出実験を開始...")
        
        all_results = []
        experiment_count = 0
        
        for aspect, split_data in splits.items():
            logger.info(f"アスペクト: {aspect}")
            
            # グループデータをフォーマット
            group_a_texts = self.format_group_for_analysis(split_data['group_a'])
            group_b_texts = self.format_group_for_analysis(split_data['group_b'])
            correct_answer = split_data['ground_truth']
            
            for shot_count in self.shot_counts:
                experiment_count += 1
                logger.info(f"  実験 {experiment_count}: {shot_count}-shot設定")
                
                try:
                    # Few-shot用例題準備
                    examples = self._create_examples(shot_count, aspect) if shot_count > 0 else None
                    
                    # contrast_factor_analyzerを使用して実験実行
                    result = self.analyzer.analyze(
                        group_a=group_a_texts,
                        group_b=group_b_texts,
                        correct_answer=correct_answer,
                        output_dir=str(self.results_dir),
                        examples=examples,
                        experiment_name=f"{aspect}_{shot_count}shot"
                    )
                    
                    # 結果に追加情報を付与
                    enhanced_result = {
                        "experiment_id": experiment_count,
                        "experiment_type": "steam_binary_contrast_factor",
                        "aspect": aspect,
                        "shot_count": shot_count,
                        "group_a_size": split_data['group_a_size'],
                        "group_b_size": split_data['group_b_size'],
                        "ground_truth": correct_answer,
                        "llm_response": result.get('process', {}).get('llm_response', 'N/A'),
                        "bert_score": result.get('evaluation', {}).get('bert_score', 0),
                        "bleu_score": result.get('evaluation', {}).get('bleu_score', 0),
                        "timestamp": datetime.now().isoformat(),
                        "full_result": result  # 完全な結果も保存
                    }
                    
                    all_results.append(enhanced_result)
                    
                    logger.info(f"    応答: {enhanced_result['llm_response']}")
                    logger.info(f"    BERT: {enhanced_result['bert_score']:.4f}, BLEU: {enhanced_result['bleu_score']:.4f}")
                
                except Exception as e:
                    logger.error(f"実験{experiment_count}でエラー: {e}")
                    continue
        
        return all_results
    
    def save_results(self, results: List[Dict]) -> str:
        """実験結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.results_dir / f"steam_binary_contrast_experiment_results_{timestamp}.json"
        
        # 結果サマリーの作成
        summary = {
            "experiment_info": {
                "experiment_type": "Steam Review Binary Contrast Factor Generation",
                "dataset": "Steam Review Aspect Dataset",
                "target_group_size": self.target_group_size,
                "aspects": self.aspects,
                "shot_counts": self.shot_counts,
                "total_experiments": len(results),
                "timestamp": timestamp,
                "random_seed": self.random_seed
            },
            "results": results
        }
        
        # JSON保存
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"実験結果を保存: {output_file}")
        return str(output_file)
    
    def generate_summary_report(self, results: List[Dict]) -> str:
        """実験結果のサマリーレポートを生成"""
        if not results:
            return ""
        
        df = pd.DataFrame(results)
        
        # 平均スコア計算
        bert_mean = df['bert_score'].mean()
        bleu_mean = df['bleu_score'].mean()
        
        # レポート生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.results_dir / f"steam_binary_experiment_report_{timestamp}.md"
        
        report_content = f"""# Steam Review Dataset 二項対比因子抽出実験レポート

**実験日時**: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}  
**データセット**: Steam Review Aspect Dataset  
**総実験数**: {len(results)}回  

---

## 📋 実験概要

### 実験設計
- **タイプ**: 二項対比因子抽出（特定アスペクト含む vs 含まない）
- **アスペクト数**: {len(self.aspects)}種類
- **Few-shot設定**: {', '.join(map(str, self.shot_counts))}
- **各グループサイズ**: {self.target_group_size}レビュー
- **総実験回数**: {len(results)}回

### 対象アスペクト
{', '.join(self.aspects)}

---

## 📊 総合結果

| 指標 | 平均スコア |
|------|-----------|
| **BERTスコア** | {bert_mean:.4f} |
| **BLEUスコア** | {bleu_mean:.4f} |

---

## 📈 詳細結果

### アスペクト別詳細

"""
        
        # アスペクト別に整理
        for aspect in self.aspects:
            aspect_results = df[df['aspect'] == aspect]
            if len(aspect_results) == 0:
                continue
            
            report_content += f"#### {aspect}\n\n"
            report_content += "| Shot設定 | BERTスコア | BLEUスコア | LLM応答 | データ分割 |\n"
            report_content += "|----------|------------|------------|---------|------------|\n"
            
            for _, result in aspect_results.iterrows():
                response_short = result['llm_response'][:50] + "..." if len(result['llm_response']) > 50 else result['llm_response']
                report_content += f"| {result['shot_count']}-shot | {result['bert_score']:.3f} | {result['bleu_score']:.3f} | {response_short} | {result['group_a_size']}件 vs {result['group_b_size']}件 |\n"
            
            report_content += "\n"
        
        # 統計サマリー
        report_content += f"""
---

## 🔍 統計分析

### Shot設定別平均スコア
"""
        
        shot_stats = df.groupby('shot_count')[['bert_score', 'bleu_score']].mean()
        for shot, stats in shot_stats.iterrows():
            report_content += f"- **{shot}-shot**: BERT={stats['bert_score']:.4f}, BLEU={stats['bleu_score']:.4f}\n"
        
        report_content += f"""
### アスペクト別平均スコア
"""
        
        aspect_stats = df.groupby('aspect')[['bert_score', 'bleu_score']].mean()
        for aspect, stats in aspect_stats.iterrows():
            report_content += f"- **{aspect}**: BERT={stats['bert_score']:.4f}, BLEU={stats['bleu_score']:.4f}\n"
        
        report_content += f"""

---

## 💡 考察

- 総実験数{len(results)}回の二項対比因子抽出を実行
- BERTスコア平均{bert_mean:.4f}は意味的類似度を示す
- BLEUスコア平均{bleu_mean:.4f}は語彙的一致度を示す
- Few-shot学習による性能変化を分析

---

**実験完了時刻**: {datetime.now().isoformat()}
"""
        
        # レポート保存
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"実験レポートを生成: {report_file}")
        return str(report_file)
    
    def print_experiment_summary(self, results: List[Dict]):
        """実験結果サマリーを表示"""
        print(f"\n{'='*60}")
        print("Steam 二項対比因子抽出実験結果サマリー")
        print(f"{'='*60}")
        
        if not results:
            print("❌ 実験結果がありません")
            return
        
        df = pd.DataFrame(results)
        
        print(f"総実験数: {len(results)}")
        print(f"平均BERTスコア: {df['bert_score'].mean():.4f}")
        print(f"平均BLEUスコア: {df['bleu_score'].mean():.4f}")
        
        # Shot別統計
        print(f"\n🎯 Shot設定別統計:")
        shot_stats = df.groupby('shot_count')[['bert_score', 'bleu_score']].mean()
        for shot, stats in shot_stats.iterrows():
            print(f"  - {shot}-shot: BERT={stats['bert_score']:.4f}, BLEU={stats['bleu_score']:.4f}")
        
        # アスペクト別統計
        print(f"\n📊 アスペクト別統計:")
        aspect_stats = df.groupby('aspect')[['bert_score', 'bleu_score']].mean()
        for aspect, stats in aspect_stats.iterrows():
            print(f"  - {aspect}: BERT={stats['bert_score']:.4f}, BLEU={stats['bleu_score']:.4f}")
        
        # サンプル応答例
        print(f"\n📝 応答例:")
        for i, result in enumerate(results[:3]):
            print(f"  実験{i+1} ({result['aspect']}-{result['shot_count']}shot):")
            print(f"    \"{result['llm_response']}\"")
    
    def run_full_experiment(self):
        """完全な実験を実行"""
        logger.info("Steam二項対比因子抽出実験を開始")
        logger.info(f"目標サンプルサイズ: {self.target_group_size}レビュー/グループ")
        logger.info(f"対象アスペクト: {', '.join(self.aspects)}")
        logger.info(f"Few-shot設定: {self.shot_counts}")
        
        # Phase 1: データ準備
        df = self.load_steam_data()
        splits = self.create_binary_splits(df)
        
        if not splits:
            logger.error("利用可能なアスペクトデータがありません。実験を中止します。")
            return
        
        # Phase 2: 対比実験実行
        results = self.run_binary_contrast_experiments(splits)
        
        if not results:
            logger.error("実験結果が得られませんでした。")
            return
        
        # Phase 3: 結果保存・表示
        output_file = self.save_results(results)
        report_file = self.generate_summary_report(results)
        self.print_experiment_summary(results)
        
        print(f"\n🎉 Steam二項対比因子抽出実験完了!")
        print(f"📄 結果ファイル: {output_file}")
        print(f"📋 レポートファイル: {report_file}")
        return results


def main():
    """メイン関数"""
    experiment = SteamBinaryContrastExperiment()
    results = experiment.run_full_experiment()
    return results


if __name__ == "__main__":
    main() 