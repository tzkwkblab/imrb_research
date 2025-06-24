# Steam Review Aspect 対比因子生成実験レポート

**実験日時**: 2025年06月24日 20:54:51  
**データセット**: Steam Review Aspect Dataset  
**総実験数**: 24回  

---

## 📋 実験概要

### 実験設計
- **アスペクト数**: 8種類
- **Few-shot設定**: 0, 1, 3
- **各グループサイズ**: 300レビュー
- **総実験回数**: 8 × 3 = 24回

### 対象アスペクト
recommended, story, gameplay, visual, audio, technical, price, suggestion

---

## 📊 総合結果

| 評価指標 | 平均スコア |
|----------|------------|
| **BERTスコア** | 0.6722 |
| **BLEUスコア** | 0.0140 |

---

## 📈 詳細結果

| アスペクト | Shot | BERTスコア | BLEUスコア | GPT応答 |
|------------|------|------------|------------|---------|
| recommended | 0 | 0.5737 | 0.0000 | "Group A reviews express satisfaction and recommen... |
| recommended | 1 | 0.6000 | 0.0000 | "Group A reviews explicitly recommend the game."... |
| recommended | 3 | 0.5772 | 0.0000 | "Group A reviews focus on gameplay elements and ex... |
| story | 0 | 0.5990 | 0.0240 | "Group A reviews focus on story and gameplay aspec... |
| story | 1 | 0.6053 | 0.0408 | "Group A reviews discuss story elements"... |
| story | 3 | 0.5842 | 0.0240 | "Group A discusses story elements, Group B does no... |
| gameplay | 0 | 0.6683 | 0.0132 | "Group A reviews focus on gameplay mechanics and p... |
| gameplay | 1 | 0.6971 | 0.0211 | "Group A focuses on gameplay specifics, Group B do... |
| gameplay | 3 | 0.6666 | 0.0115 | "Group A reviews focus on gameplay mechanics, perf... |
| visual | 0 | 0.7046 | 0.0000 | "Specific mentions of graphics quality and control... |
| visual | 1 | 0.7435 | 0.0000 | "Specific mentions of graphics quality and visuals... |
| visual | 3 | 0.7703 | 0.0000 | "Specific mentions of graphics and visuals"... |
| audio | 0 | 0.7766 | 0.0330 | "Specific mentions of audio quality and music"... |
| audio | 1 | 0.7766 | 0.0330 | "Specific mentions of audio quality and music"... |
| audio | 3 | 0.7508 | 0.0278 | "Group A reviews specifically mention audio and mu... |
| technical | 0 | 0.6094 | 0.0000 | "Direct mentions of bugs and glitches"... |
| technical | 1 | 0.7078 | 0.0330 | "Specific mentions of technical issues and bugs"... |
| technical | 3 | 0.6030 | 0.0000 | "Specific mentions of bugs and glitches"... |
| price | 0 | 0.6911 | 0.0408 | "Explicit mention of game's price value"... |
| price | 1 | 0.6062 | 0.0000 | "Group A discusses cost-value relation, Group B do... |
| price | 3 | 0.6819 | 0.0330 | "Explicit mentions of game price or cost"... |
| suggestion | 0 | 0.7089 | 0.0000 | "Direct suggestions for game improvements"... |
| suggestion | 1 | 0.7156 | 0.0000 | "Specific suggestions for game improvements"... |
| suggestion | 3 | 0.7156 | 0.0000 | "Specific suggestions for game improvements"... |

---

## 🔍 分析結果

### アスペクト別平均スコア
- **audio**: BERT=0.7680, BLEU=0.0313
- **gameplay**: BERT=0.6773, BLEU=0.0153
- **price**: BERT=0.6597, BLEU=0.0246
- **recommended**: BERT=0.5836, BLEU=0.0000
- **story**: BERT=0.5962, BLEU=0.0296
- **suggestion**: BERT=0.7134, BLEU=0.0000
- **technical**: BERT=0.6401, BLEU=0.0110
- **visual**: BERT=0.7395, BLEU=0.0000

### Shot設定別平均スコア
- **0-shot**: BERT=0.6665, BLEU=0.0139
- **1-shot**: BERT=0.6815, BLEU=0.0160
- **3-shot**: BERT=0.6687, BLEU=0.0120

---

## 💡 考察

- 総実験数24回中、すべての実験でGPT応答を取得
- BERTスコア平均0.6722は意味的類似度を示す
- BLEUスコア平均0.0140は語彙的一致度を示す

---

**実験完了時刻**: 2025-06-24T20:54:51.199928
