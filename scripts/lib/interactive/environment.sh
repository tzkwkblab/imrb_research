# shellcheck shell=bash

check_environment() {
    print_section "環境チェック"

    if [[ -z "$VIRTUAL_ENV" ]]; then
        print_info "仮想環境をアクティベート中..."
        if [[ -f "$VENV_PATH/bin/activate" ]]; then
            # shellcheck disable=SC1090
            source "$VENV_PATH/bin/activate"
            print_success "仮想環境をアクティベートしました"
        else
            print_error "仮想環境が見つかりません: $VENV_PATH"
            exit 1
        fi
    else
        print_success "仮想環境は既にアクティブです"
    fi

    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        print_error "Pythonスクリプトが見つかりません: $PYTHON_SCRIPT"
        exit 1
    fi

    print_success "環境チェック完了"
}

