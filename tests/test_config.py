"""
测试配置文件
包含测试所需的配置参数和辅助函数
"""

import os
from pathlib import Path
from datetime import datetime, timedelta

# 项目路径配置
PROJECT_ROOT = Path(__file__).parent.parent
TESTS_ROOT = Path(__file__).parent
DATA_ROOT = PROJECT_ROOT / "data"
LOGS_ROOT = PROJECT_ROOT / "logs"

# 测试数据配置
TEST_CONFIG = {
    # 测试股票代码
    "test_symbols": [
        "000001.SZ",  # 平安银行
        "000002.SZ",  # 万科A
        "600000.SH",  # 浦发银行
        "600036.SH",  # 招商银行
        "000858.SZ"   # 五粮液
    ],
    
    # 测试时间范围
    "test_date_range": {
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "recent_start": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        "recent_end": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    },
    
    # 数据源配置
    "data_sources": {
        "akshare": {
            "enabled": True,
            "timeout": 30,
            "retry_times": 3,
            "rate_limit": 1.0  # 每秒请求限制
        },
        "tushare": {
            "enabled": True,
            "timeout": 30,
            "retry_times": 3,
            "token_required": True,
            "rate_limit": 0.5
        },
        "yahoo": {
            "enabled": False,  # 可选数据源
            "timeout": 20,
            "retry_times": 2
        }
    },
    
    # 性能基准配置
    "performance_benchmarks": {
        "max_fetch_time": 30,      # 数据获取最大时间(秒)
        "max_process_time": 10,    # 数据处理最大时间(秒)
        "max_memory_mb": 500,      # 最大内存使用(MB)
        "max_data_rows": 10000,    # 最大数据行数
        "min_success_rate": 0.8    # 最小成功率
    },
    
    # 数据质量配置
    "data_quality": {
        "required_columns": ["open", "high", "low", "close", "volume"],
        "optional_columns": ["amount", "turnover", "pre_close"],
        "min_data_points": 10,      # 最少数据点数
        "max_missing_ratio": 0.1,   # 最大缺失率
        "price_change_limit": 0.15  # 单日最大涨跌幅限制
    },
    
    # 算法测试配置
    "algo_test": {
        "initial_capital": 100000,
        "benchmark": "000001.SZ",
        "test_strategies": [
            "buy_and_hold",
            "moving_average",
            "mean_reversion"
        ],
        "min_sharpe_ratio": -2.0,   # 最小夏普比率
        "max_drawdown": -0.5        # 最大回撤限制
    },
    
    # 缓存配置
    "cache": {
        "enabled": True,
        "ttl_seconds": 3600,        # 缓存生存时间
        "max_size_mb": 100,         # 最大缓存大小
        "cleanup_interval": 300     # 清理间隔(秒)
    }
}

# 环境变量配置
ENV_CONFIG = {
    "tushare_token": os.getenv("TUSHARE_TOKEN", ""),
    "akshare_timeout": int(os.getenv("AKSHARE_TIMEOUT", "30")),
    "test_mode": os.getenv("TEST_MODE", "unit"),  # unit, integration, full
    "log_level": os.getenv("LOG_LEVEL", "INFO"),
    "parallel_tests": os.getenv("PARALLEL_TESTS", "false").lower() == "true"
}

# 测试辅助函数
class TestHelpers:
    """测试辅助工具类"""
    
    @staticmethod
    def create_test_directories():
        """创建测试所需目录"""
        dirs_to_create = [
            TESTS_ROOT / "temp",
            TESTS_ROOT / "fixtures",
            TESTS_ROOT / "outputs",
            DATA_ROOT / "test_cache",
            LOGS_ROOT / "tests"
        ]
        
        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def cleanup_test_files():
        """清理测试文件"""
        import shutil
        
        cleanup_dirs = [
            TESTS_ROOT / "temp",
            TESTS_ROOT / "outputs",
            DATA_ROOT / "test_cache"
        ]
        
        for dir_path in cleanup_dirs:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                dir_path.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def get_test_symbol(index: int = 0) -> str:
        """获取测试股票代码"""
        symbols = TEST_CONFIG["test_symbols"]
        return symbols[index % len(symbols)]
    
    @staticmethod
    def get_test_date_range(recent: bool = False) -> tuple:
        """获取测试日期范围"""
        date_config = TEST_CONFIG["test_date_range"]
        if recent:
            return date_config["recent_start"], date_config["recent_end"]
        else:
            return date_config["start_date"], date_config["end_date"]
    
    @staticmethod
    def is_data_source_enabled(source_name: str) -> bool:
        """检查数据源是否启用"""
        return TEST_CONFIG["data_sources"].get(source_name, {}).get("enabled", False)
    
    @staticmethod
    def get_performance_limit(metric: str) -> float:
        """获取性能指标限制"""
        return TEST_CONFIG["performance_benchmarks"].get(metric, float('inf'))
    
    @staticmethod
    def validate_data_quality(data, strict: bool = True) -> dict:
        """验证数据质量"""
        if data is None or data.empty:
            return {"valid": False, "reason": "数据为空"}
        
        quality_config = TEST_CONFIG["data_quality"]
        issues = []
        
        # 检查必要列
        required_cols = quality_config["required_columns"]
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            issues.append(f"缺少必要列: {missing_cols}")
        
        # 检查数据量
        if len(data) < quality_config["min_data_points"]:
            issues.append(f"数据点不足: {len(data)} < {quality_config['min_data_points']}")
        
        # 检查缺失率
        if not data.empty:
            missing_ratio = data.isnull().sum().sum() / (len(data) * len(data.columns))
            if missing_ratio > quality_config["max_missing_ratio"]:
                issues.append(f"缺失率过高: {missing_ratio:.2%}")
        
        # 检查价格数据合理性
        if all(col in data.columns for col in ['high', 'low', 'open', 'close']):
            price_issues = (
                (data['high'] < data['low']) |
                (data['high'] < data['open']) |
                (data['high'] < data['close']) |
                (data['low'] > data['open']) |
                (data['low'] > data['close'])
            ).sum()
            
            if price_issues > 0:
                issues.append(f"价格关系异常: {price_issues}条记录")
        
        return {
            "valid": len(issues) == 0 or not strict,
            "issues": issues,
            "data_points": len(data),
            "columns": list(data.columns)
        }

# 测试装饰器
def require_data_source(source_name: str):
    """装饰器: 要求特定数据源可用"""
    def decorator(test_func):
        def wrapper(*args, **kwargs):
            if not TestHelpers.is_data_source_enabled(source_name):
                print(f"⚠️ 跳过测试 {test_func.__name__}: {source_name}数据源未启用")
                return
            return test_func(*args, **kwargs)
        return wrapper
    return decorator

def performance_test(max_time: float = None, max_memory_mb: float = None):
    """装饰器: 性能测试限制"""
    def decorator(test_func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                result = test_func(*args, **kwargs)
                
                elapsed = time.time() - start_time
                if max_time and elapsed > max_time:
                    raise AssertionError(f"性能测试失败: 耗时{elapsed:.2f}s > {max_time}s")
                
                return result
                
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"⚠️ 测试 {test_func.__name__} 异常 (耗时{elapsed:.2f}s): {e}")
                raise
        return wrapper
    return decorator

# 初始化测试环境
def setup_test_environment():
    """设置测试环境"""
    # 创建必要目录
    TestHelpers.create_test_directories()
    
    # 设置日志
    import logging
    log_level = getattr(logging, ENV_CONFIG["log_level"].upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOGS_ROOT / "tests" / "test.log"),
            logging.StreamHandler()
        ]
    )
    
    print(f"✅ 测试环境已初始化")
    print(f"   项目根目录: {PROJECT_ROOT}")
    print(f"   测试目录: {TESTS_ROOT}")
    print(f"   日志级别: {ENV_CONFIG['log_level']}")
    print(f"   测试模式: {ENV_CONFIG['test_mode']}")

def teardown_test_environment():
    """清理测试环境"""
    TestHelpers.cleanup_test_files()
    print("✅ 测试环境已清理")

if __name__ == "__main__":
    # 测试配置文件
    setup_test_environment()
    
    print("\n📋 测试配置:")
    print(f"   测试股票: {TEST_CONFIG['test_symbols']}")
    print(f"   时间范围: {TEST_CONFIG['test_date_range']}")
    print(f"   启用的数据源: {[k for k, v in TEST_CONFIG['data_sources'].items() if v['enabled']]}")
    
    teardown_test_environment()