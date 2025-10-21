# 実験サマリー: tmpg_oc0b4t

- 実行時刻: 20251021_150419
- 出力先: /Users/seinoshun/imrb_research/src/analysis/experiments/2025/10/10/results/20251021_150419
- 総実験数: 3
- 成功数: 3

## 設定

```yaml
experiments:
- aspects:
  - gameplay
  - visual
  - story
  dataset: steam
  group_size: 50
  split_type: binary_label
general:
  aspect_descriptions_file: /Users/seinoshun/imrb_research/data/analysis-workspace/aspect_descriptions/steam/steam_v1.csv
  console_output: true
  debug_mode: true
  use_aspect_descriptions: true
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
| steam | gameplay | 0.5367 | 0.0000 | poor | steam_gameplay_20251021_150419_20251021_150420.json |
| steam | visual | 0.5452 | 0.0000 | poor | steam_visual_20251021_150419_20251021_150427.json |
| steam | story | 0.5500 | 0.0000 | poor | steam_story_20251021_150419_20251021_150431.json |

## ログ

- Pythonログ: logs/python.log
- CLIログ: logs/cli_run.log
