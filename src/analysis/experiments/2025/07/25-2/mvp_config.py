"""
MVP実験設定

新しいutils統合ツールを活用した対比因子生成実験の最小構成版
Steam Reviewデータセットでのgameplay vs visual対比実験
"""

# データセット設定
DATASET = "steam"
ASPECTS = ["gameplay", "visual"]

# 実験設定
GROUP_SIZE = 100  # MVP用の小さいサンプルサイズ
SHOT_CONFIG = 0   # 0-shotのみ
OUTPUT_DIR = "results/"

# LLM設定
TEMPERATURE = 0.7
MAX_TOKENS = 1000
MODEL_NAME = "gpt-3.5-turbo"

# 出力設定
SAVE_FORMAT = "json"
DEBUG_MODE = True
CONSOLE_OUTPUT = True

# 実験メタデータ
EXPERIMENT_VERSION = "MVP-1.0"
DESCRIPTION = "最小構成での対比因子生成実験" 