# 実験サマリー: tmporbm772c

- 実行時刻: 20251117_174223
- 出力先: /Users/seinoshun/imrb_research/src/analysis/experiments/2025/11/17/results/20251117_174223
- 総実験数: 3
- 成功数: 0

## 設定

```yaml
evaluation:
  llm_evaluation_model: gpt-4o-mini
  llm_evaluation_temperature: 0.0
  use_llm_score: true
experiments:
- aspects:
  - gameplay
  - visual
  - story
  dataset: steam
  group_size: 50
  split_type: aspect_vs_others
general:
  aspect_descriptions_file: /Users/seinoshun/imrb_research/data/analysis-workspace/aspect_descriptions/steam/descriptions_official.csv
  console_output: true
  debug_mode: true
  examples_file: /Users/seinoshun/imrb_research/data/analysis-workspace/contrast_examples/steam/steam_examples_v1.json
  max_examples: 2
  silent_mode: false
  use_aspect_descriptions: true
  use_examples: true
llm:
  max_tokens: 1000
  model: gpt-5-nano
  temperature: 0.7
output:
  directory: results/
  format: json
  save_intermediate: true

```

## 結果概要

| データセット | アスペクト | 件数(A/B) | 例題数 | BERT | BLEU | LLM | LLM理由 | 品質 | LLM出力 | 出力ファイル |
| --- | --- | --- | ---:| ---:| ---:| ---:| --- | --- | --- | --- |

## 比較対象テキスト

## ログ

- Pythonログ: logs/python.log
- CLIログ: logs/cli_run.log
