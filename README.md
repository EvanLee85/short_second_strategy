# 短周期量化交易系统

一个基于多数据源的高频量化交易系统，支持灵活的数据源切换、复权处理和Zipline集成。

## 🚀 快速开始

### 1. 环境安装

```bash
# 安装依赖
pip install pandas numpy zipline-reloaded akshare tushare

# 克隆项目
git clone <your-repo-url>
cd short_second_strategy
```

### 2. 配置设置

#### 基础配置 (`config/settings.py`)

```python
# 数据源配置
DATA_SOURCES = {
    'akshare': {
        'enabled': True,
        'priority': 1,
        'timeout': 30
    },
    'tushare': {
        'enabled': True,
        'priority': 2,
        'token': 'your_tushare_token_here',  # 必须配置
        'timeout': 30
    }
}

# 数据存储路径
DATA_PATHS = {
    'raw_data': './data/raw/',
    'processed_data': './data/processed/', 
    'zipline_data': './data/zipline/'
}

# 复权设置
ADJUSTMENT_CONFIG = {
    'method': 'qfq',  # qfq前复权, hfq后复权, none不复权
    'base_date': None  # 复权基准日期，None表示最新
}
```

#### 环境变量配置 (`.env`)

```bash
# 复制配置模板
cp config/.env.example .env

# 编辑配置文件
TUSHARE_TOKEN=your_tushare_token_here
LOG_LEVEL=INFO
ZIPLINE_ROOT=./data/zipline/
```

### 3. 运行顺序 ⭐

**严格按照以下顺序执行，避免数据不一致：**

```bash
# Step 1: 配置验证
python scripts/verify_config.py

# Step 2: 运行测试套件
python tests/run_tests.py

# Step 3: 数据获取与处理
python scripts/fetch_data.py --symbols 000001.SZ,600000.SH --start-date 2024-01-01

# Step 4: Zipline数据摄入
python scripts/zipline_ingest.py --bundle custom_bundle

# Step 5: 运行策略回测
python strategies/run_backtest.py --strategy sample_strategy
```

## 📁 项目结构

```
short_second_strategy/
├── README.md                    # 本文档
├── config/                      # 配置文件
│   ├── settings.py             # 主配置文件
│   ├── .env.example            # 环境变量模板
│   └── logging.conf            # 日志配置
├── data_sources/                # 数据源模块
│   ├── akshare_source.py       # Akshare数据源
│   ├── tushare_source.py       # Tushare数据源
│   └── unified_fetcher.py      # 统一数据获取器
├── data_processor/              # 数据处理模块
│   ├── session_normalizer.py  # 会话标准化
│   ├── price_adjuster.py       # 复权处理
│   └── symbol_mapper.py        # 代码映射
├── backend/                     # 后端集成
│   ├── data_fetcher_facade.py  # 数据获取门面
│   ├── zipline_csv_writer.py   # CSV生成器
│   └── backend_integration.py  # 集成适配器
├── tests/                       # 测试模块
│   ├── run_tests.py            # 测试运行器
│   ├── unit_tests.py           # 单元测试
│   └── integration_tests.py    # 集成测试
├── scripts/                     # 工具脚本
│   ├── verify_config.py        # 配置验证
│   ├── fetch_data.py           # 数据获取
│   └── zipline_ingest.py       # Zipline摄入
├── strategies/                  # 交易策略
│   ├── sample_strategy.py      # 示例策略
│   └── run_backtest.py         # 回测运行器
└── docs/                        # 文档目录
    ├── API.md                  # API文档
    ├── TROUBLESHOOTING.md      # 故障排查
    └── DEVELOPMENT.md          # 开发指南
```

## ⚙️ 配置说明

### 数据源配置

系统支持多个数据源，按优先级自动切换：

```python
DATA_SOURCES = {
    'akshare': {
        'enabled': True,
        'priority': 1,        # 优先级：1最高
        'timeout': 30,        # 请求超时时间(秒)
        'rate_limit': 1.0,    # 限流：每秒请求数
        'retry_times': 3      # 失败重试次数
    },
    'tushare': {
        'enabled': True,
        'priority': 2,
        'token': 'your_token', # Tushare API token
        'timeout': 30,
        'rate_limit': 0.5,     # Tushare限流更严格
        'retry_times': 3
    }
}
```

### 复权处理配置

```python
ADJUSTMENT_CONFIG = {
    'method': 'qfq',           # 复权方式
    'base_date': None,         # 复权基准日期
    'handle_missing': 'drop',  # 缺失数据处理方式
    'validate_prices': True    # 是否验证价格关系
}

# 复权方式说明：
# 'qfq' - 前复权：以最新价格为基准向前调整
# 'hfq' - 后复权：以历史价格为基准向后调整  
# 'none' - 不复权：使用原始价格数据
```

### Zipline集成配置

```python
ZIPLINE_CONFIG = {
    'bundle_name': 'custom_bundle',
    'data_frequency': 'daily',
    'calendar': 'SHSZ',        # 沪深交易日历
    'start_session': '2020-01-01',
    'end_session': '2024-12-31'
}
```

## 🔧 使用说明

### 数据获取

```python
from data_sources.unified_fetcher import UnifiedDataFetcher

# 创建数据获取器
fetcher = UnifiedDataFetcher()

# 获取单只股票数据
data = fetcher.get_stock_data(
    symbol='000001.SZ',
    start_date='2024-01-01',
    end_date='2024-12-31',
    adjust='qfq'  # 前复权
)

# 批量获取数据
symbols = ['000001.SZ', '600000.SH', '000002.SZ']
batch_data = fetcher.batch_get_data(
    symbols=symbols,
    start_date='2024-01-01',
    end_date='2024-12-31'
)
```

### 后端集成使用

```python
# 启用后端集成（一次性设置）
from backend.backend_integration import enable_backend_integration

enable_backend_integration(
    csv_data_path='./data/raw/',
    auto_patch=True  # 自动patch pandas函数
)

# 现有代码无需修改，自动使用新数据源！
import pandas as pd
data = pd.read_csv('data/000001.SZ.csv')  # 自动切换到新数据获取器
```

### Zipline策略开发

```python
from zipline import run_algorithm
from zipline.api import order_percent, symbol

def initialize(context):
    """策略初始化"""
    context.asset = symbol('000001.SZ')
    
def handle_data(context, data):
    """每日处理逻辑"""
    price = data.current(context.asset, 'close')
    
    # 简单的买入持有策略
    if not context.portfolio.positions[context.asset]:
        order_percent(context.asset, 1.0)

# 运行回测
result = run_algorithm(
    start='2024-01-01',
    end='2024-12-31',
    initialize=initialize,
    handle_data=handle_data,
    bundle='custom_bundle'
)
```

## 🧪 测试验证

```bash
# 运行完整测试套件
python tests/run_tests.py

# 运行特定测试
python tests/unit_tests.py                    # 单元测试
python tests/integration_tests.py             # 集成测试

# 验证部署
python test_deployment.py                     # 部署验证

# 检查数据一致性
python scripts/data_consistency_check.py      # 数据一致性检查
```

## 📊 监控与日志

### 日志配置

系统提供详细的日志记录：

```python
import logging

# 配置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system.log'),
        logging.StreamHandler()
    ]
)
```

### 性能监控

```python
from backend.backend_integration import get_integration_stats

# 获取集成统计
stats = get_integration_stats()
print(f"数据获取次数: {stats['read_csv_intercepts']}")
print(f"回退次数: {stats['fallback_calls']}")
print(f"错误次数: {stats['errors']}")
```

## 🚨 常见故障排查

### 快速诊断

```bash
# 运行系统诊断
python scripts/system_diagnosis.py

# 检查配置问题
python scripts/verify_config.py --verbose

# 数据源连通性测试
python scripts/test_data_sources.py
```

### 常见问题解决

#### 1. 数据源连接失败

**现象**: `ConnectionError: 数据源连接超时`

**解决方案**:
```bash
# 检查网络连接
ping www.baidu.com

# 验证API token
python scripts/test_data_sources.py --source tushare

# 调整超时设置
# 在config/settings.py中增加timeout值
```

#### 2. 复权数据不一致

**现象**: 同一股票不同时间获取的数据价格不匹配

**原因**: 复权基准日期不同导致

**解决方案**:
```python
# 统一复权基准
ADJUSTMENT_CONFIG = {
    'method': 'qfq',
    'base_date': '2024-12-31',  # 设置固定基准日期
    'cache_adjustment_factors': True
}

# 清理缓存重新获取
python scripts/clear_cache.py --type adjustment
```

#### 3. 会话数据不一致

**现象**: 交易日历与数据日期不匹配

**解决方案**:
```python
# 使用标准交易日历
from zipline.utils.calendars import get_calendar

calendar = get_calendar('SHSZ')  # 沪深交易所日历

# 或手动指定交易日
TRADING_CALENDAR = {
    'exclude_weekends': True,
    'exclude_holidays': True,
    'custom_holidays': ['2024-01-01', '2024-02-10']  # 自定义假期
}
```

#### 4. Zipline摄入失败

**现象**: `zipline ingest` 命令失败

**解决方案**:
```bash
# 检查数据格式
python scripts/validate_zipline_data.py

# 清理Zipline缓存
zipline clean --bundle custom_bundle

# 重新摄入数据
python scripts/zipline_ingest.py --bundle custom_bundle --force
```

## 📞 技术支持

### 获取帮助

- 📖 查看详细文档: [docs/](./docs/)
- 🐛 问题反馈: [GitHub Issues](issues链接)
- 💬 技术讨论: [内部技术群]

### 开发与贡献

- 🔧 开发指南: [docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md)
- 🧪 测试指南: [docs/TESTING.md](./docs/TESTING.md)
- 📋 代码规范: [docs/CODING_STANDARDS.md](./docs/CODING_STANDARDS.md)

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

*最后更新: 2025-08-27*
*版本: 1.0.0*