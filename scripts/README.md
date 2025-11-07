## scripts/ 概要

実験の起動や変換等の補助スクリプトを配置します。

### run_interactive_experiment.sh

対話式にデータセット/アスペクト/分割タイプ等を選択し実験を実行するスクリプトです。

#### 起動方法

```bash
cd /Users/seinoshun/imrb_research
source .venv/bin/activate
bash scripts/run_interactive_experiment.sh
```

#### 選択肢の説明

1. **サイレントモード設定**
   - 無効（推奨）: ファイル保存とログ生成が行われます
   - 有効: ファイル保存をスキップし、コンソール出力のみ（デバッグ用途）

2. **データセット選択**
   - `steam`: Steamゲームレビューデータセット（動作確認済み）
   - `semeval`: SemEval ABSAレストランレビューデータセット（実験的）
   - `amazon`: Amazon商品レビューデータセット（実験的）
   - `retrieved_concepts`: COCO画像キャプションデータセット（動作確認済み）

3. **アスペクト選択**
   - データセットごとに利用可能なアスペクトが表示されます
   - Steam: gameplay, visual, story, audio, technical, price, suggestion, recommended
   - Retrieved Concepts: concept_0 ～ concept_299（300個）

4. **分割タイプ選択**
   - `binary_label`: ポジ/ネガ分類用（Steam推奨）
   - `aspect_vs_others`: アスペクト間比較用（汎用）
   - `aspect_vs_bottom100`: Top-100 vs Bottom-100（retrieved_concepts専用）

5. **グループサイズ設定**
   - 各グループ（A/B）のサンプル数を指定（デフォルト: 50）

#### 詳細ドキュメント

- [実験スクリプト使い方ガイド](../docs/experiments/guides/experiment-script-guide.md)
- [Steam実験手順](../docs/experiments/playbooks/steam-experiment-guide.md)
- [retrieved_concepts実験手順](../docs/experiments/playbooks/retrieved-concepts-experiment-guide.md)
- [トラブルシューティング](../docs/experiments/troubleshooting/common-issues.md)
