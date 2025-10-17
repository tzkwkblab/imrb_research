# 実験サマリー: tmpctiuiyx6

- 実行時刻: 20251017_141511
- 出力先: /Users/seinoshun/imrb_research/src/analysis/experiments/2025/10/10/results/20251017_141511
- 総実験数: 2
- 成功数: 2

## 設定

```yaml
experiments:
- aspects:
  - gameplay
  - visual
  dataset: steam
  group_size: 50
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
| steam | gameplay | 0.5633 | 0.0000 | poor | steam_gameplay_20251017_141511_20251017_141511.json |
| steam | visual | 0.5248 | 0.0000 | poor | steam_visual_20251017_141511_20251017_141518.json |
