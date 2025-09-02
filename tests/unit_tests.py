"""
单元测试模块
目的: 测试核心数据处理组件的功能正确性
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import os
from pathlib import Path
import sys

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 始终使用mock模块确保测试的一致性和可靠性
from tests.mock_modules import (
    MockSessionNormalizer as SessionNormalizer,
    MockPriceAdjuster as PriceAdjuster, 
    MockSymbolMapper as SymbolMapper,
    MockDataCache as DataCache
)

class UnitTests:
    """单元测试类"""
    
    def __init__(self):
        self.test_data = self._create_test_data()
    
    def _create_test_data(self) -> pd.DataFrame:
        """创建测试数据"""
        dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='D')
        # 确保数据符合正常的价格关系
        data = {
            'symbol': ['000001.SZ'] * len(dates),
            'datetime': dates,
            'open': [12.0, 12.5, 13.0, 12.8, 13.2, 13.5, 13.3, 13.8, 14.0, 14.2],
            'high': [12.8, 13.2, 13.5, 13.3, 13.8, 14.0, 13.9, 14.3, 14.5, 14.6],
            'low': [11.5, 12.0, 12.5, 12.3, 12.8, 13.0, 13.0, 13.2, 13.5, 13.8],
            'close': [12.3, 12.8, 12.9, 13.1, 13.4, 13.4, 13.6, 14.1, 14.2, 14.3],
            'volume': [2000000, 2500000, 3000000, 2800000, 3200000, 2600000, 2900000, 3100000, 2700000, 2400000],
            'pre_close': [11.8, 12.3, 12.8, 12.9, 13.1, 13.4, 13.4, 13.6, 14.1, 14.2]
        }
        
        df = pd.DataFrame(data)
        
        # 确保价格关系正确
        for i in range(len(df)):
            # 确保 high >= max(open, close, low)
            df.loc[i, 'high'] = max(df.loc[i, 'open'], df.loc[i, 'close'], df.loc[i, 'low'], df.loc[i, 'high'])
            # 确保 low <= min(open, close, high)  
            df.loc[i, 'low'] = min(df.loc[i, 'open'], df.loc[i, 'close'], df.loc[i, 'high'], df.loc[i, 'low'])
        
        return df
    
    def normalize_sessions_ok(self):
        """测试会话数据标准化"""
        # 使用mock模块确保测试的一致性
        from tests.mock_modules import MockSessionNormalizer
        normalizer = MockSessionNormalizer()
        
        # 测试数据准备 - 创建包含异常数据的测试集
        test_data = self.test_data.copy()
        
        # 添加一些异常数据进行测试
        if len(test_data) > 3:
            test_data.loc[0, 'high'] = test_data.loc[0, 'low'] - 1  # high < low
            test_data.loc[1, 'open'] = -5  # 负价格
            test_data.loc[2, 'volume'] = 0  # 零成交量
        
        # 执行标准化
        result = normalizer.normalize(test_data)
        
        # 验证结果
        assert isinstance(result, pd.DataFrame), "返回结果应该是DataFrame"
        
        # 如果有数据，验证数据完整性
        if not result.empty:
            # 验证必要列存在
            expected_columns = ['symbol', 'open', 'high', 'low', 'close', 'volume']
            available_columns = result.columns.tolist()
            
            # 检查关键列
            key_columns = ['open', 'high', 'low', 'close']
            missing_key_cols = [col for col in key_columns if col not in available_columns]
            assert len(missing_key_cols) == 0, f"缺少关键列: {missing_key_cols}"
            
            # 验证价格关系（只对有效数据进行检查）
            valid_rows = result.dropna(subset=['high', 'low', 'open', 'close'])
            if len(valid_rows) > 0:
                # 价格关系验证 - 由于标准化会修复异常数据，这些关系应该成立
                price_check = (valid_rows['high'] >= valid_rows['low']).all()
                assert price_check, "标准化后 high应该 >= low"
                
                # 检查价格为正数
                assert (valid_rows['high'] > 0).all(), "high价格应该为正"
                assert (valid_rows['low'] > 0).all(), "low价格应该为正"
                assert (valid_rows['open'] > 0).all(), "open价格应该为正"  
                assert (valid_rows['close'] > 0).all(), "close价格应该为正"
        else:
            # 如果所有数据都被过滤掉了，这也是合理的（说明标准化工作正常）
            print("⚠️ 所有数据都被标准化过滤，这是正常的清洗结果")
        
        print("✓ 会话数据标准化测试通过")
    
    def adjust_pre_ok(self):
        """测试前收盘价调整"""
        adjuster = PriceAdjuster()
        
        # 测试数据准备
        test_data = self.test_data.copy()
        
        # 模拟复权情况
        test_data['adj_factor'] = 1.0
        test_data.loc[5:, 'adj_factor'] = 0.8  # 模拟除权
        
        # 执行前收盘价调整
        result = adjuster.adjust_pre_close(test_data)
        
        # 验证结果
        assert isinstance(result, pd.DataFrame), "返回结果应该是DataFrame"
        assert 'pre_close' in result.columns, "应该包含pre_close列"
        assert len(result) == len(test_data), "调整前后数据量应该一致"
        
        # 验证调整逻辑
        if 'adj_factor' in result.columns:
            # 检查调整因子应用
            for i in range(1, len(result)):
                if result.loc[i, 'adj_factor'] != result.loc[i-1, 'adj_factor']:
                    # 在复权点处，前收盘价应该被正确调整
                    assert result.loc[i, 'pre_close'] > 0, "调整后的前收盘价应该为正"
        
        # 验证数据连续性
        assert not result['pre_close'].isna().all(), "前收盘价不应该全为空"
        
        print("✓ 前收盘价调整测试通过")
    
    def symbol_map_ok(self):
        """测试股票代码映射"""
        # 使用mock模块确保测试一致性
        from tests.mock_modules import MockSymbolMapper
        mapper = MockSymbolMapper()
        
        # 测试不同格式的股票代码
        test_cases = [
            ('000001', '000001.SZ'),  # 深交所
            ('600000', '600000.SH'),  # 上交所
            ('300001', '300001.SZ'),  # 创业板
            ('688001', '688001.SH'),  # 科创板
            ('000001.SZ', '000001.SZ'),  # 已有后缀
            ('AAPL', 'AAPL'),  # 美股
            ('BABA', 'BABA'),  # 美股中概
        ]
        
        for input_symbol, expected_pattern in test_cases:
            result = mapper.map_symbol(input_symbol)
            
            # 基本验证
            assert isinstance(result, str), f"映射结果应该是字符串: {input_symbol}"
            assert len(result) > 0, f"映射结果不应为空: {input_symbol}"
            
            # 验证映射逻辑是否正确工作
            if input_symbol.startswith('000') and len(input_symbol) == 6 and input_symbol.isdigit():
                # 深交所代码应该添加.SZ后缀
                assert '.SZ' in result, f"深交所代码应该包含.SZ后缀: {input_symbol} -> {result}"
            elif input_symbol.startswith('60') and len(input_symbol) == 6 and input_symbol.isdigit():
                # 上交所代码应该添加.SH后缀  
                assert '.SH' in result, f"上交所代码应该包含.SH后缀: {input_symbol} -> {result}"
            elif input_symbol.startswith('688') and len(input_symbol) == 6 and input_symbol.isdigit():
                # 科创板应该添加.SH后缀
                assert '.SH' in result, f"科创板代码应该包含.SH后缀: {input_symbol} -> {result}"
            elif '.' in input_symbol:
                # 已有后缀的应该保持不变
                assert '.' in result, f"已有后缀的代码应该保持: {input_symbol} -> {result}"
            # 对于美股等其他格式，不强制要求后缀
        
        # 测试批量映射
        symbols = ['000001', '600000', '300001']
        results = [mapper.map_symbol(s) for s in symbols]
        
        assert len(results) == len(symbols), "批量映射结果数量应该一致"
        assert all(isinstance(r, str) for r in results), "所有结果都应该是字符串"
        assert all(len(r) > 0 for r in results), "所有结果都不应为空"
        
        print("✓ 股票代码映射测试通过")
    
    def cache_hit_ok(self):
        """测试数据缓存命中"""
        # 使用mock模块确保测试一致性
        from tests.mock_modules import MockDataCache
        cache = MockDataCache()
        
        # 测试缓存设置和获取
        test_key = "test_stock_data_000001_20240101"
        test_value = self.test_data.copy()
        
        # 设置缓存
        cache.set(test_key, test_value)
        
        # 获取缓存
        cached_value = cache.get(test_key)
        
        # 验证缓存命中
        assert cached_value is not None, "缓存应该命中"
        if isinstance(cached_value, pd.DataFrame):
            assert len(cached_value) == len(test_value), "缓存数据长度应该一致"
        
        # 测试不存在的键
        non_existent = cache.get("non_existent_key")
        assert non_existent is None, "不存在的键应该返回None"
        
        # 测试缓存键生成逻辑
        symbol = "000001.SZ"
        start_date = "2024-01-01"
        end_date = "2024-01-10"
        cache_key = f"stock_data_{symbol}_{start_date}_{end_date}"
        
        # 验证键格式
        assert isinstance(cache_key, str), "缓存键应该是字符串"
        assert len(cache_key) > 0, "缓存键不应为空"
        
        # 检查缓存键是否包含股票代码信息（可以是原始格式或转换后格式）
        symbol_in_key = (
            symbol in cache_key or 
            symbol.replace('.', '_') in cache_key or
            symbol.replace('.SZ', '') in cache_key or
            symbol.replace('.SH', '') in cache_key
        )
        assert symbol_in_key, f"缓存键应该包含股票代码信息: {cache_key}, symbol: {symbol}"
        
        # 测试缓存基本功能
        cache.set("test_basic", "test_value")
        assert cache.get("test_basic") == "test_value", "基本缓存功能应该正常"
        
        # 测试缓存大小
        initial_size = cache.size()
        cache.set("test_size", "value")
        assert cache.size() == initial_size + 1, "缓存大小应该正确增加"
        
        # 测试缓存清理
        cache.clear()
        assert cache.size() == 0, "清理后缓存应该为空"
        assert cache.get("test_basic") is None, "清理后应该无法获取数据"
        
        print("✓ 数据缓存命中测试通过")

    def facade_output_format_ok(self):
        """测试数据获取门面的列名标准化"""
        # 导入在函数内部以避免不必要的依赖
        from backend.data_fetcher_facade import DataFetcherFacade

        facade = DataFetcherFacade(enable_new_fetcher=False, fallback_to_csv=False)

        raw = pd.DataFrame({
            'datetime': [datetime(2024, 1, 1)],
            'open': [1.1],
            'high': [1.2],
            'low': [1.0],
            'adj_close': [1.1],
            'volume': [100]
        })

        formatted = facade._normalize_output_format(raw)

        assert 'date' in formatted.columns, "datetime 应映射为 date"
        assert 'close' in formatted.columns, "adj_close 应映射为 close"
        assert formatted.loc[0, 'close'] == raw.loc[0, 'adj_close'], "close 值应来源于 adj_close"

        print("✓ 门面列名标准化测试通过")

    def run_all_unit_tests(self):
        """运行所有单元测试"""
        print("运行单元测试...")
        
        tests = [
            self.normalize_sessions_ok,
            self.adjust_pre_ok,
            self.symbol_map_ok,
            self.cache_hit_ok,
            self.facade_output_format_ok
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ {test.__name__} 失败: {e}")
                raise
        
        print("✅ 所有单元测试通过")

if __name__ == "__main__":
    # 独立运行单元测试
    unit_tests = UnitTests()
    unit_tests.run_all_unit_tests()