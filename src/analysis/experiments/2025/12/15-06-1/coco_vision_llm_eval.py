#!/usr/bin/env python3
import os, json, logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

import sys

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    repo_root = Path(__file__).resolve().parents[5]
    coco_img_dir = repo_root / "論文" / "image" / "coco"

    image_a = coco_img_dir / "concept_0_group_a.jpg"
    image_b = coco_img_dir / "concept_0_group_b.jpg"

    label = "Group A features everyday scenes and objects, while Group B focuses on events and people in formal settings."

    utils_dir = Path(__file__).resolve().parents[2] / "utils"
    sys.path.append(str(utils_dir))
    sys.path.append(str(utils_dir / "LLM"))

    from scores.llm_vision_score import calculate_llm_vision_alignment_score

    result = calculate_llm_vision_alignment_score(
        label=label,
        image_a_path=image_a,
        image_b_path=image_b,
        model_name=os.getenv("COCO_VISION_EVAL_MODEL", "gpt-4o"),
        temperature=0.0,
        max_tokens=250,
    )

    out = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "model": os.getenv("COCO_VISION_EVAL_MODEL", "gpt-4o"),
        "concept": "concept_0",
        "label": label,
        "image_a_path": str(image_a),
        "image_b_path": str(image_b),
        "result": result,
    }

    out_dir = Path(__file__).parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"coco_vision_llm_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("saved: %s", out_path)


if __name__ == "__main__":
    main()


