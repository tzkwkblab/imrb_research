# 実験サマリー: tmpbvpdspva

- 実行時刻: 20251017_142256
- 出力先: /Users/seinoshun/imrb_research/src/analysis/experiments/2025/10/10/results/20251017_142256
- 総実験数: 1
- 成功数: 1

## 設定

```yaml
experiments:
- aspects:
  - story
  dataset: steam
  group_size: 3
  split_type: binary_label
general:
  console_output: true
  debug_mode: true
  use_aspect_descriptions: false
llm:
  max_tokens: 150
  model: gpt-4o-mini
  temperature: 0.7
output:
  directory: results/
  format: json
  save_intermediate: true

```

## 結果概要

| データセット | アスペクト | BERT | BLEU | 品質 | 出力ファイル |
| --- | --- | ---:| ---:| --- | --- |
| steam | story | 0.6940 | 0.0000 | poor | steam_story_20251017_142256_20251017_142256.json |
