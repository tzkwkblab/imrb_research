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
            
            analyzer = ContrastFactorAnalyzer(debug=self.debug)
            
            result = analyzer.analyze(
                group_a=splits.group_a,
                group_b=splits.group_b,
                correct_answer=splits.correct_answer,
                output_dir=str(out_dir),
                experiment_name=experiment_id
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
        # スクリプト直下のresultsに時刻ディレクトリ作成（experiments/{YYYY}/{MM}/{DD}/results/時刻）
        base_output_dir = SCRIPT_DIR / "results"
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
            base_output_dir = SCRIPT_DIR / "results"
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
        lines.append("| データセット | アスペクト | BERT | BLEU | 品質 | 出力ファイル |")
        lines.append("| --- | --- | ---:| ---:| --- | --- |")
        for r in results:
            if not r.get('summary', {}).get('success', False):
                continue
            info = r.get('experiment_info', {})
            evals = r.get('evaluation', {})
            out_file = r.get('output_file', '')
            lines.append(
                f"| {info.get('dataset','')} | {info.get('aspect','')} | "
                f"{evals.get('bert_score',0):.4f} | {evals.get('bleu_score',0):.4f} | "
                f"{r.get('summary',{}).get('quality_assessment',{}).get('overall_quality','')} | "
                f"{Path(out_file).name if out_file else ''} |"
            )
        lines.append("")
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
            root_dir = SCRIPT_DIR.parents[5] / 'results'
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
            template = tf.read()

        # プレースホルダ置換
        rendered = template
        rendered = rendered.replace('{{TIMESTAMP}}', str(meta.get('timestamp', '')))
        rendered = rendered.replace('{{RUN_NAME}}', str(self.run_name))
        rendered = rendered.replace('{{DETAIL_DIR_PATH}}', rel_detail_dir)
        rendered = rendered.replace('{{DETAIL_SUMMARY_PATH}}', rel_detail_summary)
        rendered = rendered.replace('{{DETAIL_DIR_MD_LINK}}', f"[詳細ディレクトリ]({rel_detail_dir})")
        rendered = rendered.replace('{{DETAIL_SUMMARY_MD_LINK}}', f"[詳細サマリー]({rel_detail_summary})")
        rendered = rendered.replace('{{TOTAL_EXPERIMENTS}}', str(meta.get('total_experiments', 0)))
        rendered = rendered.replace('{{SUCCESSFUL_EXPERIMENTS}}', str(meta.get('successful_experiments', 0)))
        rendered = rendered.replace('{{RESULTS_TABLE}}', results_table)
        # 追加置換
        rendered = rendered.replace('{{DATASET_LIST}}', dataset_list)
        rendered = rendered.replace('{{ASPECT_LIST}}', aspect_list)
        rendered = rendered.replace('{{DETAIL_DIR_ABS}}', detail_dir_abs)
        rendered = rendered.replace('{{CONFIG_PATH}}', config_path)
        rendered = rendered.replace('{{RUN_DIR_NAME}}', run_dir_name)
        rendered = rendered.replace('{{LLM_MODEL}}', llm_model)
        rendered = rendered.replace('{{RESULT_JSON_PATH}}', result_json_rel)
        rendered = rendered.replace('{{LOG_DIR_PATH}}', rel_log_dir)
        rendered = rendered.replace('{{CLI_LOG_PATH}}', rel_cli_log)
        rendered = rendered.replace('{{CLI_LOG_MD_LINK}}', f"[CLIログ]({rel_cli_log})")

        # 出力
        overview_path = root_dir / f"summary_{meta.get('timestamp','')}.md"
        # コメント行(<!-- -->)は概要には含めない
        rendered_lines = [ln for ln in rendered.splitlines() if not ln.strip().startswith('<!--')]
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
            lines.append(
                f"| {info.get('dataset','')} | {info.get('aspect','')} | {evals.get('bert_score',0):.4f} | {evals.get('bleu_score',0):.4f} |"
            )
        return "\n".join(lines)
    
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

