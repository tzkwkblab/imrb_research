#!/usr/bin/env python3
"""
統合対比因子生成実験：新しいutils統合ツール活用版

【実装内容】
- DatasetManager.from_config()による設定ファイル駆動
- ContrastFactorAnalyzerによる統合分析
- 3フェーズ実験パターン（データ準備→実験実行→結果分析）
- 3データセット×アスペクト×Few-shot設定の包括的実験
- JSON・Markdown形式での結果出力

【評価指標】
- BERTスコア（意味類似度・主要指標）
- BLEUスコア（表層一致度・主要指標）
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from tqdm import tqdm

# Utils統合パス設定
utils_dir = Path(__file__).parent.parent.parent / "utils"
sys.path.append(str(utils_dir))

# 新しいutils完全活用
from dataset_manager import DatasetManager
from contrast_factor_analyzer import ContrastFactorAnalyzer
from config import DatasetConfig, ConfigValidator

# 実験固有設定
from experiment_config import CONFIG

# 基本設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class UnifiedContrastExperiment:
    """統合対比因子生成実験クラス"""
    
    def __init__(self, config=CONFIG):
        """
        初期化
        Args:
            config: 実験設定オブジェクト
        """
        self.config = config
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 結果保存用
        self.results = []
        self.summary_stats = {}
        self.errors = []
        
        # コンポーネント初期化（遅延ロード）
        self.dataset_manager = None
        self.contrast_analyzer = None
    
    def _initialize_components(self):
        """コンポーネント初期化（遅延ロード）"""
        if self.dataset_manager is None:
            logger.info("DatasetManager初期化（設定ファイル駆動）")
            self.dataset_manager = DatasetManager.from_config()
        
        if self.contrast_analyzer is None:
            logger.info("ContrastFactorAnalyzer初期化")
            self.contrast_analyzer = ContrastFactorAnalyzer(debug=self.config.debug_mode)
    
    def phase1_data_preparation(self) -> Dict:
        """Phase 1: データ準備"""
        logger.info("=== Phase 1: データ準備開始 ===")
        
        self._initialize_components()
        
        # 1. 設定検証
        logger.info("Step 1: 設定検証")
        validation_result = self.dataset_manager.validate_configuration()
        logger.info(f"設定検証結果: {validation_result['status']}")
        
        if validation_result['warnings']:
            for warning in validation_result['warnings']:
                logger.warning(f"設定警告: {warning}")
        
        # 2. データセット利用可能性確認
        logger.info("Step 2: データセット利用可能性確認")
        available_datasets = self.dataset_manager.list_available_datasets()
        
        accessible_datasets = []
        for dataset_id in self.config.target_datasets:
            if dataset_id in available_datasets:
                info = available_datasets[dataset_id]
                if info.get('accessible', False):
                    accessible_datasets.append(dataset_id)
                    logger.info(f"✅ {dataset_id}: アクセス可能")
                else:
                    logger.warning(f"❌ {dataset_id}: アクセス不可 - {info.get('warnings', ['不明なエラー'])[0]}")
            else:
                logger.error(f"❌ {dataset_id}: 設定なし")
        
        # 3. 各データセットの統計情報取得
        logger.info("Step 3: データセット統計情報取得")
        dataset_stats = {}
        for dataset_id in accessible_datasets:
            try:
                stats = self.dataset_manager.get_data_statistics(dataset_id)
                dataset_stats[dataset_id] = stats
                logger.info(f"{dataset_id}: {stats.get('total_samples', 'N/A')}サンプル")
            except Exception as e:
                logger.error(f"{dataset_id}統計取得エラー: {e}")
        
        # 4. 実験マトリックス生成
        logger.info("Step 4: 実験マトリックス生成")
        experiment_matrix = []
        
        for exp_def in self.config.get_experiment_matrix():
            dataset_id = exp_def['dataset_id']
            if dataset_id in accessible_datasets:
                experiment_matrix.append(exp_def)
            else:
                logger.warning(f"実験スキップ: {exp_def['experiment_id']} (データセット利用不可)")
        
        phase1_result = {
            "validation": validation_result,
            "accessible_datasets": accessible_datasets,
            "dataset_stats": dataset_stats,
            "experiment_matrix": experiment_matrix,
            "total_experiments": len(experiment_matrix)
        }
        
        logger.info(f"Phase 1完了: {len(experiment_matrix)}実験を実行予定")
        return phase1_result
    
    def phase2_contrast_experiment(self, phase1_result: Dict) -> List[Dict]:
        """Phase 2: 対比実験実行"""
        logger.info("=== Phase 2: 対比実験実行開始 ===")
        
        experiment_matrix = phase1_result['experiment_matrix']
        results = []
        
        with tqdm(total=len(experiment_matrix), desc="実験進行") as pbar:
            for i, exp_def in enumerate(experiment_matrix):
                pbar.set_description(f"実験 {i+1}/{len(experiment_matrix)}: {exp_def['experiment_id']}")
                
                try:
                    result = self._execute_single_experiment(exp_def)
                    results.append(result)
                    
                    if self.config.save_intermediate:
                        self._save_intermediate_result(result, exp_def['experiment_id'])
                    
                except Exception as e:
                    error_msg = f"実験失敗 {exp_def['experiment_id']}: {e}"
                    logger.error(error_msg)
                    self.errors.append({
                        "experiment_id": exp_def['experiment_id'],
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                
                pbar.update(1)
        
        logger.info(f"Phase 2完了: {len(results)}実験成功, {len(self.errors)}実験失敗")
        return results
    
    def _execute_single_experiment(self, exp_def: Dict) -> Dict:
        """単一実験実行"""
        dataset_id = exp_def['dataset_id']
        domain = exp_def['domain']
        aspect = exp_def['aspect']
        shot_setting = exp_def['shot_setting']
        split_type = exp_def['split_type']
        group_size = exp_def['group_size']
        
        # データ分割取得
        if domain:
            splits = self.dataset_manager.get_binary_splits(
                dataset_id=dataset_id,
                aspect=aspect,
                group_size=group_size,
                split_type=split_type,
                domain=domain
            )
        else:
            splits = self.dataset_manager.get_binary_splits(
                dataset_id=dataset_id,
                aspect=aspect,
                group_size=group_size,
                split_type=split_type
            )
        
        # Few-shot例題作成
        examples = None
        if shot_setting > 0:
            try:
                examples = self.dataset_manager.create_examples(
                    dataset_id=dataset_id,
                    aspect=aspect,
                    shot_count=shot_setting,
                    domain=domain
                )
            except Exception as e:
                logger.warning(f"Few-shot例題作成失敗 {exp_def['experiment_id']}: {e}")
                examples = None
        
        # 対比因子分析実行
        result = self.contrast_analyzer.analyze(
            group_a=splits.group_a,
            group_b=splits.group_b,
            correct_answer=splits.correct_answer,
            examples=examples,
            output_dir=self.config.output_dir,
            experiment_name=exp_def['experiment_id']
        )
        
        # 実験定義を結果に追加
        result['experiment_definition'] = exp_def
        
        return result
    
    def _save_intermediate_result(self, result: Dict, experiment_id: str):
        """中間結果保存"""
        output_path = Path(self.config.output_dir) / f"{experiment_id}_{self.timestamp}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    def phase3_results_analysis(self, phase1_result: Dict, phase2_results: List[Dict]) -> Dict:
        """Phase 3: 結果保存・レポート生成"""
        logger.info("=== Phase 3: 結果分析・保存開始 ===")
        
        # 1. 包括的結果構造化
        comprehensive_results = {
            "experiment_info": {
                "experiment_name": self.config.experiment_name,
                "timestamp": self.timestamp,
                "total_experiments": len(phase2_results),
                "successful_experiments": len(phase2_results),
                "failed_experiments": len(self.errors),
                "target_datasets": self.config.target_datasets,
                "accessible_datasets": phase1_result['accessible_datasets'],
                "configuration": {
                    "group_size": self.config.group_size,
                    "shot_settings": self.config.shot_settings,
                    "random_seed": self.config.random_seed
                }
            },
            "data_preparation": phase1_result,
            "results": phase2_results,
            "errors": self.errors,
            "summary": self._generate_summary_statistics(phase2_results)
        }
        
        # 2. JSON結果保存
        json_path = Path(self.config.output_dir) / f"unified_contrast_experiment_results_{self.timestamp}.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSON結果保存: {json_path}")
        
        # 3. Markdownレポート生成
        if self.config.generate_report:
            report_content = self._generate_markdown_report(comprehensive_results)
            report_path = Path(self.config.output_dir) / f"experiment_report_{self.timestamp}.md"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"Markdownレポート保存: {report_path}")
            comprehensive_results['report_path'] = str(report_path)
        
        comprehensive_results['json_path'] = str(json_path)
        logger.info("Phase 3完了: 結果分析・保存終了")
        
        return comprehensive_results
    
    def _generate_summary_statistics(self, results: List[Dict]) -> Dict:
        """統計サマリー生成"""
        if not results:
            return {"total_experiments": 0, "success_rate": 0.0}
        
        bert_scores = []
        bleu_scores = []
        dataset_stats = {}
        shot_stats = {}
        
        for result in results:
            # スコア収集
            eval_data = result.get('evaluation', {})
            bert_score = eval_data.get('bert_score')
            bleu_score = eval_data.get('bleu_score')
            
            if bert_score is not None:
                bert_scores.append(bert_score)
            if bleu_score is not None:
                bleu_scores.append(bleu_score)
            
            # データセット別統計
            exp_def = result.get('experiment_definition', {})
            dataset_id = exp_def.get('dataset_id', 'unknown')
            shot_setting = exp_def.get('shot_setting', 0)
            
            if dataset_id not in dataset_stats:
                dataset_stats[dataset_id] = []
            dataset_stats[dataset_id].append(result)
            
            if shot_setting not in shot_stats:
                shot_stats[shot_setting] = []
            shot_stats[shot_setting].append(result)
        
        # 統計計算
        summary = {
            "total_experiments": len(results),
            "success_rate": len(results) / (len(results) + len(self.errors)) if self.errors else 1.0,
            "score_statistics": {
                "bert_score": {
                    "count": len(bert_scores),
                    "mean": sum(bert_scores) / len(bert_scores) if bert_scores else 0.0,
                    "min": min(bert_scores) if bert_scores else 0.0,
                    "max": max(bert_scores) if bert_scores else 0.0
                },
                "bleu_score": {
                    "count": len(bleu_scores),
                    "mean": sum(bleu_scores) / len(bleu_scores) if bleu_scores else 0.0,
                    "min": min(bleu_scores) if bleu_scores else 0.0,
                    "max": max(bleu_scores) if bleu_scores else 0.0
                }
            },
            "dataset_breakdown": {
                dataset_id: len(results_list) 
                for dataset_id, results_list in dataset_stats.items()
            },
            "shot_breakdown": {
                f"{shot}shot": len(results_list)
                for shot, results_list in shot_stats.items()
            }
        }
        
        return summary
    
    def _generate_markdown_report(self, comprehensive_results: Dict) -> str:
        """Markdownレポート生成"""
        exp_info = comprehensive_results['experiment_info']
        summary = comprehensive_results['summary']
        results = comprehensive_results['results']
        
        report = f"""# 統合対比因子生成実験レポート

## 実験概要

| 項目 | 値 |
|------|-----|
| 実験名 | {exp_info['experiment_name']} |
| 実行日時 | {exp_info['timestamp']} |
| 総実験数 | {exp_info['total_experiments']} |
| 成功実験数 | {exp_info['successful_experiments']} |
| 失敗実験数 | {exp_info['failed_experiments']} |
| 成功率 | {summary['success_rate']:.1%} |

## データセット概要

| データセット | 実験数 | 利用可能 |
|-------------|-------|----------|
"""
        
        for dataset_id in exp_info['target_datasets']:
            count = summary['dataset_breakdown'].get(dataset_id, 0)
            accessible = "✅" if dataset_id in exp_info['accessible_datasets'] else "❌"
            report += f"| {dataset_id} | {count} | {accessible} |\n"
        
        report += f"""
## 評価結果サマリー

### BERTスコア（意味類似度・主要指標）
| 統計量 | 値 |
|--------|-----|
| 平均 | {summary['score_statistics']['bert_score']['mean']:.4f} |
| 最小 | {summary['score_statistics']['bert_score']['min']:.4f} |
| 最大 | {summary['score_statistics']['bert_score']['max']:.4f} |
| 有効サンプル数 | {summary['score_statistics']['bert_score']['count']} |

### BLEUスコア（表層一致度・主要指標）
| 統計量 | 値 |
|--------|-----|
| 平均 | {summary['score_statistics']['bleu_score']['mean']:.4f} |
| 最小 | {summary['score_statistics']['bleu_score']['min']:.4f} |
| 最大 | {summary['score_statistics']['bleu_score']['max']:.4f} |
| 有効サンプル数 | {summary['score_statistics']['bleu_score']['count']} |

## Few-shot設定別結果

| Shot設定 | 実験数 |
|----------|-------|
"""
        
        for shot_key, count in summary['shot_breakdown'].items():
            report += f"| {shot_key} | {count} |\n"
        
        report += f"""
## 実験結果詳細

| 実験ID | データセット | アスペクト | Shot設定 | BERTスコア | BLEUスコア |
|--------|-------------|----------|----------|-----------|-----------|
"""
        
        for result in results[:20]:  # 最初の20件のみ表示
            exp_def = result.get('experiment_definition', {})
            eval_data = result.get('evaluation', {})
            
            experiment_id = exp_def.get('experiment_id', 'N/A')
            dataset_id = exp_def.get('dataset_id', 'N/A')
            aspect = exp_def.get('aspect', 'N/A')
            shot_setting = exp_def.get('shot_setting', 'N/A')
            bert_score = eval_data.get('bert_score', 0.0)
            bleu_score = eval_data.get('bleu_score', 0.0)
            
            report += f"| {experiment_id} | {dataset_id} | {aspect} | {shot_setting}shot | {bert_score:.4f} | {bleu_score:.4f} |\n"
        
        if len(results) > 20:
            report += f"\n*他{len(results)-20}実験の結果は省略*\n"
        
        if comprehensive_results['errors']:
            report += f"""
## エラー・失敗ケース

| 実験ID | エラー内容 |
|--------|-----------|
"""
            for error in comprehensive_results['errors'][:10]:  # 最初の10件のみ
                report += f"| {error['experiment_id']} | {error['error']} |\n"
        
        report += f"""
## 実験結論

この実験では、新しいutils統合ツール（DatasetManager・ContrastFactorAnalyzer）を活用して、
{exp_info['total_experiments']}の対比因子生成実験を実行しました。

**主要指標結果:**
- **BERTスコア平均**: {summary['score_statistics']['bert_score']['mean']:.4f} (意味類似度)
- **BLEUスコア平均**: {summary['score_statistics']['bleu_score']['mean']:.4f} (表層一致度)

**技術的成果:**
- 設定ファイル駆動による実験管理の実現
- 3フェーズ構造による組織化された実験フロー
- 複数データセット横断での統一的分析
- 自動レポート生成による結果可視化

実験ログファイル: `{comprehensive_results.get('json_path', 'N/A')}`
"""
        
        return report
    
    def run_full_experiment(self) -> Dict:
        """完全実験実行"""
        logger.info(f"統合対比因子生成実験開始: {self.config.experiment_name}")
        logger.info(f"推定実行時間: {self.config.get_estimated_time()}")
        
        try:
            # Phase 1: データ準備
            phase1_result = self.phase1_data_preparation()
            
            # Phase 2: 対比実験実行
            phase2_results = self.phase2_contrast_experiment(phase1_result)
            
            # Phase 3: 結果分析・保存
            final_results = self.phase3_results_analysis(phase1_result, phase2_results)
            
            logger.info("=== 実験完了 ===")
            logger.info(f"総実験数: {final_results['experiment_info']['total_experiments']}")
            logger.info(f"成功実験数: {final_results['experiment_info']['successful_experiments']}")
            logger.info(f"平均BERTスコア: {final_results['summary']['score_statistics']['bert_score']['mean']:.4f}")
            logger.info(f"平均BLEUスコア: {final_results['summary']['score_statistics']['bleu_score']['mean']:.4f}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"実験実行中にエラー発生: {e}")
            raise


def main():
    """メイン実行関数"""
    print("=== 統合対比因子生成実験：新しいutils統合ツール活用版 ===")
    
    # 実験設定確認
    print(f"\n📋 実験設定:")
    print(f"  実験名: {CONFIG.experiment_name}")
    print(f"  対象データセット: {CONFIG.target_datasets}")
    print(f"  総実験数: {CONFIG.get_total_experiments()}")
    print(f"  推定実行時間: {CONFIG.get_estimated_time()}")
    
    # 実験実行
    experiment = UnifiedContrastExperiment(CONFIG)
    
    try:
        results = experiment.run_full_experiment()
        
        print(f"\n✅ 実験完了!")
        print(f"  成功実験数: {results['experiment_info']['successful_experiments']}")
        print(f"  平均BERTスコア: {results['summary']['score_statistics']['bert_score']['mean']:.4f}")
        print(f"  平均BLEUスコア: {results['summary']['score_statistics']['bleu_score']['mean']:.4f}")
        print(f"  結果ファイル: {results.get('json_path', 'N/A')}")
        
        if 'report_path' in results:
            print(f"  レポート: {results['report_path']}")
        
    except Exception as e:
        print(f"\n❌ 実験失敗: {e}")
        logger.exception("実験実行エラー")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 