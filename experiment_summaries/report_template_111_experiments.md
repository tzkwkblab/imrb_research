# 実験レポート：71 実験（メイン 37 + サブ 34）

**実験実行日**: {{EXPERIMENT_DATE}}  
**実験実行時刻**: {{EXPERIMENT_TIMESTAMP}}  
**総実験数**: 71 実験  
**成功実験数**: {{SUCCESSFUL_EXPERIMENTS}} / 71

---

## 1. 実験構成

### 1.1 メイン実験（37 実験）

データセット別の性能比較を目的とした基本実験。**group_size=100 に統一**。

| データセット | アスペクト数 | 実験数 | アスペクト一覧                             |
| ------------ | ------------ | ------ | ------------------------------------------ |
| Steam        | 4            | 4      | gameplay, visual, story, audio             |
| Amazon       | 5            | 5      | quality, price, delivery, service, product |
| GoEmotions   | 28           | 28     | 全 28 アスペクト                           |
| SemEval      | 4            | 4      | food, service, battery, screen             |

**設定**:

- Few-shot: 1
- GPT モデル: gpt-4o-mini
- LLM 評価: 有効
- アスペクト説明文: 使用しない（単語比較）
- **group_size: 100**（コンテキスト長超過を防ぐため）

### 1.2 サブ実験（34 実験）

#### 1.2.1 Steam データセット - group_size 変化による影響調査（24 実験）

**目的**: 問題数（group_size）による性能変化を検証

**実験パターン**:

- group_size: 50, 100, 150, 200, 300（5 パターン）
- アスペクト: gameplay, visual, story, audio（4 種類）
- Few-shot: 1
- GPT モデル: gpt-4o-mini
- **合計**: 20 実験

**gpt-5.1 での group_size=300 検証（4 実験）**:

- group_size: 300
- アスペクト: gameplay, visual, story, audio（4 種類）
- Few-shot: 1
- GPT モデル: gpt-5.1（コンテキスト長調整可能モデル）
- **目的**: コンテキスト長を調整できるモデルで group_size=300 が実行可能か検証

#### 1.2.2 Retrieved Concepts (COCO) - 別枠実験（10 実験）

**目的**: 正解のないデータセットに対する対比因子生成の考察

**設定**:

- Few-shot: 0
- GPT モデル: gpt-4o-mini, gpt-5.1（両方）
- LLM 評価: 無効
- アスペクト説明文: 使用しない（単語比較）
- group_size: 50
- コンセプト: concept_0, concept_1, concept_2, concept_10, concept_50（5 個 × 2 モデル = 10 実験）

**注意**: スコアは参考値。出力された対比因子と画像を見比べて考察。

---

## 2. メイン実験結果

### 2.1 Steam データセット（4 アスペクト、group_size=100）

| アスペクト | BERT | BLEU | LLM | LLM 理由 |
| ---------- | ---- | ---- | --- | -------- |
| gameplay   | -    | -    | -   | -        |
| visual     | -    | -    | -   | -        |
| story      | -    | -    | -   | -        |
| audio      | -    | -    | -   | -        |

**平均スコア**:

- BERT 平均: -
- BLEU 平均: -
- LLM 平均: -

### 2.2 Amazon データセット（5 アスペクト、group_size=100）

| アスペクト | BERT | BLEU | LLM | LLM 理由 |
| ---------- | ---- | ---- | --- | -------- |
| quality    | -    | -    | -   | -        |
| price      | -    | -    | -   | -        |
| delivery   | -    | -    | -   | -        |
| service    | -    | -    | -   | -        |
| product    | -    | -    | -   | -        |

**平均スコア**:

- BERT 平均: -
- BLEU 平均: -
- LLM 平均: -

### 2.3 GoEmotions データセット（28 アスペクト、group_size=100）

| アスペクト     | BERT | BLEU | LLM | LLM 理由 |
| -------------- | ---- | ---- | --- | -------- |
| admiration     | -    | -    | -   | -        |
| amusement      | -    | -    | -   | -        |
| anger          | -    | -    | -   | -        |
| annoyance      | -    | -    | -   | -        |
| approval       | -    | -    | -   | -        |
| caring         | -    | -    | -   | -        |
| confusion      | -    | -    | -   | -        |
| curiosity      | -    | -    | -   | -        |
| desire         | -    | -    | -   | -        |
| disappointment | -    | -    | -   | -        |
| disapproval    | -    | -    | -   | -        |
| disgust        | -    | -    | -   | -        |
| embarrassment  | -    | -    | -   | -        |
| excitement     | -    | -    | -   | -        |
| fear           | -    | -    | -   | -        |
| gratitude      | -    | -    | -   | -        |
| grief          | -    | -    | -   | -        |
| joy            | -    | -    | -   | -        |
| love           | -    | -    | -   | -        |
| nervousness    | -    | -    | -   | -        |
| optimism       | -    | -    | -   | -        |
| pride          | -    | -    | -   | -        |
| realization    | -    | -    | -   | -        |
| relief         | -    | -    | -   | -        |
| remorse        | -    | -    | -   | -        |
| sadness        | -    | -    | -   | -        |
| surprise       | -    | -    | -   | -        |
| neutral        | -    | -    | -   | -        |

**平均スコア**:

- BERT 平均: -
- BLEU 平均: -
- LLM 平均: -

### 2.4 SemEval データセット（4 アスペクト、group_size=100）

| ドメイン   | アスペクト | BERT | BLEU | LLM | LLM 理由 |
| ---------- | ---------- | ---- | ---- | --- | -------- |
| restaurant | food       | -    | -    | -   | -        |
| restaurant | service    | -    | -    | -   | -        |
| laptop     | battery    | -    | -    | -   | -        |
| laptop     | screen     | -    | -    | -   | -        |

**平均スコア**:

- BERT 平均: -
- BLEU 平均: -
- LLM 平均: -

### 2.5 メイン実験全体サマリー

| データセット | アスペクト数 | BERT 平均 | BLEU 平均 | LLM 平均 |
| ------------ | ------------ | --------- | --------- | -------- |
| Steam        | 4            | -         | -         | -        |
| Amazon       | 5            | -         | -         | -        |
| GoEmotions   | 28           | -         | -         | -        |
| SemEval      | 4            | -         | -         | -        |
| **全体平均** | **37**       | **-**     | **-**     | **-**    |

---

## 3. サブ実験結果

### 3.1 Steam データセット - group_size 変化による影響調査（20 実験）

**gpt-4o-mini での group_size 変化**

| アスペクト | group_size=50 | group_size=100 | group_size=150 | group_size=200 | group_size=300 |
| ---------- | ------------- | -------------- | -------------- | -------------- | -------------- |
|            | BERT/BLEU/LLM | BERT/BLEU/LLM  | BERT/BLEU/LLM  | BERT/BLEU/LLM  | BERT/BLEU/LLM  |
| gameplay   | -/-/-         | -/-/-          | -/-/-          | -/-/-          | -/-/-          |
| visual     | -/-/-         | -/-/-          | -/-/-          | -/-/-          | -/-/-          |
| story      | -/-/-         | -/-/-          | -/-/-          | -/-/-          | -/-/-          |
| audio      | -/-/-         | -/-/-          | -/-/-          | -/-/-          | -/-/-          |

**分析**:

- group_size による性能変化: -
- 最適な group_size: -
- コンテキスト長超過エラーの発生状況: -

### 3.2 Steam データセット - gpt-5.1 での group_size=300 検証（4 実験）

**目的**: コンテキスト長を調整できるモデル（gpt-5.1）で group_size=300 が実行可能か検証

| アスペクト | gpt-5.1 BERT | gpt-5.1 BLEU | gpt-5.1 LLM | エラー発生 |
| ---------- | ------------ | ------------ | ----------- | ---------- |
| gameplay   | -            | -            | -           | -          |
| visual     | -            | -            | -           | -          |
| story      | -            | -            | -           | -          |
| audio      | -            | -            | -           | -          |

**分析**:

- gpt-5.1 での group_size=300 実行可能性: -
- gpt-4o-mini との性能比較: -
- コンテキスト長調整の効果: -

### 3.3 Retrieved Concepts (COCO) - 別枠実験（10 実験）

**注意**: この実験は正解ラベルがないため、BERT/BLEU スコアは参考値です。出力された対比因子と画像を見比べて考察します。

| コンセプト | モデル      | BERT（参考） | BLEU（参考） | 対比因子出力 | 画像との整合性 |
| ---------- | ----------- | ------------ | ------------ | ------------ | -------------- |
| concept_0  | gpt-4o-mini | -            | -            | -            | -              |
| concept_0  | gpt-5.1     | -            | -            | -            | -              |
| concept_1  | gpt-4o-mini | -            | -            | -            | -              |
| concept_1  | gpt-5.1     | -            | -            | -            | -              |
| concept_2  | gpt-4o-mini | -            | -            | -            | -              |
| concept_2  | gpt-5.1     | -            | -            | -            | -              |
| concept_10 | gpt-4o-mini | -            | -            | -            | -              |
| concept_10 | gpt-5.1     | -            | -            | -            | -              |
| concept_50 | gpt-4o-mini | -            | -            | -            | -              |
| concept_50 | gpt-5.1     | -            | -            | -            | -              |

**考察**:

- モデル間の出力の違い: -
- コンセプト別の特徴: -
- 画像との整合性: -

---

## 4. 総合分析

### 4.1 データセット別性能比較（group_size=100 統一）

| データセット | アスペクト数 | BERT 平均 | BLEU 平均 | LLM 平均 | 特徴 |
| ------------ | ------------ | --------- | --------- | -------- | ---- |
| Steam        | 4            | -         | -         | -        | -    |
| Amazon       | 5            | -         | -         | -        | -    |
| GoEmotions   | 28           | -         | -         | -        | -    |
| SemEval      | 4            | -         | -         | -        | -    |

### 4.2 group_size による影響分析（Steam データセット）

- group_size=50 vs 100 vs 150 vs 200 vs 300 の性能比較: -
- 最適な group_size: -
- コンテキスト長超過エラーの発生パターン: -

### 4.3 モデル性能比較（Steam データセット、group_size=300）

- gpt-4o-mini vs gpt-5.1 の性能差: -
- コンテキスト長調整可能モデルの効果: -
- エラー発生率の違い: -

### 4.4 COCO 実験の考察

- 正解なしデータセットでの対比因子生成の特徴: -
- モデル間の違い: -
- 画像との整合性: -

---

## 5. 結論

### 5.1 主要な発見

1. **データセット別性能（group_size=100 統一）**: -
2. **group_size による影響**: -
3. **コンテキスト長調整可能モデルの効果**: -
4. **最適な group_size**: -
5. **正解なしデータセットでの対比因子生成**: -

### 5.2 技術的改善点

1. **プロンプト長制限機能**: group_size=100 に制限することでコンテキスト長超過エラーを防止
2. **エラーハンドリング**: リトライ機能とコンテキスト長超過エラーの早期検出を実装
3. **メモリ使用量削減**: 並列実行数を 1/5 に削減（最大 8→ 最大 2）

### 5.3 今後の課題

- group_size による性能変化の詳細分析
- コンテキスト長調整可能モデルの活用方法
- より効率的なプロンプト生成手法の検討

---

## 6. 付録

### 6.1 実験設定詳細

- 実験マトリックス: `実験マトリックス.json`
- 実行スクリプト: `src/analysis/experiments/2025/10/10/run_batch_from_matrix.py`
- **主要変更点**:
  - メイン実験: group_size=100 に統一
  - Steam サブ実験: group_size 変化による影響調査（50/100/150/200/300）
  - gpt-5.1 での group_size=300 検証実験を追加

### 6.2 結果ファイル

- 個別実験結果: `src/analysis/experiments/{YYYY}/{MM}/{DD}/results/`
- 集計結果: 本レポート

### 6.3 参考資料

- 実験計画書: `実験計画書.md`
- データセット情報: `docs/datasets/`

---

**レポート作成日**: {{REPORT_DATE}}  
**作成者**: 清野駿
