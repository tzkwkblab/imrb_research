# Retrieved Concepts Dataset (COCO Captions)

本データセットは、ファルヌシュさん（共同実験者）から提供された、MS-COCO 2017 train splitの画像キャプションデータを、300個の潜在コンセプトに対して類似度順に取得したものです。

## データセット概要

- **データソース**: MS-COCO 2017 train split
- **類似度計算**: CLIP (ViT-B/32) コサイン類似度
- **コンセプト数**: 300個の潜在コンセプト
- **取得数**: 各コンセプトあたりTop-100とBottom-100の2セット

## データ構造

### Top-100データセット (`retrieved_dataset_100.json`)

各コンセプトに対して、最も類似度が高い100枚の画像とそのキャプションを取得したデータセットです。

### Bottom-100データセット (`retrieved_dataset_bottom_100.json`)

各コンセプトに対して、最も類似度が低い（最も異なる）100枚の画像とそのキャプションを取得したデータセットです。

### データ形式

```json
{
  "timestamp": "2025-11-07T00:20:23.352663+00:00",
  "k": 100,
  "results": [
    {
      "concept_id": 0,
      "topk": [
        {
          "rank": 1,
          "score": 0.85,
          "path": "data/coco/train2017/000000081860.jpg",
          "captions": [
            "A group of business people pose for a picture.",
            "..."
          ]
        }
      ],
      "bottomk": [
        {
          "rank": 1,
          "score": 0.15,
          "path": "data/coco/train2017/000000081860.jpg",
          "captions": [
            "A group of business people pose for a picture.",
            "..."
          ]
        }
      ]
    }
  ]
}
```

### フィールド説明

- `concept_id`: コンセプトID（0-299）
- `rank`: ランク（Top-100では1が最も類似、Bottom-100では1が最も非類似）
- `score`: CLIP類似度スコア（0.0-1.0）
- `path`: COCO画像ファイルパス
- `captions`: 人間がアノテーションした5つのキャプション

## データ配置

```
data/external/retrieved-concepts/farnoosh/
├── current -> v1.0_2025-10-29/
└── v1.0_2025-10-29/
    ├── dataset_info.json
    ├── retrieved_dataset_100.json (Top-100)
    └── retrieved_dataset_bottom_100.json (Bottom-100)
```

## 実験での使用方法

### データセットID

実験パイプラインでは `retrieved_concepts` として参照します。

### アスペクト名

各コンセプトは `concept_0`, `concept_1`, ..., `concept_299` として参照されます。

### 推奨分割タイプ

**`aspect_vs_bottom100`** を推奨します。

この分割タイプでは：
- **グループA**: 対象コンセプトのTop-100から抽出（最も類似度が高い画像のキャプション）
- **グループB**: 対象コンセプトのBottom-100から抽出（最も類似度が低い画像のキャプション）

これにより、コンセプトに特徴的な要素をより明確に抽出できます。

### 実行例

#### 対話型スクリプト

```bash
bash scripts/run_interactive_experiment.sh
# データセット: retrieved_concepts を選択
# アスペクト: concept_0 を選択
# 分割タイプ: aspect_vs_bottom100 (デフォルト)
```

#### コマンドライン実行

```bash
python src/analysis/experiments/2025/10/10/run_experiment.py \
  --dataset retrieved_concepts \
  --aspect concept_0 \
  --group-size 10 \
  --split-type aspect_vs_bottom100
```

### メタデータ

各レコードには以下のメタデータが含まれます：

- `concept_id`: コンセプトID
- `image_path`: 画像ファイルパス
- `score`: 類似度スコア
- `rank`: ランク
- `source_type`: `"top100"` または `"bottom100"`

## 注意事項

- Top-100とBottom-100は別々のJSONファイルに格納されていますが、ローダーが自動的に両方を読み込みます
- 各画像には5つのキャプションが含まれているため、1コンセプトあたり最大500件（Top-100） + 500件（Bottom-100） = 1000件のレコードが生成されます
- データセットは大容量（361,506行）のため、ストリーミングパーサーを使用してメモリ効率的に読み込みます

## 関連ドキュメント

- [実験スクリプト使い方ガイド](../experiments/guides/experiment-script-guide.md)
- [retrieved_concepts実験手順](../experiments/playbooks/retrieved-concepts-experiment-guide.md)
- [統一パイプラインREADME](../../../src/analysis/experiments/2025/10/10/README.md)

