#!/usr/bin/env python3
"""
シンプルなクリーンアップテスト
実際の実験スクリプトと同じ構造でテスト
"""

import os
import sys
import time
import signal
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

import run_batch_from_matrix
from concurrent.futures import ProcessPoolExecutor


def worker_task(n):
    """長時間実行するタスク"""
    print(f"Worker {n} started (PID: {os.getpid()})", flush=True)
    time.sleep(60)
    return f"Worker {n} completed"


def main():
    print("=" * 60)
    print("クリーンアップ機能テスト（実運用シミュレーション）")
    print("=" * 60)
    
    run_batch_from_matrix.register_cleanup_handlers()
    
    print(f"\n1. プロセスプールを作成中...")
    executor = ProcessPoolExecutor(max_workers=4)
    run_batch_from_matrix._executor = executor
    
    print(f"2. タスクを送信中...")
    futures = []
    for i in range(8):
        future = executor.submit(worker_task, i)
        futures.append(future)
        print(f"   タスク {i} を送信", flush=True)
    
    print(f"\n3. 10秒実行後、Ctrl+Cで停止してください...")
    print(f"   または kill -TERM {os.getpid()} で停止")
    print(f"   現在のPID: {os.getpid()}")
    
    try:
        time.sleep(10)
        print(f"\n4. 正常終了")
        executor.shutdown(wait=True)
    except KeyboardInterrupt:
        print(f"\n4. 中断されました。クリーンアップを実行...")
        run_batch_from_matrix.cleanup_child_processes()
    
    print(f"\n5. プロセス確認...")
    current_pid = os.getpid()
    try:
        import psutil
        current = psutil.Process(current_pid)
        children = current.children(recursive=True)
        print(f"   残っている子プロセス数: {len(children)}")
        if children:
            print("   残っている子プロセス:")
            for child in children:
                print(f"     - PID {child.pid}: {child.name()}")
        else:
            print("   ✓ すべての子プロセスがクリーンアップされました")
    except ImportError:
        print("   psutilがインストールされていないため、詳細な確認はスキップします")
    except Exception as e:
        print(f"   プロセス確認エラー: {e}")
    
    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)


if __name__ == "__main__":
    main()

