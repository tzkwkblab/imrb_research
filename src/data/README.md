## src/data/ 概要

データ取得・前処理・特徴定義などのスクリプト群です。外部データは `data/external/`、処理結果は `data/processed/` を利用します。

### 主なサブ構成

- `download_*.py` / `collect.py`: データ取得・同期
- `features/` と `features.py`: アスペクト等の機能定義
- `examples/`: サンプル CSV
- `sampling/`: サンプリング関連

### 実行前提

- 仮想環境を有効化
- 外部データは `data/README.md` の構造に従って配置

詳細は各スクリプトの先頭説明と `data/README.md` を参照してください。
