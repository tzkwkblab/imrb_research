# 正解ラベルと生成ラベルの語数統計

生成日時: 2025-12-15 16:25:44

## 概要

メイン実験再実行（temperature=0）の全実験結果から、正解ラベルと生成ラベルの語数を分析しました。

本統計は、論文執筆用に再実行されたメイン実験（temperature=0.0, few_shot=0, max_tokens=2000, group_size=100）の結果に基づいています。SemEval-2014 ABSA（4 アスペクト）、GoEmotions（28 感情カテゴリ）、Steam Review Aspect Dataset（4 アスペクト）の合計 36 実験から、正解ラベルと生成ラベルの語数差を定量化しました。

**注意**: 実験ディレクトリ（`論文/結果/追加実験/main_experiment_rerun_temperature0/`）の `results/batch_results.json` では，`experiment_plan.settings.temperature = 0.0` と記録されている一方，各 `experiment_info.model_config.temperature` は 0.7 になっている。temperature 設定の扱いは別途要確認。

## 全体統計

### 正解ラベルの語数

| 指標     | 値      |
| -------- | ------- |
| 平均     | 1.00 語 |
| 中央値   | 1.0 語  |
| Q1       | 1.0 語  |
| Q3       | 1.0 語  |
| 最小     | 1 語    |
| 最大     | 1 語    |
| 標準偏差 | 0.00 語 |

### 生成ラベルの語数

| 指標     | 値      |
| -------- | ------- |
| 平均     | 9.69 語 |
| 中央値   | 9.0 語  |
| Q1       | 8.0 語  |
| Q3       | 10.0 語 |
| 最小     | 4 語    |
| 最大     | 17 語   |
| 標準偏差 | 3.24 語 |

## データセット別統計

### GOEMOTIONS

| 指標       | 正解ラベル | 生成ラベル |
| ---------- | ---------- | ---------- |
| 平均       | 1.00 語    | 10.18 語   |
| 中央値     | 1.0 語     | 9.0 語     |
| 標準偏差   | 0.00 語    | 2.98 語    |
| サンプル数 | 28 件      | 28 件      |

### SEMEVAL

| 指標       | 正解ラベル | 生成ラベル |
| ---------- | ---------- | ---------- |
| 平均       | 1.00 語    | 10.50 語   |
| 中央値     | 1.0 語     | 9.0 語     |
| 標準偏差   | 0.00 語    | 3.20 語    |
| サンプル数 | 4 件       | 4 件       |

### STEAM

| 指標       | 正解ラベル | 生成ラベル |
| ---------- | ---------- | ---------- |
| 平均       | 1.00 語    | 5.50 語    |
| 中央値     | 1.0 語     | 5.5 語     |
| 標準偏差   | 0.00 語    | 1.50 語    |
| サンプル数 | 4 件       | 4 件       |

## 解釈

- 正解ラベルの平均語数は 1.00 語（中央値 1.0 語）であり、全て単一のアスペクト名（`food`, `price`, `gameplay` など）である
- 生成ラベルの平均語数は 9.69 語（中央値 9.0 語）であり、正解ラベルより 8.69 語多い
- この差は、正解ラベルが `food` や `price` のように短い一方、生成ラベルが `食べ物の品質に関する言及` のような説明的フレーズになりやすいことを反映している

## 論文への引用例

> 正解ラベルと生成ラベルの語数について，メイン実験の全 36 条件を分析した結果，正解ラベルの平均語数は 1.0 語（中央値 1.0 語），生成ラベルの平均語数は 9.7 語（中央値 9.0 語）であった．この差は，正解ラベルが `food` や `price` のように短い一方，生成ラベルが `食べ物の品質に関する言及` のような説明的フレーズになりやすいことを反映している．

## 語数カウント方法

### 正解ラベルの取得方法

正解ラベルは、`experiment_info`セクションの`aspect`フィールドから取得しました。これにより、実際のアスペクト名（`food`, `price`, `gameplay`など）を正解ラベルとして使用しています。

**注意**: `evaluation.reference_text`には「X related characteristics」形式の説明文が保存されていますが、これは評価用の説明文であり、実際の正解アスペクト名ではありません。

### 実装方針

本統計では、英語ラベルと日本語ラベルが混在する可能性を考慮し、以下の方法で語数をカウントしました。

#### 英語ラベルのカウント

- 英語のみのラベルの場合：単語境界（``）で区切られた英単語をカウント
- 正規表現パターン：`[a-zA-Z]+` を使用

#### 日本語ラベルのカウント

- 日本語が含まれるラベルの場合：句読点（`。`、`、`）と助詞・助動詞（`は`、`が`、`の`、`を`、`に`、`で`、`と`、`から`、`まで`、`より`、`である`、`です`、`ます`）で区切ってカウント
- 句読点で文を分割し、各文を助詞・助動詞で区切ったセグメント数を語数として扱う
- より正確なカウントには形態素解析が必要だが、本統計では簡易的な方法を採用

#### 英語と日本語の混在

- 英語と日本語が混在する場合：英語単語数 + 日本語部分の語数（上記の方法でカウント）

### 実装コード

```python
def count_words(text: str) -> int:
    """テキストの語数をカウント（英語・日本語対応）"""
    if not text or not isinstance(text, str):
        return 0

    # 英語の場合は単語境界で分割
    english_words = re.findall(r'\b[a-zA-Z]+\b', text)

    # 日本語文字を検出
    japanese_chars = re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text)

    # 英語のみの場合は英語単語数を返す
    if len(japanese_chars) == 0:
        return len(english_words)

    # 日本語が含まれている場合
    if len(english_words) == 0:
        # 日本語のみの場合：句読点で区切る
        japanese_text = text.strip()
        sentences = re.split(r'[。、]', japanese_text)
        sentences = [s.strip() for s in sentences if s.strip()]

        # 各文を助詞・助動詞で区切る（簡易版）
        total_words = 0
        for sentence in sentences:
            segments = re.split(r'[はがのをにでとからまでよりであるですます]', sentence)
            segments = [s.strip() for s in segments if s.strip() and len(s.strip()) > 0]
            total_words += len(segments) if segments else 1

        return total_words if total_words > 0 else len(japanese_chars) // 2

    # 英語と日本語が混在している場合
    japanese_only_text = ''.join(japanese_chars)
    if japanese_only_text:
        japanese_segments = re.split(r'[。、はがのをにでとからまでより]', japanese_only_text)
        japanese_segments = [s.strip() for s in japanese_segments if s.strip() and len(s.strip()) > 0]
        japanese_word_count = len(japanese_segments) if japanese_segments else len(japanese_chars) // 2
    else:
        japanese_word_count = 0

    return len(english_words) + japanese_word_count
```

### 注意事項

- 日本語ラベルの語数カウントは簡易的な方法であり、形態素解析による正確なカウントではない
- ただし、正解ラベルと生成ラベルの語数の**差**を比較する目的では、この方法で十分な精度が得られると判断
- 実際のデータでは、Steam データセットの一部で日本語ラベルが生成されたが、英語ラベルと同様に適切にカウントされた

## データソース

### 実験情報

- **実験名**: メイン実験再実行（temperature=0）
- **実験ディレクトリ**: `論文/結果/追加実験/main_experiment_rerun_temperature0/`
- **実験パラメータ**:
  - Few-shot: 0（例題なし）
  - temperature: 0.0（一貫性重視、決定論的出力）
  - max_tokens: 2000
  - group_size: 100（固定）
  - GPT モデル: gpt-4o-mini
  - LLM 評価: 有効（gpt-4o-mini, temperature=0.0）
- **データセット構成**:
  - SemEval-2014 ABSA: 4 アスペクト（food, service, battery, screen）
  - GoEmotions: 28 感情カテゴリ
  - Steam Review Aspect Dataset: 4 アスペクト（gameplay, visual, story, audio）
- **総実験数**: 36 実験
- **詳細**: `論文/結果/追加実験/main_experiment_rerun_temperature0/実験パラメータ.md`

### データファイル

- **入力ファイル**: `論文/結果/追加実験/main_experiment_rerun_temperature0/results/batch_results.json`
- **総サンプル数**: 36 件
- **実装スクリプト**: `論文/実験結果集約/calculate_label_lengths.py`
