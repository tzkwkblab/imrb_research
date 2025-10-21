#!/bin/bash

# 対話型実験実行スクリプト
# 使いやすいメニューインターフェースで実験設定と実行を行う

set -e

# =====================================
# 色設定
# =====================================
setup_colors() {
    if [[ -t 1 ]]; then
        RED='\033[0;31m'
        GREEN='\033[0;32m'
        YELLOW='\033[1;33m'
        BLUE='\033[0;34m'
        MAGENTA='\033[0;35m'
        CYAN='\033[0;36m'
        BOLD='\033[1m'
        NC='\033[0m'
    else
        RED=''
        GREEN=''
        YELLOW=''
        BLUE=''
        MAGENTA=''
        CYAN=''
        BOLD=''
        NC=''
    fi
}

# =====================================
# グローバル変数
# =====================================
PROJECT_ROOT="/Users/seinoshun/imrb_research"
PYTHON_SCRIPT="$PROJECT_ROOT/src/analysis/experiments/2025/10/10/run_experiment.py"
VENV_PATH="$PROJECT_ROOT/.venv"
# プロジェクト内の設定ファイルに固定（ホーム直下は使用しない）
CONFIG_FILE="$PROJECT_ROOT/.experiment_config"
TEMP_RESULT_FILE="/tmp/experiment_result_$$.json"

# 実験設定変数
DATASET=""
ASPECTS=""
GROUP_SIZE=""
SPLIT_TYPE=""
USE_ASPECT_DESCRIPTIONS="0"
ASPECT_DESCRIPTIONS_FILE=""

# =====================================
# ユーティリティ関数
# =====================================

print_header() {
    echo -e "${BOLD}${CYAN}"
    echo "============================================================"
    echo "$1"
    echo "============================================================"
    echo -e "${NC}"
}

print_section() {
    echo -e "\n${BOLD}${BLUE}=== $1 ===${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# =====================================
# 環境設定
# =====================================

check_environment() {
    print_section "環境チェック"
    
    # 仮想環境チェック
    if [[ -z "$VIRTUAL_ENV" ]]; then
        print_info "仮想環境をアクティベート中..."
        if [[ -f "$VENV_PATH/bin/activate" ]]; then
            source "$VENV_PATH/bin/activate"
            print_success "仮想環境をアクティベートしました"
        else
            print_error "仮想環境が見つかりません: $VENV_PATH"
            exit 1
        fi
    else
        print_success "仮想環境は既にアクティブです"
    fi
    
    # Pythonスクリプトチェック
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        print_error "Pythonスクリプトが見つかりません: $PYTHON_SCRIPT"
        exit 1
    fi
    
    print_success "環境チェック完了"
}

# =====================================
# 設定保存・読み込み
# =====================================

save_config() {
    # 値をクォートして安全にsource可能にする
    # 例: ASPECTS="gameplay visual"
    cat > "$CONFIG_FILE" << EOF
DATASET="$DATASET"
ASPECTS="$ASPECTS"
GROUP_SIZE="$GROUP_SIZE"
SPLIT_TYPE="$SPLIT_TYPE"
USE_ASPECT_DESCRIPTIONS="$USE_ASPECT_DESCRIPTIONS"
ASPECT_DESCRIPTIONS_FILE="$ASPECT_DESCRIPTIONS_FILE"
EOF
    print_info "設定を保存しました: $CONFIG_FILE"
}

load_previous_config() {
    # プロジェクト内の設定のみ参照
    if [[ -f "$CONFIG_FILE" ]]; then
        # シェルの単語分割で誤動作しないようにクォート済みファイルをsource
        source "$CONFIG_FILE"
        print_section "前回の設定"
        echo "データセット: $DATASET"
        echo "アスペクト: $ASPECTS"
        echo "グループサイズ: $GROUP_SIZE"
        echo "分割タイプ: $SPLIT_TYPE"
        echo "説明文比較: $([[ "$USE_ASPECT_DESCRIPTIONS" == "1" ]] && echo "有効" || echo "無効")"
        if [[ "$USE_ASPECT_DESCRIPTIONS" == "1" ]]; then
            echo "説明CSV: $ASPECT_DESCRIPTIONS_FILE"
        fi
        echo ""
        
        read -p "前回の設定を使用しますか？ (y/n): " use_previous
        if [[ "$use_previous" == "y" || "$use_previous" == "Y" ]]; then
            return 0
        fi
    fi
    return 1
}
# =====================================
# 説明CSV選択
# =====================================

select_description_csv() {
    print_section "アスペクト説明CSV選択（任意）"

    # 探索ディレクトリ（データ配置ディレクトリ配下）
    local desc_dir="$PROJECT_ROOT/data/analysis-workspace/aspect_descriptions/$DATASET"
    local -a csv_files=()

    if [[ -d "$desc_dir" ]]; then
        while IFS= read -r -d '' f; do
            csv_files+=("$f")
        done < <(find "$desc_dir" -maxdepth 1 -type f -name "*.csv" -print0 2>/dev/null | sort -z)
    fi

    # 外部デフォルト（存在すれば追加候補）
    local external_csv=""
    case "$DATASET" in
        steam)
            external_csv="$PROJECT_ROOT/data/external/steam-review-aspect-dataset/current/descriptions.csv"
            ;;
        semeval)
            external_csv="$PROJECT_ROOT/data/external/absa-review-dataset/pyabsa-integrated/current/descriptions.csv"
            ;;
        amazon)
            external_csv="$PROJECT_ROOT/data/external/amazon-product-reviews/kaggle-bittlingmayer/current/descriptions.csv"
            ;;
    esac

    local has_external=0
    if [[ -f "$external_csv" ]]; then
        has_external=1
    fi

    echo "0) 単語比較（説明文なし）"

    local i=1
    for f in "${csv_files[@]}"; do
        echo "$i) $(basename "$f")"
        i=$((i+1))
    done

    local external_index=-1
    if [[ $has_external -eq 1 ]]; then
        external_index=$i
        echo "$i) 外部データセットのdescriptions.csv"
    fi

    echo ""
    read -p "選択してください (番号、Enter=0): " choice
    if [[ -z "$choice" ]]; then
        choice=0
    fi

    if [[ "$choice" == "0" ]]; then
        USE_ASPECT_DESCRIPTIONS="0"
        ASPECT_DESCRIPTIONS_FILE=""
        print_success "単語比較を選択しました"
        return 0
    fi

    # 数値チェック
    if ! [[ "$choice" =~ ^[0-9]+$ ]]; then
        print_error "無効な入力です"
        return 1
    fi

    local idx=$choice
    local total_internal=${#csv_files[@]}
    if [[ $idx -ge 1 && $idx -le $total_internal ]]; then
        USE_ASPECT_DESCRIPTIONS="1"
        ASPECT_DESCRIPTIONS_FILE="${csv_files[$((idx-1))]}"
        print_success "説明CSVを選択: $(basename "$ASPECT_DESCRIPTIONS_FILE")"
        return 0
    fi

    if [[ $has_external -eq 1 && $idx -eq $external_index ]]; then
        USE_ASPECT_DESCRIPTIONS="1"
        ASPECT_DESCRIPTIONS_FILE="$external_csv"
        print_success "外部の説明CSVを選択: $ASPECT_DESCRIPTIONS_FILE"
        return 0
    fi

    print_error "無効な番号です"
    return 1
}


# =====================================
# データセット選択
# =====================================

select_dataset() {
    print_section "データセット選択"
    
    echo "1. Steam Reviews (動作確認済み)"
    echo "2. SemEval ABSA (実験的)"
    echo "3. Amazon Reviews (実験的)"
    echo ""
    
    while true; do
        read -p "選択してください (1-3): " choice
        case $choice in
            1) DATASET="steam"; break;;
            2) DATASET="semeval"; break;;
            3) DATASET="amazon"; break;;
            *) print_error "無効な選択です。1-3の数字を入力してください";;
        esac
    done
    
    print_success "データセット: $DATASET を選択しました"
}

# =====================================
# アスペクト選択
# =====================================

select_aspects() {
    print_section "アスペクト選択"
    
    local -a available_aspects
    
    case $DATASET in
        steam)
            available_aspects=("gameplay" "visual" "story" "audio" "technical" "price" "suggestion" "recommended")
            ;;
        semeval)
            available_aspects=("food" "service" "atmosphere" "price")
            ;;
        amazon)
            available_aspects=("quality" "price" "delivery" "service" "product")
            ;;
    esac
    
    echo "利用可能なアスペクト:"
    for i in "${!available_aspects[@]}"; do
        echo "$((i+1)). ${available_aspects[$i]}"
    done
    echo ""
    
    while true; do
        read -p "選択してください（カンマ区切りで複数可, 例: 1,2,3）: " selection
        
        # カンマで分割
        IFS=',' read -ra SELECTED <<< "$selection"
        
        local selected_aspects=()
        local valid=true
        
        for num in "${SELECTED[@]}"; do
            num=$(echo "$num" | xargs)  # trim
            if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 1 ] && [ "$num" -le "${#available_aspects[@]}" ]; then
                selected_aspects+=("${available_aspects[$((num-1))]}")
            else
                print_error "無効な番号: $num"
                valid=false
                break
            fi
        done
        
        if $valid && [ ${#selected_aspects[@]} -gt 0 ]; then
            ASPECTS=$(IFS=' '; echo "${selected_aspects[*]}")
            echo ""
            print_success "選択されたアスペクト: $ASPECTS"
            break
        else
            print_error "有効なアスペクトを選択してください"
        fi
    done
}

# =====================================
# グループサイズ入力
# =====================================

input_group_size() {
    print_section "グループサイズ設定"
    
    echo "推奨値:"
    echo "  - テスト: 10-20"
    echo "  - 通常: 50-100"
    echo "  - 本格実験: 200-500"
    echo ""
    
    while true; do
        read -p "グループサイズを入力 (デフォルト: 50): " size
        
        if [[ -z "$size" ]]; then
            GROUP_SIZE=50
            break
        elif [[ "$size" =~ ^[0-9]+$ ]] && [ "$size" -ge 1 ]; then
            GROUP_SIZE=$size
            break
        else
            print_error "正の整数を入力してください"
        fi
    done
    
    print_success "グループサイズ: $GROUP_SIZE"
}

# =====================================
# 分割タイプ選択
# =====================================

select_split_type() {
    print_section "分割タイプ選択"
    
    echo "1. binary_label (Steamデータセット用)"
    echo "2. aspect_vs_others (SemEval/Amazonデータセット用)"
    echo ""
    
    local default_type
    if [[ "$DATASET" == "steam" ]]; then
        default_type="binary_label"
        print_info "Steamデータセットには binary_label が推奨されます"
    else
        default_type="aspect_vs_others"
        print_info "$DATASET データセットには aspect_vs_others が推奨されます"
    fi
    
    while true; do
        read -p "選択してください (1-2, Enter=推奨): " choice
        
        if [[ -z "$choice" ]]; then
            SPLIT_TYPE=$default_type
            break
        fi
        
        case $choice in
            1) SPLIT_TYPE="binary_label"; break;;
            2) SPLIT_TYPE="aspect_vs_others"; break;;
            *) print_error "無効な選択です。1か2を入力してください";;
        esac
    done
    
    print_success "分割タイプ: $SPLIT_TYPE"
}

# =====================================
# 設定確認
# =====================================

confirm_settings() {
    print_section "設定確認"
    
    echo -e "実験設定:"
    echo "  データセット: $DATASET"
    echo "  アスペクト: $ASPECTS"
    echo "  グループサイズ: $GROUP_SIZE"
    echo "  分割タイプ: $SPLIT_TYPE"
    echo "  説明文比較: $([[ "$USE_ASPECT_DESCRIPTIONS" == "1" ]] && echo "有効" || echo "無効")"
    if [[ "$USE_ASPECT_DESCRIPTIONS" == "1" ]]; then
        echo "  説明CSV: $ASPECT_DESCRIPTIONS_FILE"
    fi
    echo ""
    
    read -p "この設定で実験を開始しますか？ (y/n): " confirm
    
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        print_warning "実験をキャンセルしました"
        return 1
    fi
    
    return 0
}

# =====================================
# 実験実行
# =====================================

run_experiment() {
    print_header "実験実行"
    
    # アスペクトを配列に変換
    IFS=' ' read -ra ASPECT_ARRAY <<< "$ASPECTS"
    
    print_info "実験を開始します..."
    echo ""
    
    # Pythonスクリプトを実行
    local cmd="python $PYTHON_SCRIPT --dataset $DATASET --group-size $GROUP_SIZE --split-type $SPLIT_TYPE"
    
    if [ ${#ASPECT_ARRAY[@]} -eq 1 ]; then
        cmd="$cmd --aspect ${ASPECT_ARRAY[0]}"
    else
        cmd="$cmd --aspects ${ASPECT_ARRAY[@]}"
    fi

    # 説明文比較オプション
    if [[ "$USE_ASPECT_DESCRIPTIONS" == "1" ]]; then
        cmd="$cmd --use-aspect-descriptions"
        if [[ -n "$ASPECT_DESCRIPTIONS_FILE" ]]; then
            cmd="$cmd --aspect-descriptions-file \"$ASPECT_DESCRIPTIONS_FILE\""
        fi
    fi
    
    echo -e "${CYAN}実行コマンド:${NC}"
    echo "$cmd"
    echo ""
    
    # 実行: 画面表示しながら一時ログへ保存
    RUN_TS="$(date +%Y%m%d_%H%M%S)"
    CLI_TMP_LOG="/tmp/cli_run_${RUN_TS}_$$.log"
    if eval "$cmd" 2>&1 | tee "$CLI_TMP_LOG"; then
        print_success "実験が正常に完了しました"
        save_config
        # 後続でログ保存処理
        :
    else
        print_error "実験中にエラーが発生しました"
        # 失敗時もログは保存対象
        :
    fi

    # 実行後: 最新の結果JSONから run_dir を取得
    local latest_json=$(find "$PROJECT_ROOT/src/analysis/experiments/2025/10/10/results" -type f -name 'batch_experiment_*.json' -print0 2>/dev/null | xargs -0 ls -t 2>/dev/null | head -1)
    local run_dir
    if [[ -n "$latest_json" ]]; then
        run_dir=$(python - "$latest_json" <<'PY'
import json,sys
p = sys.argv[1] if len(sys.argv) > 1 else None
if not p:
    print("")
    raise SystemExit(0)
with open(p,'r',encoding='utf-8') as f:
    d=json.load(f)
print(d.get('experiment_meta',{}).get('output_dir',''))
PY
)
    fi

    if [[ -n "$run_dir" ]]; then
        mkdir -p "$run_dir/logs"
        mv "$CLI_TMP_LOG" "$run_dir/logs/cli_run.log" 2>/dev/null || cp "$CLI_TMP_LOG" "$run_dir/logs/cli_run.log"
        # 環境スナップショット
        {
            echo "date: $(date)"
            echo "uname: $(uname -a)"
            echo "which python: $(which python)"
            echo "python --version: $(python --version 2>&1)"
            echo "pip list:"; pip list
            echo "git status -sb:"; git -C "$PROJECT_ROOT" status -sb
            echo "git head:"; git -C "$PROJECT_ROOT" rev-parse HEAD
        } > "$run_dir/logs/env_snapshot.txt"
    else
        print_warning "run_dirが特定できずCLIログの保存をスキップしました"
    fi

    # 正常終了/異常終了の戻り値は直前のevalの終了コードを反映できないため0固定
    return 0
}

# =====================================
# ディレクトリ検索
# =====================================

search_directory() {
    local search_name="$1"
    local max_depth=3
    
    print_info "検索中... (3階層まで)"
    
    # 検索実行（プロジェクトルートから）
    cd "$PROJECT_ROOT"
    local results
    mapfile -t results < <(find . -maxdepth $max_depth -type d -name "*$search_name*" 2>/dev/null | sort)
    
    local count=${#results[@]}
    
    if [ $count -eq 0 ]; then
        print_error "ディレクトリが見つかりません"
        return 1
    elif [ $count -gt 10 ]; then
        print_warning "検索結果が多すぎます ($count件)"
        echo "より具体的な名前を入力してください"
        return 2
    else
        echo -e "\n${BOLD}【検索結果: $count件】${NC}"
        for i in "${!results[@]}"; do
            echo "  $((i+1)). ${results[$i]}"
        done
        
        # グローバル配列に保存（選択用）
        SEARCH_RESULTS=("${results[@]}")
        return 0
    fi
}

select_from_list() {
    local count=${#SEARCH_RESULTS[@]}
    
    while true; do
        read -p "保存先を選択 (1-$count): " choice
        
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "$count" ]; then
            SELECTED_DIR="${SEARCH_RESULTS[$((choice-1))]}"
            return 0
        else
            print_error "無効な選択です。1-${count}の数字を入力してください"
        fi
    done
}

# =====================================
# 結果保存
# =====================================

save_results() {
    print_section "結果保存"
    
    read -p "結果を保存しますか？ (y/n): " save_choice
    
    if [[ "$save_choice" != "y" && "$save_choice" != "Y" ]]; then
        print_info "結果を保存せずに終了します"
        return 0
    fi
    
    # 最新の結果ファイルを検索（サブディレクトリ含む）
    local result_file=$(find "$PROJECT_ROOT/src/analysis/experiments/2025/10/10/results" -type f -name 'batch_experiment_*.json' -print0 2>/dev/null | xargs -0 ls -t 2>/dev/null | head -1)
    
    if [[ -z "$result_file" ]]; then
        print_error "結果ファイルが見つかりません"
        return 1
    fi
    
    print_success "結果ファイル: $(basename $result_file)"
    
    # ディレクトリ検索ループ
    while true; do
        echo ""
        read -p "保存先ディレクトリ名を入力: " dir_name
        
        if [[ -z "$dir_name" ]]; then
            print_error "ディレクトリ名を入力してください"
            continue
        fi
        
        if search_directory "$dir_name"; then
            select_from_list
            break
        elif [ $? -eq 2 ]; then
            # 10件以上ヒット、再検索
            continue
        else
            # 0件ヒット
            echo ""
            read -p "新しいディレクトリを作成しますか？ (y/n): " create_new
            if [[ "$create_new" == "y" || "$create_new" == "Y" ]]; then
                read -p "作成するパス (プロジェクトルートからの相対パス): " new_path
                SELECTED_DIR="$new_path"
                mkdir -p "$PROJECT_ROOT/$new_path"
                print_success "ディレクトリを作成しました: $new_path"
                break
            fi
        fi
    done
    
    # ファイルコピー
    local dest_dir="$PROJECT_ROOT/$SELECTED_DIR"
    local dest_file="$dest_dir/$(basename $result_file)"
    
    mkdir -p "$dest_dir"
    if cp "$result_file" "$dest_file"; then
        print_success "結果を保存しました: $dest_file"
        
        # 結果サマリーを表示
        echo ""
        print_info "結果サマリー:"
        python - "$dest_file" <<'PY'
import json,sys
path = sys.argv[1] if len(sys.argv) > 1 else None
if not path:
    raise SystemExit(0)
with open(path,'r',encoding='utf-8') as f:
    data = json.load(f)
meta = data.get('experiment_meta',{})
print(f"  総実験数: {meta.get('total_experiments',0)}")
print(f"  成功: {meta.get('successful_experiments',0)}")
print(f"  タイムスタンプ: {meta.get('timestamp','')}")
PY
    else
        print_error "ファイルのコピーに失敗しました"
        return 1
    fi
}

# =====================================
# メインメニュー
# =====================================

main_menu() {
    clear
    print_header "対話型実験実行システム"
    
    # 環境チェック
    check_environment
    
    # 前回の設定読み込み
    if load_previous_config; then
        if confirm_settings; then
            run_experiment
            save_results
            return 0
        fi
    fi
    
    # 新規設定
    select_dataset
    select_aspects
    input_group_size
    select_split_type
    # 説明CSV選択（任意）
    select_description_csv || true
    
    # 確認と実行
    if confirm_settings; then
        run_experiment
        save_results
    else
        print_warning "実験をキャンセルしました"
        return 1
    fi
}

# =====================================
# エントリーポイント
# =====================================

# 色設定
setup_colors

# メイン実行
main_menu

# クリーンアップ
if [[ -f "$TEMP_RESULT_FILE" ]]; then
    rm -f "$TEMP_RESULT_FILE"
fi

print_header "実験システム終了"
