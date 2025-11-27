# COCOデータセット実験設定確認

## 指定パラメータ

| パラメータ | 指定値 | 確認 |
|-----------|--------|------|
| group_size | 100 | ✓ |
| temperature | 0 | ✓ (paramaters.ymlで0.0に設定済み) |
| few_shot | 0 | ✓ |
| LLM評価 | なし | ✓ |
| モデル | gpt-4o-mini | ✓ |

## 現在の設定ファイル確認

### 1. パラメータ設定 (`src/analysis/experiments/utils/config/paramaters.yml`)

```yaml
model: gpt-4o-mini
temperature: 0.0  # ← 指定通り0に設定済み
max_tokens: 2000
```

### 2. データセット設定 (`src/analysis/experiments/utils/datasetManager/configs/dataset_configs.yaml`)

```yaml
retrieved_concepts:
  path: "/Users/seinoshun/imrb_research/data/external/retrieved-concepts/farnoosh/current"
  domain: "vision"
  language: "en"
```

### 3. 過去の実験で使用されたコンセプト

- concept_0
- concept_1
- concept_2
- concept_10
- concept_50

## 実験設定の詳細

### データセット情報

- **データソース**: MS-COCO 2017 train split
- **類似度計算**: CLIP (ViT-B/32) コサイン類似度
- **コンセプト数**: 300個（concept_0 ～ concept_299）
- **各コンセプトのデータ数**: 
  - Top-100: 100枚 × 5キャプション = 500件
  - Bottom-100: 100枚 × 5キャプション = 500件

### 分割戦略

- **分割タイプ**: `aspect_vs_bottom100`
- **グループA**: 対象コンセプトのTop-100から抽出（group_size=100）
- **グループB**: 対象コンセプトのBottom-100から抽出（group_size=100）

### プロンプト設定

- **Few-shot例**: なし（0-shot）
- **出力言語**: 英語
- **単語数**: 5-10単語
- **アスペクト記述**: 無効

### 評価設定

- **BERTScore**: 計算されるが、正解ラベルがないため参考値
- **BLEU**: 計算されるが、正解ラベルがないため参考値
- **LLM評価**: 無効

## 実験マトリックスに追加する設定

以下の5つのコンセプトで実験を実行：

```json
{
  "experiment_id": "retrieved_concepts_concept_0_0_4omini_word",
  "dataset": "retrieved_concepts",
  "aspect": "concept_0",
  "domain": null,
  "few_shot": 0,
  "gpt_model": "gpt-4o-mini",
  "group_size": 100,
  "split_type": "aspect_vs_bottom100",
  "use_llm_evaluation": false,
  "llm_evaluation_model": null,
  "use_aspect_descriptions": false
}
```

同様に、concept_1, concept_2, concept_10, concept_50 でも実行。

## 確認事項

1. ✅ temperature=0.0 は既に設定済み
2. ✅ group_size=100 は各コンセプトのTop-100/Bottom-100（各500件）の範囲内
3. ✅ few_shot=0 は設定可能
4. ✅ LLM評価なしは設定可能
5. ✅ gpt-4o-mini は使用可能

## 次のステップ

実験マトリックスにCOCOデータセットの実験を追加して実行する準備が整いました。

