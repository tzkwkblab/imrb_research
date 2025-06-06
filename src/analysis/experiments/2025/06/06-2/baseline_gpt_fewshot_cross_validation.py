"""
改良版ベースライン構築コード
- 訓練・テスト分割を廃止
- Few-shot/Zero-shot学習実験を導入
- クロスバリデーション方式を実装
- 全特徴評価を可能にする
- ハルシネーション検証機能を追加
"""

import sys
import os
import openai
import pandas as pd
from dotenv import load_dotenv
import json
from pathlib import Path
from datetime import datetime
import numpy as np
from typing import List, Dict, Optional

RANDOM_SEED = 42
FEATURE_COUNT = 20


def split_reviews_by_feature_index(
    test_size=0.2,
    csv_file_path='src/analysis/experiments/2025/05/15/processed_reviews.csv',
    feature_name_col='feature_name'
):
    """
    特徴インデックスに基づいてレビューデータを分割する関数
    """
    if not 0 <= test_size <= 1:
        print(f"エラー: test_size は 0 から 1 の間で指定してください。指定値: {test_size}")
        return None

    # CSVファイルを読み込む
    try:
        df = pd.read_csv(csv_file_path)
        print(f"{csv_file_path} を読み込みました。データ件数: {len(df)}") 
    except FileNotFoundError:
        print(f"エラー: {csv_file_path} が見つかりません。") 
        return None
    except Exception as e:
        print(f"エラー: ファイル読み込み中にエラーが発生しました - {e}") 
        return None

    # 特徴カラムの確認
    feature_cols = [col for col in df.columns if col.startswith('final_feature_')]
    if not feature_cols:
        print("エラー: 'final_feature_' で始まるカラムがCSVファイルに見つかりません。")
        return None

    # トレーニングとテストの分割点を計算
    total_features = FEATURE_COUNT  # 特徴の総数
    split_index = int(total_features * (1 - test_size))
    
    # 結果を格納する辞書
    results = {
        'train': [],
        'test': []
    }

    # 特徴ごとに処理
    for feature_index in range(1, total_features + 1):
        feature_col = f'final_feature_{feature_index}'
        
        # 特徴カラムが存在するか確認
        if feature_col not in df.columns:
            print(f"警告: 特徴カラム '{feature_col}' がCSVファイルに見つかりません。スキップします。")
            continue
        
        # 特徴名を取得（存在する場合）
        feature_name = None
        if feature_name_col in df.columns:
            # 特徴に関連する名前を取得する処理（データ構造に依存）
            # この例では、最初に特徴を持つレコードから特徴名を取得
            feature_records = df[df[feature_col] == 1]
            if len(feature_records) > 0 and feature_name_col in feature_records.columns:
                feature_name = feature_records[feature_name_col].iloc[0]
        
        # 特徴を持つ/持たないレビュー群に分割
        df_has_feature = df[df[feature_col] == 1].copy()
        df_no_feature = df[df[feature_col] == 0].copy()
        
        # 特徴名がない場合はデフォルト名を設定
        if feature_name is None:
            feature_name = f"Feature {feature_index}"
        
        # 分割点に基づいてトレーニングまたはテストに追加
        feature_data = [df_has_feature, df_no_feature, feature_name]
        
        if feature_index <= split_index:
            results['train'].append(feature_data)
        else:
            results['test'].append(feature_data)
    
    print(f"トレーニングセット: 特徴1〜{split_index}の{len(results['train'])}個の特徴")
    print(f"テストセット: 特徴{split_index+1}〜{total_features}の{len(results['test'])}個の特徴")
    
    return results


class ImprovedGPTAnalyzer:
    def __init__(self):
        # .envファイルから環境変数を読み込む
        load_dotenv()
        
        # 環境変数からAPIキーを設定
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        if not self.client.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    def load_all_features(self, csv_file_path='src/analysis/experiments/2025/05/15/processed_reviews.csv'):
        """全特徴データを読み込む（分割なし）"""
        print("全特徴データを読み込み中...")
        split_data = split_reviews_by_feature_index(
            test_size=0.0,  # 分割しない
            csv_file_path=csv_file_path
        )
        
        if not split_data or 'train' not in split_data:
            raise ValueError("データの読み込みに失敗しました")
        
        # 全特徴を統合
        all_features = split_data['train']
        print(f"読み込み完了: {len(all_features)}個の特徴")
        
        return all_features
    
    def load_all_reviews(self, csv_file_path='src/analysis/experiments/2025/05/15/processed_reviews.csv'):
        """全レビューデータを読み込む（ハルシネーション検証用）"""
        print("全レビューデータを読み込み中...")
        try:
            df = pd.read_csv(csv_file_path)
            print(f"読み込み完了: {len(df)}件のレビュー")
            return df
        except Exception as e:
            raise ValueError(f"データの読み込みに失敗しました: {e}")
    
    def extract_review_samples(self, df_has_feature, df_no_feature, sample_size=5):
        """レビューグループから指定数のサンプルを抽出"""
        # 特徴を含むレビューからサンプル抽出
        has_feature_samples = []
        if len(df_has_feature) > 0:
            sample_count = min(sample_size, len(df_has_feature))
            samples = df_has_feature.sample(n=sample_count, random_state=RANDOM_SEED)
            has_feature_samples = samples['review_text'].tolist()
        
        # 特徴を含まないレビューからサンプル抽出
        no_feature_samples = []
        if len(df_no_feature) > 0:
            sample_count = min(sample_size, len(df_no_feature))
            samples = df_no_feature.sample(n=sample_count, random_state=RANDOM_SEED)
            no_feature_samples = samples['review_text'].tolist()
        
        return has_feature_samples, no_feature_samples
    
    def extract_random_groups(self, all_reviews, sample_size=10, random_seed=None):
        """全レビューからランダムに2グループを抽出（ハルシネーション検証用）"""
        if random_seed is None:
            random_seed = RANDOM_SEED
        
        # レビューをシャッフル
        shuffled = all_reviews.sample(frac=1, random_state=random_seed).reset_index(drop=True)
        
        # 十分なデータがあるか確認
        if len(shuffled) < 2 * sample_size:
            raise ValueError(f"データ不足: {len(shuffled)}件のレビューでは{sample_size}×2グループを作成できません")
        
        # 2グループに分割
        group_a = shuffled.iloc[:sample_size]['review_text'].tolist()
        group_b = shuffled.iloc[sample_size:2*sample_size]['review_text'].tolist()
        
        return group_a, group_b
    
    def create_few_shot_prompt(self, example_features: List, target_feature, example_sample_size=3, target_sample_size=10):
        """Few-shot学習用プロンプトを生成"""
        # 例題部分の構築
        example_prompts = []
        for i, ex_feature in enumerate(example_features):
            ex_has, ex_no = self.extract_review_samples(
                ex_feature[0], ex_feature[1], sample_size=example_sample_size
            )
            
            # 特徴記述を取得（CSVから）
            feature_description = self.get_feature_description(ex_feature[2])
            
            example_group_a = "\n".join([f"- {review}" for review in ex_has])
            example_group_b = "\n".join([f"- {review}" for review in ex_no])
            
            example_prompts.append(f"""例題{i+1}
【グループ A のレビュー】
{example_group_a}

【グループ B のレビュー】
{example_group_b}

回答例：{feature_description}""")
        
        # 問題部分の構築
        target_has, target_no = self.extract_review_samples(
            target_feature[0], target_feature[1], sample_size=target_sample_size
        )
        
        problem_group_a = "\n".join([f"- {review}" for review in target_has])
        problem_group_b = "\n".join([f"- {review}" for review in target_no])
        
        # プロンプト全体の構築
        examples_text = "\n\n".join(example_prompts) if example_prompts else ""
        
        prompt = f"""あなたはレビューテキスト分析の専門家です。これから 2 つのレビューグループを提示します：

- グループ A：特定の特徴を含むレビュー集合
- グループ B：その特徴を含まないレビュー集合

【出力形式】

英単語で 5 から 10 単語程度で出してください。

{examples_text}

では、これから問題を提示します。以下の二つのグループのレビューを見て、グループ A に存在し、グループ B に存在しない特徴や表現パターンを特定し、その違いを回答してください。

【グループ A のレビュー】
{problem_group_a}

【グループ B のレビュー】
{problem_group_b}

回答："""

        return prompt
    
    def create_random_group_prompt(self, group_a, group_b):
        """ランダムグループ用プロンプトを生成（ハルシネーション検証用）"""
        group_a_text = "\n".join([f"- {review}" for review in group_a])
        group_b_text = "\n".join([f"- {review}" for review in group_b])
        
        prompt = f"""あなたはレビューテキスト分析の専門家です。これから 2 つのレビューグループを提示します：

- グループ A：ランダムに選択されたレビュー集合
- グループ B：ランダムに選択されたレビュー集合

【出力形式】

英単語で 5 から 10 単語程度で出してください。

以下の二つのグループのレビューを見て、グループ A に存在し、グループ B に存在しない特徴や表現パターンを特定し、その違いを回答してください。

【グループ A のレビュー】
{group_a_text}

【グループ B のレビュー】
{group_b_text}

回答："""

        return prompt
    
    def create_hallucination_detection_prompt(self, context_reviews_a, context_reviews_b, gpt_statement):
        """ハルシネーション判定用プロンプトを生成"""
        context_a_text = "\n".join([f"- {review}" for review in context_reviews_a])
        context_b_text = "\n".join([f"- {review}" for review in context_reviews_b])
        
        prompt = f"""あなたはレビュー分析の専門家です。
以下の「コンテキスト」は、2つのランダムなレビューグループの内容です。
「ステートメント」は、それらの違いをGPTが説明したものです。

このステートメントがコンテキストに根拠があるかを0～1のスコアで評価してください。
- 0 = 完全に根拠あり（コンテキストから明確に読み取れる違い）
- 0.5 = 部分的に根拠あり（一部は読み取れるが、一部は推測）
- 1 = 完全に根拠なし（コンテキストに存在しない違いを述べている）

【コンテキスト】
グループA:
{context_a_text}

グループB:
{context_b_text}

【ステートメント】
{gpt_statement}

【評価】
このステートメントのハルシネーションスコア（0～1）を数値のみで回答してください："""

        return prompt
    
    def get_feature_description(self, feature_name):
        """特徴名から特徴記述を取得"""
        # 簡単な特徴名→記述のマッピング（実際のCSVから取得すべき）
        feature_mapping = {
            "Feature 1": "Contains mentions of price or cost",
            "Feature 2": "Includes technical details or specifications",
            "Feature 3": "Contains comparisons with competing products",
            "Feature 4": "Mentions long-term usage experience",
            "Feature 5": "Explains specific use cases or purposes",
            # 必要に応じて他の特徴も追加
        }
        return feature_mapping.get(feature_name, "Unknown feature")
    
    def query_gpt(self, prompt):
        """GPTに問い合わせ"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert in analyzing product reviews and identifying textual patterns."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"API呼び出し中にエラーが発生しました: {e}")
            return None
    
    def query_gpt_for_hallucination_score(self, prompt):
        """ハルシネーション判定用のGPT問い合わせ"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert evaluator of text analysis accuracy. Respond only with a numerical score between 0 and 1."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # より一貫した判定のため低めに設定
                max_tokens=10
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # 数値のみを抽出
            try:
                score = float(response_text)
                return max(0.0, min(1.0, score))  # 0-1の範囲に制限
            except ValueError:
                print(f"スコア解析エラー: {response_text}")
                return None
            
        except Exception as e:
            print(f"ハルシネーション判定API呼び出し中にエラーが発生しました: {e}")
            return None
    
    def save_results(self, results, output_file=None):
        """結果をファイルに保存"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"src/analysis/experiments/2025/06/06-2/improved_results_{timestamp}.json"
        
        # 出力ディレクトリを作成
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"結果を保存しました: {output_file}")
        
        return output_file
    
    def run_hallucination_experiment(self, num_experiments=20, sample_size=10):
        """
        ハルシネーション検証実験を実行
        
        Args:
            num_experiments: 実験回数
            sample_size: 各グループのサンプル数
        """
        print(f"\n{'='*60}")
        print(f"ハルシネーション検証実験開始 ({num_experiments}回実験)")
        print(f"{'='*60}")
        
        # 全レビューデータを読み込み
        all_reviews = self.load_all_reviews()
        
        all_results = []
        
        for experiment_idx in range(num_experiments):
            print(f"\n--- 実験 {experiment_idx + 1}/{num_experiments} ---")
            
            # ランダムシードを変えて異なるグループを生成
            random_seed = RANDOM_SEED + experiment_idx
            
            try:
                # ランダムに2グループを抽出
                group_a, group_b = self.extract_random_groups(
                    all_reviews, 
                    sample_size=sample_size, 
                    random_seed=random_seed
                )
                
                # GPTに違いを説明させる
                prompt = self.create_random_group_prompt(group_a, group_b)
                gpt_response = self.query_gpt(prompt)
                
                if gpt_response:
                    print(f"GPT回答: {gpt_response}")
                    
                    # ハルシネーション判定
                    hallucination_prompt = self.create_hallucination_detection_prompt(
                        group_a, group_b, gpt_response
                    )
                    hallucination_score = self.query_gpt_for_hallucination_score(hallucination_prompt)
                    
                    if hallucination_score is not None:
                        print(f"ハルシネーションスコア: {hallucination_score}")
                        
                        result = {
                            "experiment_id": experiment_idx + 1,
                            "random_seed": random_seed,
                            "sample_size": sample_size,
                            "group_a": group_a,
                            "group_b": group_b,
                            "prompt": prompt,
                            "gpt_response": gpt_response,
                            "hallucination_prompt": hallucination_prompt,
                            "hallucination_score": hallucination_score,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        all_results.append(result)
                    else:
                        print(f"実験{experiment_idx + 1}: ハルシネーション判定に失敗")
                else:
                    print(f"実験{experiment_idx + 1}: GPT回答取得に失敗")
                    
            except Exception as e:
                print(f"実験{experiment_idx + 1}でエラー: {e}")
                continue
        
        # 結果保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"src/analysis/experiments/2025/06/06-2/hallucination_results_{timestamp}.json"
        self.save_results(all_results, output_file)
        
        # 統計サマリー
        self.print_hallucination_summary(all_results)
        
        return all_results
    
    def print_hallucination_summary(self, results):
        """ハルシネーション実験結果のサマリーを表示"""
        if not results:
            print("結果がありません")
            return
        
        scores = [r['hallucination_score'] for r in results if r['hallucination_score'] is not None]
        
        if not scores:
            print("有効なスコアがありません")
            return
        
        print(f"\n{'='*60}")
        print("ハルシネーション検証結果サマリー")
        print(f"{'='*60}")
        print(f"実験数: {len(results)}")
        print(f"有効スコア数: {len(scores)}")
        print(f"平均ハルシネーションスコア: {np.mean(scores):.3f}")
        print(f"標準偏差: {np.std(scores):.3f}")
        print(f"最小値: {np.min(scores):.3f}")
        print(f"最大値: {np.max(scores):.3f}")
        print(f"中央値: {np.median(scores):.3f}")
        
        # スコア分布
        low_hallucination = sum(1 for s in scores if s <= 0.3)
        medium_hallucination = sum(1 for s in scores if 0.3 < s <= 0.7)
        high_hallucination = sum(1 for s in scores if s > 0.7)
        
        print(f"\nスコア分布:")
        print(f"  低ハルシネーション (0-0.3): {low_hallucination}件 ({low_hallucination/len(scores)*100:.1f}%)")
        print(f"  中ハルシネーション (0.3-0.7): {medium_hallucination}件 ({medium_hallucination/len(scores)*100:.1f}%)")
        print(f"  高ハルシネーション (0.7-1.0): {high_hallucination}件 ({high_hallucination/len(scores)*100:.1f}%)")
        
        # 例を表示
        print(f"\n回答例:")
        for i, result in enumerate(results[:3]):
            if result['hallucination_score'] is not None:
                print(f"  実験{i+1}: \"{result['gpt_response']}\" (スコア: {result['hallucination_score']})")
    
    def run_few_shot_analysis(self, shot_counts=[0, 1, 3], target_features=None):
        """
        Few-shot/zero-shot実験を実行
        
        Args:
            shot_counts: 例題数のリスト（例: [0, 1, 3]）
            target_features: 対象特徴のインデックスリスト（Noneの場合は全特徴）
        """
        all_features = self.load_all_features()
        num_features = len(all_features)
        
        if target_features is None:
            target_features = list(range(num_features))
        
        all_results = []
        
        for shot_count in shot_counts:
            print(f"\n{'='*60}")
            print(f"{shot_count}-shot 設定で分析開始")
            print(f"{'='*60}")
            
            for target_idx in target_features:
                if target_idx >= num_features:
                    print(f"警告: 特徴インデックス {target_idx} は範囲外です")
                    continue
                
                target_feature = all_features[target_idx]
                target_name = target_feature[2]
                
                print(f"\n--- 特徴{target_idx + 1}の分析: {target_name} ({shot_count}-shot) ---")
                
                # 例題として使う特徴を選択（target_idx以外からshot_count個ランダム抽出）
                example_features = []
                if shot_count > 0:
                    example_indices = [i for i in range(num_features) if i != target_idx]
                    if len(example_indices) >= shot_count:
                        np.random.seed(RANDOM_SEED + target_idx)  # 再現性のため
                        selected_indices = np.random.choice(
                            example_indices, 
                            size=shot_count, 
                            replace=False
                        )
                        example_features = [all_features[i] for i in selected_indices]
                        example_names = [f[2] for f in example_features]
                        print(f"例題として使用: {example_names}")
                    else:
                        print(f"警告: 例題数 {shot_count} が利用可能な特徴数を超えています")
                        continue
                
                # プロンプト生成
                prompt = self.create_few_shot_prompt(example_features, target_feature)
                
                # GPTに問い合わせ
                print("GPTに問い合わせ中...")
                gpt_response = self.query_gpt(prompt)
                
                if gpt_response:
                    print(f"GPT回答: {gpt_response}")
                    
                    # 結果をまとめる
                    result = {
                        "shot_count": shot_count,
                        "target_feature_index": int(target_idx + 1),
                        "target_feature_name": target_name,
                        "example_features": [f[2] for f in example_features],
                        "example_feature_indices": [int(i + 1) for i in selected_indices] if shot_count > 0 else [],
                        "prompt": prompt,
                        "gpt_response": gpt_response,
                        "timestamp": datetime.now().isoformat(),
                        "target_feature_stats": {
                            "has_feature_count": len(target_feature[0]),
                            "no_feature_count": len(target_feature[1])
                        }
                    }
                    
                    all_results.append(result)
                else:
                    print(f"特徴{target_idx + 1}のGPT回答取得に失敗しました")
        
        # 結果保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"src/analysis/experiments/2025/06/06-2/few_shot_results_{timestamp}.json"
        self.save_results(all_results, output_file)
        
        # サマリー表示
        self.print_analysis_summary(all_results)
        
        return all_results
    
    def run_cross_validation_analysis(self, k_folds=5, shot_count=1):
        """
        クロスバリデーション方式での分析
        
        Args:
            k_folds: フォールド数
            shot_count: 各フォールドでの例題数
        """
        all_features = self.load_all_features()
        num_features = len(all_features)
        
        print(f"\n{'='*60}")
        print(f"{k_folds}-fold クロスバリデーション分析開始 ({shot_count}-shot)")
        print(f"{'='*60}")
        
        # 特徴をk個のフォールドに分割
        np.random.seed(RANDOM_SEED)
        indices = np.random.permutation(num_features)
        fold_size = num_features // k_folds
        
        all_results = []
        
        for fold in range(k_folds):
            print(f"\n--- Fold {fold + 1}/{k_folds} ---")
            
            # テスト用特徴の選択
            start_idx = fold * fold_size
            end_idx = start_idx + fold_size if fold < k_folds - 1 else num_features
            test_indices = indices[start_idx:end_idx]
            
            # 訓練用特徴の選択（テスト以外）
            train_indices = np.concatenate([indices[:start_idx], indices[end_idx:]])
            
            print(f"テスト特徴: {[i + 1 for i in test_indices]}")
            print(f"例題候補特徴: {[i + 1 for i in train_indices[:10]]}...")  # 最初の10個のみ表示
            
            # 各テスト特徴について評価
            for test_idx in test_indices:
                target_feature = all_features[test_idx]
                target_name = target_feature[2]
                
                print(f"\n特徴{test_idx + 1}の分析: {target_name}")
                
                # 例題特徴をランダム選択
                example_features = []
                if shot_count > 0 and len(train_indices) >= shot_count:
                    np.random.seed(RANDOM_SEED + test_idx)
                    selected_train_indices = np.random.choice(
                        train_indices, 
                        size=shot_count, 
                        replace=False
                    )
                    example_features = [all_features[i] for i in selected_train_indices]
                
                # プロンプト生成と評価
                prompt = self.create_few_shot_prompt(example_features, target_feature)
                gpt_response = self.query_gpt(prompt)
                
                if gpt_response:
                    result = {
                        "fold": fold + 1,
                        "shot_count": shot_count,
                        "target_feature_index": int(test_idx + 1),
                        "target_feature_name": target_name,
                        "example_features": [f[2] for f in example_features],
                        "gpt_response": gpt_response,
                        "timestamp": datetime.now().isoformat()
                    }
                    all_results.append(result)
                    print(f"GPT回答: {gpt_response}")
        
        # 結果保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"src/analysis/experiments/2025/06/06-2/cross_validation_results_{timestamp}.json"
        self.save_results(all_results, output_file)
        
        return all_results
    
    def run_comprehensive_analysis(self):
        """包括的分析（全特徴 × 複数shot設定）"""
        print("=== 包括的分析開始 ===")
        
        # Few-shot分析
        few_shot_results = self.run_few_shot_analysis(
            shot_counts=[0, 1, 3, 5],
            target_features=list(range(10))  # 最初の10特徴で実験
        )
        
        # クロスバリデーション分析
        cv_results = self.run_cross_validation_analysis(k_folds=5, shot_count=1)
        
        # 統合結果の保存
        combined_results = {
            "analysis_type": "comprehensive_improved_analysis",
            "few_shot_results": few_shot_results,
            "cross_validation_results": cv_results,
            "total_experiments": len(few_shot_results) + len(cv_results),
            "timestamp": datetime.now().isoformat()
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"src/analysis/experiments/2025/06/06-2/comprehensive_results_{timestamp}.json"
        self.save_results(combined_results, output_file)
        
        return combined_results
    
    def run_comprehensive_with_hallucination_analysis(self):
        """包括的分析（Few-shot + ハルシネーション検証）"""
        print("=== 包括的分析（ハルシネーション検証含む）開始 ===")
        
        # Few-shot分析
        few_shot_results = self.run_few_shot_analysis(
            shot_counts=[0, 1, 3],
            target_features=list(range(5))  # 最初の5特徴で実験（時間短縮）
        )
        
        # ハルシネーション検証実験
        hallucination_results = self.run_hallucination_experiment(
            num_experiments=15,  # 15回実験
            sample_size=10
        )
        
        # 統合結果の保存
        combined_results = {
            "analysis_type": "comprehensive_with_hallucination_analysis",
            "few_shot_results": few_shot_results,
            "hallucination_results": hallucination_results,
            "total_experiments": len(few_shot_results) + len(hallucination_results),
            "timestamp": datetime.now().isoformat()
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"src/analysis/experiments/2025/06/06-2/comprehensive_with_hallucination_{timestamp}.json"
        self.save_results(combined_results, output_file)
        
        return combined_results
    
    def print_analysis_summary(self, results):
        """分析結果のサマリーを表示"""
        print(f"\n{'='*60}")
        print("分析結果サマリー")
        print(f"{'='*60}")
        
        # Shot数別の統計
        shot_counts = {}
        for result in results:
            shot = result['shot_count']
            if shot not in shot_counts:
                shot_counts[shot] = []
            shot_counts[shot].append(result)
        
        for shot, shot_results in shot_counts.items():
            print(f"\n{shot}-shot 結果 ({len(shot_results)}件):")
            for result in shot_results[:3]:  # 最初の3件のみ表示
                print(f"  特徴{result['target_feature_index']}: {result['gpt_response']}")
            if len(shot_results) > 3:
                print(f"  ... 他{len(shot_results) - 3}件")


def main():
    """メイン関数"""
    try:
        analyzer = ImprovedGPTAnalyzer()
        
        # ハルシネーション検証を含む包括的分析の実行
        results = analyzer.run_comprehensive_with_hallucination_analysis()
        
        print("\n=== 改良版分析（ハルシネーション検証含む）完了 ===")
        print(f"Few-shot実験: {len(results['few_shot_results'])}件")
        print(f"ハルシネーション実験: {len(results['hallucination_results'])}件")
        print(f"総実験数: {results['total_experiments']}件")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
