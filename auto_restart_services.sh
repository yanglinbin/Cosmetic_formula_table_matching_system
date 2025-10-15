#!/bin/bash

# ===============================================================================
# 化妆品配方匹配系统 - 自动重启服务脚本
# 
# 描述: 智能检测并重启相关服务，包含健康检查和错误处理
# 作者: 系统管理员
# 版本: v2.0
# 最后更新: $(date +"%Y-%m-%d")
# ===============================================================================

# 配置参数
PROJECT_PATH="/opt/cosmetic_formula_system"
LOG_FILE="/var/log/cosmetic_formula_restart.log"
BACKUP_SUFFIX=$(date +"%Y%m%d_%H%M%S")

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 日志函数
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

info() { log "INFO" "${BLUE}$*${NC}"; }
warn() { log "WARN" "${YELLOW}$*${NC}"; }
error() { log "ERROR" "${RED}$*${NC}"; }
success() { log "SUCCESS" "${GREEN}$*${NC}"; }

# 显示帮助信息
show_help() {
    cat << EOF
${WHITE}化妆品配方匹配系统 - 服务重启脚本${NC}

${CYAN}使用方法:${NC}
  $0 [选项] [模式]

${CYAN}重启模式:${NC}
  full        完全重启所有服务 (MySQL + 应用 + Nginx) [默认]
  app         只重启应用服务 (cosmetic-formula)
  web         只重启Web服务 (Nginx)
  db          只重启数据库服务 (MySQL)
  graceful    优雅重启 (逐步重启，等待连接结束)

${CYAN}选项:${NC}
  -h, --help     显示帮助信息
  -v, --verbose  详细输出模式
  -f, --force    强制重启 (跳过健康检查)
  -b, --backup   重启前备份配置文件
  -c, --check    仅检查服务状态，不重启
  -t, --test     测试模式 (显示将要执行的操作)

${CYAN}示例:${NC}
  $0                    # 完全重启所有服务
  $0 app                # 只重启应用服务
  $0 full --backup      # 完全重启并备份配置
  $0 --check            # 检查所有服务状态
  $0 graceful -v        # 优雅重启，详细输出

${CYAN}日志文件:${NC} $LOG_FILE
EOF
}

# 检查是否以root权限运行
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "此脚本需要root权限运行，请使用 sudo"
        exit 1
    fi
}

# 检查服务状态
check_service_status() {
    local service=$1
    local status
    
    if systemctl is-active --quiet "$service"; then
        status="${GREEN}运行中${NC}"
        return 0
    else
        status="${RED}已停止${NC}"
        return 1
    fi
}

# 检查端口监听状态
check_port() {
    local port=$1
    local service_name=$2
    
    if netstat -tlnp 2>/dev/null | grep -q ":${port} "; then
        info "${service_name} 端口 ${port} 正常监听"
        return 0
    else
        warn "${service_name} 端口 ${port} 未监听"
        return 1
    fi
}

# 等待服务启动
wait_for_service() {
    local service=$1
    local timeout=${2:-30}
    local count=0
    
    info "等待 ${service} 服务启动..."
    
    while [ $count -lt $timeout ]; do
        if systemctl is-active --quiet "$service"; then
            success "${service} 服务已启动"
            return 0
        fi
        sleep 2
        count=$((count + 2))
        echo -n "."
    done
    
    echo
    error "${service} 服务启动超时 (${timeout}秒)"
    return 1
}

# 等待端口可用
wait_for_port() {
    local port=$1
    local timeout=${2:-30}
    local count=0
    
    info "等待端口 ${port} 可用..."
    
    while [ $count -lt $timeout ]; do
        if netstat -tlnp 2>/dev/null | grep -q ":${port} "; then
            success "端口 ${port} 已可用"
            return 0
        fi
        sleep 2
        count=$((count + 2))
        echo -n "."
    done
    
    echo
    error "端口 ${port} 启动超时 (${timeout}秒)"
    return 1
}

# 健康检查
health_check() {
    local failed=0
    
    info "执行服务健康检查..."
    
    # 检查服务状态
    for service in mysql cosmetic-formula nginx; do
        if ! check_service_status "$service" > /dev/null; then
            error "服务 ${service} 未运行"
            failed=1
        fi
    done
    
    # 检查端口
    check_port 3306 "MySQL" || failed=1
    check_port 8000 "Python应用" || failed=1
    check_port 8010 "Nginx" || failed=1
    
    # HTTP健康检查
    if timeout 10 curl -s http://localhost:8010 > /dev/null 2>&1; then
        success "HTTP服务响应正常"
    else
        error "HTTP服务响应异常"
        failed=1
    fi
    
    return $failed
}

# 备份配置文件
backup_configs() {
    if [[ "$BACKUP" == "true" ]]; then
        info "备份配置文件..."
        
        local backup_dir="/opt/backups/configs_${BACKUP_SUFFIX}"
        mkdir -p "$backup_dir"
        
        # 备份应用配置
        cp "${PROJECT_PATH}/system_config.ini" "${backup_dir}/" 2>/dev/null
        cp "${PROJECT_PATH}/mysql_config.ini" "${backup_dir}/" 2>/dev/null
        
        # 备份Nginx配置
        cp "/etc/nginx/sites-available/cosmetic-formula" "${backup_dir}/" 2>/dev/null
        
        # 备份系统服务配置
        cp "/etc/systemd/system/cosmetic-formula.service" "${backup_dir}/" 2>/dev/null
        
        success "配置文件已备份到: ${backup_dir}"
    fi
}

# 强制清理端口占用
force_cleanup() {
    info "清理可能的端口占用..."
    
    # 清理8000端口占用（Python应用）
    local pids=$(lsof -ti:8000 2>/dev/null)
    if [[ -n "$pids" ]]; then
        warn "强制结束占用端口8000的进程: $pids"
        echo "$pids" | xargs kill -9 2>/dev/null
        sleep 2
    fi
    
    # 清理8010端口占用（如果不是nginx）
    local nginx_pid=$(pgrep nginx | head -1)
    local port8010_pids=$(lsof -ti:8010 2>/dev/null)
    if [[ -n "$port8010_pids" ]]; then
        for pid in $port8010_pids; do
            if [[ "$pid" != "$nginx_pid" ]]; then
                warn "强制结束占用端口8010的非nginx进程: $pid"
                kill -9 "$pid" 2>/dev/null
            fi
        done
        sleep 2
    fi
}

# 重启MySQL服务
restart_mysql() {
    info "重启 MySQL 数据库服务..."
    
    if [[ "$TEST_MODE" == "true" ]]; then
        info "[测试模式] 将执行: systemctl restart mysql"
        return 0
    fi
    
    systemctl stop mysql
    sleep 3
    systemctl start mysql
    
    if wait_for_service mysql 60; then
        if wait_for_port 3306 30; then
            success "MySQL 服务重启成功"
            return 0
        fi
    fi
    
    error "MySQL 服务重启失败"
    return 1
}

# 重启应用服务
restart_app() {
    info "重启 Python 应用服务..."
    
    if [[ "$TEST_MODE" == "true" ]]; then
        info "[测试模式] 将执行: systemctl restart cosmetic-formula"
        return 0
    fi
    
    systemctl stop cosmetic-formula
    
    # 如果强制模式，清理端口占用
    if [[ "$FORCE" == "true" ]]; then
        force_cleanup
    fi
    
    sleep 5
    systemctl start cosmetic-formula
    
    if wait_for_service cosmetic-formula 60; then
        if wait_for_port 8000 45; then
            success "Python应用服务重启成功"
            return 0
        fi
    fi
    
    error "Python应用服务重启失败"
    return 1
}

# 重启Nginx服务
restart_nginx() {
    info "重启 Nginx Web服务..."
    
    if [[ "$TEST_MODE" == "true" ]]; then
        info "[测试模式] 将执行: systemctl restart nginx"
        return 0
    fi
    
    # 测试Nginx配置
    if ! nginx -t > /dev/null 2>&1; then
        error "Nginx配置文件语法错误，取消重启"
        return 1
    fi
    
    systemctl stop nginx
    sleep 3
    systemctl start nginx
    
    if wait_for_service nginx 30; then
        if wait_for_port 8010 20; then
            success "Nginx服务重启成功"
            return 0
        fi
    fi
    
    error "Nginx服务重启失败"
    return 1
}

# 优雅重启
graceful_restart() {
    info "执行优雅重启..."
    
    # 获取当前连接数
    local connections=$(netstat -ant | grep :8010 | wc -l)
    info "当前HTTP连接数: $connections"
    
    if [[ $connections -gt 0 ]]; then
        warn "等待现有连接结束 (最多等待60秒)..."
        local count=0
        while [[ $connections -gt 0 && $count -lt 30 ]]; do
            sleep 2
            connections=$(netstat -ant | grep :8010 | wc -l)
            count=$((count + 1))
            echo -n "."
        done
        echo
    fi
    
    # 执行重启
    restart_full
}

# 完全重启所有服务
restart_full() {
    info "开始完全重启所有服务..."
    local failed=0
    
    backup_configs
    
    # 按顺序重启: MySQL -> 应用 -> Nginx
    restart_mysql || failed=1
    sleep 3
    restart_app || failed=1
    sleep 3
    restart_nginx || failed=1
    
    if [[ $failed -eq 0 ]]; then
        success "所有服务重启完成"
        
        # 执行健康检查
        if [[ "$FORCE" != "true" ]]; then
            sleep 5
            if health_check; then
                success "健康检查通过"
            else
                warn "健康检查发现问题，请查看详细日志"
            fi
        fi
    else
        error "部分服务重启失败"
        return 1
    fi
}

# 检查所有服务状态
check_all_services() {
    info "检查所有服务状态..."
    
    echo
    printf "${WHITE}%-20s %-15s %-10s %-15s${NC}\n" "服务名称" "systemd状态" "端口" "端口状态"
    echo "=================================================================="
    
    # MySQL
    if check_service_status mysql > /dev/null; then
        mysql_status="${GREEN}运行中${NC}"
    else
        mysql_status="${RED}已停止${NC}"
    fi
    
    if check_port 3306 "MySQL" > /dev/null 2>&1; then
        mysql_port="${GREEN}监听${NC}"
    else
        mysql_port="${RED}未监听${NC}"
    fi
    
    printf "%-20s %-24s %-10s %-24s\n" "MySQL" "$mysql_status" "3306" "$mysql_port"
    
    # Python应用
    if check_service_status cosmetic-formula > /dev/null; then
        app_status="${GREEN}运行中${NC}"
    else
        app_status="${RED}已停止${NC}"
    fi
    
    if check_port 8000 "应用" > /dev/null 2>&1; then
        app_port="${GREEN}监听${NC}"
    else
        app_port="${RED}未监听${NC}"
    fi
    
    printf "%-20s %-24s %-10s %-24s\n" "Python应用" "$app_status" "8000" "$app_port"
    
    # Nginx
    if check_service_status nginx > /dev/null; then
        nginx_status="${GREEN}运行中${NC}"
    else
        nginx_status="${RED}已停止${NC}"
    fi
    
    if check_port 8010 "Nginx" > /dev/null 2>&1; then
        nginx_port="${GREEN}监听${NC}"
    else
        nginx_port="${RED}未监听${NC}"
    fi
    
    printf "%-20s %-24s %-10s %-24s\n" "Nginx" "$nginx_status" "8010" "$nginx_port"
    
    echo
    
    # 系统资源使用情况
    info "系统资源使用情况:"
    echo "内存使用: $(free -h | awk '/^Mem:/ {print $3 "/" $2 " (" int($3/$2*100) "%)"}')"
    echo "磁盘使用: $(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 ")"}')"
    echo "系统负载: $(uptime | awk -F'load average:' '{print $2}' | sed 's/^[ \t]*//')"
    
    # HTTP连接测试
    echo
    info "HTTP连接测试:"
    if timeout 5 curl -s -o /dev/null -w "HTTP状态码: %{http_code}, 响应时间: %{time_total}s\n" http://localhost:8010; then
        success "HTTP服务正常"
    else
        error "HTTP服务异常"
    fi
}

# 发送通知（可扩展邮件、短信等）
send_notification() {
    local status=$1
    local message=$2
    
    # 记录到系统日志
    logger -t "cosmetic-formula-restart" "$status: $message"
    
    # 这里可以添加其他通知方式，如邮件、Slack等
    # echo "$message" | mail -s "服务重启通知 - $status" admin@example.com
}

# 主函数
main() {
    # 默认参数
    RESTART_MODE="full"
    VERBOSE=false
    FORCE=false
    BACKUP=false
    CHECK_ONLY=false
    TEST_MODE=false
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            -b|--backup)
                BACKUP=true
                shift
                ;;
            -c|--check)
                CHECK_ONLY=true
                shift
                ;;
            -t|--test)
                TEST_MODE=true
                shift
                ;;
            full|app|web|db|graceful)
                RESTART_MODE=$1
                shift
                ;;
            *)
                error "未知参数: $1"
                echo "使用 $0 --help 查看帮助信息"
                exit 1
                ;;
        esac
    done
    
    # 检查root权限
    check_root
    
    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # 开始执行
    info "===== 化妆品配方匹配系统服务重启脚本启动 ====="
    info "执行时间: $(date)"
    info "执行模式: $RESTART_MODE"
    info "参数: VERBOSE=$VERBOSE, FORCE=$FORCE, BACKUP=$BACKUP, TEST_MODE=$TEST_MODE"
    
    # 仅检查模式
    if [[ "$CHECK_ONLY" == "true" ]]; then
        check_all_services
        exit 0
    fi
    
    # 预检查（非强制模式）
    if [[ "$FORCE" != "true" && "$TEST_MODE" != "true" ]]; then
        info "执行预检查..."
        if ! health_check; then
            warn "预检查发现问题，建议使用 --force 强制重启或先手动修复问题"
            exit 1
        fi
    fi
    
    # 执行相应的重启操作
    case $RESTART_MODE in
        full)
            restart_full
            ;;
        app)
            backup_configs
            restart_app
            ;;
        web)
            backup_configs
            restart_nginx
            ;;
        db)
            backup_configs
            restart_mysql
            ;;
        graceful)
            graceful_restart
            ;;
        *)
            error "未知的重启模式: $RESTART_MODE"
            exit 1
            ;;
    esac
    
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        success "===== 服务重启脚本执行完成 ====="
        send_notification "SUCCESS" "服务重启成功 - 模式: $RESTART_MODE"
    else
        error "===== 服务重启脚本执行失败 ====="
        send_notification "FAILED" "服务重启失败 - 模式: $RESTART_MODE"
    fi
    
    exit $exit_code
}

# 信号处理
trap 'error "脚本被中断"; exit 130' INT TERM

# 执行主函数
main "$@"
