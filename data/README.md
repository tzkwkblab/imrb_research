# データディレクトリ構造

このプロジェクトのデータ管理構造について説明します。

## ディレクトリ構造

```
data/
├── external/                          # 外部データセット（読み取り専用）
│   └── amazon-product-reviews/        # Amazon商品レビューデータセット
│       └── kaggle-bittlingmayer/      # Kaggle - bittlingmayer作者
│           ├── v1.0_2025-06-09/       # バージョン_ダウンロード日
│           │   ├── reviews_Electronics_5.json.gz
│           │   ├── aspect-labeled/
│           │   └── dataset_info.json
│           └── current -> v1.0_2025-06-09/  # 最新版へのリンク
├── processed/                         # 前処理済みデータ
│   └── amazon-reviews/
│       ├── cleaned/                   # クリーニング済み
│       ├── sampled/                   # サンプリング済み
│       └── feature-extracted/        # 特徴抽出済み
├── analysis-workspace/               # 分析作業用
├── cache/                           # 一時キャッシュファイル
└── raw/                            # 旧構造（非推奨）
```

## 使用方法

### 外部データアクセス

```python
# 最新版へのアクセス
current_data = "data/external/amazon-product-reviews/kaggle-bittlingmayer/current/"

# 特定バージョンへのアクセス
v1_data = "data/external/amazon-product-reviews/kaggle-bittlingmayer/v1.0_2025-06-09/"
```

### 処理済みデータの保存

```python
# クリーニング済みデータ
processed_path = "data/processed/amazon-reviews/cleaned/"

# サンプリング済みデータ
sampled_path = "data/processed/amazon-reviews/sampled/"
```

## データセット情報

各外部データセットには `dataset_info.json` ファイルが含まれており、以下の情報が記録されています：

- データセット名と説明
- ソース（Kaggle、HuggingFace 等）
- ダウンロード日とバージョン
- ファイル情報（サイズ、形式、レコード数）
- 使用上の注意点
- ライセンス情報

## 命名規則

### バージョニング

- `v{major}.{minor}_{YYYY-MM-DD}` 形式
- 例: `v1.0_2025-06-09`

### ディレクトリ名

- 英語、小文字、ハイフン区切り
- 例: `amazon-product-reviews`, `kaggle-bittlingmayer`

## 注意事項

1. **external/** ディレクトリのデータは直接編集禁止
2. 処理済みデータは **processed/** ディレクトリに保存
3. 一時ファイルは **cache/** ディレクトリを使用
4. 新しいデータセット追加時は構造に従って整理

## 外部データセット一覧（2025 年 6 月現在）

| ディレクトリ名              | 内容・特徴                                      |
| --------------------------- | ----------------------------------------------- |
| amazon-product-reviews      | Amazon 商品レビュー（Kaggle: bittlingmayer 等） |
| absa-review-dataset         | ABSA（アスペクトベース感情分析）用レビュー      |
| semeval-absa                | SemEval 公式 ABSA タスク用データ                |
| steam-review-aspect-dataset | Steam ゲームレビューのアスペクト多ラベルデータ  |

- それぞれバージョン管理・current リンク・dataset_info.json 付き
- サブディレクトリ例：`kaggle-bittlingmayer/`, `pyabsa-integrated/`, `v1.0_YYYY-MM-DD/` など
