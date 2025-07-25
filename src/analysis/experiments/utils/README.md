# 対比因子分析 統合ツール

utils ディレクトリには、対比因子実験のための統合ツールが含まれています。

## 🎯 主要機能

### **統合分析ツール** (`contrast_factor_analyzer.py`)

- **プロンプト生成**: 対比因子抽出用の構造化プロンプト作成
- **LLM 問い合わせ**: GPT による自動分析実行
- **スコア計算**: BERT スコア・BLEU スコアによる評価
- **結果保存**: JSON 形式での包括的な結果記録

## 🚀 クイックスタート

### 1. 基本的な使用方法

```python
from contrast_factor_analyzer import ContrastFactorAnalyzer

# アナライザー初期化
analyzer = ContrastFactorAnalyzer(debug=True)

# 分析実行
result = analyzer.analyze(
    group_a=["Great battery life", "Long-lasting battery"],
    group_b=["Poor screen quality", "Slow performance"],
    correct_answer="Battery performance and power management",
    output_dir="results/",
    experiment_name="battery_vs_screen"
)

# 結果確認
print(f"BERTスコア: {result['evaluation']['bert_score']:.4f}")
print(f"BLEUスコア: {result['evaluation']['bleu_score']:.4f}")
print(f"品質評価: {result['summary']['quality_assessment']['overall_quality']}")
```

### 2. Few-shot 学習を使用

```python
examples = [
    {
        "group_a": ["Fast delivery", "Quick shipping"],
        "group_b": ["Slow response", "Delayed support"],
        "answer": "Delivery speed and response time"
    }
]

result = analyzer.analyze(
    group_a=group_a,
    group_b=group_b,
    correct_answer=correct_answer,
    output_dir="results/",
    examples=examples,  # Few-shot例題
    output_language="英語"
)
```

### 3. バッチ実験

```python
experiments = [
    {
        "group_a": ["Fast performance", "Quick response"],
        "group_b": ["Large file size", "Heavy application"],
        "correct_answer": "Performance speed"
    },
    {
        "group_a": ["Secure encryption", "Privacy protection"],
        "group_b": ["Complex setup", "Difficult configuration"],
        "correct_answer": "Security features"
    }
]

results = analyzer.analyze_batch(
    experiments=experiments,
    output_dir="results/batch/",
    base_experiment_name="multi_feature_test"
)
```

## 📋 コンポーネント詳細

### 🎛️ **コア機能**

| ファイル                      | 機能               | 説明                           |
| ----------------------------- | ------------------ | ------------------------------ |
| `contrast_factor_analyzer.py` | **統合分析**       | 全機能を統合した主要ツール     |
| `get_score.py`                | **スコア計算**     | BERT スコア・BLEU スコアの計算 |
| `prompt_contrast_factor.py`   | **プロンプト生成** | 構造化プロンプトの自動生成     |

### 🤖 **LLM 連携**

| ファイル                | 機能                 | 説明                                 |
| ----------------------- | -------------------- | ------------------------------------ |
| `LLM/llm_factory.py`    | **LLM ファクトリー** | プロバイダー抽象化・クライアント作成 |
| `LLM/base_llm.py`       | **抽象基底クラス**   | 統一インターフェース定義             |
| `LLM/gpt/gpt_client.py` | **GPT クライアント** | OpenAI API 連携実装                  |

### ⚙️ **設定・スコア**

| ファイル                       | 機能            | 説明                     |
| ------------------------------ | --------------- | ------------------------ |
| `../conf/experiment_config.py` | **設定管理**    | 実験パラメータの一元管理 |
| `../conf/paramaters.yml`       | **YAML 設定**   | モデル・プロンプト設定   |
| `scores/bert_score.py`         | **BERT スコア** | 意味的類似度計算         |
| `scores/bleu_score.py`         | **BLEU スコア** | 表層一致度計算           |

## 📝 使用例

### **基本実行**

```bash
cd src/analysis/experiments/utils
python example_contrast_analysis.py
```

### **個別テスト**

```bash
# 統合ツールテスト
python contrast_factor_analyzer.py

# LLM接続テスト
python LLM/example_usage.py

# スコア計算テスト
python get_score.py

# プロンプト生成テスト
python prompt_contrast_factor.py
```

## 🔧 設定

### **環境変数設定**

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### **モデル設定** (`conf/paramaters.yml`)

```yaml
model: gpt-4o-mini
temperature: 0.7
max_tokens: 100
```

## 📊 結果形式

統合ツールは以下の構造で JSON 結果を出力:

```json
{
  "experiment_info": {
    "timestamp": "20250101_120000",
    "experiment_name": "battery_vs_screen",
    "model_config": {...}
  },
  "input": {
    "group_a": [...],
    "group_b": [...],
    "correct_answer": "..."
  },
  "process": {
    "prompt": "...",
    "llm_response": "..."
  },
  "evaluation": {
    "bert_score": 0.8234,
    "bleu_score": 0.6123
  },
  "summary": {
    "success": true,
    "quality_assessment": {
      "overall_quality": "good"
    }
  }
}
```

## 🎨 品質評価基準

| スコア範囲 | BERT レベル | BLEU レベル | 総合評価  |
| ---------- | ----------- | ----------- | --------- |
| 0.8+       | high        | high/medium | excellent |
| 0.6-0.8    | medium      | high/medium | good      |
| 0.4-0.6    | medium/high | any         | fair      |
| 0.4 未満   | low         | low         | poor      |

## 🔄 拡張方法

### **新しい LLM プロバイダー追加**

1. `LLM/base_llm.py`を継承したクライアント作成
2. `LLM/llm_factory.py`にプロバイダー登録

### **新しいスコア指標追加**

1. `scores/`ディレクトリに新しいスコア実装
2. `get_score.py`に統合

### **カスタム品質評価**

`ContrastFactorAnalyzer._assess_quality()`メソッドをオーバーライド

## 🐛 トラブルシューティング

### **よくあるエラー**

```bash
# APIキー未設定
ValueError: OPENAI_API_KEY環境変数が設定されていません
→ export OPENAI_API_KEY="your-key"

# モデル名不正
エラー: モデル 'invalid-model' は利用できません
→ conf/paramaters.ymlのモデル名を確認

# ライブラリ不足
ImportError: 必要なライブラリがインストールされていません
→ pip install sentence-transformers scikit-learn nltk
```

### **デバッグモード**

```python
analyzer = ContrastFactorAnalyzer(debug=True)  # 詳細ログ出力
```

## 📈 パフォーマンス

- **単一分析**: 約 10-30 秒（モデル・プロンプト長による）
- **バッチ実験**: N 件 × 15 秒程度
- **メモリ使用**: BERT モデル初回読み込み時に約 500MB

---

## 🎯 統一データセット管理インターフェース（v1.1）

### DatasetManager

全データセットを統一的に操作可能にする統合インターフェース。

#### 基本使用法

```python
from dataset_manager import DatasetManager

# 初期化
manager = DatasetManager()

# 1行でデータ取得・実験準備完了
splits = manager.get_binary_splits("steam", aspect="gameplay", group_size=300)

# 即座に実験開始
analyzer = ContrastFactorAnalyzer()
result = analyzer.analyze(splits.group_a, splits.group_b, splits.correct_answer)
```

#### 対応データセット

| データセット   | ID        | 分割タイプ         | アスペクト例              |
| -------------- | --------- | ------------------ | ------------------------- |
| Steam Reviews  | `steam`   | `binary_label`     | gameplay, story, visual   |
| SemEval ABSA   | `semeval` | `aspect_vs_others` | food, service, atmosphere |
| Amazon Reviews | `amazon`  | `aspect_vs_others` | product, quality, price   |

#### 高度な使用例

```python
# クロスデータセット比較
for dataset_id in ["steam", "semeval"]:
    splits = manager.get_binary_splits(dataset_id, aspect="price", group_size=300)
    examples = manager.create_examples(dataset_id, "price", shot_count=1)
    result = analyzer.analyze(splits.group_a, splits.group_b, splits.correct_answer, examples=examples)

# 実験設定自動取得
config = manager.get_experiment_config("steam")
print(f"利用可能アスペクト: {config['aspects']}")
print(f"予想実験数: {config['estimated_experiments']}")

# バッチ実験
for aspect in config['aspects'][:3]:
    for shot_count in config['shot_settings']:
        splits = manager.get_binary_splits("steam", aspect=aspect, group_size=100, split_type="binary_label")
        examples = manager.create_examples("steam", aspect, shot_count)
        result = analyzer.analyze(splits.group_a, splits.group_b, splits.correct_answer, examples=examples)
```

#### 設定ファイル（dataset_configs.yaml）

```yaml
datasets:
  steam:
    path: "/path/to/steam/data"
    domain: "gaming"
    aspects: ["gameplay", "story", "visual", ...]

experiment_defaults:
  group_size: 300
  shot_settings: [0, 1, 3]
  random_seed: 42
```

#### 効果

- **コード削減**: 従来の 531 行 → 約 100 行（81%削減）
- **実装時間短縮**: データセット切り替えが 1 行で完了
- **エラー削減**: 統一インターフェースによる安定性向上
- **拡張性**: 新データセット追加が`BaseDatasetLoader`継承のみで対応

---

📚 **関連ドキュメント**:

- [実験管理ルール](../../../.cursor/rules/)
- [データ構造説明](../../../../data/README.md)
- [SemEval 実験例](../2025/06/12/)
- [統一インターフェース実装例](../2025/07/18/)
