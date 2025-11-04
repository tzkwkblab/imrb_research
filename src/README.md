## src/ 概要

分析・実験コード一式。上位の流れは `src/analysis/` にあり、データ取得・前処理は `src/data/` が担当します。

### ディレクトリ

- `analysis/`: 実験パイプライン・分析ツール群（主要ロジック）
- `data/`: データ取得/変換・機能定義スクリプト（コード側）

### 実行エントリ

- 統一パイプライン例: `src/analysis/experiments/2025/10/10/run_experiment.py`
- 対話型ランナー: `scripts/run_interactive_experiment.sh`

詳細は各サブディレクトリの README を参照してください。
