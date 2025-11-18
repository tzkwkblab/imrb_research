## プロジェクト概要

このリポジトリは、説明可能 AI のための「対比因子ラベル生成」手法を検証する研究プロジェクトです。A/B 2 群のテキスト差分を LLM で要約し、意味的に妥当なラベル（対比因子）を自動生成・評価します。詳細は各ディレクトリの README と `docs/` を参照してください。

### 研究テーマ/方向性（要点）

- **目的**: 2 群（A: 特徴あり, B: 特徴なし）の本質的差分を自然言語で要約し、概念レベルの説明を自動生成
- **適用データ**: Steam ゲームレビュー、SemEval ABSA（レストラン）、Amazon レビュー、GoEmotions（感情分類）
- **評価**: 主要指標は BERTScore と BLEU（意味/語彙の両面を記録）

## ディレクトリ構成（トップレベル）

- `src/`: 分析/実験コード（統一パイプライン、ユーティリティ、データ処理）
- `data/`:
  - `external/` 外部データ（読み取り専用、`current` シンボリックリンク運用）
  - `processed/` 前処理済み
  - `analysis-workspace/` 実験で参照する説明 CSV や例題
  - `cache/` 一時ファイル
- `docs/`: データセット・実験・ユーティリティなどのドキュメント集
- `experiment_summaries/`: 実験サマリーの Markdown
- `scripts/`: 実行支援スクリプト（対話型実験ランナー等）
- `slide/`: 発表用スライド（Markdown→PPTX 変換ユーティリティあり）
- `論文/`: LaTeX 原稿一式（和文テンプレート）

各詳細は当該ディレクトリ直下の README または `docs/` を参照してください。

## データ管理と配置（要点）

- 基本構造と運用は `data/README.md` を参照
- 外部データは `data/external/{dataset}/{source}/{version}/` に配置し、最新版は `current` リンクで参照
- 処理済みは `data/processed/`、ワーク系（説明 CSV や few-shot 例題）は `data/analysis-workspace/`
- 直接編集禁止: `external/` 配下（バージョン/整合性保持）

## 主要データセット（概要のみ）

- **Steam Review aspect dataset**（8 アスペクト: recommended, story, gameplay, visual, audio, technical, price, suggestion）

  - ドキュメント: `docs/datasets/steam-review-aspect-dataset/README.md`
  - 正規 CSV: `data/analysis-workspace/aspect_descriptions/steam/descriptions_official.csv`

- **SemEval ABSA (Restaurants)**（`food, service, price, atmosphere` を採用）

  - ドキュメント: `docs/datasets/semeval-absa/README.md`
  - 正規 CSV: `data/analysis-workspace/aspect_descriptions/semeval/descriptions_official.csv`

- **Amazon Product Reviews (Bittlingmayer)**（本プロジェクト独自アスペクト: `quality, price, delivery, service, product`）
  - ドキュメント: `docs/datasets/amazon-product-reviews/README.md`
  - 正規 CSV: `data/analysis-workspace/aspect_descriptions/amazon/descriptions_official.csv`

- **Retrieved Concepts (COCO Captions)**（300 コンセプト: concept_0 ～ concept_299）
  - ドキュメント: `docs/datasets/retrieved-concepts/README.md`
  - Top-100/Bottom-100 の類似度順キャプションデータ

- **GoEmotions**（28感情カテゴリ: admiration, amusement, anger, joy, neutral など）
  - ドキュメント: `docs/datasets/goemotions/README.md`
  - Redditコメントから収集された細粒度感情分類データセット

## 実験ワークフローと配置

- 実験結果は日付階層: `src/analysis/experiments/{YYYY}/{MM}/{DD-実験番号}/`
  - 例: `2025/10/10/` に統一パイプライン（`run_experiment.py`, `pipeline_config.yaml` 等）
  - 結果は `results/batch_experiment_*.json` として保存（実験メタ情報含む）
- 実験履歴の集約は `src/analysis/experiment_history_consolidator.py`（サマリーは `experiment_summaries/`）

## 実行方法（最短ルート）

1. 仮想環境の準備/アクティベート（プロジェクトルート）

```bash
cd /Users/seinoshun/imrb_research
source .venv/bin/activate
```

2. 対話型ランナー（推奨）

```bash
bash scripts/run_interactive_experiment.sh
```

詳細な使い方は [実験スクリプト使い方ガイド](docs/experiments/guides/experiment-script-guide.md) を参照してください。

3. 直接実行（例: 2025/10/10 の統一パイプライン）

```bash
cd src/analysis/experiments/2025/10/10
python run_experiment.py --config pipeline_config.yaml
# あるいは: python run_experiment.py --dataset steam --aspect gameplay --group-size 50
```

## 評価指標（研究の主要スコア）

- **BERTScore**（意味類似）と **BLEU**（語彙一致）を常に記録
- 位置づけ/理由は `docs/` と各実験 README を参照

## ドキュメントの見方

- データセット詳細: `docs/datasets/`
- 実験ドキュメント: `docs/experiments/`
- ユーティリティ/再利用パターン: `docs/utils.md`, `docs/reusable-components/`

## 論文（原稿）

- 場所: `論文/`
- 主ファイル: `論文/masterThesisJaSample.tex`
- ビルド例（latexmk がある場合）:

```bash
cd /Users/seinoshun/imrb_research/論文
latexmk -pdf masterThesisJaSample.tex
```

## スライド（発表資料）

- 場所: `slide/`
- 変換: Markdown → PPTX 変換ユーティリティ `slide/util/md2pptx.sh`

```bash
bash slide/util/md2pptx.sh
```

## 環境準備（Python）

- 依存関係: `requirements.txt`
- 実行前に仮想環境を必ずアクティベート（システム Python 禁止）

## コミットルール

- 1 行・最大 50 文字目安、命令形で簡潔に（詳細は `.cursor/rules/` を参照）

---

補足: 本 README は概要のみを記載しています。各項目の詳細は該当ディレクトリの README または `docs/` に配置しています。
