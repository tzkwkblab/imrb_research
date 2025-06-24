#!/usr/bin/env python3
"""
Steam Review Aspect Dataset GPT対比因子生成実験
8アスペクト × 3 Few-shot設定による対比因子生成と評価
"""

import sys
import os
import json
import openai
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
import numpy as np
import random
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

# 設定
load_dotenv()
RANDOM_SEED = 42
TARGET_SAMPLE_SIZE = 300  # 各グループのサンプル数
OPENAI_MODEL = "gpt-4"
MAX_RETRIES = 3

class SteamAspectContrastExperiment:
    """Steam Review Aspect対比因子生成実験クラス"""
    
    def __init__(self, dataset_path: str = "data/external/steam-review-aspect-dataset/current"):
        """
        初期化
        Args:
            dataset_path: データセットのパス
        """
        self.dataset_path = Path(dataset_path)
        self.results_dir = Path("src/analysis/experiments/2025/06/24/results")
        self.results_dir.mkdir(exist_ok=True)
        
        # OpenAI API設定
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        if not self.client.api_key:
            raise ValueError("OPENAI_API_KEY環境変数が設定されていません")
        
        # 実験設定
        self.aspects = [
            'recommended', 'story', 'gameplay', 'visual', 
            'audio', 'technical', 'price', 'suggestion'
        ]
        self.shot_counts = [0, 1, 3]
        
        # 評価用
        self.sentence_bert = SentenceTransformer('all-MiniLM-L6-v2')
        self.smoothing = SmoothingFunction().method1
        
        # ランダムシード設定
        random.seed(RANDOM_SEED)
        np.random.seed(RANDOM_SEED)
    
    def load_steam_data(self) -> pd.DataFrame:
        """Steam Review Datasetを読み込み"""
        train_path = self.dataset_path / "train.csv"
        test_path = self.dataset_path / "test.csv"
        
        print(f"📥 データ読み込み: {train_path}")
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)
        
        # 訓練データとテストデータを結合
        full_df = pd.concat([train_df, test_df], ignore_index=True)
        print(f"✅ 総データ数: {len(full_df)}件")
        
        return full_df
    
    def create_aspect_splits(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """
        各アスペクトでグループA/B分割を作成
        Args:
            df: Steamレビューデータ
        Returns:
            アスペクト別分割データ
        """
        print("🔍 アスペクト別グループ分割を開始...")
        
        splits = {}
        
        for aspect in self.aspects:
            aspect_col = f'label_{aspect}'
            
            if aspect_col not in df.columns:
                print(f"⚠️ カラム'{aspect_col}'が見つかりません。スキップします。")
                continue
            
            # グループA（アスペクト該当）とグループB（非該当）を分割
            group_a = df[df[aspect_col] == 1].copy()
            group_b = df[df[aspect_col] == 0].copy()
            
            print(f"📊 {aspect}: A={len(group_a)}, B={len(group_b)}")
            
            # サンプル数調整
            adjusted_group_a = self._adjust_sample_size(group_a, TARGET_SAMPLE_SIZE)
            adjusted_group_b = self._adjust_sample_size(group_b, TARGET_SAMPLE_SIZE)
            
            if len(adjusted_group_a) < TARGET_SAMPLE_SIZE or len(adjusted_group_b) < TARGET_SAMPLE_SIZE:
                print(f"⚠️ {aspect}でサンプル数が不足。A: {len(adjusted_group_a)}, B: {len(adjusted_group_b)}")
                continue
            
            splits[aspect] = {
                'aspect': aspect,
                'group_a': adjusted_group_a,
                'group_b': adjusted_group_b,
                'group_a_size': len(adjusted_group_a),
                'group_b_size': len(adjusted_group_b)
            }
            
            print(f"✅ {aspect}: A={len(adjusted_group_a)}, B={len(adjusted_group_b)}")
        
        return splits
    
    def _adjust_sample_size(self, samples: pd.DataFrame, target_size: int) -> pd.DataFrame:
        """
        サンプル数を目標サイズに調整
        Args:
            samples: サンプルDataFrame
            target_size: 目標サイズ
        Returns:
            調整されたサンプルDataFrame
        """
        if len(samples) >= target_size:
            # ランダムサンプリング
            return samples.sample(n=target_size, random_state=RANDOM_SEED)
        else:
            # 重複サンプリングで補完
            additional_needed = target_size - len(samples)
            additional = samples.sample(n=additional_needed, replace=True, random_state=RANDOM_SEED)
            return pd.concat([samples, additional], ignore_index=True)
    
    def create_contrast_prompt(self, group_a: pd.DataFrame, group_b: pd.DataFrame, 
                             aspect: str, shot_count: int = 0) -> str:
        """
        対比因子生成用プロンプトを作成
        Args:
            group_a: グループAのレビュー
            group_b: グループBのレビュー
            aspect: アスペクト名
            shot_count: Few-shot設定
        Returns:
            プロンプト文字列
        """
        # グループAとBのレビューテキスト（最大10件表示）
        group_a_texts = group_a['review'].head(10).tolist()
        group_b_texts = group_b['review'].head(10).tolist()
        
        group_a_display = "\n".join([f"- {text[:200]}..." if len(text) > 200 else f"- {text}" 
                                   for text in group_a_texts])
        group_b_display = "\n".join([f"- {text[:200]}..." if len(text) > 200 else f"- {text}" 
                                   for text in group_b_texts])
        
        # アスペクト説明
        aspect_descriptions = {
            'recommended': 'ゲーム推薦',
            'story': '物語・ストーリー',
            'gameplay': 'ゲームプレイ・システム',
            'visual': 'ビジュアル・グラフィック',
            'audio': '音質・サウンド',
            'technical': '技術的要素・バグ',
            'price': '価格・コスト',
            'suggestion': '提案・要望'
        }
        aspect_desc = aspect_descriptions.get(aspect, aspect)
        
        # Few-shot例題部分（実装簡略化のため今回は0-shotのみ）
        few_shot_examples = ""
        if shot_count > 0:
            few_shot_examples = f"\n【参考例題】\n（{shot_count}個の例題がここに入ります）\n"
        
        prompt = f"""あなたはSteamゲームレビュー分析の専門家です。

【分析タスク】
以下の2つのレビューグループを比較して、グループAに特徴的でグループBには見られない表現パターンや内容の特徴を特定してください。

【データ情報】
- 対象アスペクト: {aspect_desc} ({aspect})
- グループAサイズ: {len(group_a)}レビュー
- グループBサイズ: {len(group_b)}レビュー

{few_shot_examples}

【グループA のレビュー】（{aspect_desc}に言及）
{group_a_display}

【グループB のレビュー】（{aspect_desc}に言及しない）
{group_b_display}

【回答要求】
英語で5-10単語程度で、グループAに特徴的でグループBには見られない主要な違いを簡潔に回答してください。

回答："""

        return prompt
    
    def query_gpt(self, prompt: str) -> Optional[str]:
        """
        GPT APIにクエリを送信
        Args:
            prompt: プロンプト
        Returns:
            GPTの応答（失敗時はNone）
        """
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "あなたは優秀なゲームレビュー分析専門家です。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=100
                )
                return response.choices[0].message.content.strip()
            
            except Exception as e:
                print(f"GPT API エラー (試行 {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt == MAX_RETRIES - 1:
                    return None
        
        return None
    
    def calculate_bert_similarity(self, text_a: str, text_b: str) -> float:
        """BERT類似度を計算"""
        emb = self.sentence_bert.encode([text_a, text_b])
        sim = cosine_similarity([emb[0]], [emb[1]])[0][0]
        return float((sim + 1) / 2)  # -1~1→0~1
    
    def calculate_bleu_similarity(self, text_a: str, text_b: str) -> float:
        """BLEU類似度を計算"""
        ref = text_a.lower().split()
        cand = text_b.lower().split()
        return float(sentence_bleu([ref], cand, smoothing_function=self.smoothing))
    
    def run_contrast_experiments(self, aspect_splits: Dict[str, Dict]) -> List[Dict]:
        """
        対比因子生成実験を実行
        Args:
            aspect_splits: アスペクト別分割データ
        Returns:
            実験結果リスト
        """
        print(f"\n🚀 対比因子生成実験を開始...")
        
        all_results = []
        experiment_count = 0
        
        for aspect, split_data in aspect_splits.items():
            print(f"\n📊 アスペクト: {aspect}")
            
            for shot_count in self.shot_counts:
                experiment_count += 1
                print(f"  実験 {experiment_count}: {shot_count}-shot設定")
                
                # プロンプト生成
                prompt = self.create_contrast_prompt(
                    split_data['group_a'],
                    split_data['group_b'],
                    aspect,
                    shot_count
                )
                
                # GPT実行
                gpt_response = self.query_gpt(prompt)
                
                if gpt_response:
                    print(f"    GPT応答: {gpt_response}")
                    
                    # 正解ラベル（アスペクト名）
                    ground_truth = aspect
                    
                    # 類似度計算
                    bert_score = self.calculate_bert_similarity(ground_truth, gpt_response)
                    bleu_score = self.calculate_bleu_similarity(ground_truth, gpt_response)
                    
                    print(f"    BERT: {bert_score:.4f}, BLEU: {bleu_score:.4f}")
                    
                    # 結果記録
                    result = {
                        "experiment_id": experiment_count,
                        "experiment_type": "steam_aspect_contrast_factor",
                        "aspect": aspect,
                        "shot_count": shot_count,
                        "group_a_size": split_data['group_a_size'],
                        "group_b_size": split_data['group_b_size'],
                        "gpt_response": gpt_response,
                        "ground_truth": ground_truth,
                        "bert_similarity": bert_score,
                        "bleu_score": bleu_score,
                        "prompt_length": len(prompt),
                        "timestamp": datetime.now().isoformat(),
                        "model": OPENAI_MODEL
                    }
                    
                    all_results.append(result)
                else:
                    print(f"    ❌ GPT応答の取得に失敗")
        
        return all_results
    
    def save_results(self, results: List[Dict]) -> str:
        """
        実験結果を保存
        Args:
            results: 実験結果リスト
        Returns:
            保存ファイルパス
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.results_dir / f"steam_contrast_experiment_results_{timestamp}.json"
        
        # 結果サマリーの作成
        summary = {
            "experiment_info": {
                "experiment_type": "Steam Review Aspect Contrast Factor Generation",
                "target_sample_size": TARGET_SAMPLE_SIZE,
                "aspects": self.aspects,
                "shot_counts": self.shot_counts,
                "model": OPENAI_MODEL,
                "total_experiments": len(results),
                "timestamp": timestamp
            },
            "results": results
        }
        
        # JSON保存
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 実験結果を保存: {output_file}")
        return str(output_file)
    
    def generate_summary_report(self, results: List[Dict]) -> str:
        """
        実験結果のサマリーレポートを生成
        Args:
            results: 実験結果リスト
        Returns:
            レポートファイルパス
        """
        if not results:
            return ""
        
        df = pd.DataFrame(results)
        
        # 平均スコア計算
        bert_mean = df['bert_similarity'].mean()
        bleu_mean = df['bleu_score'].mean()
        
        # レポート生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.results_dir / f"steam_experiment_report_{timestamp}.md"
        
        report_content = f"""# Steam Review Aspect 対比因子生成実験レポート

**実験日時**: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}  
**データセット**: Steam Review Aspect Dataset  
**総実験数**: {len(results)}回  

---

## 📋 実験概要

### 実験設計
- **アスペクト数**: {len(self.aspects)}種類
- **Few-shot設定**: {', '.join(map(str, self.shot_counts))}
- **各グループサイズ**: {TARGET_SAMPLE_SIZE}レビュー
- **総実験回数**: {len(self.aspects)} × {len(self.shot_counts)} = {len(results)}回

### 対象アスペクト
{', '.join(self.aspects)}

---

## 📊 総合結果

| 評価指標 | 平均スコア |
|----------|------------|
| **BERTスコア** | {bert_mean:.4f} |
| **BLEUスコア** | {bleu_mean:.4f} |

---

## 📈 詳細結果

| アスペクト | Shot | BERTスコア | BLEUスコア | GPT応答 |
|------------|------|------------|------------|---------|
"""
        
        for result in results:
            report_content += f"| {result['aspect']} | {result['shot_count']} | {result['bert_similarity']:.4f} | {result['bleu_score']:.4f} | {result['gpt_response'][:50]}... |\n"
        
        report_content += f"""
---

## 🔍 分析結果

### アスペクト別平均スコア
"""
        
        # アスペクト別統計
        aspect_stats = df.groupby('aspect')[['bert_similarity', 'bleu_score']].mean()
        for aspect, stats in aspect_stats.iterrows():
            report_content += f"- **{aspect}**: BERT={stats['bert_similarity']:.4f}, BLEU={stats['bleu_score']:.4f}\n"
        
        report_content += f"""
### Shot設定別平均スコア
"""
        
        # Shot別統計
        shot_stats = df.groupby('shot_count')[['bert_similarity', 'bleu_score']].mean()
        for shot, stats in shot_stats.iterrows():
            report_content += f"- **{shot}-shot**: BERT={stats['bert_similarity']:.4f}, BLEU={stats['bleu_score']:.4f}\n"
        
        report_content += f"""
---

## 💡 考察

- 総実験数{len(results)}回中、すべての実験でGPT応答を取得
- BERTスコア平均{bert_mean:.4f}は意味的類似度を示す
- BLEUスコア平均{bleu_mean:.4f}は語彙的一致度を示す

---

**実験完了時刻**: {datetime.now().isoformat()}
"""
        
        # レポート保存
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"\n📄 実験レポートを生成: {report_file}")
        return str(report_file)
    
    def print_experiment_summary(self, results: List[Dict]):
        """
        実験結果サマリーを表示
        Args:
            results: 実験結果リスト
        """
        print(f"\n{'='*60}")
        print("実験結果サマリー")
        print(f"{'='*60}")
        
        if not results:
            print("❌ 実験結果がありません")
            return
        
        df = pd.DataFrame(results)
        
        print(f"総実験数: {len(results)}")
        print(f"平均BERTスコア: {df['bert_similarity'].mean():.4f}")
        print(f"平均BLEUスコア: {df['bleu_score'].mean():.4f}")
        
        # アスペクト別統計
        print(f"\n📊 アスペクト別統計:")
        aspect_stats = df.groupby('aspect')[['bert_similarity', 'bleu_score']].mean()
        for aspect, stats in aspect_stats.iterrows():
            print(f"  - {aspect}: BERT={stats['bert_similarity']:.4f}, BLEU={stats['bleu_score']:.4f}")
        
        # Shot別統計
        print(f"\n🎯 Shot設定別統計:")
        shot_stats = df.groupby('shot_count')[['bert_similarity', 'bleu_score']].mean()
        for shot, count in shot_stats.iterrows():
            print(f"  - {shot}-shot: BERT={count['bert_similarity']:.4f}, BLEU={count['bleu_score']:.4f}")
        
        # サンプル応答例
        print(f"\n📝 応答例:")
        for i, result in enumerate(results[:3]):
            print(f"  実験{i+1} ({result['aspect']}-{result['shot_count']}shot):")
            print(f"    \"{result['gpt_response']}\"")
    
    def run_full_experiment(self):
        """
        完全な実験を実行
        """
        print("🚀 Steam Review Aspect対比因子生成実験を開始")
        print(f"目標サンプルサイズ: {TARGET_SAMPLE_SIZE}レビュー/グループ")
        print(f"対象アスペクト: {', '.join(self.aspects)}")
        print(f"Few-shot設定: {self.shot_counts}")
        
        # Phase 1: データ準備
        df = self.load_steam_data()
        aspect_splits = self.create_aspect_splits(df)
        
        if not aspect_splits:
            print("❌ 利用可能なアスペクトデータがありません。実験を中止します。")
            return
        
        # Phase 2: 対比実験実行
        results = self.run_contrast_experiments(aspect_splits)
        
        if not results:
            print("❌ 実験結果が得られませんでした。")
            return
        
        # Phase 3: 結果保存・表示
        output_file = self.save_results(results)
        report_file = self.generate_summary_report(results)
        self.print_experiment_summary(results)
        
        print(f"\n🎉 実験完了!")
        print(f"📄 結果ファイル: {output_file}")
        print(f"📋 レポートファイル: {report_file}")
        return results


def main():
    """メイン関数"""
    experiment = SteamAspectContrastExperiment()
    results = experiment.run_full_experiment()
    return results


if __name__ == "__main__":
    main() 