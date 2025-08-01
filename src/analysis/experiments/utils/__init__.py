# utils統合ツールパッケージ

# 主要クラス・関数のインポート
try:
    # 相対インポートを試行
    from .contrast_factor_analyzer import ContrastFactorAnalyzer
    from .dataset_manager import DatasetManager, LoaderFactory, SplitterFactory
    from .get_score import (
        calculate_scores, 
        calculate_scores_batch, 
        calculate_one_to_many,
        calculate_scores_with_descriptions
    )
    from .prompt_contrast_factor import generate_contrast_factor_prompt
    from .aspect_description_manager import AspectDescriptionManager
    
    # LLM関連
    from .LLM.llm_factory import LLMFactory
    from .LLM.base_llm import BaseLLM
    
    # 設定関連
    from .config import DatasetConfig, ConfigValidator, ValidationError
    
    # データローダー関連
    from .loaders.base import BaseDatasetLoader, UnifiedRecord
    from .loaders.steam_loader import SteamDatasetLoader
    from .loaders.semeval_loader import SemEvalDatasetLoader
    from .loaders.amazon_loader import AmazonDatasetLoader
    
    # 分割戦略関連
    from .splitters.base import BaseSplitter, BinarySplitResult, SplitOptions
    from .splitters.aspect_splitter import AspectSplitter
    from .splitters.binary_splitter import BinarySplitter
    
    # スコア計算関連
    from .scores.bert_score import calculate_bert_score
    from .scores.bleu_score import calculate_bleu_score
    
except ImportError:
    # 絶対インポートにフォールバック
    try:
        from contrast_factor_analyzer import ContrastFactorAnalyzer
        from dataset_manager import DatasetManager, LoaderFactory, SplitterFactory
        from get_score import (
            calculate_scores, 
            calculate_scores_batch, 
            calculate_one_to_many,
            calculate_scores_with_descriptions
        )
        from prompt_contrast_factor import generate_contrast_factor_prompt
        from aspect_description_manager import AspectDescriptionManager
        
        # LLM関連
        from LLM.llm_factory import LLMFactory
        from LLM.base_llm import BaseLLM
        
        # 設定関連
        from config import DatasetConfig, ConfigValidator, ValidationError
        
        # データローダー関連
        from loaders.base import BaseDatasetLoader, UnifiedRecord
        from loaders.steam_loader import SteamDatasetLoader
        from loaders.semeval_loader import SemEvalDatasetLoader
        from loaders.amazon_loader import AmazonDatasetLoader
        
        # 分割戦略関連
        from splitters.base import BaseSplitter, BinarySplitResult, SplitOptions
        from splitters.aspect_splitter import AspectSplitter
        from splitters.binary_splitter import BinarySplitter
        
        # スコア計算関連
        from scores.bert_score import calculate_bert_score
        from scores.bleu_score import calculate_bleu_score
        
    except ImportError as e:
        print(f"Warning: Failed to import some utils components: {e}")
        # 最低限の空クラスを定義（エラー回避）
        class ContrastFactorAnalyzer: pass
        class DatasetManager: pass

# パッケージ全体で利用可能な主要クラス・関数
__all__ = [
    # 統合ツール
    'ContrastFactorAnalyzer',
    'DatasetManager',
    'LoaderFactory', 
    'SplitterFactory',
    
    # スコア計算
    'calculate_scores',
    'calculate_scores_batch',
    'calculate_one_to_many',
    'calculate_scores_with_descriptions',
    'calculate_bert_score',
    'calculate_bleu_score',
    
    # プロンプト生成
    'generate_contrast_factor_prompt',
    
    # アスペクト管理
    'AspectDescriptionManager',
    
    # LLM関連
    'LLMFactory',
    'BaseLLM',
    
    # 設定管理
    'DatasetConfig',
    'ConfigValidator', 
    'ValidationError',
    
    # データローダー
    'BaseDatasetLoader',
    'UnifiedRecord',
    'SteamDatasetLoader',
    'SemEvalDatasetLoader',
    'AmazonDatasetLoader',
    
    # 分割戦略
    'BaseSplitter',
    'BinarySplitResult',
    'SplitOptions',
    'AspectSplitter',
    'BinarySplitter',
]