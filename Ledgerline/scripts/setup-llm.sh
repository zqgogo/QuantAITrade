#!/usr/bin/env bash
set -euo pipefail

LEDGERLINE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG_FILE="$LEDGERLINE_ROOT/config/llm.config.json"
DEMO_FILE="$LEDGERLINE_ROOT/config/llm.config.demo.json"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

usage() {
    cat <<EOF
用法: $(basename "$0") <provider> [api_key] [model]

配置 Ledgerline LLM 提供商。首次使用需从 demo 复制配置文件。

提供商:
  zhipu     智谱 AI (glm-4.7-flash / glm-4-plus)
  openai    OpenAI (gpt-5.5-mini / gpt-5.5)
  ollama    本地 Ollama (qwen3:8b / qwen2.5:7b) - 需本地安装
  mock      模拟模式（无需 API Key）

示例:
  $(basename "$0") zhipu sk-xxxxxxxxxxxxxxxx
  $(basename "$0") zhipu sk-xxxxxxxxxxxxxxxx glm-4-plus
  $(basename "$0") openai sk-xxxxxxxxxxxxxxx
  $(basename "$0") mock

提示: 配置文件 $CONFIG_FILE 已在 .gitignore 中，不会被提交。
EOF
}

select_provider() {
    echo -e "${CYAN}请选择 LLM 提供商:${NC}"
    echo "  1) zhipu   - 智谱 AI"
    echo "  2) openai  - OpenAI"
    echo "  3) ollama  - 本地 Ollama"
    echo "  4) mock    - 模拟模式"
    read -rp "请输入 [1-4]: " choice
    case $choice in
        1) echo "zhipu" ;;
        2) echo "openai" ;;
        3) echo "ollama" ;;
        4) echo "mock" ;;
        *) echo "" ;;
    esac
}

select_model() {
    local provider=$1
    echo -e "${CYAN}可用模型:${NC}"
    case $provider in
        zhipu)
            echo "  1) glm-4.7-flash  (默认，快速)"
            echo "  2) glm-4-plus     (更强)"
            read -rp "请选择 [1-2，默认1]: " choice
            case $choice in 2) echo "glm-4-plus" ;; *) echo "glm-4.7-flash" ;; esac
            ;;
        openai)
            echo "  1) gpt-5.5-mini   (默认)"
            echo "  2) gpt-5.5"
            read -rp "请选择 [1-2，默认1]: " choice
            case $choice in 2) echo "gpt-5.5" ;; *) echo "gpt-5.5-mini" ;; esac
            ;;
        ollama)
            echo "  1) qwen3:8b       (默认)"
            echo "  2) qwen2.5:7b"
            read -rp "请选择 [1-2，默认1]: " choice
            case $choice in 2) echo "qwen2.5:7b" ;; *) echo "qwen3:8b" ;; esac
            ;;
        *) echo "" ;;
    esac
}

if [[ $# -gt 0 && "$1" == "-h" || "$1" == "--help" ]]; then
    usage
    exit 0
fi

if [[ $# -ge 1 ]]; then
    PROVIDER=$1
else
    PROVIDER=$(select_provider)
    if [[ -z "$PROVIDER" ]]; then
        echo -e "${RED}无效选择${NC}"
        exit 1
    fi
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo -e "${YELLOW}配置文件不存在，从 demo 复制...${NC}"
    cp "$DEMO_FILE" "$CONFIG_FILE"
fi

if [[ "$PROVIDER" != "mock" ]]; then
    if [[ $# -ge 2 ]]; then
        API_KEY=$2
    else
        read -rp "请输入 ${PROVIDER} API Key: " API_KEY
    fi
    if [[ -z "$API_KEY" ]]; then
        echo -e "${RED}API Key 不能为空${NC}"
        exit 1
    fi
fi

if [[ $# -ge 3 ]]; then
    MODEL=$3
elif [[ "$PROVIDER" != "mock" ]]; then
    MODEL=$(select_model "$PROVIDER")
fi

echo -e "${CYAN}正在配置...${NC}"

python3 - "$CONFIG_FILE" "$PROVIDER" "${API_KEY:-}" "${MODEL:-}" <<'PYEOF'
import json, sys

config_path, provider, api_key, model = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

with open(config_path, "r") as f:
    config = json.load(f)

if provider not in config["providers"]:
    print(f"Error: provider '{provider}' not found in config")
    sys.exit(1)

config["active_provider"] = provider

if api_key:
    config["providers"][provider]["api_key"] = api_key

if model:
    config["providers"][provider]["default_model"] = model

with open(config_path, "w") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"OK: active_provider={provider}")
if model:
    print(f"OK: default_model={model}")
if api_key:
    masked = api_key[:4] + "****" + api_key[-4:] if len(api_key) > 8 else "****"
    print(f"OK: api_key={masked}")
PYEOF

echo -e "${GREEN}配置完成!${NC}"
echo -e "  配置文件: ${CYAN}$CONFIG_FILE${NC}"
echo -e "  已在 .gitignore 中，不会被提交"
echo ""
echo -e "启动服务: ${YELLOW}./scripts/dev.sh${NC}"
