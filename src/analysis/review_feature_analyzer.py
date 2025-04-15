"""
1. OpenAI APIを使用してレビューテキストを分析
2. 各特徴について1（当てはまる）または0（当てはまらない）を判定
"""

import openai
import pandas as pd
import json
from pathlib import Path
from dotenv import load_dotenv
import os

# 
class ReviewFeatureAnalyzer:
    def __init__(self):
        # .envファイルから環境変数を読み込む
        load_dotenv()
        
        # 環境変数からAPIキーを設定
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        if not self.client.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # 特徴定義の読み込み
        self.features_df = pd.read_csv("src/data/features/definitions/review_features.csv")
        
    def analyze_review(self, review_text, review_rating):
        """一つのレビューに対して20個の特徴を分析"""
        
        # プロンプトの作成
        prompt = self._create_prompt(review_text, review_rating)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたは商品レビューを分析する専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0  # 決定論的な応答を得るため
            )
            
            # 応答の解析
            result = self._parse_response(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Error during API call: {e}")
            return None
        
    def _create_prompt(self, review_text, rating):
        """分析用のプロンプトを作成"""
        features_list = "\n".join([
            f"{row['feature_id']}. {row['feature_description']}"
            for _, row in self.features_df.iterrows()
        ])
        
        prompt = f"""
以下の商品レビューに対して、各特徴が当てはまるかどうかを判定してください。

【レビュー】
{review_text}

【レビュー評価】
{rating}

【特徴リスト】
{features_list}

各特徴について、以下の2つの情報を含めて回答してください：
1. value: その特徴が当てはまる場合は1、当てはまらない場合は0
2. reason: 判定理由を1文で簡潔に説明（具体的な引用を含める）

回答形式：
{{
    "features": {{
        "1": {{ 
            "value": 0 or 1,
            "reason": "判定理由（'具体的な引用'に基づく）"
        }},
        "2": {{ 
            "value": 0 or 1,
            "reason": "判定理由（'具体的な引用'に基づく）"
        }},
        ...
    }}
}}
"""
        return prompt
    
    def _parse_response(self, response_text):
        """APIレスポンスをパース"""
        try:
            # JSON部分を抽出して解析
            json_str = response_text.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            result = json.loads(json_str)
            return result
        except Exception as e:
            print(f"Error parsing response: {e}")
            return None

# 使用例
if __name__ == "__main__":
    analyzer = ReviewFeatureAnalyzer()
    
    # テスト用レビュー
    review = """Yeah, I don't get this obsession with Monster brand cable either. When I got my 5.1 set-up, I thought the only way to get 5.1 sound was to use an optical wire anyway. Well, on my system it was, as it had no RCA jacks for all those discrete channels. All it has is one optical jack and one set of L/R RCA jacks for a stereo VCR source.So all I did was go to Wal Mart or Radio Shack (can't remember which) and bought the only optical cable they had for like 20 bucks. Works just fine. My problem if anything is my receiver. But I think I'll be upgrading sometime later this year."""
    
    result = analyzer.analyze_review(review, 3.0)
    
    if result and 'features' in result:
        # 結果の表示
        print("=== Review Analysis Results ===\n")
        for feature_id, feature_data in result['features'].items():
            feature_desc = analyzer.features_df.loc[
                analyzer.features_df['feature_id'] == int(feature_id), 
                'feature_description'
            ].iloc[0]
            print(f"\nFeature {feature_id}: {feature_desc}")
            if isinstance(feature_data, dict):
                print(f"Value: {feature_data.get('value', 'N/A')}")
                print(f"Reason: {feature_data.get('reason', 'N/A')}")
            else:
                print(f"Value: {feature_data}")