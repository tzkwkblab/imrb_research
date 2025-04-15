# AI同士の言語創発実験における説明可能性の研究

## 研究概要

我々は、AI同士の言語創発実験において創発する（新たな言語の）メッセージの意味を、人間の言葉へと翻訳することで、説明可能AIを構築するというアプローチについて研究している。

### 具体的な研究例
商品レビューのテキストから、そのレビューの評価点（星の数）を予測する説明可能AIモデルを構築する場合：
1. 商品レビューを入力すると、送信者モデルはいくつかのメッセージを受信者モデルに送る
2. 受信者モデルはそのメッセージに基づいて評価点を予測する
3. 各メッセージの意味を人間の言葉で記述する（例：「このテキストは価格が高いという旨の内容を含んでいる」）

## 実験目的
二つのレビュー集合の特徴の違いを見つけるAIモデルを構築して、レビュー集合Aにあってレビュー集合Bにはない特徴を、AIがちゃんと説明できるか検証する。

## 環境設定

### 必要条件
- Python 3.9以上
- OpenAI API キー

### 依存パッケージ
```bash
pip install -r requirements.txt
```

主要な依存関係：
- openai==1.53.0
- pandas==2.2.1
- python-dotenv==1.0.1

### 環境変数の設定
`.env`ファイルを作成し、以下の内容を設定：
```
OPENAI_API_KEY=your_api_key_here
```

## 再現手順

### 1. データ準備
#### 1.1 特徴定義の作成
- 場所: `src/data/features/definitions/review_features.csv`
- フォーマット: CSV（feature_id, feature_description）
- 作成方法: 手動で20個の特徴を定義

#### 1.2 レビューデータの収集
```bash
python src/data/collect.py
```

### 2. 特徴分析
#### 2.1 レビュー特徴の抽出
```bash
python src/analysis/review_feature_analyzer.py
```
- 入力: レビューテキスト
- 出力: 20個の特徴の有無（1/0）と判定理由

### 3. 評価指標

#### 3.1 特徴抽出の精度(仮)
人間の評価者による判定との一致率を使用
```python
accuracy = (正しく判定された特徴数) / (全特徴数)
```

#### 3.2 説明の質的評価
- 説明の具体性
- 引用部分の適切性
- 理由の妥当性

## プロジェクト構造
```
.
├── README.md
├── requirements.txt
├── notebooks/
│   └── data_visualization.ipynb
└── src/
    ├── analysis/
    │   └── review_feature_analyzer.py
    └── data/
        ├── collect.py
        ├── features.py
        └── features/
            └── definitions/
                ├── review_features.csv
                └── review_features.txt
```

## 研究者情報
- 氏名：清野駿
- 所属：筑波大学大学院 人間総合科学学術院 人間総合科学研究群 情報学学位プログラム 博士前期課程2年
- 学生番号：202421675

## 注意事項
- OpenAI APIの利用には課金が発生する可能性があります
- 大量のAPIリクエストを行う場合は、レート制限に注意してください