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

```bash
python src/analysis/experiments/2025/10/10/analyze_experiment_results.py \
  --workspace-dir results/20251119_153853/analysis_workspace \
  --model gpt-5.1
```

## 実行内容

- **個別実験考察**: 71実験すべてについて、単語レベルでの詳細分析をLLM（gpt-5.1）に依頼
- **カテゴリ単位考察**: メイン実験全体、steam_group_size、steam_gpt51、retrieved_conceptsの各カテゴリについて統合分析
- **MDレポート生成**: 実験ごとの考察レポートをMarkdown形式で生成

## 出力先

- 個別実験ログ: `results/20251119_153853/analysis_workspace/logs/{experiment_id}/analysis_{timestamp}.log`
- カテゴリログ: `results/20251119_153853/analysis_workspace/logs/category_{category_name}/summary_{timestamp}.log`
- MDレポート: `results/20251119_153853/analysis_workspace/reports/{experiment_id}.md`

## 注意事項

- gpt-5.1が利用不可の場合は自動的にgpt-4oにフォールバック
- 中断してもチェックポイントから再開可能（`analysis_checkpoint.json`）
- 全71実験の処理には時間がかかります（API呼び出し回数に応じて）

## 進捗確認

```bash
# 完了した実験数を確認
python3 -c "import json; c=json.load(open('results/20251119_153853/analysis_workspace/analysis_checkpoint.json')); print(f'完了: {len(c.get(\"completed_experiment_ids\", []))}件')" 2>/dev/null || echo "チェックポイントファイルが見つかりません"

# 生成されたログファイル数を確認
find results/20251119_153853/analysis_workspace/logs -name "*.log" | wc -l
```

