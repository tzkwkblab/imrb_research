from typing import List, Dict
import openai
import pandas as pd
from tqdm import tqdm

class FeatureExtractor:
    def __init__(self):
        self.features = [
            "価格が高いという旨の内容を含んでいる",
            "ポジティブな内容から始まっている",
            "競合商品との比較に関する内容を含んでいる",
            "商品の品質について言及している",
            "配送や発送に関する内容を含んでいる",
            "使用経験の詳細な説明がある",
            "カスタマーサービスについて言及している",
            "商品の耐久性について言及している",
            "コストパフォーマンスについて言及している",
            "商品のデザインについて言及している"
        ]
    
    def extract_features_with_chatgpt(self, review: str) -> Dict[str, int]:
        """
        ChatGPTを使用して特徴を抽出する
        
        Args:
            review: レビューテキスト
            
        Returns:
            特徴の有無を示す辞書 {特徴: 0or1}
        """
        prompt = f"""
        以下の商品レビューについて、各特徴の有無を判定してください：
        
        レビュー: {review}
        
        特徴:
        {chr(10).join(f"{i+1}. {f}" for i, f in enumerate(self.features))}
        
        回答形式: カンマ区切りの0と1のリスト（例: 1,0,1,0,1,0,1,0,1,0）
        ※0=特徴なし、1=特徴あり
        """
        
        # ChatGPT APIを使用して判定
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.choices[0].message.content.strip()
            
            # 結果を0/1のリストに変換
            labels = [int(x) for x in result.split(",")]
            
            # 辞書形式で返す
            return dict(zip(self.features, labels))
            
        except Exception as e:
            print(f"Error processing review: {e}")
            return {f: 0 for f in self.features}
    
    def process_dataset(self, reviews: List[str], batch_size: int = 10) -> pd.DataFrame:
        """
        データセット全体の特徴を抽出する
        
        Args:
            reviews: レビューのリスト
            batch_size: バッチサイズ
            
        Returns:
            特徴行列のDataFrame
        """
        results = []
        for i in tqdm(range(0, len(reviews), batch_size)):
            batch = reviews[i:i + batch_size]
            batch_results = [self.extract_features_with_chatgpt(review) for review in batch]
            results.extend(batch_results)
        
        return pd.DataFrame(results)

def validate_features(df: pd.DataFrame, sample_size: int = 100) -> pd.DataFrame:
    """
    特徴抽出の品質を人手で確認するためのサンプルを生成
    
    Args:
        df: 特徴行列のDataFrame
        sample_size: 確認するサンプル数
        
    Returns:
        検証用のDataFrame
    """
    validation_sample = df.sample(n=sample_size)
    validation_sample['human_verified'] = None
    validation_sample['comments'] = ''
    return validation_sample
