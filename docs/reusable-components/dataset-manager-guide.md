# DatasetManager 使い方ガイド

## 概要

**用途**: 複数データセットの統一管理・二項分割・実験支援
**再利用性**: high
**適用場面**: データセット横断実験、対比因子抽出、Few-shot 学習

## 基本的な使い方

### 1. 初期化

```python
from analysis.experiments.utils.dataset_manager import DatasetManager

# 設定ファイル駆動（推奨）
manager = DatasetManager.from_config()

# 手動設定
from analysis.experiments.utils.config import DatasetConfig
config = DatasetConfig("custom_config.yaml")
manager = DatasetManager(config=config)

# 従来方式（後方互換）
manager = DatasetManager()
```

### 2. データセット情報確認

```python
# 利用可能データセット一覧
datasets = manager.list_available_datasets()
for dataset_id, info in datasets.items():
    print(f"{dataset_id}: {info['domain']} ({len(info['aspects'])} aspects)")
    if info.get('accessible'):
        print(f"  ✅ アクセス可能")
    else:
        print(f"  ❌ アクセス不可")

# データ統計情報
stats = manager.get_data_statistics("steam")
print(f"Steam統計: {stats['total_records']}件")
print(f"アスペクト分布: {stats['aspects']}")
```

### 3. 二項分割（メイン機能）

#### バイナリラベル分割（Steam 向け）

```python
# ポジティブ vs ネガティブ分割
splits = manager.get_binary_splits(
    dataset_id="steam",
    aspect="gameplay",
    group_size=300,
    split_type="binary_label"
)

print(f"グループA（ポジティブ）: {len(splits.group_a)}件")
print(f"グループB（ネガティブ）: {len(splits.group_b)}件")
print(f"正解: {splits.correct_answer}")
```

#### アスペクト vs その他分割

```python
# 特定アスペクト vs 他アスペクト分割
splits = manager.get_binary_splits(
    dataset_id="semeval",
    aspect="food",
    group_size=200,
    split_type="aspect_vs_others"
)

print(f"フード関連: {len(splits.group_a)}件")
print(f"その他: {len(splits.group_b)}件")
```

#### 高度なオプション

```python
# ラベルバランス調整付き分割
splits = manager.get_binary_splits(
    dataset_id="steam",
    aspect="visual",
    group_size=250,
    split_type="binary_label",
    balance_labels=True,           # ラベルバランス調整
    min_samples_per_label=50       # 最小サンプル数
)

# メタデータ確認
metadata = splits.metadata
print(f"元データサイズ: A={metadata['original_a_size']}, B={metadata['original_b_size']}")
print(f"タイムスタンプ: {metadata['timestamp']}")
```

## Few-shot 学習支援

### 例題生成

```python
# Few-shot用例題を自動生成
examples = manager.create_examples(
    dataset_id="steam",
    aspect="story",
    shot_count=3,
    language="en"
)

for i, example in enumerate(examples):
    print(f"例題{i+1}:")
    print(f"  グループA: {example['group_a']}")
    print(f"  グループB: {example['group_b']}")
    print(f"  正解: {example['answer']}")
```

### 実験設定生成

```python
# 実験パラメータ自動設定
exp_config = manager.get_experiment_config(
    dataset_id="steam",
    aspects=["gameplay", "story", "visual"],
    shot_settings=[0, 1, 3, 5]
)

print(f"推定実験数: {exp_config['estimated_experiments']}")
print(f"使用アスペクト: {exp_config['aspects']}")
print(f"Shot設定: {exp_config['shot_settings']}")
```

## 実験パターン

### パターン 1: 単一データセット対比実験

```python
def run_single_dataset_experiment(dataset_id, aspects):
    """単一データセットでの対比実験"""
    manager = DatasetManager.from_config()
    results = []

    for aspect in aspects:
        for shot_count in [0, 1, 3]:
            # 分割実行
            splits = manager.get_binary_splits(
                dataset_id, aspect, group_size=300
            )

            # Few-shot例題生成
            examples = manager.create_examples(
                dataset_id, aspect, shot_count
            )

            results.append({
                "aspect": aspect,
                "shot_count": shot_count,
                "data": splits,
                "examples": examples
            })

    return results

# 実行例
results = run_single_dataset_experiment("steam", ["gameplay", "story"])
```

### パターン 2: データセット横断比較実験

```python
def run_cross_dataset_experiment(datasets, aspect_mapping):
    """データセット横断比較実験"""
    manager = DatasetManager.from_config()
    results = {}

    for dataset_id in datasets:
        aspects = aspect_mapping.get(dataset_id, [])
        dataset_results = []

        for aspect in aspects:
            splits = manager.get_binary_splits(
                dataset_id, aspect, group_size=200
            )
            dataset_results.append({
                "aspect": aspect,
                "splits": splits,
                "stats": manager.get_data_statistics(dataset_id)
            })

        results[dataset_id] = dataset_results

    return results

# 実行例
aspect_mapping = {
    "steam": ["gameplay", "story"],
    "semeval": ["food", "service"],
    "amazon": ["product"]
}
results = run_cross_dataset_experiment(
    ["steam", "semeval", "amazon"],
    aspect_mapping
)
```

### パターン 3: 設定検証付き実験

```python
def run_validated_experiment(dataset_id, aspects):
    """設定検証付き安全な実験実行"""
    manager = DatasetManager.from_config()

    # 事前検証
    validation = manager.validate_configuration()
    if validation['status'] != 'valid':
        print("設定に問題があります:")
        for warning in validation['warnings']:
            print(f"  ⚠️ {warning}")

    # データセットアクセス確認
    datasets = manager.list_available_datasets()
    if not datasets[dataset_id].get('accessible', False):
        raise RuntimeError(f"データセット {dataset_id} にアクセスできません")

    # 実験実行
    results = []
    for aspect in aspects:
        splits = manager.get_binary_splits(dataset_id, aspect)
        results.append(splits)

    return results
```

## 新機能

### 設定検証

```python
# 設定ファイル検証
validation = manager.validate_configuration()
print(f"ステータス: {validation['status']}")

if validation['warnings']:
    print("警告:")
    for warning in validation['warnings']:
        print(f"  ⚠️ {warning}")
```

### キャッシュ管理

```python
# データキャッシュクリア（メモリ節約）
manager.clear_cache()

# ローダー個別取得（高度な使用）
loader = manager.get_loader("steam")
records = loader.load_with_cache()
stats = loader.get_data_stats()
```

### 分割戦略の詳細制御

```python
# 分割戦略を直接使用
from analysis.experiments.utils.splitters import BinarySplitter, SplitOptions

splitter = BinarySplitter()
options = SplitOptions(
    group_size=500,
    balance_labels=True,
    min_samples_per_label=100
)

records = manager.get_dataset_records("steam")
result = splitter.split(records, "gameplay", options)
```

## 設定ファイルカスタマイズ

### dataset_configs.yaml 拡張

```yaml
# 新しいデータセット追加
datasets:
  custom_dataset:
    path: "/path/to/custom/dataset"
    domain: "custom_domain"
    language: "ja"
    aspects: ["aspect1", "aspect2"]

# 新しいローダー登録
loaders:
  custom_dataset:
    class: "CustomDatasetLoader"
    module: "loaders.custom_loader"

# 例題テンプレート追加
example_templates:
  custom_dataset:
    aspect1:
      - group_a: ["例文A1", "例文A2"]
        group_b: ["例文B1", "例文B2"]
        answer: "期待される差異"
```

## トラブルシューティング

### よくあるエラー

1. **ImportError: attempted relative import**

   ```python
   # 解決方法: sys.pathにプロジェクトルートを追加
   import sys
   sys.path.insert(0, '/path/to/imrb_research/src')
   ```

2. **ValidationError: データパスが存在しません**

   ```python
   # 解決方法: データパス確認
   datasets = manager.list_available_datasets()
   print(datasets['steam']['warnings'])  # 警告確認
   ```

3. **ValueError: アスペクトのレコードが見つかりません**
   ```python
   # 解決方法: 利用可能アスペクト確認
   loader = manager.get_loader("steam")
   aspects = loader.get_available_aspects()
   print(f"利用可能アスペクト: {aspects}")
   ```

## パフォーマンス最適化

### メモリ使用量削減

```python
# 大量データ処理時のメモリ最適化
manager = DatasetManager.from_config()

# 必要なデータセットのみキャッシュ
records = manager.get_dataset_records("steam", use_cache=False)

# 処理後にキャッシュクリア
manager.clear_cache()
```

### バッチ処理最適化

```python
# 効率的なバッチ処理
def efficient_batch_processing(dataset_id, aspects, group_size=300):
    manager = DatasetManager.from_config()

    # 一度だけデータ読み込み
    records = manager.get_dataset_records(dataset_id)

    results = []
    for aspect in aspects:
        # キャッシュされたデータを使用
        splits = manager.get_binary_splits(
            dataset_id, aspect, group_size, use_cache=True
        )
        results.append(splits)

    return results
```

## 移行ガイド

### 既存コードから新 API への移行

```python
# 旧: 直接初期化
# manager = DatasetManager()

# 新: 設定ファイル駆動（推奨）
manager = DatasetManager.from_config()

# 旧: 基本的な分割のみ
# splits = manager.get_binary_splits("steam", "gameplay", 300)

# 新: オプション付き分割
splits = manager.get_binary_splits(
    "steam", "gameplay", 300,
    balance_labels=True,
    min_samples_per_label=50
)

# 新機能の活用
validation = manager.validate_configuration()
stats = manager.get_data_statistics("steam")
```

**注意点**:

- 既存 API は完全に後方互換性を保持
- 段階的移行が可能
- 新機能は従来 API と併用可能
