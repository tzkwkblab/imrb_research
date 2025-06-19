#!/usr/bin/env python3
"""
SemEval ABSA対比因子生成実験のBERT/BLEUスコア計算スクリプト
"""
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

RESULTS_PATH = Path(__file__).parent / "results/semeval_contrast_experiment_results_20250613_143104.json"

# --- 類似度計算クラス ---
class TextSimilarityEvaluator:
    def __init__(self):
        self.sentence_bert = SentenceTransformer('all-MiniLM-L6-v2')
        self.smoothing = SmoothingFunction().method1

    def calculate_bert_similarity(self, text_a: str, text_b: str) -> float:
        emb = self.sentence_bert.encode([text_a, text_b])
        sim = cosine_similarity([emb[0]], [emb[1]])[0][0]
        return float((sim + 1) / 2)  # -1~1→0~1

    def calculate_bleu_similarity(self, text_a: str, text_b: str) -> float:
        ref = text_a.lower().split()
        cand = text_b.lower().split()
        return float(sentence_bleu([ref], cand, smoothing_function=self.smoothing))

# --- メイン処理 ---
def main():
    with open(RESULTS_PATH, encoding='utf-8') as f:
        data = json.load(f)
    results = data['results']

    rows = []
    evaluator = TextSimilarityEvaluator()

    for r in results:
        feature = r['feature']
        gpt_response = r['gpt_response'].strip('"')
        domain = r['domain']
        shot = r['shot_count']
        bert = evaluator.calculate_bert_similarity(feature, gpt_response)
        bleu = evaluator.calculate_bleu_similarity(feature, gpt_response)
        rows.append({
            'domain': domain,
            'feature': feature,
            'shot': shot,
            'gpt_response': gpt_response,
            'bert_similarity': bert,
            'bleu_score': bleu
        })

    df = pd.DataFrame(rows)
    print("\n=== 類似度スコア集計 ===")
    print(df[['domain','feature','shot','bert_similarity','bleu_score']].to_string(index=False))
    print("\n--- 平均値 ---")
    print(df[['bert_similarity','bleu_score']].mean())

    # CSV保存
    out_path = Path(__file__).parent / "semeval_absa_similarity_scores.csv"
    df.to_csv(out_path, index=False)
    print(f"\nCSV出力: {out_path}")

if __name__ == "__main__":
    main() 