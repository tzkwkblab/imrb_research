#!/usr/bin/env python3
"""
3-shot実験の完了を待って結果を分析するスクリプト
"""

import time
import subprocess
from pathlib import Path

def check_experiment_status(results_dir: str) -> bool:
    """実験が完了したか確認"""
    results_path = Path(results_dir) / "batch_results.json"
    return results_path.exists()

def wait_for_completion(results_dir: str, check_interval: int = 60):
    """実験の完了を待つ"""
    print(f"実験の完了を待っています: {results_dir}")
    print("チェック間隔: {}秒".format(check_interval))
    
    while True:
        if check_experiment_status(results_dir):
            print("実験が完了しました！")
            return True
        
        print(f"実行中... ({time.strftime('%Y-%m-%d %H:%M:%S')})")
        time.sleep(check_interval)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="3-shot実験の完了を待って結果を分析")
    parser.add_argument('--results-dir', type=str, required=True, help='結果ディレクトリ')
    parser.add_argument('--check-interval', type=int, default=60, help='チェック間隔（秒）')
    
    args = parser.parse_args()
    
    # 完了を待つ
    wait_for_completion(args.results_dir, args.check_interval)
    
    # 結果を分析
    script_dir = Path(__file__).parent
    analyze_script = script_dir / "analyze_3shot_results.py"
    
    print("結果を分析します...")
    subprocess.run([
        "python", str(analyze_script),
        "--results-dir", args.results_dir
    ])

if __name__ == "__main__":
    main()












