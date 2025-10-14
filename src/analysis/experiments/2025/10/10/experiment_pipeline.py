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
        
    def setup_logging(self):
        """ログ設定"""
        log_level = logging.INFO if self.debug else logging.WARNING
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
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
        split_type: str = "aspect_vs_others"
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
            
            # 出力ディレクトリ設定
            output_dir = Path(self.config['output']['directory'])
            output_dir.mkdir(parents=True, exist_ok=True)
            
            analyzer = ContrastFactorAnalyzer(debug=self.debug)
            
            result = analyzer.analyze(
                group_a=splits.group_a,
                group_b=splits.group_b,
                correct_answer=splits.correct_answer,
                output_dir=str(output_dir),
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
                    split_type=split_type
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
        
        # 出力ディレクトリ設定
        output_dir = Path(self.config['output']['directory'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 統合結果作成
        summary = {
            "experiment_meta": {
                "timestamp": self.timestamp,
                "config_file": str(self.config_path),
                "total_experiments": len(results),
                "successful_experiments": sum(
                    1 for r in results if r.get('summary', {}).get('success', False)
                )
            },
            "results": results
        }
        
        # 保存
        filename = f"batch_experiment_{self.timestamp}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"\n📁 結果保存: {filepath}")
        
        return str(filepath)
    
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

