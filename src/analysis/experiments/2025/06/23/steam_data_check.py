import pandas as pd
from pathlib import Path

# データパス
base_dir = Path("data/external/steam-review-aspect-dataset/current")
train_path = base_dir / "train.csv"
test_path = base_dir / "test.csv"

print("=== train.csv サンプル ===")
df_train = pd.read_csv(train_path)
print(df_train.head())

print("\n=== test.csv サンプル ===")
df_test = pd.read_csv(test_path)
print(df_test.head())

# アスペクト列のユニーク値
if "labels" in df_train.columns:
    print("\ntrain.csv アスペクト（labels）ユニーク値:")
    print(pd.unique(df_train["labels"]))
if "labels" in df_test.columns:
    print("\ntest.csv アスペクト（labels）ユニーク値:")
    print(pd.unique(df_test["labels"])) 