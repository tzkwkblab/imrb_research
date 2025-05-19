import os
import glob
import csv
import re
from pathlib import Path

INPUT_DIR = Path("src/data/human_validated_reviews/")
OUTPUT_CSV = Path("src/analysis/experiments/2025/05/15/processed_reviews.csv")
FEATURE_COUNT = 20


def parse_review_md(md_path):
    """
    1つのmdファイルから必要な情報を抽出し、dictで返す。
    """
    with md_path.open('r', encoding='utf-8') as f:
        text = f.read()

    # review_id
    review_id = re.search(r'# レビュー ?ID: ?(\d+)', text)
    review_id = review_id.group(1) if review_id else ''

    # product_id
    product_id = re.search(r'商品 ?ID: ?([A-Z0-9]+)', text)
    product_id = product_id.group(1) if product_id else ''

    # rating
    rating = re.search(r'評価点: ?([0-9.]+)', text)
    rating = rating.group(1) if rating else ''

    # title
    title = re.search(r'タイトル: ?(.+)', text)
    title = title.group(1).strip() if title else ''

    # review_text（原文）
    review_text = re.search(r'### 原文\s*\n\s*([\s\S]+?)\s*\n\s*### 日本語訳', text)
    if review_text:
        # 改行を空白に置換し、連続する空白を1つにまとめる
        review_text = review_text.group(1).strip()
        review_text = re.sub(r'\s+', ' ', review_text)

    else:
        review_text = ''

    # 各特徴の情報を抽出
    features = {}
    for i in range(1, FEATURE_COUNT + 1):
        # 特徴iのブロックを抽出
        pattern = rf'### 特徴 ?{i}\s*\n[\s\S]+?- GPT ?の判定：([01])\s*\n- \[ ?([ xX])? ?\] 判定が不適切な場合はチェック\s*\n[\s\S]+?#### コメント\s*\n```\s*([\s\S]*?)```'
        m = re.search(pattern, text)
        if m:
            gpt_value = int(m.group(1))
            checked = 1 if m.group(2) else 0
            comment = m.group(3).strip()
            # 最終判定値: チェックがONなら値を反転、OFFならGPT値
            final_value = 1 - gpt_value if checked else gpt_value
        else:
            # 別のパターンも試す（フォーマットのバリエーション対応）
            alt_pattern = rf'### 特徴 ?{i}[\s\S]+?GPT ?の判定：([01])[\s\S]+?\[ ?([ xX])? ?\] 判定が不適切な場合はチェック[\s\S]+?コメント\s*\n```\s*([\s\S]*?)```'
            m = re.search(alt_pattern, text)
            if m:
                gpt_value = int(m.group(1))
                checked = 1 if m.group(2) else 0
                comment = m.group(3).strip()
                final_value = 1 - gpt_value if checked else gpt_value
            else:
                gpt_value = ''
                checked = ''
                comment = ''
                final_value = ''
        
        features[i] = {
            'gpt_judgement': gpt_value,
            'human_check': checked,
            'human_comment': comment,
            'final': final_value
        }

    # 返却dict
    row = {
        'review_id': review_id,
        'product_id': product_id,
        'rating': rating,
        'title': title,
        'review_text': review_text,
    }
    for i in range(1, FEATURE_COUNT + 1):
        row[f'gpt_judgement_feature_{i}'] = features[i]['gpt_judgement']
        row[f'human_check_feature_{i}'] = features[i]['human_check']
        row[f'human_comment_feature_{i}'] = features[i]['human_comment']
        row[f'final_feature_{i}'] = features[i]['final']
    return row


def main():
    input_dir = INPUT_DIR
    md_files = sorted(input_dir.glob('validated_review_*.md'))
    print(f'Found {len(md_files)} files.')

    rows = []
    for md_path in md_files:
        row = parse_review_md(md_path)
        rows.append(row)

    # カラム名を定義
    fieldnames = ['review_id', 'product_id', 'rating', 'title', 'review_text']
    for i in range(1, FEATURE_COUNT + 1):
        fieldnames.append(f'gpt_judgement_feature_{i}')
        fieldnames.append(f'human_check_feature_{i}')
        fieldnames.append(f'human_comment_feature_{i}')
        fieldnames.append(f'final_feature_{i}')

    output_path = OUTPUT_CSV
    with output_path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f'CSV出力完了: {output_path}')


if __name__ == '__main__':
    main() 