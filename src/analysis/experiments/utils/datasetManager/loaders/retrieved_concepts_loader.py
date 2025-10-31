"""
Retrieved Concepts (COCO captions retrieved per concept) 専用ローダー

大容量 JSON を一括ロードせず、`results` 配下の各コンセプトオブジェクト単位で
小分割パースして `UnifiedRecord` に変換する。
"""

from pathlib import Path
from typing import Dict, Generator, List, Optional
import json

from .base import BaseDatasetLoader, UnifiedRecord
from ..configs.dataset_config import DatasetConfig


class RetrievedConceptsDatasetLoader(BaseDatasetLoader):
    """Farnoosh 共有の retrieved_dataset_100.json を扱うローダー"""

    def __init__(self, base_path: Optional[str] = None, config: Optional[DatasetConfig] = None):
        if base_path is None and config is not None:
            dataset_info = config.get_dataset_info("retrieved_concepts")
            base_path = dataset_info.path
        elif base_path is None:
            # external配下の標準配置（currentシンボリックリンク）
            base_path = "/Users/seinoshun/imrb_research/data/external/retrieved-concepts/farnoosh/current"

        super().__init__(base_path, "retrieved_concepts")
        self.config = config
        self._aspects: Optional[List[str]] = None

    def load_raw_data(self) -> List[UnifiedRecord]:
        """JSON をコンセプト単位でパースしてフラットなレコードに変換"""
        target = Path(str(self.base_path))
        # ディレクトリが指定された場合は中のJSONを探索
        if target.is_dir():
            json_file = self._find_json_file(target)
            if json_file is None:
                raise FileNotFoundError(f"JSONファイルが見つかりません: {target}")
            file_path = json_file
        else:
            file_path = target
            if not file_path.exists():
                raise FileNotFoundError(f"データファイルが見つかりません: {file_path}")

        records: List[UnifiedRecord] = []
        discovered_aspects: List[str] = []

        for concept_obj in self._iter_concept_objects(file_path):
            concept_id = concept_obj.get("concept_id")
            if concept_id is None:
                continue
            aspect_name = f"concept_{int(concept_id)}"
            if aspect_name not in discovered_aspects:
                discovered_aspects.append(aspect_name)

            topk = concept_obj.get("topk", [])
            for item in topk:
                captions = item.get("captions", []) or []
                image_path = item.get("path", "")
                score = item.get("score", None)
                rank = item.get("rank", None)

                for caption in captions:
                    text = str(caption).strip()
                    if not text:
                        continue
                    records.append(
                        UnifiedRecord(
                            text=text,
                            aspect=aspect_name,
                            label=1,  # 本データはアスペクトに対するポジティブ集合
                            domain="vision",
                            dataset_id="retrieved_concepts",
                            metadata={
                                "concept_id": int(concept_id),
                                "image_path": image_path,
                                "score": score,
                                "rank": rank,
                            },
                        )
                    )

        self._aspects = discovered_aspects
        return records

    def get_available_aspects(self) -> List[str]:
        if self._aspects is not None:
            return list(self._aspects)

        # 事前に全量ロードしていない場合は軽量スキャンでアスペクトのみ収集
        target = Path(str(self.base_path))
        if target.is_dir():
            json_file = self._find_json_file(target)
            if json_file is None:
                return []
            file_path = json_file
        else:
            file_path = target
        aspects: List[str] = []
        for concept_obj in self._iter_concept_objects(file_path):
            cid = concept_obj.get("concept_id")
            if cid is None:
                continue
            name = f"concept_{int(cid)}"
            if name not in aspects:
                aspects.append(name)
        self._aspects = aspects
        return aspects

    def get_domain_info(self) -> Dict:
        return {
            "domain": "vision",
            "dataset": "retrieved_concepts",
            "language": "en",
            "data_path": str(self.base_path) if self.base_path else None,
        }

    def _iter_concept_objects(self, file_path: Path) -> Generator[Dict, None, None]:
        """
        `results` 配下の各コンセプトオブジェクトを文字列バッファで切り出し、
        個別に json.loads する簡易ストリーミングパーサ。
        """
        with open(file_path, "r", encoding="utf-8") as f:
            in_results = False
            capturing = False
            brace_depth = 0
            buffer_lines: List[str] = []

            for raw_line in f:
                line = raw_line.rstrip("\n")

                if not in_results:
                    if '"results"' in line and "[" in line:
                        in_results = True
                    continue

                # 結果配列の終端
                if in_results and not capturing and "]" in line:
                    break

                # オブジェクト開始検出
                if in_results and not capturing:
                    if "{" in line:
                        capturing = True
                        brace_depth = line.count("{") - line.count("}")
                        buffer_lines = [line]
                        # 単行で完結する場合
                        if brace_depth == 0:
                            try:
                                obj = json.loads("".join(buffer_lines).strip().rstrip(","))
                                yield obj
                            except Exception:
                                pass
                            capturing = False
                            buffer_lines = []
                    continue

                if capturing:
                    buffer_lines.append(line)
                    brace_depth += line.count("{") - line.count("}")
                    if brace_depth == 0:
                        try:
                            obj = json.loads("\n".join(buffer_lines).strip().rstrip(","))
                            yield obj
                        except Exception:
                            # 解析失敗時はスキップ
                            pass
                        capturing = False
                        buffer_lines = []

    def _find_json_file(self, dir_path: Path) -> Optional[Path]:
        """ディレクトリ内のretrieved_dataset_*.jsonを優先探索"""
        candidates = sorted(dir_path.glob("retrieved_dataset_*.json"))
        if candidates:
            return candidates[0]
        # フォールバック: 直下の単一JSON
        any_json = sorted(dir_path.glob("*.json"))
        return any_json[0] if any_json else None


