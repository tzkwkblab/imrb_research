# 実験サマリー: tmp9uj5x_0c

- 実行時刻: 20251117_175419
- 出力先: /Users/seinoshun/imrb_research/src/analysis/experiments/2025/11/17/results/20251117_175419
- 総実験数: 3
- 成功数: 3

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
  max_tokens: 5000
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
| steam | (gameplay) Controls | A:50/B:50 | 2 | 0.6685 | 0.0000 | 0.2000 | ゲームプレイの特性と感情的深さは異なる概念です。 | poor | Emotional depth and narrative complexity | steam_gameplay_20251117_175419_20251117_175420.json |
| steam | (visual) Aesthetic | A:50/B:50 | 2 | 0.6012 | 0.0000 | 0.2000 | 参照テキストと候補テキストは異なるテーマであるため。 | poor | Humor, nostalgia, and self-deprecation. | steam_visual_20251117_175419_20251117_175429.json |
| steam | (story) Story | A:50/B:50 | 2 | 0.7566 | 0.0000 | 0.4000 | ストーリーの特徴とゲームプレイの革新は異なる概念。 | poor | Innovative gameplay mechanics and engaging narratives. | steam_story_20251117_175419_20251117_175436.json |

## 比較対象テキスト

### 実験 1: steam - gameplay

**正解テキスト (Reference):**

```
gameplay related characteristics
```

**生成テキスト (Candidate):**

```
Emotional depth and narrative complexity
```

### 実験 2: steam - visual

**正解テキスト (Reference):**

```
visual related characteristics
```

**生成テキスト (Candidate):**

```
Humor, nostalgia, and self-deprecation.
```

### 実験 3: steam - story

**正解テキスト (Reference):**

```
story related characteristics
```

**生成テキスト (Candidate):**

```
Innovative gameplay mechanics and engaging narratives.
```

## ログ

- Pythonログ: logs/python.log
- CLIログ: logs/cli_run.log
