# Steamデータセット実験手順

Steam Review Aspect Datasetを使用した対比因子生成実験の手順です。

## データセット概要

- **データセットID**: `steam`
- **レコード数**: 約8,800件
- **アスペクト数**: 8個
- **推奨分割タイプ**: `binary_label`

## アスペクト一覧

| アスペクト | 説明 |
|-----------|------|
| gameplay | 操作性、メカニクス、インタラクティブ性、難易度などゲームプレイ上の要素 |
| visual | 美術性、アートスタイル、アニメーション、視覚効果など視覚要素 |
| story | 物語、キャラクター、設定、世界観構築などストーリーテリング要素 |
| audio | サウンドデザイン、音楽、ボイスアクトなど聴覚要素 |
| technical | バグ、パフォーマンス、OS/コントローラ対応など技術的側面 |
| price | ゲーム本体や追加コンテンツの価格に関する要素 |
| suggestion | 価格やパブリッシャーの提携など、ゲームの状態に関する提案・要望 |
| recommended | レビュワーがゲームを推奨するかどうか |

## 推奨設定

### グループサイズ

- **テスト/動作確認**: 10-20
- **通常実験**: 50-100
- **本格実験**: 200-300

### 分割タイプ

**`binary_label`** を推奨します。

- グループA: 対象アスペクトでポジティブ（label=1）のレビュー
- グループB: 対象アスペクトでネガティブ（label=0）のレビュー

### アスペクト説明文

公式CSV (`data/analysis-workspace/aspect_descriptions/steam/descriptions_official.csv`) の使用を推奨します。

## 実行例

### 対話型スクリプト

```bash
bash scripts/run_interactive_experiment.sh
```

1. データセット: `1` (Steam Reviews)
2. 正解アスペクトの表現: `2` (センテンス・公式)
3. アスペクト: `1,2,3` (gameplay, visual, story)
4. グループサイズ: `50`
5. 分割タイプ: `2` (binary_label)
6. 例題: `n` (使用しない)

### コマンドライン実行

```bash
cd /Users/seinoshun/imrb_research/src/analysis/experiments/2025/10/10
source ../../../../.venv/bin/activate

# 単一アスペクト
python run_experiment.py \
  --dataset steam \
  --aspect gameplay \
  --group-size 50 \
  --split-type binary_label \
  --use-aspect-descriptions \
  --aspect-descriptions-file ../../../../data/analysis-workspace/aspect_descriptions/steam/descriptions_official.csv

# 複数アスペクト
python run_experiment.py \
  --dataset steam \
  --aspects gameplay visual story \
  --group-size 50 \
  --split-type binary_label \
  --use-aspect-descriptions \
  --aspect-descriptions-file ../../../../data/analysis-workspace/aspect_descriptions/steam/descriptions_official.csv
```

### 設定ファイル

```yaml
experiments:
  - dataset: steam
    aspects:
      - gameplay
      - visual
      - story
    group_size: 50
    split_type: binary_label
    use_aspect_descriptions: true
    aspect_descriptions_file: data/analysis-workspace/aspect_descriptions/steam/descriptions_official.csv

output:
  directory: results/
  format: json

llm:
  model: gpt-4o-mini
  temperature: 0.7
  max_tokens: 150
```

## 注意点

1. **サンプル数**: 各アスペクトのポジ/ネガサンプル数が異なるため、グループサイズを大きくしすぎるとエラーになる場合があります
2. **アスペクト説明文**: 説明文を使用することで、より意味的な評価が可能になります
3. **評価スコア**: BERTスコアとBLEUスコアの両方を確認してください

## 期待される出力例

```
=== 結果 ===
BERTスコア: 0.5419
BLEUスコア: 0.0000
LLM応答: グループAは詳細なゲーム評価と感情的な反応が特徴。
品質評価: poor
```

## 関連ドキュメント

- [Steamデータセット詳細](../../datasets/steam-review-aspect-dataset/README.md)
- [実験スクリプト使い方ガイド](../guides/experiment-script-guide.md)
- [トラブルシューティング](../troubleshooting/common-issues.md)

