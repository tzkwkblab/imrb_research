#!/usr/bin/env python3
"""
LLM共通処理の使用例
"""

from dotenv import load_dotenv
from llm_factory import LLMFactory

# 環境変数読み込み
load_dotenv()


def test_model_configuration_debug():
    """設定ファイルのモデル名読み込みをデバッグモードでテスト"""
    print("=" * 60)
    print("設定ファイルからのモデル読み込みテスト（デバッグモード）")
    print("=" * 60)
    
    # デバッグモード有効でクライアント作成
    print("\n--- デバッグモード有効でのクライアント作成 ---")
    llm_client = LLMFactory.create_client(debug=True)
    
    print(f"\n[結果] 実際に使用されているモデル: {llm_client.get_model_name()}")
    print(f"[結果] デフォルト温度: {llm_client.default_temperature}")
    print(f"[結果] デフォルトmax_tokens: {llm_client.default_max_tokens}")
    
    return llm_client


def test_model_override_debug():
    """モデル名を明示的に指定した場合のテスト"""
    print("\n" + "=" * 60)
    print("モデル名明示指定テスト（デバッグモード）")
    print("=" * 60)
    
    test_model = "gpt-4o-mini"
    print(f"\n--- {test_model} を明示指定してクライアント作成 ---")
    
    try:
        llm_client = LLMFactory.create_client(model_name=test_model, debug=True)
        print(f"\n[結果] 成功: {llm_client.get_model_name()}")
        return llm_client
    except SystemExit as e:
        print(f"\n[結果] モデル検証エラーで終了: {e}")
        return None
    except Exception as e:
        print(f"\n[結果] その他エラー: {e}")
        return None


def test_invalid_model_debug():
    """存在しないモデル名でのエラーテスト"""
    print("\n" + "=" * 60)
    print("不正モデル名エラーテスト（デバッグモード）")
    print("=" * 60)
    
    invalid_model = "invalid-model-name-12345"
    print(f"\n--- {invalid_model} を指定してエラー確認 ---")
    
    try:
        llm_client = LLMFactory.create_client(model_name=invalid_model, debug=True)
        print(f"\n[結果] 予期せず成功: {llm_client.get_model_name()}")
        return llm_client
    except SystemExit as e:
        print(f"\n[結果] 期待通りモデル検証エラーで終了")
        return None
    except Exception as e:
        print(f"\n[結果] その他エラー: {e}")
        return None


def test_api_calls_debug(client):
    """API呼び出しをデバッグモードでテスト"""
    if client is None:
        print("\n[スキップ] クライアントが作成されていないため、API呼び出しテストをスキップ")
        return
    
    print("\n" + "=" * 60)
    print("API呼び出しテスト（デバッグモード）")
    print("=" * 60)
    
    # シンプルなテスト
    print("\n--- シンプルなAPI呼び出し ---")
    response = client.ask("Hello, how are you?")
    print(f"[結果] 応答: {response}")
    
    # パラメータ指定テスト
    print("\n--- パラメータ指定API呼び出し ---")
    response = client.ask(
        "Say just one word: 'Success'",
        temperature=0.1,
        max_tokens=5
    )
    print(f"[結果] 応答: {response}")


def main():
    """メイン関数 - 段階的にテスト実行"""
    
    print("LLM設定テスト開始")
    
    # 1. 設定ファイルからのモデル読み込みテスト
    client1 = test_model_configuration_debug()
    
    # 2. モデル名明示指定テスト
    client2 = test_model_override_debug()
    
    # 3. 有効なクライアントでAPI呼び出しテスト
    valid_client = client1 if client1 else client2
    test_api_calls_debug(valid_client)
    
    # 4. 利用可能モデル一覧表示（デバッグモード）
    print("\n" + "=" * 60)
    print("利用可能モデル一覧取得（デバッグモード）")
    print("=" * 60)
    
    try:
        print("\n--- デバッグモード有効でモデル一覧取得 ---")
        available_models = LLMFactory.get_supported_models(debug=True)
        print(f"\n[結果] 取得成功: {len(available_models)}個のモデル")
        print("最初の10個:")
        for i, model in enumerate(available_models[:10]):
            print(f"  {i+1:2d}. {model}")
            
    except Exception as e:
        print(f"[結果] モデル一覧取得エラー: {e}")
    
    print("\n" + "=" * 60)
    print("全テスト完了")
    print("=" * 60)
    
    # 最後に不正モデル名テスト（プログラム終了のため最後に実行）
    print("\n最後に不正モデル名テストを実行します（プログラムが終了する可能性があります）")
    input("Enterキーを押すと続行...")
    test_invalid_model_debug()


if __name__ == "__main__":
    main()