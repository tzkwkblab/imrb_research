"""
ベースライン構築のためのコード
- レビューデータを分割して読み込み
- 特徴1を例題、特徴2を問題としてGPTに問い合わせ
- メモのプロンプト形式に従って実装
"""

import sys
import os
# パスを追加してreview_data_splitterをインポートできるようにする
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, '..', '19')
sys.path.append(parent_dir)

from review_data_splitter import split_reviews_by_feature_index
import openai
import pandas as pd
from dotenv import load_dotenv
import json
from pathlib import Path
from datetime import datetime

RANDOM_SEED = 42


class BaselineGPTAnalyzer:
    def __init__(self):
        # .envファイルから環境変数を読み込む
        load_dotenv()
        
        # 環境変数からAPIキーを設定
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        if not self.client.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    def load_review_data(self, csv_file_path='src/analysis/experiments/2025/05/15/processed_reviews.csv'):
        """レビューデータを分割して読み込む"""
        print("レビューデータを読み込み中...")
        split_data = split_reviews_by_feature_index(
            test_size=0.2,
            csv_file_path=csv_file_path
        )
        
        if not split_data:
            raise ValueError("データの読み込みに失敗しました")
        
        print(f"トレーニングセット: {len(split_data['train'])}個の特徴")
        print(f"テストセット: {len(split_data['test'])}個の特徴")
        
        return split_data
    
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
    
    def create_prompt(self, feature1_data, feature2_data):
        """プロンプトを生成"""
        # 特徴1（例題用）のサンプルを抽出
        feature1_has, feature1_no = self.extract_review_samples(
            feature1_data[0], feature1_data[1], sample_size=3
        )
        
        # 特徴2（問題用）のサンプルを抽出
        feature2_has, feature2_no = self.extract_review_samples(
            feature2_data[0], feature2_data[1], sample_size=10
        )
        
        # 例題1のレビューテキストを組み立て
        example1_group_a = "\n".join([f"- {review}" for review in feature1_has])
        example1_group_b = "\n".join([f"- {review}" for review in feature1_no])
        
        # 問題のレビューテキストを組み立て
        problem_group_a = "\n".join([f"- {review}" for review in feature2_has])
        problem_group_b = "\n".join([f"- {review}" for review in feature2_no])
        
        prompt = f"""あなたはレビューテキスト分析の専門家です。これから 2 つのレビューグループを提示します：

- グループ A：特定の特徴を含むレビュー集合
- グループ B：その特徴を含まないレビュー集合

【出力形式】

英単語で 5 から 10 単語程度で出してください。

回答の例として、以下に例題とその回答を示します。

例題１
【グループ A のレビュー】
{example1_group_a}

【グループ B のレビュー】
{example1_group_b}

回答例：Contains mentions of price or cost

では、これから問題を提示します。以下の二つのグループのレビューを見て、グループ A に存在し、グループ B に存在しない特徴や表現パターンを特定し、その違いを回答してください。

【グループ A のレビュー】
{problem_group_a}

【グループ B のレビュー】
{problem_group_b}

回答："""

        return prompt
    
    def query_gpt(self, prompt):
        """GPTに問い合わせ"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
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
    
    def save_results(self, results, output_file=None):
        """結果をファイルに保存"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"src/analysis/experiments/2025/05/20/baseline_results_{timestamp}.json"
        
        # 出力ディレクトリを作成
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"結果を保存しました: {output_file}")
        
        return output_file
    
    def run_baseline_analysis(self):
        """ベースライン分析を実行（特徴1を例題として、特徴2〜5を問題として順次実行）"""
        print("=== ベースライン分析開始 ===")
        
        # データを読み込み
        split_data = self.load_review_data()
        
        # 特徴1〜5のデータを確認
        if len(split_data['train']) < 5:
            raise ValueError("トレーニングデータに十分な特徴が存在しません（最低5個必要）")
        
        # 特徴1を例題として固定
        feature1_data = split_data['train'][0]  # 特徴1
        print(f"\n例題として使用: {feature1_data[2]}")
        print(f"- 特徴を含むレビュー: {len(feature1_data[0])}件")
        print(f"- 特徴を含まないレビュー: {len(feature1_data[1])}件")
        
        # 結果を格納するリスト
        all_results = []
        
        # 特徴2〜5を順次処理
        for feature_idx in range(1, 5):  # インデックス1〜4（特徴2〜5）
            feature_data = split_data['train'][feature_idx]
            feature_name = feature_data[2]
            
            print(f"\n{'='*60}")
            print(f"特徴{feature_idx + 1}の分析開始: {feature_name}")
            print(f"- 特徴を含むレビュー: {len(feature_data[0])}件")
            print(f"- 特徴を含まないレビュー: {len(feature_data[1])}件")
            
            # プロンプトを生成
            print("プロンプトを生成中...")
            prompt = self.create_prompt(feature1_data, feature_data)
            
            # GPTに問い合わせ
            print("GPTに問い合わせ中...")
            gpt_response = self.query_gpt(prompt)
            
            if gpt_response:
                print(f"\n=== 特徴{feature_idx + 1}のGPT回答 ===")
                print(gpt_response)
                print("=" * 50)
                
                # 結果をまとめる
                result = {
                    "feature_number": feature_idx + 1,
                    "timestamp": datetime.now().isoformat(),
                    "feature1_info": {
                        "name": feature1_data[2],
                        "has_feature_count": len(feature1_data[0]),
                        "no_feature_count": len(feature1_data[1])
                    },
                    "target_feature_info": {
                        "name": feature_name,
                        "has_feature_count": len(feature_data[0]),
                        "no_feature_count": len(feature_data[1])
                    },
                    "prompt": prompt,
                    "gpt_response": gpt_response
                }
                
                all_results.append(result)
                
                # 個別結果を保存
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                individual_file = f"src/analysis/experiments/2025/05/20/baseline_feature{feature_idx + 1}_{timestamp}.json"
                self.save_results(result, individual_file)
                
            else:
                print(f"特徴{feature_idx + 1}のGPT回答取得に失敗しました")
                
        # 全体結果をまとめて保存
        if all_results:
            summary_results = {
                "analysis_type": "baseline_features_2_to_5",
                "total_features_analyzed": len(all_results),
                "example_feature": feature1_data[2],
                "results": all_results
            }
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_file = f"src/analysis/experiments/2025/05/20/baseline_summary_{timestamp}.json"
            self.save_results(summary_results, summary_file)
            
            print(f"\n{'='*60}")
            print("=== 全体分析結果サマリー ===")
            for result in all_results:
                print(f"特徴{result['feature_number']}: {result['target_feature_info']['name']}")
                print(f"  GPT回答: {result['gpt_response']}")
                print()
        
        return all_results


def main():
    """メイン関数"""
    try:
        analyzer = BaselineGPTAnalyzer()
        results = analyzer.run_baseline_analysis()
        
        if results:
            print("\n=== ベースライン分析完了 ===")
            print(f"例題として使用した特徴: {results[0]['feature1_info']['name']}")
            print(f"分析対象特徴数: {len(results)}個")
            print("\n--- 各特徴の分析結果 ---")
            for result in results:
                print(f"特徴{result['feature_number']}: {result['target_feature_info']['name']}")
                print(f"  GPTの回答: {result['gpt_response']}")
                print()
        else:
            print("分析に失敗しました")
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
