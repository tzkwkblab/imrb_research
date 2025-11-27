# Retrieved Concepts 実験 - 論文執筆用参照ガイド

## 1. 実験概要

### 1.1 実験目的

Retrieved Concepts (COCO Captions) データセットを使用した対比因子生成実験。正解ラベルがないデータセットに対する対比因子生成の考察を目的とする。

### 1.2 実験の特徴

- **正解ラベルなし**: 評価スコア（BERT/BLEU）は参考値として扱う
- **画像との整合性確認**: 生成された対比因子と画像を見比べて考察
- **0-shot設定**: Few-shot例を使用しない設定で実行
- **モデル比較**: gpt-4o-mini と gpt-5.1 の両方で実験

### 1.3 実験構成

- **総実験数**: 10 実験
- **コンセプト数**: 5 コンセプト（concept_0, concept_1, concept_2, concept_10, concept_50）
- **モデル**: gpt-4o-mini（5 実験）+ gpt-5.1（5 実験）
- **実行日時**: 2025-11-19

## 2. 実験パラメータ

| パラメータ | 値 |
|-----------|-----|
| Few-shot 設定 | 0-shot（固定） |
| GPT モデル | gpt-4o-mini（5 実験）+ gpt-5.1（5 実験） |
| group_size | 50（固定） |
| temperature | 0.7 |
| max_tokens | 100 |
| LLM 評価 | 無効 |
| アスペクト記述 | 無効 |
| 分割タイプ | aspect_vs_bottom100 |

### 2.1 データセット情報

- **データソース**: MS-COCO 2017 train split
- **類似度計算**: CLIP (ViT-B/32) コサイン類似度
- **コンセプト数**: 300個の潜在コンセプト
- **取得数**: 各コンセプトあたりTop-100とBottom-100の2セット
- **データパス**: `data/external/retrieved-concepts/farnoosh/current`

### 2.2 分割戦略

- **グループA**: 対象コンセプトのTop-100から抽出（コンセプトに最も類似した画像のキャプション）
- **グループB**: 対象コンセプトのBottom-100から抽出（コンセプトに最も類似していない画像のキャプション）

## 3. 実験結果へのパス

### 3.1 統合結果

- **統合結果JSON**: `results/20251119_153853/batch_results.json`
  - 全71実験の実行結果（Retrieved Concepts実験10件を含む）
  - 各実験の入力データ、生成ラベル、評価スコア（BERTScore, BLEU）

### 3.2 個別結果

各実験の詳細結果は以下のパスに保存されています：

| 実験ID | コンセプト | モデル | 結果ファイルパス |
|--------|-----------|--------|-----------------|
| retrieved_concepts_concept_0_0_4o-mini_word | concept_0 | gpt-4o-mini | `results/20251119_153853/individual/retrieved_concepts_concept_0_0_4o-mini_word.json` |
| retrieved_concepts_concept_0_0_51_word | concept_0 | gpt-5.1 | `results/20251119_153853/individual/retrieved_concepts_concept_0_0_51_word.json` |
| retrieved_concepts_concept_1_0_4o-mini_word | concept_1 | gpt-4o-mini | `results/20251119_153853/individual/retrieved_concepts_concept_1_0_4o-mini_word.json` |
| retrieved_concepts_concept_1_0_51_word | concept_1 | gpt-5.1 | `results/20251119_153853/individual/retrieved_concepts_concept_1_0_51_word.json` |
| retrieved_concepts_concept_2_0_4o-mini_word | concept_2 | gpt-4o-mini | `results/20251119_153853/individual/retrieved_concepts_concept_2_0_4o-mini_word.json` |
| retrieved_concepts_concept_2_0_51_word | concept_2 | gpt-5.1 | `results/20251119_153853/individual/retrieved_concepts_concept_2_0_51_word.json` |
| retrieved_concepts_concept_10_0_4o-mini_word | concept_10 | gpt-4o-mini | `results/20251119_153853/individual/retrieved_concepts_concept_10_0_4o-mini_word.json` |
| retrieved_concepts_concept_10_0_51_word | concept_10 | gpt-5.1 | `results/20251119_153853/individual/retrieved_concepts_concept_10_0_51_word.json` |
| retrieved_concepts_concept_50_0_4o-mini_word | concept_50 | gpt-4o-mini | `results/20251119_153853/individual/retrieved_concepts_concept_50_0_4o-mini_word.json` |
| retrieved_concepts_concept_50_0_51_word | concept_50 | gpt-5.1 | `results/20251119_153853/individual/retrieved_concepts_concept_50_0_51_word.json` |

### 3.3 統計情報

- **統計情報JSON**: `論文/結果/実験設定/experiment_statistics.json`
  - データセット別統計（Retrieved Conceptsセクション）
  - 平均 BERTScore: 0.599
  - 平均 BLEU: 0.000
  - BERTScore範囲: 0.541 - 0.667

## 4. 考察レポートへのパス

各実験のLLM考察レポートは以下のパスに保存されています：

| 実験ID | 考察レポートパス |
|--------|----------------|
| retrieved_concepts_concept_0_0_4o-mini_word | `results/20251119_153853/analysis_workspace/reports/retrieved_concepts_concept_0_0_4o-mini_word.md` |
| retrieved_concepts_concept_0_0_51_word | `results/20251119_153853/analysis_workspace/reports/retrieved_concepts_concept_0_0_51_word.md` |
| retrieved_concepts_concept_1_0_4o-mini_word | `results/20251119_153853/analysis_workspace/reports/retrieved_concepts_concept_1_0_4o-mini_word.md` |
| retrieved_concepts_concept_1_0_51_word | `results/20251119_153853/analysis_workspace/reports/retrieved_concepts_concept_1_0_51_word.md` |
| retrieved_concepts_concept_2_0_4o-mini_word | `results/20251119_153853/analysis_workspace/reports/retrieved_concepts_concept_2_0_4o-mini_word.md` |
| retrieved_concepts_concept_2_0_51_word | `results/20251119_153853/analysis_workspace/reports/retrieved_concepts_concept_2_0_51_word.md` |
| retrieved_concepts_concept_10_0_4o-mini_word | `results/20251119_153853/analysis_workspace/reports/retrieved_concepts_concept_10_0_4o-mini_word.md` |
| retrieved_concepts_concept_10_0_51_word | `results/20251119_153853/analysis_workspace/reports/retrieved_concepts_concept_10_0_51_word.md` |
| retrieved_concepts_concept_50_0_4o-mini_word | `results/20251119_153853/analysis_workspace/reports/retrieved_concepts_concept_50_0_4o-mini_word.md` |
| retrieved_concepts_concept_50_0_51_word | `results/20251119_153853/analysis_workspace/reports/retrieved_concepts_concept_50_0_51_word.md` |

### 4.1 考察レポートの内容

各レポートには以下の内容が含まれています：

1. **個別実験の詳細考察**
   - 単語レベルでの特徴分析
   - 文脈・意味的ニュアンスの考察
   - 正解ラベルとの比較
   - 実験設定の影響
   - 改善の示唆

2. **Retrieved Conceptsカテゴリ全体の考察**
   - カテゴリ全体の傾向（共通パターンとデータ差異）
   - パフォーマンスの特徴（スコア傾向と要因）
   - 設定パラメータの影響
   - 洞察と示唆

## 5. 画像パス

各実験の画像URLは、個別結果JSONファイルの `input.group_a_top5_image_urls` と `input.group_b_top5_image_urls` に含まれています。

### 5.1 concept_0

#### gpt-4o-mini

**グループA（Top-100）画像URL**:
- http://images.cocodataset.org/train2017/000000105396.jpg
- http://images.cocodataset.org/train2017/000000007489.jpg
- http://images.cocodataset.org/train2017/000000394197.jpg
- http://images.cocodataset.org/train2017/000000395678.jpg
- http://images.cocodataset.org/train2017/000000091113.jpg

**グループB（Bottom-100）画像URL**:
- http://images.cocodataset.org/train2017/000000081860.jpg
- http://images.cocodataset.org/train2017/000000139263.jpg
- http://images.cocodataset.org/train2017/000000227607.jpg
- http://images.cocodataset.org/train2017/000000267548.jpg
- http://images.cocodataset.org/train2017/000000535143.jpg

#### gpt-5.1

**グループA（Top-100）画像URL**:
- http://images.cocodataset.org/train2017/000000105396.jpg
- http://images.cocodataset.org/train2017/000000007489.jpg
- http://images.cocodataset.org/train2017/000000394197.jpg
- http://images.cocodataset.org/train2017/000000395678.jpg
- http://images.cocodataset.org/train2017/000000091113.jpg

**グループB（Bottom-100）画像URL**:
- http://images.cocodataset.org/train2017/000000081860.jpg
- http://images.cocodataset.org/train2017/000000139263.jpg
- http://images.cocodataset.org/train2017/000000227607.jpg
- http://images.cocodataset.org/train2017/000000267548.jpg
- http://images.cocodataset.org/train2017/000000535143.jpg

### 5.2 concept_1

#### gpt-4o-mini

**グループA（Top-100）画像URL**:
- http://images.cocodataset.org/train2017/000000433452.jpg
- http://images.cocodataset.org/train2017/000000411385.jpg
- http://images.cocodataset.org/train2017/000000150669.jpg
- http://images.cocodataset.org/train2017/000000456323.jpg
- http://images.cocodataset.org/train2017/000000408625.jpg

**グループB（Bottom-100）画像URL**:
- http://images.cocodataset.org/train2017/000000095812.jpg
- http://images.cocodataset.org/train2017/000000053263.jpg
- http://images.cocodataset.org/train2017/000000426903.jpg
- http://images.cocodataset.org/train2017/000000240057.jpg
- http://images.cocodataset.org/train2017/000000360217.jpg

#### gpt-5.1

（個別結果JSONファイルから取得可能）

### 5.3 concept_2

#### gpt-4o-mini

**グループA（Top-100）画像URL**:
- http://images.cocodataset.org/train2017/000000105396.jpg
- http://images.cocodataset.org/train2017/000000572063.jpg
- http://images.cocodataset.org/train2017/000000453442.jpg
- http://images.cocodataset.org/train2017/000000351567.jpg
- http://images.cocodataset.org/train2017/000000138922.jpg

**グループB（Bottom-100）画像URL**:
- http://images.cocodataset.org/train2017/000000433472.jpg
- http://images.cocodataset.org/train2017/000000501358.jpg
- http://images.cocodataset.org/train2017/000000352088.jpg
- http://images.cocodataset.org/train2017/000000075270.jpg
- http://images.cocodataset.org/train2017/000000398175.jpg

#### gpt-5.1

（個別結果JSONファイルから取得可能）

### 5.4 concept_10

#### gpt-4o-mini

**グループA（Top-100）画像URL**:
- http://images.cocodataset.org/train2017/000000269090.jpg
- http://images.cocodataset.org/train2017/000000559525.jpg
- http://images.cocodataset.org/train2017/000000024086.jpg
- http://images.cocodataset.org/train2017/000000543408.jpg
- http://images.cocodataset.org/train2017/000000441108.jpg

**グループB（Bottom-100）画像URL**:
- http://images.cocodataset.org/train2017/000000389681.jpg
- http://images.cocodataset.org/train2017/000000074434.jpg
- http://images.cocodataset.org/train2017/000000005482.jpg
- http://images.cocodataset.org/train2017/000000022271.jpg
- http://images.cocodataset.org/train2017/000000028044.jpg

#### gpt-5.1

（個別結果JSONファイルから取得可能）

### 5.5 concept_50

#### gpt-4o-mini

**グループA（Top-100）画像URL**:
- http://images.cocodataset.org/train2017/000000397613.jpg
- http://images.cocodataset.org/train2017/000000030210.jpg
- http://images.cocodataset.org/train2017/000000303672.jpg
- http://images.cocodataset.org/train2017/000000303570.jpg
- http://images.cocodataset.org/train2017/000000540275.jpg

**グループB（Bottom-100）画像URL**:
- http://images.cocodataset.org/train2017/000000487741.jpg
- http://images.cocodataset.org/train2017/000000042862.jpg
- http://images.cocodataset.org/train2017/000000384007.jpg
- http://images.cocodataset.org/train2017/000000220118.jpg
- http://images.cocodataset.org/train2017/000000466229.jpg

#### gpt-5.1

（個別結果JSONファイルから取得可能）

### 5.6 画像パスの取得方法

各実験の画像URLは、個別結果JSONファイルの以下のパスから取得できます：

```json
{
  "input": {
    "group_a_top5_image_urls": [...],
    "group_b_top5_image_urls": [...]
  }
}
```

## 6. 実験結果サマリー

### 6.1 各実験の結果

| コンセプト | モデル | BERTスコア | BLEUスコア | LLM応答 |
|-----------|--------|-----------|-----------|---------|
| concept_0 | gpt-4o-mini | 0.609 | 0.000 | "Group A includes casual everyday scenes and objects." |
| concept_0 | gpt-5.1 | 0.615 | 0.000 | （個別結果JSONファイルを参照） |
| concept_1 | gpt-4o-mini | 0.547 | 0.000 | （個別結果JSONファイルを参照） |
| concept_1 | gpt-5.1 | 0.554 | 0.000 | （個別結果JSONファイルを参照） |
| concept_2 | gpt-4o-mini | 0.668 | 0.000 | （個別結果JSONファイルを参照） |
| concept_2 | gpt-5.1 | 0.541 | 0.000 | "Outdoor animals, landscapes, benches, skateboards, and black‑white photos" |
| concept_10 | gpt-4o-mini | 0.603 | 0.000 | "Group A focuses on people, families, and outdoor activities." |
| concept_10 | gpt-5.1 | 0.607 | 0.000 | "Children, toys, stuffed animals, birthdays, family, play, sports" |
| concept_50 | gpt-4o-mini | 0.620 | 0.000 | "Group A focuses on various electronic devices, especially cell phones." |
| concept_50 | gpt-5.1 | 0.632 | 0.000 | "Group A focuses on phones, electronics, and broken devices." |

**注**: 詳細な結果は個別結果JSONファイルを参照してください。

### 6.2 統計情報

- **平均 BERTScore**: 0.599
- **平均 BLEU**: 0.000
- **BERTScore範囲**: 0.541 - 0.667
- **最高 BERTScore**: 0.667 (concept_2, gpt-4o-mini)
- **最低 BERTScore**: 0.541 (concept_2, gpt-5.1)

### 6.3 モデル比較

| モデル | 平均 BERTScore | 実験数 |
|--------|---------------|--------|
| gpt-4o-mini | 0.609 | 5 |
| gpt-5.1 | 0.590 | 5 |

**注**: 両モデルともほぼ同等の性能を示している。

## 7. 論文執筆時の参照方法

### 7.1 実験パラメータの引用

論文執筆時に実験パラメータを引用する場合：

- **Few-shot設定**: 0-shot（例示なし）
- **group_size**: 50
- **モデル**: gpt-4o-mini と gpt-5.1
- **評価指標**: BERTScore（参考値）、BLEU（参考値）

### 7.2 実験結果の引用

- **統合結果**: `results/20251119_153853/batch_results.json` から数値を参照
- **統計情報**: `論文/結果/実験設定/experiment_statistics.json` の `retrieved_concepts` セクションを参照
- **個別結果**: 各実験の個別結果JSONファイルから詳細を参照

### 7.3 考察の引用

- **個別考察**: 各実験の考察レポート（`results/20251119_153853/analysis_workspace/reports/`）から引用
- **主要な発見**:
  - グループ間の意味的対比は「物体／静的シーン寄り」対「人物・行為・イベント寄り」という軸で現れることが多い
  - 0-shot設定では出力形式が不明瞭になりやすい
  - 評価指標としてBLEUは短い命名タスクに不適切
  - 両モデル（gpt-4o-mini と gpt-5.1）ともほぼ同等の性能を示している

### 7.4 画像の参照

- **画像URL**: 各実験の個別結果JSONファイルの `input.group_a_top5_image_urls` と `input.group_b_top5_image_urls` から取得
- **画像の用途**: 生成された対比因子と画像を見比べて、対比因子の妥当性を確認
- **画像の説明**: グループAはコンセプトに最も類似した画像、グループBはコンセプトに最も類似していない画像

## 8. 注意事項

### 8.1 評価スコアの位置づけ

- **BERTScore/BLEUは参考値**: 正解ラベルがないため、スコアは参考値として扱う
- **画像との整合性確認**: 生成された対比因子と画像を見比べて考察することが重要
- **0-shot設定の影響**: 0-shot設定では出力形式が不明瞭になりやすい

### 8.2 データセットの特徴

- **COCOデータセット**: 多様な日常シーンを含むため、群間差分が微妙かつ多面的
- **簡潔なラベル化の困難**: 多様性の高さにより、簡潔なラベルに落とすのは困難
- **サブクラスタ化の必要性**: A内に複数サブトピックが混在する場合は、サブクラスタ化が必要

## 9. 関連ファイル

- **実験パラメータ整理**: `論文/結果/実験設定/実験パラメータとデータソース整理.md`
- **データセット詳細**: `docs/datasets/retrieved-concepts/README.md`
- **実験手順ガイド**: `docs/experiments/playbooks/retrieved-concepts-experiment-guide.md`

