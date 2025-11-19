#!/usr/bin/env python3
"""
実験結果考察スクリプト

実験結果JSONをLLMに読み込ませ、詳細な考察を行い、階層的にログをまとめてMDレポートを生成する。
"""

import json
import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import random

# パス設定
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src" / "analysis" / "experiments" / "utils"))

from LLM.llm_factory import LLMFactory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_research_context(context_path: Path) -> str:
    """研究背景を読み込み"""
    if not context_path.exists():
        logger.warning(f"研究背景ファイルが見つかりません: {context_path}")
        return ""
    
    with open(context_path, 'r', encoding='utf-8') as f:
        return f.read()


def sample_texts(texts: List[str], max_samples: int = 20) -> List[str]:
    """テキストリストからサンプルを抽出（長すぎる場合）"""
    if len(texts) <= max_samples:
        return texts
    
    # ランダムサンプリング
    return random.sample(texts, max_samples)


def format_experiment_data(exp_data: Dict[str, Any], max_samples: int = 20) -> str:
    """実験データを効率的にフォーマット"""
    lines = []
    
    exp_info = exp_data.get('experiment_info', {})
    input_data = exp_data.get('input', {})
    output_data = exp_data.get('output', {})
    scores = exp_data.get('scores', {})
    
    lines.append("## 実験設定")
    lines.append(f"- データセット: {exp_info.get('dataset', 'unknown')}")
    lines.append(f"- アスペクト: {exp_info.get('aspect', 'unknown')}")
    lines.append(f"- グループサイズ: {exp_info.get('group_size', 'unknown')}")
    lines.append(f"- Few-shot: {exp_info.get('input_data', {}).get('examples_count', 0)}")
    lines.append(f"- GPTモデル: {exp_info.get('model_config', {}).get('model', 'unknown')}")
    lines.append("")
    
    lines.append("## 入力データ")
    group_a = input_data.get('group_a', [])
    group_b = input_data.get('group_b', [])
    correct_answer = input_data.get('correct_answer', '')
    
    lines.append(f"### グループA（発火群）: {len(group_a)}件")
    lines.append("代表サンプル:")
    for i, text in enumerate(sample_texts(group_a, max_samples), 1):
        lines.append(f"{i}. {text[:200]}{'...' if len(text) > 200 else ''}")
    lines.append("")
    
    lines.append(f"### グループB（非発火群）: {len(group_b)}件")
    lines.append("代表サンプル:")
    for i, text in enumerate(sample_texts(group_b, max_samples), 1):
        lines.append(f"{i}. {text[:200]}{'...' if len(text) > 200 else ''}")
    lines.append("")
    
    if correct_answer:
        lines.append(f"### 正解ラベル: {correct_answer}")
        lines.append("")
    
    lines.append("## 出力結果")
    llm_response = output_data.get('llm_response', '')
    quality = output_data.get('quality_evaluation', '')
    
    lines.append(f"### LLM生成対比因子: {llm_response}")
    if quality:
        lines.append(f"### 品質評価: {quality}")
    lines.append("")
    
    lines.append("## 評価スコア")
    bert_score = scores.get('bert_score', 0)
    bleu_score = scores.get('bleu_score', 0)
    lines.append(f"- BERTスコア: {bert_score:.4f}")
    lines.append(f"- BLEUスコア: {bleu_score:.4f}")
    lines.append("")
    
    return '\n'.join(lines)


def generate_experiment_analysis_prompt(
    research_context: str,
    exp_data: Dict[str, Any],
    exp_config: Dict[str, Any]
) -> str:
    """個別実験考察用プロンプトを生成"""
    experiment_data_str = format_experiment_data(exp_data)
    
    prompt = f"""あなたは説明可能AIの研究における実験結果の分析専門家です。以下の研究背景と実験結果を詳細に考察してください。

# 研究背景

{research_context}

# 実験結果

{experiment_data_str}

# 考察指示

以下の観点から、この実験結果を詳細に分析してください：

1. **単語レベルでの特徴分析**
   - グループAとグループBのテキストを単語レベルで比較し、グループAに特徴的な単語・表現を特定してください
   - 特定された単語がどのような文脈で使用されているか分析してください
   - 単語の意味的ニュアンスや感情的な側面も考察してください

2. **文脈・意味的ニュアンスの考察**
   - グループAのテキスト群が共通して持つ文脈的特徴を分析してください
   - グループBとの違いがどのような意味的・概念的差異を表しているか考察してください
   - 抽象的な概念や間接的な表現の有無を分析してください

3. **正解ラベルとの比較**
   - LLMが生成した対比因子が正解ラベルとどの程度一致しているか評価してください
   - 一致している部分と不一致の部分を具体的に指摘してください
   - BERTスコアとBLEUスコアの乖離の原因を考察してください

4. **実験設定の影響**
   - Few-shot設定が出力に与えた影響を分析してください
   - グループサイズやデータセットの特性が結果に与えた影響を考察してください

5. **改善の示唆**
   - この実験結果から得られる知見や改善の方向性を提示してください

考察は日本語で、具体的かつ詳細に記述してください。単語レベルでの分析を特に重視し、具体例を交えて説明してください。
"""
    
    return prompt


def generate_category_analysis_prompt(
    category_name: str,
    category_description: str,
    experiment_logs: List[Dict[str, Any]]
) -> str:
    """カテゴリ単位考察用プロンプトを生成"""
    logs_text = "\n\n".join([
        f"## 実験 {i+1}: {log['experiment_id']}\n\n{log['analysis']}"
        for i, log in enumerate(experiment_logs)
    ])
    
    prompt = f"""あなたは説明可能AIの研究における実験結果の分析専門家です。以下の実験カテゴリの個別実験考察をまとめて、カテゴリ全体の傾向・パターン・洞察を抽出してください。

# 実験カテゴリ

**カテゴリ名**: {category_name}
**説明**: {category_description}

# 個別実験の考察ログ

{logs_text}

# 考察指示

以下の観点から、このカテゴリ全体の実験結果を分析してください：

1. **カテゴリ全体の傾向**
   - 個別実験の考察から見られる共通パターンを抽出してください
   - データセットやアスペクトによる違いを分析してください

2. **パフォーマンスの特徴**
   - スコアの分布や傾向を分析してください
   - 高い/低いスコアの実験の特徴を比較してください

3. **設定パラメータの影響**
   - Few-shot、グループサイズ、モデルなどの設定が結果に与えた影響を分析してください

4. **洞察と示唆**
   - このカテゴリの実験から得られる主要な知見をまとめてください
   - 今後の研究への示唆を提示してください

考察は日本語で、カテゴリ全体の視点から包括的に記述してください。
"""
    
    return prompt


def save_analysis_log(
    log_dir: Path,
    experiment_id: str,
    analysis: str,
    metadata: Dict[str, Any]
) -> Path:
    """分析ログを保存"""
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"analysis_{timestamp}.log"
    
    log_data = {
        'experiment_id': experiment_id,
        'timestamp': timestamp,
        'analysis': analysis,
        'metadata': metadata
    }
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    return log_file


def analyze_individual_experiments(
    workspace_dir: Path,
    research_context: str,
    llm_client: Any,
    checkpoint_file: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """個別実験を考察"""
    main_list_path = workspace_dir / "main_experiments" / "experiment_list.json"
    sub_list_path = workspace_dir / "sub_experiments" / "experiment_list.json"
    
    # チェックポイントを読み込み
    completed_ids = set()
    if checkpoint_file and checkpoint_file.exists():
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
            completed_ids = set(checkpoint.get('completed_experiment_ids', []))
    
    results = []
    log_dir = workspace_dir / "logs"
    
    # メイン実験を処理
    if main_list_path.exists():
        with open(main_list_path, 'r', encoding='utf-8') as f:
            main_list = json.load(f)
        
        for exp_info in main_list.get('experiments', []):
            exp_id = exp_info['experiment_id']
            
            if exp_id in completed_ids:
                logger.info(f"スキップ（既に完了）: {exp_id}")
                continue
            
            if not exp_info.get('file_path'):
                logger.warning(f"ファイルパスが見つかりません: {exp_id}")
                continue
            
            exp_file = workspace_dir.parent / exp_info['file_path']
            if not exp_file.exists():
                logger.warning(f"実験ファイルが見つかりません: {exp_file}")
                continue
            
            logger.info(f"実験を分析中: {exp_id}")
            
            try:
                # 実験データを読み込み
                with open(exp_file, 'r', encoding='utf-8') as f:
                    exp_data = json.load(f)
                
                # プロンプト生成
                prompt = generate_experiment_analysis_prompt(
                    research_context,
                    exp_data,
                    exp_info.get('config', {})
                )
                
                # LLMに問い合わせ
                analysis = llm_client.ask(
                    prompt,
                    temperature=0.7,
                    max_tokens=2000
                )
                
                if not analysis:
                    logger.error(f"LLM応答が取得できませんでした: {exp_id}")
                    continue
                
                # ログを保存
                metadata = {
                    'experiment_config': exp_info.get('config', {}),
                    'scores': exp_data.get('scores', {})
                }
                log_file = save_analysis_log(
                    log_dir / exp_id,
                    exp_id,
                    analysis,
                    metadata
                )
                
                results.append({
                    'experiment_id': exp_id,
                    'type': 'main',
                    'analysis': analysis,
                    'log_file': str(log_file)
                })
                
                completed_ids.add(exp_id)
                
                # チェックポイントを更新
                if checkpoint_file:
                    checkpoint_data = {
                        'completed_experiment_ids': list(completed_ids),
                        'last_updated': datetime.now().isoformat()
                    }
                    with open(checkpoint_file, 'w', encoding='utf-8') as f:
                        json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"完了: {exp_id}")
                
            except Exception as e:
                logger.error(f"エラーが発生しました ({exp_id}): {e}", exc_info=True)
                continue
    
    # サブ実験を処理
    if sub_list_path.exists():
        with open(sub_list_path, 'r', encoding='utf-8') as f:
            sub_list = json.load(f)
        
        for category_data in sub_list.get('categories', {}).values():
            for exp_info in category_data.get('experiments', []):
                exp_id = exp_info['experiment_id']
                
                if exp_id in completed_ids:
                    logger.info(f"スキップ（既に完了）: {exp_id}")
                    continue
                
                if not exp_info.get('file_path'):
                    logger.warning(f"ファイルパスが見つかりません: {exp_id}")
                    continue
                
                exp_file = workspace_dir.parent / exp_info['file_path']
                if not exp_file.exists():
                    logger.warning(f"実験ファイルが見つかりません: {exp_file}")
                    continue
                
                logger.info(f"実験を分析中: {exp_id}")
                
                try:
                    # 実験データを読み込み
                    with open(exp_file, 'r', encoding='utf-8') as f:
                        exp_data = json.load(f)
                    
                    # プロンプト生成
                    prompt = generate_experiment_analysis_prompt(
                        research_context,
                        exp_data,
                        exp_info.get('config', {})
                    )
                    
                    # LLMに問い合わせ
                    analysis = llm_client.ask(
                        prompt,
                        temperature=0.7,
                        max_tokens=2000
                    )
                    
                    if not analysis:
                        logger.error(f"LLM応答が取得できませんでした: {exp_id}")
                        continue
                    
                    # ログを保存
                    metadata = {
                        'experiment_config': exp_info.get('config', {}),
                        'scores': exp_data.get('scores', {})
                    }
                    log_file = save_analysis_log(
                        log_dir / exp_id,
                        exp_id,
                        analysis,
                        metadata
                    )
                    
                    results.append({
                        'experiment_id': exp_id,
                        'type': 'sub',
                        'analysis': analysis,
                        'log_file': str(log_file)
                    })
                    
                    completed_ids.add(exp_id)
                    
                    # チェックポイントを更新
                    if checkpoint_file:
                        checkpoint_data = {
                            'completed_experiment_ids': list(completed_ids),
                            'last_updated': datetime.now().isoformat()
                        }
                        with open(checkpoint_file, 'w', encoding='utf-8') as f:
                            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"完了: {exp_id}")
                    
                except Exception as e:
                    logger.error(f"エラーが発生しました ({exp_id}): {e}", exc_info=True)
                    continue
    
    return results


def analyze_categories(
    workspace_dir: Path,
    individual_results: List[Dict[str, Any]],
    llm_client: Any
) -> Dict[str, str]:
    """カテゴリ単位で考察"""
    metadata_path = workspace_dir / "metadata.json"
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    category_analyses = {}
    log_dir = workspace_dir / "logs"
    
    # メイン実験全体
    main_experiments = [r for r in individual_results if r.get('type') == 'main']
    if main_experiments:
        logger.info("メイン実験全体を分析中...")
        prompt = generate_category_analysis_prompt(
            "メイン実験",
            "データセット別性能比較（group_size=100統一）",
            main_experiments
        )
        
        analysis = llm_client.ask(prompt, temperature=0.7, max_tokens=2000)
        if analysis:
            category_analyses['main'] = analysis
            save_analysis_log(
                log_dir / "category_main",
                "main_experiments",
                analysis,
                {'count': len(main_experiments)}
            )
    
    # サブ実験カテゴリ
    sub_list_path = workspace_dir / "sub_experiments" / "experiment_list.json"
    if sub_list_path.exists():
        with open(sub_list_path, 'r', encoding='utf-8') as f:
            sub_list = json.load(f)
        
        for category_name, category_data in sub_list.get('categories', {}).items():
            category_experiments = [
                r for r in individual_results
                if r['experiment_id'] in [e['experiment_id'] for e in category_data.get('experiments', [])]
            ]
            
            if category_experiments:
                logger.info(f"カテゴリを分析中: {category_name}")
                description = metadata.get('experiment_plan', {}).get('sub_experiment_settings', {}).get(
                    category_name.replace('_', ''), {}
                ).get('purpose', f"{category_name}の実験")
                
                prompt = generate_category_analysis_prompt(
                    category_name,
                    description,
                    category_experiments
                )
                
                analysis = llm_client.ask(prompt, temperature=0.7, max_tokens=2000)
                if analysis:
                    category_analyses[category_name] = analysis
                    save_analysis_log(
                        log_dir / f"category_{category_name}",
                        category_name,
                        analysis,
                        {'count': len(category_experiments)}
                    )
    
    return category_analyses


def generate_md_reports(
    workspace_dir: Path,
    individual_results: List[Dict[str, Any]],
    category_analyses: Dict[str, str]
):
    """MDレポートを生成"""
    reports_dir = workspace_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    for result in individual_results:
        exp_id = result['experiment_id']
        analysis = result['analysis']
        
        md_content = f"""# 実験考察レポート: {exp_id}

## 個別実験の詳細考察

{analysis}

"""
        
        # カテゴリ単位の考察も含める
        if result.get('type') == 'main':
            if 'main' in category_analyses:
                md_content += f"""## メイン実験全体の考察

{category_analyses['main']}

"""
        else:
            # サブ実験の場合、該当カテゴリの考察を追加
            sub_list_path = workspace_dir / "sub_experiments" / "experiment_list.json"
            if sub_list_path.exists():
                with open(sub_list_path, 'r', encoding='utf-8') as f:
                    sub_list = json.load(f)
                
                for category_name, category_data in sub_list.get('categories', {}).items():
                    if any(e['experiment_id'] == exp_id for e in category_data.get('experiments', [])):
                        if category_name in category_analyses:
                            md_content += f"""## {category_name}カテゴリ全体の考察

{category_analyses[category_name]}

"""
                        break
        
        report_file = reports_dir / f"{exp_id}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"レポート生成: {report_file}")


def main():
    parser = argparse.ArgumentParser(description='実験結果をLLMで考察し、MDレポートを生成')
    parser.add_argument('--workspace-dir', type=str, required=True,
                       help='analysis_workspaceディレクトリのパス')
    parser.add_argument('--model', type=str, default='gpt-5.1',
                       help='使用するLLMモデル（デフォルト: gpt-5.1）')
    parser.add_argument('--skip-individual', action='store_true',
                       help='個別実験の考察をスキップ')
    parser.add_argument('--skip-category', action='store_true',
                       help='カテゴリ単位の考察をスキップ')
    parser.add_argument('--skip-reports', action='store_true',
                       help='MDレポート生成をスキップ')
    
    args = parser.parse_args()
    
    workspace_dir = Path(args.workspace_dir)
    if not workspace_dir.exists():
        logger.error(f"workspaceディレクトリが見つかりません: {workspace_dir}")
        return 1
    
    # 研究背景を読み込み
    context_path = workspace_dir / "research_context.md"
    research_context = load_research_context(context_path)
    
    if not research_context:
        logger.warning("研究背景が読み込めませんでした。続行しますが、プロンプトに含まれません。")
    
    # LLMクライアントを作成
    try:
        llm_client = LLMFactory.create_client(model_name=args.model, debug=False)
        logger.info(f"LLMクライアント作成: {args.model}")
    except Exception as e:
        logger.error(f"LLMクライアントの作成に失敗しました: {e}")
        # gpt-5.1が使えない場合はgpt-4oにフォールバック
        logger.info("gpt-4oにフォールバックします")
        try:
            llm_client = LLMFactory.create_client(model_name='gpt-4o', debug=False)
        except Exception as e2:
            logger.error(f"フォールバックも失敗しました: {e2}")
            return 1
    
    checkpoint_file = workspace_dir / "analysis_checkpoint.json"
    
    # 個別実験の考察
    individual_results = []
    if not args.skip_individual:
        logger.info("個別実験の考察を開始...")
        individual_results = analyze_individual_experiments(
            workspace_dir,
            research_context,
            llm_client,
            checkpoint_file
        )
        logger.info(f"個別実験の考察完了: {len(individual_results)}件")
    else:
        # 既存のログから読み込み
        log_dir = workspace_dir / "logs"
        if log_dir.exists():
            for exp_dir in log_dir.iterdir():
                if exp_dir.is_dir() and not exp_dir.name.startswith('category_'):
                    exp_id = exp_dir.name
                    log_files = sorted(exp_dir.glob("analysis_*.log"))
                    if log_files:
                        with open(log_files[-1], 'r', encoding='utf-8') as f:
                            log_data = json.load(f)
                            individual_results.append({
                                'experiment_id': exp_id,
                                'type': 'main' if 'main' in exp_id else 'sub',
                                'analysis': log_data.get('analysis', ''),
                                'log_file': str(log_files[-1])
                            })
    
    # カテゴリ単位の考察
    category_analyses = {}
    if not args.skip_category and individual_results:
        logger.info("カテゴリ単位の考察を開始...")
        category_analyses = analyze_categories(
            workspace_dir,
            individual_results,
            llm_client
        )
        logger.info(f"カテゴリ単位の考察完了: {len(category_analyses)}件")
    
    # MDレポート生成
    if not args.skip_reports and individual_results:
        logger.info("MDレポートを生成中...")
        generate_md_reports(workspace_dir, individual_results, category_analyses)
        logger.info("MDレポート生成完了")
    
    logger.info("=" * 60)
    logger.info("すべての処理が完了しました")
    logger.info(f"個別実験: {len(individual_results)}件")
    logger.info(f"カテゴリ考察: {len(category_analyses)}件")
    logger.info("=" * 60)
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

