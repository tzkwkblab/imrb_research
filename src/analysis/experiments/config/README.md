# 統一実験条件設定ファイル

プロンプト、使用モデル、出力ランダム性(temperature)、評価指標(BERT/BLEU スコア)などの実験条件を統一管理するためのファイル群です。

## ファイル構成

```
src/analysis/experiments/config/
├── experiment_config.py          # Python設定ファイル（メイン）
├── experiment_settings.json      # JSON設定ファイル
├── config_usage_example.py       # 使用方法サンプル
└── README.md                     # このファイル
```

## 主要機能

### 📋 設定項目

| 項目              | 説明                  | 設定値例                         |
| ----------------- | --------------------- | -------------------------------- |
| **モデル設定**    | 使用 LLM とパラメータ | `gpt-4`, `gpt-3.5-turbo`         |
| **Temperature**   | 出力ランダム性        | `0.0`(決定的) ～ `1.0`(高創造性) |
| **Few-shot 設定** | 例題数と学習設定      | `[0, 1, 3, 5]`                   |
| **評価指標**      | 使用する評価手法      | `BERT_score`, `BLEU_score`       |
| **プロンプト**    | タスク別テンプレート  | 対比因子抽出、特徴判定等         |
| **データセット**  | 使用データと特徴      | `SemEval ABSA`, `Amazon Reviews` |

### 🎛️ プリセット設定

| プリセット名        | モデル  | Temperature | 用途           |
| ------------------- | ------- | ----------- | -------------- |
| `high_precision`    | GPT-4   | 0.0         | 高精度実験     |
| `balanced`          | GPT-4   | 0.3         | 標準実験       |
| `high_creativity`   | GPT-3.5 | 1.0         | 創造性重視実験 |
| `research_standard` | GPT-4   | 0.3         | 論文用標準設定 |

## 使用方法

### Python 設定ファイル使用

```python
from config.experiment_config import ExperimentConfig, BALANCED_CONFIG

# 1. デフォルト設定
config = ExperimentConfig()

# 2. カスタム設定
config = ExperimentConfig(
    model_key="gpt-4",
    temperature_key="low_creativity",
    fewshot_key="standard",
    evaluation_key="primary"
)

# 3. プリセット設定
config = BALANCED_CONFIG

# 4. プロンプト取得
prompt = config.get_prompt_template("contrast")

# 5. 設定出力
config_dict = config.to_dict()
```

### JSON 設定ファイル使用

```python
import json

# JSON設定読み込み
with open('config/experiment_settings.json', 'r') as f:
    settings = json.load(f)

# 設定値取得
model_config = settings["models"]["gpt-4"]
temp_value = settings["temperature_settings"]["low_creativity"]["value"]
prompt_template = settings["prompt_templates"]["basic_contrast"]["template"]
```

## 評価指標設計思想

本研究では以下の評価指標を採用：

### 主要指標

- **BERT スコア**: 意味類似度に基づく深層ベクトル比較
- **BLEU スコア**: n-gram ベースの表層一致率

### 参考指標

- **分類精度**: 1/0 判定正解率（参考値）

### 設計根拠

LLM 説明文と人間定義正解説明の一致度測定が主目的であり、説明タスクにおける意味的妥当性を重視します。

## プロンプトテンプレート

### 対比因子抽出プロンプト

```
あなたは{domain_context}レビュー分析の専門家です。

【分析タスク】
以下の2つのレビューグループを比較して、グループAに特徴的で
グループBには見られない表現パターンや内容の特徴を特定してください。
...
```

### 特徴判定プロンプト

```
あなたは商品レビューを分析する専門家です。
以下の商品レビューに対して、各特徴が当てはまるかどうかを判定してください。
...
```

### ハルシネーション検証プロンプト

```
以下のレビューグループの分析結果について、その妥当性を評価してください。
...
```

## 実験実行での統合例

```python
# 実験スクリプトでの使用例
from config.experiment_config import ExperimentConfig
import openai

def run_contrast_experiment():
    # 研究標準設定を読み込み
    config = ExperimentConfig(
        model_key="gpt-4",
        temperature_key="low_creativity",
        evaluation_key="primary"
    )

    # OpenAI API設定
    client = openai.OpenAI()

    # プロンプト生成
    prompt = config.get_prompt_template("contrast").format(
        domain_context="レストラン",
        feature="food",
        group_a_size=100,
        group_b_size=100,
        few_shot_examples="",
        group_a_reviews=group_a_data,
        group_b_reviews=group_b_data
    )

    # GPT実行
    response = client.chat.completions.create(
        model=config.model.name,
        messages=[{"role": "user", "content": prompt}],
        temperature=config.model.temperature,
        max_tokens=config.model.max_tokens
    )

    # 評価指標計算
    if config.evaluation.use_bert_score:
        bert_score = calculate_bert_similarity(response, reference)

    if config.evaluation.use_bleu_score:
        bleu_score = calculate_bleu_similarity(response, reference)
```

## 新しい実験設定の追加

### 1. Python 設定追加

```python
# experiment_config.py に追加
CUSTOM_CONFIG = ExperimentConfig(
    model_key="gpt-4-turbo",
    temperature_key="balanced",
    fewshot_key="comprehensive",
    evaluation_key="comprehensive"
)
```

### 2. JSON 設定追加

```json
// experiment_settings.json に追加
"experiment_presets": {
  "my_custom_preset": {
    "model": "gpt-4-turbo",
    "temperature": "balanced",
    "fewshot": "comprehensive",
    "evaluation": "comprehensive",
    "description": "カスタム実験設定"
  }
}
```

## 設定ファイルの利点

### 🔧 実験条件の統一

- 全実験で一貫した設定使用
- 設定変更の一元管理
- 実験の再現性確保

### 📊 研究デザインの明確化

- 評価指標の優先順位明示
- プロンプト設計の標準化
- 実験パラメータの体系化

### ⚡ 開発効率の向上

- 設定コードの重複排除
- プリセット活用による時間短縮
- 設定ミスの防止

### 📈 実験管理の改善

- 設定履歴の追跡可能
- 異なる設定での比較容易
- 論文執筆時の設定参照簡単

## トラブルシューティング

### よくある問題

1. **モジュールインポートエラー**

   ```python
   # 解決法：パスを正しく設定
   import sys
   sys.path.append('src/analysis/experiments/config')
   ```

2. **JSON 読み込みエラー**

   ```python
   # 解決法：エンコーディング指定
   with open('settings.json', 'r', encoding='utf-8') as f:
       config = json.load(f)
   ```

3. **設定キーエラー**
   ```python
   # 解決法：利用可能キーを確認
   from experiment_config import MODEL_CONFIGS
   print(list(MODEL_CONFIGS.keys()))
   ```

## 更新履歴

| 日付       | バージョン | 変更内容 |
| ---------- | ---------- | -------- |
| 2025-06-18 | 1.0        | 初版作成 |

## 関連ファイル

- 📁 [実験履歴統合ドキュメント](../../../data/analysis-workspace/experiment_history_consolidated_20250618_155212.md)
- 📁 [研究ルール](../../../../.cursor/rules/)
- 📁 [データ管理構造](../../../../data/README.md)
