## analysis/ 概要

実験パイプラインと分析ユーティリティの中核です。日付別ディレクトリで実験を管理し、結果は JSON で保存します。

### 主な構成

- `experiments/`: 日付階層の実験ディレクトリ（例: `2025/10/10/`）
- `experiments/utils/`: データセット管理・LLM・スコア計算ユーティリティ
- `results_batch_analysis/`: バッチ結果の二次分析成果物
- スクリプト例:
  - `batch_review_analyzer.py` / `review_feature_analyzer.py`
  - `experiment_history_consolidator.py`（履歴集約）

### 実験の起動

- 推奨: ルートの対話スクリプト `scripts/run_interactive_experiment.sh`
- 直接実行例: 各日付ディレクトリの `run_experiment.py`

詳細は `experiments/` および `experiments/utils/` の README を参照してください。
