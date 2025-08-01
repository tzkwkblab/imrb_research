# Steam 8アスペクト対比因子生成実験

## 概要

Steamレビューデータセットを使用した8アスペクト対比因子生成実験です。
アスペクト説明文機能を使用して、より高精度なスコア計算を実現します。

## 実験設定

### 対象アスペクト
- recommended
- story  
- gameplay
- visual
- audio
- technical
- price
- suggestion

### Shot設定
- 0-shot
- 1-shot
- 3-shot

### 実験規模
- 総実験数: 24個 (8アスペクト × 3shot設定)
- 各グループサイズ: 300件
- アスペクト説明文使用: 有効

## ファイル構成

```
29/
├── experiment_config.py          # 実験設定
├── steam_aspect_experiment.py    # メイン実験スクリプト
├── results/                      # 結果保存ディレクトリ
│   ├── steam_8aspect_experiment_YYYYMMDD_HHMMSS.json
│   └── summary_table_YYYYMMDD_HHMMSS.md
└── README.md                     # このファイル
```

## 実行方法

```bash
cd src/analysis/experiments/2025/07/29
python steam_aspect_experiment.py
```

## 出力形式

### 1. JSON結果ファイル
詳細な実験結果とメタデータを含むJSONファイル

### 2. Markdown表形式
| アスペクト | 0-shot | 1-shot | 3-shot |
|-----------|--------|--------|--------|
| recommended | 0.8234 | 0.8456 | 0.8678 |
| story | 0.7891 | 0.8123 | 0.8345 |
| ... | ... | ... | ... |

## 技術仕様

### 使用ツール
- DatasetManager: データセット管理
- ContrastFactorAnalyzer: 対比因子分析
- AspectDescriptionManager: アスペクト説明文管理

### スコア計算
- BERTスコア: 意味類似度
- BLEUスコア: 表層一致度

### LLM設定
- モデル: GPT-3.5-turbo
- 温度: 0.7
- 最大トークン: 1000

## 期待される結果

アスペクト説明文機能により、従来のアスペクト名使用と比較してBERTスコアが向上することが期待されます。

## 注意事項

- 実験実行には約30-60分かかります
- APIキーが設定されていることを確認してください
- 十分なディスク容量を確保してください