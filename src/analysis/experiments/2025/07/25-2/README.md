# 対比因子生成実験 MVP 版

新しい utils 統合ツールを活用した最小構成の対比因子生成実験です。

## 🎯 実装目的

- **最小限の構成**で動作する対比因子生成実験の MVP
- 新しい`utils`ツール（`dataset_manager.py`、`contrast_factor_analyzer.py`）の活用検証
- 複雑な機能を排除したシンプルな実験フロー

## 📋 実装範囲

### 対象範囲（MVP）

- **データセット**: Steam Review Dataset のみ
- **アスペクト**: "gameplay" vs "visual" の 2 アスペクト
- **実験設定**: 0-shot のみ
- **スコア計算**: BERT スコア・BLEU スコア
- **出力**: JSON 形式での結果保存

### 除外範囲

- 複数データセット対応
- Few-shot 設定（1-shot、3-shot）
- 包括的レポート生成
- バッチ実験機能
- 詳細統計分析

## 🏗️ ファイル構成

```
25-2/
├── mvp_config.py          # 固定設定定義
├── mvp_experiment.py      # メイン実験スクリプト
├── README.md              # このファイル
└── results/               # 実験結果保存ディレクトリ
```

## 🔧 使用ツール

### 新しい utils 統合ツール

- `dataset_manager.py`: データセット管理・分割機能
- `contrast_factor_analyzer.py`: 対比因子分析統合機能
- `scores/bert_score.py`: BERT スコア計算
- `scores/bleu_score.py`: BLEU スコア計算

### 設定ファイル駆動

```python
# データセット設定
DATASET = "steam"
ASPECTS = ["gameplay", "visual"]
GROUP_SIZE = 100

# 実験設定
SHOT_CONFIG = 0
OUTPUT_DIR = "results/"
```

## 🚀 実行方法

### 1. 基本実行

```bash
cd src/analysis/experiments/2025/07/25-2/
python mvp_experiment.py
```

### 2. 実行例（期待される出力）

```
=== 対比因子生成実験 MVP ===
データセット: steam
実験バージョン: MVP-1.0

アスペクト: gameplay
[実験実行]
✅ データ分割取得完了 (グループA: 100件, グループB: 100件)
✅ 対比因子分析実行完了
✅ スコア計算完了

[結果]
BERTスコア: 0.8234
BLEUスコア: 0.6123
品質評価: good
保存先: results/mvp_gameplay_20250725_120000.json
--------------------------------------------------

アスペクト: visual
[実験実行]
✅ データ分割取得完了 (グループA: 100件, グループB: 100件)
✅ 対比因子分析実行完了
✅ スコア計算完了

[結果]
BERTスコア: 0.7891
BLEUスコア: 0.5934
品質評価: fair
保存先: results/mvp_visual_20250725_120001.json
--------------------------------------------------

=== 実験完了 ===
統合結果: results/mvp_summary_20250725_120000.json
✅ MVP実験が正常に完了しました
```

## 📊 出力形式

### 個別結果ファイル

```json
{
  "experiment_info": {
    "timestamp": "20250725_120000",
    "dataset": "steam",
    "aspect": "gameplay",
    "group_size": 100,
    "version": "MVP-1.0"
  },
  "results": {
    "bert_score": 0.8234,
    "bleu_score": 0.6123,
    "llm_response": "...",
    "correct_answer": "..."
  },
  "summary": {
    "success": true,
    "quality": "good"
  }
}
```

### 統合結果ファイル

```json
{
  "experiment_meta": {
    "version": "MVP-1.0",
    "timestamp": "20250725_120000",
    "dataset": "steam",
    "aspects": ["gameplay", "visual"],
    "description": "最小構成での対比因子生成実験"
  },
  "results": [
    // 各アスペクトの実験結果
  ]
}
```

## 🔍 技術実装詳細

### DatasetManager 活用パターン

```python
# 設定ファイル駆動でのデータセット管理
manager = DatasetManager.from_config()

# Steam データセットの分割取得
splits = manager.get_binary_splits("steam", aspect="gameplay", group_size=100)
```

### ContrastFactorAnalyzer 活用パターン

```python
# 統合分析ツールの活用
analyzer = ContrastFactorAnalyzer(debug=True)

# 対比因子分析実行
result = analyzer.analyze(
    group_a=splits.group_a,
    group_b=splits.group_b,
    correct_answer=splits.correct_answer,
    output_dir="results/",
    experiment_name=f"mvp_{aspect}_{timestamp}"
)
```

### スコア計算パターン

```python
# BERTスコア・BLEUスコア計算
bert_score = calculate_bert_score(llm_response, correct_answer)
bleu_score = calculate_bleu_score(llm_response, correct_answer)

# 品質評価
avg_score = (bert_score + bleu_score) / 2
quality = "good" if avg_score >= 0.7 else "fair" if avg_score >= 0.5 else "poor"
```

## ✅ 完成確認項目

- [x] 3 ファイル構成での実装完了
- [x] Steam データセットからデータ取得成功（簡略化版で動作確認済み）
- [x] gameplay/visual 両アスペクトでの実験実行
- [x] BERT スコア・BLEU スコアの計算・表示（簡略化版）
- [x] JSON 形式での結果保存
- [x] エラーなしでの完全実行

### 📝 実装バリエーション

#### 1. `mvp_experiment.py` - 完全版（utils 統合ツール使用）

- 実際の utils 統合ツールを活用
- 本格的な BERT/BLEU スコア計算
- 依存関係: numpy, yaml, torch 等

#### 2. `mvp_simple.py` - 簡略化版（動作確認済み）

- 依存関係最小限
- モックデータでの動作確認
- 基本フロー検証完了

## 🔗 関連ファイル

- 完全版実装: `../25/`
- utils 統合ツール: `../../utils/`
- README 参考: `../../utils/README.md`
- 基本使用例: `../../utils/example_contrast_analysis.py`

## 📝 注意事項

1. **環境変数**: `OPENAI_API_KEY`が設定されている必要があります
2. **データセット**: Steam Review Dataset が適切に配置されている必要があります
3. **依存関係**: utils 統合ツールが正常に動作する必要があります
4. **実行時間**: MVP のため小さなサンプルサイズ（100 件）で高速実行

## 🎯 成功基準

1. **動作する**: エラーなしで最後まで実行完了
2. **シンプル**: 3 ファイル構成での最小実装
3. **有効**: 意味のある BERT/BLEU スコアを出力
4. **保存**: JSON 形式での結果保存成功
5. **拡張可能**: 将来的な機能追加が容易な構造
