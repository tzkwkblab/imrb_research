#!/usr/bin/env python3
"""
研究背景抽出モジュール

論文texファイルから研究背景・経緯を抽出し、Markdown形式で保存する。
"""

import re
import argparse
import logging
from pathlib import Path
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def extract_latex_content(text: str, command: str) -> str:
    """LaTeXコマンドの内容を抽出"""
    pattern = rf'\\{command}\{{([^}}]+)\}}'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return ""


def clean_latex_text(text: str) -> str:
    """LaTeXコマンドを除去してテキストをクリーンアップ"""
    # itemize環境を処理
    text = re.sub(r'\\begin\{itemize\}.*?\\end\{itemize\}', '', text, flags=re.DOTALL)
    # \itemを箇条書きに変換
    text = re.sub(r'\\item\s+', '- ', text)
    # \textbf{}を太字マークダウンに変換
    text = re.sub(r'\\textbf\{([^}]+)\}', r'**\1**', text)
    # \textit{}をイタリックマークダウンに変換
    text = re.sub(r'\\textit\{([^}]+)\}', r'*\1*', text)
    # \cite{}を除去
    text = re.sub(r'\\cite\{[^}]+\}', '', text)
    # 数式環境を除去
    text = re.sub(r'\$[^$]+\$', '', text)
    text = re.sub(r'\\\[.*?\\\]', '', text, flags=re.DOTALL)
    text = re.sub(r'\\\(.*?\\\)', '', text, flags=re.DOTALL)
    # その他のLaTeXコマンドを除去（再帰的に処理）
    while True:
        new_text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
        if new_text == text:
            break
        text = new_text
    # 余分な空白を整理
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text


def extract_chapter_sections(tex_content: str, chapter_title: str) -> Dict[str, str]:
    """指定された章のセクションを抽出"""
    # 章の開始位置を検索
    chapter_pattern = rf'\\chapter\{{[^}}]*{re.escape(chapter_title)}[^}}]*\}}'
    chapter_match = re.search(chapter_pattern, tex_content)
    
    if not chapter_match:
        return {}
    
    start_pos = chapter_match.end()
    
    # 次の章の開始位置を検索
    next_chapter_match = re.search(r'\\chapter\{', tex_content[start_pos:])
    if next_chapter_match:
        end_pos = start_pos + next_chapter_match.start()
    else:
        end_pos = len(tex_content)
    
    chapter_text = tex_content[start_pos:end_pos]
    
    sections = {}
    
    # セクションを抽出
    section_pattern = r'\\section\{([^}]+)\}(.*?)(?=\\section\{|\\chapter\{|$)'
    for match in re.finditer(section_pattern, chapter_text, re.DOTALL):
        section_title = match.group(1)
        section_content = match.group(2)
        
        # サブセクションも抽出
        subsection_pattern = r'\\subsection\{([^}]+)\}(.*?)(?=\\subsection\{|\\section\{|$)'
        subsections = {}
        for sub_match in re.finditer(subsection_pattern, section_content, re.DOTALL):
            sub_title = sub_match.group(1)
            sub_content = sub_match.group(2)
            subsections[sub_title] = clean_latex_text(sub_content)
        
        sections[section_title] = {
            'content': clean_latex_text(section_content),
            'subsections': subsections
        }
    
    return sections


def extract_research_context(tex_path: Path) -> Dict[str, any]:
    """論文texファイルから研究背景を抽出"""
    with open(tex_path, 'r', encoding='utf-8') as f:
        tex_content = f.read()
    
    # タイトルと概要を抽出
    title = extract_latex_content(tex_content, 'maintitle')
    japanese_abstract = extract_latex_content(tex_content, 'jabst')
    
    # 序章を抽出
    introduction_sections = extract_chapter_sections(tex_content, '序章')
    
    # 関連研究を抽出
    related_work_sections = extract_chapter_sections(tex_content, '関連研究')
    
    # 提案を抽出
    proposal_sections = extract_chapter_sections(tex_content, '提案')
    
    return {
        'title': title,
        'abstract': japanese_abstract,
        'introduction': introduction_sections,
        'related_work': related_work_sections,
        'proposal': proposal_sections
    }


def format_as_markdown(context: Dict[str, any]) -> str:
    """抽出したコンテキストをMarkdown形式に整形"""
    md_lines = []
    
    md_lines.append("# 研究背景と経緯\n")
    md_lines.append(f"## 研究タイトル\n\n{context['title']}\n\n")
    
    md_lines.append("## 概要\n\n")
    md_lines.append(f"{context['abstract']}\n\n")
    
    md_lines.append("## 序章\n\n")
    for section_title, section_data in context['introduction'].items():
        md_lines.append(f"### {section_title}\n\n")
        if isinstance(section_data, dict) and 'content' in section_data:
            md_lines.append(f"{section_data['content']}\n\n")
            if section_data.get('subsections'):
                for sub_title, sub_content in section_data['subsections'].items():
                    md_lines.append(f"#### {sub_title}\n\n")
                    md_lines.append(f"{sub_content}\n\n")
        else:
            md_lines.append(f"{section_data}\n\n")
    
    md_lines.append("## 関連研究\n\n")
    for section_title, section_data in context['related_work'].items():
        md_lines.append(f"### {section_title}\n\n")
        if isinstance(section_data, dict) and 'content' in section_data:
            md_lines.append(f"{section_data['content']}\n\n")
            if section_data.get('subsections'):
                for sub_title, sub_content in section_data['subsections'].items():
                    md_lines.append(f"#### {sub_title}\n\n")
                    md_lines.append(f"{sub_content}\n\n")
        else:
            md_lines.append(f"{section_data}\n\n")
    
    md_lines.append("## 提案手法\n\n")
    for section_title, section_data in context['proposal'].items():
        md_lines.append(f"### {section_title}\n\n")
        if isinstance(section_data, dict) and 'content' in section_data:
            md_lines.append(f"{section_data['content']}\n\n")
        else:
            md_lines.append(f"{section_data}\n\n")
    
    return '\n'.join(md_lines)


def main():
    parser = argparse.ArgumentParser(description='論文texファイルから研究背景を抽出')
    parser.add_argument('--tex-file', type=str, default='論文/masterThesisJaSample.tex',
                       help='論文texファイルのパス')
    parser.add_argument('--output', type=str, default=None,
                       help='出力Markdownファイルのパス（デフォルト: analysis_workspace/research_context.md）')
    parser.add_argument('--workspace-dir', type=str, default=None,
                       help='analysis_workspaceディレクトリのパス')
    
    args = parser.parse_args()
    
    # パスを解決
    tex_path = Path(args.tex_file)
    if not tex_path.exists():
        # プロジェクトルートからの相対パスを試す
        project_root = Path(__file__).parent.parent.parent.parent.parent.parent
        tex_path = project_root / args.tex_file
        if not tex_path.exists():
            logger.error(f"論文texファイルが見つかりません: {args.tex_file}")
            return 1
    
    # 出力パスを決定
    if args.output:
        output_path = Path(args.output)
    elif args.workspace_dir:
        output_path = Path(args.workspace_dir) / "research_context.md"
    else:
        # デフォルト: プロジェクトルートのresults/20251119_153853/analysis_workspace/research_context.md
        project_root = Path(__file__).parent.parent.parent.parent.parent.parent
        output_path = project_root / "results/20251119_153853/analysis_workspace/research_context.md"
    
    logger.info(f"論文texファイルを読み込み: {tex_path}")
    context = extract_research_context(tex_path)
    
    logger.info("Markdown形式に変換中...")
    markdown_content = format_as_markdown(context)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    logger.info(f"研究背景を保存: {output_path}")
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

