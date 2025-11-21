# 実験結果考察実行プロンプト（LLMエージェント用）

以下の手順で実験結果の考察を開始してください。

## 実行環境の確認

```bash
cd /Users/seinoshun/imrb_research
source .venv/bin/activate
```

## 実行コマンド

### バックグラウンド実行（推奨）

```bash
python src/analysis/experiments/2025/10/10/analyze_experiment_results.py \
  --workspace-dir results/20251119_153853/analysis_workspace \
  --model gpt-5.1 \
  --background
```

### フォアグラウンド実行（デバッグ時）

```bash
python src/analysis/experiments/2025/10/10/analyze_experiment_results.py \
  --workspace-dir results/20251119_153853/analysis_workspace \
  --model gpt-5.1 \
  --debug
```

## 実行内容

- **個別実験考察**: 71実験すべてについて、単語レベルでの詳細分析をLLM（gpt-5.1）に依頼
- **カテゴリ単位考察**: メイン実験全体、steam_group_size、steam_gpt51、retrieved_conceptsの各カテゴリについて統合分析
- **MDレポート生成**: 実験ごとの考察レポートをMarkdown形式で生成

## 進捗確認

実行開始後、以下のコマンドで進捗を確認できます：

```bash
# 実行状態確認
python src/analysis/experiments/2025/10/10/analyze_experiment_results.py \
  --workspace-dir results/20251119_153853/analysis_workspace \
  --status

# ログファイルのリアルタイム監視
tail -f results/20251119_153853/analysis_workspace/analysis.log

# 完了した実験数を確認
python3 -c "import json; c=json.load(open('results/20251119_153853/analysis_workspace/analysis_checkpoint.json')); print(f'完了: {len(c.get(\"completed_experiment_ids\", []))}件')" 2>/dev/null || echo "チェックポイントファイルが見つかりません"
```

## プロセス停止

必要に応じて、以下のコマンドでプロセスを停止できます：

```bash
python src/analysis/experiments/2025/10/10/analyze_experiment_results.py \
  --workspace-dir results/20251119_153853/analysis_workspace \
  --stop
```

## 注意事項

- gpt-5.1が利用不可の場合は自動的にgpt-4oにフォールバック
- 中断してもチェックポイントから再開可能（`analysis_checkpoint.json`）
- 全71実験の処理には時間がかかります（API呼び出し回数に応じて）
- 並列実行は最大3プロセスまで許可（同じworkspace_dirは1プロセスのみ）
- バックグラウンド実行中はPIDファイルでプロセスを管理

## 実行時間の目安

- **個別実験考察**: 71実験 × 約20-30秒/実験 = 約24-36分
- **カテゴリ単位考察**: 4カテゴリ × 約30-60秒/カテゴリ = 約2-4分
- **合計**: 約30-45分程度（API応答時間に依存）

注意: エラーやリトライが発生した場合はさらに時間がかかる可能性があります。

## 出力先

- 個別実験ログ: `results/20251119_153853/analysis_workspace/logs/{experiment_id}/analysis_{timestamp}.log`
- カテゴリログ: `results/20251119_153853/analysis_workspace/logs/category_{category_name}/summary_{timestamp}.log`
- MDレポート: `results/20251119_153853/analysis_workspace/reports/{experiment_id}.md`
- 実行ログ: `results/20251119_153853/analysis_workspace/analysis.log`
- PIDファイル: `results/20251119_153853/analysis_workspace/analysis.pid`

