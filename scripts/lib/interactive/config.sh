# shellcheck shell=bash

save_config() {
    if [[ "$SILENT_MODE" == "1" ]]; then
        return
    fi

    cat > "$CONFIG_FILE" <<EOF
DATASET="$DATASET"
ASPECTS="$ASPECTS"
GROUP_SIZE="$GROUP_SIZE"
SPLIT_TYPE="$SPLIT_TYPE"
USE_ASPECT_DESCRIPTIONS="$USE_ASPECT_DESCRIPTIONS"
ASPECT_DESCRIPTIONS_FILE="$ASPECT_DESCRIPTIONS_FILE"
USE_EXAMPLES="$USE_EXAMPLES"
EXAMPLES_FILE="$EXAMPLES_FILE"
MAX_EXAMPLES="$MAX_EXAMPLES"
USE_LLM_SCORE="$USE_LLM_SCORE"
LLM_EVALUATION_MODEL="$LLM_EVALUATION_MODEL"
LLM_EVALUATION_TEMPERATURE="$LLM_EVALUATION_TEMPERATURE"
EOF

    print_info "設定を保存しました: $CONFIG_FILE"
}

load_previous_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        return 1
    fi

    # shellcheck disable=SC1090
    source "$CONFIG_FILE"

    print_section "前回の設定"
    echo "データセット: $DATASET"
    echo "アスペクト: $ASPECTS"
    echo "グループサイズ: $GROUP_SIZE"
    echo "分割タイプ: $SPLIT_TYPE"
    if [[ "$USE_ASPECT_DESCRIPTIONS" == "1" ]]; then
        echo "説明文比較: 有効"
        echo "説明CSV: $ASPECT_DESCRIPTIONS_FILE"
    else
        echo "説明文比較: 無効"
    fi
    if [[ "$USE_EXAMPLES" == "1" ]]; then
        echo "例題使用: 有効"
        echo "例題ファイル: $EXAMPLES_FILE"
        if [[ -n "$MAX_EXAMPLES" ]]; then
            echo "最大例題数: $MAX_EXAMPLES"
        fi
    else
        echo "例題使用: 無効"
    fi
    if [[ "$USE_LLM_SCORE" == "1" ]]; then
        echo "LLM評価スコア: 有効"
        echo "LLM評価モデル: $LLM_EVALUATION_MODEL"
        echo "LLM評価温度: $LLM_EVALUATION_TEMPERATURE"
    else
        echo "LLM評価スコア: 無効"
    fi
    echo ""

    read -p "前回の設定を使用しますか？ (y/n): " use_previous
    if [[ "$use_previous" == "y" || "$use_previous" == "Y" ]]; then
        return 0
    fi

    return 1
}

