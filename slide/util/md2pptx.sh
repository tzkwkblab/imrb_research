#!/bin/bash

# slideフォルダ内のmdファイルを自動で探して、
# 「どのmdファイルをスライドにしますか？」と聞いて
# 選択したmdファイルをpptxに変換する(名前は元のmdファイル名と同一にする)

# スクリプトの実行場所を取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SLIDE_DIR="$(dirname "$SCRIPT_DIR")"

echo "slideフォルダ内のMarkdownファイルを検索中..."

# slideフォルダ内のmdファイルを再帰的に検索
MD_FILES=()
while IFS= read -r -d '' file; do
    MD_FILES+=("$file")
done < <(find "$SLIDE_DIR" -name "*.md" -type f -print0)

# mdファイルが見つからない場合
if [ ${#MD_FILES[@]} -eq 0 ]; then
    echo "ERROR: slideフォルダ内にMarkdownファイルが見つかりません。"
    exit 1
fi

echo "見つかったMarkdownファイル:"
echo

# ファイル一覧を表示
for i in "${!MD_FILES[@]}"; do
    # 相対パスで表示
    rel_path="${MD_FILES[$i]#$SLIDE_DIR/}"
    echo "  $((i+1)). $rel_path"
done

echo
echo -n "変換するファイルの番号を選択してください (1-${#MD_FILES[@]}): "
read -r selection

# 入力値の検証
if ! [[ "$selection" =~ ^[0-9]+$ ]] || [ "$selection" -lt 1 ] || [ "$selection" -gt ${#MD_FILES[@]} ]; then
    echo "ERROR: 無効な選択です。1から${#MD_FILES[@]}の間で選択してください。"
    exit 1
fi

# 選択されたファイル
selected_file="${MD_FILES[$((selection-1))]}"
selected_dir="$(dirname "$selected_file")"
selected_name="$(basename "$selected_file" .md)"

echo
echo "選択されたファイル: ${selected_file#$SLIDE_DIR/}"
echo "出力ディレクトリ: ${selected_dir#$SLIDE_DIR/}"

# 変換オプションを選択
echo
echo "変換オプションを選択してください:"
echo "  1. 通常のPowerPoint形式 (推奨)"
echo "  2. 編集可能なPowerPoint形式 (実験的、LibreOffice必要)"
echo -n "選択 (1-2): "
read -r option

case $option in
    1)
        output_file="$selected_dir/${selected_name}.pptx"
        echo
        echo "通常のPowerPoint形式に変換中..."
        npx @marp-team/marp-cli "$selected_file" --pptx -o "$output_file"
        ;;
    2)
        output_file="$selected_dir/${selected_name}_editable.pptx"
        echo
        echo "編集可能なPowerPoint形式に変換中..."
        npx @marp-team/marp-cli "$selected_file" --pptx-editable -o "$output_file"
        ;;
    *)
        echo "ERROR: 無効な選択です。1または2を選択してください。"
        exit 1
        ;;
esac

# 変換結果の確認
if [ $? -eq 0 ] && [ -f "$output_file" ]; then
    file_size=$(ls -lh "$output_file" | awk '{print $5}')
    echo
    echo "変換完了！"
    echo "出力ファイル: ${output_file#$SLIDE_DIR/}"
    echo "ファイルサイズ: $file_size"
    echo
    echo "Finderで生成されたファイルの場所を開いています..."
    open "$selected_dir"
else
    echo
    echo "ERROR: 変換に失敗しました。"
    echo "トラブルシューティング:"
    echo "   - Marp CLIがインストールされているか確認: npx @marp-team/marp-cli --version"
    echo "   - 編集可能形式の場合、LibreOfficeがインストールされているか確認: soffice --version"
    exit 1
fi