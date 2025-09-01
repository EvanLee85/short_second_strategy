#!/bin/bash
# 量化交易前端系统 - 项目设置与启动脚本

set -e  # 遇到错误立即退出

echo "🚀 短周期量化交易系统 - 前端联调部署"
echo "================================================"

# 项目根目录
PROJECT_ROOT=$(pwd)
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT/backend"

# 颜色输出函数
print_success() { echo -e "\033[32m✅ $1\033[0m"; }
print_warning() { echo -e "\033[33m⚠️  $1\033[0m"; }
print_error() { echo -e "\033[31m❌ $1\033[0m"; }
print_info() { echo -e "\033[34mℹ️  $1\033[0m"; }

# 检查Python环境
check_python() {
    print_info "检查Python环境..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 未安装"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    print_success "Python版本: $PYTHON_VERSION"
    
    if [ $(echo "$PYTHON_VERSION >= 3.8" | bc -l) -eq 0 ]; then
        print_warning "建议使用Python 3.8+版本"
    fi
}

# 创建项目目录结构
setup_directories() {
    print_info "创建项目目录结构..."
    
    # 创建主要目录
    mkdir -p "$FRONTEND_DIR/js"
    mkdir -p "$FRONTEND_DIR/css"
    mkdir -p "$BACKEND_DIR"
    mkdir -p "data/raw"
    mkdir -p "data/processed"
    mkdir -p "logs"
    mkdir -p "scripts"
    
    print_success "目录结构创建完成"
}

# 安装Python依赖
install_dependencies() {
    print_info "安装Python依赖..."
    
    # 检查是否有虚拟环境
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        print_success "使用虚拟环境: $VIRTUAL_ENV"
    else
        print_warning "建议在虚拟环境中运行"
    fi
    
    # 安装基础依赖
    pip3 install flask flask-cors flask-socketio pandas numpy python-socketio python-engineio
    
    # 安装可选依赖
    print_info "尝试安装可选依赖..."
    pip3 install akshare tushare matplotlib seaborn --no-deps --ignore-installed 2>/dev/null || print_warning "部分可选依赖安装失败，可手动安装"
    
    print_success "Python依赖安装完成"
}

# 创建前端文件
create_frontend_files() {
    print_info "创建前端文件..."
    
    # 创建主HTML文件（从artifact复制）
    print_info "复制前端仪表盘HTML文件..."
    
    # 创建JavaScript模块目录
    cat > "$FRONTEND_DIR/js/config.js" << 'EOF'
// 前端配置文件
const CONFIG = {
    API_BASE_URL: '/api/v1',
    WEBSOCKET_URL: window.location.origin,
    UPDATE_INTERVALS: {
        MACRO: 60000,      // 1分钟
        STOCKS: 30000,     // 30秒
        TRADING: 15000,    // 15秒
        REALTIME: 5000     // 5秒
    },
    CHART_COLORS: {
        PRIMARY: '#3b82f6',
        SUCCESS: '#10b981',
        WARNING: '#f59e0b',
        DANGER: '#ef4444'
    }
};

window.CONFIG = CONFIG;
EOF

    # 创建README文件
    cat > "$PROJECT_ROOT/README.md" << 'EOF'
# 短周期量化交易系统 - 前端仪表盘

## 功能层次

### 第1层：只读大盘/轮动/候选池/闸门结果
- 宏观环境监控
- 板块轮动分析
- 股票筛选结果
- 量化闸门状态

### 第2层：交互筛选与买点回放
- 动态筛选条件调整
- 买点时机回放分析
- 个股详细分析

### 第3层：实时分时订阅（SocketIO）
- WebSocket实时数据推送
- 分时图表更新
- 实时持仓监控

## 技术架构

- **前端**: HTML5 + 原生JavaScript + Socket.IO
- **后端**: Python Flask + Flask-SocketIO
- **数据**: RESTful API + WebSocket推送
- **样式**: 现代化CSS3 (无第三方UI框架依赖)

## 快速启动

```bash
# 1. 运行项目设置
bash project_setup.sh

# 2. 启动后端服务
python backend_api_server.py

# 3. 访问前端界面
open http://localhost:5000
```

## API接口

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/macro/overview` | GET | 宏观环境概览 |
| `/api/v1/sector/rotation` | GET | 板块轮动分析 |
| `/api/v1/stocks/candidates` | GET | 股票候选池 |
| `/api/v1/trading/positions` | GET | 交易持仓 |

## WebSocket事件

- `macro_update` - 宏观数据更新
- `sector_update` - 板块数据更新
- `stocks_update` - 股票数据更新
- `tick_data` - 实时行情推送

EOF

    print_success "前端文件创建完成"
}

# 创建后端API服务文件
create_backend_files() {
    print_info "创建后端API服务文件..."
    
    # 注意：实际的backend_api_server.py内容应该从之前的artifact中复制
    print_info "请将backend_api_server.py内容保存到backend目录"
    
    # 创建启动脚本
    cat > "$PROJECT_ROOT/start_server.py" << 'EOF'
#!/usr/bin/env python3
"""
量化交易系统启动脚本
"""

import os
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

if __name__ == "__main__":
    try:
        from backend_api_server import app, socketio
        print("启动量化交易API服务器...")
        print("前端访问地址: http://localhost:5000/")
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保backend_api_server.py文件存在")
        sys.exit(1)
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)
EOF

    chmod +x "$PROJECT_ROOT/start_server.py"
    print_success "后端文件创建完成"
}

# 创建开发工具
create_dev_tools() {
    print_info "创建开发工具..."
    
    # 创建测试脚本
    cat > "$PROJECT_ROOT/test_api.py" << 'EOF'
#!/usr/bin/env python3
"""
API接口测试脚本
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000/api/v1"

def test_endpoint(endpoint, description):
    """测试API端点"""
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        print(f"[{response.status_code}] {description}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ 数据长度: {len(str(data))}")
            if 'timestamp' in data:
                print(f"  ✓ 更新时间: {data['timestamp']}")
        else:
            print(f"  ✗ 错误: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"  ✗ 连接错误: {e}")
    
    print()

def main():
    print("API接口测试")
    print("=" * 40)
    
    endpoints = [
        ("/macro/overview", "宏观环境概览"),
        ("/sector/rotation", "板块轮动分析"), 
        ("/stocks/candidates", "股票候选池"),
        ("/trading/positions", "交易持仓"),
        ("/stocks/002415/buypoint", "买点分析")
    ]
    
    for endpoint, desc in endpoints:
        test_endpoint(endpoint, desc)
        time.sleep(0.5)
    
    print("测试完成")

if __name__ == "__main__":
    main()
EOF

    chmod +x "$PROJECT_ROOT/test_api.py"
    
    # 创建监控脚本
    cat > "$PROJECT_ROOT/monitor.py" << 'EOF'
#!/usr/bin/env python3
"""
系统监控脚本
"""

import requests
import time
import json
from datetime import datetime

def check_system_health():
    """检查系统健康状态"""
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 系统正常")
            print(f"  连接客户端: {data.get('clients_connected', 0)}")
            print(f"  活跃订阅: {data.get('active_subscriptions', 0)}")
            return True
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 系统异常: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 连接失败: {e}")
        return False

def main():
    print("系统监控启动...")
    print("按 Ctrl+C 停止监控")
    
    try:
        while True:
            check_system_health()
            time.sleep(30)  # 每30秒检查一次
    except KeyboardInterrupt:
        print("\n监控已停止")

if __name__ == "__main__":
    main()
EOF

    chmod +x "$PROJECT_ROOT/monitor.py"
    print_success "开发工具创建完成"
}

# 运行系统检查
run_system_check() {
    print_info "运行系统检查..."
    
    # 检查端口占用
    if netstat -tlnp 2>/dev/null | grep -q ":5000 "; then
        print_warning "端口5000已被占用，请先关闭占用进程"
    else
        print_success "端口5000可用"
    fi
    
    # 检查必要的Python包
    python3 -c "import flask, pandas, numpy" 2>/dev/null && print_success "Python依赖检查通过" || print_error "Python依赖缺失"
    
    print_success "系统检查完成"
}

# 显示使用说明
show_usage() {
    echo ""
    echo "🎯 使用说明"
    echo "================================================"
    echo ""
    echo "1. 启动后端服务器："
    echo "   python start_server.py"
    echo ""
    echo "2. 访问前端界面："
    echo "   打开浏览器访问: http://localhost:5000"
    echo ""
    echo "3. 测试API接口："
    echo "   python test_api.py"
    echo ""
    echo "4. 监控系统状态："
    echo "   python monitor.py"
    echo ""
    echo "📁 项目结构："
    echo "   ├── frontend/              # 前端文件"
    echo "   │   ├── js/               # JavaScript模块"
    echo "   │   └── css/              # 样式文件"  
    echo "   ├── backend_api_server.py  # 后端API服务"
    echo "   ├── start_server.py       # 启动脚本"
    echo "   ├── test_api.py           # API测试"
    echo "   └── monitor.py            # 系统监控"
    echo ""
    echo "🔧 功能特性："
    echo "   • 第1层: 只读仪表盘 (宏观/板块/股票/交易)"
    echo "   • 第2层: 交互筛选与买点回放"
    echo "   • 第3层: 实时WebSocket数据推送"
    echo ""
    echo "📡 API端点："
    echo "   • GET /api/v1/macro/overview    # 宏观环境"
    echo "   • GET /api/v1/sector/rotation   # 板块轮动"
    echo "   • GET /api/v1/stocks/candidates # 股票筛选"
    echo "   • GET /api/v1/trading/positions # 交易持仓"
    echo "   • WebSocket /socket.io/         # 实时推送"
    echo ""
}

# 主执行函数
main() {
    case "${1:-setup}" in
        "setup")
            check_python
            setup_directories
            install_dependencies
            create_frontend_files
            create_backend_files
            create_dev_tools
            run_system_check
            show_usage
            print_success "项目设置完成！"
            ;;
        "start")
            print_info "启动系统..."
            python3 start_server.py
            ;;
        "test")
            print_info "运行API测试..."
            python3 test_api.py
            ;;
        "monitor")
            print_info "启动系统监控..."
            python3 monitor.py
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            print_error "未知命令: $1"
            echo "使用 './project_setup.sh help' 查看帮助"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"