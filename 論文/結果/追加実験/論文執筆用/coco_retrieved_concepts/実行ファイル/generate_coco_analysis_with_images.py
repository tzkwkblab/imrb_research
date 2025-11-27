#!/usr/bin/env python3
"""
COCO実験結果の画像付きLLM分析スクリプト（GPT-5.1用）

上位5枚とボトム5枚の画像をGPT-5.1に入力して考察を生成する。
"""

import json
import argparse
import sys
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# パス設定
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src" / "analysis" / "experiments" / "utils"))

from LLM.llm_factory import LLMFactory

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_research_context(context_path: Path) -> str:
    """研究コンテキストを読み込み"""
    if not context_path.exists():
        logger.warning(f"研究背景ファイルが見つかりません: {context_path}")
        return ""
    
    with open(context_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # .mdcファイルの場合はフロントマターを除去
        if content.startswith('---'):
            lines = content.split('\n')
            in_frontmatter = True
            result_lines = []
            for line in lines:
                if in_frontmatter and line.strip() == '---':
                    in_frontmatter = False
                    continue
                if not in_frontmatter:
                    result_lines.append(line)
            return '\n'.join(result_lines)
        return content


def load_batch_results(batch_results_path: Path) -> List[Dict[str, Any]]:
    """バッチ結果を読み込み"""
    if not batch_results_path.exists():
        raise FileNotFoundError(f"バッチ結果ファイルが見つかりません: {batch_results_path}")
    
    with open(batch_results_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('results', [])


def extract_image_urls(result: Dict[str, Any], top_n: int = 5) -> Dict[str, List[str]]:
    """実験結果から画像URLを抽出"""
    input_data = result.get('input', {})
    return {
        'group_a': input_data.get('group_a_top5_image_urls', [])[:top_n],
        'group_b': input_data.get('group_b_top5_image_urls', [])[:top_n]
    }


def generate_analysis_prompt_with_images(
    research_context: str,
    experiment_result: Dict[str, Any],
    image_urls: Dict[str, List[str]]
) -> str:
    """画像を含む分析プロンプトを生成"""
    exp_info = experiment_result.get('experiment_info', {})
    aspect = exp_info.get('aspect', 'N/A')
    llm_response = experiment_result.get('process', {}).get('llm_response', 'N/A')
    
    eval_data = experiment_result.get('evaluation', {})
    bert_score = 0
    if 'bert_score' in eval_data and eval_data['bert_score'] is not None:
        if isinstance(eval_data['bert_score'], dict):
            bert_score = eval_data['bert_score'].get('f1', 0)
        else:
            bert_score = float(eval_data['bert_score'])
    
    prompt = f"""あなたは説明可能AIの研究における実験結果の分析専門家です。

# 研究背景

{research_context}

# 実験結果

- コンセプト: {aspect}
- 生成された対比因子: {llm_response}
- BERTスコア: {bert_score:.4f}

# 画像情報

以下の画像は、このコンセプトに関連するCOCOデータセットの画像です。

**グループA（Top-100から抽出）**: コンセプトに最も類似した画像（{len(image_urls.get('group_a', []))}枚）
**グループB（Bottom-100から抽出）**: コンセプトに最も類似していない画像（{len(image_urls.get('group_b', []))}枚）

生成された対比因子「{llm_response}」が、これらの画像の特徴と整合しているかを確認し、以下の観点から1500文字程度で詳細に考察してください。

1. **生成された対比因子と画像の整合性**
   - グループAの画像に共通する視覚的特徴が対比因子に反映されているか
   - グループBの画像との違いが適切に表現されているか
   - 画像から読み取れる内容と対比因子の記述が一致しているか
   - 具体的な画像の内容を引用しながら説明してください

2. **画像から読み取れる特徴と対比因子の関係**
   - 画像から視覚的に確認できる特徴（色、形状、構図、被写体、背景など）が対比因子に含まれているか
   - 対比因子が画像の内容を適切に説明しているか
   - 画像のキャプション（テキスト）と画像の視覚的内容の関係
   - 各画像の具体的な特徴を言及してください

3. **対比因子の妥当性**
   - 生成された対比因子が画像を見た人間の直感と一致するか
   - 対比因子が意味的に意味のある違いを表現しているか
   - グループAとグループBの画像の違いが明確に表現されているか
   - 対比因子が画像の本質的な特徴を捉えているか

4. **本研究への示唆**
   - 画像との整合性確認が対比因子生成の評価にどのように寄与するか
   - 正解ラベルがないデータセットでの評価方法の有効性
   - 視覚的検証の重要性
   - 今後の研究への示唆

考察は日本語で、具体的かつ詳細に記述してください。画像の視覚的特徴を具体的に言及し、各画像の内容を詳細に分析してください。
"""
    return prompt


def analyze_with_images_gpt5(
    prompt: str,
    image_urls: Dict[str, List[str]],
    model_name: str = "gpt-5.1",
    max_retries: int = 3
) -> Optional[str]:
    """画像を含めてGPT-5.1に問い合わせ"""
    try:
        client = LLMFactory.create_client(model_name=model_name, debug=False)
        
        # すべての画像URLを結合（グループA + グループB）
        all_image_urls = image_urls.get('group_a', []) + image_urls.get('group_b', [])
        
        if not all_image_urls:
            logger.warning("画像URLが見つかりません。テキストのみで分析します。")
            messages = [{"role": "user", "content": prompt}]
            return client.query(messages)
        
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # 画像付きクエリを実行
        if hasattr(client, 'query_with_images'):
            logger.info(f"画像付きクエリを実行中... (画像数: {len(all_image_urls)})")
            
            for attempt in range(max_retries):
                try:
                    # GPT-5.1の場合はmax_completion_tokensを100000に設定
                    max_tokens = 100000 if model_name.lower().startswith('gpt-5') else 8000
                    response = client.query_with_images(
                        messages=messages,
                        image_urls=all_image_urls,
                        max_completion_tokens=max_tokens
                    )
                    
                    if response and response.strip():
                        return response.strip()
                    else:
                        logger.warning(f"LLM応答が空です（試行 {attempt+1}/{max_retries}）")
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt
                            logger.info(f"{wait_time}秒待機してからリトライ...")
                            time.sleep(wait_time)
                
                except Exception as e:
                    logger.warning(f"LLM問い合わせエラー（試行 {attempt+1}/{max_retries}）: {e}")
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.info(f"{wait_time}秒待機してからリトライ...")
                        time.sleep(wait_time)
            
            logger.error("LLM問い合わせに失敗しました")
            return None
        else:
            logger.warning("画像入力機能が利用できません。通常のクエリを実行します。")
            return client.query(messages)
    
    except ValueError as e:
        if "画像入力に対応していません" in str(e):
            logger.error(f"エラー: {e}")
            logger.error("推奨: GPT-4oまたはGPT-4o-miniを使用してください。")
            return None
        raise
    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def main():
    parser = argparse.ArgumentParser(description="COCO実験結果の画像付きLLM分析（GPT-5.1用）")
    parser.add_argument('--batch-results', '-b', required=True, help='バッチ結果JSONファイル')
    parser.add_argument('--research-context', '-r', required=True, help='研究コンテキストMDファイル')
    parser.add_argument('--output', '-o', required=True, help='出力MDファイル')
    parser.add_argument('--model', '-m', default='gpt-5.1', help='使用するLLMモデル（デフォルト: gpt-5.1）')
    parser.add_argument('--aspect', '-a', help='特定のアスペクトのみ分析')
    parser.add_argument('--max-images', type=int, default=5, help='各グループから使用する最大画像数（デフォルト: 5）')
    parser.add_argument('--debug', action='store_true', help='デバッグモード')
    parser.add_argument('--preview-prompt', action='store_true', help='プロンプトを表示して終了（LLMに送信しない）')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # ファイル読み込み
        logger.info("データを読み込み中...")
        batch_results = load_batch_results(Path(args.batch_results))
        research_context = load_research_context(Path(args.research_context))
        
        if not research_context:
            logger.warning("研究コンテキストが空です。続行します...")
        
        logger.info(f"実験結果を読み込み: {len(batch_results)}件")
        
        # プロンプトプレビューモードの場合はここで終了
        if args.preview_prompt:
            logger.info("プロンプトプレビューモード: プロンプトを表示して終了します")
        
        # 各実験結果を分析
        analyses = []
        for result in batch_results:
            exp_info = result.get('experiment_info', {})
            aspect = exp_info.get('aspect', '')
            
            if args.aspect and aspect != args.aspect:
                continue
            
            # 画像URLを抽出
            image_urls = extract_image_urls(result, top_n=args.max_images)
            
            if not image_urls.get('group_a') and not image_urls.get('group_b'):
                logger.warning(f"警告: {aspect} の画像URLが見つかりません")
                continue
            
            # プロンプト生成
            prompt = generate_analysis_prompt_with_images(
                research_context,
                result,
                image_urls
            )
            
            # プロンプトプレビューモード
            if args.preview_prompt:
                print("=" * 80)
                print(f"コンセプト: {aspect}")
                print("=" * 80)
                print("\n【プロンプト】\n")
                print(prompt)
                print("\n" + "=" * 80)
                print(f"\n画像URL:")
                print(f"  グループA ({len(image_urls.get('group_a', []))}枚):")
                for i, url in enumerate(image_urls.get('group_a', []), 1):
                    print(f"    {i}. {url}")
                print(f"  グループB ({len(image_urls.get('group_b', []))}枚):")
                for i, url in enumerate(image_urls.get('group_b', []), 1):
                    print(f"    {i}. {url}")
                print("\n" + "=" * 80 + "\n")
                continue
            
            # LLM分析
            logger.info(f"\n分析中: {aspect}...")
            logger.info(f"  グループA画像数: {len(image_urls.get('group_a', []))}")
            logger.info(f"  グループB画像数: {len(image_urls.get('group_b', []))}")
            
            analysis = analyze_with_images_gpt5(prompt, image_urls, args.model)
            
            if analysis:
                analyses.append({
                    'aspect': aspect,
                    'analysis': analysis,
                    'image_urls': image_urls,
                    'llm_response': result.get('process', {}).get('llm_response', 'N/A'),
                    'bert_score': result.get('evaluation', {}).get('bert_score', 0)
                })
                logger.info(f"  ✓ 分析完了")
            else:
                logger.error(f"  ✗ 分析失敗")
        
        # レポート生成
        report = f"""# COCO実験結果 - 画像付きLLM考察（GPT-5.1）

生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
使用モデル: {args.model}
画像数: 各グループ{args.max_images}枚（合計{args.max_images * 2}枚）

"""
        
        for item in analyses:
            # BERTスコアの処理
            bert_score = item['bert_score']
            if isinstance(bert_score, dict):
                bert_score = bert_score.get('f1', 0)
            else:
                bert_score = float(bert_score) if bert_score is not None else 0
            
            report += f"""## {item['aspect']}

### 実験結果

- **生成された対比因子**: {item['llm_response']}
- **BERTスコア**: {bert_score:.4f}

### 画像との整合性考察

{item['analysis']}

### 参照画像

#### グループA（Top-100から抽出）

"""
            for i, url in enumerate(item['image_urls'].get('group_a', []), 1):
                report += f"{i}. ![画像A-{i}]({url})\n"
            
            report += "\n#### グループB（Bottom-100から抽出）\n"
            for i, url in enumerate(item['image_urls'].get('group_b', []), 1):
                report += f"{i}. ![画像B-{i}]({url})\n"
            
            report += "\n---\n\n"
        
        # プロンプトプレビューモードの場合はレポートを保存しない
        if args.preview_prompt:
            logger.info("プロンプトプレビューモード: プロンプト表示を完了しました")
            return 0
        
        # ファイルに保存
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding='utf-8')
        logger.info(f"\nレポートを保存しました: {output_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())

