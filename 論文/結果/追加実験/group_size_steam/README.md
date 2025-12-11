# Steamデータセット Group Size実験

## ディレクトリ構造

```
group_size_steam/
├── 実行ファイル/          # 実験マトリックス生成スクリプト
│   └── generate_group_size_matrix.py
├── マトリックス/          # 実験マトリックスJSON
│   └── steam_group_size_matrix.json
└── README.md
```

## 実験内容

### データセット
- **データセット**: Steam
- **アスペクト**: gameplay, visual, story, audio（4アスペクト）

### Group Size設定
- **50**: グループサイズ50
- **100**: グループサイズ100
- **150**: グループサイズ150
- **200**: グループサイズ200
- **300**: グループサイズ300

### 実験パラメータ
- **few_shot**: 0（固定）
- **LLM評価**: 有効（use_llm_evaluation: true）
- **GPTモデル**: gpt-4o-mini（固定）
- **分割タイプ**: aspect_vs_others

### 評価指標
- **BERTスコア**: 意味類似度評価
- **BLEUスコア**: n-gram一致率評価
- **LLM評価**: GPT-4o-miniによる意味的類似度評価

## 実験数
- **総実験数**: 20実験
- **構成**: 4アスペクト × 5group_size設定 = 20実験

## 使用方法

### 1. マトリックスの生成
```bash
python 論文/結果/追加実験/group_size_steam/実行ファイル/generate_group_size_matrix.py
```

### 2. 実験の実行
```bash
python src/analysis/experiments/2025/10/10/run_batch_from_matrix.py \
  --matrix 論文/結果/追加実験/group_size_steam/マトリックス/steam_group_size_matrix.json \
  --background
```

### 3. 結果の確認
実験結果は `results/{timestamp}/` に保存されます。












