# メイン実験再実行

メイン実験を理想パラメータで再実行するための追加実験です。

## 実験概要

**目的**: メイン実験を理想パラメータで再実行し、論文執筆に必要な正確な結果を取得する  
**総実験数**: 36実験

## パラメータ設定

| パラメータ | 実際の設定 | 理想の設定 |
|-----------|----------|----------|
| **Few-shot** | 1-shot | **0-shot** |
| **max_tokens** | 100 | **2000** |
| **temperature** | 0.7 | **0.0** |
| **group_size** | 100 | 100 |
| **LLM評価** | 有効 | 有効 |

詳細は [`実験パラメータ.md`](実験パラメータ.md) を参照してください。

## データセット構成

| データセット | アスペクト数 | 実験数 |
|------------|-----------|--------|
| SemEval | 4 | 4 |
| GoEmotions | 28 | 28 |
| Steam | 4 | 4 |
| **合計** | **36** | **36** |

**除外データセット**: Amazon (5実験), Retrieved Concepts/COCO (10実験)

## 実行方法

### Step 1: マトリックスの生成

```bash
cd /Users/seinoshun/imrb_research
source .venv/bin/activate

python 論文/結果/追加実験/main_experiment_rerun/実行ファイル/generate_main_experiment_matrix.py
```

### Step 2: 実験の実行

```bash
python src/analysis/experiments/2025/10/10/run_batch_from_matrix.py \
  --matrix 論文/結果/追加実験/main_experiment_rerun/マトリックス/main_experiment_matrix.json \
  --output-dir 論文/結果/追加実験/main_experiment_rerun/results \
  --background \
  --debug
```

### Step 3: 実行状態確認

```bash
python src/analysis/experiments/2025/10/10/run_batch_from_matrix.py \
  --status \
  --output-dir 論文/結果/追加実験/main_experiment_rerun/results
```

### Step 4: 実行停止（必要な場合）

```bash
python src/analysis/experiments/2025/10/10/run_batch_from_matrix.py \
  --stop \
  --output-dir 論文/結果/追加実験/main_experiment_rerun/results
```

## 結果確認

実行後、以下のディレクトリに結果が保存されます：

- `results/batch_results.json` - 統合結果
- `results/individual/*.json` - 個別結果（36ファイル）
- `results/checkpoint.json` - チェックポイント（中断時再開用）

## 評価指標

- **BERTScore**: 意味類似度評価（主要指標）
- **BLEU Score**: n-gram一致率評価（参考指標）
- **LLM評価**: GPT-4o-miniによる意味的類似度評価（補助指標）

## 実行時間・コスト見積もり

- **実行時間**: 約6-18分（順次実行）、約3-9分（2並列）
- **コスト**: 数ドル〜数十ドル（max_tokens=2000に増加のため出力トークン数が増加）

## 注意事項

### パラメータ設定の確認

- `run_batch_from_matrix.py`の修正が正しく反映されているか確認
- 実験マトリックスの`experiment_plan.settings`に`temperature`と`max_tokens`が含まれているか確認

### 実行前チェックリスト

- [ ] 仮想環境がアクティブになっている
- [ ] 環境変数（OPENAI_API_KEY）が設定されている
- [ ] マトリックスが正しく生成されている
- [ ] 結果保存ディレクトリが作成可能か確認

## LLM考察取得

実験結果からLLM（gpt-5.1）による考察を自動生成できます。

### Step 1: 統計情報の生成

```bash
python 論文/結果/追加実験/main_experiment_rerun_temperature0/実行ファイル/generate_main_experiment_statistics.py
```

### Step 2: 考察の取得

```bash
python 論文/結果/追加実験/main_experiment_rerun_temperature0/実行ファイル/generate_main_experiment_analysis.py
```

### 出力ファイル

- `main_experiment_statistics.json` - 統計情報
- `main_experiment_analysis.md` - LLMによる考察レポート

詳細は [`LLM考察取得ガイド.md`](../LLM考察取得ガイド.md) を参照してください。

## 実装詳細

実装計画の詳細は [`実装計画.md`](実装計画.md) を参照してください。

## 関連ファイル

- 実験パラメータ: [`実験パラメータ.md`](実験パラメータ.md)
- 実装計画: [`実装計画.md`](実装計画.md)
- マトリックス生成スクリプト: [`実行ファイル/generate_main_experiment_matrix.py`](実行ファイル/generate_main_experiment_matrix.py)
- 統計情報生成スクリプト: [`実行ファイル/generate_main_experiment_statistics.py`](実行ファイル/generate_main_experiment_statistics.py)
- 考察取得スクリプト: [`実行ファイル/generate_main_experiment_analysis.py`](実行ファイル/generate_main_experiment_analysis.py)
- 実験マトリックス: [`マトリックス/main_experiment_matrix.json`](マトリックス/main_experiment_matrix.json)
- 考察レポート: [`main_experiment_analysis.md`](main_experiment_analysis.md)

