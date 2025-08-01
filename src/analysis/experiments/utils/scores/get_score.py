#!/usr/bin/env python3
"""
テキスト類似度スコア計算

二つのテキストからBERTスコアとBLEUスコアを計算する
# 使用例（単一）
bert_score, bleu_score = calculate_scores("text1", "text2")

# 使用例（バッチ）
pairs = [("text1", "text2"), ("text3", "text4")]
scores_per_pair = calculate_scores_batch(pairs)
→ [(bert_score_pair1=0.9, bleu_score_pair1=0.8), 
    (bert_score_pair2=0.7, bleu_score_pair2=0.6)]

# 使用例（1対多）
scores_per_candidate = calculate_one_to_many(
    "text1",
    ["text2", "text3", "text4"]
)
→ [(bert_score_candidate1=0.9, bleu_score_candidate1=0.8), 
    (bert_score_candidate2=0.7, bleu_score_candidate2=0.6), 
    (bert_score_candidate3=0.5, bleu_score_candidate3=0.4)]
"""

from typing import Tuple, List
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    import nltk
except ImportError as e:
    print(f"必要なライブラリがインストールされていません: {e}")
    print("pip install sentence-transformers scikit-learn nltk")
    exit(1)

# NLTK データのダウンロード
try:
    nltk.download('punkt', quiet=True)
except:
    pass

# グローバルモデル（再利用のため）
_model = None
_smoothing = None


def _get_model():
    """モデルの遅延読み込み（再利用）"""
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def _get_smoothing():
    """スムージング関数の遅延読み込み（再利用）"""
    global _smoothing
    if _smoothing is None:
        _smoothing = SmoothingFunction().method1
    return _smoothing


def calculate_scores(text_a: str, text_b: str) -> Tuple[float, float]:
    """
    二つのテキストのBERTスコアとBLEUスコアを計算
    
    Args:
        text_a: テキストA
        text_b: テキストB
        
    Returns:
        (BERTスコア, BLEUスコア) のタプル
    """
    # BERTスコア計算（モデル再利用）
    model = _get_model()
    embeddings = model.encode([text_a, text_b])
    bert_similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    bert_score = float((bert_similarity + 1) / 2)
    
    # BLEUスコア計算
    if not text_a.strip() or not text_b.strip():
        bleu_score = 0.0
    else:
        ref_tokens = text_a.lower().split()
        hyp_tokens = text_b.lower().split()
        smoothing = _get_smoothing()
        bleu_score = sentence_bleu([ref_tokens], hyp_tokens, smoothing_function=smoothing)
    
    return bert_score, bleu_score


def calculate_scores_batch(text_pairs: List[Tuple[str, str]]) -> List[Tuple[float, float]]:
    """
    大量のテキストペアのスコアを効率的に計算
    
    Args:
        text_pairs: [(text_a1, text_b1), (text_a2, text_b2), ...] のリスト
        
    Returns:
        [(bert_score1, bleu_score1), (bert_score2, bleu_score2), ...] のリスト
    """
    if not text_pairs:
        return []
    
    # 全テキストを一度にエンコード（効率化）
    model = _get_model()
    all_texts = []
    for text_a, text_b in text_pairs:
        all_texts.extend([text_a, text_b])
    
    # バッチエンコーディング
    all_embeddings = model.encode(all_texts)
    
    # スムージング関数（再利用）
    smoothing = _get_smoothing()
    
    results = []
    for i, (text_a, text_b) in enumerate(text_pairs):
        # BERTスコア計算
        emb_a = all_embeddings[i * 2]
        emb_b = all_embeddings[i * 2 + 1]
        bert_similarity = cosine_similarity([emb_a], [emb_b])[0][0]
        bert_score = float((bert_similarity + 1) / 2)
        
        # BLEUスコア計算
        if not text_a.strip() or not text_b.strip():
            bleu_score = 0.0
        else:
            ref_tokens = text_a.lower().split()
            hyp_tokens = text_b.lower().split()
            bleu_score = sentence_bleu([ref_tokens], hyp_tokens, smoothing_function=smoothing)
        
        results.append((bert_score, bleu_score))
    
    return results


def calculate_one_to_many(reference_text: str, candidate_texts: List[str]) -> List[Tuple[float, float]]:
    """
    1つの参照テキストと複数の候補テキストを比較
    
    Args:
        reference_text: 参照テキスト
        candidate_texts: 候補テキストのリスト
        
    Returns:
        各候補との(BERTスコア, BLEUスコア)のリスト
    """
    pairs = [(reference_text, candidate) for candidate in candidate_texts]
    return calculate_scores_batch(pairs)


def calculate_scores_with_descriptions(
    text_a: str, 
    text_b: str, 
    aspect_manager=None,
    use_descriptions: bool = False
) -> Tuple[float, float]:
    """
    アスペクト説明文オプション付きスコア計算
    
    Args:
        text_a: テキストA（通常はアスペクト名）
        text_b: テキストB（LLM応答）
        aspect_manager: アスペクト説明文管理クラス
        use_descriptions: 説明文を使用するかどうか
        
    Returns:
        (BERTスコア, BLEUスコア) のタプル
    """
    if use_descriptions and aspect_manager and aspect_manager.has_descriptions():
        # アスペクト名を説明文に変換
        text_a = aspect_manager.get_description(text_a)
    
    return calculate_scores(text_a, text_b)


def main():
    """テスト"""
    print("=== 単一比較テスト ===")
    bert_score, bleu_score = calculate_scores("技術的な詳細", "Includes technical details")
    print(f"BERTスコア: {bert_score:.4f}, BLEUスコア: {bleu_score:.4f}")
    
    print("\n=== バッチ比較テスト ===")
    test_pairs = [
        ("技術的な詳細", "Includes technical details"),
        ("競合製品との比較", "Contains comparisons"),
        ("全く関係ない話", "Completely unrelated topic"),
    ]
    
    results = calculate_scores_batch(test_pairs)
    for i, ((text_a, text_b), (bert_score, bleu_score)) in enumerate(zip(test_pairs, results), 1):
        print(f"ペア {i}: BERT={bert_score:.4f}, BLEU={bleu_score:.4f}")
        print(f"  A: {text_a}")
        print(f"  B: {text_b}")
    
    print("\n=== 1対多比較テスト ===")
    reference = "技術的な詳細について"
    candidates = ["Technical details", "Product specs", "User manual", "Random text"]
    
    results = calculate_one_to_many(reference, candidates)
    for candidate, (bert_score, bleu_score) in zip(candidates, results):
        print(f"{candidate}: BERT={bert_score:.4f}, BLEU={bleu_score:.4f}")


if __name__ == "__main__":
    main()
