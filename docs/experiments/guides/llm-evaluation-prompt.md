# LLM評価プロンプト仕様

## 概要

LLM評価スコアは、参照テキスト（正解ラベル）と候補テキスト（LLM出力）の意味的類似度をLLMで評価する指標です。BERTスコアやBLEUスコアと並んで、対比因子生成の品質を評価するために使用されます。

## プロンプト定義場所

**実装ファイル**: `src/analysis/experiments/utils/scores/llm_score.py`

**関数**: `_create_evaluation_prompt(reference_text: str, candidate_text: str) -> str`

## プロンプトテンプレート

```python
参照テキストと候補テキストの意味的類似度を5段階（1-5）で評価してください。

参照テキスト: {reference_text}

候補テキスト: {candidate_text}

評価基準:
- 5: 完全に同じ意味
- 4: ほぼ同じ意味（細かい違いのみ）
- 3: 類似しているが一部異なる
- 2: 部分的に類似している
- 1: ほとんど異なる

出力形式（JSON形式）:
{
    "score": 4,
    "normalized_score": 0.8,
    "reasoning": "評価理由を簡潔に説明"
}

score: 1-5の整数スコア
normalized_score: 0.0-1.0に正規化したスコア（score/5.0）
reasoning: 評価理由の説明（50文字以内）

JSON形式のみで回答してください。
```

## 評価基準の詳細

| スコア | 意味 | 説明 |
|--------|------|------|
| 5 | 完全に同じ意味 | 参照テキストと候補テキストが完全に同じ意味を表している |
| 4 | ほぼ同じ意味 | 細かい違いのみで、本質的な意味は同じ |
| 3 | 類似しているが一部異なる | 全体的に類似しているが、一部異なる点がある |
| 2 | 部分的に類似している | 一部の要素が類似しているが、全体としては異なる |
| 1 | ほとんど異なる | ほとんど異なる意味を表している |

## 出力形式

### JSON構造

```json
{
    "score": 4,
    "normalized_score": 0.8,
    "reasoning": "評価理由を簡潔に説明"
}
```

### フィールド説明

- **score**: 1-5の整数スコア（必須）
- **normalized_score**: 0.0-1.0に正規化したスコア（`score / 5.0`）。省略時は自動計算される
- **reasoning**: 評価理由の説明（50文字以内、推奨）

### 正規化スコア

- スコア1 → 0.2
- スコア2 → 0.4
- スコア3 → 0.6
- スコア4 → 0.8
- スコア5 → 1.0

## 使用例

### 基本的な使用

```python
from src.analysis.experiments.utils.scores.llm_score import calculate_llm_score

reference = "ゲームプレイの詳細な批評と開発者への提案"
candidate = "Detailed game mechanics criticism and developer suggestions."

result = calculate_llm_score(
    reference_text=reference,
    candidate_text=candidate,
    model_name="gpt-4o-mini",
    temperature=0.0
)

if result:
    print(f"スコア: {result['score']}/5")
    print(f"正規化スコア: {result['normalized_score']:.4f}")
    print(f"理由: {result['reasoning']}")
```

### バッチ処理

```python
from src.analysis.experiments.utils.scores.llm_score import calculate_llm_score_batch

pairs = [
    ("参照テキスト1", "候補テキスト1"),
    ("参照テキスト2", "候補テキスト2"),
]

results = calculate_llm_score_batch(
    text_pairs=pairs,
    model_name="gpt-4o-mini",
    temperature=0.0
)
```

### 非同期処理（高速化）

```python
import asyncio
from src.analysis.experiments.utils.scores.llm_score import calculate_llm_score_batch_async

async def main():
    pairs = [
        ("参照テキスト1", "候補テキスト1"),
        ("参照テキスト2", "候補テキスト2"),
    ]
    
    results = await calculate_llm_score_batch_async(
        text_pairs=pairs,
        model_name="gpt-4o-mini",
        temperature=0.0,
        max_concurrent=5  # 同時実行数
    )

asyncio.run(main())
```

## 設定パラメータ

### モデル設定

- **model_name**: 使用するLLMモデル名（デフォルト: `"gpt-4o-mini"`）
- **temperature**: 温度パラメータ（デフォルト: `0.0`）
  - 0.0: 決定論的な出力（推奨）
  - 0.0より大きい値: より多様な出力

### リトライ設定

- **timeout**: タイムアウト秒数（デフォルト: `30`）
- **max_retries**: 最大リトライ回数（デフォルト: `3`）

### 非同期設定

- **max_concurrent**: 同時実行数の上限（デフォルト: `5`）

## エラーハンドリング

### 失敗時の動作

- LLM評価が失敗した場合、`None`を返す
- バッチ処理では、失敗したペアは`None`として返される
- 部分的な失敗でも、成功した評価結果は返される

### よくあるエラー

1. **空のテキスト**: 空のテキストが渡された場合、警告を出して`None`を返す
2. **JSON解析エラー**: LLMの応答がJSON形式でない場合、警告を出して`None`を返す
3. **スコア範囲外**: スコアが1-5の範囲外の場合、警告を出して`None`を返す
4. **タイムアウト**: タイムアウトが発生した場合、リトライ後に失敗した場合は`None`を返す

## 他の評価指標との比較

| 指標 | 特徴 | 適用範囲 |
|------|------|----------|
| **BERTスコア** | 深層ベクトル比較、意味的類似度 | 高次元意味空間での類似度測定 |
| **BLEUスコア** | n-gramベースの表層一致率 | 表現的一致度評価 |
| **LLMスコア** | LLMによる意味的類似度評価 | 人間の判断に近い評価、文脈理解 |

## 実装の詳細

### プロンプト生成

プロンプトは`_create_evaluation_prompt()`関数で生成されます。この関数は以下のパラメータを受け取ります：

- `reference_text`: 参照テキスト（正解ラベル）
- `candidate_text`: 候補テキスト（LLM出力）

### JSON解析

LLMの応答からJSONを抽出する際、以下の処理を行います：

1. コードブロック（```json ... ``` や ``` ... ```）を除去
2. JSONをパース
3. バリデーション（scoreの存在確認、範囲チェック）
4. 型変換（score → int, normalized_score → float）

### 正規化スコアの計算

`normalized_score`が存在しない場合、`score / 5.0`で自動計算されます。

## 関連ファイル

- **実装**: `src/analysis/experiments/utils/scores/llm_score.py`
- **統合**: `src/analysis/experiments/utils/scores/get_score.py`
- **使用**: `src/analysis/experiments/utils/cfGenerator/contrast_factor_analyzer.py`
- **設定**: `src/analysis/experiments/2025/10/10/pipeline_config.yaml`

## 参考

- [評価指標設計思想ルール](.cursor/rules/evaluation_metrics_design.mdc)
- [実験パイプライン設定](../playbooks/)

