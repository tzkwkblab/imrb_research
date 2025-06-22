#!/usr/bin/env python3
"""
BLEUスコア計算ツール

シンプルなBLEUスコア計算機能
# 使用例
score = calculate_bleu_score(
    "The quick brown fox jumps over the lazy dog",
    "A quick brown fox jumps over the lazy dog"
)
"""

import argparse
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
import nltk

# 必要なデータをダウンロード
try:
    nltk.download('punkt', quiet=True)
except:
    pass


def calculate_bleu_score(reference: str, hypothesis: str) -> float:
    """
    BLEUスコアを計算
    
    Args:
        reference: 参照テキスト
        hypothesis: 候補テキスト
        
    Returns:
        BLEUスコア (0.0-1.0)
    """
    if not reference.strip() or not hypothesis.strip():
        return 0.0
    
    ref_tokens = reference.lower().split()
    hyp_tokens = hypothesis.lower().split()
    
    smoothing = SmoothingFunction().method1
    return sentence_bleu([ref_tokens], hyp_tokens, smoothing_function=smoothing)


def main():
    parser = argparse.ArgumentParser(description='BLEUスコア計算')
    parser.add_argument('reference', help='参照テキスト')
    parser.add_argument('hypothesis', help='候補テキスト')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細出力')
    
    args = parser.parse_args()
    
    score = calculate_bleu_score(args.reference, args.hypothesis)
    
    if args.verbose:
        print(f"参照: {args.reference}")
        print(f"候補: {args.hypothesis}")
        print(f"BLEUスコア: {score:.4f}")
    else:
        print(f"{score:.4f}")


if __name__ == "__main__":
    main()
