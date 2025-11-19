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
import time
import gc
import signal
import atexit
import multiprocessing
from pathlib import Path
from datetime import datetime, timedelta
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
# PROJECT_ROOT: src/analysis/experiments/2025/10/10 から6階層上がってプロジェクトルート
# より確実な方法: プロジェクトルートにdataディレクトリがあることを利用
_candidate_root = SCRIPT_DIR
for _ in range(7):  # 最大7階層まで探索
    if (_candidate_root / "data").exists() and (_candidate_root / "data" / "external").exists():
        PROJECT_ROOT = _candidate_root
        break
    _candidate_root = _candidate_root.parent
else:
    # フォールバック: 6階層上がる
    PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(EXPERIMENTS_DIR))

from experiment_pipeline import ExperimentPipeline

# 例題ファイルマッピング設定を読み込み
EXAMPLES_MAPPING_FILE = SCRIPT_DIR / "dataset_examples_mapping.yaml"
_examples_mapping_cache: Optional[Dict[str, Any]] = None

# グローバル変数: プロセスプールとクリーンアップフラグ
_executor: Optional[ProcessPoolExecutor] = None
_cleanup_registered = False
_child_pids: set = set()


def load_examples_mapping() -> Dict[str, Any]:
    """
    例題ファイルマッピング設定を読み込む
    
    Returns:
        マッピング設定辞書
    """
    global _examples_mapping_cache
    if _examples_mapping_cache is not None:
        return _examples_mapping_cache
    
    if EXAMPLES_MAPPING_FILE.exists():
        with open(EXAMPLES_MAPPING_FILE, 'r', encoding='utf-8') as f:
            _examples_mapping_cache = yaml.safe_load(f) or {}
    else:
        _examples_mapping_cache = {}
    
    return _examples_mapping_cache


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
    
    # マッピング設定を読み込み
    mapping_config = load_examples_mapping()
    mappings = mapping_config.get('mappings', {})
    
    # マッピング設定から例題ファイルパスを取得
    if dataset in mappings:
        mapped_path = mappings[dataset]
        if mapped_path is None:
            return None
        
        # 相対パスの場合は絶対パスに変換
        if not Path(mapped_path).is_absolute():
            # 相対パスは examples_dir からの相対パスとして扱う
            full_path = examples_dir / mapped_path
        else:
            full_path = Path(mapped_path)
        
        # パスを正規化して存在確認
        full_path = full_path.resolve()
        if full_path.exists():
            return str(full_path)
        else:
            logging.debug(f"マッピングで指定された例題ファイルが見つかりません: {full_path} (examples_dir={examples_dir})")
            return None
    
    # マッピング設定がない場合は従来の検索方法を使用
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


def find_aspect_descriptions_file(dataset: str) -> Optional[str]:
    """
    データセット用のアスペクト説明文ファイルを検索
    
    Args:
        dataset: データセット名
        
    Returns:
        アスペクト説明文ファイルのパス（見つからない場合はNone）
    """
    descriptions_dir = PROJECT_ROOT / "data" / "analysis-workspace" / "aspect_descriptions"
    
    # データセット別のファイル名マッピング
    file_mapping = {
        'steam': 'descriptions_official.csv',
        'semeval': 'descriptions_official.csv',
        'goemotions': 'descriptions_official.csv',
        'amazon': 'descriptions_official.csv',
        'retrieved_concepts': None  # retrieved_conceptsにはアスペクト説明文がない
    }
    
    if dataset not in file_mapping:
        return None
    
    filename = file_mapping[dataset]
    if filename is None:
        return None
    
    file_path = descriptions_dir / dataset / filename
    if file_path.exists():
        return str(file_path)
    
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
    effective_few_shot = few_shot
    
    if few_shot > 0:
        examples_file = find_examples_file(dataset)
        if not examples_file:
            mapping_config = load_examples_mapping()
            on_not_found = mapping_config.get('default_behavior', {}).get('on_not_found', 'warn')
            
            if on_not_found == "error":
                raise FileNotFoundError(
                    f"例題ファイルが見つかりません: {dataset} (few_shot={few_shot})。"
                    f"マッピング設定を確認してください: {EXAMPLES_MAPPING_FILE}"
                )
            elif on_not_found == "skip":
                logging.warning(f"例題ファイルが見つかりません: {dataset} (few_shot={few_shot})。この実験をスキップします。")
                return None  # スキップする場合はNoneを返す
            else:  # warn
                logging.warning(f"例題ファイルが見つかりません: {dataset} (few_shot={few_shot})。few_shot=0として実行します。")
                effective_few_shot = 0  # few_shot=0として実行
    
    # アスペクト説明文ファイルの解決
    aspect_descriptions_file = find_aspect_descriptions_file(dataset)
    
    # 実験マトリックスJSONで明示的に指定されていればそれを使用、なければfalse（単語を基本とする）
    use_aspect_descriptions = exp_config.get('use_aspect_descriptions', False)
    
    # センテンス比較を有効にする場合のみ説明文ファイルを設定
    if use_aspect_descriptions:
        if aspect_descriptions_file is None:
            logging.warning(f"センテンス比較が指定されましたが、説明文ファイルが見つかりません: {dataset}。単語比較で実行します。")
            use_aspect_descriptions = False
    else:
        # 単語比較の場合、説明文ファイルは使用しない
        aspect_descriptions_file = None
    
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
            'use_aspect_descriptions': use_aspect_descriptions,
            'aspect_descriptions_file': aspect_descriptions_file,
            'use_examples': effective_few_shot > 0,
            'examples_file': examples_file,
            'max_examples': effective_few_shot if effective_few_shot > 0 else None
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


def load_checkpoint(checkpoint_file: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    チェックポイントから進捗を復元
    
    Args:
        checkpoint_file: チェックポイントファイルパス
        
    Returns:
        (完了した結果リスト, 完了した実験IDリスト)
    """
    if not checkpoint_file.exists():
        return [], []
    
    try:
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint_data = json.load(f)
        return checkpoint_data.get('results', []), checkpoint_data.get('completed_ids', [])
    except Exception as e:
        logging.warning(f"チェックポイント読み込みエラー: {e}")
        return [], []


def save_checkpoint(checkpoint_file: Path, results: List[Dict[str, Any]], completed_ids: List[str]):
    """
    チェックポイントを保存
    
    Args:
        checkpoint_file: チェックポイントファイルパス
        results: 完了した結果リスト
        completed_ids: 完了した実験IDリスト
    """
    try:
        checkpoint_data = {
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'completed_ids': completed_ids
        }
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.warning(f"チェックポイント保存エラー: {e}")


def format_timedelta(seconds: float) -> str:
    """秒数を読みやすい形式に変換"""
    td = timedelta(seconds=int(seconds))
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}日")
    if hours > 0:
        parts.append(f"{hours}時間")
    if minutes > 0:
        parts.append(f"{minutes}分")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}秒")
    
    return "".join(parts)


def save_pid(pid_file: Path):
    """PIDファイルを保存"""
    try:
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
        atexit.register(cleanup_pid, pid_file)
    except Exception as e:
        logging.warning(f"PIDファイル保存エラー: {e}")


def cleanup_pid(pid_file: Path):
    """PIDファイルを削除"""
    try:
        if pid_file.exists():
            pid_file.unlink()
    except Exception:
        pass


def cleanup_child_processes():
    """子プロセスをクリーンアップ"""
    global _executor, _child_pids
    
    try:
        current_pid = os.getpid()
        
        if _executor is not None:
            logging.info("子プロセスプールをシャットダウン中...")
            try:
                _executor.shutdown(wait=False, cancel_futures=True)
            except Exception as e:
                logging.warning(f"executor.shutdownエラー: {e}")
            _executor = None
        
        if _child_pids:
            logging.info(f"子プロセス {len(_child_pids)} 個を停止中...")
            for pid in list(_child_pids):
                try:
                    if is_process_running(pid):
                        os.kill(pid, signal.SIGTERM)
                except Exception:
                    pass
            time.sleep(1)
            for pid in list(_child_pids):
                try:
                    if is_process_running(pid):
                        os.kill(pid, signal.SIGKILL)
                except Exception:
                    pass
            _child_pids.clear()
        
        try:
            import psutil
            current = psutil.Process(current_pid)
            children = current.children(recursive=True)
            if children:
                logging.info(f"残っている子プロセス {len(children)} 個を停止中...")
                for child in children:
                    try:
                        child.terminate()
                    except Exception:
                        pass
                time.sleep(1)
                for child in children:
                    try:
                        if child.is_running():
                            child.kill()
                    except Exception:
                        pass
        except ImportError:
            pass
        except Exception as e:
            logging.warning(f"psutilによるクリーンアップエラー: {e}")
            
    except Exception as e:
        logging.warning(f"子プロセスクリーンアップエラー: {e}")


def register_cleanup_handlers():
    """クリーンアップハンドラを登録"""
    global _cleanup_registered
    
    if _cleanup_registered:
        return
    
    def signal_handler(signum, frame):
        logging.warning(f"シグナル {signum} を受信しました。クリーンアップを実行します...")
        cleanup_child_processes()
        sys.exit(130 if signum == signal.SIGINT else 143)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    atexit.register(cleanup_child_processes)
    _cleanup_registered = True


def load_pid(pid_file: Path) -> Optional[int]:
    """PIDファイルからPIDを読み込み"""
    try:
        if pid_file.exists():
            with open(pid_file, 'r') as f:
                return int(f.read().strip())
    except Exception:
        pass
    return None


def is_process_running(pid: int) -> bool:
    """プロセスが実行中か確認"""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def stop_process(pid_file: Path) -> bool:
    """実行中のプロセスを停止（子プロセスも含む）"""
    pid = load_pid(pid_file)
    if pid is None:
        print(f"PIDファイルが見つかりません: {pid_file}")
        return False
    
    if not is_process_running(pid):
        print(f"プロセス {pid} は実行されていません")
        cleanup_pid(pid_file)
        return False
    
    try:
        import psutil
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            print(f"親プロセス {pid} と子プロセス {len(children)} 個を停止中...")
            
            for child in children:
                try:
                    child.terminate()
                except Exception:
                    pass
            
            parent.terminate()
            time.sleep(2)
            
            for child in children:
                try:
                    if child.is_running():
                        child.kill()
                except Exception:
                    pass
            
            if parent.is_running():
                parent.kill()
            
            print(f"プロセス {pid} と子プロセスを停止しました")
        except ImportError:
            os.kill(pid, signal.SIGTERM)
            print(f"プロセス {pid} に停止シグナルを送信しました")
            time.sleep(1)
            
            if is_process_running(pid):
                os.kill(pid, signal.SIGKILL)
                print(f"プロセス {pid} を強制終了しました")
        
        cleanup_pid(pid_file)
        return True
    except Exception as e:
        print(f"プロセス停止エラー: {e}")
        return False


def check_status(pid_file: Path, output_dir: Path) -> int:
    """実行状態を確認"""
    pid = load_pid(pid_file)
    if pid is None:
        print("実行中のプロセスはありません")
        return 1
    
    if not is_process_running(pid):
        print(f"プロセス {pid} は実行されていません（PIDファイルが残っています）")
        cleanup_pid(pid_file)
        return 1
    
    log_file = output_dir / "run.log"
    checkpoint_file = output_dir / "checkpoint.json"
    
    print(f"実行中: PID {pid}")
    print(f"出力ディレクトリ: {output_dir}")
    
    if log_file.exists():
        log_size = log_file.stat().st_size
        print(f"ログファイル: {log_file} ({log_size:,} bytes)")
    
    if checkpoint_file.exists():
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            completed = len(checkpoint_data.get('completed_ids', []))
            print(f"完了済み実験数: {completed}")
        except Exception:
            pass
    
    return 0


def daemonize(log_file: str) -> int:
    """
    プロセスをデーモン化（Unix系のみ）
    
    Args:
        log_file: ログファイルの絶対パス（文字列）
    
    Returns:
        子プロセスのPID（親プロセスのみ）
    """
    if os.name == 'nt':
        raise RuntimeError("バックグラウンド実行はUnix系システムでのみサポートされています")
    
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        pid = os.fork()
        if pid > 0:
            return pid
    except OSError as e:
        sys.stderr.write(f"fork failed: {e}\n")
        sys.exit(1)
    
    os.chdir("/")
    os.setsid()
    os.umask(0)
    
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"fork failed: {e}\n")
        sys.exit(1)
    
    sys.stdout.flush()
    sys.stderr.flush()
    
    si = open(os.devnull, 'r')
    so = open(log_file, 'a+')
    se = open(log_file, 'a+', 1)
    
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())
    
    return 0


def run_parallel_experiments(
    experiments: List[Dict[str, Any]],
    output_dir: Path,
    max_workers: int = None,
    checkpoint_file: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    並列実行で実験を実行（チェックポイント対応）
    
    Args:
        experiments: 実験設定のリスト
        output_dir: 出力ディレクトリ
        max_workers: 最大並列数（Noneの場合はCPUコア数、最大8）
        checkpoint_file: チェックポイントファイルパス
        
    Returns:
        実験結果のリスト
    """
    import multiprocessing
    
    if max_workers is None:
        # メモリ使用量削減のため、並列実行数を1/5に削減（最大8 -> 最大2）
        max_workers = min(max(1, multiprocessing.cpu_count() // 5), 2)
    
    # チェックポイントから復元
    checkpoint_path = checkpoint_file or (output_dir / "checkpoint.json")
    completed_results, completed_ids = load_checkpoint(checkpoint_path)
    completed_set = set(completed_ids)
    
    # 実験IDごとの出力ディレクトリを作成
    exp_output_dir = output_dir / "experiments"
    exp_output_dir.mkdir(parents=True, exist_ok=True)
    
    # 実行引数を準備（スキップされる実験と完了済み実験を除外）
    args_list = []
    skipped_experiments = []
    for exp in experiments:
        exp_id = exp['experiment_id']
        
        # 既に完了している場合はスキップ
        if exp_id in completed_set:
            continue
        
        # 設定変換を試みて、スキップされるか確認
        try:
            config = convert_matrix_to_config(exp)
            if config is None:
                skipped_experiments.append(exp_id)
                continue
        except Exception as e:
            logging.warning(f"実験設定変換エラー ({exp_id}): {e}")
            skipped_experiments.append(exp_id)
            continue
        
        args_list.append((exp, exp_id, exp_output_dir / exp_id))
    
    if skipped_experiments:
        logging.info(f"スキップされた実験: {len(skipped_experiments)}件")
    
    if completed_results:
        logging.info(f"チェックポイントから復元: {len(completed_results)}件完了済み")
    
    # 実行開始時刻
    start_time = time.time()
    results = completed_results.copy()
    failed_experiments = [r['experiment_info']['experiment_id'] for r in completed_results if not r.get('success', False)]
    
    total_experiments = len(experiments)
    remaining_experiments = len(args_list)
    
    if remaining_experiments == 0:
        logging.info("全ての実験が完了済みです")
        return results
    
    # エラーログファイル
    error_log_file = output_dir / "errors.log"
    error_log_file.touch()
    
    global _executor
    register_cleanup_handlers()
    
    _executor = ProcessPoolExecutor(max_workers=max_workers)
    try:
        executor = _executor
        # タスクを送信
        future_to_exp = {
            executor.submit(run_single_experiment_wrapper, args): args[1]
            for args in args_list
        }
        
        # 進捗バーで結果を取得
        completed_count = len(completed_results)
        with tqdm(total=total_experiments, initial=completed_count, desc="実験実行中", unit="件") as pbar:
            last_checkpoint_time = time.time()
            checkpoint_interval = 30  # 30秒ごとにチェックポイント保存
            
            for future in as_completed(future_to_exp):
                experiment_id = future_to_exp[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed_count += 1
                    
                    if not result.get('success', False):
                        failed_experiments.append(experiment_id)
                        # エラーのみログファイルに記録
                        error_info = result.get('experiment_info', {})
                        error_msg = error_info.get('error', 'Unknown error')
                        with open(error_log_file, 'a', encoding='utf-8') as f:
                            f.write(f"[{datetime.now().isoformat()}] {experiment_id}: {error_msg}\n")
                    
                    # 予測時間計算
                    elapsed_time = time.time() - start_time
                    completed = completed_count
                    remaining = total_experiments - completed
                    
                    if completed > 0:
                        avg_time_per_exp = elapsed_time / completed
                        estimated_remaining = avg_time_per_exp * remaining
                        estimated_completion = datetime.now() + timedelta(seconds=estimated_remaining)
                        
                        # 進捗バーの説明を更新
                        success_count = sum(1 for r in results if r.get('success', False))
                        fail_count = len(failed_experiments)
                        pbar.set_postfix({
                            '成功': success_count,
                            '失敗': fail_count,
                            '予測終了': estimated_completion.strftime("%H:%M:%S")
                        })
                    
                    # 定期的にチェックポイント保存
                    current_time = time.time()
                    if current_time - last_checkpoint_time >= checkpoint_interval:
                        completed_ids = [r['experiment_info']['experiment_id'] for r in results]
                        save_checkpoint(checkpoint_path, results, completed_ids)
                        last_checkpoint_time = current_time
                        
                        # メモリクリーンアップ
                        gc.collect()
                    
                except Exception as e:
                    error_msg = f"結果取得エラー: {str(e)}"
                    logging.error(f"実験結果取得エラー ({experiment_id}): {e}")
                    results.append({
                        'experiment_info': {
                            'experiment_id': experiment_id,
                            'error': error_msg
                        },
                        'success': False
                    })
                    failed_experiments.append(experiment_id)
                    completed_count += 1
                    
                    # エラーログに記録
                    with open(error_log_file, 'a', encoding='utf-8') as f:
                        f.write(f"[{datetime.now().isoformat()}] {experiment_id}: {error_msg}\n")
                finally:
                    pbar.update(1)
            
            # 最終チェックポイント保存
            completed_ids = [r['experiment_info']['experiment_id'] for r in results]
            save_checkpoint(checkpoint_path, results, completed_ids)
    finally:
        if _executor is not None:
            _executor.shutdown(wait=True)
            _executor = None
    
    if failed_experiments:
        logging.warning(f"失敗した実験: {len(failed_experiments)}件")
        logging.info(f"エラーログ: {error_log_file}")
    
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
        help='並列実行数 (default: CPUコア数/5、最大2)'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default=None,
        help='出力ディレクトリ (default: results/{timestamp})'
    )
    
    parser.add_argument(
        '--background', '-b',
        action='store_true',
        help='バックグラウンド実行'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='実行状態を確認'
    )
    
    parser.add_argument(
        '--stop',
        action='store_true',
        help='実行中のプロセスを停止'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='デバッグモード'
    )
    
    args = parser.parse_args()
    
    # 状態確認
    if args.status:
        if not args.output_dir:
            print("エラー: --status には --output-dir が必要です")
            return 1
        output_dir = Path(args.output_dir)
        pid_file = output_dir / "run.pid"
        return check_status(pid_file, output_dir)
    
    # プロセス停止
    if args.stop:
        if not args.output_dir:
            print("エラー: --stop には --output-dir が必要です")
            return 1
        output_dir = Path(args.output_dir)
        pid_file = output_dir / "run.pid"
        if stop_process(pid_file):
            return 0
        return 1
    
    # 出力ディレクトリを設定
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("results") / timestamp
    
    pid_file = output_dir / "run.pid"
    
    # ログ設定
    log_level = logging.DEBUG if args.debug else logging.INFO
    
    # バックグラウンド実行の場合
    if args.background:
        output_dir = output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        log_file = (output_dir / "run.log").resolve()
        pid_file = pid_file.resolve()
        
        # 既に実行中の場合はエラー
        if pid_file.exists():
            pid = load_pid(pid_file)
            if pid and is_process_running(pid):
                print(f"既に実行中のプロセスがあります: PID {pid}")
                print(f"状態確認: python {sys.argv[0]} --status --output-dir {output_dir}")
                print(f"停止: python {sys.argv[0]} --stop --output-dir {output_dir}")
                return 1
        
        # デーモン化
        log_file_abs_str = str(log_file.resolve())
        child_pid = daemonize(log_file_abs_str)
        
        # 親プロセスの場合（child_pid > 0）
        if child_pid > 0:
            # 子プロセスのPIDファイルが作成されるまで少し待つ
            time.sleep(0.5)
            print(f"バックグラウンド実行開始: PID {child_pid}")
            print(f"出力ディレクトリ: {output_dir}")
            print(f"PIDファイル: {pid_file}")
            print(f"ログファイル: {log_file}")
            print(f"状態確認: python {sys.argv[0]} --status --output-dir {output_dir}")
            print(f"停止: python {sys.argv[0]} --stop --output-dir {output_dir}")
            sys.exit(0)
        
        # 子プロセス（デーモン）の処理
        # デーモン化後はログファイルに出力
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file_abs_str, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        logger = logging.getLogger(__name__)
        
        # デーモン化後にシグナルハンドラを再登録
        register_cleanup_handlers()
        
        # PIDファイルを保存（デーモン化後の子プロセスで）
        save_pid(pid_file)
        logger.info(f"バックグラウンド実行開始: PID {os.getpid()}")
        logger.info(f"PIDファイル: {pid_file}")
        logger.info(f"ログファイル: {log_file}")
    else:
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger(__name__)
        register_cleanup_handlers()
    
    try:
        # PIDファイルを保存
        if args.background:
            save_pid(pid_file)
            logger.info(f"PIDファイル: {pid_file}")
        
        # 実験マトリックスを読み込み
        logger.info(f"実験マトリックスを読み込み: {args.matrix}")
        matrix_data = load_experiment_matrix(args.matrix)
        
        experiments = matrix_data.get('experiments', [])
        experiment_plan = matrix_data.get('experiment_plan', {})
        
        logger.info(f"実験数: {len(experiments)}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"出力ディレクトリ: {output_dir}")
        
        # チェックポイントファイルパス
        checkpoint_file = output_dir / "checkpoint.json"
        
        # 並列実行
        actual_workers = args.workers if args.workers is not None else min(max(1, multiprocessing.cpu_count() // 5), 2)
        logger.info(f"並列実行開始 (workers={actual_workers}, CPUコア数={multiprocessing.cpu_count()})")
        if checkpoint_file.exists():
            logger.info(f"チェックポイントから再開: {checkpoint_file}")
        
        results = run_parallel_experiments(
            experiments=experiments,
            output_dir=output_dir,
            max_workers=args.workers,
            checkpoint_file=checkpoint_file
        )
        
        # 結果を保存
        logger.info("結果を保存中...")
        save_results(results, output_dir, experiment_plan)
        
        # サマリー表示
        successful = sum(1 for r in results if r.get('success', False))
        failed = len(results) - successful
        
        logger.info("=" * 60)
        logger.info("実行完了")
        logger.info(f"総実験数: {len(experiments)}件")
        logger.info(f"完了: {len(results)}件")
        logger.info(f"成功: {successful}件")
        logger.info(f"失敗: {failed}件")
        logger.info(f"結果ディレクトリ: {output_dir}")
        if failed > 0:
            error_log_file = output_dir / "errors.log"
            logger.info(f"エラーログ: {error_log_file}")
        logger.info("=" * 60)
        
        # PIDファイルを削除
        cleanup_pid(pid_file)
        
        return 0 if failed == 0 else 1
        
    except KeyboardInterrupt:
        logger.warning("実行が中断されました")
        cleanup_child_processes()
        cleanup_pid(pid_file)
        return 130
        
    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        cleanup_child_processes()
        cleanup_pid(pid_file)
        return 1
    finally:
        cleanup_child_processes()


if __name__ == "__main__":
    exit(main())

