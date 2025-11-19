#!/usr/bin/env python3
"""
実験結果整理スクリプト

メイン実験とサブ実験を分類し、解析用に整理されたディレクトリ構造を作成する。
"""

import json
import shutil
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_experiment_matrix(matrix_path: str) -> Dict[str, Any]:
    """実験マトリックスを読み込み"""
    with open(matrix_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def classify_experiments(experiments: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
    """
    メイン実験とサブ実験を分類
    
    メイン実験の条件:
    - group_size=100
    - few_shot=1
    - gpt_model="gpt-4o-mini"
    - datasetがretrieved_concepts以外
    - experiment_idに"group_size"が含まれない（Steamのサブ実験を除外）
    
    サブ実験:
    - 上記以外すべて
    """
    main_experiments = []
    sub_experiments = []
    
    for exp in experiments:
        exp_id = exp.get('experiment_id', '')
        dataset = exp.get('dataset', '')
        group_size = exp.get('group_size', 0)
        few_shot = exp.get('few_shot', 0)
        gpt_model = exp.get('gpt_model', '')
        
        # メイン実験の条件
        is_main = (
            group_size == 100 and
            few_shot == 1 and
            gpt_model == 'gpt-4o-mini' and
            dataset != 'retrieved_concepts' and
            'group_size' not in exp_id
        )
        
        if is_main:
            main_experiments.append(exp)
        else:
            sub_experiments.append(exp)
    
    return main_experiments, sub_experiments


def find_result_files(results_dir: Path) -> Dict[str, Path]:
    """
    実験IDから結果ファイルパスへのマッピングを作成
    
    Returns:
        {experiment_id: result_file_path}
    """
    experiment_files = {}
    
    # experimentsディレクトリから検索
    experiments_dir = results_dir / "experiments"
    if experiments_dir.exists():
        for exp_dir in experiments_dir.iterdir():
            if not exp_dir.is_dir():
                continue
            
            # ディレクトリ内のJSONファイルを検索
            json_files = list(exp_dir.glob("*.json"))
            if json_files:
                # 最初のJSONファイルを使用（通常は1つ）
                experiment_files[exp_dir.name] = json_files[0]
    
    # individualディレクトリからも検索（experimentsディレクトリにない場合）
    individual_dir = results_dir / "individual"
    if individual_dir.exists():
        for json_file in individual_dir.glob("*.json"):
            # ファイル名から実験IDを抽出（拡張子を除く）
            exp_id = json_file.stem
            if exp_id not in experiment_files:
                experiment_files[exp_id] = json_file
    
    return experiment_files


def create_analysis_structure(
    base_output_dir: Path,
    main_experiments: List[Dict],
    sub_experiments: List[Dict],
    experiment_files: Dict[str, Path],
    experiment_plan: Dict[str, Any]
) -> Dict[str, Any]:
    """
    解析用ディレクトリ構造を作成
    
    構造:
    analysis_workspace/
    ├── main_experiments/
    │   ├── by_dataset/
    │   │   ├── steam/
    │   │   ├── amazon/
    │   │   ├── goemotions/
    │   │   └── semeval/
    │   └── experiment_list.json
    ├── sub_experiments/
    │   ├── steam_group_size/
    │   ├── steam_gpt51/
    │   ├── retrieved_concepts/
    │   └── experiment_list.json
    └── metadata.json
    """
    workspace_dir = base_output_dir / "analysis_workspace"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    
    # メイン実験の整理
    main_dir = workspace_dir / "main_experiments"
    main_dir.mkdir(exist_ok=True)
    main_by_dataset = main_dir / "by_dataset"
    main_by_dataset.mkdir(exist_ok=True)
    
    main_list = []
    main_by_dataset_dict = defaultdict(list)
    
    for exp in main_experiments:
        exp_id = exp.get('experiment_id', '')
        dataset = exp.get('dataset', 'unknown')
        result_file = experiment_files.get(exp_id)
        
        if result_file:
            # データセット別ディレクトリにコピー
            dataset_dir = main_by_dataset / dataset
            dataset_dir.mkdir(exist_ok=True)
            
            dest_file = dataset_dir / f"{exp_id}.json"
            shutil.copy2(result_file, dest_file)
            
            main_by_dataset_dict[dataset].append({
                'experiment_id': exp_id,
                'file_path': str(dest_file.relative_to(base_output_dir)),
                'config': exp
            })
        
        main_list.append({
            'experiment_id': exp_id,
            'file_path': str(result_file.relative_to(base_output_dir)) if result_file else None,
            'config': exp
        })
    
    # メイン実験リストを保存
    with open(main_dir / "experiment_list.json", 'w', encoding='utf-8') as f:
        json.dump({
            'total': len(main_list),
            'by_dataset': dict(main_by_dataset_dict),
            'experiments': main_list
        }, f, ensure_ascii=False, indent=2)
    
    # サブ実験の整理
    sub_dir = workspace_dir / "sub_experiments"
    sub_dir.mkdir(exist_ok=True)
    
    # サブ実験をカテゴリ別に分類
    steam_group_size = []
    steam_gpt51 = []
    retrieved_concepts = []
    other_sub = []
    
    for exp in sub_experiments:
        exp_id = exp.get('experiment_id', '')
        dataset = exp.get('dataset', '')
        gpt_model = exp.get('gpt_model', '')
        result_file = experiment_files.get(exp_id)
        
        exp_info = {
            'experiment_id': exp_id,
            'file_path': str(result_file.relative_to(base_output_dir)) if result_file else None,
            'source_file': str(result_file) if result_file else None,
            'config': exp
        }
        
        if dataset == 'steam' and 'group_size' in exp_id:
            if gpt_model == 'gpt-5.1':
                steam_gpt51.append(exp_info)
            else:
                steam_group_size.append(exp_info)
        elif dataset == 'retrieved_concepts':
            retrieved_concepts.append(exp_info)
        else:
            other_sub.append(exp_info)
    
    # サブ実験カテゴリ別ディレクトリ作成
    if steam_group_size:
        steam_gs_dir = sub_dir / "steam_group_size"
        steam_gs_dir.mkdir(exist_ok=True)
        for exp_info in steam_group_size:
            if exp_info.get('source_file'):
                src_file = Path(exp_info['source_file'])
                if src_file.exists():
                    dest_file = steam_gs_dir / f"{exp_info['experiment_id']}.json"
                    shutil.copy2(src_file, dest_file)
                    exp_info['file_path'] = str(dest_file.relative_to(base_output_dir))
                    del exp_info['source_file']
    
    if steam_gpt51:
        steam_g51_dir = sub_dir / "steam_gpt51"
        steam_g51_dir.mkdir(exist_ok=True)
        for exp_info in steam_gpt51:
            if exp_info.get('source_file'):
                src_file = Path(exp_info['source_file'])
                if src_file.exists():
                    dest_file = steam_g51_dir / f"{exp_info['experiment_id']}.json"
                    shutil.copy2(src_file, dest_file)
                    exp_info['file_path'] = str(dest_file.relative_to(base_output_dir))
                    del exp_info['source_file']
    
    if retrieved_concepts:
        rc_dir = sub_dir / "retrieved_concepts"
        rc_dir.mkdir(exist_ok=True)
        for exp_info in retrieved_concepts:
            if exp_info.get('source_file'):
                src_file = Path(exp_info['source_file'])
                if src_file.exists():
                    dest_file = rc_dir / f"{exp_info['experiment_id']}.json"
                    shutil.copy2(src_file, dest_file)
                    exp_info['file_path'] = str(dest_file.relative_to(base_output_dir))
                    del exp_info['source_file']
    
    # サブ実験リストを保存
    with open(sub_dir / "experiment_list.json", 'w', encoding='utf-8') as f:
        json.dump({
            'total': len(sub_experiments),
            'categories': {
                'steam_group_size': {
                    'count': len(steam_group_size),
                    'experiments': steam_group_size
                },
                'steam_gpt51': {
                    'count': len(steam_gpt51),
                    'experiments': steam_gpt51
                },
                'retrieved_concepts': {
                    'count': len(retrieved_concepts),
                    'experiments': retrieved_concepts
                },
                'other': {
                    'count': len(other_sub),
                    'experiments': other_sub
                }
            },
            'all_experiments': sub_experiments
        }, f, ensure_ascii=False, indent=2)
    
    # メタデータを保存
    metadata = {
        'created_at': datetime.now().strftime("%Y%m%d_%H%M%S"),
        'source_results_dir': str(base_output_dir),
        'experiment_plan': experiment_plan,
        'summary': {
            'main_experiments': len(main_experiments),
            'sub_experiments': len(sub_experiments),
            'main_by_dataset': {k: len(v) for k, v in main_by_dataset_dict.items()},
            'sub_categories': {
                'steam_group_size': len(steam_group_size),
                'steam_gpt51': len(steam_gpt51),
                'retrieved_concepts': len(retrieved_concepts),
                'other': len(other_sub)
            }
        }
    }
    
    with open(workspace_dir / "metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return metadata


def main():
    parser = argparse.ArgumentParser(description='実験結果を整理して解析用ディレクトリ構造を作成')
    parser.add_argument('--results-dir', type=str, required=True,
                       help='結果ディレクトリのパス（例: results/20251119_153853）')
    parser.add_argument('--matrix', type=str, default='実験マトリックス.json',
                       help='実験マトリックスJSONファイルのパス')
    parser.add_argument('--dry-run', action='store_true',
                       help='実際にファイルをコピーせず、分類のみ実行')
    
    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        logger.error(f"結果ディレクトリが見つかりません: {results_dir}")
        return 1
    
    # 実験マトリックスを読み込み
    matrix_path = Path(args.matrix)
    if not matrix_path.exists():
        matrix_path = results_dir.parent.parent.parent.parent.parent / args.matrix
        if not matrix_path.exists():
            logger.error(f"実験マトリックスが見つかりません: {args.matrix}")
            return 1
    
    logger.info(f"実験マトリックスを読み込み: {matrix_path}")
    matrix_data = load_experiment_matrix(str(matrix_path))
    experiments = matrix_data.get('experiments', [])
    experiment_plan = matrix_data.get('experiment_plan', {})
    
    # 実験を分類
    logger.info("実験を分類中...")
    main_experiments, sub_experiments = classify_experiments(experiments)
    logger.info(f"メイン実験: {len(main_experiments)}件")
    logger.info(f"サブ実験: {len(sub_experiments)}件")
    
    # 結果ファイルを検索
    logger.info("結果ファイルを検索中...")
    experiment_files = find_result_files(results_dir)
    logger.info(f"見つかった結果ファイル: {len(experiment_files)}件")
    
    if args.dry_run:
        logger.info("DRY RUNモード: ファイルはコピーしません")
        logger.info(f"メイン実験ID: {[e.get('experiment_id') for e in main_experiments[:5]]}")
        logger.info(f"サブ実験ID: {[e.get('experiment_id') for e in sub_experiments[:5]]}")
        return 0
    
    # 解析用ディレクトリ構造を作成
    logger.info("解析用ディレクトリ構造を作成中...")
    metadata = create_analysis_structure(
        results_dir,
        main_experiments,
        sub_experiments,
        experiment_files,
        experiment_plan
    )
    
    logger.info("=" * 60)
    logger.info("整理完了")
    logger.info(f"出力ディレクトリ: {results_dir / 'analysis_workspace'}")
    logger.info(f"メイン実験: {metadata['summary']['main_experiments']}件")
    logger.info(f"サブ実験: {metadata['summary']['sub_experiments']}件")
    logger.info("=" * 60)
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

