# 論文ディレクトリ

修士論文「大規模言語モデルを用いた対比因子ラベル生成手法に関する研究」の LaTeX ソースコードと関連ファイルを管理するディレクトリです。

## ディレクトリ構成

```
論文/
├── masterThesisJa.tex          # メインLaTeXファイル
├── masterThesisJa.sty          # 論文スタイルファイル
├── latexmkrc                   # latexmk設定ファイル
├── chapters/                   # 各章のLaTeXソース
│   ├── 01_introduction.tex
│   ├── 02_related_work.tex
│   ├── 03_proposal.tex
│   ├── 04_experiment_and_results.tex
│   ├── 05_discussion.tex
│   ├── 06_conclusion.tex
│   ├── acknowledgments.tex
│   └── references.tex
├── 実験結果集約/                # 実験結果の集約スクリプトとレポート
├── 結果/                       # 実験結果と分析レポート
├── image/                      # 論文に使用する画像
├── 各章v1/                     # 各章のMarkdown版（v1）
├── archive/                    # 過去バージョンのアーカイブ
└── references_search_list.md   # 参考文献検索リスト
```

## ビルド方法

### 前提条件

- pLaTeX（日本語 LaTeX）
- pbibtex（参考文献処理）
- latexmk（ビルド自動化）

### ビルドコマンド

```bash
# PDFを生成
latexmk masterThesisJa.tex

# クリーンアップ
latexmk -c masterThesisJa.tex

# 完全クリーンアップ
latexmk -C masterThesisJa.tex
```

## 主要ファイル

### masterThesisJa.tex

論文のメインファイル。各章を`\input`で読み込みます。

### masterThesisJa.sty

論文のスタイル定義（表紙、ページ設定、コマンド定義など）。

### chapters/

各章の LaTeX ソースコード：

- **01_introduction.tex**: 序論
- **02_related_work.tex**: 関連研究
- **03_proposal.tex**: 提案手法
- **04_experiment_and_results.tex**: 実験と結果
- **05_discussion.tex**: 考察
- **06_conclusion.tex**: 結論
- **acknowledgments.tex**: 謝辞
- **references.tex**: 参考文献

## サブディレクトリ

### 実験結果集約/

論文執筆用に実験結果を集約するスクリプトとレポート。

詳細は [`実験結果集約/README.md`](実験結果集約/README.md) を参照。

### 結果/

実験結果と分析レポートを格納。

- **追加実験/**: 追加実験の結果と分析
  - **論文執筆用/**: 論文執筆時に参照しやすいように整理された実験結果
- **実験設定/**: 実験パラメータと設定ファイル

### image/

論文に使用する画像ファイル。

- **coco/**: COCO データセットの画像
- **LIME.png, SHAP.png**: 説明手法の図

### 各章 v1/

各章の Markdown 版（v1）。執筆過程の記録。

### archive/

過去バージョンのアーカイブ。

## 関連ファイル

### references_search_list.md

参考文献の検索リスト。論文執筆時に参照。

### download_coco_images.py

COCO データセットの画像をダウンロードするスクリプト。

## 論文情報

- **タイトル（日本語）**: 大規模言語モデルを用いた対比因子ラベル生成手法に関する研究
- **タイトル（英語）**: A Study on Generating Contrastive Factor Labels for Explainable AI
- **学生**: 清野 駿 (202421675)
- **指導教員**: 若林 啓、伊藤 寛祥
- **提出予定**: 2025 年 12 月

## 注意事項

- LaTeX ファイルの文字エンコーディングは UTF-8 です
- 画像ファイルは`image/`ディレクトリに配置してください
- 実験結果を更新した場合は、`実験結果集約/`のスクリプトを実行してレポートを再生成してください
