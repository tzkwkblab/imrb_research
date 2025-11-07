# トラブルシューティングガイド

実験実行中によく発生するエラーとその対処法をまとめています。

## 目次

1. [API キー関連のエラー](#api-キー関連のエラー)
2. [データ読み込みエラー](#データ読み込みエラー)
3. [サンプル数不足エラー](#サンプル数不足エラー)
4. [分割タイプ関連のエラー](#分割タイプ関連のエラー)
5. [LLM API エラー](#llm-api-エラー)
6. [その他のエラー](#その他のエラー)
7. [デバッグ方法](#デバッグ方法)

## API キー関連のエラー

### エラーメッセージ

```
OPENAI_API_KEY環境変数が設定されていません
```

### 原因

`.env`ファイルにAPIキーが設定されていない、または環境変数が読み込まれていない。

### 対処法

1. **`.env`ファイルの確認**

```bash
cd /Users/seinoshun/imrb_research
cat .env | grep OPENAI_API_KEY
```

2. **環境変数の設定**

`.env`ファイルに以下を追加：

```
OPENAI_API_KEY=sk-...
```

3. **環境変数の読み込み確認**

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('OPENAI_API_KEY' in os.environ)"
```

`True`が表示されれば正常です。

4. **仮想環境の確認**

仮想環境がアクティブになっているか確認：

```bash
echo $VIRTUAL_ENV
source .venv/bin/activate
```

## データ読み込みエラー

### エラーメッセージ

```
データファイルが見つかりません: /path/to/data
JSONファイルが見つかりません: /path/to/data
```

### 原因

データセットのパスが正しくない、またはデータファイルが存在しない。

### 対処法

1. **データセットパスの確認**

```bash
# Steam
ls -la /Users/seinoshun/imrb_research/data/external/steam-review-aspect-dataset/current/

# retrieved_concepts
ls -la /Users/seinoshun/imrb_research/data/external/retrieved-concepts/farnoosh/current/
```

2. **シンボリックリンクの確認**

`current`リンクが正しく設定されているか確認：

```bash
ls -la /Users/seinoshun/imrb_research/data/external/retrieved-concepts/farnoosh/current
```

3. **データファイルの存在確認**

```bash
# retrieved_conceptsの場合
ls -la /Users/seinoshun/imrb_research/data/external/retrieved-concepts/farnoosh/v1.0_2025-10-29/
```

`retrieved_dataset_100.json`と`retrieved_dataset_bottom_100.json`の両方が存在することを確認。

4. **データローダーのテスト**

```bash
cd /Users/seinoshun/imrb_research/src/analysis/experiments/2025/10/10
python -c "
from utils.datasetManager.dataset_manager import DatasetManager
from pathlib import Path
manager = DatasetManager(data_root=Path('/Users/seinoshun/imrb_research/data/external'))
records = manager.load_dataset('retrieved_concepts')
print(f'読み込み成功: {len(records)}件')
"
```

## サンプル数不足エラー

### エラーメッセージ

```
ポジティブサンプルが不足: 10 < 50
アスペクト 'xxx' のレコードが見つかりません
```

### 原因

指定したグループサイズに対して、利用可能なサンプル数が不足している。

### 対処法

1. **グループサイズの調整**

グループサイズを小さくする：

```bash
python run_experiment.py --dataset steam --aspect gameplay --group-size 10
```

2. **利用可能なサンプル数の確認**

```bash
python -c "
from utils.datasetManager.dataset_manager import DatasetManager
from pathlib import Path
manager = DatasetManager(data_root=Path('/Users/seinoshun/imrb_research/data/external'))
records = manager.load_dataset('steam')
aspect_records = [r for r in records if r.aspect == 'gameplay']
positive = [r for r in aspect_records if r.label == 1]
negative = [r for r in aspect_records if r.label == 0]
print(f'ポジティブ: {len(positive)}件')
print(f'ネガティブ: {len(negative)}件')
"
```

3. **分割タイプの変更**

`aspect_vs_others`に変更すると、より多くのサンプルが利用可能になる場合があります。

## 分割タイプ関連のエラー

### エラーメッセージ

```
未対応の分割タイプ: xxx
```

### 原因

存在しない分割タイプを指定している。

### 対処法

1. **利用可能な分割タイプの確認**

- `binary_label`: ポジ/ネガ分類用
- `aspect_vs_others`: アスペクト間比較用
- `aspect_vs_bottom100`: Top-100 vs Bottom-100（retrieved_concepts専用）

2. **データセットと分割タイプの組み合わせ確認**

- Steam → `binary_label`（推奨）または`aspect_vs_others`
- SemEval/Amazon → `aspect_vs_others`
- retrieved_concepts → `aspect_vs_bottom100`（推奨）または`aspect_vs_others`

3. **コマンドの修正**

```bash
# 誤り
python run_experiment.py --dataset retrieved_concepts --aspect concept_0 --split-type binary_label

# 正しい
python run_experiment.py --dataset retrieved_concepts --aspect concept_0 --split-type aspect_vs_bottom100
```

## LLM API エラー

### エラーメッセージ

```
HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 429 Too Many Requests"
HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 401 Unauthorized"
```

### 原因

- APIレート制限に達した
- APIキーが無効
- ネットワークエラー

### 対処法

1. **レート制限エラー（429）**

- しばらく待ってから再実行
- グループサイズを小さくして実験数を減らす
- `--silent`フラグで動作確認のみ行う

2. **認証エラー（401）**

- APIキーが正しいか確認
- APIキーに有効期限がないか確認
- `.env`ファイルの再読み込み

3. **ネットワークエラー**

- インターネット接続を確認
- プロキシ設定を確認
- ファイアウォール設定を確認

## その他のエラー

### メモリ不足エラー

**症状**: 大容量データセット（retrieved_concepts）の読み込み時にメモリ不足

**対処法**:
- 一度に処理するコンセプト数を減らす
- グループサイズを小さくする
- ストリーミングパーサーが正しく動作しているか確認

### インポートエラー

**症状**: `ModuleNotFoundError`や`ImportError`

**対処法**:
1. 仮想環境がアクティブか確認
2. 必要なパッケージがインストールされているか確認

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

3. Pythonパスの確認

```bash
python -c "import sys; print(sys.path)"
```

### ファイル書き込みエラー

**症状**: 結果ファイルの保存に失敗

**対処法**:
1. 出力ディレクトリの権限確認

```bash
ls -la /Users/seinoshun/imrb_research/src/analysis/experiments/2025/10/10/results/
```

2. ディレクトリの作成

```bash
mkdir -p /Users/seinoshun/imrb_research/src/analysis/experiments/2025/10/10/results/
```

3. `--silent`フラグでファイル保存をスキップして動作確認

## デバッグ方法

### デバッグモードの有効化

```bash
python run_experiment.py --dataset steam --aspect gameplay --debug
```

デバッグモードでは詳細なログが出力されます。

### サイレントモードでの動作確認

```bash
python run_experiment.py --dataset retrieved_concepts --aspect concept_0 --group-size 5 --split-type aspect_vs_bottom100 --silent
```

`--silent`フラグを使用すると、ファイル保存をスキップして動作確認ができます。

### データローダーの個別テスト

```bash
cd /Users/seinoshun/imrb_research/src/analysis/experiments/2025/10/10
python test_utils_import.py
```

### ログファイルの確認

対話型スクリプトを使用した場合、ログは以下に保存されます：

```
src/analysis/experiments/2025/10/31/results/{timestamp}/logs/
├── cli_run.log
└── python.log
```

### 段階的なデバッグ

1. **データ読み込みの確認**

```python
from utils.datasetManager.dataset_manager import DatasetManager
from pathlib import Path

manager = DatasetManager(data_root=Path('/Users/seinoshun/imrb_research/data/external'))
records = manager.load_dataset('retrieved_concepts')
print(f'読み込み成功: {len(records)}件')
```

2. **分割の確認**

```python
result = manager.split_dataset('retrieved_concepts', 'concept_0', 5, 'aspect_vs_bottom100')
print(f'Group A: {len(result.group_a)}件')
print(f'Group B: {len(result.group_b)}件')
```

3. **LLM呼び出しの確認**

```python
from utils.cfGenerator.contrast_factor_analyzer import ContrastFactorAnalyzer

analyzer = ContrastFactorAnalyzer(debug=True)
# 小さなサンプルでテスト
```

## よくある質問

### Q: 実験が途中で止まる

A: ネットワークエラーやAPIレート制限の可能性があります。`--silent`フラグで動作確認し、グループサイズを小さくして再実行してください。

### Q: 結果ファイルが生成されない

A: `--silent`フラグが指定されていないか確認してください。また、出力ディレクトリの権限を確認してください。

### Q: スコアが0になる

A: BLEUスコアは語彙的一致度のため、完全に異なる表現では0になることがあります。BERTスコアを主に確認してください。

### Q: retrieved_conceptsでグループBが空になる

A: `aspect_vs_bottom100`を使用しているか確認してください。`aspect_vs_others`では、retrieved_conceptsデータセットではグループBが正しく生成されない場合があります。

## 関連ドキュメント

- [実験スクリプト使い方ガイド](../guides/experiment-script-guide.md)
- [統一パイプラインREADME](../../../src/analysis/experiments/2025/10/10/README.md)

