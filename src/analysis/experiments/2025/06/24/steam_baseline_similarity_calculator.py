#!/usr/bin/env python3
"""
Steam Review Aspect Dataset ベースライン類似度計算
8アスペクト名間のBERT/BLEU類似度ベースライン計算
"""

import argparse
import itertools
import json
from pathlib import Path
from typing import List
from transformers import BertTokenizer, BertModel
import torch
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
import numpy as np

class BertEmbedder:
    """BERT埋め込み取得用クラス"""
    def __init__(self, model_name='bert-base-uncased'):
        self.tokenizer = BertTokenizer.from_pretrained(model_name)
        self.model = BertModel.from_pretrained(model_name)
        self.model.eval()

    def get_embedding(self, text: str):
        """テキストのBERT埋め込みを取得"""
        with torch.no_grad():
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=64)
            outputs = self.model(**inputs)
            # [CLS]トークンのベクトルを使う
            return outputs.last_hidden_state[0, 0, :].numpy()

def bert_cosine_similarity(text1, text2, embedder):
    """BERTコサイン類似度を計算"""
    v1 = embedder.get_embedding(text1)
    v2 = embedder.get_embedding(text2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

def bleu_score(text1, text2):
    """BLEUスコアを計算"""
    ref = text1.split()
    hyp = text2.split()
    smoothie = SmoothingFunction().method1
    return sentence_bleu([ref], hyp, smoothing_function=smoothie)

def main():
    parser = argparse.ArgumentParser(description='Steam Review Aspectベースライン類似度計算')
    parser.add_argument('--output', type=str, default='steam_baseline_similarity_results.json', help='出力ファイル名')
    args = parser.parse_args()

    # Steam Review Aspect Dataset の8アスペクト
    aspects = [
        'recommended', 'story', 'gameplay', 'visual', 
        'audio', 'technical', 'price', 'suggestion'
    ]
    
    print(f"アスペクトリスト: {aspects}")

    # 全ペア生成
    pairs = list(itertools.combinations(aspects, 2))
    print(f"ペア数: {len(pairs)}")

    # BERT埋め込み
    print("BERT埋め込みモデルを読み込み中...")
    embedder = BertEmbedder()

    bert_scores = []
    bleu_scores = []
    
    print("\n類似度計算中...")
    for f1, f2 in pairs:
        bert = bert_cosine_similarity(f1, f2, embedder)
        bleu = bleu_score(f1, f2)
        bert_scores.append(bert)
        bleu_scores.append(bleu)
        print(f"{f1} <-> {f2}: BERT={bert:.4f}, BLEU={bleu:.4f}")

    # 統計
    bert_mean = float(np.mean(bert_scores))
    bleu_mean = float(np.mean(bleu_scores))
    bert_std = float(np.std(bert_scores))
    bleu_std = float(np.std(bleu_scores))
    
    result = {
        'dataset': 'Steam Review Aspect Dataset',
        'aspects': aspects,
        'pair_details': [
            {
                'aspect1': pair[0],
                'aspect2': pair[1], 
                'bert_score': bert_scores[i],
                'bleu_score': bleu_scores[i]
            }
            for i, pair in enumerate(pairs)
        ],
        'summary_statistics': {
            'bert_mean': bert_mean,
            'bleu_mean': bleu_mean,
            'bert_std': bert_std,
            'bleu_std': bleu_std,
            'num_pairs': len(pairs),
            'num_aspects': len(aspects)
        }
    }
    
    print(f"\n=== ベースライン統計サマリー ===")
    print(f"BERT類似度平均: {bert_mean:.4f} (±{bert_std:.4f})")
    print(f"BLEUスコア平均: {bleu_mean:.4f} (±{bleu_std:.4f})")
    print(f"アスペクト数: {len(aspects)}")
    print(f"ペア数: {len(pairs)}")

    # 保存
    output_path = Path(args.output)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n結果を {output_path} に保存しました")
    
    return result

if __name__ == "__main__":
    main() 