# 実験スクリプト使い方ガイド

本ガイドでは、対比因子生成実験を実行するための2つの方法（対話型スクリプトとコマンドライン実行）について詳しく説明します。

## 目次

1. [対話型スクリプトの使い方](#対話型スクリプトの使い方)
2. [コマンドライン実行の詳細](#コマンドライン実行の詳細)
3. [分割タイプの詳細説明](#分割タイプの詳細説明)
4. [設定ファイルの書き方](#設定ファイルの書き方)
5. [実行例と出力の読み方](#実行例と出力の読み方)

## 対話型スクリプトの使い方

### 起動方法

```bash
cd /Users/seinoshun/imrb_research
source .venv/bin/activate
bash scripts/run_interactive_experiment.sh
```

### 操作手順

#### 1. サイレントモード設定

最初に、サイレントモードを有効にするか選択します。

- **無効（推奨）**: ファイル保存とログ生成が行われます
- **有効**: ファイル保存をスキップし、コンソール出力のみ（デバッグ用途）

#### 2. データセット選択

以下の4つのデータセットから選択できます：

1. **Steam Reviews** (動作確認済み)
   - ゲームレビューデータセット
   - 8つのアスペクト: gameplay, visual, story, audio, technical, price, suggestion, recommended

2. **SemEval ABSA** (実験的)
   - レストランレビューデータセット
   - 4つのアスペクト: food, service, atmosphere, price

3. **Amazon Reviews** (実験的)
   - 商品レビューデータセット
   - 5つのアスペクト: quality, price, delivery, service, product

4. **Retrieved Concepts** (COCO captions, concept_i)
   - COCO画像キャプションデータセット
   - 300個のコンセプト: concept_0 ～ concept_299

#### 3. 正解アスペクトの表現モード選択

アスペクト名をそのまま使うか、説明文を使うかを選択します。

1. **説明文なし**: アスペクト名をそのまま使用（例: "gameplay"）
2. **センテンス（公式）**: 公式CSVの説明文を使用（推奨）
3. **センテンス（任意CSV）**: 任意のCSVファイルから説明文を選択

#### 4. アスペクト選択

データセットに応じて選択方法が異なります：

**Steam/SemEval/Amazonの場合:**
- 番号をカンマ区切りで入力（例: `1,2,3`）
- 複数のアスペクトを一度に選択可能

**Retrieved Conceptsの場合:**
- コンセプトIDを指定（例: `0` / `0,1,2` / `0-9` / `0-4,10,20-25`）
- 範囲指定や複数指定が可能

#### 5. グループサイズ設定

各グループ（A/B）のサンプル数を指定します。

- **テスト**: 10-20（動作確認用）
- **通常**: 50-100（標準的な実験）
- **本格実験**: 200-500（高精度な実験）

デフォルト: 50

#### 6. 分割タイプ選択

3つの分割タイプから選択できます：

1. **aspect_vs_others** (通常のアスペクト比較用)
   - グループA: 対象アスペクトを含むレコード
   - グループB: 対象アスペクトを含まないレコード
   - 汎用的なアスペクト間比較に使用

2. **binary_label** (ネガポジ分類用)
   - グループA: ポジティブラベル（label=1）
   - グループB: ネガティブラベル（label=0）
   - Steamデータセットで推奨

3. **aspect_vs_bottom100** (Top-100 vs Bottom-100)
   - グループA: 対象コンセプトのTop-100から抽出
   - グループB: 対象コンセプトのBottom-100から抽出
   - retrieved_conceptsデータセット専用（デフォルト）

**推奨設定:**
- Steam → `binary_label`
- SemEval/Amazon → `aspect_vs_others`
- retrieved_concepts → `aspect_vs_bottom100`

#### 7. 例題（Few-shot）設定

Few-shot学習を使用するか選択します。

- **使用しない（推奨）**: ゼロショットで実行
- **使用する**: 例題ファイルを指定してFew-shot学習を実行

#### 8. 設定確認と実行

選択した設定を確認し、実行を承認すると実験が開始されます。

### 設定の保存と再利用

対話型スクリプトは、前回の設定を `.experiment_config` に保存します。次回起動時に前回の設定を再利用するか確認されます。

## コマンドライン実行の詳細

### 基本的な使い方

```bash
cd /Users/seinoshun/imrb_research/src/analysis/experiments/2025/10/10
source ../../../../.venv/bin/activate

# 単一アスペクト実験
python run_experiment.py --dataset steam --aspect gameplay --group-size 50

# 複数アスペクト実験
python run_experiment.py --dataset steam --aspects gameplay visual story --group-size 50
```

### オプション一覧

| オプション | 短縮形 | 説明 | デフォルト |
|-----------|--------|------|-----------|
| `--config` | `-c` | 設定ファイルパス | `pipeline_config.yaml` |
| `--dataset` | `-d` | データセット名 | 必須 |
| `--aspect` | `-a` | アスペクト名（単一） | - |
| `--aspects` | - | アスペクト名（複数） | - |
| `--group-size` | `-g` | グループサイズ | 50 |
| `--split-type` | - | 分割タイプ | `binary_label` |
| `--use-aspect-descriptions` | - | アスペクト説明文を使用 | False |
| `--aspect-descriptions-file` | - | 説明文CSVファイルパス | - |
| `--use-examples` | - | Few-shot例題を使用 | False |
| `--examples-file` | - | 例題ファイルパス | - |
| `--max-examples` | - | 使用する例題数 | 全件 |
| `--silent` | - | ファイル保存をスキップ | False |
| `--debug` | - | デバッグモード | True |
| `--output-dir` | - | 出力ディレクトリ | `results/` |

### `--silent`フラグの使い方

`--silent`フラグを使用すると、ファイル保存をスキップしてコンソール出力のみを行います。デバッグや動作確認に便利です。

```bash
python run_experiment.py --dataset retrieved_concepts --aspect concept_0 --group-size 5 --split-type aspect_vs_bottom100 --silent
```

**注意**: `--silent`モードでは結果ファイルは生成されません。

## 分割タイプの詳細説明

### binary_label

**用途**: ポジティブ/ネガティブ分類用

**動作**:
- グループA: 対象アスペクトでラベル=1（ポジティブ）のレコード
- グループB: 対象アスペクトでラベル=0（ネガティブ）のレコード

**推奨データセット**: Steam

**使用例**:
```bash
python run_experiment.py --dataset steam --aspect gameplay --split-type binary_label
```

### aspect_vs_others

**用途**: アスペクト間比較用（汎用）

**動作**:
- グループA: 対象アスペクトを含むレコード
- グループB: 対象アスペクトを含まないレコード（他のアスペクトからランダム抽出）

**推奨データセット**: SemEval, Amazon

**使用例**:
```bash
python run_experiment.py --dataset semeval --aspect food --split-type aspect_vs_others
```

### aspect_vs_bottom100

**用途**: Top-100 vs Bottom-100比較（retrieved_concepts専用）

**動作**:
- グループA: 対象コンセプトのTop-100から抽出（最も類似度が高い画像のキャプション）
- グループB: 対象コンセプトのBottom-100から抽出（最も類似度が低い画像のキャプション）

**推奨データセット**: retrieved_concepts（デフォルト）

**使用例**:
```bash
python run_experiment.py --dataset retrieved_concepts --aspect concept_0 --split-type aspect_vs_bottom100
```

**特徴**:
- コンセプトに特徴的な要素をより明確に抽出できる
- Top-100とBottom-100の対比により、コンセプトの本質的な特徴を浮き彫りにする

## 設定ファイルの書き方

### 基本的な設定ファイル

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

### retrieved_concepts用設定ファイル

```yaml
experiments:
  - dataset: retrieved_concepts
    aspects:
      - concept_0
      - concept_1
      - concept_2
    group_size: 10
    split_type: aspect_vs_bottom100

output:
  directory: results/
  format: json

llm:
  model: gpt-4o-mini
  temperature: 0.7
  max_tokens: 100
```

### 設定ファイルから実行

```bash
python run_experiment.py --config pipeline_config.yaml
```

## 実行例と出力の読み方

### コンソール出力例

```
============================================================
統一実験パイプライン
============================================================

[モード] コマンドライン引数から実行
データセット: retrieved_concepts

==================================================
実験開始: retrieved_concepts_concept_0_20251107_142358
データセット: retrieved_concepts
アスペクト: concept_0
グループサイズ: 5
分割タイプ: aspect_vs_bottom100

[1/3] データ読み込み中...
データセット読み込み: 300000件のレコード
アスペクト 'concept_0' のレコード: 1000件
✅ データ読み込み完了 (A: 5件, B: 5件)
正解ラベル: concept_0 related characteristics

[2/3] 対比因子分析実行中...
✅ LLM応答取得完了

[3/3] スコア確認中...
✅ スコア確認完了

==================================================
=== 結果 ===
BERTスコア: 0.6133
BLEUスコア: 0.0000
LLM応答: Everyday objects and solitary scenes.
品質評価: poor

📁 結果保存: results/batch_experiment_20251107_142358.json

✅ パイプライン実行完了
```

### 出力の読み方

- **BERTスコア**: 意味的類似度（0.0-1.0、高いほど良い）
- **BLEUスコア**: 語彙的一致度（0.0-1.0、高いほど良い）
- **LLM応答**: 生成された対比因子ラベル
- **品質評価**: poor / medium / good（BERT/BLEUスコアの平均に基づく）

### JSON結果ファイル

結果は `results/batch_experiment_*.json` に保存されます。

```json
{
  "experiment_meta": {
    "timestamp": "20251107_142358",
    "total_experiments": 1,
    "successful_experiments": 1
  },
  "results": [
    {
      "experiment_info": {
        "dataset": "retrieved_concepts",
        "aspect": "concept_0",
        "group_size": 5,
        "split_type": "aspect_vs_bottom100"
      },
      "input": {
        "group_a": [...],
        "group_b": [...]
      },
      "process": {
        "prompt": "...",
        "llm_response": "Everyday objects and solitary scenes."
      },
      "evaluation": {
        "bert_score": 0.6133,
        "bleu_score": 0.0
      }
    }
  ]
}
```

## 関連ドキュメント

- [Steamデータセット実験手順](../playbooks/steam-experiment-guide.md)
- [retrieved_conceptsデータセット実験手順](../playbooks/retrieved-concepts-experiment-guide.md)
- [トラブルシューティング](../troubleshooting/common-issues.md)
- [統一パイプラインREADME](../../../src/analysis/experiments/2025/10/10/README.md)

