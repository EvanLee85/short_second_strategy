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
✅ tushare_fetch_ok: PASSED (1.876s)
✅ merge_fallback_ok: PASSED (0.234s)
✅ zipline_ingest_ok: PASSED (0.456s)
✅ algo_smoke_ok: PASSED (1.123s)

============================================================
📊 测试结果汇总
============================================================
🎉 所有测试通过! (9/9)
⏱️  总耗时: 6.365s

📄 详细报告已保存: tests/test_report.json
```

## 🔧 自定义测试

### 添加新的单元测试

1. 在 `unit_tests.py` 中添加测试方法：

```python
def my_custom_test_ok(self):
    """自定义测试"""
    # 测试逻辑
    assert condition, "测试失败原因"
    print("✓ 自定义测试通过")
```

2. 在 `run_tests.py` 中注册测试：

```python
self.unit_tests = [
    "normalize_sessions_ok",
    "adjust_pre_ok", 
    "symbol_map_ok",
    "cache_hit_ok",
    "my_custom_test_ok"  # 新增
]
```

### 添加新的集成测试

类似地在 `integration_tests.py` 中添加测试方法并注册。

## 🎯 测试策略

### 数据驱动测试

使用 `fixtures/` 目录存放测试数据：

```python
def load_test_fixture(filename: str) -> pd.DataFrame:
    """加载测试数据"""
    filepath = TESTS_ROOT / "fixtures" / filename
    return pd.read_csv(filepath)

# 使用测试数据
test_data = load_test_fixture("sample_stock_data.csv")
```

### 参数化测试

测试多个股票代码：

```python
def test_multiple_symbols(self):
    """测试多个股票代码"""
    symbols = ["000001.SZ", "600000.SH", "300001.SZ"]
    for symbol in symbols:
        result = self.fetch_data(symbol)
        assert not result.empty, f"数据获取失败: {symbol}"
```

### 边界条件测试

```python
def test_edge_cases(self):
    """测试边界条件"""
    edge_cases = [
        ("", "空字符串"),
        ("INVALID", "无效代码"),
        ("000001.XX", "错误后缀")
    ]
    
    for symbol, description in edge_cases:
        try:
            result = self.process_symbol(symbol)
            # 验证错误处理
        except Exception as e:
            print(f"✓ 正确处理边界条件: {description}")
```

## 📝 最佳实践

### 1. 测试独立性

每个测试应该独立运行，不依赖其他测试的结果：

```python
def setUp(self):
    """测试前准备"""
    self.test_data = self.create_fresh_test_data()

def tearDown(self):
    """测试后清理"""
    self.cleanup_test_resources()
```

### 2. 异常处理

测试应该能够处理各种异常情况：

```python
def test_network_failure(self):
    """测试网络异常"""
    with patch('requests.get', side_effect=ConnectionError):
        # 测试网络异常时的处理
        result = self.data_source.fetch_data("000001.SZ")
        assert result is None or result.empty
```

### 3. 性能测试

关注性能敏感的操作：

```python
@performance_test(max_time=5.0, max_memory_mb=200)
def test_large_dataset_processing(self):
    """测试大数据集处理性能"""
    large_data = self.generate_large_dataset(10000)
    result = self.processor.process(large_data)
    assert len(result) == len(large_data)
```

### 4. 数据质量验证

确保数据质量符合预期：

```python
def validate_data_quality(self, data: pd.DataFrame) -> bool:
    """验证数据质量"""
    quality_checks = [
        len(data) > 0,  # 非空
        not data.isnull().all().any(),  # 无全空列
        (data['high'] >= data['low']).all(),  # 价格关系正确
        (data['volume'] >= 0).all()  # 成交量非负
    ]
    return all(quality_checks)
```

## 🔍 故障诊断

### 测试失败排查流程

1. **查看错误信息**
   ```bash
   ❌ normalize_sessions_ok: AssertionError: high应该 >= low
   ```

2. **启用调试模式**
   ```bash
   export LOG_LEVEL="DEBUG"
   python tests/run_tests.py
   ```

3. **单独运行失败测试**
   ```python
   # 在unit_tests.py中直接调用
   if __name__ == "__main__":
       tests = UnitTests()
       tests.normalize_sessions_ok()
   ```

4. **检查测试数据**
   - 验证输入数据格式
   - 检查数据边界条件
   - 确认业务逻辑正确性

### 日志分析

测试日志保存在 `logs/tests/test.log`：

```
2024-01-15 10:30:15 - tests.unit_tests - INFO - 开始数据标准化测试
2024-01-15 10:30:15 - tests.unit_tests - DEBUG - 输入数据: 1000行，6列
2024-01-15 10:30:15 - tests.unit_tests - WARNING - 发现3行异常数据，已清理
2024-01-15 10:30:15 - tests.unit_tests - INFO - 数据标准化完成: 997行
```

## 🚀 进阶用法

### 并行测试执行

```bash
export PARALLEL_TESTS=true
python tests/run_tests.py
```

### 测试覆盖率报告

```bash
pip install pytest-cov
pytest tests/ --cov=. --cov-report=html
```

### 压力测试模式

```python
def stress_test_data_processing(self):
    """压力测试数据处理"""
    for i in range(100):  # 重复100次
        large_data = self.generate_random_data(5000)
        result = self.processor.process(large_data)
        assert self.validate_result(result)
```

## 📞 支持与反馈

### 遇到问题？

1. 检查本文档的故障处理部分
2. 查看测试日志文件
3. 运行调试模式获取详细信息
4. 联系开发团队

### 贡献测试用例

欢迎贡献新的测试用例！请确保：

- 测试用例有明确的目的
- 包含充分的文档说明
- 遵循现有的代码风格
- 通过所有现有测试

---

## 📋 检查清单

运行测试前，请确认：

- [ ] 已安装必要依赖 (`pip install -r requirements.txt`)
- [ ] 已设置环境变量 (如需要)
- [ ] 网络连接正常 (集成测试)
- [ ] 有足够的磁盘空间存储测试结果
- [ ] Python版本 >= 3.8

测试完成后，请检查：

- [ ] 所有核心测试通过 (通过率 ≥ 80%)
- [ ] 无严重性能问题
- [ ] 测试报告已生成
- [ ] 异常情况已妥善处理

---

*最后更新: 2025-08-27*
*版本: 1.0.0*

总结
📋 完整测试框架结构
🎯 核心文件

run_tests.py - 主测试运行脚本

一键运行所有测试
实时显示通过/失败状态
生成详细的JSON报告


unit_tests.py - 单元测试模块

✅ normalize_sessions_ok - 会话数据标准化测试
✅ adjust_pre_ok - 前收盘价调整测试
✅ symbol_map_ok - 股票代码映射测试
✅ cache_hit_ok - 数据缓存命中测试


integration_tests.py - 集成测试模块

✅ akshare_fetch_ok - Akshare数据获取测试
✅ tushare_fetch_ok - Tushare数据获取测试
✅ merge_fallback_ok - 数据源合并回退测试
✅ zipline_ingest_ok - Zipline数据摄入测试
✅ algo_smoke_ok - 算法引擎冒烟测试



🛠️ 支持文件

mock_modules.py - 模拟组件

提供完整的模拟数据源和处理组件
确保测试能独立运行，不依赖外部API


test_config.py - 测试配置

集中管理测试参数和性能基准
提供测试辅助工具类


setup_tests.py - 环境设置脚本

自动检查和安装依赖
创建测试目录和示例数据


README.md - 详细使用说明

完整的使用指南和故障排查



🚀 快速使用指南
1. 环境设置
bash# 设置测试环境
python tests/setup_tests.py

# 或手动安装基础依赖
pip install pandas numpy python-dateutil
2. 运行测试
bash# 运行完整测试套件
python tests/run_tests.py

# 预期输出示例:
# ============================================================
# 数据源替换测试套件  
# ============================================================
# 🔧 单元测试:
# ✅ normalize_sessions_ok: PASSED (0.123s)
# ✅ adjust_pre_ok: PASSED (0.089s)
# ✅ symbol_map_ok: PASSED (0.056s) 
# ✅ cache_hit_ok: PASSED (0.067s)
#
# 🔗 集成测试:
# ✅ akshare_fetch_ok: PASSED (2.341s)
# ✅ tushare_fetch_ok: PASSED (1.876s)
# ✅ merge_fallback_ok: PASSED (0.234s)
# ✅ zipline_ingest_ok: PASSED (0.456s)  
# ✅ algo_smoke_ok: PASSED (1.123s)
#
# 🎉 所有测试通过! (9/9)
3. 查看详细报告
测试完成后会生成 tests/test_report.json，包含完整的测试结果和性能数据。
✨ 核心特性

🎯 目标明确: 专门验证"替换数据源"不会破坏上层功能
🔄 自动回退: 当真实API不可用时，自动使用模拟数据
⚡ 性能监控: 内置性能基准，确保替换后性能不下降
📊 详细报告: JSON格式报告，便于CI/CD集成
🛡️ 错误处理: 完善的异常处理和错误信息
🔧 易扩展: 模块化设计，易于添加新测试用例

🎉 一次性判断脚本
这个测试框架完全满足你的需求："一次性跑完即可判断通过与否的脚本(只打印通过/失败与原因)"。

✅ 单元测试覆盖核心数据处理组件
✅ 集成测试验证端到端数据流
✅ 一次运行，立即得到通过/失败结果
✅ 清晰的成功/失败原因说明
✅ 详细的性能和错误报告