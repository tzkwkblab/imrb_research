---
marp: true
theme: default
auto-scaling: true
paginate: false
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

## AI は

## 思考過程は

## 説明できない

![bg right:70%](./images/病名診断AI.png)

---

<div class="large-text">

## 説明可能 AI（XAI）の必要性

- AI の意思決定プロセスを人間が理解したい
- 医療、金融などの重要な判断での透明性確保

## </div>

---

## 課題：手動で判断理由をラベリング

【現状】専門家が AI の判断理由を手動で定義

- 例：「過去の食事データから、アレルギーだと判断した」

### 新しいデータドメインごとに、判断理由の再ラベリングが必要

![bg right:40%](./images/専門家定義.png)

---

# 目的

<div class="large-text center">

**LLM による判断理由自動生成の実現可能性を定量的に検証**

「グループ A に特徴的でグループ B には見られないテキスト的傾向（対比因子）」を LLM が正確に説明できるか？

</div>

---

# 手法

### 1. LLM にグループ A/B のレビュー集合を入力

- A：価格に言及してるレビュー、B：価格に言及してないレビュー

### 2. LLM がグループ A の特徴的差異を自然言語で記述

- "A は値段について喋っている"

---

```
以下の2つのデータグループを比較して、グループAに特徴的で
グループBには見られない表現パターンや内容の特徴を特定してください。
{examples_section}

【グループA】
{group_a_text}

【グループB】
{group_b_text}

{output_language}で{word_count}程度で、
グループAに特徴的でグループBには見られな主要な違いを簡潔に回答してください。
```

- **例示**：`{examples_section}`で、例題を提示する

  - `【例題】グループ A：〜〜〜　グループ B：〜〜〜　正解：ラベル X`

- `{output_language}`と`{word_count}`で言語・文字数を指定

---

# 実験設定

<div class="large-text">

**データセット**

- SemEval（レストランデータセット）、
- Steam（ゲームデータセット）

**実験の条件**

- 各グループ 300 件
- 0/1/3-shot
- GPT-4o-mini

</div>

---

# 結果・結論

## 結果

- 対比因子を適切に抽出することに成功
- 例題を提示することで、20%ほどスコアが向上

## 結論

- **LLM による対比因子生成の実現可能性を確認**
- 人間にとっても納得感のある出力を得られることがわかった
- **限界**：抽象的・概念的な答え（提案、推薦など）が正解のタスクでは抽出困難
