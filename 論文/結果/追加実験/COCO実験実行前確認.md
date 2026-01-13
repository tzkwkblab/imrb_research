# COCOデータセット実験 - 実行前パラメータ確認

## ✅ 実装完了

COCOデータセット（Retrieved Concepts）の実験設定を実験マトリックスに追加しました。

## 📊 実験設定サマリー

| 項目 | 値 |
|------|-----|
| **実験数** | 5実験 |
| **コンセプト** | concept_0, concept_1, concept_2, concept_10, concept_50 |
| **group_size** | 100 |
| **temperature** | 0.0 |
| **few_shot** | 0 |
| **LLM評価** | 無効 |
| **モデル** | gpt-4o-mini |
| **分割タイプ** | aspect_vs_bottom100 |

## 🔍 パラメータ詳細確認

### 実験マトリックス設定

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

### パラメータ設定ファイル (`src/analysis/experiments/utils/config/paramaters.yml`)

```yaml
model: gpt-4o-mini
temperature: 0.0  # ← 指定通り0に設定
max_tokens: 2000
```

## 📋 実行前チェックリスト

### 必須確認項目

- [x] **group_size=100**: 実験マトリックスに設定済み
- [x] **temperature=0.0**: `paramaters.yml`に設定済み
- [x] **few_shot=0**: 実験マトリックスに設定済み
- [x] **use_llm_evaluation=false**: 実験マトリックスに設定済み
- [x] **gpt_model=gpt-4o-mini**: 実験マトリックスに設定済み
- [x] **split_type=aspect_vs_bottom100**: 実験マトリックスに設定済み
- [x] **5つのコンセプト追加**: concept_0, concept_1, concept_2, concept_10, concept_50
- [x] **総実験数更新**: 36 → 41（メイン36 + サブ5）

### データセット確認

- [x] **データパス**: `data/external/retrieved-concepts/farnoosh/current`
- [x] **各コンセプトのデータ数**: Top-100/Bottom-100 それぞれ500件
- [x] **group_size=100**: データ数の範囲内（500件以下）

## 🚀 実行コマンド

実験実行前に、以下のコマンドで最終確認ができます：

```bash
# COCO実験の設定を確認
python3 -c "
import json
data = json.load(open('実験マトリックス.json'))
coco_exps = [e for e in data['experiments'] if e['dataset'] == 'retrieved_concepts']
print(f'COCO実験数: {len(coco_exps)}')
for e in coco_exps:
    print(f\"\\n実験ID: {e['experiment_id']}\")
    print(f\"  アスペクト: {e['aspect']}\")
    print(f\"  group_size: {e['group_size']}\")
    print(f\"  few_shot: {e['few_shot']}\")
    print(f\"  use_llm_evaluation: {e['use_llm_evaluation']}\")
    print(f\"  gpt_model: {e['gpt_model']}\")
"

# パラメータ設定を確認
cat src/analysis/experiments/utils/config/paramaters.yml
```

## ⚠️ 注意事項

1. **正解ラベルなし**: BERTScore/BLEUは計算されますが、参考値として扱ってください
2. **画像との整合性**: 生成された対比因子と画像を見比べて考察してください
3. **データ読み込み時間**: 大容量データセットのため、初回読み込みに時間がかかる可能性があります
4. **temperature=0.0**: 一貫性重視の設定です

## 📝 次のステップ

1. 上記のチェックリストを確認
2. 実験実行コマンドを実行
3. 結果を確認して、生成された対比因子と画像を比較

## 📄 関連ファイル

- 実験マトリックス: `実験マトリックス.json`
- パラメータ設定: `src/analysis/experiments/utils/config/paramaters.yml`
- データセット設定: `src/analysis/experiments/utils/datasetManager/configs/dataset_configs.yaml`
- 設定確認ドキュメント: `論文/結果/追加実験/COCO実験設定確認.md`



















