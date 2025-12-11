# Steam Few-shot実験

## ディレクトリ構造

```
fewshot/steam/
├── 実行ファイル/          # 実験マトリックス生成スクリプト
│   └── generate_steam_fewshot_matrix.py
└── マトリックス/          # 実験マトリックスJSON
    └── steam_fewshot_matrix.json
```

## 実験内容

### データセット
- **データセット**: Steam
- **アスペクト**: gameplay, visual, story, audio（4アスペクト）

### Few-shot設定
- **0-shot**: 例題なし
- **1-shot**: 例題1個
- **3-shot**: 例題3個

### 実験パラメータ
- **group_size**: 100
- **LLM評価**: 無効（use_llm_evaluation: false）
- **GPTモデル**: gpt-4o-mini
- **例題ファイル**: `data/analysis-workspace/contrast_examples/steam/steam_examples_v1.json`

### 評価指標
- **BERTスコア**: 意味類似度評価
- **BLEUスコア**: n-gram一致率評価

## 実験数
- **総実験数**: 12実験
- **構成**: 4アスペクト × 3Few-shot設定 = 12実験

## 使用方法

### 1. マトリックスの生成
```bash
python 論文/結果/追加実験/fewshot/steam/実行ファイル/generate_steam_fewshot_matrix.py
```

### 2. 実験の実行
```bash
python src/analysis/experiments/2025/10/10/run_batch_from_matrix.py \
  --matrix 論文/結果/追加実験/fewshot/steam/マトリックス/steam_fewshot_matrix.json \
  --background
```

### 3. 結果の確認
実験結果は `results/{timestamp}/` に保存されます。












