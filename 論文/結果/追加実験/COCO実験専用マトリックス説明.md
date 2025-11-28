# COCO実験専用マトリックス

## 概要

COCOデータセット（Retrieved Concepts）の検証実験専用のマトリックスファイルです。

## ファイル

- **マトリックスファイル**: `実験マトリックス_coco.json`

## 実験設定

| パラメータ | 値 |
|-----------|-----|
| **実験数** | 5実験 |
| **コンセプト** | concept_0, concept_1, concept_2, concept_10, concept_50 |
| **group_size** | 100 |
| **temperature** | 0.0 |
| **few_shot** | 0 |
| **LLM評価** | 無効 |
| **モデル** | gpt-4o-mini |
| **分割タイプ** | aspect_vs_bottom100 |

## 実験一覧

1. `retrieved_concepts_concept_0_0_4omini_word` - concept_0
2. `retrieved_concepts_concept_1_0_4omini_word` - concept_1
3. `retrieved_concepts_concept_2_0_4omini_word` - concept_2
4. `retrieved_concepts_concept_10_0_4omini_word` - concept_10
5. `retrieved_concepts_concept_50_0_4omini_word` - concept_50

## 実行方法

このマトリックスファイルを使用して実験を実行する場合、実行スクリプトでこのファイルを指定してください。

```bash
# 例: バッチ実行スクリプトで使用
python run_batch_from_matrix.py --matrix 実験マトリックス_coco.json
```

## 注意事項

- このマトリックスはCOCO実験専用です
- 元の `実験マトリックス.json` とは独立しています
- 正解ラベルがないため、BERTScore/BLEUは参考値として扱ってください


