#!/usr/bin/env python3
"""
モデル選択ヘルパースクリプト

GPTの場合はAPIから動的に利用可能なモデルを取得し、選択肢を表示する。
その他のプロバイダーはモデルレジストリから取得する。
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent.parent
sys.path.insert(0, str(project_root / "src" / "analysis" / "experiments" / "utils"))

# .envファイルを読み込む
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

try:
    from LLM.model_registry import (
        MODEL_REGISTRY,
        get_all_models_by_tier,
        filter_available_models,
        get_provider_from_model_id
    )
    from LLM.llm_factory import LLMFactory
except ImportError as e:
    print(f"エラー: モジュールのインポートに失敗しました: {e}", file=sys.stderr)
    sys.exit(1)


def get_gpt_models_from_api() -> list:
    """
    GPTの利用可能なモデルをAPIから動的に取得
    
    Returns:
        モデル情報のリスト
    """
    try:
        # GPTクライアントを作成してモデル一覧を取得
        gpt_models = LLMFactory.get_supported_models(provider='openai', debug=False)
        
        # chat completions用のモデルのみをフィルタリング
        # gpt-4, gpt-3.5, o1, o3系のモデルのみを対象
        chat_models = []
        for model_id in gpt_models:
            model_lower = model_id.lower()
            if (model_lower.startswith('gpt-') or 
                model_lower.startswith('o1') or 
                model_lower.startswith('o3')):
                # 表示名を生成
                if model_lower.startswith('gpt-4o-mini'):
                    display_name = 'GPT-4o Mini'
                elif model_lower.startswith('gpt-4o'):
                    display_name = 'GPT-4o'
                elif model_lower.startswith('gpt-4-turbo'):
                    display_name = 'GPT-4 Turbo'
                elif model_lower.startswith('gpt-4'):
                    display_name = 'GPT-4'
                elif model_lower.startswith('gpt-3.5-turbo'):
                    display_name = 'GPT-3.5 Turbo'
                elif model_lower.startswith('o1'):
                    display_name = f'O1 ({model_id})'
                elif model_lower.startswith('o3'):
                    display_name = f'O3 ({model_id})'
                else:
                    display_name = model_id
                
                chat_models.append({
                    'model_id': model_id,
                    'display_name': display_name,
                    'provider': 'openai'
                })
        
        # モデル名でソート（gpt-4o-miniを先頭に）
        def sort_key(model):
            model_id = model['model_id'].lower()
            if model_id.startswith('gpt-4o-mini'):
                return (0, model_id)
            elif model_id.startswith('gpt-4o'):
                return (1, model_id)
            elif model_id.startswith('gpt-4'):
                return (2, model_id)
            elif model_id.startswith('gpt-3.5'):
                return (3, model_id)
            elif model_id.startswith('o1'):
                return (4, model_id)
            elif model_id.startswith('o3'):
                return (5, model_id)
            else:
                return (6, model_id)
        
        chat_models.sort(key=sort_key)
        return chat_models
    
    except Exception as e:
        print(f"警告: GPTモデル一覧の取得に失敗しました: {e}", file=sys.stderr)
        return []


def get_available_models_by_tier(tier: int) -> list:
    """
    指定されたTierの利用可能なモデル一覧を取得
    
    Args:
        tier: Tier番号 (1, 2, 3)
    
    Returns:
        利用可能なモデル情報のリスト
    """
    all_models = get_all_models_by_tier(tier)
    available_models = []
    
    for model in all_models:
        provider = model['provider']
        model_id = model['model_id']
        
        try:
            # プロバイダーが利用可能か確認
            if provider not in LLMFactory._providers:
                continue
            
            # GPTの場合はAPIから動的に取得したモデルのみを使用
            if provider == 'openai':
                gpt_models = get_gpt_models_from_api()
                gpt_model_ids = [m['model_id'] for m in gpt_models]
                if model_id not in gpt_model_ids:
                    continue
            
            # 実際に利用可能なモデルか確認（API呼び出しは行わず、レジストリのみ確認）
            # 実際のAPI呼び出しは時間がかかるため、レジストリに定義されているモデルのみを返す
            available_models.append(model)
        except Exception:
            # エラーが発生した場合はスキップ
            continue
    
    return available_models


def list_models_for_selection():
    """
    選択用のモデル一覧を表示
    
    GPTの場合はAPIから動的に取得したモデルのみを表示する
    
    Returns:
        選択可能なモデルのリスト
    """
    all_options = []
    option_index = 1
    
    # GPTの場合はAPIから動的に取得
    gpt_models = get_gpt_models_from_api()
    if gpt_models:
        for model in gpt_models:
            print(f"   {option_index}) {model['display_name']} ({model['model_id']})")
            all_options.append({
                'index': option_index,
                'model_id': model['model_id'],
                'display_name': model['display_name'],
                'provider': 'openai',
                'tier': None
            })
            option_index += 1
    
    return all_options


def get_model_by_index(index: int) -> dict:
    """
    インデックスからモデル情報を取得
    
    Args:
        index: 選択されたインデックス
    
    Returns:
        モデル情報辞書
    """
    all_options = []
    
    # GPTモデルのみを追加
    gpt_models = get_gpt_models_from_api()
    for model in gpt_models:
        all_options.append({
            'model_id': model['model_id'],
            'display_name': model['display_name'],
            'provider': 'openai'
        })
    
    if 1 <= index <= len(all_options):
        return all_options[index - 1]
    return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # モデル一覧を表示
        options = list_models_for_selection()
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "list":
        options = list_models_for_selection()
    elif command == "get" and len(sys.argv) >= 3:
        index = int(sys.argv[2])
        model = get_model_by_index(index)
        if model:
            print(model['model_id'])
        else:
            print("", file=sys.stderr)
            sys.exit(1)
    else:
        print("使用方法: python model_selector.py [list|get <index>]", file=sys.stderr)
        sys.exit(1)

