#!/usr/bin/env python3
"""
統一実験パイプライン

複数データセット対応の実験パイプライン実装
設定ファイル駆動で保守性の高い設計
"""

import sys
import json
import yaml
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

# utilsディレクトリのパス設定
SCRIPT_DIR = Path(__file__).parent
EXPERIMENTS_DIR = SCRIPT_DIR.parent.parent.parent
sys.path.insert(0, str(EXPERIMENTS_DIR))

# 必要なモジュールをインポート
from utils.datasetManager.dataset_manager import DatasetManager
from utils.cfGenerator.contrast_factor_analyzer import ContrastFactorAnalyzer
from utils.scores.get_score import calculate_scores


class ExperimentPipeline:
    """統一実験パイプライン"""
    
    def __init__(self, config_path: str, debug: bool = True):
        """
        初期化
        
        Args:
            config_path: 設定ファイルパス
            debug: デバッグモード
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.debug = debug
        self.setup_logging()
        
        self.dataset_manager = None
        self.results = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_name = self._derive_run_name()
        self.run_dir: Optional[Path] = None
        # アスペクト説明CSVのキャッシュ {csv_path: {aspect: description}}
        self._desc_cache: Dict[str, Dict[str, str]] = {}
        # 例題ファイルのキャッシュ {path: List[Dict]}
        self._examples_cache: Dict[str, List[Dict]] = {}

    def _get_dated_results_base(self) -> Path:
        """日付(YYYY/MM/DD)に基づく結果ベースディレクトリを返す。
        例: src/analysis/experiments/2025/10/21/results
        """
        try:
            y = self.timestamp[0:4]
            m = self.timestamp[4:6]
            d = self.timestamp[6:8]
        except Exception:
            from datetime import datetime as _dt
            now = _dt.now()
            y = f"{now.year:04d}"
            m = f"{now.month:02d}"
            d = f"{now.day:02d}"
        return EXPERIMENTS_DIR / y / m / d / "results"

    def _derive_run_name(self) -> str:
        """実行名を決定（configのrun_name > 設定ファイル名）"""
        try:
            name_from_config = self.config.get('run_name')
            if isinstance(name_from_config, str) and name_from_config.strip():
                return name_from_config.strip()
        except Exception:
            pass
        return self.config_path.stem
        
    def setup_logging(self):
        """ログ設定"""
        log_level = logging.INFO if self.debug else logging.WARNING
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _attach_file_logger(self) -> None:
        """実行ディレクトリ配下にファイルロガーを取り付ける"""
        if self.run_dir is None:
            return
        log_dir = self.run_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        from logging import FileHandler, Formatter
        fh = FileHandler(log_dir / "python.log", encoding="utf-8")
        fh.setLevel(logging.DEBUG if self.debug else logging.INFO)
        fmt = Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        fh.setFormatter(fmt)
        root = logging.getLogger()
        # 重複追加防止
        if not any(getattr(h, 'baseFilename', '').endswith("python.log") for h in root.handlers):
            root.addHandler(fh)
    
    def _load_config(self) -> Dict:
        """設定ファイル読み込み"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def validate_config(self) -> bool:
        """設定ファイル検証"""
        self.logger.info("設定ファイルを検証中...")
        
        # 必須キーの確認
        required_keys = ['experiments', 'output', 'llm']
        for key in required_keys:
            if key not in self.config:
                self.logger.error(f"必須キー '{key}' が設定ファイルにありません")
                return False
        
        # 実験設定の確認
        if not self.config['experiments']:
            self.logger.error("実験設定が空です")
            return False
        
        self.logger.info("✅ 設定ファイル検証完了")
        return True
    
    def setup_dataset_manager(self):
        """DatasetManager初期化"""
        self.logger.info("DatasetManagerを初期化中...")
        
        try:
            # データルートパスを指定
            data_root = Path("/Users/seinoshun/imrb_research/data/external")
            self.dataset_manager = DatasetManager(data_root=data_root)
            
            self.logger.info("✅ DatasetManager初期化完了")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ DatasetManager初期化失敗: {e}")
            return False
    
    def run_single_experiment(
        self, 
        dataset: str, 
        aspect: str, 
        group_size: int,
        split_type: str = "aspect_vs_others",
        output_dir: Optional[Path] = None
    ) -> Optional[Dict]:
        """
        単一実験実行
        
        Args:
            dataset: データセット名
            aspect: アスペクト名
            group_size: グループサイズ
            split_type: 分割タイプ
            
        Returns:
            実験結果辞書
        """
        experiment_id = f"{dataset}_{aspect}_{self.timestamp}"
        
        self.logger.info(f"\n{'='*50}")
        self.logger.info(f"実験開始: {experiment_id}")
        self.logger.info(f"データセット: {dataset}")
        self.logger.info(f"アスペクト: {aspect}")
        self.logger.info(f"グループサイズ: {group_size}")
        self.logger.info(f"分割タイプ: {split_type}")
        
        try:
            # [1/3] データ分割取得
            self.logger.info(f"\n[1/3] データ読み込み中...")
            
            # データセット情報を確認
            try:
                records = self.dataset_manager.load_dataset(dataset)
                self.logger.info(f"データセット読み込み: {len(records)}件のレコード")
                
                # アスペクト分布確認
                aspect_records = [r for r in records if r.aspect == aspect]
                self.logger.info(f"アスペクト '{aspect}' のレコード: {len(aspect_records)}件")
                
            except Exception as e:
                self.logger.error(f"データセット読み込みエラー: {e}")
                raise
            
            splits = self.dataset_manager.split_dataset(
                dataset_id=dataset,
                aspect=aspect,
                group_size=group_size,
                split_type=split_type
            )
            
            self.logger.info(f"✅ データ読み込み完了 (A: {len(splits.group_a)}件, B: {len(splits.group_b)}件)")
            self.logger.info(f"正解ラベル: {splits.correct_answer}")
            
            # [2/3] 対比因子分析実行
            self.logger.info(f"\n[2/3] 対比因子分析実行中...")
            
            # 出力ディレクトリ設定（実行ディレクトリ配下）
            out_dir = output_dir if output_dir is not None else Path(self.config['output']['directory'])
            out_dir.mkdir(parents=True, exist_ok=True)
            
            # 一般設定から説明文利用フラグとCSVファイルパスを取得
            general_cfg = self.config.get('general', {}) or {}
            use_desc = bool(general_cfg.get('use_aspect_descriptions', False))
            desc_file = general_cfg.get('aspect_descriptions_file')
            # 例題設定
            use_examples = bool(general_cfg.get('use_examples', False))
            examples_file = general_cfg.get('examples_file')
            max_examples = general_cfg.get('max_examples')
            if isinstance(max_examples, str):
                try:
                    max_examples = int(max_examples) if max_examples.strip() else None
                except Exception:
                    max_examples = None

            analyzer = ContrastFactorAnalyzer(debug=self.debug, use_aspect_descriptions=use_desc)
            
            # 例題読み込み（必要時）
            examples_payload: Optional[List[Dict]] = None
            if use_examples and examples_file:
                examples_all = self._load_examples_file(str(examples_file))
                if isinstance(max_examples, int) and max_examples > 0:
                    examples_payload = examples_all[:max_examples]
                else:
                    examples_payload = examples_all

            result = analyzer.analyze(
                group_a=splits.group_a,
                group_b=splits.group_b,
                correct_answer=splits.correct_answer,
                output_dir=str(out_dir),
                experiment_name=experiment_id,
                # デフォルトの説明文フォールバック用（外部データ標準のdescriptions.csv）
                dataset_path=str(self.dataset_manager.data_root / 'steam-review-aspect-dataset' / 'current') if dataset == 'steam' else None,
                aspect_descriptions_file=desc_file,
                examples=examples_payload
            )
            
            self.logger.info("✅ LLM応答取得完了")
            
            # [3/3] スコア確認（analyzersで既に計算済み）
            self.logger.info(f"\n[3/3] スコア確認中...")
            
            bert_score = result['evaluation']['bert_score']
            bleu_score = result['evaluation']['bleu_score']
            llm_response = result['process']['llm_response']
            
            self.logger.info("✅ スコア確認完了")
            
            # 結果表示
            self.logger.info(f"\n{'='*50}")
            self.logger.info(f"=== 結果 ===")
            self.logger.info(f"BERTスコア: {bert_score:.4f}")
            self.logger.info(f"BLEUスコア: {bleu_score:.4f}")
            self.logger.info(f"LLM応答: {llm_response}")
            self.logger.info(f"品質評価: {result['summary']['quality_assessment']['overall_quality']}")
            
            # メタデータ追加
            result['experiment_info']['dataset'] = dataset
            result['experiment_info']['aspect'] = aspect
            result['experiment_info']['group_size'] = group_size
            result['experiment_info']['split_type'] = split_type
            # 選択モード/CSVパス（analyzer側で既に含めるが明示的に保持）
            result['experiment_info']['use_aspect_descriptions'] = bool(use_desc)
            result['experiment_info']['aspect_descriptions_file'] = desc_file or ''
            # 例題メタ情報
            result['experiment_info']['use_examples'] = bool(use_examples)
            result['experiment_info']['examples_file'] = examples_file or ''
            result['experiment_info']['examples_count_used'] = len(examples_payload or [])
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 実験失敗 ({experiment_id}): {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "experiment_info": {
                    "experiment_id": experiment_id,
                    "dataset": dataset,
                    "aspect": aspect,
                    "error": str(e)
                },
                "summary": {
                    "success": False,
                    "error": str(e)
                }
            }
    
    def run_batch_experiments(self) -> List[Dict]:
        """バッチ実験実行"""
        self.logger.info("=" * 60)
        self.logger.info("バッチ実験開始")
        self.logger.info("=" * 60)
        
        all_results = []
        
        # 実行用ディレクトリを準備
        # 日付ベースパスに時刻ディレクトリ作成（experiments/{YYYY}/{MM}/{DD}/results/時刻）
        base_output_dir = self._get_dated_results_base()
        base_output_dir.mkdir(parents=True, exist_ok=True)
        self.run_dir = base_output_dir / f"{self.timestamp}"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"出力ディレクトリ: {self.run_dir}")
        # ファイルロガー取り付け
        self._attach_file_logger()

        # 各実験設定を実行
        for exp_config in self.config['experiments']:
            dataset = exp_config['dataset']
            aspects = exp_config['aspects']
            group_size = exp_config.get('group_size', 100)
            split_type = exp_config.get('split_type', 'aspect_vs_others')
            
            self.logger.info(f"\n📊 データセット: {dataset}")
            self.logger.info(f"対象アスペクト: {aspects}")
            
            # 各アスペクトで実験実行
            for aspect in aspects:
                result = self.run_single_experiment(
                    dataset=dataset,
                    aspect=aspect,
                    group_size=group_size,
                    split_type=split_type,
                    output_dir=self.run_dir
                )
                
                if result:
                    all_results.append(result)
        
        self.results = all_results
        return all_results
    
    def save_results(self, results: Optional[List[Dict]] = None) -> str:
        """結果保存"""
        if results is None:
            results = self.results
        
        if not results:
            self.logger.warning("保存する結果がありません")
            return ""
        
        # 出力ディレクトリ（実行用ディレクトリ配下）
        if self.run_dir is None:
            base_output_dir = self._get_dated_results_base()
            self.run_dir = base_output_dir / f"{self.timestamp}"
            self.run_dir.mkdir(parents=True, exist_ok=True)
        
        # 統合結果作成
        summary = {
            "experiment_meta": {
                "timestamp": self.timestamp,
                "config_file": str(self.config_path),
                "total_experiments": len(results),
                "successful_experiments": sum(
                    1 for r in results if r.get('summary', {}).get('success', False)
                ),
                "run_name": self.run_name,
                "output_dir": str(self.run_dir)
            },
            "results": results
        }
        
        # 保存
        filename = f"batch_experiment_{self.timestamp}.json"
        filepath = self.run_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"\n📁 結果保存: {filepath}")

        # 実行時設定の保存（スナップショット）
        self._save_run_configuration()

        # マークダウンサマリーの生成（詳細）
        self._write_markdown_summary(summary)
        # ルートresultsに概要を作成
        self._write_root_overview(summary)
        
        return str(filepath)

    def _save_run_configuration(self) -> None:
        """実行時設定（有効値）を保存"""
        if self.run_dir is None:
            return
        # 設定スナップショット（元YAML）
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                original_yaml = f.read()
            with open(self.run_dir / 'pipeline_config_snapshot.yaml', 'w', encoding='utf-8') as f:
                f.write(original_yaml)
        except Exception:
            pass
        # 実行メタ（JSON）
        effective = {
            "timestamp": self.timestamp,
            "run_name": self.run_name,
            "output_dir": str(self.run_dir),
            "config_path": str(self.config_path),
            "experiments": self.config.get('experiments', []),
            "llm": self.config.get('llm', {}),
            "general": self.config.get('general', {})
        }
        with open(self.run_dir / 'run_effective_config.json', 'w', encoding='utf-8') as f:
            json.dump(effective, f, ensure_ascii=False, indent=2)

    def _write_markdown_summary(self, summary_data: Dict) -> None:
        """設定値と結果概要のMarkdownを作成"""
        if self.run_dir is None:
            return
        lines = []
        meta = summary_data.get('experiment_meta', {})
        results = summary_data.get('results', [])
        lines.append(f"# 実験サマリー: {self.run_name}")
        lines.append("")
        lines.append(f"- 実行時刻: {meta.get('timestamp', '')}")
        lines.append(f"- 出力先: {meta.get('output_dir', '')}")
        lines.append(f"- 総実験数: {meta.get('total_experiments', 0)}")
        lines.append(f"- 成功数: {meta.get('successful_experiments', 0)}")
        lines.append("")
        # 設定
        lines.append("## 設定")
        lines.append("")
        lines.append("```yaml")
        try:
            with open(self.run_dir / 'pipeline_config_snapshot.yaml', 'r', encoding='utf-8') as f:
                lines.append(f.read())
        except Exception:
            # フォールバックとして簡易設定
            lines.append(yaml.safe_dump(self.config, allow_unicode=True))
        lines.append("```")
        lines.append("")
        # 結果一覧
        lines.append("## 結果概要")
        lines.append("")
        lines.append("| データセット | アスペクト | 件数(A/B) | 例題数 | BERT | BLEU | 品質 | LLM出力 | 出力ファイル |")
        lines.append("| --- | --- | --- | ---:| ---:| ---:| --- | --- | --- |")
        for r in results:
            if not r.get('summary', {}).get('success', False):
                continue
            info = r.get('experiment_info', {})
            evals = r.get('evaluation', {})
            out_file = r.get('output_file', '')
            # アスペクト表示（説明文モード時は (元アスペクト) 説明文）
            aspect_name = info.get('aspect', '')
            aspect_display = aspect_name
            try:
                if info.get('use_aspect_descriptions') and info.get('aspect_descriptions_file'):
                    csv_path = str(info.get('aspect_descriptions_file'))
                    desc_map = self._load_aspect_descriptions(csv_path)
                    desc_text = desc_map.get(aspect_name, '')
                    if desc_text:
                        aspect_display = f"({aspect_name}) {desc_text}"
            except Exception:
                pass
            # 件数（A/B）
            a_count = len(((r.get('input') or {}).get('group_a') or []))
            b_count = len(((r.get('input') or {}).get('group_b') or []))
            counts_display = f"A:{a_count}/B:{b_count}"
            # 例題数
            examples_count = int((info.get('examples_count_used') or 0))
            # LLM出力（テーブル向けに整形・短縮）
            llm_text = (r.get('process', {}) or {}).get('llm_response', '') or ''
            llm_text = llm_text.replace("\n", " ").replace("|", "｜").strip()
            if len(llm_text) > 160:
                llm_text = llm_text[:157] + "..."
            lines.append(
                f"| {info.get('dataset','')} | {aspect_display} | {counts_display} | {examples_count} | "
                f"{evals.get('bert_score',0):.4f} | {evals.get('bleu_score',0):.4f} | "
                f"{r.get('summary',{}).get('quality_assessment',{}).get('overall_quality','')} | "
                f"{llm_text} | "
                f"{Path(out_file).name if out_file else ''} |"
            )
        lines.append("")

    def _load_examples_file(self, path: str) -> List[Dict]:
        """例題ファイル(JSON/YAML)を読み込み、簡易検証して返す。キャッシュあり。"""
        if not path:
            return []
        if path in self._examples_cache:
            return self._examples_cache[path]
        ext = (Path(path).suffix or '').lower()
        data = []
        try:
            if ext in ['.yaml', '.yml']:
                import yaml as _yaml
                with open(path, 'r', encoding='utf-8') as f:
                    data = _yaml.safe_load(f) or []
            else:
                import json as _json
                with open(path, 'r', encoding='utf-8') as f:
                    data = _json.load(f) or []
        except Exception as e:
            self.logger.warning(f"例題ファイルの読み込みに失敗: {path} ({e})")
            data = []
        # 検証・整形
        valid: List[Dict] = []
        if isinstance(data, list):
            for item in data:
                try:
                    ga = item.get('group_a') if isinstance(item, dict) else None
                    gb = item.get('group_b') if isinstance(item, dict) else None
                    ans = item.get('answer') if isinstance(item, dict) else None
                    if isinstance(ga, list) and isinstance(gb, list) and isinstance(ans, str):
                        valid.append({'group_a': ga, 'group_b': gb, 'answer': ans})
                except Exception:
                    continue
        self._examples_cache[path] = valid
        return valid
        # ログリンク
        lines.append("## ログ")
        lines.append("")
        try:
            rel_python_log = os.path.relpath(self.run_dir / 'logs/python.log', self.run_dir)
            rel_cli_log = os.path.relpath(self.run_dir / 'logs/cli_run.log', self.run_dir)
            lines.append(f"- Pythonログ: {rel_python_log}")
            lines.append(f"- CLIログ: {rel_cli_log}")
        except Exception:
            pass
        lines.append("")
        # 保存
        md_path = self.run_dir / 'summary.md'
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

    def _write_root_overview(self, summary_data: Dict) -> None:
        """プロジェクトルートresults/に概要Markdownを保存し、詳細へのパスを記載"""
        try:
            root_dir = SCRIPT_DIR.parents[5] / 'experiment_summaries'
        except Exception:
            return
        root_dir.mkdir(parents=True, exist_ok=True)

        # テンプレートを用意（なければ生成）
        template_dir = root_dir / 'template'
        template_dir.mkdir(parents=True, exist_ok=True)
        template_path = template_dir / 'root_overview_template.md'
        if not template_path.exists():
            default_tpl = []
            # 説明コメント（生成物には含めない）
            default_tpl.append("<!-- テンプレ説明: 下記の記号は実行時に置換されます（このコメントは出力に含まれません） -->")
            default_tpl.append("<!-- {{TIMESTAMP}}: 実行時刻(YYYYMMDD_HHMMSS) -->")
            default_tpl.append("<!-- {{RUN_NAME}}: 実験名（configのrun_name。未設定時は設定ファイル名） -->")
            default_tpl.append("<!-- {{DETAIL_DIR_PATH}}: 詳細ディレクトリへの相対パス -->")
            default_tpl.append("<!-- {{DETAIL_SUMMARY_PATH}}: 詳細summary.mdへの相対パス -->")
            default_tpl.append("<!-- {{DETAIL_DIR_MD_LINK}}: [詳細ディレクトリ](相対パス) へのリンク -->")
            default_tpl.append("<!-- {{DETAIL_SUMMARY_MD_LINK}}: [詳細サマリー](相対パス) へのリンク -->")
            default_tpl.append("<!-- {{TOTAL_EXPERIMENTS}}: 総実験数 / {{SUCCESSFUL_EXPERIMENTS}}: 成功数 -->")
            default_tpl.append("<!-- {{RESULTS_TABLE}}: 先頭数件の結果テーブル（データセット/アスペクト/BERT/BLEU） -->")
            # 追加プレースホルダ（任意で使用可）
            default_tpl.append("<!-- 追加: {{DATASET_LIST}}（ユニークなデータセットのカンマ区切り） -->")
            default_tpl.append("<!-- 追加: {{ASPECT_LIST}}（ユニークなアスペクトのカンマ区切り） -->")
            default_tpl.append("<!-- 追加: {{DETAIL_DIR_ABS}}（詳細ディレクトリの絶対パス） -->")
            default_tpl.append("<!-- 追加: {{CONFIG_PATH}}（使用した設定ファイルのパス） -->")
            default_tpl.append("<!-- 追加: {{RUN_DIR_NAME}}（詳細ディレクトリ名のみ） -->")
            default_tpl.append("<!-- 追加: {{LLM_MODEL}}（設定のllm.model） -->")
            default_tpl.append("<!-- 追加: {{RESULT_JSON_PATH}}（バッチ結果JSONの相対パス） -->\n")
            default_tpl.append("# 実験概要 {{TIMESTAMP}}")
            default_tpl.append("")
            default_tpl.append("- 実験名: {{RUN_NAME}}")
            default_tpl.append("- {{DETAIL_DIR_MD_LINK}}")
            default_tpl.append("- {{DETAIL_SUMMARY_MD_LINK}}")
            default_tpl.append("- 総実験数: {{TOTAL_EXPERIMENTS}} / 成功: {{SUCCESSFUL_EXPERIMENTS}}\n")
            default_tpl.append("- データセット: {{DATASET_LIST}}")
            default_tpl.append("- アスペクト: {{ASPECT_LIST}}\n")
            default_tpl.append("## 結果概要")
            default_tpl.append("{{RESULTS_TABLE}}")
            with open(template_path, 'w', encoding='utf-8') as tf:
                tf.write("\n".join(default_tpl))

        # 置換データ作成
        meta = summary_data.get('experiment_meta', {})
        results = summary_data.get('results', [])
        rel_detail_dir = os.path.relpath(self.run_dir, root_dir) if self.run_dir else ''
        rel_detail_summary = os.path.relpath(self.run_dir / 'summary.md', root_dir) if self.run_dir else ''
        results_table = self._build_results_table(results, limit=5)
        # 追加変数を構築
        datasets = sorted({(r.get('experiment_info') or {}).get('dataset', '') for r in results if r.get('experiment_info')})
        aspects = sorted({(r.get('experiment_info') or {}).get('aspect', '') for r in results if r.get('experiment_info')})
        dataset_list = ", ".join([d for d in datasets if d])
        aspect_list = ", ".join([a for a in aspects if a])
        detail_dir_abs = str(self.run_dir) if self.run_dir else ''
        config_path = str(self.config_path)
        run_dir_name = self.run_dir.name if self.run_dir else ''
        llm_model = (self.config.get('llm') or {}).get('model', '')
        result_json_rel = os.path.relpath(self.run_dir / f"batch_experiment_{meta.get('timestamp','')}.json", root_dir) if self.run_dir else ''
        rel_log_dir = os.path.relpath(self.run_dir / 'logs', root_dir) if self.run_dir else ''
        rel_cli_log = os.path.relpath(self.run_dir / 'logs/cli_run.log', root_dir) if self.run_dir else ''

        with open(template_path, 'r', encoding='utf-8') as tf:
            template_lines = tf.read().splitlines()

        # プレースホルダ置換（コメント行は置換しない）
        def apply_replacements(text: str) -> str:
            text = text.replace('{{TIMESTAMP}}', str(meta.get('timestamp', '')))
            text = text.replace('{{RUN_NAME}}', str(self.run_name))
            text = text.replace('{{DETAIL_DIR_PATH}}', rel_detail_dir)
            text = text.replace('{{DETAIL_SUMMARY_PATH}}', rel_detail_summary)
            text = text.replace('{{DETAIL_DIR_MD_LINK}}', f"[詳細ディレクトリ]({rel_detail_dir})")
            text = text.replace('{{DETAIL_SUMMARY_MD_LINK}}', f"[詳細サマリー]({rel_detail_summary})")
            text = text.replace('{{TOTAL_EXPERIMENTS}}', str(meta.get('total_experiments', 0)))
            text = text.replace('{{SUCCESSFUL_EXPERIMENTS}}', str(meta.get('successful_experiments', 0)))
            text = text.replace('{{RESULTS_TABLE}}', results_table)
            # 追加置換
            text = text.replace('{{DATASET_LIST}}', dataset_list)
            text = text.replace('{{ASPECT_LIST}}', aspect_list)
            text = text.replace('{{DETAIL_DIR_ABS}}', detail_dir_abs)
            text = text.replace('{{CONFIG_PATH}}', config_path)
            text = text.replace('{{RUN_DIR_NAME}}', run_dir_name)
            text = text.replace('{{LLM_MODEL}}', llm_model)
            text = text.replace('{{RESULT_JSON_PATH}}', result_json_rel)
            text = text.replace('{{LOG_DIR_PATH}}', rel_log_dir)
            text = text.replace('{{CLI_LOG_PATH}}', rel_cli_log)
            text = text.replace('{{CLI_LOG_MD_LINK}}', f"[CLIログ]({rel_cli_log})")
            return text

        rendered_lines_all = []
        for ln in template_lines:
            if ln.strip().startswith('<!--'):
                # コメント行はそのまま保持（後段で除外）
                rendered_lines_all.append(ln)
            else:
                rendered_lines_all.append(apply_replacements(ln))
        rendered = "\n".join(rendered_lines_all)

        # 出力
        overview_path = root_dir / f"summary_{meta.get('timestamp','')}.md"
        # コメント行(<!-- -->)は概要には含めない
        rendered_lines = [ln for ln in rendered.splitlines() if not ln.strip().startswith('<!--')]
        # 追記: アスペクトごとのLLM出力一覧テーブル
        try:
            outputs_table = self._build_llm_outputs_table(results)
            if outputs_table.strip():
                rendered_lines.append("")
                rendered_lines.append("## LLM出力一覧")
                rendered_lines.append("")
                rendered_lines.extend(outputs_table.splitlines())
        except Exception:
            pass
        with open(overview_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(rendered_lines))

    def _build_results_table(self, results: List[Dict], limit: int = 5) -> str:
        """結果テーブルMarkdownを作成"""
        lines = []
        lines.append("| データセット | アスペクト | BERT | BLEU |")
        lines.append("| --- | --- | ---:| ---:|")
        for r in results[:limit]:
            info = r.get('experiment_info', {})
            evals = r.get('evaluation', {})
            aspect_name = info.get('aspect', '')
            aspect_display = aspect_name
            try:
                if info.get('use_aspect_descriptions') and info.get('aspect_descriptions_file'):
                    csv_path = str(info.get('aspect_descriptions_file'))
                    desc_map = self._load_aspect_descriptions(csv_path)
                    desc_text = desc_map.get(aspect_name, '')
                    if desc_text:
                        aspect_display = f"({aspect_name}) {desc_text}"
            except Exception:
                pass
            lines.append(
                f"| {info.get('dataset','')} | {aspect_display} | {evals.get('bert_score',0):.4f} | {evals.get('bleu_score',0):.4f} |"
            )
        return "\n".join(lines)

    def _build_llm_outputs_table(self, results: List[Dict], limit: Optional[int] = None) -> str:
        """LLM出力をアスペクトごとに一覧化する表（ルート概要用）"""
        if not results:
            return ""
        rows = results if limit is None else results[:limit]
        lines: List[str] = []
        lines.append("| データセット | アスペクト | LLM出力 |")
        lines.append("| --- | --- | --- |")
        for r in rows:
            info = r.get('experiment_info', {}) or {}
            dataset = info.get('dataset', '')
            aspect_name = info.get('aspect', '')
            aspect_display = aspect_name
            try:
                if info.get('use_aspect_descriptions') and info.get('aspect_descriptions_file'):
                    csv_path = str(info.get('aspect_descriptions_file'))
                    desc_map = self._load_aspect_descriptions(csv_path)
                    desc_text = desc_map.get(aspect_name, '')
                    if desc_text:
                        aspect_display = f"({aspect_name}) {desc_text}"
            except Exception:
                pass
            llm_text = ((r.get('process') or {}).get('llm_response') or '')
            llm_text = llm_text.replace("\n", " ").replace("|", "｜").strip()
            if len(llm_text) > 200:
                llm_text = llm_text[:197] + "..."
            lines.append(f"| {dataset} | {aspect_display} | {llm_text} |")
        return "\n".join(lines)

    def _load_aspect_descriptions(self, csv_path: str) -> Dict[str, str]:
        """アスペクト説明CSVを読み込み（パス毎にキャッシュ）"""
        if not csv_path:
            return {}
        if csv_path in self._desc_cache:
            return self._desc_cache[csv_path]
        mapping: Dict[str, str] = {}
        try:
            import csv
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    aspect = (row.get('aspect') or '').strip()
                    desc = (row.get('description') or '').strip()
                    if aspect:
                        mapping[aspect] = desc
        except Exception:
            mapping = {}
        self._desc_cache[csv_path] = mapping
        return mapping
    
    def print_summary(self):
        """実験サマリー表示"""
        if not self.results:
            self.logger.info("実験結果がありません")
            return
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("=== 実験サマリー ===")
        self.logger.info("=" * 60)
        
        total = len(self.results)
        successful = sum(1 for r in self.results if r.get('summary', {}).get('success', False))
        
        self.logger.info(f"総実験数: {total}")
        self.logger.info(f"成功: {successful}")
        self.logger.info(f"失敗: {total - successful}")
        
        # スコアサマリー
        self.logger.info("\n=== スコアサマリー ===")
        for result in self.results:
            if result.get('summary', {}).get('success', False):
                exp_info = result['experiment_info']
                evaluation = result['evaluation']
                
                dataset = exp_info.get('dataset', 'N/A')
                aspect = exp_info.get('aspect', 'N/A')
                bert = evaluation.get('bert_score', 0)
                bleu = evaluation.get('bleu_score', 0)
                
                self.logger.info(f"{dataset:10s} {aspect:15s} BERT: {bert:.4f}  BLEU: {bleu:.4f}")
    
    def run(self) -> bool:
        """パイプライン実行"""
        try:
            # 設定検証
            if not self.validate_config():
                return False
            
            # DatasetManager初期化
            if not self.setup_dataset_manager():
                return False
            
            # バッチ実験実行
            results = self.run_batch_experiments()
            
            # 結果保存
            self.save_results(results)
            
            # サマリー表示
            self.print_summary()
            
            self.logger.info("\n✅ パイプライン実行完了")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ パイプライン実行エラー: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """メイン実行"""
    # デフォルト設定ファイル
    default_config = Path(__file__).parent / "pipeline_config.yaml"
    
    pipeline = ExperimentPipeline(str(default_config), debug=True)
    success = pipeline.run()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())

