import argparse
import itertools
import json
from pathlib import Path
from typing import List
from transformers import BertTokenizer, BertModel
import torch
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
import numpy as np

# BERT埋め込み取得用
class BertEmbedder:
    def __init__(self, model_name='bert-base-uncased'):
        self.tokenizer = BertTokenizer.from_pretrained(model_name)
        self.model = BertModel.from_pretrained(model_name)
        self.model.eval()

    def get_embedding(self, text: str):
        with torch.no_grad():
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=64)
            outputs = self.model(**inputs)
            # [CLS]トークンのベクトルを使う
            return outputs.last_hidden_state[0, 0, :].numpy()

# BERTコサイン類似度
def bert_cosine_similarity(text1, text2, embedder):
    v1 = embedder.get_embedding(text1)
    v2 = embedder.get_embedding(text2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

# BLEUスコア
def bleu_score(text1, text2):
    ref = text1.split()
    hyp = text2.split()
    smoothie = SmoothingFunction().method1
    return sentence_bleu([ref], hyp, smoothing_function=smoothie)

# 特徴リスト自動抽出
def extract_features_from_json(json_path):
    with open(json_path) as f:
        data = json.load(f)
    features = []
    for domain, feats in data['experiment_info']['domain_features'].items():
        features.extend(feats)
    return list(sorted(set(features)))


def main():
    parser = argparse.ArgumentParser(description='特徴記述間のBERT/BLEU類似度ベースライン計算')
    parser.add_argument('--features', nargs='+', default=None, help='特徴リスト（省略時はjsonから自動抽出）')
    parser.add_argument('--json', type=str, default='src/analysis/experiments/2025/06/12/results/semeval_contrast_experiment_results_20250613_143104.json', help='特徴リスト抽出用jsonファイル')
    parser.add_argument('--output', type=str, default='baseline_similarity_results_semeval.json', help='出力ファイル名')
    args = parser.parse_args()

    # 特徴リスト取得
    if args.features is not None:
        features = args.features
    else:
        features = extract_features_from_json(args.json)
    print(f"特徴リスト: {features}")

    # 全ペア生成
    pairs = list(itertools.combinations(features, 2))
    print(f"ペア数: {len(pairs)}")

    # BERT埋め込み
    embedder = BertEmbedder()

    bert_scores = []
    bleu_scores = []
    for f1, f2 in pairs:
        bert = bert_cosine_similarity(f1, f2, embedder)
        bleu = bleu_score(f1, f2)
        bert_scores.append(bert)
        bleu_scores.append(bleu)
        print(f"{f1} <-> {f2}: BERT={bert:.4f}, BLEU={bleu:.4f}")

    # 統計
    bert_mean = float(np.mean(bert_scores))
    bleu_mean = float(np.mean(bleu_scores))
    result = {
        'features': features,
        'bert_scores': bert_scores,
        'bleu_scores': bleu_scores,
        'bert_mean': bert_mean,
        'bleu_mean': bleu_mean,
        'num_pairs': len(pairs)
    }
    print(f"\nBERT類似度平均: {bert_mean:.4f}")
    print(f"BLEUスコア平均: {bleu_mean:.4f}")

    # 保存
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"結果を {args.output} に保存しました")

if __name__ == '__main__':
    main() 