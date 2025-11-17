# shellcheck shell=bash

_preview_command() {
    local preview=""
    local arg
    for arg in "$@"; do
        if [[ -z "$preview" ]]; then
            preview=$(printf '%q' "$arg")
        else
            preview+=" "$(printf '%q' "$arg")
        fi
    done
    echo "$preview"
}

_store_cli_log() {
    local log_path=$1
    local run_dir=$2

    if [[ -z "$run_dir" ]]; then
        print_warning "run_dirが特定できずCLIログの保存をスキップしました"
        return
    fi

    mkdir -p "$run_dir/logs"
    if ! mv "$log_path" "$run_dir/logs/cli_run.log" 2>/dev/null; then
        cp "$log_path" "$run_dir/logs/cli_run.log"
    fi

    {
        echo "date: $(date)"
        echo "uname: $(uname -a)"
        echo "which python: $(which python)"
        echo "python --version: $(python --version 2>&1)"
        echo "pip list:"; pip list
        echo "git status -sb:"; git -C "$PROJECT_ROOT" status -sb
        echo "git head:"; git -C "$PROJECT_ROOT" rev-parse HEAD
    } > "$run_dir/logs/env_snapshot.txt"
}

_latest_run_dir() {
    local results_base="$PROJECT_ROOT/src/analysis/experiments/$(date +%Y)/$(date +%m)/$(date +%d)/results"
    local latest_json
    latest_json=$(find "$results_base" -type f -name 'batch_experiment_*.json' -print0 2>/dev/null | xargs -0 ls -t 2>/dev/null | head -1)
    if [[ -z "$latest_json" ]]; then
        echo ""
        return
    fi

    python - "$latest_json" <<'PY'
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else None
if not path:
    print("")
    raise SystemExit(0)

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

print(data.get("experiment_meta", {}).get("output_dir", ""))
PY
}

run_experiment() {
    print_header "実験実行"

    IFS=' ' read -ra ASPECT_ARRAY <<< "$ASPECTS"

    local cmd=(python "$PYTHON_SCRIPT" --dataset "$DATASET" --group-size "$GROUP_SIZE" --split-type "$SPLIT_TYPE")

    if [[ ${#ASPECT_ARRAY[@]} -eq 1 ]]; then
        cmd+=(--aspect "${ASPECT_ARRAY[0]}")
    else
        cmd+=(--aspects)
        cmd+=("${ASPECT_ARRAY[@]}")
    fi

    if [[ "$USE_ASPECT_DESCRIPTIONS" == "1" ]]; then
        cmd+=(--use-aspect-descriptions)
        if [[ -n "$ASPECT_DESCRIPTIONS_FILE" ]]; then
            cmd+=(--aspect-descriptions-file "$ASPECT_DESCRIPTIONS_FILE")
        fi
    fi

    if [[ "$USE_EXAMPLES" == "1" ]]; then
        cmd+=(--use-examples)
        if [[ -n "$EXAMPLES_FILE" ]]; then
            cmd+=(--examples-file "$EXAMPLES_FILE")
        fi
        if [[ -n "$MAX_EXAMPLES" ]]; then
            cmd+=(--max-examples "$MAX_EXAMPLES")
        fi
    fi

    if [[ -n "$LLM_MODEL" ]]; then
        cmd+=(--llm-model "$LLM_MODEL")
    fi

    if [[ "$USE_LLM_SCORE" == "1" ]]; then
        cmd+=(--use-llm-score)
        if [[ -n "$LLM_EVALUATION_MODEL" ]]; then
            cmd+=(--llm-evaluation-model "$LLM_EVALUATION_MODEL")
        fi
        if [[ -n "$LLM_EVALUATION_TEMPERATURE" ]]; then
            cmd+=(--llm-evaluation-temperature "$LLM_EVALUATION_TEMPERATURE")
        fi
    fi

    if [[ "$SILENT_MODE" == "1" ]]; then
        cmd+=(--silent)
    fi

    print_info "実験を開始します..."
    echo ""

    echo -e "${CYAN}実行コマンド:${NC}"
    _preview_command "${cmd[@]}"
    echo ""

    local run_ts
    run_ts=$(date +%Y%m%d_%H%M%S)

    if [[ "$SILENT_MODE" == "1" ]]; then
        if "${cmd[@]}"; then
            print_success "実験が正常に完了しました"
        else
            print_error "実験中にエラーが発生しました"
        fi
        return
    fi

    local cli_tmp_log="/tmp/cli_run_${run_ts}_$$.log"
    "${cmd[@]}" 2>&1 | tee "$cli_tmp_log"
    local exit_code=${PIPESTATUS[0]}

    if [[ $exit_code -eq 0 ]]; then
        print_success "実験が正常に完了しました"
        save_config
    else
        print_error "実験中にエラーが発生しました"
    fi

    local run_dir
    run_dir=$(_latest_run_dir)
    if [[ -f "$cli_tmp_log" ]]; then
        _store_cli_log "$cli_tmp_log" "$run_dir"
    fi
}

