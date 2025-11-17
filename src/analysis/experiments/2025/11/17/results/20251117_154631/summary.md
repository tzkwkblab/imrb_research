# 実験サマリー: tmpqpdwbrl9

- 実行時刻: 20251117_154631
- 出力先: /Users/seinoshun/imrb_research/src/analysis/experiments/2025/11/17/results/20251117_154631
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
| steam | (gameplay) Controls | A:50/B:50 | 2 | 0.6696 | 0.0000 | 0.2000 | 参照テキストと候補テキストは異なるテーマを扱っているため。 | poor | Emotional depth and character-driven narratives | steam_gameplay_20251117_154631_20251117_154631.json |
| steam | (visual) Aesthetic | A:50/B:50 | 2 | 0.5952 | 0.0000 | 0.2000 | 両者は異なるテーマで、関連性がほとんどない。 | poor | Emotionally driven storytelling and nostalgic gameplay. | steam_visual_20251117_154631_20251117_154640.json |
| steam | (story) Story | A:50/B:50 | 2 | 0.7553 | 0.0000 | 0.6000 | ストーリーの特徴とゲームプレイの強調は異なるが関連性あり | fair | Emphasis on gameplay mechanics and narrative depth. | steam_story_20251117_154631_20251117_154648.json |

## 比較対象テキスト

### 実験 1: steam - gameplay

**正解テキスト (Reference):**

```
gameplay related characteristics
```

**生成テキスト (Candidate):**

```
Emotional depth and character-driven narratives
```

### 実験 2: steam - visual

**正解テキスト (Reference):**

```
visual related characteristics
```

**生成テキスト (Candidate):**

```
Emotionally driven storytelling and nostalgic gameplay.
```

### 実験 3: steam - story

**正解テキスト (Reference):**

```
story related characteristics
```

**生成テキスト (Candidate):**

```
Emphasis on gameplay mechanics and narrative depth.
```

## ログ

- Pythonログ: logs/python.log
- CLIログ: logs/cli_run.log
