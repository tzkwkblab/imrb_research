#!/usr/bin/env python3
"""
Steam Review Aspect Dataset Downloader
Kaggle APIを使ってSteamゲームレビューアスペクトデータセットをダウンロード
"""

import os
import zipfile
import json
from pathlib import Path
from datetime import datetime
from kaggle.api.kaggle_api_extended import KaggleApi

class SteamReviewAspectDatasetDownloader:
    def __init__(self, output_dir: str = "data/external/steam-review-aspect-dataset"):
        self.output_dir = Path(output_dir)
        self.dataset_name = "ilosvigil/steam-review-aspect-dataset"
        self.api = None

    def setup_kaggle_api(self):
        print("Setting up Kaggle API...")
        self.api = KaggleApi()
        self.api.authenticate()
        print("✅ Kaggle API authenticated successfully")

    def download_dataset(self, force_download: bool = False):
        version_str = f"v1.0_{datetime.now().strftime('%Y-%m-%d')}"
        version_dir = self.output_dir / version_str
        version_dir.mkdir(parents=True, exist_ok=True)

        # 既存zipファイルがあれば削除（force時）
        if force_download:
            for z in version_dir.glob("*.zip"):
                z.unlink()

        # 既存zipファイルがあれば再利用
        zip_files = list(version_dir.glob("*.zip"))
        if zip_files and not force_download:
            zip_file = zip_files[0]
            print(f"⚠️  Dataset already exists: {zip_file}")
            print("Use force_download=True to re-download")
            return zip_file, version_dir

        print(f"📥 Downloading dataset: {self.dataset_name}")
        print(f"📁 Output directory: {version_dir}")
        os.chdir(version_dir)
        self.api.dataset_download_files(self.dataset_name, path=".")

        # ダウンロード後のzipファイル自動検出
        zip_files = list(version_dir.glob("*.zip"))
        if not zip_files:
            raise FileNotFoundError("No zip file found after download.")
        zip_file = zip_files[0]
        print(f"✅ Download completed! ({zip_file})")
        return zip_file, version_dir

    def extract_dataset(self, zip_file: Path):
        extract_dir = zip_file.parent
        print(f"📦 Extracting {zip_file.name}...")
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        extracted_files = [f.name for f in extract_dir.iterdir() if f.is_file() and f.name != zip_file.name]
        print(f"✅ Extracted files: {extracted_files}")
        return extracted_files

    def create_metadata(self, version_dir: Path, extracted_files: list):
        # ファイル情報取得
        files_info = []
        for fname in extracted_files:
            fpath = version_dir / fname
            size = fpath.stat().st_size if fpath.exists() else 0
            records = 0
            if fname.endswith('.csv'):
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        records = sum(1 for _ in f) - 1  # ヘッダ除外
                except Exception:
                    pass
            files_info.append({
                "filename": fname,
                "size_bytes": size,
                "format": fname.split('.')[-1],
                "records": records
            })
        metadata = {
            "dataset_name": "steam-review-aspect-dataset",
            "source": "Kaggle",
            "kaggle_url": "https://www.kaggle.com/datasets/ilosvigil/steam-review-aspect-dataset",
            "download_date": datetime.now().strftime("%Y-%m-%d"),
            "download_time": datetime.now().isoformat(),
            "version": version_dir.name,
            "description": "Steamゲームレビューのアスペクトラベル付きデータセット。8種類のアスペクトを含む。",
            "files": files_info,
            "license": "CC BY 4.0"
        }
        metadata_file = version_dir / "dataset_info.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        print(f"📄 Created metadata: {metadata_file}")
        return metadata_file

    def setup_current_link(self, version_dir: Path):
        current_link = self.output_dir / "current"
        if current_link.exists() or current_link.is_symlink():
            current_link.unlink()
        current_link.symlink_to(version_dir.name)
        print(f"🔗 Created symlink: current -> {version_dir.name}")

    def run(self, force_download: bool = False):
        print("=== Steam Review Aspect Dataset Downloader ===")
        try:
            self.setup_kaggle_api()
            zip_file, version_dir = self.download_dataset(force_download)
            extracted_files = self.extract_dataset(zip_file)
            self.create_metadata(version_dir, extracted_files)
            self.setup_current_link(version_dir)
            print("\n✅ === Download Complete ===")
            print(f"📁 Data location: {version_dir}")
            print(f"🔗 Access via: {self.output_dir}/current/")
            print(f"📦 Files: {extracted_files}")
            return version_dir
        except Exception as e:
            print(f"❌ Error occurred: {e}")
            raise

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Download Steam Review Aspect Dataset from Kaggle")
    parser.add_argument('--force', action='store_true', help='Force re-download even if files exist')
    parser.add_argument('--output-dir', default='data/external/steam-review-aspect-dataset', help='Output directory (default: data/external/steam-review-aspect-dataset)')
    args = parser.parse_args()
    downloader = SteamReviewAspectDatasetDownloader(args.output_dir)
    downloader.run(force_download=args.force)

if __name__ == "__main__":
    main() 