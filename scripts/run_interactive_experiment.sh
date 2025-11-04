#!/bin/bash

# 対話型実験実行スクリプト
# 使いやすいメニューインターフェースで実験設定と実行を行う

set -e

SILENT_MODE=0

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
USE_EXAMPLES="0"
EXAMPLES_FILE=""
MAX_EXAMPLES=""

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

choose_silent_mode() {
    print_section "サイレントモード設定"
    while true; do
        read -p "サイレント実行を有効にしますか？ (y/n, Enter=n): " answer
        if [[ -z "$answer" || "$answer" =~ ^[Nn]$ ]]; then
            SILENT_MODE=0
            print_info "サイレントモード: 無効"
            break
        elif [[ "$answer" =~ ^[Yy]$ ]]; then
            SILENT_MODE=1
            print_info "サイレントモード: 有効（ファイル保存とログ生成をスキップ）"
            break
        else
            print_warning "y か n を入力してください"
        fi
    done
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
    if [[ "$SILENT_MODE" == "1" ]]; then
        return
    fi
    # 値をクォートして安全にsource可能にする
    # 例: ASPECTS="gameplay visual"
    cat > "$CONFIG_FILE" << EOF
DATASET="$DATASET"
ASPECTS="$ASPECTS"
GROUP_SIZE="$GROUP_SIZE"
SPLIT_TYPE="$SPLIT_TYPE"
USE_ASPECT_DESCRIPTIONS="$USE_ASPECT_DESCRIPTIONS"
ASPECT_DESCRIPTIONS_FILE="$ASPECT_DESCRIPTIONS_FILE"
USE_EXAMPLES="$USE_EXAMPLES"
EXAMPLES_FILE="$EXAMPLES_FILE"
MAX_EXAMPLES="$MAX_EXAMPLES"
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
        echo "例題使用: $([[ "$USE_EXAMPLES" == "1" ]] && echo "有効" || echo "無効")"
        if [[ "$USE_EXAMPLES" == "1" ]]; then
            echo "例題ファイル: $EXAMPLES_FILE"
            if [[ -n "$MAX_EXAMPLES" ]]; then
                echo "最大例題数: $MAX_EXAMPLES"
            fi
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
# 正解アスペクト表現モード選択（単語 or センテンス）
# =====================================

choose_aspect_representation() {
    print_section "正解アスペクトの表現モード選択"

    # データセット別 公式説明CSV（内部ワークスペース優先）
    local internal_official_csv="$PROJECT_ROOT/data/analysis-workspace/aspect_descriptions/$DATASET/descriptions_official.csv"

    # 外部デフォルト（存在すればフォールバック候補：ただし編集は行わない）
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

    echo "1) 単語（説明文なし）"
    echo "2) センテンス（公式）"
    echo "3) センテンス（任意のCSVを選択）"
    echo ""

    local default_choice=2
    read -p "選択してください (1-3, Enter=${default_choice}): " choice
    if [[ -z "$choice" ]]; then choice=$default_choice; fi

    case "$choice" in
        1)
            USE_ASPECT_DESCRIPTIONS="0"
            ASPECT_DESCRIPTIONS_FILE=""
            print_success "単語比較（説明文なし）を選択しました"
            ;;
        2)
            # 内部公式CSVが最優先、無ければ外部current配下をフォールバック候補に
            if [[ -f "$internal_official_csv" ]]; then
                USE_ASPECT_DESCRIPTIONS="1"
                ASPECT_DESCRIPTIONS_FILE="$internal_official_csv"
                print_success "センテンス（公式・内部）を選択: $ASPECT_DESCRIPTIONS_FILE"
            elif [[ -f "$external_csv" ]]; then
                USE_ASPECT_DESCRIPTIONS="1"
                ASPECT_DESCRIPTIONS_FILE="$external_csv"
                print_warning "内部の公式CSVが見つかりませんでした。外部のcurrent/descriptions.csvを使用します"
                print_success "センテンス（公式・外部）を選択: $ASPECT_DESCRIPTIONS_FILE"
            else
                print_warning "公式CSVが見つかりません。任意CSVの選択に切り替えます"
                select_description_csv || true
            fi
            ;;
        3)
            select_description_csv || true
            ;;
        *)
            print_error "無効な選択です。単語比較（説明文なし）にフォールバックします"
            USE_ASPECT_DESCRIPTIONS="0"
            ASPECT_DESCRIPTIONS_FILE=""
            ;;
    esac
}

# =====================================
# 例題ファイル選択
# =====================================

select_examples_file() {
    print_section "例題（Few-shot）設定"
    read -p "例題を使用しますか？ (y/n, Enter=n): " use_ex
    if [[ -z "$use_ex" || "$use_ex" == "n" || "$use_ex" == "N" ]]; then
        USE_EXAMPLES="0"
        EXAMPLES_FILE=""
        MAX_EXAMPLES=""
        print_info "例題は使用しません"
        return 0
    fi

    USE_EXAMPLES="1"
    local ex_dir="$PROJECT_ROOT/data/analysis-workspace/contrast_examples/$DATASET"
    # retrieved_concepts の場合は Steam の例題を使用
    if [[ "$DATASET" == "retrieved_concepts" ]]; then
        ex_dir="$PROJECT_ROOT/data/analysis-workspace/contrast_examples/steam"
        print_info "retrieved_concepts 用に Steam の例題ディレクトリを使用します: $ex_dir"
    fi
    local -a files=()
    if [[ -d "$ex_dir" ]]; then
        while IFS= read -r -d '' f; do files+=("$f"); done < <(find "$ex_dir" -maxdepth 1 -type f \( -name "*.json" -o -name "*.yaml" -o -name "*.yml" \) -print0 2>/dev/null | sort -z)
    fi
    echo "0) 使用しない（0-shot）"
    local i=1
    for f in "${files[@]}"; do
        echo "$i) $(basename "$f")"
        i=$((i+1))
    done
    echo ""
    read -p "選択してください (番号, Enter=0): " idx
    if [[ -z "$idx" ]]; then idx=0; fi
    if [[ "$idx" == "0" ]]; then
        USE_EXAMPLES="0"
        EXAMPLES_FILE=""
        MAX_EXAMPLES=""
        print_info "例題は使用しません"
        return 0
    fi
    if ! [[ "$idx" =~ ^[0-9]+$ ]]; then
        print_error "無効な入力です"
        return 1
    fi
    local total=${#files[@]}
    if [[ $idx -lt 1 || $idx -gt $total ]]; then
        print_error "無効な番号です"
        return 1
    fi
    EXAMPLES_FILE="${files[$((idx-1))]}"
    print_success "例題ファイル: $(basename "$EXAMPLES_FILE")"
    read -p "最大例題数を指定しますか？ (空=全件): " MAX_EXAMPLES
    return 0
}


# =====================================
# データセット選択
# =====================================

select_dataset() {
    print_section "データセット選択"
    
    echo "1. Steam Reviews (動作確認済み)"
    echo "2. SemEval ABSA (実験的)"
    echo "3. Amazon Reviews (実験的)"
    echo "4. Retrieved Concepts (COCO captions, concept_i)"
    echo ""
    
    while true; do
        read -p "選択してください (1-4): " choice
        case $choice in
            1) DATASET="steam"; break;;
            2) DATASET="semeval"; break;;
            3) DATASET="amazon"; break;;
            4) DATASET="retrieved_concepts"; break;;
            *) print_error "無効な選択です。1-4の数字を入力してください";;
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
        retrieved_concepts)
            echo "concept_i を指定してください（0-299）。"
            echo "例: 0  /  0,1,2  /  0-9  /  0-4,10,20-25"
            while true; do
                read -p "入力: " selection
                if [[ -z "$selection" ]]; then
                    print_error "入力が空です"
                    continue
                fi
                # 解析
                IFS=',' read -ra TOKENS <<< "$selection"
                local -a selected_aspects=()
                local valid=true
                for tk in "${TOKENS[@]}"; do
                    tk=$(echo "$tk" | xargs)
                    if [[ "$tk" =~ ^[0-9]+$ ]]; then
                        num=$tk
                        if [ "$num" -ge 0 ] && [ "$num" -le 299 ]; then
                            selected_aspects+=("concept_${num}")
                        else
                            print_error "範囲外: $num (0-299)"
                            valid=false; break
                        fi
                    elif [[ "$tk" =~ ^([0-9]+)-([0-9]+)$ ]]; then
                        start=${BASH_REMATCH[1]}
                        end=${BASH_REMATCH[2]}
                        if [ "$start" -le "$end" ] && [ "$start" -ge 0 ] && [ "$end" -le 299 ]; then
                            for ((i=start;i<=end;i++)); do selected_aspects+=("concept_${i}"); done
                        else
                            print_error "無効な範囲: $tk"
                            valid=false; break
                        fi
                    else
                        print_error "無効なトークン: $tk"
                        valid=false; break
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
            return 0
            ;;
    esac
    
    echo "利用可能なアスペクト:"
    for i in "${!available_aspects[@]}"; do
        echo "$((i+1)). ${available_aspects[$i]}"
    done
    echo ""
    
    while true; do
        read -p "選択してください（カンマ区切りで複数可, 例: 1,2,3）: " selection
        
        IFS=',' read -ra SELECTED <<< "$selection"
        
        local selected_aspects=()
        local valid=true
        
        for num in "${SELECTED[@]}"; do
            num=$(echo "$num" | xargs)
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
    
    echo "1. aspect_vs_others (通常のアスペクト比較用 - 推奨)"
    echo "   対象アスペクトを含む vs 含まないレビューを比較"
    echo ""
    echo "2. binary_label (ネガポジ分類用)"
    echo "   同一アスペクト内でラベル1(ポジ) vs ラベル0(ネガ)の感情評価を比較"
    echo "   ※感情的な分類をしたい場合のみ"
    echo ""
    
    local default_type="aspect_vs_others"
    print_info "通常のアスペクト間比較には aspect_vs_others が推奨されます"
    
    while true; do
        read -p "選択してください (1-2, Enter=推奨): " choice
        
        if [[ -z "$choice" ]]; then
            SPLIT_TYPE=$default_type
            break
        fi
        
        case $choice in
            1) SPLIT_TYPE="aspect_vs_others"; break;;
            2) SPLIT_TYPE="binary_label"; break;;
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
    echo "  例題使用: $([[ "$USE_EXAMPLES" == "1" ]] && echo "有効" || echo "無効")"
    if [[ "$USE_EXAMPLES" == "1" ]]; then
        echo "  例題ファイル: $EXAMPLES_FILE"
        if [[ -n "$MAX_EXAMPLES" ]]; then
            echo "  最大例題数: $MAX_EXAMPLES"
        fi
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
    # 例題オプション
    if [[ "$USE_EXAMPLES" == "1" ]]; then
        cmd="$cmd --use-examples"
        if [[ -n "$EXAMPLES_FILE" ]]; then
            cmd="$cmd --examples-file \"$EXAMPLES_FILE\""
        fi
        if [[ -n "$MAX_EXAMPLES" ]]; then
            cmd="$cmd --max-examples $MAX_EXAMPLES"
        fi
    fi
    
    if [[ "$SILENT_MODE" == "1" ]]; then
        cmd="$cmd --silent"
    fi

    echo -e "${CYAN}実行コマンド:${NC}"
    echo "$cmd"
    echo ""
    
    RUN_TS="$(date +%Y%m%d_%H%M%S)"

    if [[ "$SILENT_MODE" == "1" ]]; then
        if eval "$cmd"; then
            print_success "実験が正常に完了しました"
        else
            print_error "実験中にエラーが発生しました"
        fi
        return 0
    fi

    CLI_TMP_LOG="/tmp/cli_run_${RUN_TS}_$$.log"
    if eval "$cmd" 2>&1 | tee "$CLI_TMP_LOG"; then
        print_success "実験が正常に完了しました"
        save_config
    else
        print_error "実験中にエラーが発生しました"
    fi

    # 実行後: 最新の結果JSONから run_dir を取得（当日の日付ディレクトリを探索）
    local results_base="$PROJECT_ROOT/src/analysis/experiments/$(date +%Y)/$(date +%m)/$(date +%d)/results"
    local latest_json=$(find "$results_base" -type f -name 'batch_experiment_*.json' -print0 2>/dev/null | xargs -0 ls -t 2>/dev/null | head -1)
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

    return 0
}

# =====================================
# （削除）手動結果保存フローは不要：パイプラインが自動保存するため

# =====================================
# メインメニュー
# =====================================

main_menu() {
    clear
    print_header "対話型実験実行システム"
    
    choose_silent_mode

    # 環境チェック
    check_environment
    
    # 前回の設定読み込み
    if load_previous_config; then
        if confirm_settings; then
            run_experiment
            return 0
        fi
    fi
    
    # 新規設定
    select_dataset
    # 表現モード（単語/センテンス）を先に決めておく
    choose_aspect_representation || true
    select_aspects
    input_group_size
    select_split_type
    # 説明CSVの個別選択は上の表現モード「3) 任意CSV選択」で実行済み
    # 例題ファイル選択（任意）
    select_examples_file || true
    
    # 確認と実行
    if confirm_settings; then
        run_experiment
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
