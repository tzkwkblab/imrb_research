# 実験結果解析ガイド

## ディレクトリ構造

```
analysis_workspace/
├── main_experiments/              # メイン実験（37件）
│   ├── by_dataset/               # データセット別に整理
│   │   ├── amazon/               # 5件
│   │   ├── goemotions/           # 28件
│   │   └── semeval/              # 4件
│   └── experiment_list.json      # 全メイン実験のリスト
├── sub_experiments/              # サブ実験（34件）
│   ├── steam_group_size/         # 20件（group_size変化実験）
│   ├── steam_gpt51/              # 4件（gpt-5.1検証）
│   ├── retrieved_concepts/       # 10件（COCO実験）
│   └── experiment_list.json     # 全サブ実験のリスト
└── metadata.json                  # メタデータ・サマリー
```

## クイックスタート

### 1. メタデータの確認

```python
import json
from pathlib import Path

base_dir = Path("results/20251119_153853/analysis_workspace")
metadata = json.load(open(base_dir / "metadata.json"))

print(f"メイン実験: {metadata['summary']['main_experiments']}件")
print(f"サブ実験: {metadata['summary']['sub_experiments']}件")
print(f"データセット別: {metadata['summary']['main_by_dataset']}")
```

### 2. メイン実験の一括読み込み

```python
import json
from pathlib import Path
from typing import List, Dict, Any

def load_main_experiments(base_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    """メイン実験をデータセット別に読み込み"""
    main_list = json.load(open(base_dir / "main_experiments/experiment_list.json"))
    results = {}
    
    for dataset, experiments in main_list['by_dataset'].items():
        results[dataset] = []
        for exp_info in experiments:
            file_path = base_dir.parent / exp_info['file_path']
            with open(file_path, 'r', encoding='utf-8') as f:
                exp_data = json.load(f)
                results[dataset].append({
                    'experiment_id': exp_info['experiment_id'],
                    'config': exp_info['config'],
                    'data': exp_data
                })
    
    return results

# 使用例
base_dir = Path("results/20251119_153853/analysis_workspace")
main_experiments = load_main_experiments(base_dir)

# データセット別にアクセス
amazon_exps = main_experiments['amazon']
goemotions_exps = main_experiments['goemotions']
semeval_exps = main_experiments['semeval']
```

### 3. サブ実験の一括読み込み

```python
def load_sub_experiments(base_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    """サブ実験をカテゴリ別に読み込み"""
    sub_list = json.load(open(base_dir / "sub_experiments/experiment_list.json"))
    results = {}
    
    for category, category_data in sub_list['categories'].items():
        results[category] = []
        for exp_info in category_data['experiments']:
            if exp_info['file_path']:
                file_path = base_dir.parent / exp_info['file_path']
                with open(file_path, 'r', encoding='utf-8') as f:
                    exp_data = json.load(f)
                    results[category].append({
                        'experiment_id': exp_info['experiment_id'],
                        'config': exp_info['config'],
                        'data': exp_data
                    })
    
    return results

# 使用例
sub_experiments = load_sub_experiments(base_dir)

# カテゴリ別にアクセス
steam_gs_exps = sub_experiments['steam_group_size']
steam_g51_exps = sub_experiments['steam_gpt51']
rc_exps = sub_experiments['retrieved_concepts']
```

### 4. 特定の実験を検索して読み込み

```python
def find_experiment(base_dir: Path, experiment_id: str) -> Dict[str, Any]:
    """実験IDから実験データを検索して読み込み"""
    # メイン実験から検索
    main_list = json.load(open(base_dir / "main_experiments/experiment_list.json"))
    for exp_info in main_list['experiments']:
        if exp_info['experiment_id'] == experiment_id:
            file_path = base_dir.parent / exp_info['file_path']
            with open(file_path, 'r', encoding='utf-8') as f:
                return {
                    'type': 'main',
                    'experiment_id': experiment_id,
                    'config': exp_info['config'],
                    'data': json.load(f)
                }
    
    # サブ実験から検索
    sub_list = json.load(open(base_dir / "sub_experiments/experiment_list.json"))
    for category_data in sub_list['categories'].values():
        for exp_info in category_data['experiments']:
            if exp_info['experiment_id'] == experiment_id:
                if exp_info['file_path']:
                    file_path = base_dir.parent / exp_info['file_path']
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return {
                            'type': 'sub',
                            'experiment_id': experiment_id,
                            'config': exp_info['config'],
                            'data': json.load(f)
                        }
    
    return None

# 使用例
exp = find_experiment(base_dir, "goemotions_admiration_1_4o-mini_word")
```

## データ構造

### 実験結果JSONの構造

各実験結果JSONファイルには以下の情報が含まれます：

```python
{
    "experiment_info": {
        "timestamp": "20251119_153925",
        "experiment_name": "...",
        "model_config": {...},
        "input_data": {...},
        "dataset": "...",
        "aspect": "...",
        "group_size": 100,
        ...
    },
    "input": {
        "group_a": [...],
        "group_b": [...],
        "examples": [...],
        "correct_answer": "..."
    },
    "output": {
        "llm_response": "...",
        "quality_evaluation": "...",
        ...
    },
    "scores": {
        "bert_score": 0.xxx,
        "bleu_score": 0.xxx,
        ...
    },
    "summary": {
        "success": true,
        ...
    }
}
```

### 主要なデータアクセス

```python
# 実験結果から主要データを抽出
def extract_key_metrics(exp_data: Dict[str, Any]) -> Dict[str, Any]:
    """実験結果から主要指標を抽出"""
    return {
        'experiment_id': exp_data['experiment_info'].get('experiment_id', ''),
        'dataset': exp_data['experiment_info'].get('dataset', ''),
        'aspect': exp_data['experiment_info'].get('aspect', ''),
        'group_size': exp_data['experiment_info'].get('group_size', 0),
        'llm_response': exp_data['output'].get('llm_response', ''),
        'bert_score': exp_data['scores'].get('bert_score', 0),
        'bleu_score': exp_data['scores'].get('bleu_score', 0),
        'quality': exp_data['output'].get('quality_evaluation', ''),
        'success': exp_data['summary'].get('success', False)
    }

# 使用例
for dataset, exps in main_experiments.items():
    for exp in exps:
        metrics = extract_key_metrics(exp['data'])
        print(f"{metrics['experiment_id']}: BERT={metrics['bert_score']:.3f}, BLEU={metrics['bleu_score']:.3f}")
```

## 解析パターン

### パターン1: データセット別性能比較

```python
# メイン実験のデータセット別平均スコアを計算
def calculate_dataset_averages(main_experiments: Dict[str, List[Dict]]) -> Dict[str, Dict[str, float]]:
    """データセット別の平均スコアを計算"""
    averages = {}
    
    for dataset, exps in main_experiments.items():
        bert_scores = []
        bleu_scores = []
        
        for exp in exps:
            scores = exp['data'].get('scores', {})
            if 'bert_score' in scores:
                bert_scores.append(scores['bert_score'])
            if 'bleu_score' in scores:
                bleu_scores.append(scores['bleu_score'])
        
        averages[dataset] = {
            'avg_bert': sum(bert_scores) / len(bert_scores) if bert_scores else 0,
            'avg_bleu': sum(bleu_scores) / len(bleu_scores) if bleu_scores else 0,
            'count': len(exps)
        }
    
    return averages
```

### パターン2: group_sizeによる影響分析

```python
# Steamサブ実験からgroup_sizeによる影響を分析
def analyze_group_size_impact(sub_experiments: Dict[str, List[Dict]]) -> Dict[str, Dict[int, float]]:
    """group_sizeによる影響を分析"""
    steam_gs_exps = sub_experiments['steam_group_size']
    
    # アスペクト別、group_size別にスコアを集計
    results = {}
    
    for exp in steam_gs_exps:
        aspect = exp['config']['aspect']
        group_size = exp['config']['group_size']
        bert_score = exp['data'].get('scores', {}).get('bert_score', 0)
        
        if aspect not in results:
            results[aspect] = {}
        results[aspect][group_size] = bert_score
    
    return results
```

### パターン3: モデル比較（gpt-4o-mini vs gpt-5.1）

```python
# Steamのgroup_size=300でgpt-4o-miniとgpt-5.1を比較
def compare_models(base_dir: Path) -> Dict[str, Dict[str, float]]:
    """モデル間の性能比較"""
    sub_list = json.load(open(base_dir / "sub_experiments/experiment_list.json"))
    
    # gpt-4o-miniのgroup_size=300実験を取得
    steam_gs_300 = [
        exp for exp in sub_list['categories']['steam_group_size']['experiments']
        if exp['config']['group_size'] == 300
    ]
    
    # gpt-5.1の実験を取得
    steam_g51 = sub_list['categories']['steam_gpt51']['experiments']
    
    comparison = {}
    
    for gs_exp in steam_gs_300:
        aspect = gs_exp['config']['aspect']
        if aspect not in comparison:
            comparison[aspect] = {}
        
        # gpt-4o-miniのスコア
        if gs_exp['file_path']:
            file_path = base_dir.parent / gs_exp['file_path']
            with open(file_path, 'r') as f:
                data = json.load(f)
                comparison[aspect]['gpt-4o-mini'] = data.get('scores', {}).get('bert_score', 0)
        
        # gpt-5.1のスコア
        g51_exp = next((e for e in steam_g51 if e['config']['aspect'] == aspect), None)
        if g51_exp and g51_exp['file_path']:
            file_path = base_dir.parent / g51_exp['file_path']
            with open(file_path, 'r') as f:
                data = json.load(f)
                comparison[aspect]['gpt-5.1'] = data.get('scores', {}).get('bert_score', 0)
    
    return comparison
```

## 便利関数まとめ

```python
from pathlib import Path
import json
from typing import Dict, List, Any

class ExperimentLoader:
    """実験結果読み込み用のヘルパークラス"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.metadata = json.load(open(base_dir / "metadata.json"))
        self.main_list = json.load(open(base_dir / "main_experiments/experiment_list.json"))
        self.sub_list = json.load(open(base_dir / "sub_experiments/experiment_list.json"))
    
    def load_main_by_dataset(self, dataset: str) -> List[Dict[str, Any]]:
        """指定データセットのメイン実験を読み込み"""
        if dataset not in self.main_list['by_dataset']:
            return []
        
        results = []
        for exp_info in self.main_list['by_dataset'][dataset]:
            file_path = self.base_dir.parent / exp_info['file_path']
            with open(file_path, 'r', encoding='utf-8') as f:
                results.append({
                    'experiment_id': exp_info['experiment_id'],
                    'config': exp_info['config'],
                    'data': json.load(f)
                })
        return results
    
    def load_sub_by_category(self, category: str) -> List[Dict[str, Any]]:
        """指定カテゴリのサブ実験を読み込み"""
        if category not in self.sub_list['categories']:
            return []
        
        results = []
        for exp_info in self.sub_list['categories'][category]['experiments']:
            if exp_info['file_path']:
                file_path = self.base_dir.parent / exp_info['file_path']
                with open(file_path, 'r', encoding='utf-8') as f:
                    results.append({
                        'experiment_id': exp_info['experiment_id'],
                        'config': exp_info['config'],
                        'data': json.load(f)
                    })
        return results
    
    def get_all_experiment_ids(self) -> List[str]:
        """全実験IDのリストを取得"""
        ids = [exp['experiment_id'] for exp in self.main_list['experiments']]
        for category_data in self.sub_list['categories'].values():
            ids.extend([exp['experiment_id'] for exp in category_data['experiments']])
        return ids

# 使用例
loader = ExperimentLoader(Path("results/20251119_153853/analysis_workspace"))
amazon_exps = loader.load_main_by_dataset("amazon")
steam_gs_exps = loader.load_sub_by_category("steam_group_size")
all_ids = loader.get_all_experiment_ids()
```

## 注意事項

1. **ファイルパス**: すべてのファイルパスは`results/20251119_153853`を基準とした相対パスです
2. **エンコーディング**: JSONファイルはUTF-8で保存されています
3. **欠損データ**: 一部の実験でスコアが欠損している可能性があります（エラーハンドリングを推奨）
4. **メモリ使用量**: 全実験を一度に読み込む場合はメモリ使用量に注意してください

## 関連ファイル

- 実験マトリックス: `実験マトリックス.json`
- 整理スクリプト: `src/analysis/experiments/2025/10/10/organize_experiment_results.py`
- 実行ログ: `results/20251119_153853/run.log`

