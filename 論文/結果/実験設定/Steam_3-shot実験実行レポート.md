# Steam 3-shot実験実行レポート

## 実行概要

### 実行日時
- **開始日時**: 2025-11-26 15:31:23
- **実験マトリックス**: `steam_3shot_experiment_matrix.json`
- **出力ディレクトリ**: `results/20251126_153123`

### 実験設定
- **データセット**: Steam
- **Few-shot設定**: 0-shot, 1-shot, 3-shot
- **アスペクト**: gameplay, visual, story, audio（4アスペクト）
- **group_size**: 100
- **LLM評価**: 無効（use_llm_evaluation: false）
- **GPTモデル**: gpt-4o-mini
- **例題ファイル**: `data/analysis-workspace/contrast_examples/steam/steam_examples_v1.json`（存在確認済み）

### 実験数
- **総実験数**: 12実験
  - 4アスペクト × 3Few-shot設定（0, 1, 3） = 12実験

## 実験マトリックス生成

### 生成スクリプト
`論文/結果/実験設定/generate_steam_3shot_matrix.py`

### 生成されたマトリックス
`論文/結果/実験設定/steam_3shot_experiment_matrix.json`

### 例題ファイル確認
- **パス**: `data/analysis-workspace/contrast_examples/steam/steam_examples_v1.json`
- **状態**: 存在確認済み
- **内容**: gameplayとvisualの例題を含む（各2例）

## 実験実行

### 実行コマンド
```bash
python src/analysis/experiments/2025/10/10/run_batch_from_matrix.py \
  --matrix 論文/結果/実験設定/steam_3shot_experiment_matrix.json \
  --background
```

### 実行状態
- **プロセスID**: 58441
- **状態**: 実行中
- **ログファイル**: `results/20251126_153123/run.log`

## 結果分析

### 分析スクリプト
`論文/結果/実験設定/analyze_steam_3shot_results.py`

### 分析内容
- Few-shot別統計（0-shot, 1-shot, 3-shotの平均BERT/BLEUスコア）
- アスペクト別統計（各アスペクトのFew-shot別スコア比較）
- 実験詳細（全実験のスコア一覧）

### 結果レポート生成
実験完了後、以下のコマンドで結果レポートを生成できます：

```bash
python 論文/結果/実験設定/analyze_steam_3shot_results.py \
  --results-dir results/20251126_153123 \
  --output 論文/結果/実験設定/Steam_3-shot実験結果レポート.md
```

## 実験一覧

| 実験ID | アスペクト | Few-shot |
|--------|----------|----------|
| steam_gameplay_0_4o-mini_word | gameplay | 0 |
| steam_gameplay_1_4o-mini_word | gameplay | 1 |
| steam_gameplay_3_4o-mini_word | gameplay | 3 |
| steam_visual_0_4o-mini_word | visual | 0 |
| steam_visual_1_4o-mini_word | visual | 1 |
| steam_visual_3_4o-mini_word | visual | 3 |
| steam_story_0_4o-mini_word | story | 0 |
| steam_story_1_4o-mini_word | story | 1 |
| steam_story_3_4o-mini_word | story | 3 |
| steam_audio_0_4o-mini_word | audio | 0 |
| steam_audio_1_4o-mini_word | audio | 1 |
| steam_audio_3_4o-mini_word | audio | 3 |

## 注意事項

1. 実験の完了には時間がかかります（12実験 × 約15秒/実験 = 約3分）
2. 実験が完了したら、`batch_results.json`が生成されます
3. 結果分析は実験完了後に実行してください

## 次のステップ

1. 実験の完了を待つ
2. 結果を分析してMarkdownレポートを生成
3. 0-shot, 1-shot, 3-shotの比較分析を実施


