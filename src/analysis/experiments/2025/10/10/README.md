# 統一実験パイプライン

複数データセット対応の実験パイプライン実装。設定ファイル駆動で保守性の高い設計。

## 機能

- ✅ 複数データセット対応（Steam, Amazon, SemEval, Retrieved Concepts）
- ✅ コマンドライン実行で BERT/BLEU スコア出力
- ✅ 設定ファイル駆動の実験管理
- ✅ JSON 形式での結果保存
- ✅ エラーハンドリング
- ✅ サイレントモード（`--silent`フラグ）

## ファイル構成

```
2025/10/10/
├── experiment_pipeline.py      # メインパイプライン実装
├── run_experiment.py            # コマンドライン実行スクリプト
├── pipeline_config.yaml         # 実験設定ファイル
├── test_utils_import.py         # utilsモジュールテスト
├── results/                     # 実験結果保存ディレクトリ
│   └── batch_experiment_*.json  # バッチ実験結果
└── README.md                    # このファイル
```

## 使用方法

### 前提条件

1. 仮想環境のアクティベート

```bash
cd /Users/seinoshun/imrb_research
source .venv/bin/activate
```

2. 環境変数設定（.env ファイルに OPENAI_API_KEY を設定）

### 基本的な使い方

#### 1. 設定ファイルから実行（推奨）

```bash
cd /Users/seinoshun/imrb_research/src/analysis/experiments/2025/10/10
python run_experiment.py --config pipeline_config.yaml
```

#### 2. コマンドライン引数で単一実験

```bash
# Steamデータセットでgameplayアスペクト実験
python run_experiment.py --dataset steam --aspect gameplay --group-size 50

# 複数アスペクトを指定
python run_experiment.py --dataset steam --aspects gameplay visual story
```

### 設定ファイル（pipeline_config.yaml）

```yaml
experiments:
  - dataset: steam
    aspects:
      - gameplay
      - visual
      - story
    group_size: 50
    split_type: binary_label

output:
  directory: results/
  format: json

llm:
  model: gpt-4o-mini
  temperature: 0.7
  max_tokens: 150
```

## コマンドラインオプション

```
usage: run_experiment.py [-h] [--config CONFIG] [--dataset {steam,semeval,amazon,retrieved_concepts}]
                        [--aspect ASPECT] [--aspects ASPECTS [ASPECTS ...]]
                        [--group-size GROUP_SIZE]
                        [--split-type {binary_label,aspect_vs_others,aspect_vs_bottom100}]
                        [--use-aspect-descriptions] [--aspect-descriptions-file FILE]
                        [--use-examples] [--examples-file FILE] [--max-examples N]
                        [--silent] [--debug] [--output-dir OUTPUT_DIR]

オプション:
  --config, -c          設定ファイルパス (default: pipeline_config.yaml)
  --dataset, -d         データセット名 (steam, semeval, amazon, retrieved_concepts)
  --aspect, -a          アスペクト名（単一指定）
  --aspects             アスペクト名（複数指定）
  --group-size, -g      グループサイズ (default: 50)
  --split-type          分割タイプ (default: binary_label)
                        - binary_label: ポジ/ネガ分類用（Steam推奨）
                        - aspect_vs_others: アスペクト間比較用（汎用）
                        - aspect_vs_bottom100: Top-100 vs Bottom-100（retrieved_concepts専用）
  --use-aspect-descriptions  アスペクト説明文を使用
  --aspect-descriptions-file  説明文CSVファイルパス
  --use-examples         Few-shot例題を使用
  --examples-file        例題ファイルパス
  --max-examples         使用する例題数
  --silent               ファイル保存をスキップ（デバッグ用途）
  --debug                デバッグモード有効化
  --output-dir           出力ディレクトリ (default: results/)
```

## 出力例

### コンソール出力

```
============================================================
統一実験パイプライン
============================================================

[モード] コマンドライン引数から実行
データセット: steam

==================================================
実験開始: steam_gameplay_20251010_160941
データセット: steam
アスペクト: gameplay
グループサイズ: 10

[1/3] データ読み込み中...
データセット読み込み: 8800件のレコード
アスペクト 'gameplay' のレコード: 1100件
✅ データ読み込み完了 (A: 10件, B: 10件)

[2/3] 対比因子分析実行中...
✅ LLM応答取得完了

[3/3] スコア確認中...
✅ スコア確認完了

==================================================
=== 結果 ===
BERTスコア: 0.5419
BLEUスコア: 0.0000
LLM応答: グループAは詳細なゲーム評価と感情的な反応が特徴。
品質評価: poor

📁 （ログ/アーカイブ）結果保存: results/batch_experiment_20251010_160941.json

============================================================
=== 実験サマリー ===
============================================================
総実験数: 1
成功: 1
失敗: 0

=== スコアサマリー ===
steam      gameplay        BERT: 0.5419  BLEU: 0.0000

✅ パイプライン実行完了
```

### JSON 結果ファイル

```json
{
  "experiment_meta": {
    "timestamp": "20251010_160941",
    "total_experiments": 1,
    "successful_experiments": 1
  },
  "results": [
    {
      "experiment_info": {
        "dataset": "steam",
        "aspect": "gameplay",
        "group_size": 10
      },
      "evaluation": {
        "bert_score": 0.5419,
        "bleu_score": 0.0
      },
      "process": {
        "llm_response": "グループAは詳細なゲーム評価と感情的な反応が特徴。"
      },
      "summary": {
        "success": true,
        "quality_assessment": {
          "overall_quality": "poor"
        }
      }
    }
  ]
}
```

## 対応データセット

### Steam Reviews（動作確認済み）

- データセット: `steam`
- アスペクト: `gameplay`, `visual`, `story`, `audio`, `technical`, `price`, `suggestion`, `recommended`
- 推奨分割タイプ: `binary_label`
- レコード数: 約8,800 件
- ドキュメント: [Steamデータセット詳細](../../../../docs/datasets/steam-review-aspect-dataset/README.md)

### Retrieved Concepts（動作確認済み）

- データセット: `retrieved_concepts`
- アスペクト: `concept_0` ～ `concept_299`（300個のコンセプト）
- 推奨分割タイプ: `aspect_vs_bottom100`
- レコード数: 約300,000 件（300コンセプト × 1000件/コンセプト）
- ドキュメント: [Retrieved Conceptsデータセット詳細](../../../../docs/datasets/retrieved-concepts/README.md)
- 実験手順: [retrieved_concepts実験手順](../../../../docs/experiments/playbooks/retrieved-concepts-experiment-guide.md)

### SemEval ABSA（実験的）

- データセット: `semeval`
- アスペクト: `food`, `service`, `atmosphere`, `price`
- 推奨分割タイプ: `aspect_vs_others`
- 注意: データローダーの動作確認が必要

### Amazon Reviews（実験的）

- データセット: `amazon`
- アスペクト: `quality`, `price`, `delivery`, `service`, `product`
- 推奨分割タイプ: `aspect_vs_others`
- 注意: データローダーの動作確認が必要

## エラーハンドリング

パイプラインは以下のエラーを適切に処理します：

- ❌ データセットパスが存在しない → エラーメッセージ表示
- ❌ API キー未設定 → `OPENAI_API_KEY環境変数が設定されていません`
- ❌ アスペクトが存在しない → `アスペクト 'xxx' のレコードが見つかりません`
- ❌ サンプル数不足 → `ポジティブサンプルが不足`
- ❌ LLM API エラー → エラー詳細を表示

## トラブルシューティング

### API キーエラー

```bash
# .envファイルを確認
cat /Users/seinoshun/imrb_research/.env | grep OPENAI_API_KEY

# 環境変数が読み込まれているか確認
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('OPENAI_API_KEY' in os.environ)"
```

### データ読み込みエラー

```bash
# データセットパスを確認
ls -la /Users/seinoshun/imrb_research/data/external/steam-review-aspect-dataset/current/

# データが読み込めるか確認
python test_utils_import.py
```

## 実装詳細

### パイプライン構造

```python
class ExperimentPipeline:
    def __init__(self, config_path, debug=True)
    def validate_config() -> bool
    def setup_dataset_manager() -> bool
    def run_single_experiment(dataset, aspect, group_size, split_type) -> Dict
    def run_batch_experiments() -> List[Dict]
    def save_results(results) -> str
    def print_summary()
    def run() -> bool
```

### 依存モジュール

- `utils.datasetManager.dataset_manager.DatasetManager` - データセット管理
- `utils.cfGenerator.contrast_factor_analyzer.ContrastFactorAnalyzer` - 対比因子分析
- `utils.scores.get_score.calculate_scores` - スコア計算

## 今後の改善点

- [ ] SemEval データセット対応
- [ ] Amazon データセット対応
- [ ] アスペクト説明文を使用した評価
- [ ] LLM ベースの評価追加
- [ ] 並列実行対応
- [ ] 進捗バー表示改善

## 分割タイプの詳細

### binary_label

ポジティブ/ネガティブ分類用の分割タイプです。

- **グループA**: 対象アスペクトでラベル=1（ポジティブ）のレコード
- **グループB**: 対象アスペクトでラベル=0（ネガティブ）のレコード
- **推奨データセット**: Steam

### aspect_vs_others

アスペクト間比較用の汎用的な分割タイプです。

- **グループA**: 対象アスペクトを含むレコード
- **グループB**: 対象アスペクトを含まないレコード（他のアスペクトからランダム抽出）
- **推奨データセット**: SemEval, Amazon

### aspect_vs_bottom100

Top-100 vs Bottom-100比較用の分割タイプです（retrieved_concepts専用）。

- **グループA**: 対象コンセプトのTop-100から抽出（最も類似度が高い画像のキャプション）
- **グループB**: 対象コンセプトのBottom-100から抽出（最も類似度が低い画像のキャプション）
- **推奨データセット**: retrieved_concepts（デフォルト）
- **特徴**: コンセプトに特徴的な要素をより明確に抽出できる

詳細は[実験スクリプト使い方ガイド](../../../../docs/experiments/guides/experiment-script-guide.md)を参照してください。

## 関連ドキュメント

- [実験スクリプト使い方ガイド](../../../../docs/experiments/guides/experiment-script-guide.md)
- [Steam実験手順](../../../../docs/experiments/playbooks/steam-experiment-guide.md)
- [retrieved_concepts実験手順](../../../../docs/experiments/playbooks/retrieved-concepts-experiment-guide.md)
- [トラブルシューティング](../../../../docs/experiments/troubleshooting/common-issues.md)
- [utils ディレクトリ README](../../utils/README.md)
- [データ構造説明](../../../../../data/README.md)
- [実験管理ルール](../../../../../.cursor/rules/)
