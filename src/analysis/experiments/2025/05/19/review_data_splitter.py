import pandas as pd
import random
import os

DEFAULT_RANDOM_SEED = 42
FEATURE_COUNT = 20


def split_reviews_by_feature(
    feature_index, 
    fix_seed=True, 
    test_size=0.2, 
    csv_file_path='src/analysis/experiments/2025/05/15/processed_reviews.csv'
):
    """
    指定された特徴番号に基づいてレビューデータを分割し、トレーニングセットとテストセットに分ける。

    Args:
        feature_index (int): 分割の基準とする特徴の番号 (1から20)。
        fix_seed (bool): ランダムシードを固定するかどうか (デフォルト: True)。
        test_size (float): テストセットの割合 (0から1, デフォルト: 0.2)。
        csv_file_path (str): 読み込むCSVファイルのパス。

    Returns:
        dict: 分割されたデータを含む辞書。
              Keys: 'has_feature_train', 'has_feature_test', 'no_feature_train', 'no_feature_test'
              Value: それぞれのDataFrame
            エラーが発生した場合はNoneを返す。
    """
    if not 1 <= feature_index <= FEATURE_COUNT:
        print(f"エラー: feature_index は 1 から {FEATURE_COUNT} の間で指定してください。指定値: {feature_index}")
        return None

    if not 0 <= test_size <= 1:
        print(f"エラー: test_size は 0 から 1 の間で指定してください。指定値: {test_size}")
        return None

    feature_col = f'final_feature_{feature_index}'

    # CSVファイルを読み込む
    try:
        df = pd.read_csv(csv_file_path)
        print(f"{csv_file_path} を読み込みました。データ件数: {len(df)}") 
    except FileNotFoundError:
        print(f"エラー: {csv_file_path} が見つかりません。") 
        return None
    except Exception as e:
        print(f"エラー: ファイル読み込み中にエラーが発生しました - {e}") 
        return None

    # 特徴カラムが存在するか確認
    if feature_col not in df.columns:
        print(f"エラー: 指定された特徴カラム '{feature_col}' がCSVファイルに見つかりません。") 
        available_features = [col for col in df.columns if col.startswith('final_feature_')] 
        print(f"利用可能な特徴カラム: {available_features}") 
        return None

    # 特徴を持つ/持たないレビュー群に分割
    df_has_feature = df[df[feature_col] == 1].copy()
    df_no_feature = df[df[feature_col] == 0].copy()

    results = {}

    # ランダムシードの設定
    random_state = DEFAULT_RANDOM_SEED if fix_seed else None

    # 'has_feature' グループの分割
    if len(df_has_feature) > 0:
        if test_size == 0:
            results['has_feature_train'] = df_has_feature
            results['has_feature_test'] = pd.DataFrame(columns=df_has_feature.columns)
        elif test_size == 1:
            results['has_feature_train'] = pd.DataFrame(columns=df_has_feature.columns)
            results['has_feature_test'] = df_has_feature
        else:
            df_has_feature_test = df_has_feature.sample(frac=test_size, random_state=random_state, replace=False)
            df_has_feature_train = df_has_feature.drop(df_has_feature_test.index)
            results['has_feature_train'] = df_has_feature_train
            results['has_feature_test'] = df_has_feature_test
    else:
        results['has_feature_train'] = pd.DataFrame(columns=df.columns)
        results['has_feature_test'] = pd.DataFrame(columns=df.columns)

    # 'no_feature' グループの分割
    if len(df_no_feature) > 0:
        if test_size == 0:
            results['no_feature_train'] = df_no_feature
            results['no_feature_test'] = pd.DataFrame(columns=df_no_feature.columns)
        elif test_size == 1:
            results['no_feature_train'] = pd.DataFrame(columns=df_no_feature.columns)
            results['no_feature_test'] = df_no_feature
        else:
            df_no_feature_test = df_no_feature.sample(frac=test_size, random_state=random_state, replace=False)
            df_no_feature_train = df_no_feature.drop(df_no_feature_test.index)
            results['no_feature_train'] = df_no_feature_train
            results['no_feature_test'] = df_no_feature_test
        # print(f"'含まない' グループ: トレーニングセット {len(results['no_feature_train'])} 件, テストセット {len(results['no_feature_test'])} 件") # デバッグログ
    else:
        results['no_feature_train'] = pd.DataFrame(columns=df.columns)
        results['no_feature_test'] = pd.DataFrame(columns=df.columns)

    return results

def split_reviews_by_feature_index(
    test_size=0.2,
    csv_file_path='src/analysis/experiments/2025/05/15/processed_reviews.csv',
    feature_name_col='feature_name'
):
    """
    特徴インデックスに基づいてレビューデータを分割する新しい方法。
    特徴1〜特徴(20-test_sizeの割合)までをトレーニングデータ、残りをテストデータとする。

    Args:
        test_size (float): テストセットの割合 (0から1, デフォルト: 0.2)。
        csv_file_path (str): 読み込むCSVファイルのパス。
        feature_name_col (str): 特徴名が格納されているカラム名。

    Returns:
        dict: 'train'と'test'キーを持つ辞書。
             各値は、特徴ごとの[含むレビュー, 含まないレビュー, 特徴名]のリスト。
             エラーが発生した場合はNoneを返す。
    """
    if not 0 <= test_size <= 1:
        print(f"エラー: test_size は 0 から 1 の間で指定してください。指定値: {test_size}")
        return None

    # CSVファイルを読み込む
    try:
        df = pd.read_csv(csv_file_path)
        print(f"{csv_file_path} を読み込みました。データ件数: {len(df)}") 
    except FileNotFoundError:
        print(f"エラー: {csv_file_path} が見つかりません。") 
        return None
    except Exception as e:
        print(f"エラー: ファイル読み込み中にエラーが発生しました - {e}") 
        return None

    # 特徴カラムの確認
    feature_cols = [col for col in df.columns if col.startswith('final_feature_')]
    if not feature_cols:
        print("エラー: 'final_feature_' で始まるカラムがCSVファイルに見つかりません。")
        return None

    # トレーニングとテストの分割点を計算
    total_features = FEATURE_COUNT  # 特徴の総数
    split_index = int(total_features * (1 - test_size))
    
    # 結果を格納する辞書
    results = {
        'train': [],
        'test': []
    }

    # 特徴ごとに処理
    for feature_index in range(1, total_features + 1):
        feature_col = f'final_feature_{feature_index}'
        
        # 特徴カラムが存在するか確認
        if feature_col not in df.columns:
            print(f"警告: 特徴カラム '{feature_col}' がCSVファイルに見つかりません。スキップします。")
            continue
        
        # 特徴名を取得（存在する場合）
        feature_name = None
        if feature_name_col in df.columns:
            # 特徴に関連する名前を取得する処理（データ構造に依存）
            # この例では、最初に特徴を持つレコードから特徴名を取得
            feature_records = df[df[feature_col] == 1]
            if len(feature_records) > 0 and feature_name_col in feature_records.columns:
                feature_name = feature_records[feature_name_col].iloc[0]
        
        # 特徴を持つ/持たないレビュー群に分割
        df_has_feature = df[df[feature_col] == 1].copy()
        df_no_feature = df[df[feature_col] == 0].copy()
        
        # 特徴名がない場合はデフォルト名を設定
        if feature_name is None:
            feature_name = f"Feature {feature_index}"
        
        # 分割点に基づいてトレーニングまたはテストに追加
        feature_data = [df_has_feature, df_no_feature, feature_name]
        
        if feature_index <= split_index:
            results['train'].append(feature_data)
        else:
            results['test'].append(feature_data)
    
    print(f"トレーニングセット: 特徴1〜{split_index}の{len(results['train'])}個の特徴")
    print(f"テストセット: 特徴{split_index+1}〜{total_features}の{len(results['test'])}個の特徴")
    
    return results

if __name__ == '__main__':
    test_csv_path = 'src/analysis/experiments/2025/05/15/processed_reviews.csv'
    
    # 新しい分割方法を使用
    print("--- 新しい分割方法でレビューデータを分割します ---")
    split_data = split_reviews_by_feature_index(
        test_size=0.2,
        csv_file_path=test_csv_path
    )
    
    if split_data:
        print("\n--- 分割結果サマリー ---")
        print(f"トレーニングセット: {len(split_data['train'])}個の特徴")
        for i, (has_feature, no_feature, feature_name) in enumerate(split_data['train']):
            print(f"  特徴{i+1}: '{feature_name}' - 含む:{len(has_feature)}件, 含まない:{len(no_feature)}件")
        
        print(f"\nテストセット: {len(split_data['test'])}個の特徴")
        for i, (has_feature, no_feature, feature_name) in enumerate(split_data['test']):
            print(f"  特徴{i+1+len(split_data['train'])}: '{feature_name}' - 含む:{len(has_feature)}件, 含まない:{len(no_feature)}件")
    else:
        print("データ分割に失敗しました。")

    print(split_data['train'][0][0].iloc[0]['review_text'])

    # 旧分割方法の例（コメントアウト）
    """
    all_results = []
    # Loop over feature indices 1 to 5
    for feature_index in range(1, 6):
        print(f"--- Splitting review data: feature_index={feature_index}, test_size=0.2, fix_seed=True ---")
        split_data = split_reviews_by_feature(
            feature_index=feature_index,
            test_size=0.2,
            fix_seed=True,
            csv_file_path=test_csv_path
        )

        if split_data:
            # Store results in the list
            all_results.append({
                'feature_index': feature_index,
                'has_feature_train': len(split_data['has_feature_train']),
                'has_feature_test': len(split_data['has_feature_test']),
                'no_feature_train': len(split_data['no_feature_train']),
                'no_feature_test': len(split_data['no_feature_test'])
            })
            print(f"Feature {feature_index} split completed.")
        else:
            print(f"Data split failed for feature {feature_index}.")

    print("\n--- All review data splits completed ---")

    # Display results as a table
    if all_results:
        results_df = pd.DataFrame(all_results)
        print("\n--- Split Results Summary ---")
        print(results_df)
    else:
        print("No results to display.")
    """

