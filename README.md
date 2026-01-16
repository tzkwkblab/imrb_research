# 対比因子ラベル生成 研究プロジェクト

## 概要

### 背景
深層学習モデルは多様なタスクで高い性能を示す一方、その内部処理はブラックボックス性が高く、意思決定の根拠を人間が理解することは容易ではない。モデル内部から抽出された潜在概念に意味を付与する作業は人手で行われており、その負担軽減のために LLM を用いた自動化が検討されている。

### 手法
A/B 2群（特徴あり/なし）のテキスト集合の差分に基づき、「Aに含まれ Bに含まれない特徴」を表す自然言語ラベル（対比因子）を LLM で生成する**対比因子ラベル生成タスク**を提案。Few-shot プロンプト（0/1/3-shot）を用い、GPT-4o-mini 等の複数モデルで実験を行った。

### 実験
SemEval-2014 ABSA、Steam ゲームレビュー、GoEmotions、COCO Retrieved Concepts など複数ドメインのデータセットを使用。各グループ100件の条件で Sentence-BERT 類似度、BLEU、LLM 評価を組み合わせて生成ラベルの品質を多角的に測定した。

### 結果
全36条件の平均で SBERT類似度 約0.698（中程度の意味的一致）、BLEU 0.008（語彙一致は低い）を記録。1-shot が最も良好で、gameplay や food のような具体的な概念では高スコア、抽象度の高い概念では低下する傾向を確認した。

### 結論
提案手法は一定の条件下で人手による解釈ラベリングを部分的に代替できることを示した。ただし抽象概念への適用や文脈を汲み取った評価など、課題も明らかになった。

---

## 🔗 主要リンク

| 項目 | リンク |
|------|--------|
| 📄 論文 (PDF) | [論文/清野_修士卒論2025__New_.pdf](論文/清野_修士卒論2025__New_.pdf) |
| 📊 論文用実験結果 | [論文/結果/](論文/結果/) |
| 🔬 実験スクリプト | [scripts/run_interactive_experiment.sh](scripts/run_interactive_experiment.sh) |
| 📝 Overleaf | [Overleaf プロジェクト](https://www.overleaf.com/project/6943b94af12b74c92a2c1b1a) |

---

## 🚀 クイックスタート

以下の手順で環境構築から実験実行まで完結します。

```bash
# 1. リポジトリのクローン
git clone https://github.com/tzkwkblab/imrb_research.git
cd imrb_research

# 2. 仮想環境の作成と有効化
python -m venv .venv
source .venv/bin/activate  # Mac/Linux

# 3. 依存ライブラリのインストール
pip install -r requirements.txt

# 4. 環境変数の設定（.env.example をコピーして編集）
cp .env.example .env
# .env を編集して API キーを設定

# 5. データセットのダウンロード
python scripts/download_datasets.py --all

# 6. 実験の実行（対話型 or コマンドライン）
bash scripts/run_interactive_experiment.sh
# または直接実行:
# python src/analysis/experiments/2025/10/10/run_experiment.py --dataset steam --aspect gameplay --group-size 100
```

---

## 📋 初期設定

### Python 環境

- **Python 3.9 以上** を推奨
- 仮想環境を必ず使用（システム Python 禁止）

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### API 認証情報の設定

`.env.example` をコピーして `.env` を作成し、各 API キーを設定してください。

```bash
cp .env.example .env
```

**必須:**
| 項目 | 用途 | 取得先 |
|------|------|--------|
| `OPENAI_API_KEY` | LLM 実験実行 | [OpenAI Platform](https://platform.openai.com/) |

**オプション（データセットダウンロード時）:**
| 項目 | 用途 | 取得先 |
|------|------|--------|
| `KAGGLE_USERNAME`, `KAGGLE_KEY` | Kaggle データセット取得 | [Kaggle Settings](https://www.kaggle.com/settings) → API → Create New Token |

---

## 📦 データセットセットアップ

`.gitignore` により `data/external/`, `data/processed/`, `data/analysis-workspace/` はリポジトリに含まれません。

```bash
# Kaggle認証情報を設定後、実行
python scripts/download_datasets.py --all

# 個別ダウンロード
python scripts/download_datasets.py --dataset steam
python scripts/download_datasets.py --dataset goemotions
python scripts/download_datasets.py --dataset amazon

# 利用可能なデータセット一覧
python scripts/download_datasets.py --list
```

詳細な配置ルールは `data/README.md` を参照してください。

---

## 🔬 実験実行

### 対話型スクリプト（推奨）

```bash
bash scripts/run_interactive_experiment.sh
```

対話形式でデータセット、アスペクト、グループサイズなどを選択できます。

### コマンドライン直接実行

```bash
# Steam データセット、gameplay アスペクト、グループサイズ 100
python src/analysis/experiments/2025/10/10/run_experiment.py \
    --dataset steam --aspect gameplay --group-size 100 --split-type binary_label
```

**主要オプション:**
| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--dataset` | データセット名 (steam, semeval, amazon, goemotions, retrieved_concepts) | 必須 |
| `--aspect` | アスペクト名 | 必須 |
| `--group-size` | 各グループのサンプル数 | 50 |
| `--split-type` | 分割タイプ (binary_label, aspect_vs_others, aspect_vs_bottom100) | binary_label |
| `--silent` | ファイル保存をスキップ（デバッグ用） | False |

詳細は [実験スクリプト使い方ガイド](docs/experiments/guides/experiment-script-guide.md) を参照してください。

---

## 📊 実行サンプルと期待結果

### サンプル実行

```bash
# サンプル: Steam の gameplay アスペクトで実験
python src/analysis/experiments/2025/10/10/run_experiment.py \
    --dataset steam --aspect gameplay --group-size 100 --split-type binary_label
```

### 期待される出力

```
============================================================
統一実験パイプライン
============================================================

[モード] コマンドライン引数から実行
データセット: steam

==================================================
実験開始: steam_gameplay_20260116_151500
データセット: steam
アスペクト: gameplay
グループサイズ: 100
分割タイプ: binary_label

[1/3] データ読み込み中...
✅ データ読み込み完了 (A: 100件, B: 100件)

[2/3] 対比因子分析実行中...
✅ LLM応答取得完了

[3/3] スコア確認中...
✅ スコア確認完了

==================================================
=== 結果 ===
BERTスコア: 0.75
BLEUスコア: 0.12
LLM応答: Engaging and immersive game mechanics with intuitive controls.
品質評価: good

📁 結果保存: results/batch_experiment_20260116_151500.json

✅ パイプライン実行完了
```

### 結果の解釈

- **BERTScore**: 意味的類似度（0.0-1.0、高いほど良い）
- **BLEUScore**: 語彙的一致度（0.0-1.0、高いほど良い）
- **LLM応答**: 生成された対比因子ラベル
- **品質評価**: `poor` / `medium` / `good`

結果ファイルは `results/batch_experiment_*.json` に保存されます。

---

## 📁 ディレクトリ構成

```
imrb_research/
├── src/                          # 分析/実験コード
├── data/                         # データディレクトリ（詳細は data/README.md）
│   ├── external/                 # 外部データセット（読み取り専用）
│   ├── processed/                # 前処理済みデータ
│   ├── analysis-workspace/       # 実験用説明CSV・例題
│   └── cache/                    # 一時ファイル
├── docs/                         # ドキュメント集
├── scripts/                      # 実行支援スクリプト
├── experiment_summaries/         # 実験サマリー
├── results/                      # 実験結果ログ
├── slide/                        # 発表スライド
├── 論文/                         # LaTeX 論文原稿
└── 引き継ぎ資料/                 # 引き継ぎ用資料
```

---

## 📚 主要データセット

| データセット | アスペクト数 | ドキュメント |
|-------------|-------------|-------------|
| Steam Review | 8 (gameplay, visual, story 等) | `docs/datasets/steam-review-aspect-dataset/` |
| SemEval ABSA | 4 (food, service, price, atmosphere) | `docs/datasets/semeval-absa/` |
| Amazon Reviews | 5 (quality, price, delivery 等) | `docs/datasets/amazon-product-reviews/` |
| GoEmotions | 28 (admiration, anger, joy 等) | `docs/datasets/goemotions/` |
| Retrieved Concepts | 300 (concept_0 ～ concept_299) | `docs/datasets/retrieved-concepts/` |

---

## 📖 ドキュメント

- **データセット詳細**: `docs/datasets/`
- **実験ガイド**: `docs/experiments/guides/experiment-script-guide.md`
- **データ管理**: `data/README.md`
- **スクリプト一覧**: `scripts/README.md`

---

## 🔧 トラブルシューティング

### Kaggle API 認証エラー

```bash
# ~/.kaggle/kaggle.json が必要
mkdir -p ~/.kaggle
# Kaggle Settings → API → Create New Token でダウンロードしたファイルを配置
chmod 600 ~/.kaggle/kaggle.json
```

### OpenAI API エラー

`.env` ファイルに有効な `OPENAI_API_KEY` が設定されているか確認してください。

### データセットが見つからない

`download_datasets.py` を実行してデータセットをダウンロードするか、`data/README.md` に従って手動配置してください。

---

補足: 各項目の詳細は該当ディレクトリの README または `docs/` に配置しています。
