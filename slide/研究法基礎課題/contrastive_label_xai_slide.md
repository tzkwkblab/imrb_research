---
marp: true
theme: default
auto-scaling: true
paginate: true
--------------

<style>
table {
  font-size: 1.2em;
  margin: 20px auto;
}
th, td {
  padding: 12px 20px;
}
.center {
  text-align: center;
}
.large-text {
  font-size: 1.3em;
  line-height: 1.5;
}
</style>

# 説明可能AIのための対比因子ラベル生成手法

清野駿（筑波大学大学院 修士2年）

---

# 背景

---

<div class="large-text">

## 説明可能 AI（XAI）の必要性

- AI の意思決定プロセスを人間が理解したい
- 医療、金融などの重要な判断での透明性確保

</div>

---

# AI は思考過程は説明できない

![](./images/病名診断AI.png)

---

# 課題

<div style="display: flex; align-items: center; gap: 50px; margin: 40px 0;">

<div style="flex: 1;">

<div class="large-text">

**既存手法の限界**

- 専門家が AI の判断理由を手動で定義
  - 例：「過去の食事データから、アレルギーだと判断した」
- 新しいデータドメインごとに判断理由を作り直す必要がある
- **スケーラビリティの問題**

</div>

</div>

<div style="flex: 1; text-align: center;">

![](./images/専門家定義.png)

</div>

</div>

---

# 目的

<div class="large-text center">

**LLM による対比因子自動生成の実現可能性を定量的に検証**

「グループ A に特徴的でグループ B には見られないテキスト的傾向」を LLM が正確に説明できるか？

</div>

---

# アプローチ

<div class="large-text">

1. GPT にグループ A/B のレビュー集合を入力
2. GPT がグループ A の特徴的差異を自然言語で記述
3. 出力の妥当性を BERT/BLEU スコアで定量評価

</div>

---

# 実験設定

<div class="large-text center">

**データ**: SemEval（レストラン）、Steam（ゲーム）

**条件**: 各グループ 300 件、0/1/3-shot、GPT-4o-mini

</div>

---

# 実験結果: データセット比較

<div class="center">

| データセット | BERT スコア |
| ------------ | ----------- |
| SemEval      | 0.718       |
| Steam        | 0.672       |

</div>

---

# 実験結果: Few-shot 効果

<div class="center">

| Shot 数 | BERT スコア |
| ------- | ----------- |
| 0       | 0.606       |
| 1       | 0.730       |
| 3       | 0.708       |

**1-shot 効果が顕著（20%向上）**

</div>

---

# 貢献

<div class="large-text">

- LLM 対比因子生成の可能性と限界を定量評価
- Few-shot 効果（特に 1-shot）を実証
- 異ジャンルでの再現性確認

</div>

---

# 今後の課題

<div class="large-text">

- 人手評価の導入
- より抽象的概念への対応
- 実用的 XAI システムへの統合

</div>
