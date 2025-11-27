# 追加実験ディレクトリ

論文執筆に必要な追加実験の実行ファイルと結果を管理するディレクトリです。

## ディレクトリ構造

```
追加実験/
├── 論文執筆用/            # 論文執筆用に整理された結果（推奨）
│   ├── model_comparison/
│   │   ├── 実験結果/
│   │   ├── 分析レポート/
│   │   └── 実験設定/
│   └── fewshot/
│       └── steam/
│           ├── 実験結果/
│           ├── 分析レポート/
│           └── 実験設定/
├── fewshot/               # Few-shot実験（実行用）
│   └── steam/
│       ├── README.md
│       ├── マトリックス/
│       │   └── steam_fewshot_matrix.json
│       └── 実行ファイル/
│           ├── generate_steam_fewshot_matrix.py
│           └── collect_fewshot_results.py
├── group_size_steam/      # Group Size実験（実行用）
│   ├── README.md
│   ├── マトリックス/
│   │   └── steam_group_size_matrix.json
│   └── 実行ファイル/
│       └── generate_group_size_matrix.py
├── model_comparison/      # モデル比較実験（実行用）
    ├── README.md
    ├── 実験パラメータ.md
    ├── マトリックス/
    │   └── steam_model_comparison_matrix.json
    └── 実行ファイル/
        └── generate_model_comparison_matrix.py
└── retrieved_concepts/    # Retrieved Concepts実験（論文執筆用）
    └── README.md
```

## 論文執筆用ディレクトリ

**論文執筆時は `論文執筆用/` ディレクトリを参照してください。**

各実験カテゴリごとに以下の構造で整理されています：

- **実験結果/**: 実験結果 JSON ファイル（batch_results.json, individual/）
- **分析レポート/**: LLM 考察と統計レポート
- **実験設定/**: 実験パラメータとマトリックス

詳細は [`論文執筆用/README.md`](論文執筆用/README.md) を参照してください。

## デフォルト設定

追加実験では、以下の設定がデフォルトとして使用されます。サブ実験で明示的に設定を変更する場合を除き、すべての実験でこれらの値が適用されます：

- **max_tokens**: 1000
- **group_size**: 100
- **評価指標**: LLM 評価を使用（use_llm_evaluation: true）
- **アスペクト**: 単語

各サブ実験のパラメータ説明では、デフォルトから変更がある場合のみ記載しています。

## 実験内容

### 1. Steam Few-shot 実験 (`fewshot/steam/`)

**目的**: Few-shot 設定（0-shot, 1-shot, 3-shot）の性能比較

**パラメータ**:

- **データセット**: Steam
- **アスペクト**: gameplay, visual, story, audio（4 アスペクト）
- **Few-shot 設定**: 0-shot, 1-shot, 3-shot
- **group_size**: 100
- **LLM 評価**: 無効（use_llm_evaluation: false）
- **GPT モデル**: gpt-4o-mini
- **総実験数**: 12 実験（4 アスペクト × 3Few-shot 設定）

詳細は `fewshot/steam/README.md` を参照。

### 2. Steam モデル比較実験 (`model_comparison/`)

**目的**: gpt-4o-mini と gpt-5.1 の性能比較

**パラメータ**:

- **データセット**: Steam
- **アスペクト**: gameplay, visual, story, audio（4 アスペクト）
- **GPT モデル**: gpt-4o-mini, gpt-5.1（2 モデル）
- **group_size**: 100
- **few_shot**: 0（固定）
- **use_llm_evaluation**: False
- **総実験数**: 8 実験（4 アスペクト × 2 モデル）

詳細は `model_comparison/README.md` と `model_comparison/実験パラメータ.md` を参照。

### 3. Steam Group Size 実験 (`group_size_steam/`)

**目的**: group_size の変化による性能への影響調査

**パラメータ**:

- **データセット**: Steam
- **アスペクト**: gameplay, visual, story, audio（4 アスペクト）
- **group_size**: 50, 100, 150, 200, 300（5 段階）
- **few_shot**: 0（固定）
- **LLM 評価**: 有効（use_llm_evaluation: true）
- **GPT モデル**: gpt-4o-mini（固定）
- **総実験数**: 20 実験（4 アスペクト × 5group_size 設定）

詳細は `group_size_steam/README.md` を参照。

### 4. Retrieved Concepts 実験 (`retrieved_concepts/`)

**目的**: 正解ラベルがないデータセット（COCO Captions）に対する対比因子生成の考察

**パラメータ**:

- **データセット**: Retrieved Concepts (COCO Captions)
- **コンセプト**: concept_0, concept_1, concept_2, concept_10, concept_50（5 コンセプト）
- **GPT モデル**: gpt-4o-mini, gpt-5.1（2 モデル）
- **group_size**: 50（固定）
- **few_shot**: 0（固定）
- **use_llm_evaluation**: False
- **総実験数**: 10 実験（5 コンセプト × 2 モデル）

**特徴**:

- 正解ラベルがないため、BERT/BLEU スコアは参考値として扱う
- 生成された対比因子と画像を見比べて考察することが重要
- 0-shot 設定で実行

詳細は `retrieved_concepts/README.md` を参照。

## 実験実行方法

### Few-shot 実験

```bash
# 1. マトリックスの生成
python 論文/結果/追加実験/fewshot/steam/実行ファイル/generate_steam_fewshot_matrix.py

# 2. 実験の実行
python src/analysis/experiments/2025/10/10/run_batch_from_matrix.py \
  --matrix 論文/結果/追加実験/fewshot/steam/マトリックス/steam_fewshot_matrix.json \
  --background
```

### Group Size 実験

```bash
# 1. マトリックスの生成
python 論文/結果/追加実験/group_size_steam/実行ファイル/generate_group_size_matrix.py

# 2. 実験の実行
python src/analysis/experiments/2025/10/10/run_batch_from_matrix.py \
  --matrix 論文/結果/追加実験/group_size_steam/マトリックス/steam_group_size_matrix.json \
  --background
```

### モデル比較実験

```bash
# 1. 実験の実行
python src/analysis/experiments/2025/10/10/run_batch_from_matrix.py \
  --matrix 論文/結果/追加実験/model_comparison/マトリックス/steam_model_comparison_matrix.json \
  --output-dir 論文/結果/追加実験/model_comparison/results \
  --background

# 2. 実行状態確認
python src/analysis/experiments/2025/10/10/run_batch_from_matrix.py \
  --status \
  --output-dir 論文/結果/追加実験/model_comparison/results
```

## 評価指標

各実験で以下の評価指標を使用：

- **BERT スコア**: 意味類似度評価
- **BLEU スコア**: n-gram 一致率評価
- **LLM 評価**: Group Size 実験のみ有効（GPT-4o-mini による意味的類似度評価）

## LLM 考察取得

実験結果を LLM（gpt-5.1）に問い合わせて考察を自動生成する機能があります。

### 実行方法

```bash
# Few-shot実験の考察取得
python 論文/結果/追加実験/fewshot/steam/実行ファイル/generate_fewshot_analysis.py
```

### 詳細な実装手順

新しい追加実験で LLM 考察を取得する場合は、以下のガイドを参照してください：

- **[LLM 考察取得ガイド](LLM考察取得ガイド.md)**: 実装手順、カスタマイズ方法、トラブルシューティング

### 実装例

- **Few-shot 実験**: `fewshot/steam/実行ファイル/generate_fewshot_analysis.py`
- **モデル比較実験**: `model_comparison/実行ファイル/generate_model_comparison_analysis.py`
- **出力例**:
  - `fewshot/steam/fewshot_analysis.md`
  - `model_comparison/model_comparison_analysis.md`

## 論文執筆時の参照

論文執筆時は、`論文執筆用/` ディレクトリ内の整理されたファイルを参照してください：

- **実験結果**: `論文執筆用/{実験カテゴリ}/実験結果/`
- **分析レポート**: `論文執筆用/{実験カテゴリ}/分析レポート/`
- **実験設定**: `論文執筆用/{実験カテゴリ}/実験設定/`

各実験カテゴリの詳細は、`論文執筆用/{実験カテゴリ}/README.md` を参照してください。

## 重要: パラメータ設定の確認

**ディレクトリ名に`temperature0`が付いていない実験は、パラメータの`temperature`が間違っている可能性があります。**

### 完了済み実験

- `main_experiment_rerun_temperature0/` - **完了済み**（temperature=0.0 で実行）

### 再実験が必要な実験

以下の実験は、ディレクトリ名に`temperature0`が付いていないため、パラメータの`temperature`設定を再確認し、必要に応じて再実験が必要です：

- `fewshot/steam/` - temperature 設定を確認し、必要に応じて再実験
- `group_size_steam/` - temperature 設定を確認し、必要に応じて再実験
- `model_comparison/` - temperature 設定を確認し、必要に応じて再実験
- `retrieved_concepts/` - temperature 設定を確認し、必要に応じて再実験

**再実験の判断基準**:

- 実験マトリックス JSON の`experiment_plan.settings.temperature`が`0.0`になっているか確認
- `0.0`以外の値（例: `0.7`）が設定されている場合は、`temperature0`サフィックスを付けたディレクトリで再実験を実行
