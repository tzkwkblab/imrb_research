"""
設定検証モジュール
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from .configs.dataset_config import DatasetConfig


class ValidationError(Exception):
    """設定検証エラー"""
    pass


class ConfigValidator:
    """設定検証クラス"""
    
    def __init__(self, config: DatasetConfig):
        """
        初期化
        
        Args:
            config: 検証対象の設定オブジェクト
        """
        self.config = config
    
    def validate_all(self) -> List[str]:
        """全体検証（警告メッセージのリストを返す）"""
        warnings = []
        
        for dataset_id in self.config.list_available_datasets():
            try:
                dataset_warnings = self.validate_dataset(dataset_id)
                if dataset_warnings:
                    warnings.extend([f"[{dataset_id}] {w}" for w in dataset_warnings])
            except ValidationError as e:
                warnings.append(f"[{dataset_id}] エラー: {e}")
        
        return warnings
    
    def validate_dataset(self, dataset_id: str) -> List[str]:
        """個別データセット検証"""
        warnings = []
        
        try:
            dataset_info = self.config.get_dataset_config(dataset_id)
        except ValueError as e:
            raise ValidationError(f"データセット情報取得失敗: {e}")
        
        # パス存在確認
        path_warnings = self._validate_path(dataset_info.get('path', ''))
        warnings.extend(path_warnings)
        
        # アスペクト検証
        aspect_warnings = self._validate_aspects(dataset_info)
        warnings.extend(aspect_warnings)
        
        # 言語設定検証
        language_warnings = self._validate_language(dataset_info.get('language', 'en'))
        warnings.extend(language_warnings)
        
        return warnings
    
    def _validate_path(self, path: str) -> List[str]:
        """パス存在確認"""
        warnings = []
        
        path_obj = Path(path)
        if not path_obj.exists():
            warnings.append(f"パスが存在しません: {path}")
        elif not path_obj.is_dir():
            warnings.append(f"ディレクトリではありません: {path}")
        else:
            # 必要ファイルの存在確認
            required_files = ["train.csv", "test.csv", "train.ft.txt", "test.ft.txt"]
            found_files = [f for f in required_files if (path_obj / f).exists()]
            
            if not found_files:
                warnings.append(f"必要なデータファイルが見つかりません: {required_files}")
        
        return warnings
    
    def _validate_aspects(self, dataset_info: Dict[str, Any]) -> List[str]:
        """アスペクト設定検証"""
        warnings = []
        
        if not dataset_info.get('aspects') and not dataset_info.get('domains'):
            warnings.append("アスペクト情報が定義されていません")
        
        if dataset_info.get('aspects'):
            if len(dataset_info['aspects']) == 0:
                warnings.append("アスペクトリストが空です")
            elif len(set(dataset_info['aspects'])) != len(dataset_info['aspects']):
                warnings.append("重複するアスペクトがあります")
        
        if dataset_info.get('domains'):
            for domain, domain_data in dataset_info['domains'].items():
                if 'aspects' not in domain_data:
                    warnings.append(f"ドメイン '{domain}' にアスペクト定義がありません")
                elif len(domain_data['aspects']) == 0:
                    warnings.append(f"ドメイン '{domain}' のアスペクトリストが空です")
        
        return warnings
    
    def _validate_language(self, language: str) -> List[str]:
        """言語設定検証"""
        warnings = []
        
        supported_languages = ["en", "ja", "zh", "fr", "de", "es"]
        if language not in supported_languages:
            warnings.append(f"未サポート言語: {language} (サポート: {supported_languages})")
        
        return warnings
    
    def check_dataset_accessibility(self, dataset_id: str) -> bool:
        """データセットアクセス可能性チェック"""
        try:
            dataset_info = self.config.get_dataset_config(dataset_id)
            path = dataset_info.get('path', '')
            if not path:
                return False
                
            path_obj = Path(path)
            
            # パス存在確認
            if not path_obj.exists():
                return False
            
            # 読み取り権限確認
            if not path_obj.is_dir():
                return False
            
            # 必要ファイルの1つでも存在すればOK
            required_files = ["train.csv", "test.csv", "train.ft.txt", "test.ft.txt"]
            for filename in required_files:
                if (path_obj / filename).exists():
                    return True
            
            return False
            
        except Exception:
            return False
    
    def get_missing_aspects(self, dataset_id: str, required_aspects: List[str]) -> List[str]:
        """不足アスペクト取得"""
        try:
            available_aspects = self.config.get_dataset_aspects(dataset_id)
            return [aspect for aspect in required_aspects if aspect not in available_aspects]
        except ValueError:
            return required_aspects 