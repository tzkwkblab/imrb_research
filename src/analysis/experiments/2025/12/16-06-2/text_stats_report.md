# データセットテキスト統計集計（GoEmotions / Steam / SemEval）

- 実行スクリプト: `text_stats_multi_dataset.py`
- 出力: 標準出力の Markdown 表と `results/text_stats_summary_YYYYMMDD_HHMMSS.json`
- トークン化定義: `text.lower().split()`（句読点除去なし，TTR は types/tokens）
- ラベル語数: `label.lower().split()` の語数（GoEmotions は ID を emotions.txt で名称に変換）

## 入力ファイル（読み取りのみ）
- GoEmotions: `data/external/goemotions/kaggle-debarshichanda/current/data/{train,dev,test}.tsv`
- Steam: `data/external/steam-review-aspect-dataset/current/{train,test}.csv` （本文は `cleaned_review` 優先、空なら `review`）
- SemEval-2014: `data/external/absa-review-dataset/pyabsa-integrated/current/ABSADatasets/datasets/apc_datasets/110.SemEval/{113.laptop14,114.restaurant14}/{train,test}.xml.seg` （3行ブロック: 0行目=本文，1行目=アスペクト）

## 集計結果（train/dev/test 合算）
|dataset|n_samples|mean_words|median_words|max_words|vocab_types|ttr|mean_labels_per_sample|pct_multi_label|ref_label_median_words|
|---|---|---|---|---|---|---|---|---|---|
|GoEmotions|54263|12.83|12.00|33|57862|0.0831|1.18|16.25%|1.00|
|Steam Review Aspect|1100|244.70|156.00|1473|29056|0.1079|3.27|90.27%|1.00|
|SemEval-2014 laptop14|2966|20.75|18.00|83|3432|0.0558|1.00|0.00%|1.00|
|SemEval-2014 restaurant14|4728|19.41|18.00|79|4381|0.0478|1.00|0.00%|1.00|

## LLM評価設定（論文 `04_experiment.tex` より）
- 評価器: GPT-4o-mini（モデル比較時のみ GPT-4o）、temperature=0.0、5段階評価→(score-1)/4で正規化
- 評価回数: 参照・候補ペアあたり1回（single pass）




