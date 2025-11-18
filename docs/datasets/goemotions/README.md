# GoEmotions データセット

GoEmotionsは、Redditコメントから収集された細粒度感情分類データセットです。28の感情カテゴリ（27感情 + neutral）でラベル付けされています。

- Kaggle: https://www.kaggle.com/datasets/debarshichanda/goemotions
- 元論文: Demszky et al. (2020) "GoEmotions: A Dataset of Fine-Grained Emotions"

## 概要

- 本データセットは、Redditのコメントから収集された感情分類用のデータセットです。
- 各テキストは1つ以上の感情ラベルを持つマルチラベル形式です。
- 本プロジェクトでは、感情を「アスペクト」として扱い、対比因子生成実験に使用します。

## アスペクト（28感情カテゴリ）

本データセットでは、以下の28の感情カテゴリが利用可能です：

- admiration（称賛）
- amusement（面白さ）
- anger（怒り）
- annoyance（いらだち）
- approval（承認）
- caring（思いやり）
- confusion（混乱）
- curiosity（好奇心）
- desire（欲望）
- disappointment（失望）
- disapproval（不承認）
- disgust（嫌悪）
- embarrassment（恥ずかしさ）
- excitement（興奮）
- fear（恐怖）
- gratitude（感謝）
- grief（悲嘆）
- joy（喜び）
- love（愛）
- nervousness（神経質）
- optimism（楽観）
- pride（誇り）
- realization（気づき）
- relief（安堵）
- remorse（後悔）
- sadness（悲しみ）
- surprise（驚き）
- neutral（中立）

## データ形式と利用方法

### アスペクト説明文（テキスト比較用）

本リポジトリのセンテンス比較（BERT）では、アスペクト名の代わりに「短い説明文」を用います。
- 正規 CSV（英語説明文）: `data/analysis-workspace/aspect_descriptions/goemotions/descriptions_official.csv`
  
  - 列構成: `aspect,description`
  - 例:
    - joy → "Feeling of great happiness, delight, or pleasure."
    - anger → "Strong feeling of displeasure, hostility, or rage towards someone or something."
    - neutral → "No particular emotion, feeling, or sentiment expressed."

### 実行時の選択

- 対話スクリプトで「正解アスペクトの表現モード」を「センテンス（公式）」にすると、上記 CSV が優先されます。
- 「センテンス（任意の CSV）」を選ぶと `data/analysis-workspace/aspect_descriptions/goemotions/` 配下から手動選択できます。

### 基本的な使い方

```python
from src.analysis.experiments.utils.datasetManager.dataset_manager import DatasetManager

manager = DatasetManager()
records = manager.load_dataset('goemotions')
```

### データセット情報

- **総レコード数**: 63,812件（マルチラベル展開後）
- **感情カテゴリ数**: 28個（27感情 + neutral）
- **ドメイン**: emotions
- **言語**: 英語

### 実験での使用

```python
# データセットの分割
split_result = manager.split_dataset(
    dataset_id='goemotions',
    aspect='joy',  # 任意の感情アスペクトを指定
    group_size=300,
    split_type='aspect_vs_others'
)

# 結果の構造
# - split_result.group_a: 指定アスペクトのテキストリスト
# - split_result.group_b: その他のアスペクトのテキストリスト
```

### コマンドラインからの実行

```bash
python src/analysis/experiments/2025/10/10/run_experiment.py \
    --dataset goemotions \
    --aspect joy \
    --group-size 300 \
    --split-type aspect_vs_others
```

## データ構造

- **ファイル形式**: TSV（タブ区切り）
- **ファイル構成**: `train.tsv`, `test.tsv`, `dev.tsv`
- **列構成**: `text`, `emotion_id`, `comment_id`
- **マルチラベル**: 1つのテキストが複数の感情IDを持つ場合、カンマ区切りで記録

## ダウンロード/出典

- Kaggle: `https://www.kaggle.com/datasets/debarshichanda/goemotions`
- ダウンロードスクリプト: `src/data/download_goemotions.py`

## 引用

研究/プロジェクトで利用する場合は、以下の論文を引用してください：

```
Dora Demszky, Davide Movshovitz-Attias, Jeongwoo Ko, Alan Cowen, Gaurav Nemade, and Sujith Ravi. "GoEmotions: A Dataset of Fine-Grained Emotions." In Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics (ACL 2020).
```

```bibtex
@inproceedings{demszky2020goemotions,
  title={GoEmotions: A Dataset of Fine-Grained Emotions},
  author={Demszky, Dora and Movshovitz-Attias, Davide and Ko, Jeongwoo and Cowen, Alan and Nemade, Gaurav and Ravi, Sujith},
  booktitle={Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics},
  year={2020}
}
```

## ライセンス/注意

- ライセンス・利用条件はKaggleデータセットページの規約に従ってください。
- 本データセットはRedditコメントから収集されているため、一部のテキストには不快・不適切な表現が含まれる可能性があります。
- 本リポジトリでの利用は、対比因子生成実験のための感情分類タスクとして位置づけられています。

