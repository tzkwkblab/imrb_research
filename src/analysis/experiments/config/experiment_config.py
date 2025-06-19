"""
統一実験条件設定ファイル
プロンプト、使用モデル、出力ランダム性、評価指標などの実験条件を統一管理
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

# ============================
# モデル設定
# ============================

@dataclass
class ModelConfig:
    """LLMモデル設定"""
    name: str
    temperature: float
    max_tokens: int
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

# 使用可能なモデル設定
MODEL_CONFIGS = {
    "gpt-4": ModelConfig(
        name="gpt-4",
        temperature=0.3,
        max_tokens=100,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    ),
    "gpt-4-turbo": ModelConfig(
        name="gpt-4-turbo",
        temperature=0.3,
        max_tokens=100,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    ),
    "gpt-3.5-turbo": ModelConfig(
        name="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=100,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )
}

# 出力ランダム性設定（temperature別）
TEMPERATURE_CONFIGS = {
    "deterministic": 0.0,  # 完全に決定的
    "low_creativity": 0.3,  # 低創造性
    "balanced": 0.7,       # バランス型
    "high_creativity": 1.0  # 高創造性
}

# ============================
# プロンプト設定
# ============================

class PromptTemplates:
    """プロンプトテンプレート集"""
    
    # 基本対比因子抽出プロンプト
    BASIC_CONTRAST_PROMPT = """あなたは{domain_context}レビュー分析の専門家です。

【分析タスク】
以下の2つのレビューグループを比較して、グループAに特徴的でグループBには見られない表現パターンや内容の特徴を特定してください。

{few_shot_examples}

【グループA のレビュー】（{feature}特徴を含む）
{group_a_reviews}

【グループB のレビュー】（{feature}特徴を含まない）
{group_b_reviews}

【回答要求】
英語で5-10単語程度で、グループAに特徴的でグループBには見られない主要な違いを簡潔に回答してください。"""

    # 特徴判定用プロンプト
    FEATURE_CLASSIFICATION_PROMPT = """あなたは商品レビューを分析する専門家です。
以下の商品レビューに対して、各特徴が当てはまるかどうかを判定してください。

【レビュー】
{review_text}

【特徴リスト】
{features_list}

回答形式：
{{
    "features": {{
        "1": 0 or 1,
        "2": 0 or 1,
        ...
    }}
}}

※ 0=特徴なし、1=特徴あり
各特徴について、当てはまる場合は1、当てはまらない場合は0で回答してください。"""

    # ハルシネーション検証プロンプト
    HALLUCINATION_DETECTION_PROMPT = """以下のレビューグループの分析結果について、その妥当性を評価してください。

【レビューグループA】
{group_a_reviews}

【レビューグループB】
{group_b_reviews}

【分析結果】
"{gpt_statement}"

【評価基準】
この分析結果が実際のレビュー内容に基づいているかを0-1のスコアで評価してください。
- 1.0: 完全に妥当で根拠がある
- 0.5: 部分的に妥当だが不完全
- 0.0: 全く根拠がない/虚偽の分析"""

# ============================
# Few-shot設定
# ============================

@dataclass 
class FewShotConfig:
    """Few-shot学習設定"""
    shot_counts: List[int]
    example_sample_size: int
    target_sample_size: int

# 標準Few-shot設定
FEWSHOT_CONFIGS = {
    "standard": FewShotConfig(
        shot_counts=[0, 1, 3, 5],
        example_sample_size=3,
        target_sample_size=10
    ),
    "minimal": FewShotConfig(
        shot_counts=[0, 1],
        example_sample_size=2,
        target_sample_size=5
    ),
    "comprehensive": FewShotConfig(
        shot_counts=[0, 1, 2, 3, 5, 8],
        example_sample_size=5,
        target_sample_size=15
    )
}

# ============================
# 評価指標設定
# ============================

@dataclass
class EvaluationConfig:
    """評価指標設定"""
    use_bert_score: bool
    use_bleu_score: bool
    use_accuracy_score: bool
    use_hallucination_score: bool
    use_domain_relevance_score: bool
    similarity_model: str
    
# 評価指標設定（研究の主要指標に基づく）
EVALUATION_CONFIGS = {
    "primary": EvaluationConfig(
        use_bert_score=True,      # 主要指標：意味類似度
        use_bleu_score=True,      # 主要指標：表層一致率
        use_accuracy_score=False, # 参考値
        use_hallucination_score=True,
        use_domain_relevance_score=True,
        similarity_model="all-MiniLM-L6-v2"
    ),
    "comprehensive": EvaluationConfig(
        use_bert_score=True,
        use_bleu_score=True,
        use_accuracy_score=True,
        use_hallucination_score=True,
        use_domain_relevance_score=True,
        similarity_model="all-MiniLM-L6-v2"
    ),
    "bert_only": EvaluationConfig(
        use_bert_score=True,
        use_bleu_score=False,
        use_accuracy_score=False,
        use_hallucination_score=False,
        use_domain_relevance_score=False,
        similarity_model="all-MiniLM-L6-v2"
    )
}

# ============================
# データセット設定
# ============================

@dataclass
class DatasetConfig:
    """データセット設定"""
    name: str
    path: str
    domains: List[str]
    features: List[str]
    sample_sizes: List[int]

# 使用可能なデータセット
DATASET_CONFIGS = {
    "amazon_reviews": DatasetConfig(
        name="Amazon Product Reviews",
        path="src/analysis/experiments/2025/05/15/processed_reviews.csv",
        domains=["general"],
        features=[f"feature_{i}" for i in range(1, 21)],
        sample_sizes=[5, 10, 15, 20]
    ),
    "semeval_absa": DatasetConfig(
        name="SemEval ABSA Dataset",
        path="data/external/semeval-absa/current/",
        domains=["restaurant", "laptop"],
        features={
            "restaurant": ["food", "service", "staff", "atmosphere", "menu", "price"],
            "laptop": ["battery", "screen", "keyboard", "performance", "design", "price"]
        },
        sample_sizes=[50, 100, 200, 300]
    )
}

# ============================
# 実験設定統合クラス
# ============================

class ExperimentConfig:
    """統一実験設定管理クラス"""
    
    def __init__(self, 
                 model_key: str = "gpt-4",
                 temperature_key: str = "low_creativity", 
                 fewshot_key: str = "standard",
                 evaluation_key: str = "primary",
                 dataset_key: str = "semeval_absa"):
        
        self.model = MODEL_CONFIGS[model_key]
        # temperatureを指定されたキーで上書き
        self.model.temperature = TEMPERATURE_CONFIGS[temperature_key]
        
        self.fewshot = FEWSHOT_CONFIGS[fewshot_key]
        self.evaluation = EVALUATION_CONFIGS[evaluation_key]
        self.dataset = DATASET_CONFIGS[dataset_key]
        
        # メタデータ
        self.created_at = datetime.now().isoformat()
        self.config_version = "1.0"
        
    def to_dict(self) -> Dict:
        """設定を辞書形式で出力"""
        return {
            "model": {
                "name": self.model.name,
                "temperature": self.model.temperature,
                "max_tokens": self.model.max_tokens,
                "top_p": self.model.top_p,
                "frequency_penalty": self.model.frequency_penalty,
                "presence_penalty": self.model.presence_penalty
            },
            "fewshot": {
                "shot_counts": self.fewshot.shot_counts,
                "example_sample_size": self.fewshot.example_sample_size,
                "target_sample_size": self.fewshot.target_sample_size
            },
            "evaluation": {
                "use_bert_score": self.evaluation.use_bert_score,
                "use_bleu_score": self.evaluation.use_bleu_score,
                "use_accuracy_score": self.evaluation.use_accuracy_score,
                "use_hallucination_score": self.evaluation.use_hallucination_score,
                "use_domain_relevance_score": self.evaluation.use_domain_relevance_score,
                "similarity_model": self.evaluation.similarity_model
            },
            "dataset": {
                "name": self.dataset.name,
                "path": self.dataset.path,
                "domains": self.dataset.domains,
                "features": self.dataset.features,
                "sample_sizes": self.dataset.sample_sizes
            },
            "metadata": {
                "created_at": self.created_at,
                "config_version": self.config_version
            }
        }
    
    def get_prompt_template(self, prompt_type: str = "contrast") -> str:
        """指定されたプロンプトテンプレートを取得"""
        if prompt_type == "contrast":
            return PromptTemplates.BASIC_CONTRAST_PROMPT
        elif prompt_type == "classification": 
            return PromptTemplates.FEATURE_CLASSIFICATION_PROMPT
        elif prompt_type == "hallucination":
            return PromptTemplates.HALLUCINATION_DETECTION_PROMPT
        else:
            raise ValueError(f"Unknown prompt type: {prompt_type}")

# ============================
# 実験条件プリセット
# ============================

# 高精度実験設定（低temperature + GPT-4）
HIGH_PRECISION_CONFIG = ExperimentConfig(
    model_key="gpt-4",
    temperature_key="deterministic", 
    fewshot_key="comprehensive",
    evaluation_key="comprehensive"
)

# バランス実験設定（中温度 + GPT-4）
BALANCED_CONFIG = ExperimentConfig(
    model_key="gpt-4",
    temperature_key="low_creativity",
    fewshot_key="standard", 
    evaluation_key="primary"
)

# 高創造性実験設定（高temperature + GPT-3.5）
HIGH_CREATIVITY_CONFIG = ExperimentConfig(
    model_key="gpt-3.5-turbo",
    temperature_key="high_creativity",
    fewshot_key="minimal",
    evaluation_key="bert_only"
)

# ============================
# 使用例
# ============================

if __name__ == "__main__":
    # 標準設定での実験設定作成
    config = ExperimentConfig()
    print("Standard Config:")
    print(f"Model: {config.model.name} (temp: {config.model.temperature})")
    print(f"Few-shot: {config.fewshot.shot_counts}")
    print(f"Evaluation: BERT={config.evaluation.use_bert_score}, BLEU={config.evaluation.use_bleu_score}")
    
    # プリセット設定の確認
    print("\nHigh Precision Config:")
    hp_config = HIGH_PRECISION_CONFIG
    print(f"Model: {hp_config.model.name} (temp: {hp_config.model.temperature})")
    
    # プロンプトテンプレートの取得
    prompt = config.get_prompt_template("contrast")
    print(f"\nPrompt template length: {len(prompt)} characters") 