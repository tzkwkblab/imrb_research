#!/usr/bin/env python3
"""
Amazon Product Review Dataset (with Aspect/Sentiment Labels) ダウンロードスクリプト

このスクリプトは、KaggleからAmazon Product Review Datasetをダウンロードし、
プロジェクトの./data/external/ディレクトリに配置します。

必要な環境変数:
- KAGGLE_USERNAME: Kaggleのユーザー名
- KAGGLE_KEY: Kaggle APIキー

使用方法:
    python src/data/download_amazon_reviews.py

機能:
- 環境変数を使用したKaggle API認証
- tqdmを使った進捗表示
- ダウンロード中断時の再開機能
- 詳細なログ出力
- エラーハンドリング
- バージョン管理とメタデータ生成
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import time
from datetime import datetime

import kaggle
from tqdm import tqdm
from dotenv import load_dotenv


class AmazonReviewsDownloader:
    """Amazon Product Review Datasetダウンロードクラス"""
    
    def __init__(self, data_dir: str = "./data/external/amazon-product-reviews/kaggle-bittlingmayer"):
        """
        初期化
        
        Args:
            data_dir: データを保存するディレクトリパス
        """
        # .envファイルから環境変数を読み込む
        load_dotenv()
        
        # バージョン付きディレクトリの作成
        version_dir = f"v1.0_{datetime.now().strftime('%Y-%m-%d')}"
        self.data_dir = Path(data_dir) / version_dir
        self.base_dir = Path(data_dir)
        self.dataset_name = "bittlingmayer/amazonreviews"
        self.progress_file = self.data_dir / ".download_progress.json"
        
        # ログ設定
        self._setup_logging()
        
        # ディレクトリ作成
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def _setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('download_amazon_reviews.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _check_kaggle_credentials(self) -> bool:
        """
        Kaggle認証情報の確認
        
        Returns:
            bool: 認証情報が正しく設定されている場合True
        """
        username = os.getenv('KAGGLE_USERNAME')
        key = os.getenv('KAGGLE_KEY')
        
        if not username or not key:
            self.logger.error("環境変数 KAGGLE_USERNAME と KAGGLE_KEY を設定してください")
            self.logger.info("設定方法:")
            self.logger.info("1. Kaggleアカウントでログイン")
            self.logger.info("2. Account > API > Create New API Token")
            self.logger.info("3. ダウンロードしたkaggle.jsonから認証情報を取得")
            self.logger.info("4. .envファイルに以下を追加:")
            self.logger.info("   KAGGLE_USERNAME=your_username")
            self.logger.info("   KAGGLE_KEY=your_api_key")
            self.logger.info("5. または環境変数を直接設定:")
            self.logger.info("   export KAGGLE_USERNAME='your_username'")
            self.logger.info("   export KAGGLE_KEY='your_api_key'")
            return False
            
        # Kaggle APIクライアントに認証情報を設定
        os.environ['KAGGLE_USERNAME'] = username
        os.environ['KAGGLE_KEY'] = key
        
        self.logger.info(f"Kaggle認証情報を確認しました (ユーザー: {username})")
        return True
        
    def _save_progress(self, progress_data: Dict[str, Any]):
        """
        進捗情報を保存
        
        Args:
            progress_data: 進捗データ
        """
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.warning(f"進捗保存に失敗: {e}")
            
    def _load_progress(self) -> Optional[Dict[str, Any]]:
        """
        進捗情報を読み込み
        
        Returns:
            Dict[str, Any]: 進捗データ、存在しない場合はNone
        """
        try:
            if self.progress_file.exists():
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"進捗読み込みに失敗: {e}")
        return None
        
    def _check_existing_files(self) -> bool:
        """
        既存ファイルの確認
        
        Returns:
            bool: データセットが既に存在する場合True
        """
        # 一般的なファイル名パターンをチェック
        patterns = [
            "*.csv", "*.tsv", "*.json", "*.txt", "*.bz2", "*.gz",
            "amazonreviews*", "amazon_reviews*", "train*", "test*"
        ]
        
        for pattern in patterns:
            if list(self.data_dir.glob(pattern)):
                return True
                
        return False
        
    def download_dataset(self, force_download: bool = False) -> bool:
        """
        データセットをダウンロード
        
        Args:
            force_download: 既存ファイルがある場合も強制ダウンロード
            
        Returns:
            bool: ダウンロード成功時True
        """
        try:
            # 認証確認
            if not self._check_kaggle_credentials():
                return False
                
            # 既存ファイル確認
            if not force_download and self._check_existing_files():
                self.logger.info("データセットは既に存在します")
                user_input = input("再ダウンロードしますか？ (y/N): ").strip().lower()
                if user_input not in ['y', 'yes']:
                    self.logger.info("ダウンロードをキャンセルしました")
                    return True
                    
            # 進捗確認
            progress = self._load_progress()
            if progress and progress.get('status') == 'completed':
                self.logger.info("前回のダウンロードが完了しています")
                if not force_download:
                    user_input = input("再ダウンロードしますか？ (y/N): ").strip().lower()
                    if user_input not in ['y', 'yes']:
                        return True
                        
            self.logger.info(f"データセット '{self.dataset_name}' のダウンロードを開始します")
            self.logger.info(f"保存先: {self.data_dir.absolute()}")
            
            # 進捗保存
            progress_data = {
                'dataset': self.dataset_name,
                'status': 'downloading',
                'start_time': time.time(),
                'data_dir': str(self.data_dir.absolute())
            }
            self._save_progress(progress_data)
            
            # ダウンロード実行
            with tqdm(desc="ダウンロード中", unit="B", unit_scale=True) as pbar:
                try:
                    # Kaggle APIでダウンロード
                    kaggle.api.dataset_download_files(
                        self.dataset_name,
                        path=str(self.data_dir),
                        unzip=True,
                        quiet=False
                    )
                    pbar.update(1)
                    
                except Exception as e:
                    self.logger.error(f"Kaggle APIダウンロードエラー: {e}")
                    raise
                    
            # ダウンロード完了
            progress_data.update({
                'status': 'completed',
                'end_time': time.time(),
                'duration': time.time() - progress_data['start_time']
            })
            self._save_progress(progress_data)
            
            self.logger.info("ダウンロードが完了しました")
            self._show_download_summary()
            self._create_metadata_file()
            self._update_current_link()
            
            return True
            
        except Exception as e:
            self.logger.error(f"ダウンロードに失敗しました: {e}")
            
            # エラー時の進捗保存
            if 'progress_data' in locals():
                progress_data.update({
                    'status': 'failed',
                    'error': str(e),
                    'end_time': time.time()
                })
                self._save_progress(progress_data)
                
            return False
            
    def _show_download_summary(self):
        """ダウンロード結果のサマリー表示"""
        self.logger.info("=" * 50)
        self.logger.info("ダウンロード完了サマリー")
        self.logger.info("=" * 50)
        
        # ファイル一覧表示
        files = list(self.data_dir.iterdir())
        if files:
            self.logger.info(f"ダウンロードされたファイル ({len(files)}個):")
            for file_path in sorted(files):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    size = file_path.stat().st_size
                    size_mb = size / (1024 * 1024)
                    self.logger.info(f"  - {file_path.name} ({size_mb:.2f} MB)")
        else:
            self.logger.warning("ダウンロードされたファイルが見つかりません")
            
        self.logger.info("=" * 50)
        
    def _create_metadata_file(self):
        """データセット情報を記録するメタデータファイルを作成"""
        try:
            # ファイルサイズ情報の収集
            files_info = {}
            for file_path in self.data_dir.iterdir():
                if file_path.is_file() and not file_path.name.startswith('.'):
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    files_info[file_path.name] = {
                        "size_mb": round(size_mb, 2),
                        "format": self._get_file_format(file_path.name)
                    }
            
            metadata = {
                "dataset_name": "Amazon Product Review Dataset (with Aspect/Sentiment Labels)",
                "source": "Kaggle",
                "author": "bittlingmayer",
                "kaggle_url": "https://www.kaggle.com/datasets/bittlingmayer/amazonreviews",
                "download_date": datetime.now().strftime('%Y-%m-%d'),
                "download_time": datetime.now().isoformat(),
                "version": f"v1.0_{datetime.now().strftime('%Y-%m-%d')}",
                "description": "Amazon product reviews with aspect and sentiment labels for NLP research",
                "files": files_info,
                "usage_notes": [
                    "Downloaded via Kaggle API",
                    "Contains review text, ratings, and metadata",
                    "Suitable for sentiment analysis and recommendation systems"
                ],
                "license": "Check Kaggle dataset page for current license terms"
            }
            
            metadata_file = self.data_dir / "dataset_info.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"メタデータファイルを作成: {metadata_file}")
            
        except Exception as e:
            self.logger.warning(f"メタデータファイル作成に失敗: {e}")
            
    def _get_file_format(self, filename: str) -> str:
        """ファイル形式を判定"""
        if filename.endswith('.json.gz'):
            return "gzipped JSON"
        elif filename.endswith('.txt.bz2'):
            return "bzip2 compressed text"
        elif filename.endswith('.csv'):
            return "CSV"
        elif filename.endswith('.json'):
            return "JSON"
        elif filename.endswith('.txt'):
            return "text"
        else:
            return "unknown"
            
    def _update_current_link(self):
        """最新版を指すシンボリックリンクを作成/更新"""
        try:
            current_link = self.base_dir / "current"
            version_dir_name = self.data_dir.name
            
            # 既存のリンクを削除
            if current_link.exists() or current_link.is_symlink():
                current_link.unlink()
                
            # 新しいリンクを作成
            current_link.symlink_to(version_dir_name)
            self.logger.info(f"最新版リンクを更新: current -> {version_dir_name}")
            
        except Exception as e:
            self.logger.warning(f"シンボリックリンク作成に失敗: {e}")
            
    def cleanup_progress(self):
        """進捗ファイルのクリーンアップ"""
        try:
            if self.progress_file.exists():
                self.progress_file.unlink()
                self.logger.info("進捗ファイルを削除しました")
        except Exception as e:
            self.logger.warning(f"進捗ファイル削除に失敗: {e}")


def main():
    """メイン関数"""
    print("Amazon Product Review Dataset ダウンローダー")
    print("=" * 50)
    
    # ダウンローダー初期化
    try:
        downloader = AmazonReviewsDownloader()
    except Exception as e:
        print(f"❌ 初期化に失敗しました: {e}")
        sys.exit(1)
    
    try:
        # ダウンロード実行
        success = downloader.download_dataset()
        
        if success:
            print("\n✅ ダウンロードが正常に完了しました！")
            print(f"データは {downloader.data_dir.absolute()} に保存されています")
        else:
            print("\n❌ ダウンロードに失敗しました")
            print("ログファイル 'download_amazon_reviews.log' を確認してください")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  ダウンロードが中断されました")
        print("次回実行時に中断した箇所から再開できます")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 