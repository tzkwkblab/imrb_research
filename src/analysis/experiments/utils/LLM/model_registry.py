"""
モデルレジストリ

各プロバイダーのモデルを性能別に3段階（Tier 1-3）で分類し、管理する。
"""

from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

MODEL_REGISTRY = {
    'openai': {
        # Tier 1 (最弱) - Fast, cost-efficient model
        'gpt-5-nano': {'tier': 1, 'display_name': 'GPT-5 nano', 'stars': '★'},
        
        # Tier 2 (中) - Balanced model
        'gpt-5-mini': {'tier': 2, 'display_name': 'GPT-5 mini', 'stars': '★★'},
        
        # Tier 3 (最強) - Most advanced model
        'gpt-5.1': {'tier': 3, 'display_name': 'GPT-5.1', 'stars': '★★★'},
    },
    'google': {
        # Tier 1 (最弱) - Most cost-effective model
        'gemini-2.5-flash-lite': {'tier': 1, 'display_name': 'Gemini 2.5 Flash-Lite', 'stars': '★'},
        
        # Tier 2 (中) - Balanced model
        'gemini-2.5-flash': {'tier': 2, 'display_name': 'Gemini 2.5 Flash', 'stars': '★★'},
        
        # Tier 3 (最強) - Most advanced model
        'gemini-2.5-pro': {'tier': 3, 'display_name': 'Gemini 2.5 Pro', 'stars': '★★★'},
    },
    'anthropic': {
        # Tier 1 (最弱) - Fast, cost-efficient model
        'claude-3-haiku-20240307': {'tier': 1, 'display_name': 'Claude 3 Haiku', 'stars': '★'},
        
        # Tier 2 (中) - Balanced model (最新Sonnet)
        'claude-sonnet-4-5-20250929': {'tier': 2, 'display_name': 'Claude Sonnet 4.5', 'stars': '★★'},
        
        # Tier 3 (最強) - Most advanced model (最新Opus)
        'claude-opus-4-1-20250805': {'tier': 3, 'display_name': 'Claude Opus 4.1', 'stars': '★★★'},
    }
}


def get_models_by_tier(provider: str, tier: int) -> List[Dict[str, str]]:
    """
    指定されたプロバイダーとTierのモデル一覧を取得
    
    Args:
        provider: プロバイダー名 ('openai', 'google', 'anthropic')
        tier: Tier番号 (1, 2, 3)
    
    Returns:
        モデル情報のリスト [{'model_id': '...', 'display_name': '...', 'stars': '...'}, ...]
    """
    if provider not in MODEL_REGISTRY:
        return []
    
    models = []
    for model_id, info in MODEL_REGISTRY[provider].items():
        if info['tier'] == tier:
            models.append({
                'model_id': model_id,
                'display_name': info['display_name'],
                'stars': info['stars'],
                'tier': tier
            })
    
    return models


def get_all_models_by_tier(tier: int) -> List[Dict[str, str]]:
    """
    全プロバイダーから指定されたTierのモデル一覧を取得
    
    Args:
        tier: Tier番号 (1, 2, 3)
    
    Returns:
        プロバイダー別のモデル情報のリスト
    """
    all_models = []
    for provider in MODEL_REGISTRY.keys():
        models = get_models_by_tier(provider, tier)
        for model in models:
            model['provider'] = provider
            all_models.append(model)
    
    return all_models


def get_model_info(provider: str, model_id: str) -> Optional[Dict[str, str]]:
    """
    指定されたモデルの情報を取得
    
    Args:
        provider: プロバイダー名
        model_id: モデルID
    
    Returns:
        モデル情報辞書、存在しない場合はNone
    """
    if provider not in MODEL_REGISTRY:
        return None
    
    if model_id not in MODEL_REGISTRY[provider]:
        return None
    
    info = MODEL_REGISTRY[provider][model_id].copy()
    info['model_id'] = model_id
    info['provider'] = provider
    return info


def filter_available_models(
    provider: str,
    available_model_ids: List[str]
) -> List[Dict[str, str]]:
    """
    レジストリに定義されたモデルのうち、実際に利用可能なモデルのみをフィルタリング
    
    Args:
        provider: プロバイダー名
        available_model_ids: APIから取得した利用可能なモデルIDのリスト
    
    Returns:
        利用可能なモデル情報のリスト
    """
    if provider not in MODEL_REGISTRY:
        return []
    
    available_models = []
    for model_id, info in MODEL_REGISTRY[provider].items():
        if model_id in available_model_ids:
            available_models.append({
                'model_id': model_id,
                'display_name': info['display_name'],
                'stars': info['stars'],
                'tier': info['tier'],
                'provider': provider
            })
    
    return available_models


def get_provider_from_model_id(model_id: str) -> Optional[str]:
    """
    モデルIDからプロバイダーを推定
    
    Args:
        model_id: モデルID
    
    Returns:
        プロバイダー名、推定できない場合はNone
    """
    model_id_lower = model_id.lower()
    
    # OpenAI
    if model_id_lower.startswith('gpt-') or model_id_lower.startswith('o'):
        return 'openai'
    
    # Google Gemini
    if model_id_lower.startswith('gemini-'):
        return 'google'
    
    # Anthropic Claude
    if model_id_lower.startswith('claude-'):
        return 'anthropic'
    
    return None

