# SemEval ABSA（Restaurants）

SemEval-2014 Task 4（Aspect Based Sentiment Analysis）のレストランドメインに関する要約です。タスク定義や評価指標は下記の公式情報を参照してください。

- タスクページ: http://alt.qcri.org/semeval2014/task4/
- 概要論文（ACL Anthology）: https://aclanthology.org/S14-2004.pdf

## 概要

- レストラン分野のレビュー文に対し、アスペクト（観点）とその極性（ポジ/ネガ等）を扱う評価タスク。
- 公式のアスペクトカテゴリとしては、レストラン領域で一般的な要素（例: Food, Service, Price, Ambience など）が用いられます。
- 本プロジェクトでは、実験パイプラインの都合上、アスペクト名を `food / service / price / atmosphere` に統一して利用します（Ambience ≒ Atmosphere）。

## アスペクト（本リポジトリで使用）

- food: 料理・飲み物に関する要素（味、品質、新鮮さ、量、バラエティなど）
- service: 接客に関する要素（スタッフの対応、速度、気配りなど）
- price: 価格に関する要素（価格水準、コスパ、割引やお得感の評価）
- atmosphere: 雰囲気・環境に関する要素（店内の雰囲気、騒音、清潔さ、内装など）

※ 公式資料では Ambience（雰囲気）表記が一般的ですが、本リポジトリでは `atmosphere` を採用しています。

## データ形式と利用方法

- 本リポジトリのセンテンス比較（BERT）では、アスペクト名の代わりに「短い説明文」を用います。
- 正規 CSV（英語説明文）: `data/analysis-workspace/aspect_descriptions/semeval/descriptions_official.csv`
  - 列構成: `aspect,description`
  - 例:
    - food → "Food and beverages: taste, quality, freshness, portion size, and variety."
    - service → "Service quality: staff friendliness, speed, and attentiveness."
    - price → "Price level and value for money: cost, deals, and perceived fairness."
    - atmosphere → "Ambience and environment: atmosphere, noise level, cleanliness, and decor."

### 実行時の選択

- 対話スクリプトで「正解アスペクトの表現モード」を「センテンス（公式）」にすると、上記 CSV が優先されます。
- 「センテンス（任意の CSV）」を選ぶと `data/analysis-workspace/aspect_descriptions/semeval/` 配下から手動選択できます。

## ダウンロード/出典

- タスクページ: `http://alt.qcri.org/semeval2014/task4/`
- 概要論文: `https://aclanthology.org/S14-2004.pdf`

## 引用

SemEval-2014 Task 4（ABSA）に準拠します。学術目的で利用する場合、上記の公式ページや論文を引用してください。

## ライセンス/注意

- SemEval データの配布・利用条件は各配布元の規約に従ってください。
- 本リポジトリにおけるアスペクト説明文は実験の再現性を目的としており、原データのライセンスや配布条件を変更するものではありません。
