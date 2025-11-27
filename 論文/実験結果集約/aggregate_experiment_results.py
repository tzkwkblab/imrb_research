#!/usr/bin/env python3
"""
実験結果とパラメータを集約するスクリプト

全ての実験の数値結果、パラメータ設定、評価方法を一つのmdファイルに集約
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent.parent
EXPERIMENT_BASE = PROJECT_ROOT / "論文" / "結果" / "追加実験" / "論文執筆用"

# 実験ディレクトリのマッピング
EXPERIMENT_DIRS = {
    "メイン実験": PROJECT_ROOT / "論文" / "結果" / "追加実験" / "main_experiment_rerun_temperature0",
    "グループサイズ比較": EXPERIMENT_BASE / "group_size_comparison" / "steam",
    "Few-shot実験": EXPERIMENT_BASE / "fewshot_llm_eval" / "steam",
    "GPT5.1比較": EXPERIMENT_BASE / "model_comparison_temperature0",
    "アスペクト説明文比較": EXPERIMENT_BASE / "aspect_description_comparison" / "steam",
    "COCO Retrieved Concepts": EXPERIMENT_BASE / "coco_retrieved_concepts",
}

# COCO実験の結果ファイルパス（resultsディレクトリに直接存在する場合）
COCO_RESULTS_FILE = PROJECT_ROOT / "results" / "20251127_140836" / "batch_results.json"


def load_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """JSONファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"警告: {file_path} の読み込みに失敗: {e}")
        return None


def load_markdown(file_path: Path) -> Optional[str]:
    """Markdownファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"警告: {file_path} の読み込みに失敗: {e}")
        return None


def extract_experiment_params(experiment_dir: Path) -> Dict[str, Any]:
    """実験パラメータを抽出"""
    params = {}
    
    # 実験パラメータ.mdを探す
    param_files = [
        experiment_dir / "実験設定" / "実験パラメータ.md",
        experiment_dir / "実験パラメータ.md",
    ]
    
    for param_file in param_files:
        if param_file.exists():
            content = load_markdown(param_file)
            if content:
                params["パラメータファイル"] = str(param_file.relative_to(PROJECT_ROOT))
                params["パラメータ内容"] = content
                break
    
    # マトリックスJSONを探す
    matrix_files = list(experiment_dir.glob("**/*matrix*.json"))
    if matrix_files:
        matrix_data = load_json(matrix_files[0])
        if matrix_data and "experiment_plan" in matrix_data:
            plan = matrix_data["experiment_plan"]
            if "settings" in plan:
                params["実験設定"] = plan["settings"]
    
    return params


def extract_experiment_results(experiment_dir: Path, results_file: Optional[Path] = None) -> Dict[str, Any]:
    """実験結果を抽出"""
    results = {}
    
    # batch_results.jsonを探す
    batch_result_files = [
        experiment_dir / "実験結果" / "batch_results.json",
        experiment_dir / "results" / "batch_results.json",
        experiment_dir / "batch_results.json",
    ]
    
    # 外部結果ファイルが指定されている場合は優先
    if results_file and results_file.exists():
        batch_result_files.insert(0, results_file)
    
    batch_data = None
    for result_file in batch_result_files:
        if result_file.exists():
            batch_data = load_json(result_file)
            if batch_data:
                break
    
    if batch_data:
        results["batch_results"] = batch_data
        
        # 実験計画情報
        if "experiment_plan" in batch_data:
            plan = batch_data["experiment_plan"]
            results["実験計画"] = {
                "総実験数": plan.get("total_experiments", 0),
                "説明": plan.get("description", ""),
                "設定": plan.get("settings", {}),
            }
        
        # 実行情報
        if "execution_info" in batch_data:
            exec_info = batch_data["execution_info"]
            results["実行情報"] = {
                "タイムスタンプ": exec_info.get("timestamp", ""),
                "成功数": exec_info.get("successful_experiments", 0),
                "失敗数": exec_info.get("failed_experiments", 0),
            }
        
        # 結果の統計を計算
        if "results" in batch_data:
            results_list = batch_data["results"]
            if results_list:
                stats = calculate_statistics(results_list)
                results["統計情報"] = stats
    
    # 統計JSONファイルを探す
    stat_files = [
        experiment_dir / "実験設定" / "*statistics.json",
        experiment_dir / "*statistics.json",
    ]
    
    for pattern in stat_files:
        for stat_file in experiment_dir.glob(str(pattern.relative_to(experiment_dir))):
            if stat_file.exists():
                stat_data = load_json(stat_file)
                if stat_data:
                    results["統計JSON"] = stat_data
                    break
    
    return results


def calculate_statistics(results_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """結果リストから統計を計算"""
    stats = {
        "総実験数": len(results_list),
        "BERTスコア": [],
        "BLEUスコア": [],
        "LLMスコア": [],
    }
    
    for result in results_list:
        # evaluationキーからスコアを取得
        eval_data = result.get("evaluation", {})
        
        # BERTスコア
        bert_score = None
        if "bert_score" in eval_data and eval_data["bert_score"] is not None:
            if isinstance(eval_data["bert_score"], dict):
                bert_score = eval_data["bert_score"].get("f1", 0)
            else:
                bert_score = float(eval_data["bert_score"])
            stats["BERTスコア"].append(bert_score)
        
        # BLEUスコア
        bleu_score = None
        if "bleu_score" in eval_data and eval_data["bleu_score"] is not None:
            bleu_score = float(eval_data["bleu_score"])
            stats["BLEUスコア"].append(bleu_score)
        
        # LLMスコア
        llm_score = None
        if "llm_score" in eval_data and eval_data["llm_score"] is not None:
            if isinstance(eval_data["llm_score"], dict):
                llm_score = eval_data["llm_score"].get("normalized_score", eval_data["llm_score"].get("score", 0))
            else:
                llm_score = float(eval_data["llm_score"])
            stats["LLMスコア"].append(llm_score)
    
    # 平均値を計算
    if stats["BERTスコア"]:
        stats["BERTスコア平均"] = sum(stats["BERTスコア"]) / len(stats["BERTスコア"])
        stats["BERTスコア最小"] = min(stats["BERTスコア"])
        stats["BERTスコア最大"] = max(stats["BERTスコア"])
    
    if stats["BLEUスコア"]:
        stats["BLEUスコア平均"] = sum(stats["BLEUスコア"]) / len(stats["BLEUスコア"])
        stats["BLEUスコア最小"] = min(stats["BLEUスコア"])
        stats["BLEUスコア最大"] = max(stats["BLEUスコア"])
    
    if stats["LLMスコア"]:
        stats["LLMスコア平均"] = sum(stats["LLMスコア"]) / len(stats["LLMスコア"])
        stats["LLMスコア最小"] = min(stats["LLMスコア"])
        stats["LLMスコア最大"] = max(stats["LLMスコア"])
    
    return stats


def format_parameter_table(params: Dict[str, Any]) -> str:
    """パラメータを表形式でフォーマット"""
    lines = []
    
    if "実験設定" in params:
        settings = params["実験設定"]
        lines.append("| パラメータ | 値 |")
        lines.append("|-----------|-----|")
        
        for key, value in settings.items():
            if isinstance(value, list):
                value_str = ", ".join(map(str, value))
            elif isinstance(value, bool):
                value_str = "有効" if value else "無効"
            else:
                value_str = str(value)
            lines.append(f"| {key} | {value_str} |")
    
    return "\n".join(lines)


def format_statistics_table(stats: Dict[str, Any]) -> str:
    """統計情報を表形式でフォーマット"""
    lines = []
    lines.append("| 指標 | 平均 | 最小 | 最大 |")
    lines.append("|------|------|------|------|")
    
    if "BERTスコア平均" in stats:
        lines.append(f"| BERTスコア | {stats['BERTスコア平均']:.4f} | {stats['BERTスコア最小']:.4f} | {stats['BERTスコア最大']:.4f} |")
    
    if "BLEUスコア平均" in stats:
        lines.append(f"| BLEUスコア | {stats['BLEUスコア平均']:.4f} | {stats['BLEUスコア最小']:.4f} | {stats['BLEUスコア最大']:.4f} |")
    
    if "LLMスコア平均" in stats:
        lines.append(f"| LLMスコア | {stats['LLMスコア平均']:.4f} | {stats['LLMスコア最小']:.4f} | {stats['LLMスコア最大']:.4f} |")
    
    return "\n".join(lines)


def generate_markdown_report() -> str:
    """Markdownレポートを生成"""
    lines = []
    lines.append("# 実験結果とパラメータ集約レポート")
    lines.append("")
    lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("このドキュメントは、論文執筆用に全ての実験の数値結果、パラメータ設定、評価方法を集約したものです。")
    lines.append("")
    
    # 評価方法の説明
    lines.append("## 評価方法")
    lines.append("")
    lines.append("### BERTスコア")
    lines.append("- **目的**: 意味類似度に基づく深層ベクトル比較")
    lines.append("- **計算方法**: SentenceTransformer('all-MiniLM-L6-v2')を使用してテキストをエンコードし、コサイン類似度を計算")
    lines.append("- **正規化**: コサイン類似度を[-1, 1]から[0, 1]に正規化")
    lines.append("- **範囲**: 0.0 - 1.0（1.0に近いほど類似）")
    lines.append("")
    
    lines.append("### BLEUスコア")
    lines.append("- **目的**: n-gramベースの表層一致率")
    lines.append("- **計算方法**: NLTKのsentence_bleuを使用（SmoothingFunction.method1を適用）")
    lines.append("- **範囲**: 0.0 - 1.0（1.0に近いほど一致）")
    lines.append("")
    
    lines.append("### LLM評価スコア")
    lines.append("- **目的**: LLMによる意味的類似度評価")
    lines.append("- **評価モデル**: 実験により異なる（gpt-4o-mini, gpt-4o等）")
    lines.append("- **評価方法**: 5段階評価（1-5）を0.0-1.0に正規化")
    lines.append("- **プロンプト**:")
    lines.append("```")
    lines.append("参照テキストと候補テキストの意味的類似度を5段階（1-5）で評価してください。")
    lines.append("")
    lines.append("参照テキスト: {reference_text}")
    lines.append("候補テキスト: {candidate_text}")
    lines.append("")
    lines.append("評価基準:")
    lines.append("- 5: 完全に同じ意味")
    lines.append("- 4: ほぼ同じ意味（細かい違いのみ）")
    lines.append("- 3: 類似しているが一部異なる")
    lines.append("- 2: 部分的に類似している")
    lines.append("- 1: ほとんど異なる")
    lines.append("")
    lines.append("出力形式（JSON形式）:")
    lines.append("{")
    lines.append("    \"score\": 4,")
    lines.append("    \"normalized_score\": 0.8,")
    lines.append("    \"reasoning\": \"評価理由を簡潔に説明\"")
    lines.append("}")
    lines.append("```")
    lines.append("")
    
    # 各実験の情報を追加
    for exp_name, exp_dir in EXPERIMENT_DIRS.items():
        # COCO実験の場合は特別な処理
        if exp_name == "COCO Retrieved Concepts":
            # COCO実験の結果ファイルを指定
            results_file = COCO_RESULTS_FILE if COCO_RESULTS_FILE.exists() else None
            if not exp_dir.exists() and not results_file:
                print(f"警告: {exp_dir} が存在しません")
                continue
        else:
            if not exp_dir.exists():
                print(f"警告: {exp_dir} が存在しません")
                continue
            results_file = None
        
        lines.append(f"## {exp_name}")
        lines.append("")
        
        # パラメータ抽出
        params = extract_experiment_params(exp_dir)
        if params:
            lines.append("### 実験パラメータ")
            lines.append("")
            
            if "実験設定" in params:
                lines.append(format_parameter_table(params))
                lines.append("")
            
            if "パラメータファイル" in params:
                lines.append(f"詳細: `{params['パラメータファイル']}`")
                lines.append("")
        
        # 結果抽出（COCO実験の場合は特別な処理）
        if exp_name == "COCO Retrieved Concepts":
            results_file = COCO_RESULTS_FILE if COCO_RESULTS_FILE.exists() else None
            results = extract_experiment_results(exp_dir, results_file)
        else:
            results = extract_experiment_results(exp_dir)
        
        # COCO実験の場合はresearch_context.mdからパラメータ情報を取得
        if exp_name == "COCO Retrieved Concepts":
            # 実験パラメータを追加
            if results and "batch_results" in results:
                batch_data = results["batch_results"]
                if "experiment_plan" in batch_data:
                    plan = batch_data["experiment_plan"]
                    settings = plan.get("settings", {})
                    main_settings = plan.get("main_experiment_settings", {})
                    
                    # 実際の結果からもパラメータを取得
                    if "results" in batch_data and len(batch_data["results"]) > 0:
                        first_result = batch_data["results"][0]
                        exp_info = first_result.get("experiment_info", {})
                        model_config = first_result.get("model_config", {})
                        
                        # パラメータの優先順位: exp_info > model_config > main_settings > settings
                        use_llm_eval = exp_info.get("use_llm_evaluation", False)
                        if use_llm_eval is None:
                            use_llm_eval = main_settings.get("use_llm_evaluation", False)
                        
                        lines.append("### 実験パラメータ")
                        lines.append("")
                        lines.append("| パラメータ | 値 |")
                        lines.append("|-----------|-----|")
                        lines.append(f"| temperature | {model_config.get('temperature', settings.get('temperature', 'N/A'))} |")
                        lines.append(f"| max_tokens | {model_config.get('max_tokens', settings.get('max_tokens', 'N/A'))} |")
                        lines.append(f"| few_shot | {exp_info.get('few_shot', main_settings.get('few_shot', 'N/A'))} |")
                        lines.append(f"| group_size | {exp_info.get('group_size', main_settings.get('group_size', 'N/A'))} |")
                        # GPTモデルはexp_infoから取得、なければmodel_configから、それでもなければmain_settingsから
                        gpt_model = exp_info.get('gpt_model') or model_config.get('model') or main_settings.get('gpt_model') or 'N/A'
                        lines.append(f"| GPTモデル | {gpt_model} |")
                        lines.append(f"| LLM評価 | {'有効' if use_llm_eval else '無効'} |")
                        if use_llm_eval:
                            llm_eval_model = exp_info.get('llm_evaluation_model') or plan.get('llm_evaluation_model') or 'N/A'
                            if llm_eval_model != 'N/A':
                                lines.append(f"| LLM評価モデル | {llm_eval_model} |")
                        lines.append(f"| アスペクト記述 | {'有効' if exp_info.get('use_aspect_descriptions', main_settings.get('use_aspect_descriptions', False)) else '無効'} |")
                        split_type = exp_info.get('split_type') or 'aspect_vs_bottom100'
                        lines.append(f"| 分割タイプ | {split_type} |")
                        lines.append("")
            
            research_context_file = exp_dir / "research_context.md"
            if research_context_file.exists():
                context_content = load_markdown(research_context_file)
                if context_content:
                    lines.append("### 実験の特徴")
                    lines.append("")
                    lines.append("- **正解ラベルなし**: 評価スコア（BERT/BLEU）は参考値として扱う")
                    lines.append("- **画像との整合性確認**: 生成された対比因子と画像を見比べて考察")
                    lines.append("- **データソース**: MS-COCO 2017 train split")
                    lines.append("- **類似度計算**: CLIP (ViT-B/32) コサイン類似度")
                    lines.append("- **コンセプト数**: 300個の潜在コンセプト")
                    lines.append("- **取得数**: 各コンセプトあたりTop-100とBottom-100の2セット")
                    lines.append("")
        
        if results:
            lines.append("### 実験結果")
            lines.append("")
            
            if "実験計画" in results:
                plan = results["実験計画"]
                lines.append(f"- **総実験数**: {plan.get('総実験数', 'N/A')}")
                lines.append(f"- **説明**: {plan.get('説明', 'N/A')}")
                lines.append("")
            
            if "実行情報" in results:
                exec_info = results["実行情報"]
                lines.append("**実行情報**:")
                lines.append(f"- タイムスタンプ: {exec_info.get('タイムスタンプ', 'N/A')}")
                lines.append(f"- 成功数: {exec_info.get('成功数', 'N/A')}")
                lines.append(f"- 失敗数: {exec_info.get('失敗数', 'N/A')}")
                lines.append("")
            
            if "統計情報" in results:
                stats = results["統計情報"]
                lines.append("**統計情報**:")
                lines.append("")
                lines.append(format_statistics_table(stats))
                lines.append("")
            
            if "統計JSON" in results:
                stat_json = results["統計JSON"]
                if "statistics" in stat_json:
                    stat_data = stat_json["statistics"]
                    lines.append("**詳細統計**:")
                    lines.append("")
                    lines.append("```json")
                    lines.append(json.dumps(stat_data, indent=2, ensure_ascii=False))
                    lines.append("```")
                    lines.append("")
        
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


def main():
    """メイン処理"""
    output_file = Path(__file__).parent / "実験結果集約レポート.md"
    
    print("実験結果とパラメータを集約中...")
    report = generate_markdown_report()
    
    print(f"レポートを生成: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("完了")


if __name__ == "__main__":
    main()

