## TODO

- ゲームデータセットをダウンロードして使えるようにする
- 今まで外部データセットをダウンロードしていたディレクトリに、同じようにデータを入れる
- 入れたデータの中身を見る。

### データ情報

## 現在着手している場所

新しいデータセットを試してみます。
Steam Review Aspect Dataset (Steam Game Review Aspect Dataset)

1. Kaggle から取得
   • データセット名：ilosvigil/steam-review-aspect-dataset
   • 構成ファイル：
   • train.csv（900 件）
   • test.csv（200 件）
   • 内容：review, cleaned_review, labels（8 アスペクト配列） ￼ ￼
   kaggle datasets download ilosvigil/steam-review-aspect-dataset
   unzip steam-review-aspect-dataset.zip -d data/steam_aspect/
2. GitHub / Hugging Face から取得
   • GitHub：ilos-vigil/steam-review-aspect-dataset リポジトリ ￼
   • Hugging Face：同データセットが提供されている（Arrow Parquet 形式）

Hugging Face 利用例（Python）：
from datasets import load_dataset
ds = load_dataset("ilosvigil/steam-review-aspect-dataset")
train = ds["train"] # 900 examples
test = ds["test"] # 200 examples

データれい：

{
"review": "Devs are on meth pricing this game at $44",
"aspects": ["Price"]
}

{
"review": "I cost twice cheaper than most of recent Mediocre AAA games like Tomb Raider 2013, Bioshock Infinite ...",
"aspects": ["Price", "Recommended", "Gameplay"]
}

| 項目         | 詳細                                                                                |
| ------------ | ----------------------------------------------------------------------------------- |
| 総レビュー数 | 1,100 件（900 トレーニング + 200 テスト）                                           |
| アスペクト数 | 8 種類（Recommended, Story, Gameplay, Visual, Audio, Technical, Price, Suggestion） |
| ファイル形式 | CSV, JSON, Apache Arrow（Parquet）                                                  |
| レビュー長   | 中長文（約 300 ～ 400 字程度）                                                      |
| 取得日付     | 2024 年 2 月 21 日時点の Steam レビューから収集                                     |
