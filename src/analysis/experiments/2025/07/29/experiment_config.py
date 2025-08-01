"""
Steam 8アスペクト対比因子生成実験設定

READMEの仕様に基づく実験パラメータ定義
"""

# 実験メタデータ
EXPERIMENT_NAME = "steam_8aspect_contrast_experiment"
EXPERIMENT_VERSION = "1.0"
DESCRIPTION = "Steam レビューデータセットを使用した8アスペクト対比因子生成実験"

# 対象アスペクト（8個）
TARGET_ASPECTS = [
    "recommended",
    "story", 
    "gameplay",
    "visual",
    "audio",
    "technical",
    "price",
    "suggestion"
]

# Shot設定
SHOT_SETTINGS = [0, 1, 3]

# データ設定
DATASET_ID = "steam"
GROUP_SIZE = 300

# アスペクト説明文機能
USE_ASPECT_DESCRIPTION = True

# LLM設定
MODEL_CONFIG = {
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 1000
}

# 出力設定
OUTPUT_DIR = "results"