#!/usr/bin/env python3
"""
追加実験に関する考察を一つのMarkdownファイルにまとめるスクリプト

論文執筆用ディレクトリから全ての追加実験の考察を抽出し、
一つの包括的なMarkdownファイルにまとめる
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent.parent
EXPERIMENT_BASE = PROJECT_ROOT / "論文" / "結果" / "追加実験" / "論文執筆用"
OUTPUT_DIR = PROJECT_ROOT / "論文" / "実験結果集約"

# 実験とその分析レポートファイルのマッピング
EXPERIMENT_ANALYSIS_FILES = {
    "モデル比較実験": {
        "file": EXPERIMENT_BASE / "model_comparison_temperature0" / "分析レポート" / "model_comparison_temperature0_analysis.md",
        "description": "gpt-4o-mini と gpt-5.1 の性能比較（temperature=0設定）"
    },
    "Few-shot実験（LLM評価有効）": {
        "file": EXPERIMENT_BASE / "fewshot_llm_eval" / "steam" / "分析レポート" / "fewshot_llm_eval_analysis.md",
        "description": "Few-shot設定（0-shot, 1-shot, 3-shot）の性能比較（LLM評価指標を含む）"
    },
    "Group Size比較実験": {
        "file": EXPERIMENT_BASE / "group_size_comparison" / "steam" / "分析レポート" / "group_size_comparison_analysis.md",
        "description": "グループサイズ（50/100/150/200/300）が対比因子生成性能に与える影響の調査"
    },
    "アスペクト説明文比較実験": {
        "file": EXPERIMENT_BASE / "aspect_description_comparison" / "steam" / "分析レポート" / "aspect_description_comparison_analysis.md",
        "description": "アスペクト説明文の有無が対比因子抽出の性能に与える影響の検証"
    },
    "データセット別性能比較実験": {
        "file": EXPERIMENT_BASE / "dataset_comparison" / "分析レポート" / "dataset_comparison_analysis.md",
        "description": "Steam、SemEval、GoEmotionsの3つのデータセット間での性能比較（0-shot設定）"
    },
    "COCO Retrieved Concepts実験": {
        "file": EXPERIMENT_BASE / "coco_retrieved_concepts" / "分析レポート" / "coco_analysis_with_images.md",
        "description": "COCOデータセットを使用した対比因子生成実験（画像付き考察）"
    }
}


def load_markdown(file_path: Path) -> Optional[str]:
    """Markdownファイルを読み込む"""
    try:
        if not file_path.exists():
            print(f"警告: ファイルが見つかりません: {file_path}")
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"警告: {file_path} の読み込みに失敗: {e}")
        return None


def extract_discussion_section(content: str, experiment_name: str) -> str:
    """Markdownコンテンツから考察セクションを抽出"""
    lines = content.split('\n')
    
    # COCO実験の場合は、最初のconcept_0から最後のconcept_50まで全て含める
    if experiment_name == "COCO Retrieved Concepts実験":
        # concept_0から始まる行を探す
        start_idx = None
        for i, line in enumerate(lines):
            if line.startswith('## concept_0'):
                start_idx = i
                break
        
        if start_idx is None:
            print(f"警告: {experiment_name} でconcept_0が見つかりません。全体を抽出します。")
            return content
        
        # concept_0から最後まで全て含める（concept_50の参照画像セクションまで）
        extracted_lines = []
        for i in range(start_idx, len(lines)):
            extracted_lines.append(lines[i])
        
        return '\n'.join(extracted_lines)
    
    # その他の実験の場合
    # 考察セクションの開始パターンを探す
    discussion_start_patterns = [
        "## LLMによる考察",
        "## LLM による考察",
        "## 考察",
        "## 主要な発見",
        "## 画像との整合性考察",
        "### 画像との整合性考察"
    ]
    
    start_idx = None
    for i, line in enumerate(lines):
        for pattern in discussion_start_patterns:
            if pattern in line:
                start_idx = i
                break
        if start_idx is not None:
            break
    
    if start_idx is None:
        # 考察セクションが見つからない場合、全体を返す
        print(f"警告: {experiment_name} で考察セクションが見つかりません。全体を抽出します。")
        return content
    
    # 次の主要セクション（## で始まる）までを抽出
    extracted_lines = [lines[start_idx]]
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        # 次の主要セクション（## で始まる）が見つかったら終了
        if line.startswith('## ') and i > start_idx + 1:
            break
        extracted_lines.append(line)
    
    return '\n'.join(extracted_lines)


def generate_discussion_document() -> str:
    """追加実験の考察をまとめたMarkdownドキュメントを生成"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    doc_lines = [
        "# 追加実験に関する考察 - 統合レポート",
        "",
        f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "このドキュメントは、追加実験に関する全ての考察を一つのファイルにまとめたものです。",
        "",
        "---",
        "",
        "## 目次",
        ""
    ]
    
    # 目次を生成
    for i, exp_name in enumerate(EXPERIMENT_ANALYSIS_FILES.keys(), 1):
        anchor = exp_name.replace(' ', '-').replace('（', '').replace('）', '')
        doc_lines.append(f"{i}. [{exp_name}](#{anchor})")
    
    doc_lines.extend([
        "",
        "---",
        ""
    ])
    
    # 各実験の考察を追加
    for exp_name, exp_info in EXPERIMENT_ANALYSIS_FILES.items():
        doc_lines.extend([
            f"## {exp_name}",
            "",
            f"**実験の説明**: {exp_info['description']}",
            "",
            "---",
            ""
        ])
        
        content = load_markdown(exp_info['file'])
        if content:
            discussion = extract_discussion_section(content, exp_name)
            doc_lines.append(discussion)
        else:
            doc_lines.append(f"*警告: {exp_info['file']} の読み込みに失敗しました*")
        
        doc_lines.extend([
            "",
            "---",
            ""
        ])
    
    # 統合的考察セクションを追加
    doc_lines.extend([
        "## 統合的考察",
        "",
        "### 実験間の関係性",
        "",
        "1. **モデル比較実験**は、**Few-shot実験**の0-shot設定でのモデル間比較を実施",
        "2. **Few-shot実験（LLM評価有効）**は、評価指標にLLM評価を含む多角的な評価を実施",
        "3. **Group Size比較実験**は、Few-shot実験の0-shot設定と同じ条件で、グループサイズのみを変化させた実験",
        "4. **アスペクト説明文比較実験**は、プロンプト設計の影響を検証",
        "5. **データセット別性能比較実験**は、データセット特性が性能に与える影響を検証",
        "6. **COCO Retrieved Concepts実験**は、画像との整合性確認が対比因子生成の評価に有効であることを実証",
        "",
        "### 主要な発見の統合",
        "",
        "#### 1. Few-shot効果の確認",
        "",
        "- Few-shot設定が性能向上に明確に寄与（0-shot: 0.5526 → 1-shot: 0.6530 → 3-shot: 0.5754（BERT）、0.30 → 0.35 → 0.40（LLM））",
        "- 特に0-shotから1-shotへの移行で大きな性能向上が観察された",
        "- アスペクトによって最適なFew-shot設定が異なる（gameplay, story: 3-shot、visual, audio: 1-shot）",
        "",
        "#### 2. モデル選択の重要性",
        "",
        "- 平均性能ではモデル間の差は小さいが、アスペクトによって最適モデルが異なる",
        "- gpt-4o-miniとgpt-5.1の性能差は限定的（BERT: 0.5453 vs 0.5375）",
        "- 実用的には、アスペクト特性に応じたモデル選択が有効",
        "",
        "#### 3. 評価指標間のトレードオフ",
        "",
        "- BERTスコアとLLMスコアで最良設定が一致しない",
        "- BERTは「表層概念レベルの一致」、LLMスコアは「人間が読んだときの説明妥当性」に近い評価",
        "- 単一指標では性能を過小・過大評価しうるため、多角的な評価が必要",
        "",
        "#### 4. Group Sizeの影響",
        "",
        "- Group Size 50〜300の範囲で性能は概ねロバスト（変動幅約0.02）",
        "- Group Size 300でわずかに高いBERTスコアを示すが、決定的な差ではない",
        "- 実用的には100〜200程度がコストと性能のバランスが良い",
        "",
        "#### 5. プロンプト設計の影響",
        "",
        "- アスペクト説明文の追加により、BERTスコアとLLMスコアが向上（特にLLMスコアの改善幅が大きい）",
        "- アスペクトによって説明文の効果が異なる（audio, gameplayで顕著な改善、visualでは悪化）",
        "- 説明文の質が重要であり、汎用的すぎるとアスペクト固有性を損なう可能性",
        "",
        "#### 6. データセット特性の影響",
        "",
        "- データセット間で性能差が大きい（SemEval: 0.7481 > GoEmotions: 0.7055 >> Steam: 0.5328）",
        "- アスペクトの語彙的一貫性、A/Bの統計的差分の大きさ、抽象度の低さが性能に影響",
        "- データセット特性を事前に把握した上で、プロンプト設計を調整することが重要",
        "",
        "#### 7. 画像との整合性確認の重要性",
        "",
        "- COCO Retrieved Concepts実験により、画像との整合性確認が対比因子生成の評価に有効であることが実証された",
        "- テキストベースのBERTスコアだけでは捉えきれない視覚的・社会的コンテクストの違いを検出可能",
        "- 正解ラベルがないデータセットでも、画像との整合性確認により対比因子の妥当性を評価可能",
        "- 視覚的検証は、将来の画像モデルニューロン解釈への応用において重要な評価手法となる",
        "",
        "### 論文への反映ポイント",
        "",
        "1. **実験結果の提示順序**: まずFew-shot実験で性能向上の可能性を示し、次にモデル比較実験でモデル選択の重要性を示す",
        "2. **数値の引用**: 各実験の主要な数値結果を適切に引用",
        "3. **考察の引用**: LLM考察から主要な発見を引用し、統合的な解釈を提示",
        "4. **評価指標の位置づけ**: BERTスコアとLLMスコアの関係性を明確に説明",
        "5. **実用的な示唆**: 各実験から得られた実用的な設計指針を提示",
        "",
        "---",
        "",
        f"*このドキュメントは {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} に自動生成されました*"
    ])
    
    return '\n'.join(doc_lines)


def main():
    """メイン処理"""
    print("追加実験の考察を抽出中...")
    
    # 出力ディレクトリの確認
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # ドキュメントを生成
    document = generate_discussion_document()
    
    # ファイルに保存
    output_file = OUTPUT_DIR / "追加実験考察統合レポート.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(document)
    
    print(f"完了: {output_file}")
    print(f"  ファイルサイズ: {len(document)} 文字")
    print(f"  行数: {len(document.split(chr(10)))} 行")


if __name__ == "__main__":
    main()

