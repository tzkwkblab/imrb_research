#!/usr/bin/env python3
"""
SemEval ABSA GPT対比因子生成実験
ドメイン別特徴ベース分割による対比因子生成と評価
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

# 上位ディレクトリから既存モジュールをインポート
sys.path.append('src/analysis/experiments/2025/06/09-2/')
from domain_aware_feature_splitter import DomainAwareFeatureSplitter

# 設定
load_dotenv()
RANDOM_SEED = 42
TARGET_SAMPLE_SIZE = 300  # 各グループのサンプル数
OPENAI_MODEL = "gpt-4"
MAX_RETRIES = 3

class SemEvalContrastExperiment:
    """SemEval ABSA対比因子生成実験クラス"""
    
    def __init__(self, dataset_path: str = None):
        """
        初期化
        Args:
            dataset_path: データセットのパス
        """
        self.splitter = DomainAwareFeatureSplitter(dataset_path)
        self.results_dir = Path("src/analysis/experiments/2025/06/12/results")
        self.results_dir.mkdir(exist_ok=True)
        
        # OpenAI API設定
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        if not self.client.api_key:
            raise ValueError("OPENAI_API_KEY環境変数が設定されていません")
        
        # 実験設定
        self.target_domains = ['restaurant', 'laptop']
        self.domain_features = {
            'restaurant': ['food', 'service', 'staff', 'atmosphere', 'menu', 'price'],
            'laptop': ['battery', 'screen', 'keyboard', 'performance', 'price', 'design']
        }
        self.shot_counts = [0, 1, 3]  # Few-shot設定
        
        # ランダムシード設定
        random.seed(RANDOM_SEED)
        np.random.seed(RANDOM_SEED)
    
    def prepare_domain_data(self) -> Dict[str, Dict]:
        """
        ドメインデータの準備と特徴ベース分割
        Returns:
            ドメイン別分割データ
        """
        print("🔍 SemEval ABSAデータの準備を開始...")
        
        # ドメイン発見
        available_domains = self.splitter.discover_domains()
        
        domain_splits = {}
        
        for domain in self.target_domains:
            if domain not in available_domains:
                print(f"⚠️ ドメイン '{domain}' が見つかりません。スキップします。")
                continue
            
            print(f"\n📊 {domain.upper()}ドメインの処理開始")
            
            # ドメインデータ読み込み
            domain_files = available_domains[domain]
            samples = self.splitter.load_domain_data(domain_files)
            
            if len(samples) < TARGET_SAMPLE_SIZE * 2:
                print(f"⚠️ {domain}ドメインのデータが不足しています。"
                      f"必要: {TARGET_SAMPLE_SIZE * 2}, 利用可能: {len(samples)}")
                continue
            
            # 特徴分析
            feature_analysis = self.splitter.analyze_domain_features(domain, samples)
            
            # 特徴ベース分割
            target_features = self.domain_features.get(domain, [])
            splits = self.splitter.create_domain_feature_splits(domain, samples, target_features)
            
            # 各特徴についてサンプル数を調整
            adjusted_splits = {}
            for feature, split_data in splits.items():
                group_a = split_data['group_a']
                group_b = split_data['group_b']
                
                # サンプル数調整
                adjusted_group_a = self._adjust_sample_size(group_a, TARGET_SAMPLE_SIZE)
                adjusted_group_b = self._adjust_sample_size(group_b, TARGET_SAMPLE_SIZE)
                
                if len(adjusted_group_a) < TARGET_SAMPLE_SIZE or len(adjusted_group_b) < TARGET_SAMPLE_SIZE:
                    print(f"⚠️ {domain}の{feature}特徴でサンプル数が不足。"
                          f"A: {len(adjusted_group_a)}, B: {len(adjusted_group_b)}")
                    continue
                
                adjusted_splits[feature] = {
                    'domain': domain,
                    'feature': feature,
                    'group_a': adjusted_group_a,
                    'group_b': adjusted_group_b,
                    'group_a_size': len(adjusted_group_a),
                    'group_b_size': len(adjusted_group_b),
                    'matching_aspects': split_data['matching_aspects']
                }
                
                print(f"✅ {feature}: A={len(adjusted_group_a)}, B={len(adjusted_group_b)}")
            
            domain_splits[domain] = adjusted_splits
        
        return domain_splits
    
    def _adjust_sample_size(self, samples: List[Dict], target_size: int) -> List[Dict]:
        """
        サンプル数を目標サイズに調整
        Args:
            samples: サンプルリスト
            target_size: 目標サイズ
        Returns:
            調整されたサンプルリスト
        """
        if len(samples) >= target_size:
            # ランダムサンプリング
            return random.sample(samples, target_size)
        else:
            # 重複サンプリングで補完
            return samples + random.choices(samples, k=target_size - len(samples))
    
    def create_contrast_prompt(self, group_a: List[Dict], group_b: List[Dict], 
                             domain: str, feature: str, shot_count: int = 0) -> str:
        """
        対比因子生成用プロンプトを作成
        Args:
            group_a: グループAのレビュー
            group_b: グループBのレビュー
            domain: ドメイン名
            feature: 特徴名
            shot_count: Few-shot設定
        Returns:
            プロンプト文字列
        """
        # グループAのレビューテキスト（最大10件表示）
        group_a_texts = [sample['review_text'] for sample in group_a[:10]]
        group_b_texts = [sample['review_text'] for sample in group_b[:10]]
        
        group_a_display = "\n".join([f"- {text[:200]}..." if len(text) > 200 else f"- {text}" 
                                   for text in group_a_texts])
        group_b_display = "\n".join([f"- {text[:200]}..." if len(text) > 200 else f"- {text}" 
                                   for text in group_b_texts])
        
        # ドメイン情報
        domain_context = {
            'restaurant': 'レストラン・飲食店',
            'laptop': 'ノートパソコン・ラップトップ'
        }.get(domain, domain)
        
        # Few-shot例題部分（実装簡略化のため今回は0-shotのみ）
        few_shot_examples = ""
        if shot_count > 0:
            few_shot_examples = f"\n【参考例題】\n（{shot_count}個の例題がここに入ります）\n"
        
        prompt = f"""あなたは{domain_context}レビュー分析の専門家です。

【分析タスク】
以下の2つのレビューグループを比較して、グループAに特徴的でグループBには見られない表現パターンや内容の特徴を特定してください。

【データ情報】
- ドメイン: {domain_context}
- 対象特徴: {feature}
- グループAサイズ: {len(group_a)}レビュー
- グループBサイズ: {len(group_b)}レビュー

{few_shot_examples}

【グループA のレビュー】（{feature}特徴を含む）
{group_a_display}

【グループB のレビュー】（{feature}特徴を含まない）
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
                        {"role": "system", "content": "あなたは優秀なレビューテキスト分析専門家です。"},
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
    
    def run_contrast_experiments(self, domain_splits: Dict[str, Dict]) -> List[Dict]:
        """
        対比因子生成実験を実行
        Args:
            domain_splits: ドメイン別分割データ
        Returns:
            実験結果リスト
        """
        print(f"\n🚀 対比因子生成実験を開始...")
        
        all_results = []
        experiment_count = 0
        
        for domain, splits in domain_splits.items():
            print(f"\n📊 {domain.upper()}ドメインの実験開始")
            
            for feature, split_data in splits.items():
                print(f"\n🎯 特徴: {feature}")
                
                for shot_count in self.shot_counts:
                    experiment_count += 1
                    print(f"  実験 {experiment_count}: {shot_count}-shot設定")
                    
                    # プロンプト生成
                    prompt = self.create_contrast_prompt(
                        split_data['group_a'],
                        split_data['group_b'],
                        domain,
                        feature,
                        shot_count
                    )
                    
                    # GPT実行
                    gpt_response = self.query_gpt(prompt)
                    
                    if gpt_response:
                        print(f"    GPT応答: {gpt_response}")
                        
                        # 結果記録
                        result = {
                            "experiment_id": experiment_count,
                            "experiment_type": "semeval_absa_contrast_factor",
                            "domain": domain,
                            "feature": feature,
                            "shot_count": shot_count,
                            "group_a_size": split_data['group_a_size'],
                            "group_b_size": split_data['group_b_size'],
                            "matching_aspects": split_data['matching_aspects'],
                            "gpt_response": gpt_response,
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
        output_file = self.results_dir / f"semeval_contrast_experiment_results_{timestamp}.json"
        
        # 結果サマリーの作成
        summary = {
            "experiment_info": {
                "experiment_type": "SemEval ABSA Contrast Factor Generation",
                "target_sample_size": TARGET_SAMPLE_SIZE,
                "domains": self.target_domains,
                "domain_features": self.domain_features,
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
    
    def print_experiment_summary(self, results: List[Dict]):
        """
        実験結果サマリーを表示
        Args:
            results: 実験結果リスト
        """
        print(f"\n{'='*60}")
        print("実験結果サマリー")
        print(f"{'='*60}")
        
        print(f"総実験数: {len(results)}")
        
        # ドメイン別統計
        domain_stats = {}
        for result in results:
            domain = result['domain']
            if domain not in domain_stats:
                domain_stats[domain] = {'total': 0, 'features': set()}
            domain_stats[domain]['total'] += 1
            domain_stats[domain]['features'].add(result['feature'])
        
        for domain, stats in domain_stats.items():
            print(f"\n📊 {domain.upper()}ドメイン:")
            print(f"  - 実験数: {stats['total']}")
            print(f"  - 特徴数: {len(stats['features'])}")
            print(f"  - 特徴: {', '.join(sorted(stats['features']))}")
        
        # Shot別統計
        shot_stats = {}
        for result in results:
            shot = result['shot_count']
            if shot not in shot_stats:
                shot_stats[shot] = 0
            shot_stats[shot] += 1
        
        print(f"\n🎯 Shot設定別統計:")
        for shot, count in sorted(shot_stats.items()):
            print(f"  - {shot}-shot: {count}実験")
        
        # サンプル応答例
        print(f"\n📝 応答例:")
        for i, result in enumerate(results[:3]):
            print(f"  実験{i+1} ({result['domain']}-{result['feature']}-{result['shot_count']}shot):")
            print(f"    \"{result['gpt_response']}\"")
    
    def run_full_experiment(self):
        """
        完全な実験を実行
        """
        print("🚀 SemEval ABSA対比因子生成実験を開始")
        print(f"目標サンプルサイズ: {TARGET_SAMPLE_SIZE}レビュー/グループ")
        print(f"対象ドメイン: {', '.join(self.target_domains)}")
        print(f"Few-shot設定: {self.shot_counts}")
        
        # Phase 1: データ準備
        domain_splits = self.prepare_domain_data()
        
        if not domain_splits:
            print("❌ 利用可能なドメインデータがありません。実験を中止します。")
            return
        
        # Phase 2: 対比実験実行
        results = self.run_contrast_experiments(domain_splits)
        
        if not results:
            print("❌ 実験結果が得られませんでした。")
            return
        
        # Phase 3: 結果保存・表示
        output_file = self.save_results(results)
        self.print_experiment_summary(results)
        
        print(f"\n🎉 実験完了! 結果ファイル: {output_file}")
        return results


def main():
    """メイン関数"""
    experiment = SemEvalContrastExperiment()
    results = experiment.run_full_experiment()
    return results


if __name__ == "__main__":
    main() 