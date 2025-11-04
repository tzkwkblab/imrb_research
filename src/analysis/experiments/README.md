## experiments/ 概要

日付ベースの階層（`{YYYY}/{MM}/{DD-実験番号}/`）で実験を管理します。各ディレクトリには実行スクリプト、設定、結果 JSON を配置します。

### 構成（例）

```
2025/10/10/
├── run_experiment.py
├── pipeline_config.yaml
├── experiment_pipeline.py
└── results/
    └── batch_experiment_*.json
```

### 実行

- 推奨: ルートの `scripts/run_interactive_experiment.sh`
- 直接: 各日付ディレクトリで `python run_experiment.py --config pipeline_config.yaml`

### 参照

- 代表実装: `2025/10/10/` の README を参照
- 共通ユーティリティ: `experiments/utils/`
