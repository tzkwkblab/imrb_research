# Few-shot実験（LLM評価有効） - Steam

このディレクトリは、LLM評価を有効にしたFew-shot実験の結果を論文執筆用に整理したものです。

## 実験概要

**目的**: Few-shot設定（0-shot, 1-shot, 3-shot）の性能比較（LLM評価指標を含む）

**実験設定**:

- **データセット**: Steam
- **アスペクト**: gameplay, visual, story, audio（4アスペクト）
- **Few-shot設定**: 0-shot, 1-shot, 3-shot
- **group_size**: 100
- **GPTモデル**: gpt-4o-mini
- **use_llm_evaluation**: True（gpt-4o-miniによる意味的類似度評価）
- **LLM評価モデル**: gpt-4o-mini
- **LLM評価温度**: 0.0
- **総実験数**: 12実験（4アスペクト × 3Few-shot設定）
- **実行日時**: 2025-11-27

## 主要結果

### Few-shot別の平均スコア

- **0-shot**: BERT=0.5526, LLM=0.3000
- **1-shot**: BERT=0.6530, LLM=0.3500（BERT改善: +0.1004, LLM改善: +0.0500）
- **3-shot**: BERT=0.5754, LLM=0.4000（BERT改善: +0.0228, LLM改善: +0.1000）

### アスペクト別の最高BERTスコア

- **gameplay**: BERT=0.6802, LLM=0.4000
- **story**: BERT=0.8356, LLM=0.6000
- **visual**: BERT=0.6449, LLM=0.2000
- **audio**: BERT=0.5850, LLM=0.2000

## 主要な発見

1. **BERTスコアは1-shotで最高、LLMスコアは3-shotで最高**
   - 評価指標間で最良設定が一致しない（BERTとLLM評価のトレードオフ）

2. **storyで両指標が高い**
   - BERT=0.8356, LLM=0.6000と突出

3. **visualとaudioでLLMスコアが低い**
   - 平均BERT=0.57程度に対してLLM=0.20と低い
   - LLM評価は「人間が読んだときの説明妥当性」に近い評価をしている可能性

4. **LLM評価は自動指標として有用**
   - BERTは「表層概念レベルの一致」、LLMスコアは「人間が読んだときの説明妥当性」に近い評価
   - 特にBLEUのような語彙一致偏重の指標よりも、タスク目的に整合的なシグナルを与えている

## ディレクトリ構造

```
fewshot_llm_eval/steam/
├── 実験結果/
│   ├── batch_results.json          # 統合実験結果（12実験分）
│   └── individual/                  # 個別実験結果（12ファイル）
├── 分析レポート/
│   ├── fewshot_llm_eval_analysis.md           # LLM考察（gpt-5.1）
│   └── fewshot_llm_eval_results_report.md    # 統計サマリー
├── 実験設定/
│   └── fewshot_llm_eval_statistics.json
└── 実行ファイル/
    ├── generate_statistics.py
    ├── generate_report.py
    └── generate_llm_analysis.py
```

## 論文執筆時の参照方法

1. **実験結果の引用**: `実験結果/batch_results.json` から数値を参照
2. **考察の引用**: `分析レポート/fewshot_llm_eval_analysis.md` から LLM 考察を参照
3. **統計情報**: `分析レポート/fewshot_llm_eval_results_report.md` から統計サマリーを参照
4. **統計データ**: `実験設定/fewshot_llm_eval_statistics.json` から詳細統計を参照


