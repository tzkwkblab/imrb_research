#!/usr/bin/env python3
"""
BERTスコア計算ユーティリティ

二つのテキストからBERT類似度を計算する
# 使用例
score = calculate_bert_score(
    "The quick brown fox jumps over the lazy dog",
    "A quick brown fox jumps over the lazy dog"
)
"""

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError as e:
    print(f"必要なライブラリがインストールされていません: {e}")
    print("pip install sentence-transformers scikit-learn")
    exit(1)


def calculate_bert_score(text_a: str, text_b: str) -> float:
    """
    二つのテキストのBERT類似度を計算
    
    Returns:
        0から1のBERT類似度スコア
    """
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode([text_a, text_b])
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return float((similarity + 1) / 2)


def main():
    """テスト"""
    test_cases = [
        ("技術的な詳細", "Includes technical details"),
        ("競合製品との比較", "Contains comparisons"),
        ("全く関係ない話", "Completely unrelated topic"),
    ]
    
    for i, (text_a, text_b) in enumerate(test_cases, 1):
        score = calculate_bert_score(text_a, text_b)
        print(f"テスト {i}: {score:.4f}")
        print(f"  A: {text_a}")
        print(f"  B: {text_b}")


if __name__ == "__main__":
    main()
