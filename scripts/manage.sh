#!/bin/bash

#########################################################################
# A股短线二线龙头策略量化系统 - 管理脚本
# 项目：short_second_strategy
# 虚拟环境：sss_py311
# 版本：V2.1
# 更新：2025-01-20
#########################################################################

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 系统路径配置
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PROJECT_NAME="short_second_strategy"
VENV_NAME="sss_py311"

# 目录配置
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/.pids"
DATA_DIR="$PROJECT_ROOT/data"
VENV_DIR="$PROJECT_ROOT/$VENV_NAME"

# 如果虚拟环境在其他位置，可以修改这里
# VENV_DIR="$HOME/.virtualenvs/$VENV_NAME"

# 进程PID文件
BACKEND_PID="$PID_DIR/backend.pid"
FRONTEND_PID="$PID_DIR/frontend.pid"
CELERY_PID="$PID_DIR/celery.pid"
REDIS_PID="$PID_DIR/redis.pid"
WEBSOCKET_PID="$PID_DIR/websocket.pid"
SCHEDULER_PID="$PID_DIR/scheduler.pid"

# 端口配置
BACKEND_PORT=${BACKEND_PORT:-5000}
FRONTEND_PORT=${FRONTEND_PORT:-8080}
WEBSOCKET_PORT=${WEBSOCKET_PORT:-8081}
REDIS_PORT=${REDIS_PORT:-6379}

# 环境变量文件
ENV_FILE="$PROJECT_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
    export $(cat $ENV_FILE | grep -v '^#' | xargs)
fi

# 创建必要的目录
create_dirs() {
    mkdir -p "$LOG_DIR"
    mkdir -p "$PID_DIR"
    mkdir -p "$DATA_DIR"/{market,stocks,cache,export,backup}
    mkdir -p "$BACKEND_DIR"/{core,data,analysis,backtest,api,utils,config}
    mkdir -p "$FRONTEND_DIR"/{css,js,assets}
}

# 打印带颜色的消息
print_msg() {
    local color=$1
    local msg=$2
    echo -e "${color}${msg}${NC}"
}

# 打印标题
print_title() {
    echo -e "\n${CYAN}╔══════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║    短线二线龙头策略量化系统 V2.1    ║${NC}"
    echo -e "${CYAN}║      Project: $PROJECT_NAME      ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════╝${NC}\n"
}

# 检查Python环境
check_python() {
    # 首先尝试使用项目虚拟环境
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
        print_msg $GREEN "✓ 已激活虚拟环境: $VENV_NAME"
        PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
        print_msg $GREEN "✓ Python版本: $PYTHON_VERSION"
    else
        print_msg $YELLOW "警告：未找到虚拟环境 $VENV_NAME"
        print_msg $BLUE "尝试创建虚拟环境..."
        
        # 检查是否有Python 3.11
        if command -v python3.11 &> /dev/null; then
            python3.11 -m venv "$VENV_DIR"
            source "$VENV_DIR/bin/activate"
            pip install --upgrade pip
            print_msg $GREEN "✓ 虚拟环境创建成功"
        elif command -v python3 &> /dev/null; then
            python3 -m venv "$VENV_DIR"
            source "$VENV_DIR/bin/activate"
            pip install --upgrade pip
            print_msg $YELLOW "注意：使用默认Python3版本创建虚拟环境"
        else
            print_msg $RED "错误：未找到Python3，请先安装Python"
            exit 1
        fi
    fi
}

# 检查并安装Python依赖
check_python_deps() {
    print_msg $BLUE "检查Python依赖..."
    
    if [ ! -f "$PROJECT_ROOT/requirements.txt" ]; then
        print_msg $YELLOW "未找到requirements.txt，跳过依赖安装"
        return
    fi
    
    # 检查是否需要安装依赖
    if ! python -c "import flask" 2>/dev/null; then
        print_msg $YELLOW "检测到缺少依赖，正在安装..."
        pip install -r "$PROJECT_ROOT/requirements.txt"
        print_msg $GREEN "✓ Python依赖安装完成"
    else
        print_msg $GREEN "✓ Python依赖已满足"
    fi
}

# 检查Node.js环境
check_node() {
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v)
        print_msg $GREEN "✓ Node.js版本: $NODE_VERSION"
        
        # 检查前端依赖
        if [ -f "$FRONTEND_DIR/package.json" ] && [ ! -d "$FRONTEND_DIR/node_modules" ]; then
            print_msg $YELLOW "安装前端依赖..."
            cd "$FRONTEND_DIR"
            npm install
            cd "$PROJECT_ROOT"
            print_msg $GREEN "✓ 前端依赖安装完成"
        fi
    else
        print_msg $YELLOW "警告：未找到Node.js，前端构建功能可能受限"
    fi
}

# 检查Redis
check_redis() {
    if command -v redis-server &> /dev/null; then
        print_msg $GREEN "✓ Redis已安装"
        return 0
    else
        print_msg $YELLOW "警告：未找到Redis，缓存功能将不可用"
        print_msg $CYAN "  提示：使用 'apt install redis-server' 或 'brew install redis' 安装"
        return 1
    fi
}

# 检查MySQL/PostgreSQL
check_database() {
    local db_available=false
    
    if command -v mysql &> /dev/null; then
        print_msg $GREEN "✓ MySQL已安装"
        db_available=true
    fi
    
    if command -v psql &> /dev/null; then
        print_msg $GREEN "✓ PostgreSQL已安装"
        db_available=true
    fi
    
    if [ "$db_available" = false ]; then
        print_msg $YELLOW "警告：未检测到数据库，将使用SQLite"
    fi
}

# 完整的依赖检查
check_dependencies() {
    print_msg $BLUE "\n检查系统依赖..."
    
    check_python
    check_python_deps
    check_node
    check_redis
    check_database
    
    print_msg $GREEN "\n✓ 依赖检查完成"
}

# 初始化配置文件
init_config() {
    if [ ! -f "$ENV_FILE" ]; then
        print_msg $BLUE "创建默认配置文件..."
        cat > "$ENV_FILE" << EOF
# 短线二线龙头策略系统配置
PROJECT_NAME=$PROJECT_NAME
ENVIRONMENT=development

# 服务端口
BACKEND_PORT=$BACKEND_PORT
FRONTEND_PORT=$FRONTEND_PORT
WEBSOCKET_PORT=$WEBSOCKET_PORT
REDIS_PORT=$REDIS_PORT

# 数据库配置
DB_TYPE=sqlite
DB_HOST=localhost
DB_PORT=3306
DB_NAME=${PROJECT_NAME}_db
DB_USER=root
DB_PASSWORD=

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=$REDIS_PORT
REDIS_DB=0

# 数据源配置
DATA_SOURCE=akshare
TUSHARE_TOKEN=

# 交易配置
BROKER_TYPE=simulator
BROKER_ACCOUNT=
BROKER_PASSWORD=

# 风险控制
MAX_POSITION_SIZE=0.3
SINGLE_STOCK_LIMIT=0.1
STOP_LOSS_RATIO=0.04

# 日志级别
LOG_LEVEL=INFO

# 密钥（请修改）
SECRET_KEY=change-this-secret-key-in-production
EOF
        print_msg $GREEN "✓ 配置文件已创建: $ENV_FILE"
        print_msg $YELLOW "  请根据实际情况修改配置"
    fi
}

# 启动后端服务
start_backend() {
    print_msg $BLUE "启动后端服务..."
    
    if [ -f "$BACKEND_PID" ]; then
        PID=$(cat "$BACKEND_PID")
        if ps -p $PID > /dev/null 2>&1; then
            print_msg $YELLOW "后端服务已在运行 (PID: $PID)"
            return
        fi
    fi
    
    cd "$PROJECT_ROOT"
    source "$VENV_DIR/bin/activate"
    
    # 检查是否有app.py文件
    if [ -f "$BACKEND_DIR/app.py" ]; then
        cd "$BACKEND_DIR"
        nohup python app.py > "$LOG_DIR/backend.log" 2>&1 &
    else
        # 创建一个简单的测试服务器
        print_msg $YELLOW "未找到app.py，启动测试服务器..."
        nohup python -m flask run --host=0.0.0.0 --port=$BACKEND_PORT > "$LOG_DIR/backend.log" 2>&1 &
    fi
    
    echo $! > "$BACKEND_PID"
    sleep 2
    
    if ps -p $(cat "$BACKEND_PID") > /dev/null 2>&1; then
        print_msg $GREEN "✓ 后端服务启动成功 (PID: $(cat $BACKEND_PID))"
        print_msg $CYAN "  API地址: http://localhost:$BACKEND_PORT"
    else
        print_msg $RED "✗ 后端服务启动失败，请查看日志: $LOG_DIR/backend.log"
        rm -f "$BACKEND_PID"
        exit 1
    fi
}

# 启动前端服务
start_frontend() {
    print_msg $BLUE "启动前端服务..."
    
    if [ -f "$FRONTEND_PID" ]; then
        PID=$(cat "$FRONTEND_PID")
        if ps -p $PID > /dev/null 2>&1; then
            print_msg $YELLOW "前端服务已在运行 (PID: $PID)"
            return
        fi
    fi
    
    cd "$FRONTEND_DIR"
    
    # 检查是否有index.html
    if [ ! -f "index.html" ]; then
        print_msg $YELLOW "创建默认首页..."
        echo "<h1>短线二线龙头策略系统</h1>" > index.html
    fi
    
    # 使用Python HTTP服务器
    source "$VENV_DIR/bin/activate"
    nohup python -m http.server $FRONTEND_PORT > "$LOG_DIR/frontend.log" 2>&1 &
    echo $! > "$FRONTEND_PID"
    
    sleep 2
    
    if ps -p $(cat "$FRONTEND_PID") > /dev/null 2>&1; then
        print_msg $GREEN "✓ 前端服务启动成功 (PID: $(cat $FRONTEND_PID))"
        print_msg $CYAN "  访问地址: http://localhost:$FRONTEND_PORT"
    else
        print_msg $RED "✗ 前端服务启动失败"
        rm -f "$FRONTEND_PID"
        exit 1
    fi
}

# 启动调度器服务
start_scheduler() {
    print_msg $BLUE "启动任务调度器..."
    
    if [ -f "$SCHEDULER_PID" ]; then
        PID=$(cat "$SCHEDULER_PID")
        if ps -p $PID > /dev/null 2>&1; then
            print_msg $YELLOW "调度器已在运行 (PID: $PID)"
            return
        fi
    fi
    
    cd "$BACKEND_DIR"
    source "$VENV_DIR/bin/activate"
    
    if [ -f "scheduler.py" ]; then
        nohup python scheduler.py > "$LOG_DIR/scheduler.log" 2>&1 &
        echo $! > "$SCHEDULER_PID"
        
        sleep 2
        
        if ps -p $(cat "$SCHEDULER_PID") > /dev/null 2>&1; then
            print_msg $GREEN "✓ 调度器启动成功 (PID: $(cat $SCHEDULER_PID))"
        else
            print_msg $RED "✗ 调度器启动失败"
            rm -f "$SCHEDULER_PID"
        fi
    else
        print_msg $YELLOW "未找到scheduler.py，跳过调度器启动"
    fi
}

# 启动Celery工作进程
start_celery() {
    print_msg $BLUE "启动Celery异步任务..."
    
    if [ -f "$CELERY_PID" ]; then
        PID=$(cat "$CELERY_PID")
        if ps -p $PID > /dev/null 2>&1; then
            print_msg $YELLOW "Celery已在运行 (PID: $PID)"
            return
        fi
    fi
    
    cd "$BACKEND_DIR"
    source "$VENV_DIR/bin/activate"
    
    # 检查是否安装了Celery
    if python -c "import celery" 2>/dev/null; then
        if [ -f "celery_app.py" ] || [ -f "app.py" ]; then
            nohup celery -A app.celery worker --loglevel=info > "$LOG_DIR/celery.log" 2>&1 &
            echo $! > "$CELERY_PID"
            
            sleep 2
            
            if ps -p $(cat "$CELERY_PID") > /dev/null 2>&1; then
                print_msg $GREEN "✓ Celery启动成功 (PID: $(cat $CELERY_PID))"
            else
                print_msg $RED "✗ Celery启动失败"
                rm -f "$CELERY_PID"
            fi
        else
            print_msg $YELLOW "未找到Celery应用文件，跳过"
        fi
    else
        print_msg $YELLOW "未安装Celery，跳过"
    fi
}

# 启动Redis服务
start_redis() {
    if ! check_redis; then
        return
    fi
    
    print_msg $BLUE "启动Redis服务..."
    
    # 检查系统Redis服务
    if systemctl is-active --quiet redis || systemctl is-active --quiet redis-server; then
        print_msg $GREEN "✓ Redis服务已在系统级运行"
        return
    fi
    
    if [ -f "$REDIS_PID" ]; then
        PID=$(cat "$REDIS_PID")
        if ps -p $PID > /dev/null 2>&1; then
            print_msg $YELLOW "Redis已在运行 (PID: $PID)"
            return
        fi
    fi
    
    nohup redis-server --port $REDIS_PORT --dir "$DATA_DIR/cache" > "$LOG_DIR/redis.log" 2>&1 &
    echo $! > "$REDIS_PID"
    
    sleep 2
    
    if ps -p $(cat "$REDIS_PID") > /dev/null 2>&1; then
        print_msg $GREEN "✓ Redis启动成功 (PID: $(cat $REDIS_PID))"
    else
        print_msg $RED "✗ Redis启动失败"
        rm -f "$REDIS_PID"
    fi
}

# 停止指定服务
stop_service() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            print_msg $BLUE "停止$service_name (PID: $PID)..."
            kill -15 $PID
            
            # 等待进程优雅退出
            local count=0
            while [ $count -lt 10 ] && ps -p $PID > /dev/null 2>&1; do
                sleep 1
                count=$((count + 1))
            done
            
            # 如果进程还在，强制终止
            if ps -p $PID > /dev/null 2>&1; then
                kill -9 $PID
                sleep 1
            fi
            
            print_msg $GREEN "✓ $service_name已停止"
        else
            print_msg $YELLOW "$service_name未在运行"
        fi
        rm -f "$pid_file"
    else
        print_msg $YELLOW "$service_name未在运行"
    fi
}

# 停止所有服务
stop_all() {
    print_msg $BLUE "\n停止所有服务..."
    
    stop_service "后端服务" "$BACKEND_PID"
    stop_service "前端服务" "$FRONTEND_PID"
    stop_service "调度器" "$SCHEDULER_PID"
    stop_service "Celery" "$CELERY_PID"
    stop_service "WebSocket" "$WEBSOCKET_PID"
    stop_service "Redis" "$REDIS_PID"
    
    print_msg $GREEN "\n✓ 所有服务已停止"
}

# 重启服务
restart_all() {
    print_msg $BLUE "\n重启系统..."
    stop_all
    sleep 2
    start_all
}

# 启动所有服务
start_all() {
    print_title
    create_dirs
    init_config
    check_dependencies
    
    print_msg $PURPLE "\n═══ 开始启动系统服务 ═══\n"
    
    start_redis
    start_backend
    start_celery
    start_scheduler
    start_frontend
    
    print_msg $GREEN "\n✓ 系统启动完成！\n"
    print_msg $CYAN "╔═══════════════════════════════════════╗"
    print_msg $CYAN "║         系统访问地址                  ║"
    print_msg $CYAN "╠═══════════════════════════════════════╣"
    print_msg $CYAN "║ 主界面: http://localhost:$FRONTEND_PORT         ║"
    print_msg $CYAN "║ API文档: http://localhost:$BACKEND_PORT/api/docs ║"
    print_msg $CYAN "║ 监控面板: http://localhost:$FRONTEND_PORT/monitor ║"
    print_msg $CYAN "╚═══════════════════════════════════════╝"
}

# 查看服务状态
show_status() {
    print_title
    print_msg $PURPLE "═══ 系统服务状态 ═══\n"
    
    local running_count=0
    local total_count=6
    
    # 检查各服务状态
    services=(
        "后端服务:$BACKEND_PID"
        "前端服务:$FRONTEND_PID"
        "调度器:$SCHEDULER_PID"
        "Celery:$CELERY_PID"
        "WebSocket:$WEBSOCKET_PID"
        "Redis:$REDIS_PID"
    )
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r service_name pid_file <<< "$service_info"
        if [ -f "$pid_file" ] && ps -p $(cat "$pid_file") > /dev/null 2>&1; then
            print_msg $GREEN "✓ $service_name: 运行中 (PID: $(cat $pid_file))"
            running_count=$((running_count + 1))
        else
            print_msg $RED "✗ $service_name: 已停止"
        fi
    done
    
    # 显示汇总
    echo
    if [ $running_count -eq $total_count ]; then
        print_msg $GREEN "状态汇总: 所有服务正常运行 ($running_count/$total_count)"
    elif [ $running_count -eq 0 ]; then
        print_msg $RED "状态汇总: 所有服务已停止 ($running_count/$total_count)"
    else
        print_msg $YELLOW "状态汇总: 部分服务运行中 ($running_count/$total_count)"
    fi
    
    # 显示端口占用
    echo
    print_msg $PURPLE "═══ 端口占用情况 ═══\n"
    
    for port in $BACKEND_PORT $FRONTEND_PORT $WEBSOCKET_PORT $REDIS_PORT; do
        if lsof -i:$port > /dev/null 2>&1; then
            print_msg $GREEN "  端口 $port: 已占用"
        else
            print_msg $YELLOW "  端口 $port: 空闲"
        fi
    done
    
    # 显示资源使用
    echo
    print_msg $PURPLE "═══ 系统资源使用 ═══\n"
    
    # CPU使用率
    if command -v top &> /dev/null; then
        CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
        print_msg $CYAN "  CPU使用率: ${CPU_USAGE:-N/A}%"
    fi
    
    # 内存使用
    if command -v free &> /dev/null; then
        MEM_USAGE=$(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2}')
        MEM_INFO=$(free -h | awk 'NR==2{printf "%s/%s", $3, $2}')
        print_msg $CYAN "  内存使用: $MEM_INFO ($MEM_USAGE)"
    fi
    
    # 磁盘使用
    DISK_USAGE=$(df -h "$PROJECT_ROOT" | awk 'NR==2{print $5}')
    DISK_INFO=$(df -h "$PROJECT_ROOT" | awk 'NR==2{printf "%s/%s", $3, $2}')
    print_msg $CYAN "  磁盘使用: $DISK_INFO ($DISK_USAGE)"
}

# 查看日志
show_logs() {
    local log_type=${1:-all}
    local lines=${2:-50}
    
    case "$log_type" in
        backend|frontend|celery|websocket|redis|scheduler|system|trading|error)
            log_file="$LOG_DIR/$log_type.log"
            if [ -f "$log_file" ]; then
                print_msg $BLUE "\n═══ $log_type 日志 (最近$lines行) ═══\n"
                tail -n $lines "$log_file"
            else
                print_msg $YELLOW "日志文件不存在: $log_file"
            fi
            ;;
        all)
            print_msg $BLUE "\n═══ 所有日志文件 ═══\n"
            ls -lah "$LOG_DIR" 2>/dev/null || print_msg $YELLOW "日志目录为空"
            ;;
        *)
            print_msg $RED "未知的日志类型: $log_type"
            print_msg $CYAN "可用类型: backend, frontend, celery, scheduler, websocket, redis, system, trading, error, all"
            ;;
    esac
}

# 实时监控日志
monitor_logs() {
    local log_type=${1:-all}
    
    print_msg $BLUE "\n开始实时监控日志 (Ctrl+C退出)...\n"
    
    case "$log_type" in
        all)
            tail -f "$LOG_DIR"/*.log 2>/dev/null || print_msg $YELLOW "没有日志文件"
            ;;
        *)
            log_file="$LOG_DIR/$log_type.log"
            if [ -f "$log_file" ]; then
                tail -f "$log_file"
            else
                print_msg $YELLOW "日志文件不存在: $log_file"
            fi
            ;;
    esac
}

# 系统健康检查
health_check() {
    print_title
    print_msg $PURPLE "═══ 系统健康检查 ═══\n"
    
    local health_score=100
    local issues=""
    
    # 检查关键服务
    if [ ! -f "$BACKEND_PID" ] || ! ps -p $(cat "$BACKEND_PID" 2>/dev/null) > /dev/null 2>&1; then
        health_score=$((health_score - 30))
        issues="$issues\n  ⚠ 后端服务未运行"
    fi
    
    if [ ! -f "$FRONTEND_PID" ] || ! ps -p $(cat "$FRONTEND_PID" 2>/dev/null) > /dev/null 2>&1; then
        health_score=$((health_score - 20))
        issues="$issues\n  ⚠ 前端服务未运行"
    fi
    
    # 检查磁盘空间
    DISK_USAGE_PCT=$(df "$PROJECT_ROOT" | awk 'NR==2{print $5}' | sed 's/%//')
    if [ $DISK_USAGE_PCT -gt 90 ]; then
        health_score=$((health_score - 20))
        issues="$issues\n  ⚠ 磁盘使用率过高 ($DISK_USAGE_PCT%)"
    fi
    
    # 检查配置文件
    if [ ! -f "$ENV_FILE" ]; then
        health_score=$((health_score - 10))
        issues="$issues\n  ⚠ 配置文件缺失"
    fi
    
    # 显示健康评分
    echo
    if [ $health_score -ge 80 ]; then
        print_msg $GREEN "系统健康评分: $health_score/100 ✓ 健康"
    elif [ $health_score -ge 60 ]; then
        print_msg $YELLOW "系统健康评分: $health_score/100 ⚠ 警告"
    else
        print_msg $RED "系统健康评分: $health_score/100 ✗ 异常"
    fi
    
    if [ -n "$issues" ]; then
        print_msg $YELLOW "\n发现的问题:$issues"
    fi
    
    # 检查日志大小
    if [ -d "$LOG_DIR" ]; then
        LOG_SIZE=$(du -sh "$LOG_DIR" 2>/dev/null | awk '{print $1}')
        print_msg $CYAN "\n日志目录大小: ${LOG_SIZE:-0}"
    fi
}

# 显示帮助信息
show_help() {
    print_title
    
    cat << EOF
使用方法: $0 [命令] [参数]

${GREEN}基础命令：${NC}
  start [service]     启动服务 (默认全部)
                      可选: backend, frontend, celery, scheduler, redis
  stop [service]      停止服务 (默认全部)
  restart [service]   重启服务 (默认全部)
  status              查看服务状态

${GREEN}日志命令：${NC}
  logs [type] [lines] 查看日志 (默认all, 50行)
                      类型: backend, frontend, celery, scheduler, 
                            redis, system, trading, error, all
  monitor [type]      实时监控日志

${GREEN}维护命令：${NC}
  health              系统健康检查
  clean               清理日志文件
  backup              备份数据
  init                初始化系统

${GREEN}帮助：${NC}
  help                显示此帮助信息

${CYAN}示例：${NC}
  $0 start                # 启动所有服务
  $0 start backend        # 只启动后端
  $0 logs backend 100     # 查看后端最近100行日志
  $0 monitor trading      # 实时监控交易日志
  $0 health              # 健康检查

${CYAN}项目信息：${NC}
  项目名称: $PROJECT_NAME
  虚拟环境: $VENV_NAME
  项目路径: $PROJECT_ROOT

EOF
}

# 初始化系统
init_system() {
    print_title
    print_msg $BLUE "初始化系统环境..."
    
    create_dirs
    init_config
    check_dependencies
    
    # 创建示例文件
    if [ ! -f "$BACKEND_DIR/__init__.py" ]; then
        touch "$BACKEND_DIR/__init__.py"
    fi
    
    print_msg $GREEN "✓ 系统初始化完成"
    print_msg $CYAN "  下一步：使用 '$0 start' 启动服务"
}

# 清理日志
clean_logs() {
    print_msg $YELLOW "清理日志文件..."
    
    # 备份重要日志
    BACKUP_DIR="$LOG_DIR/backup/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    for log_file in "$LOG_DIR"/*.log; do
        if [ -f "$log_file" ]; then
            cp "$log_file" "$BACKUP_DIR/" 2>/dev/null
            > "$log_file"  # 清空日志文件
        fi
    done
    
    print_msg $GREEN "✓ 日志已清理并备份到: $BACKUP_DIR"
}

# 备份数据
backup_data() {
    print_msg $BLUE "备份系统数据..."
    
    BACKUP_DIR="$DATA_DIR/backup/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 备份配置文件
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "$BACKUP_DIR/"
    fi
    
    # 备份数据文件
    if [ -d "$DATA_DIR/cache" ]; then
        cp -r "$DATA_DIR/cache" "$BACKUP_DIR/" 2>/dev/null
    fi
    
    # 创建备份信息文件
    cat > "$BACKUP_DIR/backup_info.txt" << EOF
备份时间: $(date)
项目名称: $PROJECT_NAME
虚拟环境: $VENV_NAME
备份路径: $BACKUP_DIR
EOF
    
    print_msg $GREEN "✓ 数据备份完成: $BACKUP_DIR"
}

# 主函数
main() {
    case "$1" in
        start)
            if [ -z "$2" ]; then
                start_all
            else
                case "$2" in
                    backend)
                        create_dirs
                        check_dependencies
                        start_backend
                        ;;
                    frontend)
                        create_dirs
                        start_frontend
                        ;;
                    celery)
                        create_dirs
                        check_dependencies
                        start_celery
                        ;;
                    scheduler)
                        create_dirs
                        check_dependencies
                        start_scheduler
                        ;;
                    redis)
                        create_dirs
                        start_redis
                        ;;
                    *)
                        print_msg $RED "未知的服务: $2"
                        show_help
                        ;;
                esac
            fi
            ;;
        stop)
            if [ -z "$2" ]; then
                stop_all
            else
                case "$2" in
                    backend)
                        stop_service "后端服务" "$BACKEND_PID"
                        ;;
                    frontend)
                        stop_service "前端服务" "$FRONTEND_PID"
                        ;;
                    celery)
                        stop_service "Celery" "$CELERY_PID"
                        ;;
                    scheduler)
                        stop_service "调度器" "$SCHEDULER_PID"
                        ;;
                    redis)
                        stop_service "Redis" "$REDIS_PID"
                        ;;
                    *)
                        print_msg $RED "未知的服务: $2"
                        show_help
                        ;;
                esac
            fi
            ;;
        restart)
            restart_all
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$2" "$3"
            ;;
        monitor)
            monitor_logs "$2"
            ;;
        health)
            health_check
            ;;
        clean)
            clean_logs
            ;;
        backup)
            backup_data
            ;;
        init)
            init_system
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            if [ -z "$1" ]; then
                show_help
            else
                print_msg $RED "未知命令: $1"
                show_help
                exit 1
            fi
            ;;
    esac
}

# 捕获退出信号
trap 'echo -e "\n${YELLOW}收到中断信号，正在退出...${NC}"; exit 0' INT TERM

# 执行主函数
main "$@"