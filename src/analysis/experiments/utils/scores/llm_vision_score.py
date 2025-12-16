#!/usr/bin/env python3
"""
画像A/Bと対比因子ラベルの整合性をLLMで5段階評価する。
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    from ..LLM.llm_factory import LLMFactory
except ImportError:
    sys.path.append(str(Path(__file__).parent.parent))
    from LLM.llm_factory import LLMFactory

logger = logging.getLogger(__name__)


def _create_vision_eval_prompt(label: str) -> str:
    return f"""あなたは厳密な評価者です。
与えられた2枚の画像は、それぞれグループAとグループBの代表例です。
以下の対比因子ラベルが、画像Aと画像Bの違いをどの程度適切に表しているかを5段階（1-5）で評価してください。

対比因子ラベル:
{label}

評価観点:
- ラベルが述べる差分が、画像Aと画像Bで一貫して観察できるか
- ラベルが曖昧すぎず、差分の中心を捉えているか
- 画像の一部の例外だけに引きずられていないか

評価基準:
- 5: 差分の中心を正確に捉え、A/Bの違いを明確に説明している
- 4: 概ね適切だが、細部にズレや不足がある
- 3: 一部は当てはまるが、差分の中心としては弱い/曖昧
- 2: 部分的にしか当てはまらず、誤解を招く
- 1: ほとんど当てはまらない

出力はJSONのみ:
{{
  "score": 4,
  "normalized_score": 0.8,
  "reasoning": "理由を簡潔に"
}}

scoreは1-5の整数。normalized_scoreはscore/5.0。reasoningは80文字以内。"""


def calculate_llm_vision_alignment_score(
    label: str,
    image_a_path: Union[str, Path],
    image_b_path: Union[str, Path],
    model_name: str = "gpt-4o",
    temperature: float = 0.0,
    max_tokens: int = 250,
) -> Optional[Dict[str, Any]]:
    if not label or not str(label).strip():
        logger.warning("空のラベルが渡されました")
        return None

    image_a_path = Path(image_a_path)
    image_b_path = Path(image_b_path)
    if not image_a_path.exists() or not image_b_path.exists():
        logger.error("画像ファイルが見つかりません: %s, %s", image_a_path, image_b_path)
        return None

    client = LLMFactory.create_client(model_name=model_name, debug=False)

    prompt = _create_vision_eval_prompt(label=str(label).strip())
    messages = [{"role": "user", "content": prompt}]

    if not hasattr(client, "query_with_images"):
        logger.error("このクライアントは画像入力に対応していません: %s", type(client).__name__)
        return None

    response = client.query_with_images(
        messages=messages,
        image_paths=[image_a_path, image_b_path],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if response is None:
        return None

    response_clean = response.strip()
    if response_clean.startswith("```"):
        lines = response_clean.split("\n")
        json_lines = []
        in_block = False
        for line in lines:
            if line.strip().startswith("```json") or line.strip().startswith("```"):
                in_block = True
                continue
            if in_block and line.strip().startswith("```"):
                break
            if in_block:
                json_lines.append(line)
        response_clean = "\n".join(json_lines).strip()

    try:
        result = json.loads(response_clean)
    except json.JSONDecodeError:
        logger.warning("JSON解析に失敗しました: %s", response[:200])
        return None

    if "score" not in result:
        return None

    score = int(result["score"])
    if not (1 <= score <= 5):
        return None

    normalized = float(result.get("normalized_score", score / 5.0))
    reasoning = str(result.get("reasoning", ""))

    return {"score": score, "normalized_score": normalized, "reasoning": reasoning}


