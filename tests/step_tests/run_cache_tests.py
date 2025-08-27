# -*- coding: utf-8 -*-
"""
增强版缓存模块测试脚本
---------------------------------
测试缓存功能（包括增强功能）：
1. 基本读写功能
2. TTL 过期机制
3. 缓存清理功能
4. 统计信息功能
5. 便捷接口
6. 多提供商支持
"""

import os
import sys
import time
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np

# 项目根目录加入 PYTHONPATH
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

# 导入缓存模块
from backend.data.cache import (
    make_ohlcv_cache_key, 
    cache_path_for, 
    get_df_if_fresh, 
    put_df,
    CACHE_ROOT
)

# 尝试导入增强功能（如果已添加）
try:
    from backend.data.cache import (
        clear_cache,
        get_cache_stats,
        cache_ohlcv_get,
        cache_ohlcv_put
    )
    HAS_ENHANCEMENTS = True
except ImportError:
    HAS_ENHANCEMENTS = False
    print("注意: 未检测到增强功能，将跳过相关测试")


def create_test_data(symbol: str = "TEST001", days: int = 10, base_price: float = 100.0) -> pd.DataFrame:
    """创建测试用的OHLCV数据"""
    dates = pd.date_range("2024-01-01", periods=days, freq="B")  # 工作日
    
    # 简单随机游走（使用不同的seed确保数据差异）
    seed = hash(symbol) % 1000
    np.random.seed(seed)
    returns = np.random.normal(0.001, 0.02, days)
    prices = base_price * (1 + returns).cumprod()
    
    df = pd.DataFrame({
        "open": prices * 0.999,
        "high": prices * 1.002,
        "low": prices * 0.998,
        "close": prices,
        "volume": np.random.randint(10000, 100000, days),
    }, index=dates)
    
    return df


def test_cache_key_generation():
    """测试缓存键生成"""
    print("测试1: 缓存键生成")
    
    # 基本键生成
    key = make_ohlcv_cache_key("TEST001", "2024-01-01", "2024-01-10", "1d", "akshare")
    expected = "ohlcv_akshare_TEST001_2024-01-01_2024-01-10_1d.csv"
    assert key == expected, f"缓存键不匹配: {key} != {expected}"
    
    # 测试特殊字符清理
    key2 = make_ohlcv_cache_key("TEST/001", "2024-01-01", "2024-01-10", "1d", "ak-share")
    assert "/" not in key2, "缓存键包含非法字符"
    
    # 测试None值处理
    key3 = make_ohlcv_cache_key("TEST001", None, None, "1d", "provider")
    assert "none" in key3.lower(), "None值未正确处理"
    
    print("✓ 缓存键生成正常")


def test_basic_read_write():
    """测试基本读写功能"""
    print("测试2: 基本读写功能")
    
    # 使用临时目录避免污染实际缓存
    original_cache_root = CACHE_ROOT
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 临时修改缓存根目录
        import backend.data.cache as cache_module
        cache_module.CACHE_ROOT = Path(tmp_dir)
        
        try:
            # 创建测试数据
            test_data = create_test_data("TEST001", 10)
            
            # 生成缓存键
            key = make_ohlcv_cache_key("TEST001", "2024-01-01", "2024-01-10", "1d", "akshare")
            
            # 写入缓存
            cache_file = put_df(key, test_data)
            assert cache_file.exists(), "缓存文件未创建"
            
            # 读取缓存（设置很长的 TTL）
            cached_data = get_df_if_fresh(key, max_age_seconds=3600)
            assert cached_data is not None, "读取缓存失败"
            
            # 验证数据完整性
            pd.testing.assert_frame_equal(test_data, cached_data, check_dtype=False, check_freq=False)
            
            # 验证列顺序
            expected_columns = ["open", "high", "low", "close", "volume"]
            assert list(cached_data.columns) == expected_columns, "列顺序不正确"
            
            print("✓ 基本读写功能正常")
            
        finally:
            # 恢复原始缓存根目录
            cache_module.CACHE_ROOT = original_cache_root


def test_ttl_expiration():
    """测试TTL过期机制"""
    print("测试3: TTL过期机制")
    
    original_cache_root = CACHE_ROOT
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        import backend.data.cache as cache_module
        cache_module.CACHE_ROOT = Path(tmp_dir)
        
        try:
            test_data = create_test_data("TEST002", 5)
            key = make_ohlcv_cache_key("TEST002", "2024-01-01", "2024-01-05", "1d", "tushare")
            
            # 写入缓存
            put_df(key, test_data)
            
            # 立即读取应该成功
            cached_data = get_df_if_fresh(key, max_age_seconds=10)
            assert cached_data is not None, "立即读取缓存失败"
            
            # 等待一点时间
            time.sleep(0.1)
            
            # 设置很短的 TTL，应该过期
            expired_data = get_df_if_fresh(key, max_age_seconds=0)
            assert expired_data is None, "过期缓存仍能读取"
            
            # 设置足够长的TTL，应该能读取
            fresh_data = get_df_if_fresh(key, max_age_seconds=60)
            assert fresh_data is not None, "未过期缓存无法读取"
            
            print("✓ TTL过期机制正常")
            
        finally:
            cache_module.CACHE_ROOT = original_cache_root


def test_file_path_generation():
    """测试文件路径生成"""
    print("测试4: 文件路径生成")
    
    key = "test_file.csv"
    path = cache_path_for(key)
    
    # 检查路径结构
    assert "ohlcv" in str(path), "缓存路径应包含 ohlcv 子目录"
    assert path.name == key, f"文件名不匹配: {path.name} != {key}"
    
    # 检查目录会被自动创建
    # 这里不实际创建，只检查逻辑
    assert path.parent.name == "ohlcv", "父目录应为 ohlcv"
    
    print("✓ 文件路径生成正常")


def test_data_format_consistency():
    """测试数据格式一致性"""
    print("测试5: 数据格式一致性")
    
    original_cache_root = CACHE_ROOT
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        import backend.data.cache as cache_module
        cache_module.CACHE_ROOT = Path(tmp_dir)
        
        try:
            # 创建包含不同数据类型的测试数据
            dates = pd.date_range("2024-01-01", periods=3, freq="D")
            test_data = pd.DataFrame({
                "open": [100.1, 101.2, 102.3],
                "high": [100.5, 101.6, 102.7],
                "low": [99.8, 100.9, 102.0],
                "close": [100.2, 101.3, 102.4],
                "volume": [10000.0, 20000.0, 30000.0],  # 确保是浮点数
            }, index=dates)
            
            key = make_ohlcv_cache_key("TEST003", "2024-01-01", "2024-01-03", "1d", "test")
            
            # 写入和读取
            put_df(key, test_data)
            cached_data = get_df_if_fresh(key, max_age_seconds=3600)
            
            # 验证列名和数据类型
            expected_columns = ["open", "high", "low", "close", "volume"]
            assert list(cached_data.columns) == expected_columns, f"列名不匹配: {list(cached_data.columns)}"
            
            # 验证索引是日期类型
            assert isinstance(cached_data.index, pd.DatetimeIndex), "索引应为 DatetimeIndex"
            
            # 验证数值近似相等（浮点精度问题）
            np.testing.assert_array_almost_equal(test_data.values, cached_data.values, decimal=6)
            
            print("✓ 数据格式一致性正常")
            
        finally:
            cache_module.CACHE_ROOT = original_cache_root


def test_missing_file_handling():
    """测试缺失文件处理"""
    print("测试6: 缺失文件处理")
    
    # 尝试读取不存在的缓存
    nonexistent_key = "nonexistent_file_12345.csv"
    result = get_df_if_fresh(nonexistent_key, max_age_seconds=3600)
    assert result is None, "不存在的缓存应返回 None"
    
    print("✓ 缺失文件处理正常")


def test_enhancement_functions():
    """测试增强功能"""
    if not HAS_ENHANCEMENTS:
        print("测试7-10: 跳过增强功能测试（未实现）")
        return
    
    print("测试7: 便捷接口功能")
    test_convenience_functions()
    
    print("测试8: 缓存统计功能")
    test_cache_stats()
    
    print("测试9: 缓存清理功能")
    test_cache_cleanup()
    
    print("测试10: 多提供商支持")
    test_multi_provider()


def test_convenience_functions():
    """测试便捷接口"""
    original_cache_root = CACHE_ROOT
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        import backend.data.cache as cache_module
        cache_module.CACHE_ROOT = Path(tmp_dir)
        
        try:
            test_data = create_test_data("CONV001", 5)
            
            # 使用便捷写入接口
            cache_file = cache_ohlcv_put(test_data, "CONV001", "2024-01-01", "2024-01-05", "1d", "convenient")
            assert cache_file.exists(), "便捷写入失败"
            
            # 使用便捷读取接口
            cached_data = cache_ohlcv_get("CONV001", "2024-01-01", "2024-01-05", "1d", "convenient", max_age_hours=1)
            assert cached_data is not None, "便捷读取失败"
            
            pd.testing.assert_frame_equal(test_data, cached_data, check_dtype=False, check_freq=False)
            
            # 测试过期
            expired_data = cache_ohlcv_get("CONV001", "2024-01-01", "2024-01-05", "1d", "convenient", max_age_hours=0)
            assert expired_data is None, "过期数据仍能读取"
            
            print("✓ 便捷接口功能正常")
            
        finally:
            cache_module.CACHE_ROOT = original_cache_root


def test_cache_stats():
    """测试缓存统计功能"""
    original_cache_root = CACHE_ROOT
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        import backend.data.cache as cache_module
        cache_module.CACHE_ROOT = Path(tmp_dir)
        
        try:
            # 创建多个不同提供商的缓存文件
            providers = ["akshare", "tushare", "yahoo"]
            symbols = ["STOCK001", "STOCK002"]
            
            for provider in providers:
                for symbol in symbols:
                    test_data = create_test_data(symbol, 3)
                    cache_ohlcv_put(test_data, symbol, "2024-01-01", "2024-01-03", "1d", provider)
            
            # 获取统计信息
            stats = get_cache_stats()
            
            # 验证统计信息
            assert stats["total_files"] == len(providers) * len(symbols), f"文件数不正确: {stats['total_files']}"
            assert stats["total_size_mb"] >= 0, f"总大小应>=0，实际: {stats['total_size_mb']}"
            # 验证文件确实存在（即使大小很小）
            assert stats["total_files"] > 0, "应该有文件存在"
            assert len(stats["providers"]) == len(providers), f"提供商数量不正确: {len(stats['providers'])}"
            
            for provider in providers:
                assert stats["providers"][provider] == len(symbols), f"提供商 {provider} 文件数不正确"
            
            print(f"✓ 缓存统计功能正常 (总文件: {stats['total_files']}, 大小: {stats['total_size_mb']:.3f}MB)")
            
        finally:
            cache_module.CACHE_ROOT = original_cache_root


def test_cache_cleanup():
    """测试缓存清理功能"""
    original_cache_root = CACHE_ROOT
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        import backend.data.cache as cache_module
        cache_module.CACHE_ROOT = Path(tmp_dir)
        
        try:
            # 创建多个缓存文件
            test_data1 = create_test_data("CLEAN001", 3)
            test_data2 = create_test_data("CLEAN002", 3)
            
            cache_ohlcv_put(test_data1, "CLEAN001", "2024-01-01", "2024-01-03", "1d", "akshare")
            cache_ohlcv_put(test_data2, "CLEAN002", "2024-01-01", "2024-01-03", "1d", "tushare")
            
            # 获取初始统计
            initial_stats = get_cache_stats()
            assert initial_stats["total_files"] == 2, "初始文件数应为2"
            
            # 清理指定提供商
            cleared_akshare = clear_cache(provider="akshare")
            assert cleared_akshare == 1, f"应清理1个akshare文件，实际清理: {cleared_akshare}"
            
            # 验证只剩下tushare文件
            after_provider_clean = get_cache_stats()
            assert after_provider_clean["total_files"] == 1, "应剩余1个文件"
            assert "tushare" in after_provider_clean["providers"], "应还有tushare文件"
            assert "akshare" not in after_provider_clean["providers"], "不应有akshare文件"
            
            # 清理所有文件
            cleared_all = clear_cache()
            assert cleared_all == 1, "应清理剩余的1个文件"
            
            # 验证全部清理
            final_stats = get_cache_stats()
            assert final_stats["total_files"] == 0, "应无文件剩余"
            
            print("✓ 缓存清理功能正常")
            
        finally:
            cache_module.CACHE_ROOT = original_cache_root


def test_multi_provider():
    """测试多提供商支持"""
    original_cache_root = CACHE_ROOT
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        import backend.data.cache as cache_module
        cache_module.CACHE_ROOT = Path(tmp_dir)
        
        try:
            # 同一个股票，不同提供商的数据
            symbol = "MULTI001"
            date_range = ("2024-01-01", "2024-01-03")
            
            data_akshare = create_test_data(symbol + "_AK", 3, 100.0)
            data_tushare = create_test_data(symbol + "_TS", 3, 101.0)  # 略不同的价格
            
            # 写入不同提供商的缓存
            cache_ohlcv_put(data_akshare, symbol, date_range[0], date_range[1], "1d", "akshare")
            cache_ohlcv_put(data_tushare, symbol, date_range[0], date_range[1], "1d", "tushare")
            
            # 读取不同提供商的缓存
            cached_akshare = cache_ohlcv_get(symbol, date_range[0], date_range[1], "1d", "akshare")
            cached_tushare = cache_ohlcv_get(symbol, date_range[0], date_range[1], "1d", "tushare")
            
            assert cached_akshare is not None, "akshare缓存读取失败"
            assert cached_tushare is not None, "tushare缓存读取失败"
            
            # 验证数据独立性
            pd.testing.assert_frame_equal(data_akshare, cached_akshare, check_dtype=False, check_freq=False)
            pd.testing.assert_frame_equal(data_tushare, cached_tushare, check_dtype=False, check_freq=False)
            
            # 验证数据确实不同
            assert not np.allclose(cached_akshare["close"].values, cached_tushare["close"].values), "不同提供商数据应该不同"
            
            print("✓ 多提供商支持正常")
            
        finally:
            cache_module.CACHE_ROOT = original_cache_root


def main():
    print("开始增强版缓存模块测试...")
    print(f"增强功能可用: {HAS_ENHANCEMENTS}")
    
    # 基础功能测试
    basic_tests = [
        test_cache_key_generation,
        test_basic_read_write,
        test_ttl_expiration,
        test_file_path_generation,
        test_data_format_consistency,
        test_missing_file_handling,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in basic_tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} 失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # 增强功能测试
    if HAS_ENHANCEMENTS:
        try:
            test_enhancement_functions()
            passed += 4  # 增强功能包含4个子测试
        except Exception as e:
            print(f"✗ 增强功能测试失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 4
    else:
        print("跳过增强功能测试")
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    total_tests = 6 + (4 if HAS_ENHANCEMENTS else 0)
    print(f"总计: {total_tests}")
    
    if failed == 0:
        print("[PASS] cache.enhanced" if HAS_ENHANCEMENTS else "[PASS] cache.basic")
        return True
    else:
        print("[FAIL] cache.enhanced" if HAS_ENHANCEMENTS else "[FAIL] cache.basic")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)