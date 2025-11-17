#!/usr/bin/env python3
"""
モデル選択ヘルパースクリプト

モデルレジストリから利用可能なモデルを取得し、選択肢を表示する。
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent.parent
sys.path.insert(0, str(project_root / "src" / "analysis" / "experiments" / "utils"))

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
    
    Returns:
        選択可能なモデルのリスト
    """
    all_options = []
    option_index = 1
    
    for tier in [1, 2, 3]:
        tier_name = {1: "最弱", 2: "中", 3: "最強"}[tier]
        stars = {1: "★", 2: "★★", 3: "★★★"}[tier]
        
        models = get_available_models_by_tier(tier)
        
        if models:
            print(f"{tier}) {stars} {tier_name}レベル")
            for model in models:
                print(f"   {option_index}) {model['display_name']} ({model['model_id']})")
                all_options.append({
                    'index': option_index,
                    'model_id': model['model_id'],
                    'display_name': model['display_name'],
                    'provider': model['provider'],
                    'tier': tier
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
    for tier in [1, 2, 3]:
        models = get_available_models_by_tier(tier)
        for model in models:
            all_options.append(model)
    
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

