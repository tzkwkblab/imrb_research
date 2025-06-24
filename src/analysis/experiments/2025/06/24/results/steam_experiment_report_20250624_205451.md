# Steam Review Aspect 対比因子生成実験レポート

**実験日時**: 2025 年 06 月 24 日 20:54:51  
**データセット**: Steam Review Aspect Dataset  
**総実験数**: 24 回

---

## 📋 実験概要

### 実験設計

- **アスペクト数**: 8 種類
- **Few-shot 設定**: 0, 1, 3
- **各グループサイズ**: 300 レビュー
- **総実験回数**: 8 × 3 = 24 回

### 対象アスペクト

recommended, story, gameplay, visual, audio, technical, price, suggestion

---

## 📊 総合結果

| 評価指標        | 平均スコア |
| --------------- | ---------- |
| **BERT スコア** | 0.6722     |
| **BLEU スコア** | 0.0140     |

---

## 📈 詳細結果

| アスペクト  | Shot | BERT スコア | BLEU スコア | GPT 応答（完全版）                                                                                                                   |
| ----------- | ---- | ----------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| recommended | 0    | 0.5737      | 0.0000      | "Group A reviews express satisfaction and recommendation, Group B reviews do not."                                                   |
| recommended | 1    | 0.6000      | 0.0000      | "Group A reviews explicitly recommend the game."                                                                                     |
| recommended | 3    | 0.5772      | 0.0000      | "Group A reviews focus on gameplay elements and experiences, while Group B reviews are more about personal opinions and criticisms." |
| story       | 0    | 0.5990      | 0.0240      | "Group A reviews focus on story and gameplay aspects."                                                                               |
| story       | 1    | 0.6053      | 0.0408      | "Group A reviews discuss story elements"                                                                                             |
| story       | 3    | 0.5842      | 0.0240      | "Group A discusses story elements, Group B does not."                                                                                |
| gameplay    | 0    | 0.6683      | 0.0132      | "Group A reviews focus on gameplay mechanics and performance, while Group B reviews do not."                                         |
| gameplay    | 1    | 0.6971      | 0.0211      | "Group A focuses on gameplay specifics, Group B does not."                                                                           |
| gameplay    | 3    | 0.6666      | 0.0115      | "Group A reviews focus on gameplay mechanics, performance, and system requirements, while Group B reviews do not."                   |
| visual      | 0    | 0.7046      | 0.0000      | "Specific mentions of graphics quality and controls"                                                                                 |
| visual      | 1    | 0.7435      | 0.0000      | "Specific mentions of graphics quality and visuals"                                                                                  |
| visual      | 3    | 0.7703      | 0.0000      | "Specific mentions of graphics and visuals"                                                                                          |
| audio       | 0    | 0.7766      | 0.0330      | "Specific mentions of audio quality and music"                                                                                       |
| audio       | 1    | 0.7766      | 0.0330      | "Specific mentions of audio quality and music"                                                                                       |
| audio       | 3    | 0.7508      | 0.0278      | "Group A reviews specifically mention audio and music."                                                                              |
| technical   | 0    | 0.6094      | 0.0000      | "Direct mentions of bugs and glitches"                                                                                               |
| technical   | 1    | 0.7078      | 0.0330      | "Specific mentions of technical issues and bugs"                                                                                     |
| technical   | 3    | 0.6030      | 0.0000      | "Specific mentions of bugs and glitches"                                                                                             |
| price       | 0    | 0.6911      | 0.0408      | "Explicit mention of game's price value"                                                                                             |
| price       | 1    | 0.6062      | 0.0000      | "Group A discusses cost-value relation, Group B doesn't."                                                                            |
| price       | 3    | 0.6819      | 0.0330      | "Explicit mentions of game price or cost"                                                                                            |
| suggestion  | 0    | 0.7089      | 0.0000      | "Direct suggestions for game improvements"                                                                                           |
| suggestion  | 1    | 0.7156      | 0.0000      | "Specific suggestions for game improvements"                                                                                         |
| suggestion  | 3    | 0.7156      | 0.0000      | "Specific suggestions for game improvements"                                                                                         |

---

## 🔍 分析結果

### アスペクト別平均スコア

- **audio**: BERT=0.7680, BLEU=0.0313
- **visual**: BERT=0.7395, BLEU=0.0000
- **suggestion**: BERT=0.7134, BLEU=0.0000
- **gameplay**: BERT=0.6773, BLEU=0.0153
- **price**: BERT=0.6597, BLEU=0.0246
- **technical**: BERT=0.6401, BLEU=0.0110
- **story**: BERT=0.5962, BLEU=0.0296
- **recommended**: BERT=0.5836, BLEU=0.0000

### Shot 設定別平均スコア

- **0-shot**: BERT=0.6665, BLEU=0.0139
- **1-shot**: BERT=0.6815, BLEU=0.0160
- **3-shot**: BERT=0.6687, BLEU=0.0120

---

## 🎯 主要な発見

### 高性能アスペクト（BERT > 0.70）

1. **audio（0.7680）**: 音質・音楽関連の専門用語が識別しやすい
2. **visual（0.7395）**: グラフィック品質への言及が明確
3. **suggestion（0.7134）**: 改善提案の文脈パターンが一貫

### 中性能アスペクト（0.60 ≤ BERT < 0.70）

4. **gameplay（0.6773）**: ゲームメカニクスの詳細説明
5. **price（0.6597）**: 価格言及の直接的表現を検出
6. **technical（0.6401）**: バグ・不具合関連の用語識別

### 低性能アスペクト（BERT < 0.60）

7. **story（0.5962）**: ストーリー要素の抽象性により識別困難
8. **recommended（0.5836）**: 推薦意図の暗黙的表現が多く最も困難

### Few-shot 学習効果

- **1-shot が最適**: 0.6815 で最高性能を達成
- **3-shot で性能低下**: 過学習の可能性を示唆
- **適切な例題数**: アスペクト識別には 1 例が最適

---

## 💡 考察

### 実験成功率

- 総実験数 24 回中、すべてで GPT 応答を取得（100%成功率）
- データ準備：8 アスペクトすべてで十分なデータ量確保

### 評価指標の解釈

- **BERT スコア平均 0.6722**: 意味的類似度として良好
- **BLEU スコア平均 0.0140**: 語彙的一致度は低めだが、創造的説明を反映

### アスペクト特性

- **客観的要素**（audio, visual）: 高い識別精度
- **主観的要素**（story, recommended）: 識別困難
- **技術的要素**（technical, gameplay）: 中程度の性能

---

**実験完了時刻**: 2025-06-24T20:54:51.199928
**次回実験への示唆**: 1-shot 学習を標準とし、低性能アスペクトの手法改善が必要
