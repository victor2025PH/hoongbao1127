#!/bin/bash
# 📥 Pull from GitHub and Deploy
# Usage: bash scripts/sh/pull-and-deploy.sh [project_dir]

set -e

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

echo "=========================================="
echo -e "${CYAN}  📥 Pull from GitHub and Deploy${NC}"
echo "=========================================="
echo ""

# 1. Detect project directory
if [ -n "$1" ]; then
    PROJECT_DIR="$1"
elif [ -n "$LUCKYRED_DIR" ]; then
    PROJECT_DIR="$LUCKYRED_DIR"
elif [ -d "/opt/luckyred" ]; then
    PROJECT_DIR="/opt/luckyred"
elif [ -d "$HOME/luckyred" ]; then
    PROJECT_DIR="$HOME/luckyred"
else
    log_error "Cannot auto-detect project directory"
    echo "Please use one of the following:"
    echo "  1. Pass directory: bash scripts/sh/pull-and-deploy.sh /path/to/project"
    echo "  2. Set env var: export LUCKYRED_DIR=/path/to/project"
    exit 1
fi

log_info "Using project directory: $PROJECT_DIR"

if [ ! -d "$PROJECT_DIR" ]; then
    log_error "Project directory does not exist: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR" || {
    log_error "Cannot enter project directory: $PROJECT_DIR"
    exit 1
}

# 2. Check Git repository
log_step "Checking Git repository..."
if [ ! -d ".git" ]; then
    log_error "Current directory is not a Git repository"
    echo "Please clone the repository first:"
    echo "  git clone https://github.com/victor2025PH/hoongbao1127.git $PROJECT_DIR"
    exit 1
fi

# Check remote repository
if ! git remote -v | grep -q "origin"; then
    log_error "Remote repository not configured"
    echo "Please add remote repository:"
    echo "  git remote add origin https://github.com/victor2025PH/hoongbao1127.git"
    exit 1
fi

# 3. Pull latest code
log_step "Pulling latest code..."
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "master")
log_info "Current branch: $CURRENT_BRANCH"

# Check for local changes (more comprehensive check)
HAS_LOCAL_CHANGES=false
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    HAS_LOCAL_CHANGES=true
elif ! git diff-files --quiet 2>/dev/null; then
    HAS_LOCAL_CHANGES=true
fi

# Save local changes if they exist
if [ "$HAS_LOCAL_CHANGES" = true ]; then
    log_warn "Uncommitted local changes detected"
    echo "Files with local changes:"
    git status --short | head -10 || true
    log_warn "Stashing local changes to allow pull..."
    git stash save "Auto-stashed before pull at $(date '+%Y-%m-%d %H:%M:%S')" || {
        log_error "Failed to stash local changes"
        echo "Please manually commit or stash your changes:"
        echo "  git stash"
        echo "  or"
        echo "  git commit -am 'Local changes'"
        exit 1
    }
    log_info "Local changes stashed successfully"
fi

# Pull code with retry logic
PULL_ATTEMPTS=0
MAX_PULL_ATTEMPTS=2

while [ $PULL_ATTEMPTS -lt $MAX_PULL_ATTEMPTS ]; do
    if git pull origin "$CURRENT_BRANCH" 2>&1; then
        log_info "Code pulled successfully"
        break
    else
        PULL_ATTEMPTS=$((PULL_ATTEMPTS + 1))
        if [ $PULL_ATTEMPTS -lt $MAX_PULL_ATTEMPTS ]; then
            log_warn "Pull failed, attempting to resolve conflicts..."
            # Try to stash any remaining changes
            git stash save "Auto-stashed during pull retry at $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null || true
            # Reset to remote state if needed
            log_warn "Resetting to match remote branch..."
            git fetch origin "$CURRENT_BRANCH"
            git reset --hard "origin/$CURRENT_BRANCH" || {
                log_error "Failed to reset to remote branch"
                exit 1
            }
            log_info "Reset to remote branch, pull should succeed now"
        else
            log_error "Failed to pull code after $MAX_PULL_ATTEMPTS attempts"
            echo "Please manually resolve conflicts:"
            echo "  git status"
            echo "  git stash"
            echo "  git pull origin $CURRENT_BRANCH"
            exit 1
        fi
    fi
done

# 4. Check required tools
log_step "Checking required tools..."
MISSING_TOOLS=()

command -v python3 >/dev/null 2>&1 || MISSING_TOOLS+=("python3")
command -v npm >/dev/null 2>&1 || MISSING_TOOLS+=("npm")

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    log_error "Missing required tools: ${MISSING_TOOLS[*]}"
    echo "Please install these tools first"
    exit 1
fi

# 5. Install/Update API dependencies
log_step "Installing API dependencies..."
cd api
if [ ! -d ".venv" ]; then
    log_warn "Virtual environment does not exist, creating..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
deactivate
log_info "API dependencies installed"
cd ..

# 6. Install/Update Bot dependencies
log_step "Installing Bot dependencies..."
cd bot
if [ ! -d ".venv" ]; then
    log_warn "Virtual environment does not exist, creating..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
deactivate
log_info "Bot dependencies installed"
cd ..

# 7. Build frontend
log_step "Building frontend..."
if [ ! -f "frontend/package.json" ]; then
    log_error "frontend/package.json does not exist"
    exit 1
fi

cd frontend
npm install --silent
npm run build
log_info "Frontend built successfully"
cd ..

# 8. Detect and restart services
log_step "Detecting system services..."

# Detect service names
API_SERVICE=""
BOT_SERVICE=""

# Try common service names
for service in luckyred-api api-luckyred luckyred-api.service; do
    if systemctl list-units --all --type=service 2>/dev/null | grep -q "$service"; then
        API_SERVICE="$service"
        break
    fi
done

for service in luckyred-bot bot-luckyred luckyred-bot.service; do
    if systemctl list-units --all --type=service 2>/dev/null | grep -q "$service"; then
        BOT_SERVICE="$service"
        break
    fi
done

# Restart services (requires root)
if [ "$EUID" -eq 0 ]; then
    log_step "Restarting services..."
    
    if [ -n "$API_SERVICE" ]; then
        if systemctl restart "$API_SERVICE" 2>/dev/null; then
            log_info "API service restarted: $API_SERVICE"
        else
            log_warn "Failed to restart API service: $API_SERVICE"
        fi
    else
        log_warn "API service not found"
    fi
    
    if [ -n "$BOT_SERVICE" ]; then
        if systemctl restart "$BOT_SERVICE" 2>/dev/null; then
            log_info "Bot service restarted: $BOT_SERVICE"
        else
            log_warn "Failed to restart Bot service: $BOT_SERVICE"
        fi
    else
        log_warn "Bot service not found"
    fi
    
    if systemctl is-active --quiet nginx 2>/dev/null; then
        systemctl reload nginx 2>/dev/null && log_info "Nginx reloaded" || log_warn "Failed to reload Nginx"
    fi
else
    log_warn "Current user does not have root privileges, cannot restart services"
    echo "Please manually execute:"
    if [ -n "$API_SERVICE" ]; then
        echo "  sudo systemctl restart $API_SERVICE"
    fi
    if [ -n "$BOT_SERVICE" ]; then
        echo "  sudo systemctl restart $BOT_SERVICE"
    fi
    echo "  sudo systemctl reload nginx"
fi

# 9. Check service status
if [ "$EUID" -eq 0 ]; then
    log_step "Checking service status..."
    echo ""
    if [ -n "$API_SERVICE" ]; then
        echo "--- API Service Status ---"
        systemctl status "$API_SERVICE" --no-pager | head -5 || true
        echo ""
    fi
    
    if [ -n "$BOT_SERVICE" ]; then
        echo "--- Bot Service Status ---"
        systemctl status "$BOT_SERVICE" --no-pager | head -5 || true
        echo ""
    fi
fi

echo "=========================================="
echo -e "${GREEN}  ✅ Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "📝 View logs:"
if [ -n "$API_SERVICE" ]; then
    echo "   API: sudo journalctl -u $API_SERVICE -f"
fi
if [ -n "$BOT_SERVICE" ]; then
    echo "   Bot: sudo journalctl -u $BOT_SERVICE -f"
fi
echo ""

