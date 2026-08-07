#!/usr/bin/env bash
set -euo pipefail

LEDGERLINE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_DIR="$LEDGERLINE_ROOT/apps/api"
WEB_DIR="$LEDGERLINE_ROOT/apps/web"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

usage() {
    cat <<EOF
用法: $(basename "$0") [api|web|all]

启动 Ledgerline 开发服务:
  api    仅启动后端 API (端口 8000)
  web    仅启动前端 Web (端口 3000)
  all    同时启动后端 + 前端（默认）

停止: Ctrl+C 结束所有子进程
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

TARGET="${1:-all}"

cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止服务...${NC}"
    [[ -n "${API_PID:-}" ]] && kill $API_PID 2>/dev/null || true
    [[ -n "${WEB_PID:-}" ]] && kill $WEB_PID 2>/dev/null || true
    wait 2>/dev/null || true
    echo -e "${GREEN}已停止${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

check_deps() {
    local missing=0

    if [[ ! -f "$API_DIR/.venv/bin/activate" ]]; then
        echo -e "${RED}后端虚拟环境不存在: $API_DIR/.venv${NC}"
        echo -e "${YELLOW}请先运行: cd $API_DIR && python3 -m venv .venv && source .venv/bin/activate && pip install -e .${NC}"
        missing=1
    fi

    if [[ ! -d "$WEB_DIR/node_modules" ]]; then
        echo -e "${RED}前端依赖未安装: $WEB_DIR/node_modules${NC}"
        echo -e "${YELLOW}请先运行: cd $LEDGERLINE_ROOT && npm install${NC}"
        missing=1
    fi

    if [[ $missing -eq 1 ]]; then
        exit 1
    fi
}

start_api() {
    echo -e "${CYAN}启动后端 API...${NC}"
    cd "$API_DIR"
    source .venv/bin/activate
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    API_PID=$!
    sleep 2
    if kill -0 $API_PID 2>/dev/null; then
        echo -e "${GREEN}后端已启动: http://localhost:8000${NC}"
        echo -e "  API 文档: http://localhost:8000/docs"
    else
        echo -e "${RED}后端启动失败${NC}"
        exit 1
    fi
}

start_web() {
    echo -e "${CYAN}启动前端 Web...${NC}"
    cd "$WEB_DIR"
    npm run dev &
    WEB_PID=$!
    sleep 3
    if kill -0 $WEB_PID 2>/dev/null; then
        echo -e "${GREEN}前端已启动: http://localhost:3000${NC}"
    else
        echo -e "${YELLOW}前端可能启动中，检查输出确认端口${NC}"
    fi
}

check_deps

case $TARGET in
    api)
        start_api
        ;;
    web)
        start_web
        ;;
    all)
        start_api
        start_web
        ;;
    *)
        echo -e "${RED}未知目标: $TARGET${NC}"
        usage
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}服务就绪!${NC}"
echo -e "  后端: http://localhost:8000"
echo -e "  前端: http://localhost:3000"
echo -e "${YELLOW}Ctrl+C 停止所有服务${NC}"

wait
