# COCO データセット実験パラメータ確認

## 実験概要

- **データセット**: Retrieved Concepts (COCO Captions)
- **実験数**: 5 実験
- **コンセプト**: concept_0, concept_1, concept_2, concept_10, concept_50

## 指定パラメータ

| パラメータ         | 指定値      | 設定ファイルでの値               | 確認 |
| ------------------ | ----------- | -------------------------------- | ---- |
| **group_size**     | 100         | 100                              | ✅   |
| **temperature**    | 0           | 0.0 (`paramaters.yml`)           | ✅   |
| **few_shot**       | 0           | 0                                | ✅   |
| **LLM 評価**       | なし        | `use_llm_evaluation: false`      | ✅   |
| **モデル**         | gpt-4o-mini | gpt-4o-mini                      | ✅   |
| **分割タイプ**     | -           | `aspect_vs_bottom100`            | ✅   |
| **アスペクト記述** | -           | `use_aspect_descriptions: false` | ✅   |

## 実験マトリックス設定

### 追加された実験（5 件）

1. **retrieved_concepts_concept_0_0_4omini_word**

   - dataset: `retrieved_concepts`
   - aspect: `concept_0`
   - few_shot: `0`
   - gpt_model: `gpt-4o-mini`
   - group_size: `100`
   - split_type: `aspect_vs_bottom100`
   - use_llm_evaluation: `false`
   - use_aspect_descriptions: `false`

2. **retrieved_concepts_concept_1_0_4omini_word**

   - 同様の設定（aspect: `concept_1`）

3. **retrieved_concepts_concept_2_0_4omini_word**

   - 同様の設定（aspect: `concept_2`）

4. **retrieved_concepts_concept_10_0_4omini_word**

   - 同様の設定（aspect: `concept_10`）

5. **retrieved_concepts_concept_50_0_4omini_word**
   - 同様の設定（aspect: `concept_50`）

## 設定ファイル確認

### 1. パラメータ設定 (`src/analysis/experiments/utils/config/paramaters.yml`)

```yaml
model: gpt-4o-mini
temperature: 0.0 # ← 指定通り0に設定
max_tokens: 2000
```

### 2. データセット設定 (`src/analysis/experiments/utils/datasetManager/configs/dataset_configs.yaml`)

```yaml
retrieved_concepts:
  path: "/Users/seinoshun/imrb_research/data/external/retrieved-concepts/farnoosh/current"
  domain: "vision"
  language: "en"
```

### 3. 実験マトリックス (`実験マトリックス.json`)

- 総実験数: 41（メイン 36 + サブ 5）
- COCO 実験: 5 件追加済み

## データセット情報

- **データソース**: MS-COCO 2017 train split
- **類似度計算**: CLIP (ViT-B/32) コサイン類似度
- **各コンセプトのデータ数**:
  - Top-100: 100 枚 × 5 キャプション = 500 件
  - Bottom-100: 100 枚 × 5 キャプション = 500 件
- **group_size=100**: 各グループ 500 件の範囲内 ✅

## 分割戦略

- **分割タイプ**: `aspect_vs_bottom100`
- **グループ A**: 対象コンセプトの Top-100 から抽出（group_size=100）
- **グループ B**: 対象コンセプトの Bottom-100 から抽出（group_size=100）

## 評価設定

- **BERTScore**: 計算されるが、正解ラベルがないため参考値
- **BLEU**: 計算されるが、正解ラベルがないため参考値
- **LLM 評価**: 無効（`use_llm_evaluation: false`）

## 実行前確認チェックリスト

- [x] group_size=100 が設定されている
- [x] temperature=0.0 が設定されている
- [x] few_shot=0 が設定されている
- [x] use_llm_evaluation=false が設定されている
- [x] gpt_model=gpt-4o-mini が設定されている
- [x] split_type=aspect_vs_bottom100 が設定されている
- [x] 5 つのコンセプト（concept_0, concept_1, concept_2, concept_10, concept_50）が追加されている
- [x] 実験マトリックスの総実験数が 41 に更新されている

## 実行コマンド

実験実行前に、以下のコマンドでパラメータを再確認できます：

```bash
# 実験マトリックスの確認
cat 実験マトリックス.json | jq '.experiments[] | select(.dataset == "retrieved_concepts")'

# パラメータ設定の確認
cat src/analysis/experiments/utils/config/paramaters.yml
```

## 注意事項

1. **正解ラベルなし**: BERTScore/BLEU は計算されますが、参考値として扱ってください
2. **画像との整合性**: 生成された対比因子と画像を見比べて考察してください
3. **データ読み込み時間**: 大容量データセットのため、初回読み込みに時間がかかる可能性があります














