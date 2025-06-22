#!/usr/bin/env python3
"""
LLM共通処理の使用例
"""

from dotenv import load_dotenv
from llm_factory import LLMFactory

# 環境変数読み込み
load_dotenv()


def main():
    """使用例"""
    
    # サポートモデル確認
    print("サポートモデル:", LLMFactory.get_supported_models())
    
    # 設定ファイルのデフォルトモデルを使用
    llm_client = LLMFactory.create_client()  # model=Noneで設定ファイルから取得
    
    print(f"使用モデル: {llm_client.get_model_name()}")
    print(f"デフォルト温度: {llm_client.default_temperature}")
    print(f"デフォルトmax_tokens: {llm_client.default_max_tokens}")
    print("\n=== テスト開始 ===")
    
    # メッセージ構築（シンプルな例）
    messages1 = [
        {"role": "user", "content": "次の文章を要約してください: 今日は良い天気です。"}
    ]
    
    # メッセージ構築（システムメッセージ付き）
    messages2 = [
        {"role": "system", "content": "あなたは優秀なレビューテキスト分析専門家です。"},
        {"role": "user", "content": "この商品レビューを分析してください: 良い商品です。"}
    ]
    
    # クエリ実行（messages版）
    response1 = llm_client.query(messages1, temperature=0.5, max_tokens=50)
    response2 = llm_client.query(messages2, temperature=0.3, max_tokens=100)
    
    # シンプルな質問（ask版）
    print("\n1. ask()メソッドテスト...")
    simple_response = llm_client.ask("『こんにちは』を英語で言うと？")
    print(f"シンプル質問: {simple_response}")
    
    print("\n2. ask()システムメッセージ付きテスト...")
    expert_response = llm_client.ask(
        "このレビューの感情を分析して: とても良い商品でした！",
        system_message="あなたは優秀なレビュー分析専門家です。"
    )
    print(f"エキスパート分析: {expert_response}")
    
    # パラメータオーバーライドテスト
    print("\n3. パラメータオーバーライドテスト...")
    override_response = llm_client.ask(
        "ランダムな数字を1つ言って",
        temperature=1.0,  # 設定ファイルの0.7をオーバーライド
        max_tokens=10     # 設定ファイルの100をオーバーライド
    )
    print(f"パラメータオーバーライド: {override_response}")
    
    print(f"\n=== 結果サマリー ===")
    print(f"モデル: {llm_client.get_model_name()}")
    print(f"messages版シンプル応答: {response1}")
    print(f"messages版レビュー分析: {response2}")
    print("\n=== テスト完了 ===")


if __name__ == "__main__":
    main()