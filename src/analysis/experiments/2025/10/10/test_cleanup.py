#!/usr/bin/env python3
"""
クリーンアップ機能のテストスクリプト

子プロセスを生成して、停止時に自動でクリーンアップされることを確認する
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

import run_batch_from_matrix
from concurrent.futures import ProcessPoolExecutor
import multiprocessing


def worker_task(n):
    """長時間実行するタスク"""
    print(f"Worker {n} started (PID: {os.getpid()})")
    time.sleep(30)
    return f"Worker {n} completed"


def test_cleanup():
    """クリーンアップ機能のテスト"""
    print("=" * 60)
    print("クリーンアップ機能テスト開始")
    print("=" * 60)
    
    run_batch_from_matrix.register_cleanup_handlers()
    
    print(f"\n1. プロセスプールを作成中...")
    executor = ProcessPoolExecutor(max_workers=4)
    
    print(f"2. タスクを送信中...")
    futures = []
    for i in range(8):
        future = executor.submit(worker_task, i)
        futures.append(future)
        print(f"   タスク {i} を送信 (Future ID: {id(future)})")
    
    print(f"\n3. 5秒待機後、クリーンアップを実行...")
    time.sleep(5)
    
    print(f"\n4. クリーンアップ実行中...")
    run_batch_from_matrix._executor = executor
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
        print("   クリーンアップは実行されました")
    except Exception as e:
        print(f"   プロセス確認エラー: {e}")
    
    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)


if __name__ == "__main__":
    test_cleanup()

