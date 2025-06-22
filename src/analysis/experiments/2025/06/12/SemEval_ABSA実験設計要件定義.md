# SemEval ABSA 実験設計要件定義

**作成日**: 2025 年 6 月 12 日  
**目的**: SemEval ABSA データセットを用いた GPT 対比因子生成実験の実装要件定義  
**実装方針**: 過去実験のスクリプトを参考に新実験システムを構築

---

## 🎯 実験目標

### 主要目的

- **SemEval ABSA データセット**を使用してドメイン別（Restaurant/Laptop）で特徴ベース分割を実行
- **グループ A とグループ B**のレビューを GPT に入力して対比因子を生成・評価
- **Few-shot 学習効果**と**ハルシネーション抑制**を定量的に分析

### 実験条件

- **データサイズ**: 50-200 レビュー/グループ（過去の 3-10 倍規模）
- **ドメイン**: Restaurant、Laptop
- **評価軸**: 正確性、具体性、ハルシネーション、ドメイン適合性
- **Few-shot 設定**: 0-shot、1-shot、3-shot

---

## 📂 参照スクリプトファイル一覧

### 🔧 核心実験スクリプト

#### 1. [`src/analysis/experiments/2025/06/06-2/baseline_gpt_fewshot_cross_validation.py`](src/analysis/experiments/2025/06/06-2/baseline_gpt_fewshot_cross_validation.py)

- **役割**: Few-shot 学習とハルシネーション検証の統合実験システム
- **重要機能**:
  - `create_few_shot_prompt()`: Few-shot 学習用プロンプト生成
  - `create_random_group_prompt()`: ハルシネーション検証用ランダムグループプロンプト
  - `run_hallucination_experiment()`: ハルシネーション検証実験
  - `run_few_shot_analysis()`: Few-shot 設定での対比因子生成実験
- **活用ポイント**: プロンプト設計と GPT 応答評価のベースライン

#### 2. [`src/analysis/experiments/2025/06/09-2/domain_aware_feature_splitter.py`](src/analysis/experiments/2025/06/09-2/domain_aware_feature_splitter.py)

- **役割**: ドメイン別特徴ベースデータ分割システム
- **重要機能**:
  - `discover_domains()`: 利用可能ドメインの自動発見
  - `create_domain_feature_splits()`: ドメイン内特徴ベース分割
  - `analyze_domain_features()`: ドメイン内特徴分析
  - `save_domain_splits_to_files()`: 分割結果の構造化保存
- **活用ポイント**: SemEval ABSA データの前処理とグループ A/B 作成

### 📊 評価・分析スクリプト

#### 3. [`src/analysis/experiments/2025/05/27/similarity_evaluation_results.json`](src/analysis/experiments/2025/05/27/similarity_evaluation_results.json)

- **役割**: BERT 類似度・BLEU 類似度評価結果
- **データ内容**:
  - 190 ペアの特徴組み合わせ評価
  - BERT 平均類似度: 0.619 (±0.065)
  - BLEU 平均類似度: 0.018 (±0.025)
- **活用ポイント**: 評価指標のベースライン値と評価手法

#### 4. [`src/analysis/experiments/2025/06/06-2/Few-shot実験詳細分析.md`](src/analysis/experiments/2025/06/06-2/Few-shot実験詳細分析.md)

- **役割**: Few-shot 学習効果の詳細分析レポート
- **分析内容**:
  - 0-shot〜5-shot の段階的性能変化
  - 特徴別 Few-shot 効果の差異
  - GPT 応答品質の定性分析
- **活用ポイント**: Few-shot 設定の最適化とプロンプト改良

### 🔄 実験管理スクリプト

#### 5. [`src/analysis/experiments/2025/06/06/baseline_gpt_fewshot_cross_validation.py`](src/analysis/experiments/2025/06/06/baseline_gpt_fewshot_cross_validation.py)

- **役割**: クロスバリデーション方式の実験システム
- **重要機能**:
  - `run_cross_validation_analysis()`: k-fold クロスバリデーション
  - `run_comprehensive_analysis()`: 包括的実験管理
  - `print_analysis_summary()`: 実験結果サマリー生成
- **活用ポイント**: 実験の再現性確保と統計的信頼性向上

#### 6. [`src/analysis/experiments/2025/05/20/baseline_gpt.py`](src/analysis/experiments/2025/05/20/baseline_gpt.py)

- **役割**: 初期ベースライン実験システム
- **重要機能**:
  - `load_review_data()`: CSV データ読み込み
  - `extract_review_samples()`: レビューサンプル抽出
  - `query_gpt()`: GPT API 呼び出し
- **活用ポイント**: 基本的な GPT 実験フローの参考

---

## 🚀 実装要件

### データ処理要件

#### 1. SemEval ABSA データ統合

```python
# domain_aware_feature_splitter.py の拡張
class SemEvalGPTExperimentRunner:
    def __init__(self):
        self.splitter = DomainAwareFeatureSplitter()
        self.gpt_analyzer = GPTAnalyzer()  # baseline_gpt_fewshot_cross_validation.py から

    def prepare_semeval_data(self):
        # ドメイン発見 → 特徴分割 → グループA/B作成
        pass
```

#### 2. 実験条件設定

- **ドメイン**: `['restaurant', 'laptop']`
- **特徴リスト**:
  - Restaurant: `['food', 'service', 'staff', 'atmosphere', 'menu', 'price']`
  - Laptop: `['battery', 'screen', 'keyboard', 'performance', 'price', 'design']`
- **データサイズ**: 50-200 レビュー/グループ（動的サイズ調整）

### GPT 実験要件

#### 1. プロンプト設計

```python
# baseline_gpt_fewshot_cross_validation.py のcreate_few_shot_prompt()を継承
def create_semeval_prompt(self, group_a_reviews, group_b_reviews, shot_count=0, examples=None):
    # SemEval特化プロンプト
    # ドメイン情報を含むプロンプト設計
    pass
```

#### 2. Few-shot 実験設定

- **Shot 数**: `[0, 1, 3]`（シンプル設定）
- **実験回数**: ドメイン別 × 特徴別 ×Shot 数 = 約 36 実験
- **評価指標**: 正確性、具体性、ハルシネーション、ドメイン適合性

### 結果保存・評価要件

#### 1. 実験結果構造

```json
{
  \"experiment_type\": \"semeval_absa_contrast_factor\",
  \"domain\": \"restaurant\",
  \"feature\": \"food\",
  \"shot_count\": 1,
  \"group_a_size\": 120,
  \"group_b_size\": 95,
  \"gpt_response\": \"Food quality descriptions and taste evaluations\",
  \"evaluation_scores\": {
    \"accuracy\": 0.85,
    \"specificity\": 0.78,
    \"hallucination\": 0.15,
    \"domain_relevance\": 0.92
  },
  \"timestamp\": \"2025-06-12T14:30:00Z\"
}
```

#### 2. 比較評価システム

- **ベースライン比較**: 過去実験結果（BERT: 0.619, BLEU: 0.018）との対比
- **ドメイン間比較**: Restaurant vs Laptop の性能差分析
- **データサイズ効果**: 50-200 レビューでの性能変化

## 🔗 関連ファイル参照

### 設定ファイル

- 環境変数: [`.env`](.env) - OpenAI API 設定
- 依存関係: [`requirements.txt`](requirements.txt) - 必要パッケージ

### データファイル

- SemEval ABSA: `data/external/absa-review-dataset/pyabsa-integrated/current/`
- 実験結果: `src/analysis/experiments/2025/06/12/`

### 文書ファイル

- 実験レポート: [`SemEval_ABSA_GPT対比因子生成検証実験レポート.md`](src/analysis/experiments/2025/06/12/SemEval_ABSA_GPT対比因子生成検証実験レポート.md)
- 過去実験分析: [`ハルシネーション検証実験レポート.md`](src/analysis/experiments/2025/06/06-2/ハルシネーション検証実験レポート.md)
