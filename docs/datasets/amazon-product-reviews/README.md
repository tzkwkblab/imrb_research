# Amazon Product Reviews（Bittlingmayer / fastText コーパス）

- Kaggle: https://www.kaggle.com/bittlingmayer/amazonreviews
- UCSD 概要: https://jmcauley.ucsd.edu/data/amazon/

## 概要

- 本コーパスは fastText 用の大規模レビュー極性データ（`train.ft.txt.bz2`, `test.ft.txt.bz2` など）として広く参照されるものです。
- 行ごとに `__label__1` / `__label__2`（など）のラベルとテキストが含まれる形式で、アスペクト注釈は提供されていません。
- 本プロジェクトでは、アスペクト比較実験のために「再現性のある独自アスペクト定義」を採用します（下記参照）。

## 本リポジトリでのアスペクト（独自定義）

- quality: 製品の作り・品質・性能特性に関する要素
- price: 価格水準とコストパフォーマンス、割引等に関する要素
- delivery: 配送速度、到着時の状態、配送の信頼性に関する要素
- service: 購入前後のカスタマーサービス、サポートの応答性等に関する要素
- product: 上記に収まらない総合的な製品満足度に関する要素

※ これらは公式定義ではありません。パイプライン既定のアスペクト名に整合し、かつ再現性を確保するための「プロジェクト定義」です。

## データ形式と利用方法

- センテンス比較（BERT）では、アスペクト名の代わりに短い説明文を用います。
- 正規 CSV: `data/analysis-workspace/aspect_descriptions/amazon/descriptions_official.csv`
  - 列構成: `aspect,description`
  - 内容は英語の短文定義（BERT 用途のため）

### 実行時の選択

- 対話スクリプトで「正解アスペクトの表現モード」を「センテンス（公式）」にすると、上記 CSV が優先されます。
- 「センテンス（任意の CSV）」を選ぶと `data/analysis-workspace/aspect_descriptions/amazon/` 配下から手動選択できます。

## ダウンロード/出典

- Kaggle: `https://www.kaggle.com/bittlingmayer/amazonreviews`
- UCSD Amazon データ一覧: `https://jmcauley.ucsd.edu/data/amazon/`

## ライセンス/注意

- ライセンス・利用条件は各配布元（Kaggle/UCSD）の規約に従ってください。
- 本リポジトリのアスペクト定義は独自のもので、原コーパスにアスペクト注釈を追加・再配布するものではありません（再現性のための記述です）。
