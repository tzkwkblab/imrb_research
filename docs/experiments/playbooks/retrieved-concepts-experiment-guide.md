# Retrieved Conceptsデータセット実験手順

Retrieved Concepts Dataset (COCO Captions)を使用した対比因子生成実験の手順です。

## データセット概要

- **データセットID**: `retrieved_concepts`
- **レコード数**: 約300,000件（300コンセプト × 1000件/コンセプト）
- **コンセプト数**: 300個（concept_0 ～ concept_299）
- **推奨分割タイプ**: `aspect_vs_bottom100`

## データ構造

各コンセプトには以下の2セットが含まれます：

- **Top-100**: 最も類似度が高い100枚の画像とそのキャプション（5キャプション/画像 = 500件）
- **Bottom-100**: 最も類似度が低い100枚の画像とそのキャプション（5キャプション/画像 = 500件）

## 推奨設定

### グループサイズ

- **テスト/動作確認**: 5-10
- **通常実験**: 10-20
- **本格実験**: 50-100

**注意**: 各コンセプトのTop-100/Bottom-100はそれぞれ500件のキャプションがあるため、グループサイズは500以下に設定してください。

### 分割タイプ

**`aspect_vs_bottom100`** を強く推奨します（デフォルト）。

- グループA: 対象コンセプトのTop-100から抽出
- グループB: 対象コンセプトのBottom-100から抽出

この分割により、コンセプトに特徴的な要素をより明確に抽出できます。

### アスペクト説明文

retrieved_conceptsデータセットには公式のアスペクト説明文はありません。説明文なしで実行してください。

## 実行例

### 対話型スクリプト

```bash
bash scripts/run_interactive_experiment.sh
```

1. データセット: `4` (Retrieved Concepts)
2. 正解アスペクトの表現: `1` (説明文なし)
3. アスペクト: `0` または `0-9` または `0,1,2` (concept_0 など)
4. グループサイズ: `10`
5. 分割タイプ: `3` (aspect_vs_bottom100) - デフォルトで選択される
6. 例題: `n` (使用しない)

### コマンドライン実行

```bash
cd /Users/seinoshun/imrb_research/src/analysis/experiments/2025/10/10
source ../../../../.venv/bin/activate

# 単一コンセプト
python run_experiment.py \
  --dataset retrieved_concepts \
  --aspect concept_0 \
  --group-size 10 \
  --split-type aspect_vs_bottom100

# 複数コンセプト
python run_experiment.py \
  --dataset retrieved_concepts \
  --aspects concept_0 concept_1 concept_2 \
  --group-size 10 \
  --split-type aspect_vs_bottom100

# サイレントモード（ファイル保存なし）
python run_experiment.py \
  --dataset retrieved_concepts \
  --aspect concept_0 \
  --group-size 5 \
  --split-type aspect_vs_bottom100 \
  --silent
```

### 設定ファイル

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

## コンセプト選択のコツ

### 単一コンセプト

```bash
--aspect concept_0
```

### 複数コンセプト（個別指定）

```bash
--aspects concept_0 concept_1 concept_2
```

### 範囲指定（対話型スクリプト）

- `0-9`: concept_0 ～ concept_9
- `0-4,10,20-25`: concept_0-4, concept_10, concept_20-25

## 注意点

1. **データ読み込み時間**: 大容量データセット（361,506行）のため、初回読み込みに時間がかかります
2. **メモリ使用量**: ストリーミングパーサーを使用していますが、大量のコンセプトを一度に処理する場合は注意してください
3. **グループサイズ**: Top-100/Bottom-100はそれぞれ500件のキャプションがあるため、グループサイズは500以下に設定してください
4. **評価スコア**: retrieved_conceptsには正解ラベルがないため、BERT/BLEUスコアは参考値として扱ってください

## 期待される出力例

```
=== 結果 ===
BERTスコア: 0.6133
BLEUスコア: 0.0000
LLM応答: Everyday objects and solitary scenes.
品質評価: poor
```

## 実験の解釈

`aspect_vs_bottom100`分割タイプでは：

- **グループA（Top-100）**: コンセプトに最も類似した画像のキャプション
- **グループB（Bottom-100）**: コンセプトに最も類似していない画像のキャプション

LLMは、Top-100に特徴的でBottom-100には見られない要素を抽出します。これにより、コンセプトの本質的な特徴を浮き彫りにできます。

## 関連ドキュメント

- [Retrieved Conceptsデータセット詳細](../../datasets/retrieved-concepts/README.md)
- [実験スクリプト使い方ガイド](../guides/experiment-script-guide.md)
- [トラブルシューティング](../troubleshooting/common-issues.md)

