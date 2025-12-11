# モデル比較実験（temperature=0版）

## 実験概要

**目的**: Steamデータセットでのgpt-4o-miniとgpt-5.1の性能比較（temperature=0設定）  
**総実験数**: 8実験  
**実行日時**: 2025-11-27

## 実験パラメータ

| パラメータ | 値 |
|-----------|-----|
| データセット | steam |
| アスペクト | gameplay, visual, story, audio (4つ) |
| GPTモデル | gpt-4o-mini, gpt-5.1 (2つ) |
| group_size | 100 (固定) |
| few_shot | 0 (固定) |
| temperature | 0.0 (生成モデル) |
| max_tokens | 100 |
| use_llm_evaluation | True |
| llm_evaluation_model | gpt-4o |
| llm_evaluation_temperature | 0.0 |
| split_type | aspect_vs_others |
| use_aspect_descriptions | False |

## 主要結果

### モデル別の平均スコア

- **gpt-4o-mini**: BERT=0.5453, LLM=0.3000
- **gpt-5.1**: BERT=0.5375, LLM=0.2500

### アスペクト別の比較

| アスペクト | gpt-4o-mini (BERT) | gpt-5.1 (BERT) | 差 | gpt-4o-mini (LLM) | gpt-5.1 (LLM) | 差 |
|----------|-------------------|---------------|-----|------------------|--------------|-----|
| gameplay | 0.5600 | 0.5423 | +0.0177 | 0.4000 | 0.2000 | +0.2000 |
| visual | 0.5425 | 0.5287 | +0.0138 | 0.2000 | 0.2000 | 0.0000 |
| story | 0.5573 | 0.5167 | +0.0406 | 0.4000 | 0.4000 | 0.0000 |
| audio | 0.5214 | 0.5621 | -0.0407 | 0.2000 | 0.2000 | 0.0000 |

## 主要ファイル

- **実験結果**: `実験結果/batch_results.json` - 統合実験結果（8実験分）
- **個別結果**: `実験結果/individual/` - 各実験の詳細結果（8ファイル）
- **LLM考察**: `分析レポート/model_comparison_temperature0_analysis.md` - gpt-5.1による詳細考察
- **統計レポート**: `分析レポート/model_comparison_temperature0_results_report.md` - 統計サマリー
- **統計情報**: `実験設定/model_comparison_temperature0_statistics.json` - モデル別・アスペクト別統計
- **実験マトリックス**: `実験設定/steam_model_comparison_temperature0_matrix.json` - 実験計画とパラメータ
- **実験パラメータ**: `実験設定/実験パラメータ.md` - 実験パラメータの詳細

## 主要な発見

1. **モデル間の性能差**
   - 平均BERTスコアではgpt-4o-miniがわずかに優位（0.5453 vs 0.5375）
   - LLMスコアでもgpt-4o-miniが優位（0.3000 vs 0.2500）
   - アスペクトによって優劣が異なる（audioではgpt-5.1が優位）

2. **temperature=0設定での特性**
   - 決定論的な出力設定での対比因子抽出の特性を確認
   - BERTスコアとLLMスコアの関係性が明らかになった
   - 0-shot設定でも実用的な対比因子抽出が可能

3. **アスペクト特性とモデル性能**
   - gameplayとstoryでgpt-4o-miniが優位
   - audioではgpt-5.1が優位
   - visualでは両モデルともLLMスコアが低い（0.2000）

4. **研究への貢献**
   - temperature=0でも実用的な対比因子抽出が可能
   - LLM評価指標の有用性を確認
   - モデル選択の実用的な指針を提供

## 論文執筆時の参照方法

1. **実験結果の引用**: `実験結果/batch_results.json`から数値を参照
2. **考察の引用**: `分析レポート/model_comparison_temperature0_analysis.md`からLLM考察を参照
3. **統計情報**: `分析レポート/model_comparison_temperature0_results_report.md`から統計サマリーを参照
4. **実験設定の確認**: `実験設定/`から実験パラメータを確認












