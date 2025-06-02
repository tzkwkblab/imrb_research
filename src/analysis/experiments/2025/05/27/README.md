# テキスト類似度評価システム

このディレクトリには、GPTが生成した特徴記述と元の特徴記述の類似度を評価するためのシステムが含まれています。

## ファイル構成

### 実行スクリプト
- `text_similarity_evaluator.py`: メインの類似度評価スクリプト（BERT・BLEU評価）
- `analysis_report_generator.py`: 詳細分析レポートと可視化生成スクリプト

### 設定・依存関係
- `requirements.txt`: 必要なPythonライブラリ一覧

### 結果ファイル
- `similarity_evaluation_results.json`: 評価結果（JSON形式）
- `similarity_evaluation_results.csv`: 評価結果（CSV形式）
- `detailed_analysis_report.md`: 詳細分析レポート

### 可視化ファイル
- `similarity_comparison.png`: BERT・BLEU類似度の比較棒グラフ
- `bert_vs_bleu_scatter.png`: BERT vs BLEU類似度の散布図

### ドキュメント
- `memo.md`: 実験記録とメモ
- `README.md`: このファイル

## 使用方法

### 1. 環境設定
```bash
pip install -r requirements.txt
```

### 2. 類似度評価の実行
```bash
python text_similarity_evaluator.py
```

### 3. 詳細分析レポートの生成
```bash
python analysis_report_generator.py
```

## 評価指標

### BERT類似度
- Sentence-BERT（all-MiniLM-L6-v2）を使用
- コサイン類似度で計算
- 0～1の範囲（1が最も類似）
- 意味的類似性を評価

### BLEU類似度  
- n-gram一致に基づく評価
- 0～1の範囲（1が完全一致）
- 語彙・語順の類似性を評価

## 結果の解釈

- **BERT類似度が高い**: 意味的に類似している
- **BLEU類似度が高い**: 語彙・表現が類似している
- **BERT高・BLEU低**: 意味は同じだが表現が異なる（パラフレーズ）
- **BERT低・BLEU高**: 表現は似ているが意味が異なる

## システムの特徴

1. **自動評価**: 人手を介さない客観的評価
2. **多角的評価**: 意味と表現の両面から評価
3. **可視化対応**: グラフによる結果の視覚化
4. **詳細分析**: 特徴別の詳細な分析レポート

## 技術スタック

- Python 3.8+
- Sentence Transformers（BERT評価）
- NLTK（BLEU評価）
- pandas（データ処理）
- matplotlib/seaborn（可視化）