#!/usr/bin/env python3
"""
SemEval実験でのLLM共通処理使用例

既存のsemeval_absa_contrast_experiment.pyのGPT処理部分を
LLM共通処理に置き換える例
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# パス設定
current_dir = Path(__file__).parent
experiments_dir = current_dir.parent.parent.parent
utils_dir = experiments_dir / "utils"
sys.path.append(str(utils_dir))
sys.path.append(str(utils_dir / "LLM"))

# 環境変数読み込み
load_dotenv()

# モジュールインポート
from llm_factory import LLMFactory


class SemEvalLLMIntegration:
    """SemEval実験のLLM統合クラス"""
    
    def __init__(self, model_name: str = None):
        """
        初期化
        Args:
            model_name: モデル名（Noneで設定ファイルのデフォルト使用）
        """
        self.llm_client = LLMFactory.create_client(model_name)
        print(f"✅ LLMクライアント初期化完了: {self.llm_client.get_model_name()}")
    
    def create_contrast_prompt(self, group_a: List[Dict], group_b: List[Dict], 
                             domain: str, feature: str, shot_count: int = 0) -> str:
        """
        対比因子生成用プロンプトを作成（既存のロジックを流用）
        """
        # グループAのレビューテキスト（最大10件表示）
        group_a_texts = [sample['review_text'] for sample in group_a[:10]]
        group_b_texts = [sample['review_text'] for sample in group_b[:10]]
        
        group_a_display = "\n".join([f"- {text[:200]}..." if len(text) > 200 else f"- {text}" 
                                   for text in group_a_texts])
        group_b_display = "\n".join([f"- {text[:200]}..." if len(text) > 200 else f"- {text}" 
                                   for text in group_b_texts])
        
        # ドメイン情報
        domain_context = {
            'restaurant': 'レストラン・飲食店',
            'laptop': 'ノートパソコン・ラップトップ'
        }.get(domain, domain)
        
        # Few-shot例題部分（実装簡略化のため今回は0-shotのみ）
        few_shot_examples = ""
        if shot_count > 0:
            few_shot_examples = f"\n【参考例題】\n（{shot_count}個の例題がここに入ります）\n"
        
        prompt = f"""あなたは{domain_context}レビュー分析の専門家です。

【分析タスク】
以下の2つのレビューグループを比較して、グループAに特徴的でグループBには見られない表現パターンや内容の特徴を特定してください。

【データ情報】
- ドメイン: {domain_context}
- 対象特徴: {feature}
- グループAサイズ: {len(group_a)}レビュー
- グループBサイズ: {len(group_b)}レビュー

{few_shot_examples}

【グループA のレビュー】（{feature}特徴を含む）
{group_a_display}

【グループB のレビュー】（{feature}特徴を含まない）
{group_b_display}

【回答要求】
英語で5-10単語程度で、グループAに特徴的でグループBには見られない主要な違いを簡潔に回答してください。

回答："""

        return prompt
    
    def query_gpt_with_llm_client(self, prompt: str, **kwargs) -> Optional[str]:
        """
        LLM共通処理を使ってGPTにクエリ（既存のquery_gpt()の置き換え）
        """
        try:
            # システムメッセージ付きでクエリ
            response = self.llm_client.ask(
                question=prompt,
                system_message="あなたは優秀なレビューテキスト分析専門家です。",
                temperature=kwargs.get('temperature', 0.3),
                max_tokens=kwargs.get('max_tokens', 100)
            )
            return response
        except Exception as e:
            print(f"❌ LLM API エラー: {e}")
            return None
    
    def run_single_experiment(self, domain: str, feature: str, shot_count: int = 0) -> Dict:
        """
        単一実験の実行例
        """
        print(f"🔬 実験実行: {domain}-{feature}-{shot_count}shot")
        
        # ダミーデータ（実際にはDomainAwareFeatureSplitterから取得）
        if domain == "laptop" and feature == "battery":
            group_a = [
                {"review_text": "Great battery life lasting all day"},
                {"review_text": "Excellent power management features"},
                {"review_text": "Long-lasting battery performance"}
            ]
            group_b = [
                {"review_text": "Poor screen quality and resolution"},
                {"review_text": "Uncomfortable keyboard layout"},
                {"review_text": "Slow system performance issues"}
            ]
        else:
            # その他のダミーデータ
            group_a = [{"review_text": f"Good {feature} quality"}]
            group_b = [{"review_text": "Poor overall experience"}]
        
        # プロンプト生成
        prompt = self.create_contrast_prompt(group_a, group_b, domain, feature, shot_count)
        
        # GPT問い合わせ（LLM共通処理使用）
        gpt_response = self.query_gpt_with_llm_client(prompt)
        
        if gpt_response:
            print(f"✅ GPT応答: {gpt_response}")
            
            # 結果記録
            result = {
                "domain": domain,
                "feature": feature,
                "shot_count": shot_count,
                "group_a_size": len(group_a),
                "group_b_size": len(group_b),
                "gpt_response": gpt_response,
                "prompt_length": len(prompt),
                "model": self.llm_client.get_model_name()
            }
            
            return result
        else:
            print(f"❌ GPT応答の取得に失敗")
            return None


def demo_integration():
    """統合デモ"""
    print("🚀 SemEval実験 LLM統合デモ")
    print("=" * 50)
    
    # LLM統合クラス初期化
    semeval_llm = SemEvalLLMIntegration()
    
    # 実験実行例
    experiments = [
        ("laptop", "battery", 0),
        ("laptop", "screen", 0),
        ("restaurant", "food", 0),
    ]
    
    results = []
    for domain, feature, shot_count in experiments:
        result = semeval_llm.run_single_experiment(domain, feature, shot_count)
        if result:
            results.append(result)
        print()
    
    # 結果サマリー
    print("📊 実験結果サマリー")
    print("=" * 50)
    for i, result in enumerate(results, 1):
        print(f"実験{i}: {result['domain']}-{result['feature']}")
        print(f"  モデル: {result['model']}")
        print(f"  応答: {result['gpt_response']}")
        print(f"  プロンプト長: {result['prompt_length']}文字")
    
    print(f"\n🎉 {len(results)}件の実験が完了しました！")
    return results


def migration_guide():
    """既存コードの移行ガイド"""
    print("\n📋 既存コードの移行ガイド")
    print("=" * 50)
    
    print("【BEFORE】既存のsemeval_absa_contrast_experiment.py")
    print("""
# 既存のコード
def query_gpt(self, prompt: str) -> Optional[str]:
    for attempt in range(MAX_RETRIES):
        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "あなたは優秀なレビューテキスト分析専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"GPT API エラー: {e}")
            return None
""")
    
    print("\n【AFTER】LLM共通処理使用版")
    print("""
# 新しいコード
def __init__(self):
    self.llm_client = LLMFactory.create_client()  # 設定ファイルから自動取得

def query_gpt(self, prompt: str) -> Optional[str]:
    return self.llm_client.ask(
        question=prompt,
        system_message="あなたは優秀なレビューテキスト分析専門家です。",
        temperature=0.3,
        max_tokens=100
    )
""")
    
    print("\n✅ 移行のメリット:")
    print("  - OpenAI APIの直接呼び出し不要")
    print("  - 設定ファイルからの自動パラメータ取得")
    print("  - 統一されたエラーハンドリング")
    print("  - 将来的な他のLLM（Claude、Gemini等）への対応容易")
    print("  - リトライ処理の共通化")


def main():
    """メイン関数"""
    try:
        # 統合デモ実行
        results = demo_integration()
        
        # 移行ガイド表示
        migration_guide()
        
        return results
        
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()