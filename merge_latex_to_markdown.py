#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LaTeXファイルをMarkdownに変換して1つのファイルにまとめるスクリプト
"""

import re
from pathlib import Path


def latex_to_markdown(text):
    """LaTeXコマンドをMarkdownに変換"""
    
    # 章見出し
    text = re.sub(r'\\chapter\{([^}]+)\}', r'# \1', text)
    
    # 節見出し
    text = re.sub(r'\\section\{([^}]+)\}', r'## \1', text)
    
    # 小節見出し
    text = re.sub(r'\\subsection\{([^}]+)\}', r'### \1', text)
    
    # 太字
    text = re.sub(r'\\textbf\{([^}]+)\}', r'**\1**', text)
    
    # 斜体
    text = re.sub(r'\\textit\{([^}]+)\}', r'*\1*', text)
    
    # 引用
    text = re.sub(r'~\\cite\{([^}]+)\}', r'[\1]', text)
    text = re.sub(r'\\cite\{([^}]+)\}', r'[\1]', text)
    
    # itemize環境
    def replace_itemize(match):
        content = match.group(1)
        items = re.findall(r'\\item\s+(.+?)(?=\\item|$)', content, re.DOTALL)
        result = []
        for item in items:
            item = item.strip()
            item = latex_to_markdown(item)  # 再帰的に処理
            result.append(f'- {item}')
        return '\n'.join(result) + '\n'
    
    text = re.sub(r'\\begin\{itemize\}(.*?)\\end\{itemize\}', replace_itemize, text, flags=re.DOTALL)
    
    # enumerate環境
    def replace_enumerate(match):
        content = match.group(1)
        items = re.findall(r'\\item\s+(.+?)(?=\\item|$)', content, re.DOTALL)
        result = []
        for i, item in enumerate(items, 1):
            item = item.strip()
            item = latex_to_markdown(item)  # 再帰的に処理
            result.append(f'{i}. {item}')
        return '\n'.join(result) + '\n'
    
    text = re.sub(r'\\begin\{enumerate\}(.*?)\\end\{enumerate\}', replace_enumerate, text, flags=re.DOTALL)
    
    # verbatim環境（コードブロック）
    text = re.sub(r'\\begin\{verbatim\}(.*?)\\end\{verbatim\}', r'```\n\1\n```', text, flags=re.DOTALL)
    
    # 数式（インライン）
    text = re.sub(r'\$([^$]+)\$', r'$\1$', text)
    
    # 数式（ブロック）- そのまま残す
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    
    # 図の参照
    text = re.sub(r'図~\\ref\{([^}]+)\}', r'図\1', text)
    
    # その他のLaTeXコマンドを削除または簡略化
    text = re.sub(r'\\mbox\{([^}]+)\}', r'\1', text)
    text = re.sub(r'\\texttt\{([^}]+)\}', r'`\1`', text)
    text = re.sub(r'\\mathrm\{([^}]+)\}', r'\1', text)
    
    # コメント行を削除
    text = re.sub(r'%.*', '', text)
    
    # 空行を整理
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text


def process_references(text):
    """参考文献セクションを処理"""
    # bibitemをMarkdown形式に変換
    def replace_bibitem(match):
        key = match.group(1)
        content = match.group(2)
        # LaTeXコマンドを簡略化
        content = re.sub(r'\\textit\{([^}]+)\}', r'*\1*', content)
        content = re.sub(r'\\url\{([^}]+)\}', r'\1', content)
        content = re.sub(r'~', ' ', content)
        content = re.sub(r'\\&', '&', content)
        content = re.sub(r'\\c\{c\}', 'ç', content)
        content = re.sub(r'\\"u', 'ü', content)
        content = re.sub(r'\\"o', 'ö', content)
        content = re.sub(r'\\"a', 'ä', content)
        content = re.sub(r'\\L', 'Ł', content)
        content = re.sub(r'\{([^}]+)\}', r'\1', content)  # 残りの{}を削除
        content = re.sub(r'\\', '', content)  # 残りのバックスラッシュを削除
        return f'- **{key}**: {content.strip()}\n'
    
    text = re.sub(r'\\bibitem\{([^}]+)\}\s*\n(.*?)(?=\\bibitem|\\end)', replace_bibitem, text, flags=re.DOTALL)
    
    # 参考文献の開始部分をMarkdown見出しに
    text = re.sub(r'\\begin\{thebibliography\}.*?\n', '# 参考文献\n\n', text)
    text = re.sub(r'\\end\{thebibliography\}', '', text)
    
    return text


def main():
    """メイン処理"""
    base_dir = Path('/Users/seinoshun/imrb_research')
    
    # 処理するファイルの順序
    files = [
        base_dir / '論文/chapters/01_introduction.tex',
        base_dir / '論文/chapters/02_related_work.tex',
        base_dir / '論文/chapters/03_proposal.tex',
        base_dir / '論文/chapters/04_experiment.tex',
        base_dir / '論文/chapters/05_results_and_discussion.tex',
        base_dir / '論文/chapters/06_discussion.tex',
        base_dir / '論文/chapters/07_conclusion.tex',
        base_dir / '論文/chapters/08_acknowledgments.tex',
        base_dir / '論文/chapters/09_references.tex',
    ]
    
    output_file = base_dir / '論文_統合.md'
    
    markdown_parts = []
    
    for file_path in files:
        if not file_path.exists():
            print(f"警告: ファイルが見つかりません: {file_path}")
            continue
        
        print(f"処理中: {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 参考文献ファイルの場合は特別処理
        if 'references' in file_path.name:
            content = process_references(content)
        else:
            content = latex_to_markdown(content)
        
        # ファイル名をセクションとして追加
        markdown_parts.append(f'<!-- {file_path.name} -->\n\n{content}\n\n')
    
    # 全ての部分を結合
    final_markdown = '\n'.join(markdown_parts)
    
    # 出力
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_markdown)
    
    print(f"\n完了: {output_file} に出力しました")


if __name__ == '__main__':
    main()

