# 実験結果集約ディレクトリ

このディレクトリは、論文執筆用に全ての実験の数値結果、パラメータ設定、評価方法を集約したものです。

## ファイル構成

- `aggregate_experiment_results.py`: 実験結果とパラメータを集約するPythonスクリプト
- `実験結果集約レポート.md`: 集約された実験結果とパラメータのレポート

## 使用方法

### レポートの再生成

```bash
# 仮想環境をアクティベート
source .venv/bin/activate

# スクリプトを実行
python 論文/実験結果集約/aggregate_experiment_results.py
```

## 集約される実験

以下の実験の結果が集約されます：

1. **メイン実験**: `論文/結果/追加実験/main_experiment_rerun_temperature0/`
2. **グループサイズ比較**: `論文/結果/追加実験/論文執筆用/group_size_comparison/steam/`
3. **Few-shot実験**: `論文/結果/追加実験/論文執筆用/fewshot_llm_eval/steam/`
4. **GPT5.1比較**: `論文/結果/追加実験/論文執筆用/model_comparison_temperature0/`
5. **アスペクト説明文比較**: `論文/結果/追加実験/論文執筆用/aspect_description_comparison/steam/`
6. **COCO Retrieved Concepts**: `論文/結果/追加実験/論文執筆用/coco_retrieved_concepts/`

## レポートの内容

各実験について以下の情報が含まれます：

- **実験パラメータ**: 実験設定（temperature, max_tokens, few_shot, group_size等）
- **実験結果**: 総実験数、成功数、失敗数
- **統計情報**: BERTスコア、BLEUスコア、LLMスコアの平均・最小・最大値
- **詳細統計**: データセット別・アスペクト別の詳細統計（JSON形式）

## 評価方法

レポートには以下の評価方法の説明が含まれます：

- **BERTスコア**: 意味類似度に基づく深層ベクトル比較
- **BLEUスコア**: n-gramベースの表層一致率
- **LLM評価スコア**: LLMによる意味的類似度評価（プロンプト含む）

## 注意事項

- レポートは実験結果の数値的な部分のみを集約しています（考察は含まれません）
- 各実験の詳細な考察は、各実験ディレクトリの`分析レポート/`を参照してください
- レポートは実行時に自動生成されるため、実験結果が更新された場合は再実行してください


