<!-- e8aecfa0-9da7-4c25-bbdc-a867a633e225 d2f6ad57-f114-43e1-8d8a-270c3eabbffc -->
# 実験自動実行スクリプト実装計画

## 概要

実験マトリックスJSON（`実験マトリックス.json`）を読み込み、102実験を自動実行するスクリプトを実装する。並列実行で時短を図る。

## 実装ファイル

### 1. メイン実行スクリプト

**ファイル**: `src/analysis/experiments/2025/10/10/run_batch_from_matrix.py`

**機能**:

- 実験マトリックスJSONを読み込み
- 各実験設定を`ExperimentPipeline`に変換
- 並列実行（multiprocessingまたはconcurrent.futures）
- 進捗バー表示（tqdm）
- エラーハンドリングとリトライ
- 結果を個別JSONと統合JSONに保存

**主要関数**:

- `load_experiment_matrix(json_path)`: JSON読み込み
- `convert_matrix_to_config(exp_config)`: 実験設定をExperimentPipeline用設定に変換
- `run_single_experiment_wrapper(args)`: 単一実験実行ラッパー（並列実行用）
- `run_parallel_experiments(experiments, max_workers)`: 並列実行
- `save_results(results, output_dir)`: 結果保存

### 2. 結果集計スクリプト

**ファイル**: `src/analysis/experiments/2025/10/10/aggregate_results.py`

**機能**:

- 実行結果を集計
- 実験計画書の表形式テンプレートに合わせてMarkdown表を生成
- データセット別スコア比較表
- Few-shot影響分析表
- GPTモデル性能差比較表
- COCO実験結果の解釈レポート

**主要関数**:

- `load_all_results(results_dir)`: 全結果JSONを読み込み
- `create_dataset_comparison_table(results)`: データセット別比較表
- `create_fewshot_analysis_table(results)`: Few-shot影響分析表
- `create_model_comparison_table(results)`: GPTモデル比較表
- `generate_summary_report(results, output_path)`: 統合レポート生成

## 実装詳細

### 実験設定変換ロジック

実験マトリックスJSONの各実験設定を`ExperimentPipeline`が期待するYAML設定形式に変換：

```python
{
    'experiments': [{
        'dataset': exp['dataset'],
        'aspects': [exp['aspect']],
        'group_size': exp['group_size'],
        'split_type': exp['split_type']
    }],
    'llm': {
        'model': exp['gpt_model'],
        'temperature': 0.7,
        'max_tokens': 100
    },
    'general': {
        'use_examples': exp['few_shot'] > 0,
        'examples_file': get_examples_file(exp['dataset']),
        'max_examples': exp['few_shot']
    },
    'evaluation': {
        'use_llm_score': exp['use_llm_evaluation'],
        'llm_evaluation_model': exp['llm_evaluation_model']
    }
}
```

### 並列実行実装

- `concurrent.futures.ProcessPoolExecutor`を使用（I/O待機が多いため）
- デフォルト並列数: CPUコア数（最大8）
- 各実験は独立プロセスで実行（メモリ分離）
- 進捗バーは`tqdm`で表示

### Few-shot例題ファイル解決

- `data/analysis-workspace/contrast_examples/{dataset}/`から自動検索
- データセット別のデフォルト例題ファイルを使用
- `few_shot=0`の場合は例題を使用しない

### エラーハンドリング

- 各実験のエラーは個別にキャッチ
- 失敗した実験は結果に`error`フィールドを記録
- リトライ機能（オプション、デフォルトは1回のみ）
- 実行ログをファイルに保存

### 結果保存形式

- 個別結果: `results/{timestamp}/{experiment_id}.json`
- 統合結果: `results/{timestamp}/batch_results.json`
- 集計レポート: `results/{timestamp}/summary_report.md`

## 実行方法

```bash
# 基本実行
python run_batch_from_matrix.py --matrix 実験マトリックス.json

# 並列数を指定
python run_batch_from_matrix.py --matrix 実験マトリックス.json --workers 4

# 結果集計のみ
python aggregate_results.py --results-dir results/20250101_120000/
```

## 依存関係

- 既存: `ExperimentPipeline`, `tqdm`
- 新規追加: なし（標準ライブラリの`concurrent.futures`を使用）

## 注意事項

- 並列実行時は各プロセスで`ExperimentPipeline`を初期化（メモリ効率）
- APIレート制限に注意（必要に応じてレート制限機能を追加）
- 大容量の結果ファイルを想定（JSON圧縮オプション検討）

### To-dos

- [ ] 実験マトリックスJSON読み込み機能を実装（load_experiment_matrix）
- [ ] 実験設定をExperimentPipeline用設定に変換する機能を実装（convert_matrix_to_config、Few-shot例題ファイル解決含む）
- [ ] 並列実行機能を実装（run_single_experiment_wrapper、run_parallel_experiments、進捗バー表示）
- [ ] 結果保存機能を実装（個別JSON、統合JSON、エラーハンドリング）
- [ ] メイン実行スクリプト（run_batch_from_matrix.py）を完成（コマンドライン引数、ログ設定）
- [ ] 結果集計スクリプトの結果読み込み機能を実装（load_all_results）
- [ ] 集計表生成機能を実装（データセット別、Few-shot、GPTモデル比較表）
- [ ] 統合レポート生成機能を実装（Markdown形式、COCO実験解釈含む）