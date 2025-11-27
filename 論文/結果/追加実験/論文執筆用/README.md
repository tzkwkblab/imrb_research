# 追加実験 - 論文執筆用ディレクトリ

このディレクトリは、論文執筆時に参照しやすいように追加実験の結果を整理したものです。

## 📖 包括的な参照ガイド

**論文執筆時は、まず以下のガイドを参照してください：**

👉 **[追加実験結果参照ガイド.md](追加実験結果参照ガイド.md)** - 追加実験の全体像を把握し、必要な情報を迅速に参照するための包括的なガイド

このガイドには以下が含まれています：

- 追加実験の全体概要と目的
- 各実験の詳細（設定、結果、発見）
- 実験間の関係性と統合的考察
- 論文執筆時の具体的な参照方法
- 主要な発見と論文への反映方法

## ディレクトリ構造

```
論文執筆用/
├── model_comparison/          # モデル比較実験
│   ├── 実験結果/              # 実験結果JSONファイル
│   ├── 分析レポート/          # LLM考察と統計レポート
│   └── 実験設定/              # 実験パラメータとマトリックス
├── example_fewshot/           # Few-shot実験（LLM評価無効）
│   └── steam/
│       ├── 実験結果/
│       ├── 分析レポート/
│       └── 実験設定/
└── fewshot_llm_eval/          # Few-shot実験（LLM評価有効）
    └── steam/
        ├── 実験結果/
        ├── 分析レポート/
        └── 実験設定/
```

## 各実験の概要

### 1. モデル比較実験 (`model_comparison/`)

**目的**: gpt-4o-mini と gpt-5.1 の性能比較

**主要ファイル**:

- **実験結果**: `実験結果/batch_results.json` - 統合実験結果
- **LLM 考察**: `分析レポート/model_comparison_analysis.md` - gpt-5.1 による詳細考察
- **統計レポート**: `分析レポート/実験結果レポート.md` - 統計サマリー
- **実験設定**: `実験設定/実験パラメータ.md` - 実験パラメータの詳細

**主要結果**:

- 平均 BERT スコア: gpt-4o-mini=0.5402, gpt-5.1=0.5404（ほぼ同等）
- アスペクトによって優劣が異なる

### 2. Few-shot 実験（LLM 評価無効） (`example_fewshot/steam/`)

**目的**: Few-shot 設定（0-shot, 1-shot, 3-shot）の性能比較

**実験設定**:

- **データセット**: Steam
- **アスペクト**: gameplay, visual, story, audio（4 アスペクト）
- **Few-shot 設定**: 0-shot, 1-shot, 3-shot
- **group_size**: 100
- **GPT モデル**: gpt-4o-mini
- **use_llm_evaluation**: False
- **総実験数**: 12 実験（4 アスペクト × 3Few-shot 設定）

**主要ファイル**:

- **実験結果**: `実験結果/batch_results.json` - 統合実験結果（12 実験分）
- **個別結果**: `実験結果/individual/` - 各実験の詳細結果（12 ファイル）
- **LLM 考察**: `分析レポート/fewshot_analysis.md` - gpt-5.1 による詳細考察（1000 文字程度）
- **統計レポート**: `分析レポート/fewshot_results_report.md` - 統計サマリーと主要発見
- **統計情報**: `実験設定/fewshot_statistics.json` - Few-shot 別・アスペクト別統計
- **実験マトリックス**: `実験設定/steam_fewshot_matrix.json` - 実験計画とパラメータ

**主要結果**:

- **Few-shot 別平均 BERT スコア**:
  - 0-shot: 0.5676
  - 1-shot: 0.6438（+0.0762）
  - 3-shot: 0.6899（+0.1223）
- **アスペクト別最高 BERT スコア（3-shot）**:
  - gameplay: 0.7925
  - story: 0.7676
  - visual: 0.6347
  - audio: 0.5647
- **主要発見**:
  - Few-shot 設定が性能向上に寄与（特に 0→1-shot で大きな改善）
  - gameplay と story で 3-shot の効果が特に大きい
  - 平均 BERT スコア 0.69 は、LLM による対比因子ラベル自動生成の実現可能性を示す

### 3. Few-shot 実験（LLM 評価有効） (`fewshot_llm_eval/steam/`)

**目的**: Few-shot 設定（0-shot, 1-shot, 3-shot）の性能比較（LLM 評価指標を含む）

**実験設定**:

- **データセット**: Steam
- **アスペクト**: gameplay, visual, story, audio（4 アスペクト）
- **Few-shot 設定**: 0-shot, 1-shot, 3-shot
- **group_size**: 100
- **GPT モデル**: gpt-4o-mini
- **use_llm_evaluation**: True（gpt-4o-mini による意味的類似度評価）
- **総実験数**: 12 実験（4 アスペクト × 3Few-shot 設定）
- **実行日時**: 2025-11-27

**主要ファイル**:

- **実験結果**: `実験結果/batch_results.json` - 統合実験結果（12 実験分）
- **個別結果**: `実験結果/individual/` - 各実験の詳細結果（12 ファイル）
- **LLM 考察**: `分析レポート/fewshot_llm_eval_analysis.md` - gpt-5.1 による詳細考察
- **統計レポート**: `分析レポート/fewshot_llm_eval_results_report.md` - 統計サマリーと主要発見
- **統計情報**: `実験設定/fewshot_llm_eval_statistics.json` - Few-shot 別・アスペクト別統計（LLM 評価含む）

**主要結果**:

- **Few-shot 別平均スコア**:
  - 0-shot: BERT=0.5526, LLM=0.3000
  - 1-shot: BERT=0.6530, LLM=0.3500（BERT 改善: +0.1004, LLM 改善: +0.0500）
  - 3-shot: BERT=0.5754, LLM=0.4000（BERT 改善: +0.0228, LLM 改善: +0.1000）
- **アスペクト別最高 BERT スコア**:
  - gameplay: BERT=0.6802, LLM=0.4000
  - story: BERT=0.8356, LLM=0.6000
  - visual: BERT=0.6449, LLM=0.2000
  - audio: BERT=0.5850, LLM=0.2000
- **主要発見**:
  - BERT スコアは 1-shot で最高（0.6530）、LLM スコアは 3-shot で最高（0.4000）
  - 評価指標間で最良設定が一致しない（BERT と LLM 評価のトレードオフ）
  - story で両指標が高い（BERT=0.8356, LLM=0.6000）
  - visual と audio で LLM スコアが低い（0.2000）が、BERT スコアは中程度
  - LLM 評価は「人間が読んだときの説明妥当性」に近い評価をしている可能性

## 論文執筆時の参照方法

1. **実験結果の引用**: `実験結果/batch_results.json` から数値を参照
2. **考察の引用**: `分析レポート/*_analysis.md` から LLM 考察を参照
3. **統計情報**: `分析レポート/*_results_report.md` から統計サマリーを参照
4. **実験設定の確認**: `実験設定/` から実験パラメータを確認

## 注意事項

- このディレクトリは論文執筆用の整理版です
- 実行ファイルや詳細なログは元のディレクトリ（`model_comparison/`, `fewshot/`）にあります
- 新しい追加実験を追加する場合は、同じ構造で整理してください
