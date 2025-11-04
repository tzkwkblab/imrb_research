# shellcheck shell=bash

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

select_description_csv() {
    print_section "アスペクト説明CSV選択（任意）"

    local desc_dir="$PROJECT_ROOT/data/analysis-workspace/aspect_descriptions/$DATASET"
    local -a csv_files=()

    if [[ -d "$desc_dir" ]]; then
        while IFS= read -r -d '' f; do
            csv_files+=("$f")
        done < <(find "$desc_dir" -maxdepth 1 -type f -name "*.csv" -print0 2>/dev/null | sort -z)
    fi

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

    echo "0) 説明文なし"

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
        print_success "説明文なしを選択しました"
        return 0
    fi

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

choose_aspect_representation() {
    print_section "正解アスペクトの表現モード選択"

    local internal_official_csv="$PROJECT_ROOT/data/analysis-workspace/aspect_descriptions/$DATASET/descriptions_official.csv"
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

    echo "1) 説明文なし"
    echo "2) センテンス（公式）"
    echo "3) センテンス（任意CSV）"
    echo ""

    local default_choice=2
    read -p "選択してください (1-3, Enter=${default_choice}): " choice
    if [[ -z "$choice" ]]; then choice=$default_choice; fi

    case "$choice" in
        1)
            USE_ASPECT_DESCRIPTIONS="0"
            ASPECT_DESCRIPTIONS_FILE=""
            print_success "説明文なしを選択しました"
            ;;
        2)
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
            print_error "無効な選択です。説明文なしにフォールバックします"
            USE_ASPECT_DESCRIPTIONS="0"
            ASPECT_DESCRIPTIONS_FILE=""
            ;;
    esac
}

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
            1) DATASET="steam"; break ;;
            2) DATASET="semeval"; break ;;
            3) DATASET="amazon"; break ;;
            4) DATASET="retrieved_concepts"; break ;;
            *) print_error "無効な選択です。1-4の数字を入力してください" ;;
        esac
    done

    print_success "データセット: $DATASET を選択しました"
}

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
                IFS=',' read -ra TOKENS <<< "$selection"
                local -a selected_aspects=()
                local valid=true
                for tk in "${TOKENS[@]}"; do
                    tk=$(echo "$tk" | xargs)
                    if [[ "$tk" =~ ^[0-9]+$ ]]; then
                        local num=$tk
                        if (( num >= 0 && num <= 299 )); then
                            selected_aspects+=("concept_${num}")
                        else
                            print_error "範囲外: $num (0-299)"
                            valid=false; break
                        fi
                    elif [[ "$tk" =~ ^([0-9]+)-([0-9]+)$ ]]; then
                        local start=${BASH_REMATCH[1]}
                        local end=${BASH_REMATCH[2]}
                        if (( start <= end && start >= 0 && end <= 299 )); then
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
                if $valid && [[ ${#selected_aspects[@]} -gt 0 ]]; then
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
            if [[ "$num" =~ ^[0-9]+$ ]] && (( num >= 1 && num <= ${#available_aspects[@]} )); then
                selected_aspects+=("${available_aspects[$((num-1))]}")
            else
                print_error "無効な番号: $num"
                valid=false
                break
            fi
        done
        if $valid && [[ ${#selected_aspects[@]} -gt 0 ]]; then
            ASPECTS=$(IFS=' '; echo "${selected_aspects[*]}")
            echo ""
            print_success "選択されたアスペクト: $ASPECTS"
            break
        else
            print_error "有効なアスペクトを選択してください"
        fi
    done
}

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
        elif [[ "$size" =~ ^[0-9]+$ ]] && (( size >= 1 )); then
            GROUP_SIZE=$size
            break
        else
            print_error "正の整数を入力してください"
        fi
    done

    print_success "グループサイズ: $GROUP_SIZE"
}

select_split_type() {
    print_section "分割タイプ選択"

    echo "1. aspect_vs_others (通常のアスペクト比較用 - 推奨)"
    echo "2. binary_label (ネガポジ分類用)"
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
            1) SPLIT_TYPE="aspect_vs_others"; break ;;
            2) SPLIT_TYPE="binary_label"; break ;;
            *) print_error "無効な選択です。1か2を入力してください" ;;
        esac
    done

    print_success "分割タイプ: $SPLIT_TYPE"
}

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
    if (( idx < 1 || idx > total )); then
        print_error "無効な番号です"
        return 1
    fi
    EXAMPLES_FILE="${files[$((idx-1))]}"
    print_success "例題ファイル: $(basename "$EXAMPLES_FILE")"
    read -p "最大例題数を指定しますか？ (空=全件): " MAX_EXAMPLES
    return 0
}

confirm_settings() {
    print_section "設定確認"

    echo "実験設定:"
    echo "  データセット: $DATASET"
    echo "  アスペクト: $ASPECTS"
    echo "  グループサイズ: $GROUP_SIZE"
    echo "  分割タイプ: $SPLIT_TYPE"
    if [[ "$USE_ASPECT_DESCRIPTIONS" == "1" ]]; then
        echo "  説明文比較: 有効"
        echo "  説明CSV: $ASPECT_DESCRIPTIONS_FILE"
    else
        echo "  説明文比較: 無効"
    fi
    if [[ "$USE_EXAMPLES" == "1" ]]; then
        echo "  例題使用: 有効"
        echo "  例題ファイル: $EXAMPLES_FILE"
        if [[ -n "$MAX_EXAMPLES" ]]; then
            echo "  最大例題数: $MAX_EXAMPLES"
        fi
    else
        echo "  例題使用: 無効"
    fi
    echo ""

    read -p "この設定で実験を開始しますか？ (y/n): " confirm

    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        print_warning "実験をキャンセルしました"
        return 1
    fi

    return 0
}

