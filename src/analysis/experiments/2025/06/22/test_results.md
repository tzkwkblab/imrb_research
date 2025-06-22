# 一連の流れ統合テスト結果

## テスト概要

対比因子抽出の完全な処理フロー：
1. **プロンプト生成** (prompt_contrast_factor.py)
2. **GPT問い合わせ** (LLM共通処理)
3. **類似度スコア計算** (get_score.py)

## テスト結果

### 0-shot テスト

| 項目 | 値 |
|------|-----|
| **テストデータ** | |
| グループA | "Great battery life lasting all day", "Excellent power management features", "Long-lasting battery performance" |
| グループB | "Poor screen quality and resolution", "Uncomfortable keyboard layout", "Slow system performance issues" |
| 期待する回答 | "Battery life and power management" |
| **プロンプト** | |
| プロンプト長 | 354文字 |
| モデル設定 | gpt-4o-mini, temperature=0.7, max_tokens=100 |
| **GPT応答** | |
| 実際の回答 | "Positive performance and features related to battery." |
| **評価スコア** | |
| BERTスコア | 0.8099 |
| BLEUスコア | 0.0330 |

### Few-shot テスト (1-shot)

| 項目 | 値 |
|------|-----|
| **例題** | |
| 例題数 | 1件 |
| 例題内容 | A: ["Fast delivery", "Quick shipping"], B: ["Slow response", "Delayed support"] → "Delivery and shipping speed" |
| **テストデータ** | |
| グループA | ["High-quality materials", "Durable construction"] |
| グループB | ["Cheap plastic", "Fragile design"] |
| 期待する回答 | "Material quality and durability" |
| **GPT応答** | |
| 実際の回答 | "Use of high-quality and durable materials" |
| **評価スコア** | |
| BERTスコア | 0.9105 |
| BLEUスコア | 0.0408 |

### 比較結果

| 手法 | BERTスコア | BLEUスコア | 改善率（BERT） |
|------|------------|------------|----------------|
| 0-shot | 0.8099 | 0.0330 | - |
| 1-shot | 0.9105 | 0.0408 | +12.4% |

## 考察

### 成功点
- ✅ **完全な処理フロー**: プロンプト生成→GPT問い合わせ→スコア計算が正常動作
- ✅ **Few-shot効果**: 1-shotでBERTスコアが12.4%向上（0.8099→0.9105）
- ✅ **意味的類似度**: BERTスコアが両方とも0.8以上で高い類似度を達成
- ✅ **モジュール統合**: 各コンポーネントが正常に連携

### 改善点
- 📝 **BLEU低スコア**: 表層的な語彙一致が少ない（0.03-0.04）
- 📝 **応答の冗長性**: GPTが期待より長い回答を生成する傾向

### 技術的検証
- **プロンプト品質**: 354文字の簡潔なプロンプトで効果的な指示
- **モデル性能**: gpt-4o-miniが意味的に適切な回答を生成
- **評価指標**: BERTスコアが意味類似度を適切に測定

## 次のステップ

1. **パラメータ調整**: temperature, max_tokensの最適化
2. **プロンプト改良**: より簡潔な回答を促すプロンプト設計
3. **Few-shot最適化**: 例題数と品質の検証
4. **大規模実験**: SemEval ABSAデータでの本格検証

---
*実行日時: 2025-06-22*  
*モデル: gpt-4o-mini*  
*評価指標: BERTスコア（意味類似度）, BLEUスコア（表層類似度）*