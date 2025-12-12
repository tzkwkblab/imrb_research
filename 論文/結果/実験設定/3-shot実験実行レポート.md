# 3-shot実験実行レポート

## 実行概要

### 実行日時
- **開始日時**: 2025-11-26 15:27:00
- **実験マトリックス**: `3shot_experiment_matrix.json`
- **出力ディレクトリ**: `results/20251126_152700`

### 実験設定
- **Few-shot設定**: 3-shot（few_shot=1の実験をfew_shot=3に変更）
- **その他のパラメータ**: 既存の1-shot実験と同じ設定を維持
  - GPTモデル: gpt-4o-mini
  - group_size: 100（メイン実験）、50/100/150/200/300（Steamサブ実験）
  - LLM評価: 有効（gpt-4o-mini）
  - アスペクト記述: 無効

### 実験数
- **総実験数**: 61実験
  - Amazon: 5実験
  - GoEmotions: 28実験
  - SemEval: 4実験
  - Steam: 24実験

## 実験マトリックス生成

既存の`実験マトリックス.json`からfew_shot=1の実験を抽出し、few_shot=3に変更したマトリックスを生成しました。

### 生成スクリプト
`論文/結果/実験設定/generate_3shot_matrix.py`

### 生成されたマトリックス
`論文/結果/実験設定/3shot_experiment_matrix.json`

## 実験実行

### 実行コマンド
```bash
python src/analysis/experiments/2025/10/10/run_batch_from_matrix.py \
  --matrix 論文/結果/実験設定/3shot_experiment_matrix.json \
  --background
```

### 実行状態
- **プロセスID**: 49450
- **状態**: 実行中
- **完了済み**: 3/61実験（2025-11-26 15:27時点）

### ログファイル
`results/20251126_152700/run.log`

## 結果分析

### 分析スクリプト
`論文/結果/実験設定/analyze_3shot_results.py`

### 分析内容
- データセット別統計（平均BERT/BLEU/LLMスコア）
- アスペクト別統計（上位10件）
- 実験詳細（サンプル）

### 結果レポート生成
実験完了後、以下のコマンドで結果レポートを生成できます：

```bash
python 論文/結果/実験設定/analyze_3shot_results.py \
  --results-dir results/20251126_152700 \
  --output 論文/結果/実験設定/3-shot実験結果レポート.md
```

## 完了待ちスクリプト

実験の完了を待って自動的に結果を分析するスクリプトも用意しました：

```bash
python 論文/結果/実験設定/wait_and_analyze_3shot.py \
  --results-dir results/20251126_152700 \
  --check-interval 60
```

## 注意事項

1. 実験の完了には時間がかかります（61実験 × 約20秒/実験 = 約20分）
2. 実験が完了したら、`batch_results.json`が生成されます
3. 結果分析は実験完了後に実行してください

## 次のステップ

1. 実験の完了を待つ
2. 結果を分析してMarkdownレポートを生成
3. 1-shot実験との比較分析を実施














