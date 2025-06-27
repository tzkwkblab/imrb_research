# 対比因子分析統合パターン

## 統合分析ツール

**用途**: グループ A/B 比較による対比因子抽出の自動化
**再利用性**: high
**使用例数**: 1 回

### 基本パターン

```python
from contrast_factor_analyzer import ContrastFactorAnalyzer

analyzer = ContrastFactorAnalyzer()
result = analyzer.analyze(
    group_a=["text1", "text2"],
    group_b=["text3", "text4"],
    correct_answer="expected feature",
    output_dir="results/"
)

# 結果確認
bert_score = result['evaluation']['bert_score']
quality = result['summary']['quality_assessment']['overall_quality']
```

### Few-shot 学習パターン

```python
examples = [{
    "group_a": ["example_a1", "example_a2"],
    "group_b": ["example_b1", "example_b2"],
    "answer": "expected difference"
}]

result = analyzer.analyze(
    group_a=group_a,
    group_b=group_b,
    correct_answer=correct_answer,
    examples=examples,
    output_dir="results/"
)
```

### バッチ実験パターン

```python
experiments = [
    {
        "group_a": ["fast", "quick"],
        "group_b": ["slow", "delayed"],
        "correct_answer": "speed"
    },
    {
        "group_a": ["secure", "safe"],
        "group_b": ["complex", "difficult"],
        "correct_answer": "security"
    }
]

results = analyzer.analyze_batch(
    experiments=experiments,
    output_dir="results/batch/",
    base_experiment_name="multi_test"
)
```

### 出力形式

```json
{
  "evaluation": {
    "bert_score": 0.85,
    "bleu_score": 0.65
  },
  "summary": {
    "quality_assessment": {
      "overall_quality": "good"
    }
  }
}
```

**注意点**:

- OpenAI API キー必須
- BERT モデル初回読み込みで約 500MB 使用
- max_tokens 調整で応答長制御
