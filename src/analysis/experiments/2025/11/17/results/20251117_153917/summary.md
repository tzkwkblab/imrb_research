# 実験サマリー: tmp686w9k8w

- 実行時刻: 20251117_153917
- 出力先: /Users/seinoshun/imrb_research/src/analysis/experiments/2025/11/17/results/20251117_153917
- 総実験数: 1
- 成功数: 1

## 設定

```yaml
evaluation:
  llm_evaluation_model: gpt-4o-mini
  llm_evaluation_temperature: 0.0
  use_llm_score: true
experiments:
- aspects:
  - gameplay
  dataset: steam
  group_size: 10
  split_type: aspect_vs_others
general:
  aspect_descriptions_file: /Users/seinoshun/imrb_research/data/analysis-workspace/aspect_descriptions/steam/descriptions_official.csv
  console_output: true
  debug_mode: true
  examples_file: /Users/seinoshun/imrb_research/data/analysis-workspace/contrast_examples/steam/steam_examples_v1.json
  max_examples: 1
  silent_mode: false
  use_aspect_descriptions: true
  use_examples: true
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

| データセット | アスペクト | 件数(A/B) | 例題数 | BERT | BLEU | LLM | LLM理由 | 品質 | LLM出力 | 出力ファイル |
| --- | --- | --- | ---:| ---:| ---:| ---:| --- | --- | --- | --- |
| steam | (gameplay) Controls | A:10/B:10 | 1 | 0.5827 | 0.0000 | 0.2000 | 両者の意味は大きく異なり、関連性がない。 | poor | Depth of analysis and personal growth narratives | steam_gameplay_20251117_153917_20251117_153917.json |

## ログ

- Pythonログ: logs/python.log
- CLIログ: logs/cli_run.log
