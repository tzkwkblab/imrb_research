# アスペクト説明文機能

## 概要

スコア算出時にアスペクト名ではなく、アスペクトの説明文テキストを使用して比較する機能です。

## 背景

**従来の処理**: `calculate_scores(correct_answer, llm_response)` で `correct_answer` はアスペクト名（例: "gameplay"）

**新しい処理**: `correct_answer` をアスペクト説明文（例: "Controls, mechanics, interactivity, difficulty and other gameplay setups."）に置き換えて比較

## 実装ファイル

### 1. AspectDescriptionManager

**ファイル**: `src/analysis/experiments/utils/aspect_description_manager.py`

**機能**: descriptions.csv からアスペクト名と説明文のマッピングを読み込み、変換を提供

```python
from aspect_description_manager import AspectDescriptionManager

# 初期化
manager = AspectDescriptionManager("data/external/steam-review-aspect-dataset")

# 説明文取得
description = manager.get_description("gameplay")
# → "Controls, mechanics, interactivity, difficulty and other gameplay setups."

# 利用可能かチェック
if manager.has_descriptions():
    # 説明文機能を使用
```

### 2. スコア計算拡張

**ファイル**: `src/analysis/experiments/utils/get_score.py`

**新機能**: `calculate_scores_with_descriptions()`

```python
from get_score import calculate_scores_with_descriptions

# 説明文オプション付きスコア計算
bert_score, bleu_score = calculate_scores_with_descriptions(
    text_a="gameplay",  # アスペクト名
    text_b="LLM応答テキスト",
    aspect_manager=manager,
    use_descriptions=True
)
```

### 3. ContrastFactorAnalyzer 統合

**ファイル**: `src/analysis/experiments/utils/contrast_factor_analyzer.py`

**新パラメータ**: `use_aspect_descriptions`, `dataset_path`

```python
from contrast_factor_analyzer import ContrastFactorAnalyzer

# 説明文オプション有効で初期化
analyzer = ContrastFactorAnalyzer(
    debug=True,
    use_aspect_descriptions=True
)

# 実験実行
result = analyzer.analyze(
    group_a=group_a,
    group_b=group_b,
    correct_answer="gameplay",
    output_dir="results",
    dataset_path="data/external/steam-review-aspect-dataset"
)
```

## 設定

**ファイル**: `src/analysis/experiments/utils/dataset_configs.yaml`

```yaml
experiment_defaults:
  use_aspect_descriptions: false # デフォルトはオフ
  group_size: 300
  shot_settings: [0, 1, 3]
```

## 使用例

### 基本的な使用

```python
# オプション有効で実験実行
analyzer = ContrastFactorAnalyzer(use_aspect_descriptions=True)
result = analyzer.analyze(
    group_a=["Great gameplay mechanics"],
    group_b=["Beautiful graphics"],
    correct_answer="gameplay",
    output_dir="results",
    dataset_path="data/external/steam-review-aspect-dataset"
)
```

### 比較実験

```python
# 通常モード（アスペクト名使用）
analyzer_normal = ContrastFactorAnalyzer(use_aspect_descriptions=False)
result_normal = analyzer_normal.analyze(...)

# 説明文モード
analyzer_desc = ContrastFactorAnalyzer(use_aspect_descriptions=True)
result_desc = analyzer_desc.analyze(..., dataset_path="...")

# 結果比較
print(f"通常: BERT={result_normal['evaluation']['bert_score']:.4f}")
print(f"説明文: BERT={result_desc['evaluation']['bert_score']:.4f}")
```

## データ形式

### descriptions.csv

```csv
aspect,description
gameplay,Controls, mechanics, interactivity, difficulty and other gameplay setups.
story,Story, character, lore, world-building and other storytelling elements.
visual,Aesthetic, art style, animation, visual effects and other visual elements.
```

## 効果

テスト結果から、説明文使用により BERT スコアが向上することを確認：

- **アスペクト名使用**: BERT=0.7255, BLEU=0.0000
- **説明文使用**: BERT=0.8108, BLEU=0.0170

## 注意点

1. **CSV 形式**: 説明文にカンマが含まれる場合、手動読み込み機能で対応
2. **フォールバック**: 説明文が見つからない場合は元のアスペクト名を使用
3. **パス指定**: `dataset_path`は descriptions.csv が存在するディレクトリを指定

## 関連ファイル

- テスト: `src/analysis/experiments/utils/test_aspect_descriptions.py`
- 使用例: `src/analysis/experiments/utils/example_aspect_descriptions_usage.py`
