#!/bin/bash

# ===============================================================================
# 化妆品配方匹配系统 - 快速重启脚本 (简化版)
# 
# 描述: 快速重启系统相关服务
# 使用方法: sudo ./quick_restart.sh
# ===============================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
info() { echo -e "${BLUE}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }

# 检查root权限
if [[ $EUID -ne 0 ]]; then
    error "此脚本需要root权限运行，请使用: sudo $0"
    exit 1
fi

echo "🚀 开始重启化妆品配方匹配系统服务..."
echo "======================================================"

# 1. 停止服务
info "停止所有服务..."
systemctl stop cosmetic-formula
systemctl stop nginx
sleep 3

# 2. 清理端口占用（如有必要）
info "检查并清理端口占用..."
PIDS_8000=$(lsof -ti:8000 2>/dev/null)
if [[ -n "$PIDS_8000" ]]; then
    warn "清理端口8000占用: $PIDS_8000"
    echo "$PIDS_8000" | xargs kill -9 2>/dev/null
fi

# 3. 启动MySQL（如果未运行）
if ! systemctl is-active --quiet mysql; then
    info "启动 MySQL 服务..."
    systemctl start mysql
    sleep 5
fi

# 4. 启动应用服务
info "启动 Python 应用服务..."
systemctl start cosmetic-formula
sleep 10

# 5. 启动Nginx
info "启动 Nginx 服务..."
systemctl start nginx
sleep 5

# 6. 检查服务状态
echo
info "检查服务状态..."
echo "======================================================"

services=("mysql" "cosmetic-formula" "nginx")
all_good=true

for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service"; then
        success "$service: 运行中"
    else
        error "$service: 未运行"
        all_good=false
    fi
done

# 7. 检查端口监听
echo
info "检查端口监听状态..."
echo "======================================================"

check_port() {
    local port=$1
    local name=$2
    if netstat -tlnp 2>/dev/null | grep -q ":${port} "; then
        success "$name (端口 $port): 正常监听"
    else
        warn "$name (端口 $port): 未监听"
        all_good=false
    fi
}

check_port 3306 "MySQL"
check_port 8000 "Python应用"
check_port 8010 "Nginx"

# 8. HTTP连接测试
echo
info "测试HTTP连接..."
if timeout 10 curl -s http://localhost:8010 > /dev/null 2>&1; then
    success "HTTP服务: 响应正常"
else
    warn "HTTP服务: 响应异常"
    all_good=false
fi

# 9. 显示结果
echo
echo "======================================================"
if $all_good; then
    success "🎉 所有服务重启完成，系统运行正常！"
    echo
    info "访问地址: http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_SERVER_IP'):8010"
    info "管理账号: admin / yanglinbin0106"
else
    warn "⚠️ 服务重启完成，但发现一些问题"
    echo
    info "请检查详细日志: sudo journalctl -u cosmetic-formula -n 50"
    info "或使用完整脚本: sudo ./auto_restart_services.sh --check"
fi

echo
info "如需查看实时日志: sudo journalctl -u cosmetic-formula -f"
echo "======================================================"
