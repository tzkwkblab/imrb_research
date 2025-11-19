#!/usr/bin/env python3
"""
実験マトリックスJSONから一括実行スクリプト

実験マトリックスJSONを読み込み、全実験を並列実行する。
"""

import sys
import json
import argparse
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import tempfile
import yaml

# 環境変数読み込み
from dotenv import load_dotenv
load_dotenv()

# パス設定
SCRIPT_DIR = Path(__file__).parent
EXPERIMENTS_DIR = SCRIPT_DIR.parent.parent.parent
PROJECT_ROOT = EXPERIMENTS_DIR.parent.parent
sys.path.insert(0, str(EXPERIMENTS_DIR))

from experiment_pipeline import ExperimentPipeline


def load_experiment_matrix(json_path: str) -> Dict[str, Any]:
    """
    実験マトリックスJSONを読み込む
    
    Args:
        json_path: JSONファイルのパス
        
    Returns:
        実験マトリックス辞書
    """
    path = Path(json_path)
    if not path.exists():
        # プロジェクトルートからの相対パスを試す
        path = PROJECT_ROOT / json_path
        if not path.exists():
            raise FileNotFoundError(f"実験マトリックスJSONが見つかりません: {json_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data


def find_examples_file(dataset: str) -> Optional[str]:
    """
    データセット用の例題ファイルを検索
    
    Args:
        dataset: データセット名
        
    Returns:
        例題ファイルのパス（見つからない場合はNone）
    """
    examples_dir = PROJECT_ROOT / "data" / "analysis-workspace" / "contrast_examples"
    
    # retrieved_conceptsはsteamの例題を使用
    if dataset == "retrieved_concepts":
        dataset = "steam"
    
    dataset_dir = examples_dir / dataset
    if not dataset_dir.exists():
        return None
    
    # JSON/YAMLファイルを検索
    for ext in ['.json', '.yaml', '.yml']:
        files = list(dataset_dir.glob(f"*{ext}"))
        if files:
            # 最初に見つかったファイルを返す
            return str(files[0])
    
    return None


def convert_matrix_to_config(exp_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    実験マトリックス設定をExperimentPipeline用設定に変換
    
    Args:
        exp_config: 実験マトリックスJSONの1実験設定
        
    Returns:
        ExperimentPipeline用設定辞書
    """
    dataset = exp_config['dataset']
    few_shot = exp_config.get('few_shot', 0)
    
    # 例題ファイルの解決
    examples_file = None
    if few_shot > 0:
        examples_file = find_examples_file(dataset)
        if not examples_file:
            logging.warning(f"例題ファイルが見つかりません: {dataset} (few_shot={few_shot})")
    
    config = {
        'experiments': [{
            'dataset': dataset,
            'aspects': [exp_config['aspect']],
            'group_size': exp_config.get('group_size', 300),
            'split_type': exp_config.get('split_type', 'aspect_vs_others')
        }],
        'output': {
            'directory': 'results/',
            'format': 'json',
            'save_intermediate': True
        },
        'llm': {
            'model': exp_config.get('gpt_model', 'gpt-4o-mini'),
            'temperature': 0.7,
            'max_tokens': 100
        },
        'general': {
            'debug_mode': False,
            'console_output': False,
            'silent_mode': False,
            'use_aspect_descriptions': False,
            'aspect_descriptions_file': None,
            'use_examples': few_shot > 0,
            'examples_file': examples_file,
            'max_examples': few_shot if few_shot > 0 else None
        },
        'evaluation': {
            'use_llm_score': exp_config.get('use_llm_evaluation', True),
            'llm_evaluation_model': exp_config.get('llm_evaluation_model', 'gpt-4o-mini'),
            'llm_evaluation_temperature': 0.0
        }
    }
    
    return config


def run_single_experiment_wrapper(args: Tuple[Dict[str, Any], str, Path]) -> Dict[str, Any]:
    """
    単一実験実行ラッパー（並列実行用）
    
    Args:
        args: (exp_config, experiment_id, output_dir)のタプル
        
    Returns:
        実験結果辞書
    """
    exp_config, experiment_id, output_dir = args
    
    try:
        # 一時設定ファイルを作成
        config_dict = convert_matrix_to_config(exp_config)
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            encoding='utf-8'
        ) as tmp:
            yaml.dump(config_dict, tmp, allow_unicode=True)
            tmp_config_path = tmp.name
        
        try:
            # ExperimentPipelineを初期化して実行
            pipeline = ExperimentPipeline(
                config_path=tmp_config_path,
                debug=False,
                silent=False
            )
            
            # データセットマネージャーをセットアップ
            if not pipeline.setup_dataset_manager():
                raise RuntimeError("DatasetManagerのセットアップに失敗")
            
            # 単一実験実行
            dataset = exp_config['dataset']
            aspect = exp_config['aspect']
            group_size = exp_config.get('group_size', 300)
            split_type = exp_config.get('split_type', 'aspect_vs_others')
            
            result = pipeline.run_single_experiment(
                dataset=dataset,
                aspect=aspect,
                group_size=group_size,
                split_type=split_type,
                output_dir=output_dir
            )
            
            if result:
                # 実験IDとメタデータを追加
                result['experiment_info']['experiment_id'] = experiment_id
                result['experiment_info']['few_shot'] = exp_config.get('few_shot', 0)
                result['experiment_info']['gpt_model'] = exp_config.get('gpt_model', 'gpt-4o-mini')
                result['experiment_info']['domain'] = exp_config.get('domain')
                result['success'] = True
            else:
                result = {
                    'experiment_info': {
                        'experiment_id': experiment_id,
                        'error': '実験実行がNoneを返しました'
                    },
                    'success': False
                }
            
            return result
            
        finally:
            # 一時ファイルを削除
            try:
                os.unlink(tmp_config_path)
            except Exception:
                pass
                
    except Exception as e:
        logging.error(f"実験実行エラー ({experiment_id}): {e}")
        import traceback
        traceback.print_exc()
        return {
            'experiment_info': {
                'experiment_id': experiment_id,
                'error': str(e)
            },
            'success': False
        }


def run_parallel_experiments(
    experiments: List[Dict[str, Any]],
    output_dir: Path,
    max_workers: int = None
) -> List[Dict[str, Any]]:
    """
    並列実行で実験を実行
    
    Args:
        experiments: 実験設定のリスト
        output_dir: 出力ディレクトリ
        max_workers: 最大並列数（Noneの場合はCPUコア数、最大8）
        
    Returns:
        実験結果のリスト
    """
    import multiprocessing
    
    if max_workers is None:
        max_workers = min(multiprocessing.cpu_count(), 8)
    
    # 実験IDごとの出力ディレクトリを作成
    exp_output_dir = output_dir / "experiments"
    exp_output_dir.mkdir(parents=True, exist_ok=True)
    
    # 実行引数を準備
    args_list = [
        (exp, exp['experiment_id'], exp_output_dir / exp['experiment_id'])
        for exp in experiments
    ]
    
    results = []
    failed_experiments = []
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # タスクを送信
        future_to_exp = {
            executor.submit(run_single_experiment_wrapper, args): args[1]
            for args in args_list
        }
        
        # 進捗バーで結果を取得
        with tqdm(total=len(experiments), desc="実験実行中") as pbar:
            for future in as_completed(future_to_exp):
                experiment_id = future_to_exp[future]
                try:
                    result = future.result()
                    results.append(result)
                    if not result.get('success', False):
                        failed_experiments.append(experiment_id)
                except Exception as e:
                    logging.error(f"実験結果取得エラー ({experiment_id}): {e}")
                    results.append({
                        'experiment_info': {
                            'experiment_id': experiment_id,
                            'error': f'結果取得エラー: {str(e)}'
                        },
                        'success': False
                    })
                    failed_experiments.append(experiment_id)
                finally:
                    pbar.update(1)
    
    if failed_experiments:
        logging.warning(f"失敗した実験: {len(failed_experiments)}件")
        logging.warning(f"失敗実験ID: {failed_experiments[:10]}...")
    
    return results


def save_results(
    results: List[Dict[str, Any]],
    output_dir: Path,
    experiment_plan: Dict[str, Any]
) -> None:
    """
    結果を保存
    
    Args:
        results: 実験結果のリスト
        output_dir: 出力ディレクトリ
        experiment_plan: 実験計画情報
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 統合結果JSONを保存
    batch_results = {
        'experiment_plan': experiment_plan,
        'execution_info': {
            'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'total_experiments': len(results),
            'successful_experiments': sum(1 for r in results if r.get('success', False)),
            'failed_experiments': sum(1 for r in results if not r.get('success', False))
        },
        'results': results
    }
    
    batch_json_path = output_dir / "batch_results.json"
    with open(batch_json_path, 'w', encoding='utf-8') as f:
        json.dump(batch_results, f, ensure_ascii=False, indent=2)
    
    logging.info(f"統合結果を保存: {batch_json_path}")
    
    # 個別結果JSONを保存
    individual_dir = output_dir / "individual"
    individual_dir.mkdir(parents=True, exist_ok=True)
    
    for result in results:
        exp_id = result.get('experiment_info', {}).get('experiment_id', 'unknown')
        if exp_id == 'unknown':
            continue
        
        individual_json_path = individual_dir / f"{exp_id}.json"
        with open(individual_json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    logging.info(f"個別結果を保存: {individual_dir} ({len(results)}件)")


def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(
        description="実験マトリックスJSONから一括実行",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--matrix', '-m',
        type=str,
        default='実験マトリックス.json',
        help='実験マトリックスJSONファイルのパス (default: 実験マトリックス.json)'
    )
    
    parser.add_argument(
        '--workers', '-w',
        type=int,
        default=None,
        help='並列実行数 (default: CPUコア数、最大8)'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default=None,
        help='出力ディレクトリ (default: results/{timestamp})'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='デバッグモード'
    )
    
    args = parser.parse_args()
    
    # ログ設定
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        # 実験マトリックスを読み込み
        logger.info(f"実験マトリックスを読み込み: {args.matrix}")
        matrix_data = load_experiment_matrix(args.matrix)
        
        experiments = matrix_data.get('experiments', [])
        experiment_plan = matrix_data.get('experiment_plan', {})
        
        logger.info(f"実験数: {len(experiments)}")
        
        # 出力ディレクトリを設定
        if args.output_dir:
            output_dir = Path(args.output_dir)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("results") / timestamp
        
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"出力ディレクトリ: {output_dir}")
        
        # 並列実行
        logger.info(f"並列実行開始 (workers={args.workers or 'auto'})")
        results = run_parallel_experiments(
            experiments=experiments,
            output_dir=output_dir,
            max_workers=args.workers
        )
        
        # 結果を保存
        logger.info("結果を保存中...")
        save_results(results, output_dir, experiment_plan)
        
        # サマリー表示
        successful = sum(1 for r in results if r.get('success', False))
        failed = len(results) - successful
        
        logger.info("=" * 60)
        logger.info("実行完了")
        logger.info(f"成功: {successful}件")
        logger.info(f"失敗: {failed}件")
        logger.info(f"結果ディレクトリ: {output_dir}")
        logger.info("=" * 60)
        
        return 0 if failed == 0 else 1
        
    except KeyboardInterrupt:
        logger.warning("実行が中断されました")
        return 130
        
    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

