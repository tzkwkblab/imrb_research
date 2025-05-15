"""
レビュー特徴の人間評価用mdファイルを生成するスクリプト
DeepL APIを使用して翻訳機能を追加

入力：all_results.json
出力：各レビューの評価用mdファイル
"""

import json
import os
from pathlib import Path
import pandas as pd
import deepl
from time import sleep
from dotenv import load_dotenv

def init_translator():
    """DeepL APIのトランスレータを初期化"""
    load_dotenv()  # .envファイルから環境変数を読み込む
    auth_key = os.getenv("DEEPL_API_KEY")
    if not auth_key:
        raise ValueError("環境変数 DEEPL_API_KEY が設定されていません")
    return deepl.Translator(auth_key)

def translate_text(translator, text, retries=3, delay=1):
    """テキストを翻訳（リトライ機能付き）"""
    for i in range(retries):
        try:
            result = translator.translate_text(text, target_lang="JA")
            return result.text
        except deepl.exceptions.DeepLException as e:
            if i == retries - 1:  # 最後のリトライでも失敗
                print(f"翻訳エラー: {e}")
                return f"翻訳エラー: {e}"
            sleep(delay)  # リトライ前に待機
    return "翻訳に失敗しました"

def load_feature_definitions():
    """特徴定義を読み込む"""
    current_dir = Path(__file__).parent
    features_csv = current_dir.parent.parent.parent / "review_features.csv"
    features_df = pd.read_csv(features_csv)
    return {
        str(row['feature_id']): row['feature_description']
        for _, row in features_df.iterrows()
    }

def generate_review_md(review_data, feature_definitions, translator, output_dir):
    """1つのレビューに対する評価用mdファイルを生成"""
    review_id = review_data['review_id']
    output_path = output_dir / f"review_{review_id:03d}.md"
    
    # 既に生成済みの場合はスキップ
    if output_path.exists():
        return None
    
    # レビュー本文の翻訳
    review_translation = translate_text(translator, review_data['review_text'])
    
    # mdファイルの内容を生成
    content = f"""# レビューID: {review_id}
評価点: {review_data['rating']}
商品ID: {review_data['product_id']}
タイトル: {review_data['summary']}

## レビュー本文
### 原文
{review_data['review_text']}

### 日本語訳
{review_translation}

## 特徴判定
"""
    
    # 各特徴の判定結果を追加
    features = review_data['analysis_result']['features']
    stability = review_data['analysis_result']['stability']
    
    for feature_id, value in features.items():
        feature_desc = feature_definitions[feature_id]
        feature_translation = translate_text(translator, feature_desc)
        stab = stability[feature_id]
        content += f"""
### 特徴{feature_id}
#### 説明
- 英語：{feature_desc}
- 日本語：{feature_translation}

#### 判定
- GPTの判定：{value}
- [ ] 判定が不適切な場合はチェック

#### コメント
```
判定が不適切な場合、その理由や気づきを記入
```

"""
    
    # ファイルに保存
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return output_path

def main(start_review_id=None):
    # 入出力パスの設定
    current_dir = Path(__file__).parent
    input_file = current_dir / "all_results.json"
    output_dir = current_dir / "human_validation"
    output_dir.mkdir(exist_ok=True)
    
    # DeepL APIの初期化
    translator = init_translator()
    
    # 特徴定義の読み込み
    feature_definitions = load_feature_definitions()
    
    # 全レビューデータの読み込み
    with open(input_file, 'r', encoding='utf-8') as f:
        reviews_data = json.load(f)
    
    # 開始位置の設定
    if start_review_id is not None:
        reviews_data = [r for r in reviews_data if r['review_id'] >= start_review_id]
    
    # 各レビューに対してmdファイルを生成
    total = len(reviews_data)
    generated_count = 0
    
    for i, review_data in enumerate(reviews_data, 1):
        output_path = generate_review_md(review_data, feature_definitions, translator, output_dir)
        if output_path:  # 新しく生成された場合のみカウント
            generated_count += 1
            print(f"生成完了 ({i}/{total}): {output_path}")
            
            # API制限を考慮して、10件ごとに少し待機
            if generated_count % 10 == 0:
                sleep(1)
    
    # 使用量の確認
    usage = translator.get_usage()
    if hasattr(usage, 'character'):
        print(f"\n翻訳API使用量: {usage.character.count} / {usage.character.limit} 文字")
    else:
        print("\n翻訳API使用量の取得に失敗しました")
    print(f"\n新規生成ファイル数: {generated_count}")
    print(f"出力ディレクトリ: {output_dir}")

if __name__ == "__main__":
    main(start_review_id=114)  # review_113.mdの次から開始 