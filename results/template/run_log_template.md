# 実行ログ貼り付けテンプレート {{TIMESTAMP}}

- 実験詳細: {{DETAIL_DIR_MD_LINK}}
- CLIログ: {{CLI_LOG_MD_LINK}}

## ログ抜粋（先頭）
```text
{{CLI_LOG_HEAD}}
```

## ログ抜粋（末尾）
```text
{{CLI_LOG_TAIL}}
```

<!-- 置換仕様:
  - {{CLI_LOG_MD_LINK}} = [cli_run.log]({{CLI_LOG_PATH}})
  - {{CLI_LOG_HEAD}} / {{CLI_LOG_TAIL}} は先頭/末尾 N 行を差し込み（Nは設定値、例: 50）
-->
