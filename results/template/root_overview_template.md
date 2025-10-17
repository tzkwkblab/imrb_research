<!-- テンプレ説明: 下記の記号は実行時に置換されます -->
<!-- {{TIMESTAMP}}: 実行時刻(YYYYMMDD_HHMMSS) -->
<!-- {{RUN_NAME}}: 実験名（configのrun_name。未設定時は設定ファイル名） -->
<!-- {{DETAIL_DIR_PATH}}: 詳細ディレクトリへの相対パス（クリック用に下のリンク変数推奨） -->
<!-- {{DETAIL_SUMMARY_PATH}}: 詳細summary.mdへの相対パス -->
<!-- {{DETAIL_DIR_MD_LINK}}: [詳細ディレクトリ](相対パス) の完成済みリンク -->
<!-- {{DETAIL_SUMMARY_MD_LINK}}: [詳細サマリー](相対パス) の完成済みリンク -->
<!-- {{TOTAL_EXPERIMENTS}}: 総実験数 / {{SUCCESSFUL_EXPERIMENTS}}: 成功数 -->
<!-- {{RESULTS_TABLE}}: 先頭数件の結果テーブル（データセット/アスペクト/BERT/BLEU） -->

# 実験概要 {{TIMESTAMP}}

- 実験名: {{RUN_NAME}}
- {{DETAIL_DIR_MD_LINK}}
- {{DETAIL_SUMMARY_MD_LINK}}
- 総実験数: {{TOTAL_EXPERIMENTS}} / 成功: {{SUCCESSFUL_EXPERIMENTS}}

## 結果概要
{{RESULTS_TABLE}}