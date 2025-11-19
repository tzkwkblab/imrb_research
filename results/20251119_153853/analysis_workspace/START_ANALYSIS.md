# 実験結果考察を開始してください

以下のコマンドを実行して、71実験の詳細考察を開始してください。

```bash
cd /Users/seinoshun/imrb_research
source .venv/bin/activate
python src/analysis/experiments/2025/10/10/analyze_experiment_results.py \
  --workspace-dir results/20251119_153853/analysis_workspace \
  --model gpt-5.1
```

**実行内容**: 全71実験についてLLM（gpt-5.1）で単語レベル詳細分析 → カテゴリ単位統合分析 → MDレポート生成

**出力先**: `results/20251119_153853/analysis_workspace/logs/` と `reports/`

**注意**: 中断してもチェックポイントから再開可能です。

