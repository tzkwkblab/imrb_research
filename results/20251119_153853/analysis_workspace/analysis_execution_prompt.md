# 実験結果考察実行プロンプト

## 実行手順

以下のコマンドを順番に実行して、実験結果の詳細考察を開始してください。

### 1. 研究背景抽出（既に完了済み）

```bash
cd /Users/seinoshun/imrb_research
source .venv/bin/activate
python src/analysis/experiments/2025/10/10/extract_research_context.py \
  --workspace-dir results/20251119_153853/analysis_workspace
```

### 2. 実験結果考察実行

#### バックグラウンド実行（推奨）

```bash
python src/analysis/experiments/2025/10/10/analyze_experiment_results.py \
  --workspace-dir results/20251119_153853/analysis_workspace \
  --model gpt-5.1 \
  --background
```

#### フォアグラウンド実行

```bash
python src/analysis/experiments/2025/10/10/analyze_experiment_results.py \
  --workspace-dir results/20251119_153853/analysis_workspace \
  --model gpt-5.1
```

## 実行内容

- **個別実験考察**: 71 実験すべてについて、単語レベルでの詳細分析を LLM（gpt-5.1）に依頼
- **カテゴリ単位考察**: メイン実験全体、steam_group_size、steam_gpt51、retrieved_concepts の各カテゴリについて統合分析
- **MD レポート生成**: 実験ごとの考察レポートを Markdown 形式で生成

## 出力先

- 個別実験ログ: `results/20251119_153853/analysis_workspace/logs/{experiment_id}/analysis_{timestamp}.log`
- カテゴリログ: `results/20251119_153853/analysis_workspace/logs/category_{category_name}/summary_{timestamp}.log`
- MD レポート: `results/20251119_153853/analysis_workspace/reports/{experiment_id}.md`
- 実行ログ: `results/20251119_153853/analysis_workspace/analysis.log`
- PID ファイル: `results/20251119_153853/analysis_workspace/analysis.pid`

## 注意事項

- gpt-5.1 が利用不可の場合は自動的に gpt-4o にフォールバック
- 中断してもチェックポイントから再開可能（`analysis_checkpoint.json`）
- 全 71 実験の処理には時間がかかります（API 呼び出し回数に応じて）
- 並列実行は最大 2 プロセスまで許可（同じ workspace_dir は 1 プロセスのみ）
- バックグラウンド実行中は PID ファイルでプロセスを管理

## 進捗確認・制御

### 実行状態確認

```bash
python src/analysis/experiments/2025/10/10/analyze_experiment_results.py \
  --workspace-dir results/20251119_153853/analysis_workspace \
  --status
```

### プロセス停止

```bash
python src/analysis/experiments/2025/10/10/analyze_experiment_results.py \
  --workspace-dir results/20251119_153853/analysis_workspace \
  --stop
```

### デバッグログ確認

```bash
# ログファイルの最新20行を確認
tail -20 results/20251119_153853/analysis_workspace/analysis.log

# リアルタイムでログを監視
tail -f results/20251119_153853/analysis_workspace/analysis.log
```

### 完了した実験数を確認

```bash
python3 -c "import json; c=json.load(open('results/20251119_153853/analysis_workspace/analysis_checkpoint.json')); print(f'完了: {len(c.get(\"completed_experiment_ids\", []))}件')" 2>/dev/null || echo "チェックポイントファイルが見つかりません"

# 生成されたログファイル数を確認
find results/20251119_153853/analysis_workspace/logs -name "*.log" | wc -l
```

## 実行時間の目安

- **個別実験考察**: 71 実験 × 約 20-30 秒/実験 = 約 24-36 分
- **カテゴリ単位考察**: 4 カテゴリ × 約 30-60 秒/カテゴリ = 約 2-4 分
- **合計**: 約 30-45 分程度（API 応答時間に依存）

注意: エラーやリトライが発生した場合はさらに時間がかかる可能性があります。
