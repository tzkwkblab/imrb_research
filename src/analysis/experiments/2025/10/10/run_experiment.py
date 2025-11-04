#!/usr/bin/env python3
"""
実験実行コマンドラインスクリプト

使用例:
  # 設定ファイルから実行
  python run_experiment.py --config pipeline_config.yaml
  
  # コマンドライン引数で実行
  python run_experiment.py --dataset steam --aspect gameplay --group-size 50
  
  # 複数アスペクト指定
  python run_experiment.py --dataset steam --aspects gameplay visual story
"""

import sys
import argparse
from pathlib import Path

# パイプラインをインポート
from experiment_pipeline import ExperimentPipeline


def parse_args():
    """コマンドライン引数解析"""
    parser = argparse.ArgumentParser(
        description="統一実験パイプライン実行スクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 設定ファイルから実行
  python run_experiment.py --config pipeline_config.yaml
  
  # 単一実験
  python run_experiment.py --dataset steam --aspect gameplay --group-size 50
  
  # 複数アスペクト
  python run_experiment.py --dataset steam --aspects gameplay visual story
        """
    )
    
    # 設定ファイル
    parser.add_argument(
        '--config', '-c',
        type=str,
        default='pipeline_config.yaml',
        help='設定ファイルパス (default: pipeline_config.yaml)'
    )
    
    # 単一実験用引数
    parser.add_argument(
        '--dataset', '-d',
        type=str,
        choices=['steam', 'semeval', 'amazon', 'retrieved_concepts'],
        help='データセット名'
    )
    
    parser.add_argument(
        '--aspect', '-a',
        type=str,
        help='アスペクト名（単一指定）'
    )
    
    parser.add_argument(
        '--aspects',
        nargs='+',
        help='アスペクト名（複数指定）'
    )
    
    parser.add_argument(
        '--group-size', '-g',
        type=int,
        default=50,
        help='グループサイズ (default: 50)'
    )
    
    parser.add_argument(
        '--split-type',
        type=str,
        choices=['binary_label', 'aspect_vs_others'],
        default='binary_label',
        help='分割タイプ (default: binary_label)'
    )

    # アスペクト説明文利用フラグ
    parser.add_argument(
        '--use-aspect-descriptions',
        action='store_true',
        help='アスペクト名の代わりに説明文を用いてスコア比較する'
    )

    # アスペクト説明CSVファイル（明示指定）
    parser.add_argument(
        '--aspect-descriptions-file',
        type=str,
        help='アスペクト説明文CSVファイル（aspect,description ヘッダー）'
    )

    # 例題（Few-shot）オプション
    parser.add_argument(
        '--use-examples',
        action='store_true',
        help='Few-shot例題をプロンプトに含める'
    )
    parser.add_argument(
        '--examples-file',
        type=str,
        help='Few-shot例題ファイル（JSON/YAML）'
    )
    parser.add_argument(
        '--max-examples',
        type=int,
        default=None,
        help='先頭N件のみ例題を使用（未指定は全件）'
    )
    
    # その他オプション
    parser.add_argument(
        '--debug',
        action='store_true',
        default=True,
        help='デバッグモード有効化'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='results/',
        help='出力ディレクトリ (default: results/)'
    )

    parser.add_argument(
        '--silent',
        action='store_true',
        help='ファイル保存を行わずサイレント動作（デバッグ用途）'
    )
    
    return parser.parse_args()


def create_quick_config(args) -> dict:
    """コマンドライン引数から設定を作成"""
    # アスペクトリスト作成
    aspects = []
    if args.aspect:
        aspects = [args.aspect]
    elif args.aspects:
        aspects = args.aspects
    
    if not aspects:
        raise ValueError("--aspect または --aspects を指定してください")
    
    # 設定辞書作成
    config = {
        'experiments': [
            {
                'dataset': args.dataset,
                'aspects': aspects,
                'group_size': args.group_size,
                'split_type': args.split_type
            }
        ],
        'output': {
            'directory': args.output_dir,
            'format': 'json',
            'save_intermediate': not args.silent
        },
        'llm': {
            'model': 'gpt-4o-mini',
            'temperature': 0.7,
            'max_tokens': 150
        },
        'general': {
            'debug_mode': args.debug,
            'console_output': not args.silent,
            'silent_mode': bool(args.silent),
            'use_aspect_descriptions': bool(args.use_aspect_descriptions),
            'aspect_descriptions_file': args.aspect_descriptions_file,
            'use_examples': bool(args.use_examples),
            'examples_file': args.examples_file,
            'max_examples': args.max_examples
        }
    }
    
    return config


def main():
    """メイン実行"""
    args = parse_args()
    
    print("=" * 60)
    print("統一実験パイプライン")
    print("=" * 60)
    
    try:
        # 設定ファイルパス解決
        config_path = Path(args.config)
        
        # コマンドライン引数でdatasetが指定されている場合
        if args.dataset:
            print("\n[モード] コマンドライン引数から実行")
            print(f"データセット: {args.dataset}")
            
            # 一時設定ファイル作成
            import yaml
            import tempfile
            
            config = create_quick_config(args)
            
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.yaml', 
                delete=False,
                encoding='utf-8'
            ) as tmp:
                yaml.dump(config, tmp, allow_unicode=True)
                tmp_config_path = tmp.name
            
            # パイプライン実行
            pipeline = ExperimentPipeline(tmp_config_path, debug=args.debug, silent=args.silent)
            success = pipeline.run()
            
            # 一時ファイル削除
            Path(tmp_config_path).unlink()
            
        else:
            # 設定ファイルから実行
            if not config_path.exists():
                config_path = Path(__file__).parent / args.config
            
            if not config_path.exists():
                print(f"❌ 設定ファイルが見つかりません: {config_path}")
                return 1
            
            print(f"\n[モード] 設定ファイルから実行")
            print(f"設定ファイル: {config_path}")
            
            # パイプライン実行
            pipeline = ExperimentPipeline(str(config_path), debug=args.debug, silent=args.silent)
            success = pipeline.run()
        
        if success:
            print("\n✅ 実験が正常に完了しました")
            return 0
        else:
            print("\n❌ 実験でエラーが発生しました")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n⚠️  実験が中断されました")
        return 130
    
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

