#!/bin/bash
# 🚀 智能部署脚本 - 自动检测和适应环境
# 使用方法: bash deploy-smart.sh [项目目录]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

echo "=========================================="
echo "  🚀 智能部署脚本 - LuckyRed"
echo "=========================================="

# 1. 检测项目目录
if [ -n "$1" ]; then
    PROJECT_DIR="$1"
elif [ -n "$LUCKYRED_DIR" ]; then
    PROJECT_DIR="$LUCKYRED_DIR"
elif [ -d "/opt/luckyred" ]; then
    PROJECT_DIR="/opt/luckyred"
elif [ -d "$HOME/luckyred" ]; then
    PROJECT_DIR="$HOME/luckyred"
else
    log_error "无法自动检测项目目录"
    echo "请使用以下方式之一："
    echo "  1. 传递目录参数: bash deploy-smart.sh /path/to/project"
    echo "  2. 设置环境变量: export LUCKYRED_DIR=/path/to/project"
    echo "  3. 在常见位置创建项目: /opt/luckyred 或 ~/luckyred"
    exit 1
fi

log_info "使用项目目录: $PROJECT_DIR"

if [ ! -d "$PROJECT_DIR" ]; then
    log_error "项目目录不存在: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR" || {
    log_error "无法进入项目目录: $PROJECT_DIR"
    exit 1
}

# 2. 检查必要的工具
log_step "检查必要的工具..."
MISSING_TOOLS=()

command -v git >/dev/null 2>&1 || MISSING_TOOLS+=("git")
command -v python3 >/dev/null 2>&1 || MISSING_TOOLS+=("python3")
command -v npm >/dev/null 2>&1 || MISSING_TOOLS+=("npm")

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    log_error "缺少必要的工具: ${MISSING_TOOLS[*]}"
    echo "请先安装这些工具："
    echo "  Ubuntu/Debian: sudo apt install git python3 python3-pip nodejs npm"
    echo "  CentOS/RHEL: sudo yum install git python3 python3-pip nodejs npm"
    exit 1
fi

log_info "所有必要工具已安装"

# 3. 检查 Git 仓库
log_step "检查 Git 仓库..."
if [ ! -d ".git" ]; then
    log_warn "当前目录不是 Git 仓库"
    read -p "是否要初始化 Git 仓库? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git init
        log_warn "请手动添加远程仓库: git remote add origin <url>"
    else
        log_warn "跳过 Git 操作，继续部署..."
    fi
else
    # 检查远程仓库
    if git remote -v | grep -q "origin"; then
        log_info "Git 仓库配置正常"
    else
        log_warn "未配置远程仓库，跳过 git pull"
    fi
fi

# 4. 拉取最新代码（如果配置了远程仓库）
if [ -d ".git" ] && git remote -v | grep -q "origin"; then
    log_step "拉取最新代码..."
    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "master")
    log_info "当前分支: $CURRENT_BRANCH"
    
    # 尝试拉取，失败也不退出
    if git pull origin "$CURRENT_BRANCH" 2>/dev/null; then
        log_info "代码更新成功"
    else
        log_warn "Git pull 失败，继续使用本地代码"
    fi
fi

# 5. 检查并创建虚拟环境（API）
log_step "检查 API 虚拟环境..."
if [ ! -d "api/.venv" ]; then
    log_warn "API 虚拟环境不存在，正在创建..."
    cd api
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    deactivate
    cd ..
    log_info "API 虚拟环境创建完成"
else
    log_info "API 虚拟环境已存在"
fi

# 6. 安装 API 依赖
log_step "安装 API 依赖..."
cd api
if [ -d ".venv" ]; then
    source .venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    deactivate
    log_info "API 依赖安装完成"
else
    log_error "API 虚拟环境不存在"
    exit 1
fi
cd ..

# 7. 检查并创建虚拟环境（Bot）
log_step "检查 Bot 虚拟环境..."
if [ ! -d "bot/.venv" ]; then
    log_warn "Bot 虚拟环境不存在，正在创建..."
    cd bot
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    deactivate
    cd ..
    log_info "Bot 虚拟环境创建完成"
else
    log_info "Bot 虚拟环境已存在"
fi

# 8. 安装 Bot 依赖
log_step "安装 Bot 依赖..."
cd bot
if [ -d ".venv" ]; then
    source .venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    deactivate
    log_info "Bot 依赖安装完成"
else
    log_error "Bot 虚拟环境不存在"
    exit 1
fi
cd ..

# 9. 构建前端
log_step "构建前端..."
if [ ! -f "frontend/package.json" ]; then
    log_error "frontend/package.json 不存在"
    exit 1
fi

cd frontend
npm install --silent
npm run build
log_info "前端构建完成"
cd ..

# 10. 检查 systemctl 服务
log_step "检查系统服务..."

# 检测服务名称
API_SERVICE=""
BOT_SERVICE=""

# 尝试常见的服务名称
for service in luckyred-api api-luckyred luckyred-api.service; do
    if systemctl list-units --all --type=service | grep -q "$service"; then
        API_SERVICE="$service"
        break
    fi
done

for service in luckyred-bot bot-luckyred luckyred-bot.service; do
    if systemctl list-units --all --type=service | grep -q "$service"; then
        BOT_SERVICE="$service"
        break
    fi
done

# 11. 重启服务（需要 root 权限）
log_step "重启服务..."

if [ "$EUID" -eq 0 ]; then
    # 有 root 权限
    if [ -n "$API_SERVICE" ]; then
        systemctl restart "$API_SERVICE" && log_info "API 服务已重启" || log_warn "API 服务重启失败"
    else
        log_warn "未找到 API 服务，跳过重启"
    fi
    
    if [ -n "$BOT_SERVICE" ]; then
        systemctl restart "$BOT_SERVICE" && log_info "Bot 服务已重启" || log_warn "Bot 服务重启失败"
    else
        log_warn "未找到 Bot 服务，跳过重启"
    fi
    
    if systemctl is-active --quiet nginx 2>/dev/null; then
        systemctl reload nginx && log_info "Nginx 已重新加载" || log_warn "Nginx 重新加载失败"
    fi
else
    # 没有 root 权限，提示用户
    log_warn "当前用户没有 root 权限，无法重启服务"
    echo "请手动执行以下命令："
    if [ -n "$API_SERVICE" ]; then
        echo "  sudo systemctl restart $API_SERVICE"
    fi
    if [ -n "$BOT_SERVICE" ]; then
        echo "  sudo systemctl restart $BOT_SERVICE"
    fi
    echo "  sudo systemctl reload nginx"
fi

# 12. 检查服务状态
log_step "检查服务状态..."
if [ "$EUID" -eq 0 ]; then
    if [ -n "$API_SERVICE" ]; then
        echo ""
        echo "--- API 服务状态 ---"
        systemctl status "$API_SERVICE" --no-pager | head -5 || true
    fi
    
    if [ -n "$BOT_SERVICE" ]; then
        echo ""
        echo "--- Bot 服务状态 ---"
        systemctl status "$BOT_SERVICE" --no-pager | head -5 || true
    fi
fi

echo ""
echo "=========================================="
echo -e "${GREEN}  ✅ 部署完成！${NC}"
echo "=========================================="
echo ""
echo "📝 查看日志："
if [ -n "$API_SERVICE" ]; then
    echo "   API: sudo journalctl -u $API_SERVICE -f"
fi
if [ -n "$BOT_SERVICE" ]; then
    echo "   Bot: sudo journalctl -u $BOT_SERVICE -f"
fi
echo ""

