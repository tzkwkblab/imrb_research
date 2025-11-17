#!/bin/bash

set -e

PROJECT_ROOT="/Users/seinoshun/imrb_research"
PYTHON_SCRIPT="$PROJECT_ROOT/src/analysis/experiments/2025/10/10/run_experiment.py"
VENV_PATH="$PROJECT_ROOT/.venv"
CONFIG_FILE="$PROJECT_ROOT/.experiment_config"

SILENT_MODE=0

DATASET=""
ASPECTS=""
GROUP_SIZE=""
SPLIT_TYPE=""
USE_ASPECT_DESCRIPTIONS="0"
ASPECT_DESCRIPTIONS_FILE=""
USE_EXAMPLES="0"
EXAMPLES_FILE=""
MAX_EXAMPLES=""

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
LIB_DIR="$SCRIPT_DIR/lib"
INTERACTIVE_DIR="$LIB_DIR/interactive"

# shellcheck source=lib/ui.sh
source "$LIB_DIR/ui.sh"
# shellcheck source=lib/interactive/environment.sh
source "$INTERACTIVE_DIR/environment.sh"
# shellcheck source=lib/interactive/config.sh
source "$INTERACTIVE_DIR/config.sh"
# shellcheck source=lib/interactive/inputs.sh
source "$INTERACTIVE_DIR/inputs.sh"
# shellcheck source=lib/interactive/runner.sh
source "$INTERACTIVE_DIR/runner.sh"

reset_experiment_state() {
    DATASET=""
    ASPECTS=""
    GROUP_SIZE=""
    SPLIT_TYPE=""
    USE_ASPECT_DESCRIPTIONS="0"
    ASPECT_DESCRIPTIONS_FILE=""
    USE_EXAMPLES="0"
    EXAMPLES_FILE=""
    MAX_EXAMPLES=""
    USE_LLM_SCORE="0"
    LLM_MODEL=""
    LLM_EVALUATION_MODEL="gpt-5-nano"
    LLM_EVALUATION_TEMPERATURE="0.0"
}

run_new_configuration() {
    reset_experiment_state

    select_dataset
    choose_aspect_representation || true
    select_aspects
    input_group_size
    select_split_type
    select_examples_file || true
    select_llm_evaluation || true

    if confirm_settings; then
        run_experiment
    else
        return 1
    fi
}

main_menu() {
    clear
    print_header "対話型実験実行システム"

    choose_silent_mode
    check_environment

    if load_previous_config; then
        if confirm_settings; then
            run_experiment
            return
        fi
        reset_experiment_state
    else
        reset_experiment_state
    fi

    if ! run_new_configuration; then
        print_warning "実験をキャンセルしました"
    fi
}

setup_colors
main_menu
print_header "実験システム終了"
