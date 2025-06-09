#!/usr/bin/env python3
"""
Amazon Review Dataset Downloader
Kaggle APIを使ってアスペクト/センチメントラベル付きデータセットをダウンロード
"""

import os
import zipfile
import json
from pathlib import Path
from datetime import datetime
from kaggle.api.kaggle_api_extended import KaggleApi

class AmazonDatasetDownloader:
    def __init__(self, output_dir: str = "data/external/amazon-product-reviews"):
        self.output_dir = Path(output_dir)
        self.dataset_name = "bittlingmayer/amazonreviews"
        self.api = None
        
    def setup_kaggle_api(self):
        """Kaggle API認証"""
        print("Setting up Kaggle API...")
        self.api = KaggleApi()
        self.api.authenticate()
        print("✅ Kaggle API authenticated successfully")
    
    def download_dataset(self, force_download: bool = False):
        """データセットをダウンロード"""
        
        # 出力ディレクトリ作成
        version_dir = self.output_dir / "kaggle-bittlingmayer" / f"v1.0_{datetime.now().strftime('%Y-%m-%d')}"
        version_dir.mkdir(parents=True, exist_ok=True)
        
        zip_file = version_dir / "amazonreviews.zip"
        
        # 既存ファイルチェック
        if zip_file.exists() and not force_download:
            print(f"⚠️  Dataset already exists: {zip_file}")
            print("Use force_download=True to re-download")
            return zip_file
        
        print(f"📥 Downloading dataset: {self.dataset_name}")
        print(f"📁 Output directory: {version_dir}")
        
        # ダウンロード実行
        os.chdir(version_dir)
        self.api.dataset_download_files(self.dataset_name)
        
        print("✅ Download completed!")
        return zip_file
    
    def extract_dataset(self, zip_file: Path):
        """データセットを解凍"""
        extract_dir = zip_file.parent
        
        print(f"📦 Extracting {zip_file.name}...")
        
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # 解凍されたファイルを確認
        extracted_files = []
        for file in extract_dir.iterdir():
            if file.name != zip_file.name:
                extracted_files.append(file.name)
        
        print(f"✅ Extracted files: {extracted_files}")
        return extracted_files
    
    def create_metadata(self, version_dir: Path, extracted_files: list):
        """データセット情報を記録"""
        metadata = {
            "dataset_name": "Amazon Product Review Dataset (with Aspect/Sentiment Labels)",
            "source": "Kaggle",
            "author": "bittlingmayer", 
            "kaggle_url": f"https://www.kaggle.com/datasets/{self.dataset_name}",
            "download_date": datetime.now().strftime("%Y-%m-%d"),
            "download_time": datetime.now().isoformat(),
            "version": version_dir.name,
            "description": "Amazon product reviews with aspect and sentiment labels for NLP research",
            "extracted_files": extracted_files,
            "usage_notes": [
                "Downloaded via Kaggle API",
                "Check file formats and structure after extraction",
                "Verify if aspect labels are included"
            ],
            "license": "Check Kaggle dataset page for current license terms"
        }
        
        metadata_file = version_dir / "dataset_info.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"📄 Created metadata: {metadata_file}")
        return metadata_file
    
    def setup_current_link(self, version_dir: Path):
        """currentシンボリックリンクを作成"""
        current_link = self.output_dir / "kaggle-bittlingmayer" / "current"
        
        # 既存リンクを削除
        if current_link.exists() or current_link.is_symlink():
            current_link.unlink()
        
        # 新しいリンクを作成
        current_link.symlink_to(version_dir.name)
        print(f"🔗 Created symlink: current -> {version_dir.name}")
    
    def run(self, force_download: bool = False):
        """メイン実行"""
        print("=== Amazon Dataset Downloader ===")
        
        try:
            # 1. Kaggle API認証
            self.setup_kaggle_api()
            
            # 2. データセットダウンロード
            zip_file = self.download_dataset(force_download)
            
            # 3. データセット解凍
            extracted_files = self.extract_dataset(zip_file)
            
            # 4. メタデータ作成
            version_dir = zip_file.parent
            self.create_metadata(version_dir, extracted_files)
            
            # 5. currentリンク作成
            self.setup_current_link(version_dir)
            
            print("\n✅ === Download Complete ===")
            print(f"📁 Data location: {version_dir}")
            print(f"🔗 Access via: {self.output_dir}/kaggle-bittlingmayer/current/")
            print(f"📦 Files: {extracted_files}")
            
            return version_dir
            
        except Exception as e:
            print(f"❌ Error occurred: {e}")
            raise

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download Amazon Review Dataset from Kaggle")
    parser.add_argument('--force', action='store_true', help='Force re-download even if files exist')
    parser.add_argument('--output-dir', default='data/external/amazon-product-reviews', 
                       help='Output directory (default: data/external/amazon-product-reviews)')
    
    args = parser.parse_args()
    
    downloader = AmazonDatasetDownloader(args.output_dir)
    downloader.run(force_download=args.force)

if __name__ == "__main__":
    main() 