#!/usr/bin/env python3
"""
文章類似度評価スクリプト

このスクリプトは、前回の実験で出力したGPTレスポンスと
元の特徴記述の類似度をBERTとBLEUを用いて評価します。

要件:
- 入力: テキストデータAとB
- 出力: 0から1の確率値（BERT類似度とBLEU類似度）
- 対象: feature2, 3, 4, 5
"""

import json
import os
import pandas as pd
import numpy as np
from typing import Tuple, Dict, List
from pathlib import Path

# 必要なライブラリのインポート
try:
    from sentence_transformers import SentenceTransformer
    from transformers import AutoTokenizer, AutoModel
    import torch
    from sklearn.metrics.pairwise import cosine_similarity
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    import nltk
except ImportError as e:
    print(f"必要なライブラリがインストールされていません: {e}")
    print("以下のコマンドでインストールしてください:")
    print("pip install sentence-transformers transformers torch scikit-learn nltk")
    exit(1)

# NLTK データのダウンロード
try:
    nltk.download('punkt', quiet=True)
except:
    pass


class TextSimilarityEvaluator:
    """テキスト類似度評価クラス"""
    
    def __init__(self):
        """初期化"""
        self.bert_model = None
        self.tokenizer = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self._load_models()
        
    def _load_models(self):
        """BERTモデルの読み込み"""
        try:
            # Sentence-BERTモデル（より高速で簡単）
            self.sentence_bert = SentenceTransformer('all-MiniLM-L6-v2')
            print("Sentence-BERTモデルを読み込みました")
        except Exception as e:
            print(f"モデル読み込みエラー: {e}")
            
    def calculate_bert_similarity(self, text_a: str, text_b: str) -> float:
        """
        BERT埋め込みを用いたコサイン類似度を計算
        
        Args:
            text_a (str): テキストA
            text_b (str): テキストB
            
        Returns:
            float: 0から1の類似度スコア
        """
        try:
            # 文章をエンベディングに変換
            embeddings = self.sentence_bert.encode([text_a, text_b])
            
            # コサイン類似度を計算
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            
            # -1から1の範囲を0から1に変換
            normalized_similarity = (similarity + 1) / 2
            
            return float(normalized_similarity)
            
        except Exception as e:
            print(f"BERT類似度計算エラー: {e}")
            return 0.0
    
    def calculate_bleu_similarity(self, text_a: str, text_b: str) -> float:
        """
        BLEU スコアを計算
        
        Args:
            text_a (str): テキストA（参照文）
            text_b (str): テキストB（候補文）
            
        Returns:
            float: 0から1のBLEUスコア
        """
        try:
            # テキストをトークン化
            reference = text_a.lower().split()
            candidate = text_b.lower().split()
            
            # スムージング関数（ゼロ除算を避けるため）
            smoothing = SmoothingFunction().method1
            
            # BLEU スコア計算
            bleu_score = sentence_bleu([reference], candidate, smoothing_function=smoothing)
            
            return float(bleu_score)
            
        except Exception as e:
            print(f"BLEU類似度計算エラー: {e}")
            return 0.0
    
    def evaluate_similarity(self, text_a: str, text_b: str) -> Tuple[float, float]:
        """
        二つのテキストの類似度を評価
        
        Args:
            text_a (str): テキストA
            text_b (str): テキストB
            
        Returns:
            Tuple[float, float]: (BERT類似度, BLEU類似度)
        """
        bert_sim = self.calculate_bert_similarity(text_a, text_b)
        bleu_sim = self.calculate_bleu_similarity(text_a, text_b)
        
        return bert_sim, bleu_sim


class DataLoader:
    """データ読み込みクラス"""
    
    def __init__(self, base_path: str):
        """
        初期化
        
        Args:
            base_path (str): プロジェクトのベースパス
        """
        self.base_path = Path(base_path)
        self.json_dir = self.base_path / "src/analysis/experiments/2025/05/20"
        self.csv_path = self.base_path / "src/analysis/experiments/review_features.csv"
        
    def load_feature_descriptions(self) -> Dict[int, str]:
        """
        特徴記述CSVを読み込み
        
        Returns:
            Dict[int, str]: feature_id -> feature_description の辞書
        """
        try:
            df = pd.read_csv(self.csv_path)
            feature_dict = {}
            for _, row in df.iterrows():
                feature_dict[row['feature_id']] = row['feature_description']
            return feature_dict
        except Exception as e:
            print(f"CSVファイル読み込みエラー: {e}")
            return {}
    
    def load_gpt_responses(self, features: List[int]) -> Dict[int, str]:
        """
        指定した特徴番号のGPTレスポンスを読み込み
        
        Args:
            features (List[int]): 読み込む特徴番号のリスト
            
        Returns:
            Dict[int, str]: feature_number -> gpt_response の辞書
        """
        gpt_responses = {}
        
        # 各特徴番号に対応するファイル名のタイムスタンプマッピング
        timestamp_map = {
            2: "20250523_154828",
            3: "20250523_154829", 
            4: "20250523_154830",
            5: "20250523_154831"
        }
        
        for feature_num in features:
            if feature_num not in timestamp_map:
                print(f"Feature {feature_num}: タイムスタンプマッピングが見つかりません")
                continue
                
            timestamp = timestamp_map[feature_num]
            json_file = self.json_dir / f"baseline_feature{feature_num}_{timestamp}.json"
            
            if not json_file.exists():
                print(f"ファイルが見つかりません: {json_file}")
                continue
                
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    gpt_responses[feature_num] = data.get('gpt_response', '')
            except Exception as e:
                print(f"JSONファイル読み込みエラー ({json_file}): {e}")
                
        return gpt_responses


def main():
    """メイン実行関数"""
    print("=== テキスト類似度評価プログラム ===")
    print()
    
    # ベースパスの設定
    base_path = "/Users/seinoshun/imrb_research"
    
    # データローダーと評価器の初期化
    loader = DataLoader(base_path)
    evaluator = TextSimilarityEvaluator()
    
    # 対象特徴番号
    target_features = [2, 3, 4, 5]
    
    # データ読み込み
    print("データを読み込み中...")
    feature_descriptions = loader.load_feature_descriptions()
    gpt_responses = loader.load_gpt_responses(target_features)
    
    if not feature_descriptions or not gpt_responses:
        print("データの読み込みに失敗しました")
        return
    
    print(f"特徴記述: {len(feature_descriptions)}件")
    print(f"GPTレスポンス: {len(gpt_responses)}件")
    print()
    
    # 評価結果を格納するリスト
    results = []
    
    # 各特徴について類似度評価を実行
    print("類似度評価を実行中...")
    for feature_num in target_features:
        if feature_num not in gpt_responses or feature_num not in feature_descriptions:
            print(f"Feature {feature_num}: データが不足しています")
            continue
            
        # テキストを取得
        text_a = gpt_responses[feature_num]  # GPTレスポンス
        text_b = feature_descriptions[feature_num]  # 元の特徴記述
        
        print(f"\\nFeature {feature_num}:")
        print(f"GPTレスポンス: \"{text_a}\"")
        print(f"元の特徴記述: \"{text_b}\"")
        
        # 類似度計算
        bert_sim, bleu_sim = evaluator.evaluate_similarity(text_a, text_b)
        
        print(f"BERT類似度: {bert_sim:.4f}")
        print(f"BLEU類似度: {bleu_sim:.4f}")
        
        # 結果を保存
        results.append({
            'feature_number': feature_num,
            'gpt_response': text_a,
            'original_description': text_b,
            'bert_similarity': bert_sim,
            'bleu_similarity': bleu_sim
        })
    
    # 結果をJSONファイルに保存
    output_path = Path(base_path) / "src/analysis/experiments/2025/05/27/similarity_evaluation_results.json"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\\n結果を保存しました: {output_path}")
    except Exception as e:
        print(f"結果保存エラー: {e}")
    
    # 結果の統計情報を表示
    print("\\n=== 評価結果サマリー ===")
    if results:
        bert_scores = [r['bert_similarity'] for r in results]
        bleu_scores = [r['bleu_similarity'] for r in results]
        
        print(f"BERT類似度 - 平均: {np.mean(bert_scores):.4f}, 標準偏差: {np.std(bert_scores):.4f}")
        print(f"BLEU類似度 - 平均: {np.mean(bleu_scores):.4f}, 標準偏差: {np.std(bleu_scores):.4f}")
        
        # CSVファイルとしても保存
        df_results = pd.DataFrame(results)
        csv_output_path = output_path.with_suffix('.csv')
        df_results.to_csv(csv_output_path, index=False, encoding='utf-8')
        print(f"CSV結果を保存しました: {csv_output_path}")


if __name__ == "__main__":
    main()