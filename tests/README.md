# 数据源替换测试套件

## 🎯 目标

保证"替换数据源"不会破坏上层功能，通过单元测试和集成测试验证系统的稳定性。

## 📁 文件结构

```
tests/
├── README.md                 # 本文档
├── requirements.txt          # 测试依赖
├── run_tests.py             # 主测试脚本 ⭐
├── test_config.py           # 测试配置
├── unit_tests.py            # 单元测试模块
├── integration_tests.py     # 集成测试模块
├── mock_modules.py          # 模拟模块
├── fixtures/                # 测试数据
├── temp/                    # 临时文件
├── outputs/                 # 测试输出
└── test_report.json        # 测试报告
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装基础依赖
pip install pandas numpy python-dateutil

# 安装完整测试环境（可选）
pip install -r tests/requirements.txt
```

### 2. 运行测试

```bash
# 运行完整测试套件
python tests/run_tests.py

# 或者从项目根目录运行
python -m tests.run_tests
```

### 3. 查看结果

测试结果将实时显示在终端，详细报告保存在 `tests/test_report.json`。

## 📊 测试覆盖

### 🔧 单元测试

| 测试名称 | 目的 | 关键验证点 |
|---------|------|-----------|
| `normalize_sessions_ok` | 会话数据标准化 | 数据清洗、价格关系修正 |
| `adjust_pre_ok` | 前收盘价调整 | 复权处理、数据连续性 |
| `symbol_map_ok` | 股票代码映射 | 格式转换、市场识别 |
| `cache_hit_ok` | 数据缓存机制 | 缓存命中、过期处理 |

### 🔗 集成测试

| 测试名称 | 目的 | 关键验证点 |
|---------|------|-----------|
| `akshare_fetch_ok` | Akshare数据获取 | API调用、数据格式 |
| `tushare_fetch_ok` | Tushare数据获取 | 配额管理、数据质量 |
| `merge_fallback_ok` | 数据源合并回退 | 优先级处理、数据完整性 |
| `zipline_ingest_ok` | Zipline数据摄入 | 格式转换、数据验证 |
| `algo_smoke_ok` | 算法引擎冒烟测试 | 基础运行、结果合理性 |

## ⚙️ 配置说明

### 测试配置 (`test_config.py`)

```python
TEST_CONFIG = {
    "test_symbols": ["000001.SZ", "600000.SH"],  # 测试股票
    "test_date_range": {
        "start_date": "2024-01-01",
        "end_date": "2024-01-31"
    },
    "performance_benchmarks": {
        "max_fetch_time": 30,      # 最大获取时间(秒)
        "max_process_time": 10,    # 最大处理时间(秒)  
        "max_memory_mb": 500       # 最大内存使用(MB)
    }
}
```

### 环境变量

```bash
export TUSHARE_TOKEN="your_tushare_token"    # Tushare令牌
export TEST_MODE="integration"               # 测试模式: unit/integration/full
export LOG_LEVEL="INFO"                      # 日志级别
```

## 🛠️ 测试模式

### 1. 单元测试模式

```bash
export TEST_MODE="unit"
python tests/run_tests.py
```

仅运行单元测试，不依赖外部API。

### 2. 集成测试模式

```bash
export TEST_MODE="integration"  
python tests/run_tests.py
```

运行完整测试套件，包括外部API调用。

### 3. 模拟测试模式

如果没有API配置或网络连接，测试框架自动使用模拟数据，确保测试能够正常进行。

## 📈 性能基准

### 时间基准

- 数据获取: < 30秒
- 数据处理: < 10秒  
- 算法运行: < 5秒

### 资源基准

- 内存使用: < 500MB
- 数据量: < 10,000行/请求

### 成功率基准

- 总体成功率: ≥ 80%
- 关键功能成功率: ≥ 95%

## 🚨 故障处理

### 常见问题

1. **API调用失败**
   ```
   ❌ akshare_fetch_ok: ConnectionError: 网络连接错误
   ```
   **解决**: 检查网络连接，或运行模拟模式测试

2. **配额不足**
   ```
   ❌ tushare_fetch_ok: API调用次数已达每日限制
   ```
   **解决**: 等待配额重置或使用模拟数据

3. **数据格式错误**
   ```
   ❌ normalize_sessions_ok: 缺少必要列: ['volume']
   ```
   **解决**: 检查数据源返回格式，更新数据处理逻辑

### 调试模式

```bash
export LOG_LEVEL="DEBUG"
python tests/run_tests.py
```

开启详细日志输出，便于问题定位。

## 🔄 持续集成

### GitHub Actions 示例

```yaml
name: Data Source Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        pip install -r tests/requirements.txt
    - name: Run tests
      run: |
        export TEST_MODE="unit"
        python tests/run_tests.py
    - name: Upload test results
      uses: actions/upload-artifact@v3
      with:
        name: test-report
        path: tests/test_report.json
```

## 📊 测试报告格式

### JSON报告结构

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "summary": {
    "total": 9,
    "passed": 8,
    "failed": 1,
    "duration": 45.2
  },
  "results": [
    {
      "name": "normalize_sessions_ok",
      "passed": true,
      "message": "PASSED",
      "duration": 0.123
    }
  ]
}
```

### 控制台输出示例

```
============================================================
数据源替换测试套件
============================================================

🔧 单元测试:
----------------------------------------
✅ normalize_sessions_ok: PASSED (0.123s)
✅ adjust_pre_ok: PASSED (0.089s)
✅ symbol_map_ok: PASSED (0.056s)
✅ cache_hit_ok: PASSED (0.067s)

🔗 集成测试:
----------------------------------------
✅ akshare_fetch_ok: PASSED (2.341s)
✅ tushare_fetch_ok