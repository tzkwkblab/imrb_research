#!/usr/bin/env python3
"""
実験結果考察スクリプト

実験結果JSONをLLMに読み込ませ、詳細な考察を行い、階層的にログをまとめてMDレポートを生成する。
"""

import json
import argparse
import logging
import sys
import os
import signal
import atexit
import time
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

# グローバル変数
_cleanup_registered = False
MAX_PARALLEL_PROCESSES = 3
GLOBAL_LOCK_DIR = Path("/tmp/imrb_analysis_locks")
GLOBAL_LOCK_DIR.mkdir(parents=True, exist_ok=True)


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
    exp_config: Dict[str, Any],
    experiment_context: Optional[Dict[str, Any]] = None
) -> str:
    """個別実験考察用プロンプトを生成"""
    experiment_data_str = format_experiment_data(exp_data)
    
    # 実験の立ち位置・役割をコンテキストとして追加
    context_section = ""
    if experiment_context:
        context_lines = []
        context_lines.append("## 実験の立ち位置と役割")
        
        exp_type = experiment_context.get('type', 'unknown')
        if exp_type == 'main':
            context_lines.append("- **実験タイプ**: メイン実験")
            context_lines.append("- **役割**: データセット別性能比較のための標準実験")
            context_lines.append("- **設定**: group_size=100で統一され、データセット間の比較を可能にする")
        elif exp_type == 'sub':
            category_name = experiment_context.get('category_name', 'unknown')
            category_description = experiment_context.get('category_description', '')
            category_purpose = experiment_context.get('category_purpose', '')
            
            context_lines.append(f"- **実験タイプ**: サブ実験（カテゴリ: {category_name}）")
            if category_description:
                context_lines.append(f"- **カテゴリ説明**: {category_description}")
            if category_purpose:
                context_lines.append(f"- **カテゴリの目的**: {category_purpose}")
            
            # カテゴリ別の詳細説明
            if category_name == 'steam_group_size':
                context_lines.append("- **この実験の役割**: Steamデータセットにおけるgroup_size変化による影響調査の一部")
                context_lines.append("- **実験計画での位置づけ**: 異なるgroup_size（50/100/150/200/300）での性能比較により、最適なグループサイズを探索")
            elif category_name == 'steam_gpt51':
                context_lines.append("- **この実験の役割**: Steamデータセットにおけるgpt-5.1モデルの性能検証")
                context_lines.append("- **実験計画での位置づけ**: group_size=300でのgpt-5.1の性能を検証し、gpt-4o-miniとの比較を行う")
            elif category_name == 'retrieved_concepts':
                context_lines.append("- **この実験の役割**: 正解のないデータセットに対する対比因子生成の考察")
                context_lines.append("- **実験計画での位置づけ**: 正解ラベルがない場合の対比因子生成の妥当性を検証（スコアは参考値、出力内容の質を重視）")
        
        overall_description = experiment_context.get('overall_description', '')
        if overall_description:
            context_lines.append("")
            context_lines.append("## 実験計画全体での位置づけ")
            context_lines.append(overall_description)
        
        context_section = "\n".join(context_lines) + "\n\n"
    
    prompt = f"""あなたは説明可能AIの研究における実験結果の分析専門家です。以下の研究背景と実験結果を詳細に考察してください。

# 研究背景

{research_context}

# 実験のコンテキスト

{context_section}# 実験結果

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
    checkpoint_file: Optional[Path] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """個別実験を考察"""
    main_list_path = workspace_dir / "main_experiments" / "experiment_list.json"
    sub_list_path = workspace_dir / "sub_experiments" / "experiment_list.json"
    
    # メタデータを読み込み
    if metadata is None:
        metadata_path = workspace_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {}
    
    experiment_plan = metadata.get('experiment_plan', {})
    overall_description = experiment_plan.get('description', '')
    sub_experiment_settings = experiment_plan.get('sub_experiment_settings', {})
    
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
                
                # 実験コンテキストを構築
                experiment_context = {
                    'type': 'main',
                    'overall_description': overall_description
                }
                
                # プロンプト生成
                prompt = generate_experiment_analysis_prompt(
                    research_context,
                    exp_data,
                    exp_info.get('config', {}),
                    experiment_context
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
        
        for category_name, category_data in sub_list.get('categories', {}).items():
            # カテゴリの説明を取得
            category_description = None
            category_purpose = None
            
            if category_name == 'steam_group_size':
                category_description = "Steamデータセットにおけるgroup_size変化による影響調査"
                steam_settings = sub_experiment_settings.get('steam', {})
                if steam_settings:
                    category_purpose = f"group_sizeを変化させて（50/100/150/200/300）、最適なグループサイズを探索"
            elif category_name == 'steam_gpt51':
                category_description = "Steamデータセットにおけるgpt-5.1モデルの性能検証"
                category_purpose = "group_size=300でのgpt-5.1の性能を検証し、gpt-4o-miniとの比較を行う"
            elif category_name == 'retrieved_concepts':
                retrieved_settings = sub_experiment_settings.get('retrieved_concepts', {})
                category_description = retrieved_settings.get('purpose', '正解のないデータセットに対する対比因子生成の考察')
                category_purpose = retrieved_settings.get('note', 'スコアは参考値、出力された対比因子と画像を見比べて考察')
            
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
                    
                    # 実験コンテキストを構築
                    experiment_context = {
                        'type': 'sub',
                        'category_name': category_name or 'unknown',
                        'category_description': category_description or '',
                        'category_purpose': category_purpose or '',
                        'overall_description': overall_description
                    }
                    
                    # プロンプト生成
                    prompt = generate_experiment_analysis_prompt(
                        research_context,
                        exp_data,
                        exp_info.get('config', {}),
                        experiment_context
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


def save_pid(pid_file: Path):
    """PIDファイルを保存"""
    try:
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
        atexit.register(cleanup_pid, pid_file)
    except Exception as e:
        logger.warning(f"PIDファイル保存エラー: {e}")


def cleanup_pid(pid_file: Path):
    """PIDファイルを削除"""
    try:
        if pid_file.exists():
            pid_file.unlink()
    except Exception:
        pass


def load_pid(pid_file: Path) -> Optional[int]:
    """PIDファイルからPIDを読み込み"""
    try:
        if pid_file.exists():
            with open(pid_file, 'r') as f:
                return int(f.read().strip())
    except Exception:
        pass
    return None


def is_process_running(pid: int) -> bool:
    """プロセスが実行中か確認"""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def stop_process(pid_file: Path) -> bool:
    """実行中のプロセスを停止（子プロセスも含む）"""
    pid = load_pid(pid_file)
    if pid is None:
        print(f"PIDファイルが見つかりません: {pid_file}")
        return False
    
    if not is_process_running(pid):
        print(f"プロセス {pid} は実行されていません")
        cleanup_pid(pid_file)
        return False
    
    try:
        import psutil
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            print(f"親プロセス {pid} と子プロセス {len(children)} 個を停止中...")
            
            for child in children:
                try:
                    child.terminate()
                except Exception:
                    pass
            
            parent.terminate()
            time.sleep(2)
            
            for child in children:
                try:
                    if child.is_running():
                        child.kill()
                except Exception:
                    pass
            
            if parent.is_running():
                parent.kill()
            
            print(f"プロセス {pid} と子プロセスを停止しました")
        except ImportError:
            os.kill(pid, signal.SIGTERM)
            print(f"プロセス {pid} に停止シグナルを送信しました")
            time.sleep(1)
            
            if is_process_running(pid):
                os.kill(pid, signal.SIGKILL)
                print(f"プロセス {pid} を強制終了しました")
        
        cleanup_pid(pid_file)
        return True
    except Exception as e:
        print(f"プロセス停止エラー: {e}")
        return False


def check_status(pid_file: Path, workspace_dir: Path) -> int:
    """実行状態を確認"""
    pid = load_pid(pid_file)
    if pid is None:
        print("実行中のプロセスはありません")
        return 1
    
    if not is_process_running(pid):
        print(f"プロセス {pid} は実行されていません（PIDファイルが残っています）")
        cleanup_pid(pid_file)
        return 1
    
    log_file = workspace_dir / "analysis.log"
    checkpoint_file = workspace_dir / "analysis_checkpoint.json"
    
    print(f"実行中: PID {pid}")
    print(f"ワークスペース: {workspace_dir}")
    
    if log_file.exists():
        log_size = log_file.stat().st_size
        print(f"ログファイル: {log_file} ({log_size:,} bytes)")
        print(f"\n最新のログ（最後の20行）:")
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-20:]:
                    print(line.rstrip())
        except Exception:
            pass
    
    if checkpoint_file.exists():
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            completed = len(checkpoint_data.get('completed_experiment_ids', []))
            last_updated = checkpoint_data.get('last_updated', 'unknown')
            print(f"\n完了済み実験数: {completed}")
            print(f"最終更新: {last_updated}")
        except Exception:
            pass
    
    return 0


def daemonize(log_file: str) -> int:
    """
    プロセスをデーモン化（Unix系のみ）
    
    Args:
        log_file: ログファイルの絶対パス（文字列）
    
    Returns:
        子プロセスのPID（親プロセスのみ）
    """
    if os.name == 'nt':
        raise RuntimeError("バックグラウンド実行はUnix系システムでのみサポートされています")
    
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        pid = os.fork()
        if pid > 0:
            return pid
    except OSError as e:
        sys.stderr.write(f"fork failed: {e}\n")
        sys.exit(1)
    
    os.chdir("/")
    os.setsid()
    os.umask(0)
    
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"fork failed: {e}\n")
        sys.exit(1)
    
    sys.stdout.flush()
    sys.stderr.flush()
    
    si = open(os.devnull, 'r')
    so = open(log_file, 'a+')
    se = open(log_file, 'a+', 1)
    
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())
    
    return 0


def acquire_workspace_lock(workspace_dir: Path) -> Optional[Path]:
    """ワークスペースのロックを取得"""
    workspace_lock_file = GLOBAL_LOCK_DIR / f"workspace_{workspace_dir.resolve().name}.lock"
    
    if workspace_lock_file.exists():
        pid = load_pid(workspace_lock_file)
        if pid and is_process_running(pid):
            return None
    
    save_pid(workspace_lock_file)
    return workspace_lock_file


def release_workspace_lock(lock_file: Optional[Path]):
    """ワークスペースのロックを解放"""
    if lock_file:
        cleanup_pid(lock_file)


def check_parallel_limit() -> bool:
    """並列実行数の上限をチェック"""
    running_count = 0
    for lock_file in GLOBAL_LOCK_DIR.glob("*.lock"):
        pid = load_pid(lock_file)
        if pid and is_process_running(pid):
            running_count += 1
    
    return running_count < MAX_PARALLEL_PROCESSES


def register_cleanup_handlers(pid_file: Path, workspace_lock_file: Optional[Path]):
    """クリーンアップハンドラを登録"""
    global _cleanup_registered
    
    if _cleanup_registered:
        return
    
    def signal_handler(signum, frame):
        logger.warning(f"シグナル {signum} を受信しました。クリーンアップを実行します...")
        cleanup_pid(pid_file)
        release_workspace_lock(workspace_lock_file)
        sys.exit(130 if signum == signal.SIGINT else 143)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    atexit.register(cleanup_pid, pid_file)
    atexit.register(release_workspace_lock, workspace_lock_file)
    _cleanup_registered = True


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
    parser.add_argument('--background', action='store_true',
                       help='バックグラウンドで実行')
    parser.add_argument('--status', action='store_true',
                       help='実行状態を確認')
    parser.add_argument('--stop', action='store_true',
                       help='実行中のプロセスを停止')
    parser.add_argument('--debug', action='store_true',
                       help='デバッグログを有効化')
    
    args = parser.parse_args()
    
    workspace_dir = Path(args.workspace_dir).resolve()
    if not workspace_dir.exists():
        logger.error(f"workspaceディレクトリが見つかりません: {workspace_dir}")
        return 1
    
    pid_file = workspace_dir / "analysis.pid"
    
    # 状態確認
    if args.status:
        return check_status(pid_file, workspace_dir)
    
    # プロセス停止
    if args.stop:
        if stop_process(pid_file):
            return 0
        return 1
    
    # ログレベル設定
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    # バックグラウンド実行の場合
    if args.background:
        # 既に実行中の場合はエラー
        if pid_file.exists():
            pid = load_pid(pid_file)
            if pid and is_process_running(pid):
                print(f"既に実行中のプロセスがあります: PID {pid}")
                print(f"状態確認: python {sys.argv[0]} --status --workspace-dir {workspace_dir}")
                print(f"停止: python {sys.argv[0]} --stop --workspace-dir {workspace_dir}")
                return 1
        
        # 並列実行数の上限チェック
        if not check_parallel_limit():
            print(f"並列実行数の上限（{MAX_PARALLEL_PROCESSES}プロセス）に達しています")
            return 1
        
        # ワークスペースロック取得
        workspace_lock_file = acquire_workspace_lock(workspace_dir)
        if workspace_lock_file is None:
            print(f"このワークスペースは既に他のプロセスで実行中です: {workspace_dir}")
            return 1
        
        # デーモン化
        log_file = (workspace_dir / "analysis.log").resolve()
        log_file_abs_str = str(log_file)
        child_pid = daemonize(log_file_abs_str)
        
        # 親プロセスの場合（child_pid > 0）
        if child_pid > 0:
            time.sleep(0.5)
            print(f"バックグラウンド実行開始: PID {child_pid}")
            print(f"ワークスペース: {workspace_dir}")
            print(f"PIDファイル: {pid_file}")
            print(f"ログファイル: {log_file}")
            print(f"状態確認: python {sys.argv[0]} --status --workspace-dir {workspace_dir}")
            print(f"停止: python {sys.argv[0]} --stop --workspace-dir {workspace_dir}")
            sys.exit(0)
        
        # 子プロセス（デーモン）の処理
        workspace_dir.mkdir(parents=True, exist_ok=True)
        save_pid(pid_file)
        register_cleanup_handlers(pid_file, workspace_lock_file)
    else:
        # フォアグラウンド実行の場合もロックチェック
        workspace_lock_file = acquire_workspace_lock(workspace_dir)
        if workspace_lock_file is None:
            logger.error(f"このワークスペースは既に他のプロセスで実行中です: {workspace_dir}")
            return 1
        
        # PIDファイルを保存（停止コマンドで使用）
        save_pid(pid_file)
        register_cleanup_handlers(pid_file, workspace_lock_file)
    
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
    
    # メタデータを読み込み
    metadata_path = workspace_dir / "metadata.json"
    metadata = {}
    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    
    # 個別実験の考察
    individual_results = []
    if not args.skip_individual:
        logger.info("個別実験の考察を開始...")
        individual_results = analyze_individual_experiments(
            workspace_dir,
            research_context,
            llm_client,
            checkpoint_file,
            metadata
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
    
    # クリーンアップ
    cleanup_pid(pid_file)
    if 'workspace_lock_file' in locals():
        release_workspace_lock(workspace_lock_file)
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

