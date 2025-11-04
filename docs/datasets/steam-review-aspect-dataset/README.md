# Steam レビュー・アスペクトデータセット

本データセットは英語の Steam レビュー 1,100 件（学習 900 / テスト 200）で構成され、英語レビューにおいてどのアスペクト（観点）が言及されているかを特定する目的で作成されました。内容の多くは SRec のブログ記事「Steam review aspect dataset」（https://srec.ai/blog/steam-review-aspect-dataset）に基づいています。また、関連背景として「Analysis of 43 million English Steam Reviews」（https://srec.ai/blog/analysis-43m-english-steam-reviews）が参照されています。

## データ収集とアノテーション

- レビューは SRec データベースのスナップショット（2024/02/21）から取得。
- SRec は Steam 提供の API（https://partner.steamgames.com/doc/store/getreviews）を用いて、全ゲーム/Mod のレビューを収集。
- アノテーション対象のバイアスを抑えるため、以下の基準を主としました。
  - 文字数
  - 「参考になった」スコア
  - 対象ゲームの人気度
  - ゲームのジャンル / カテゴリ

本データセットにはレビューを特徴づける 8 つのアスペクトがあります。アノテータは 1 名です。暗黙的な言及（例: キャラクターが魅力的だと良い 等）や、欠如の言及（例: ストーリーが本質的に無い 等）も、そのアスペクトが含まれると見なします。

> 8 アスペクトの説明と例

| アスペクト | 短い説明 | レビューテキスト例 |
| --- | --- | --- |
| Recommended | レビュワーがゲームを推奨するかどうか（レビュー投稿者自身の判断に基づく）。 | ... In conclusion, good game |
| Story | 物語、キャラクター、設定、世界観構築などストーリーテリング要素。 | Excellent game, but has an awful-abrupt ending that comes out of nowhere and doesnt make sense ... |
| Gameplay | 操作性、メカニクス、インタラクティブ性、難易度などゲームプレイ上の要素。 | Gone are the days of mindless building and fun. Power grids? Taxes? Intense accounting and counter-intuitive path building ... |
| Visual | 美術性、アートスタイル、アニメーション、視覚効果など視覚要素。 | Gorgeous graphics + 80s/90s anime artstyle + Spooky + Atmospheric ... |
| Audio | サウンドデザイン、音楽、ボイスアクトなど聴覚要素。 | ... catchy music, wonderful narrator saying very kind words ... |
| Technical | バグ、パフォーマンス、OS/コントローラ対応など技術的側面。 | bad doesnt fit a 1080p monitor u bastard ... |
| Price | ゲーム本体や追加コンテンツの価格に関する要素。 | Devs are on meth pricing this game at $44 |
| Suggestion | 価格やパブリッシャーの提携など、ゲームの状態に関する提案・要望。 | ... but needs a bit of personal effort to optimize the controls for PC, otherwise ... |

注意: 一部のレビューには不快・差別的・不適切と感じられる表現が含まれる場合があります。これらの表現を支持・容認・推奨する意図は一切ありません。

## データ形式

利便性のため、CSV / JSON / Apache Arrow 形式が提供されています。`example` ディレクトリのノートブックで最小例を確認できます。レビュー本文は生テキストとクリーニング後テキストの両方が含まれ、クリーニングでは BBCode の除去、過剰な空白や改行の正規化が行われています。

## モデル・ベンチマーク

詳細は `./model_benchmark/README.md` を参照してください。

## ダウンロード

以下から取得できます（GitHub のほか、ミラー配布先もあり）。

- Hugging Face: https://huggingface.co/datasets/ilos-vigil/steam-review-aspect-dataset
- Kaggle: https://www.kaggle.com/datasets/ilosvigil/steam-review-aspect-dataset

# 引用

研究/プロジェクトで利用する場合は、次のブログ記事を引用してください: https://srec.ai/blog/steam-review-aspect-dataset

```
Sandy Khosasi. "Steam review aspect dataset". (2024).
```

```bibtex
@misc{srec:steam-review-aspect-dataset,
	title        = {Steam review aspect dataset},
	author       = {Sandy Khosasi},
	year         = {2024},
	month        = {may},
	day          = {29},
	url          = {https://srec.ai/blog/steam-review-aspect-dataset},
    urldate      = {2024-05-29}
}
```

# ライセンス

本データセットは Creative Commons Attribution 4.0 International（https://creativecommons.org/licenses/by/4.0）で提供されています。

## 統計

> 各アスペクトの件数

| アスペクト | Train | Test |
| --- | ---:| ---:|
| Recommended | 667 | 148 |
| Story | 400 | 89 |
| Gameplay | 693 | 154 |
| Visual | 391 | 87 |
| Audio | 227 | 51 |
| Technical | 259 | 57 |
| Price | 213 | 47 |
| Suggestion | 97 | 21 |

> 1レビューあたりのアスペクト数

| 総アスペクト数 | Train | Test |
| --- | ---:| ---:|
| 0 | 1 | 7 |
| 1 | 88 | 11 |
| 2 | 214 | 43 |
| 3 | 218 | 55 |
| 4 | 184 | 49 |
| 5 | 140 | 21 |
| 6 | 46 | 8 |
| 7 | 7 | 5 |
| 8 | 2 | 1 |

> ゲームごとのレビュー数

| ゲームごとのレビュー数 | Train | Test |
| --- | ---:| ---:|
| 1 | 280 | 164 |
| 2 | 301 | 18 |
| 3 | 6 | 0 |

> 文字数統計

|  | Train (review) | Train (cleaned review) | Test (review) | Test (cleaned review) |
| --- | ---:| ---:| ---:| ---:|
| Q1 | 417 | 416.75 | 390 | 390 |
| Q2（中央値） | 871 | 867.5 | 888 | 888 |
| Q3 | 1810.5 | 1753.75 | 1629.75 | 1623.5 |
| 平均 | 1408.49 | 1389.06 | 1286.12 | 1267.96 |
