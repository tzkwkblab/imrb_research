# COCO Retrieved Concepts 実験 - 画像付きLLM考察生成

## 概要

COCO実験結果に対して、GPT-5.1を使用して画像を含めた考察を自動生成する。

## 機能

- 上位5枚とボトム5枚の画像をGPT-5.1に入力
- 生成された対比因子と画像の整合性を詳細に考察
- トークン数を多めに設定（max_completion_tokens=8000）してコンテキストを確保

## ファイル構成

```
coco_retrieved_concepts/
├── 実行ファイル/
│   └── generate_coco_analysis_with_images.py  # 画像付き分析スクリプト
├── 分析レポート/
│   └── coco_analysis_with_images.md  # 出力先（自動生成）
└── research_context.md  # 研究コンテキスト
```

## 実行方法

### 基本的な実行

```bash
# 仮想環境をアクティベート
source .venv/bin/activate

# スクリプト実行
python 論文/結果/追加実験/論文執筆用/coco_retrieved_concepts/実行ファイル/generate_coco_analysis_with_images.py \
  --batch-results results/20251127_140836/batch_results.json \
  --research-context 論文/結果/追加実験/論文執筆用/coco_retrieved_concepts/research_context.md \
  --output 論文/結果/追加実験/論文執筆用/coco_retrieved_concepts/分析レポート/coco_analysis_with_images.md \
  --model gpt-5.1 \
  --max-images 5
```

### 特定のコンセプトのみ分析

```bash
python 論文/結果/追加実験/論文執筆用/coco_retrieved_concepts/実行ファイル/generate_coco_analysis_with_images.py \
  --batch-results results/20251127_140836/batch_results.json \
  --research-context 論文/結果/追加実験/論文執筆用/coco_retrieved_concepts/research_context.md \
  --output 論文/結果/追加実験/論文執筆用/coco_retrieved_concepts/分析レポート/coco_analysis_concept_0.md \
  --model gpt-5.1 \
  --aspect concept_0 \
  --max-images 5
```

### デバッグモード

```bash
python 論文/結果/追加実験/論文執筆用/coco_retrieved_concepts/実行ファイル/generate_coco_analysis_with_images.py \
  --batch-results results/20251127_140836/batch_results.json \
  --research-context 論文/結果/追加実験/論文執筆用/coco_retrieved_concepts/research_context.md \
  --output 論文/結果/追加実験/論文執筆用/coco_retrieved_concepts/分析レポート/coco_analysis_with_images.md \
  --model gpt-5.1 \
  --debug
```

## パラメータ説明

- `--batch-results` / `-b`: バッチ結果JSONファイルのパス（必須）
- `--research-context` / `-r`: 研究コンテキストMDファイルのパス（必須）
- `--output` / `-o`: 出力MDファイルのパス（必須）
- `--model` / `-m`: 使用するLLMモデル（デフォルト: gpt-5.1）
- `--aspect` / `-a`: 特定のアスペクトのみ分析（オプション）
- `--max-images`: 各グループから使用する最大画像数（デフォルト: 5）
- `--debug`: デバッグモードを有効化

## 実装の特徴

### 画像入力機能

- GPTClientに`query_with_images()`メソッドを追加
- 画像URLとローカル画像ファイルの両方に対応
- GPT-5.1の推論モデル判定とトークン数設定を自動化

### トークン数設定

- GPT-5.1の場合、`max_completion_tokens=8000`をデフォルトで設定
- コンテキストが足りるように多めに設定

### エラーハンドリング

- 画像入力が未対応のモデルの場合はエラーメッセージを表示
- リトライ機能（最大3回）を実装
- 画像URLが見つからない場合はテキストのみで分析

## 注意事項

1. **GPT-5.1の画像入力対応**
   - GPT-5.1が推論モデル（o1/o3系）の場合、画像入力が未対応の可能性があります
   - 未対応の場合は、GPT-4oまたはGPT-4o-miniを使用してください

2. **APIコスト**
   - 画像を含むリクエストは通常のテキストリクエストより高コストです
   - GPT-5.1は特に高コストの可能性があります

3. **画像数制限**
   - 一度に送信できる画像数に制限がある可能性があります
   - `--max-images`オプションで調整可能です

4. **実行時間**
   - 画像を含むリクエストは処理に時間がかかります
   - 複数のコンセプトを分析する場合は時間に余裕を持って実行してください

## 出力形式

生成されるレポートには以下が含まれます：

1. **実験結果サマリー**
   - コンセプト名
   - 生成された対比因子
   - BERTスコア

2. **画像との整合性考察**
   - GPT-5.1による詳細な考察（1500文字程度）
   - 画像の視覚的特徴の具体的な言及

3. **参照画像**
   - グループA（Top-100から抽出）の画像URL
   - グループB（Bottom-100から抽出）の画像URL

## 関連ファイル

- GPTClient実装: `src/analysis/experiments/utils/LLM/gpt/gpt_client.py`
- 研究コンテキスト: `論文/結果/追加実験/論文執筆用/coco_retrieved_concepts/research_context.md`
- 実験結果: `results/20251127_140836/batch_results.json`














