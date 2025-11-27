# LLM 考察取得ガイド

追加実験の結果を LLM（gpt-5.1）に問い合わせて考察を取得するための実装手順です。

## 概要

実験結果の JSON ファイルと統計情報を読み込み、研究コンテキストと合わせて LLM に問い合わせ、1000 文字程度の考察を自動生成します。

## 前提条件

- Python 仮想環境がアクティブであること
- `OPENAI_API_KEY`環境変数が設定されていること
- プロジェクトの LLM ユーティリティが利用可能であること

## ファイル構造

```
追加実験/
└── {実験カテゴリ}/
    └── {データセット}/
        ├── research_context.md          # 研究コンテキスト（必須）
        ├── {experiment}_statistics.json # 統計情報（必須）
        ├── 結果/
        │   └── batch_results.json       # バッチ結果（必須）
        └── 実行ファイル/
            └── generate_{experiment}_analysis.py  # 分析スクリプト
```

## 実装手順

### ステップ 1: 研究コンテキストファイルの準備

既存の`research_context.md`をコピーするか、新規作成します。

```bash
# 既存のものをコピーする場合
cp results/20251119_153853/analysis_workspace/research_context.md \
   論文/結果/追加実験/{実験カテゴリ}/{データセット}/research_context.md

# または、論文texファイルから抽出する場合
python src/analysis/experiments/2025/10/10/extract_research_context.py \
  --tex-file 論文/masterThesisJa.tex \
  --output 論文/結果/追加実験/{実験カテゴリ}/{データセット}/research_context.md
```

### ステップ 2: 統計情報 JSON の準備

実験結果から統計情報を抽出した JSON ファイルを準備します。

**必須フィールド**:

- `statistics.few_shot_stats`: Few-shot 別統計（該当する場合）
- `statistics.aspect_stats`: アスペクト別統計（該当する場合）
- `statistics.total_experiments`: 総実験数
- `statistics.successful`: 成功数
- `statistics.failed`: 失敗数

**例**:

```json
{
  "statistics": {
    "total_experiments": 12,
    "successful": 12,
    "failed": 0,
    "few_shot_stats": {
      "0": {
        "avg_bert_score": 0.5676,
        "min_bert_score": 0.52,
        "max_bert_score": 0.626
      }
    },
    "aspect_stats": {
      "gameplay": {
        "avg_bert_score": 0.6672,
        "max_bert_score": 0.7925
      }
    }
  }
}
```

### ステップ 3: バッチ結果 JSON の準備

実験実行時に生成される`batch_results.json`を準備します。

**必須フィールド**:

- `results[]`: 実験結果の配列
  - `experiment_info`: 実験情報（aspect, few_shot 等）
  - `evaluation`: 評価結果（bert_score, bleu_score 等）
  - `process.llm_response`: LLM 出力（オプション）

### ステップ 4: 分析スクリプトの作成

`generate_fewshot_analysis.py`をテンプレートとして、実験に合わせてカスタマイズします。

**基本構造**:

```python
#!/usr/bin/env python3
"""
{実験名}結果のLLM分析スクリプト
"""

import json
import argparse
import logging
import sys
import time
from pathlib import Path
from datetime import datetime

# パス設定
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src" / "analysis" / "experiments" / "utils"))

from LLM.llm_factory import LLMFactory

# 1. 研究コンテキスト読み込み関数
def load_research_context(context_path: Path) -> str:
    """研究コンテキストを読み込み"""
    if not context_path.exists():
        logger.warning(f"研究背景ファイルが見つかりません: {context_path}")
        return ""
    with open(context_path, 'r', encoding='utf-8') as f:
        return f.read()

# 2. 統計情報読み込み関数
def load_statistics(statistics_path: Path) -> Dict[str, Any]:
    """統計情報を読み込み"""
    # 実装...

# 3. バッチ結果読み込み関数
def load_batch_results(batch_results_path: Path) -> List[Dict[str, Any]]:
    """バッチ結果を読み込み"""
    # 実装...

# 4. プロンプト生成関数
def generate_analysis_prompt(
    research_context: str,
    statistics: Dict[str, Any],
    results: List[Dict[str, Any]]
) -> str:
    """分析プロンプトを生成"""
    # 実験に合わせてカスタマイズ
    prompt = f"""...
    {research_context}
    ...
    """
    return prompt

# 5. LLM問い合わせ関数
def analyze_with_llm(prompt: str, model_name: str = "gpt-5.1") -> Optional[str]:
    """LLMに問い合わせて考察を取得"""
    client = LLMFactory.create_client(model_name=model_name, debug=False)
    # リトライ処理を含む実装...
    return response

# 6. レポート生成関数
def generate_analysis_report(...):
    """分析レポートを生成"""
    # 実装...

# 7. メイン関数
def main():
    """メイン実行"""
    # argparse設定と実行フロー
```

### ステップ 5: プロンプトのカスタマイズ

実験の特性に合わせてプロンプトを調整します。

**カスタマイズポイント**:

1. **実験設定の説明**: データセット、アスペクト、パラメータ等
2. **統計情報のフォーマット**: 実験に応じた統計の表示方法
3. **考察指示**: 実験の目的に合わせた観点の設定
4. **BLEU スコアの確認**: 全実験で BLEU スコアが 0.0000 の場合、考察の最初にその旨を一文追加する

**プロンプトテンプレート**:

```python
prompt = f"""あなたは説明可能AIの研究における実験結果の分析専門家です。

# 研究背景
{research_context}

# 実験結果
{statistics_text}
{results_text}

# 考察指示
この実験結果から言えることを1000文字程度で考察してください。

1. **{観点1}**
2. **{観点2}**
3. **{観点3}**
4. **{観点4}**

考察は日本語で、具体的かつ詳細に記述してください。
"""
```

**注意**: 全実験で BLEU スコアが 0.0000 の場合、LLM 考察生成後に手動で最初のセクションに「全実験で BLEU スコアは 0.0000 であり、表層的な語彙一致はほとんど見られない。」という一文を追加してください。

## 実行方法

### 基本的な実行

```bash
# 仮想環境をアクティベート
source .venv/bin/activate

# スクリプト実行
python 論文/結果/追加実験/{実験カテゴリ}/{データセット}/実行ファイル/generate_{experiment}_analysis.py
```

### オプション指定

```bash
python generate_{experiment}_analysis.py \
  --statistics fewshot_statistics.json \
  --batch-results 結果/batch_results.json \
  --research-context research_context.md \
  --output fewshot_analysis.md \
  --model gpt-5.1 \
  --debug
```

### オプション説明

- `--statistics, -s`: 統計情報 JSON ファイルのパス
- `--batch-results, -b`: バッチ結果 JSON ファイルのパス
- `--research-context, -r`: 研究コンテキスト MD ファイルのパス
- `--output, -o`: 出力 MD ファイルのパス
- `--model, -m`: 使用する LLM モデル（デフォルト: gpt-5.1）
- `--debug`: デバッグモード

## 実装例: Few-shot 実験

実際の実装例として、`論文/結果/追加実験/fewshot/steam/実行ファイル/generate_fewshot_analysis.py`を参照してください。

**主な特徴**:

- Few-shot 別統計の表示
- アスペクト別統計の表示
- 詳細結果のグループ化表示
- 4 つの観点での考察指示

## トラブルシューティング

### エラー: 研究背景ファイルが見つかりません

**原因**: `research_context.md`が存在しない

**解決策**:

```bash
# 既存のものをコピー
cp results/20251119_153853/analysis_workspace/research_context.md \
   論文/結果/追加実験/{実験カテゴリ}/{データセット}/research_context.md
```

### エラー: ImportError: attempted relative import

**原因**: パスの設定が間違っている

**解決策**: スクリプトのパス設定を確認

```python
sys.path.insert(0, str(project_root / "src" / "analysis" / "experiments" / "utils"))
from LLM.llm_factory import LLMFactory
```

### エラー: LLM 応答が取得できない

**原因**: API キー未設定、ネットワークエラー、モデル名の誤り

**解決策**:

1. 環境変数の確認: `echo $OPENAI_API_KEY`
2. モデル名の確認: `gpt-5.1`が正しいか
3. リトライ処理が動作しているか確認（最大 3 回）

### エラー: 統計情報のフィールドが見つからない

**原因**: JSON ファイルの構造が想定と異なる

**解決策**: 統計情報 JSON の構造を確認し、`format_statistics_for_prompt()`関数を調整

## カスタマイズ方法

### 異なる実験タイプへの対応

1. **モデル比較実験**: モデル別統計を追加
2. **group_size 変化実験**: group_size 別統計を追加
3. **データセット比較実験**: データセット別統計を追加

### プロンプトの調整

実験の目的に合わせて、考察指示を変更します：

```python
# 例: モデル比較実験の場合
考察指示 = """
1. **モデル間の性能差の要因**
2. **モデル特性による出力の違い**
3. **コストパフォーマンスの観点**
4. **実用性への示唆**
"""
```

### 出力フォーマットの変更

`generate_analysis_report()`関数を修正して、レポートの構造を変更できます。

## ベストプラクティス

1. **プロンプトの明確化**: 実験の目的と期待する考察を明確に指示
2. **統計情報の整理**: 重要な指標を優先的に表示
3. **エラーハンドリング**: リトライ処理とログ出力を実装
4. **再利用性**: テンプレート化して他の実験でも使い回せるように
5. **ドキュメント化**: 実験ごとにカスタマイズ内容を記録
6. **BLEU スコアの確認**: 全実験で BLEU スコアが 0.0000 の場合、生成された LLM 考察の最初のセクション（通常は「モデル間の性能差の意味」や「実験設定での結果の解釈」など）の冒頭に「全実験で BLEU スコアは 0.0000 であり、表層的な語彙一致はほとんど見られない。」という一文を追加する。これは、BLEU スコアが表層的な語彙一致を評価する指標であり、対比因子抽出タスクでは意味的類似度（BERT スコア）が主要指標であることを明確にするためである。

## 関連ファイル

- **テンプレート**: `論文/結果/追加実験/fewshot/steam/実行ファイル/generate_fewshot_analysis.py`
- **研究コンテキスト抽出**: `src/analysis/experiments/2025/10/10/extract_research_context.py`
- **LLM ユーティリティ**: `src/analysis/experiments/utils/LLM/llm_factory.py`
- **既存の分析スクリプト**: `src/analysis/experiments/2025/10/10/analyze_experiment_results.py`

## 参考: Few-shot 実験の実装例

完全な実装例は以下を参照：

- `論文/結果/追加実験/fewshot/steam/実行ファイル/generate_fewshot_analysis.py`
- `論文/結果/追加実験/fewshot/steam/fewshot_analysis.md`（出力例）

## 参考: COCO Retrieved Concepts 実験（画像付き考察）の実装例

画像を含む LLM 考察を生成する実装例は以下を参照：

- `論文/結果/追加実験/論文執筆用/coco_retrieved_concepts/実行ファイル/generate_coco_analysis_with_images.py`
- `論文/結果/追加実験/論文執筆用/coco_retrieved_concepts/分析レポート/coco_analysis_with_images.md`（出力例）

### 画像付き考察の特徴

- GPT-5.1 を使用して画像を含む考察を生成
- 上位 5 枚とボトム 5 枚の画像を GPT-5.1 に入力
- 生成された対比因子と画像の視覚的特徴の整合性を詳細に分析
- `max_completion_tokens=100000`でコンテキストを確保

### プロンプトプレビュー機能

`--preview-prompt`オプションを使用すると、実際に LLM に送信する前にプロンプトを確認できます：

```bash
python generate_coco_analysis_with_images.py \
  --batch-results results/20251127_140836/batch_results.json \
  --research-context research_context.md \
  --output coco_analysis_with_images.md \
  --model gpt-5.1 \
  --preview-prompt
```

### 画像入力機能

GPTClient に`query_with_images()`メソッドを追加し、画像 URL とローカル画像ファイルの両方に対応しています。

- 画像 URL: `http://`または`https://`で始まる URL をそのまま使用可能
- ローカル画像: base64 エンコードして送信
- GPT-5.1 の場合、`max_completion_tokens=100000`を自動設定
