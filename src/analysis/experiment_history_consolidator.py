#!/usr/bin/env python3
"""
実験記録統合システム

experiments配下の全mdファイルを時系列順に統合し、
LLMが読みやすい単一のドキュメントを生成する。
"""

import os
import re
import glob
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import json

class ExperimentHistoryConsolidator:
    def __init__(self, experiments_dir: str = "src/analysis/experiments"):
        self.experiments_dir = Path(experiments_dir)
        self.output_dir = Path("data/analysis-workspace")
        self.output_dir.mkdir(exist_ok=True)
        
    def extract_date_from_path(self, filepath: Path) -> Tuple[datetime, str]:
        """ファイルパスから日付と実験番号を抽出"""
        parts = filepath.parts
        
        # パスから年/月/日を探す
        year, month, day = None, None, None
        experiment_id = ""
        
        for i, part in enumerate(parts):
            if part.isdigit() and len(part) == 4 and 2020 <= int(part) <= 2030:
                year = int(part)
                if i + 1 < len(parts) and parts[i + 1].isdigit() and len(parts[i + 1]) <= 2:
                    month = int(parts[i + 1])
                    if i + 2 < len(parts):
                        day_part = parts[i + 2]
                        # 日付部分から数字を抽出
                        day_match = re.match(r'(\d+)', day_part)
                        if day_match:
                            day = int(day_match.group(1))
                            # 実験番号も抽出
                            if '-' in day_part:
                                experiment_id = day_part
                            else:
                                experiment_id = str(day)
        
        if year and month and day:
            try:
                date_obj = datetime(year, month, day)
                return date_obj, experiment_id
            except ValueError:
                pass
        
        # フォールバック: ファイルの更新日時を使用
        stat = filepath.stat()
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        return mod_time, filepath.stem
    
    def extract_title_from_content(self, content: str) -> str:
        """mdファイルの内容から最初のヘッダーを抽出"""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                # マークダウンのヘッダーから#を除去
                title = re.sub(r'^#+\s*', '', line).strip()
                if title:
                    return title
        return "無題"
    
    def collect_md_files(self) -> List[Dict]:
        """experiments配下の全mdファイルを収集し、メタデータを付与"""
        md_files = []
        pattern = str(self.experiments_dir / "**" / "*.md")
        
        for filepath in glob.glob(pattern, recursive=True):
            filepath = Path(filepath)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                date_obj, experiment_id = self.extract_date_from_path(filepath)
                title = self.extract_title_from_content(content)
                
                file_info = {
                    'filepath': filepath,
                    'relative_path': filepath.relative_to(self.experiments_dir),
                    'date': date_obj,
                    'experiment_id': experiment_id,
                    'title': title,
                    'content': content,
                    'size_bytes': len(content.encode('utf-8')),
                    'char_count': len(content),
                    'line_count': len(content.split('\n'))
                }
                
                md_files.append(file_info)
                
            except (UnicodeDecodeError, PermissionError) as e:
                print(f"Warning: {filepath}の読み込みに失敗: {e}")
                continue
        
        # 日付順にソート
        md_files.sort(key=lambda x: (x['date'], x['experiment_id']))
        
        return md_files
    
    def generate_consolidated_document(self, md_files: List[Dict]) -> str:
        """統合ドキュメントを生成"""
        
        # ヘッダー部分
        now = datetime.now()
        header = f"""# 実験記録統合ドキュメント

**生成日時**: {now.strftime('%Y年%m月%d日 %H:%M:%S')}  
**対象期間**: {md_files[0]['date'].strftime('%Y年%m月%d日')} ～ {md_files[-1]['date'].strftime('%Y年%m月%d日')}  
**総実験数**: {len(md_files)}件  
**総文字数**: {sum(f['char_count'] for f in md_files):,}文字  

## 概要

このドキュメントは、説明可能AIのための対比因子ラベル生成手法に関する研究の実験記録を時系列順に統合したものです。
各実験の詳細な記録を通じて、研究の進展と発見を追跡できます。

## 目次

"""
        
        # 目次生成
        toc = ""
        for i, file_info in enumerate(md_files, 1):
            date_str = file_info['date'].strftime('%Y/%m/%d')
            toc += f"{i}. [{date_str} - {file_info['title']}](#{i}-{file_info['experiment_id']})\n"
        
        # 実験内容部分
        content_sections = "\n\n---\n\n"
        
        for i, file_info in enumerate(md_files, 1):
            date_str = file_info['date'].strftime('%Y年%m月%d日')
            
            section_header = f"""## {i}. 実験記録 - {date_str} {{#{i}-{file_info['experiment_id']}}}

**実験ID**: {file_info['experiment_id']}  
**ファイルパス**: `{file_info['relative_path']}`  
**文字数**: {file_info['char_count']:,}文字  
**行数**: {file_info['line_count']:,}行  

### 実験内容

"""
            
            # 元のコンテンツのヘッダーレベルを調整（### を #### に変換など）
            adjusted_content = self.adjust_header_levels(file_info['content'])
            
            content_sections += section_header + adjusted_content + "\n\n---\n\n"
        
        # 統計情報
        stats = self.generate_statistics(md_files)
        
        footer = f"""## 統計情報

{stats}

---

**注意**: このドキュメントは自動生成されています。元のファイルを編集してください。
"""
        
        return header + toc + content_sections + footer
    
    def adjust_header_levels(self, content: str) -> str:
        """マークダウンのヘッダーレベルを調整（ネストを深くする）"""
        lines = content.split('\n')
        adjusted_lines = []
        
        for line in lines:
            if line.strip().startswith('#'):
                # 既存のヘッダーに#を1つ追加してレベルを下げる
                adjusted_lines.append('#' + line)
            else:
                adjusted_lines.append(line)
        
        return '\n'.join(adjusted_lines)
    
    def generate_statistics(self, md_files: List[Dict]) -> str:
        """統計情報を生成"""
        total_chars = sum(f['char_count'] for f in md_files)
        total_lines = sum(f['line_count'] for f in md_files)
        avg_chars = total_chars / len(md_files) if md_files else 0
        
        # 月別統計
        monthly_stats = {}
        for file_info in md_files:
            month_key = file_info['date'].strftime('%Y年%m月')
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {'count': 0, 'chars': 0}
            monthly_stats[month_key]['count'] += 1
            monthly_stats[month_key]['chars'] += file_info['char_count']
        
        stats = f"""### 基本統計

| 項目 | 値 |
|------|------|
| 総実験数 | {len(md_files)}件 |
| 総文字数 | {total_chars:,}文字 |
| 総行数 | {total_lines:,}行 |
| 平均文字数/実験 | {avg_chars:,.0f}文字 |

### 月別実験数

| 月 | 実験数 | 文字数 |
|------|------|------|"""
        
        for month, data in sorted(monthly_stats.items()):
            stats += f"\n| {month} | {data['count']}件 | {data['chars']:,}文字 |"
        
        return stats
    
    def save_metadata(self, md_files: List[Dict]) -> str:
        """メタデータをJSONファイルとして保存"""
        metadata = []
        for file_info in md_files:
            metadata.append({
                'relative_path': str(file_info['relative_path']),
                'date': file_info['date'].isoformat(),
                'experiment_id': file_info['experiment_id'],
                'title': file_info['title'],
                'char_count': file_info['char_count'],
                'line_count': file_info['line_count'],
                'size_bytes': file_info['size_bytes']
            })
        
        metadata_file = self.output_dir / f"experiment_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return str(metadata_file)
    
    def consolidate(self) -> Tuple[str, str]:
        """実験記録を統合し、ファイルを生成"""
        print("実験記録ファイルを収集中...")
        md_files = self.collect_md_files()
        
        if not md_files:
            raise ValueError("統合対象のmdファイルが見つかりません")
        
        print(f"発見: {len(md_files)}個の実験記録ファイル")
        
        print("統合ドキュメントを生成中...")
        consolidated_content = self.generate_consolidated_document(md_files)
        
        # 出力ファイル名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.output_dir / f"experiment_history_consolidated_{timestamp}.md"
        
        # ファイル保存
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(consolidated_content)
        
        # メタデータ保存
        metadata_file = self.save_metadata(md_files)
        
        print(f"統合完了!")
        print(f"出力ファイル: {output_file}")
        print(f"メタデータ: {metadata_file}")
        print(f"統合した実験数: {len(md_files)}件")
        print(f"総文字数: {sum(f['char_count'] for f in md_files):,}文字")
        
        return str(output_file), metadata_file

def main():
    """メイン実行関数"""
    try:
        consolidator = ExperimentHistoryConsolidator()
        output_file, metadata_file = consolidator.consolidate()
        
        print("\n=== 統合処理完了 ===")
        print(f"統合ドキュメント: {output_file}")
        print(f"メタデータファイル: {metadata_file}")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        raise

if __name__ == "__main__":
    main() 