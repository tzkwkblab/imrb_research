# 実験実行プロンプト

## 実験概要

**総実験数**: 71 実験（メイン 37 + サブ 34）  
**目的**: データセット別性能比較 + group_size 変化による影響調査

## 実験構成

### メイン実験（37 件）

- **group_size=100 に統一**（コンテキスト長超過を防ぐため）
- データセット: Steam(4), Amazon(5), GoEmotions(28), SemEval(4)
- 設定: Few-shot=1, gpt-4o-mini, LLM 評価有効

### サブ実験（34 件）

- **Steam - group_size 変化調査（24 件）**
  - group_size: 50, 100, 150, 200, 300（各アスペクト ×5 パターン = 20 件）
  - gpt-5.1 で group_size=300 検証（4 件）
- **COCO - retrieved_concepts（10 件）**

## 実行方法

```bash
cd /Users/seinoshun/imrb_research
source .venv/bin/activate

# バックグラウンド実行
python src/analysis/experiments/2025/10/10/run_batch_from_matrix.py \
  --background \
  --debug \
  --matrix 実験マトリックス.json
```

## 実行状態確認

```bash
# 最新の結果ディレクトリを確認
ls -lt src/analysis/experiments/2025/10/10/results/ | head -3

# 状態確認（最新ディレクトリのパスを指定）
python src/analysis/experiments/2025/10/10/run_batch_from_matrix.py \
  --status \
  --output-dir results/YYYYMMDD_HHMMSS
```

## 停止方法

```bash
python src/analysis/experiments/2025/10/10/run_batch_from_matrix.py \
  --stop \
  --output-dir results/YYYYMMDD_HHMMSS
```

## 重要な注意事項

1. **メモリ使用量**: 並列実行数は自動で 1/5 に削減済み（最大 2 並列）
2. **プロンプト長制限**: group_size=100 以上の場合、プロンプト生成時に 100 件に制限される
3. **エラーハンドリング**: コンテキスト長超過エラーは自動検出され、リトライをスキップ
4. **チェックポイント**: 中断しても`checkpoint.json`から再開可能

## 期待される結果

- **メイン実験**: 各データセットで group_size=100 での性能を測定
- **Steam サブ実験**: group_size による性能変化を検証
- **gpt-5.1 検証**: group_size=300 が実行可能か確認

## トラブルシューティング

- **コンテキスト長超過エラー**: group_size=300 の gpt-4o-mini 実験で発生する可能性あり（gpt-5.1 では回避可能か検証）
- **プロセスが残る場合**: `pkill -9 -f "run_batch_from_matrix"`で強制停止
- **ログ確認**: `results/YYYYMMDD_HHMMSS/run.log`で進捗確認

## 関連ファイル

- 実験マトリックス: `実験マトリックス.json`
- 実行スクリプト: `src/analysis/experiments/2025/10/10/run_batch_from_matrix.py`
- レポート雛形: `experiment_summaries/report_template_111_experiments.md`
