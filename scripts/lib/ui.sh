# shellcheck shell=bash

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
    echo -e "${GREEN}[成功] $1${NC}"
}

print_error() {
    echo -e "${RED}[エラー] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[警告] $1${NC}"
}

print_info() {
    echo -e "${CYAN}[情報] $1${NC}"
}

