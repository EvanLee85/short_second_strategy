"""
数据获取门面类 - 无痛替换的关键组件
提供与原有CSV读取相同的接口，底层使用新的数据获取逻辑

设计原则:
1. 保持与原有接口完全兼容
2. 透明地处理数据源切换
3. 保留原有的错误处理和异常类型
4. 支持渐进式迁移
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Union, Dict, List, Any
from datetime import datetime, timedelta
import warnings
import logging

# 配置日志
logger = logging.getLogger(__name__)

class DataFetcherFacade:
    """
    数据获取门面类
    
    提供与原有CSV读取完全兼容的接口，内部使用新的数据获取器
    支持无缝替换原有的直接CSV读取逻辑
    """
    
    def __init__(self, 
                 enable_new_fetcher: bool = True,
                 fallback_to_csv: bool = True,
                 csv_data_path: Optional[str] = None):
        """
        初始化数据获取门面
        
        Args:
            enable_new_fetcher: 是否启用新的数据获取器
            fallback_to_csv: 新获取器失败时是否回退到CSV
            csv_data_path: CSV数据文件路径（用于回退）
        """
        self.enable_new_fetcher = enable_new_fetcher
        self.fallback_to_csv = fallback_to_csv
        self.csv_data_path = Path(csv_data_path) if csv_data_path else None
        
        # 懒加载数据获取器
        self._fetcher = None
        self._csv_cache = {}
        
        # 兼容性映射
        self._column_mapping = {
            # 新接口 -> 旧接口列名映射
            'datetime': 'date',
            'adj_close': 'close',  # 如果需要复权价格
        }
        
        # 性能统计
        self._stats = {
            'new_fetcher_calls': 0,
            'csv_fallback_calls': 0,
            'cache_hits': 0
        }
    
    @property
    def fetcher(self):
        """懒加载数据获取器"""
        if self._fetcher is None and self.enable_new_fetcher:
            try:
                # 这里导入新的数据获取器
                from data_sources.unified_fetcher import UnifiedDataFetcher
                self._fetcher = UnifiedDataFetcher()
                logger.info("新数据获取器初始化成功")
            except ImportError as e:
                logger.warning(f"无法导入新数据获取器: {e}")
                self._fetcher = None
        return self._fetcher
    
    def get_ohlcv(self, 
                  symbol: str, 
                  start_date: Optional[Union[str, datetime]] = None,
                  end_date: Optional[Union[str, datetime]] = None,
                  **kwargs) -> pd.DataFrame:
        """
        获取OHLCV数据 - 新的统一接口
        
        这是替换原有CSV读取的核心方法
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 额外参数，保持向后兼容
            
        Returns:
            pd.DataFrame: OHLCV数据，格式与原有CSV读取保持一致
        """
        try:
            # 尝试使用新的数据获取器
            if self.fetcher:
                logger.debug(f"使用新获取器获取数据: {symbol}")
                data = self._fetch_with_new_fetcher(symbol, start_date, end_date, **kwargs)
                if data is not None and not data.empty:
                    self._stats['new_fetcher_calls'] += 1
                    return self._normalize_output_format(data)
            
            # 回退到CSV读取
            if self.fallback_to_csv:
                logger.debug(f"回退到CSV读取: {symbol}")
                data = self._fetch_from_csv(symbol, start_date, end_date, **kwargs)
                if data is not None and not data.empty:
                    self._stats['csv_fallback_calls'] += 1
                    return data
            
            # 如果都失败了，返回空DataFrame但保持列结构
            logger.warning(f"所有数据源都失败，返回空DataFrame: {symbol}")
            return self._create_empty_dataframe()
            
        except Exception as e:
            logger.error(f"获取数据时发生异常: {symbol}, {e}")
            if self.fallback_to_csv:
                return self._fetch_from_csv(symbol, start_date, end_date, **kwargs)
            raise
    
    def _fetch_with_new_fetcher(self, 
                               symbol: str, 
                               start_date: Optional[Union[str, datetime]],
                               end_date: Optional[Union[str, datetime]],
                               **kwargs) -> Optional[pd.DataFrame]:
        """使用新数据获取器获取数据"""
        try:
            # 转换日期格式
            start_str = self._normalize_date(start_date)
            end_str = self._normalize_date(end_date)
            
            # 调用新的获取器
            data = self.fetcher.get_stock_data(
                symbol=symbol,
                start_date=start_str,
                end_date=end_str,
                **kwargs
            )
            
            return data
            
        except Exception as e:
            logger.warning(f"新数据获取器失败: {symbol}, {e}")
            return None
    
    def _fetch_from_csv(self, 
                       symbol: str,
                       start_date: Optional[Union[str, datetime]],
                       end_date: Optional[Union[str, datetime]],
                       **kwargs) -> pd.DataFrame:
        """从CSV文件读取数据 - 原有逻辑的包装"""
        try:
            # 构造CSV文件路径
            csv_file = self._get_csv_file_path(symbol)
            
            if not csv_file or not csv_file.exists():
                logger.warning(f"CSV文件不存在: {csv_file}")
                return self._create_empty_dataframe()
            
            # 检查缓存
            cache_key = f"{symbol}_{start_date}_{end_date}"
            if cache_key in self._csv_cache:
                self._stats['cache_hits'] += 1
                return self._csv_cache[cache_key].copy()
            
            # 读取CSV文件
            data = pd.read_csv(csv_file)
            
            # 标准化列名
            data = self._normalize_csv_columns(data)
            
            # 过滤日期范围
            if start_date or end_date:
                data = self._filter_date_range(data, start_date, end_date)
            
            # 缓存结果
            self._csv_cache[cache_key] = data.copy()
            
            return data
            
        except Exception as e:
            logger.error(f"CSV读取失败: {symbol}, {e}")
            return self._create_empty_dataframe()
    
    def _get_csv_file_path(self, symbol: str) -> Optional[Path]:
        """获取CSV文件路径"""
        if not self.csv_data_path:
            return None
        
        # 支持多种CSV文件命名规则
        possible_names = [
            f"{symbol}.csv",
            f"{symbol.replace('.', '_')}.csv",
            f"{symbol.lower()}.csv",
            f"{symbol.upper()}.csv"
        ]
        
        for name in possible_names:
            csv_file = self.csv_data_path / name
            if csv_file.exists():
                return csv_file
        
        return None
    
    def _normalize_date(self, date: Optional[Union[str, datetime]]) -> Optional[str]:
        """标准化日期格式"""
        if date is None:
            return None
        
        if isinstance(date, str):
            return date
        elif isinstance(date, datetime):
            return date.strftime('%Y-%m-%d')
        else:
            return str(date)
    
    def _normalize_csv_columns(self, data: pd.DataFrame) -> pd.DataFrame:
        """标准化CSV列名"""
        # 常见的列名映射
        column_mappings = {
            'Date': 'date',
            'DATE': 'date',
            'Datetime': 'date',
            'DATETIME': 'date',
            'Open': 'open',
            'OPEN': 'open',
            'High': 'high',
            'HIGH': 'high',
            'Low': 'low',
            'LOW': 'low',
            'Close': 'close',
            'CLOSE': 'close',
            'Volume': 'volume',
            'VOLUME': 'volume',
            'vol': 'volume'
        }
        
        # 重命名列
        data = data.rename(columns=column_mappings)
        
        # 确保日期列为datetime类型
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
        
        return data
    
    def _filter_date_range(self, 
                          data: pd.DataFrame,
                          start_date: Optional[Union[str, datetime]],
                          end_date: Optional[Union[str, datetime]]) -> pd.DataFrame:
        """过滤日期范围"""
        if 'date' not in data.columns:
            return data
        
        result = data.copy()
        
        if start_date:
            start_dt = pd.to_datetime(start_date)
            result = result[result['date'] >= start_dt]
        
        if end_date:
            end_dt = pd.to_datetime(end_date)
            result = result[result['date'] <= end_dt]
        
        return result.reset_index(drop=True)
    
    def _normalize_output_format(self, data: pd.DataFrame) -> pd.DataFrame:
        """标准化输出格式，确保与原有接口兼容"""
        if data.empty:
            return self._create_empty_dataframe()
        
        result = data.copy()
        
        # 应用列名映射
        reverse_mapping = {v: k for k, v in self._column_mapping.items()}
        result = result.rename(columns=reverse_mapping)
        
        # 确保必要列存在
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in result.columns:
                logger.warning(f"缺少必要列: {col}")
                # 可以选择填充默认值或者抛出异常
                if col == 'volume':
                    result[col] = 0
                else:
                    result[col] = np.nan
        
        # 确保数据类型正确
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in result.columns:
                result[col] = pd.to_numeric(result[col], errors='coerce')
        
        return result
    
    def _create_empty_dataframe(self) -> pd.DataFrame:
        """创建空的DataFrame，保持列结构一致"""
        return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    
    # === 兼容性方法 - 模拟原有的CSV读取接口 ===
    
    def read_csv(self, file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
        """
        兼容原有的read_csv接口
        
        这个方法保持与原有pandas.read_csv相同的签名，
        但内部可以选择使用新的数据源
        """
        file_path = Path(file_path)
        
        # 从文件名推断股票代码
        symbol = self._extract_symbol_from_filename(file_path.stem)
        
        if symbol and self.enable_new_fetcher:
            # 尝试使用新的获取器
            try:
                return self.get_ohlcv(symbol, **kwargs)
            except Exception as e:
                logger.warning(f"新获取器失败，回退到CSV: {e}")
        
        # 原有的CSV读取逻辑
        return pd.read_csv(file_path, **kwargs)
    
    def _extract_symbol_from_filename(self, filename: str) -> Optional[str]:
        """从文件名提取股票代码"""
        # 简单的提取逻辑，可以根据实际需求调整
        filename = filename.replace('_', '.')
        
        # 常见的股票代码模式
        import re
        patterns = [
            r'^(\d{6}\.(SZ|SH))$',  # 中国股票
            r'^([A-Z]{1,5})$',      # 美股
            r'^(\d{6})$',           # 纯数字代码
        ]
        
        for pattern in patterns:
            match = re.match(pattern, filename.upper())
            if match:
                return match.group(1)
        
        return None
    
    # === 性能和监控方法 ===
    
    def get_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        return {
            **self._stats,
            'cache_size': len(self._csv_cache),
            'new_fetcher_enabled': self.enable_new_fetcher,
            'fallback_enabled': self.fallback_to_csv
        }
    
    def clear_cache(self):
        """清空缓存"""
        self._csv_cache.clear()
        logger.info("CSV缓存已清空")
    
    def health_check(self) -> Dict[str, bool]:
        """健康检查"""
        health = {
            'new_fetcher_available': self.fetcher is not None,
            'csv_path_configured': self.csv_data_path is not None,
            'csv_path_exists': self.csv_data_path.exists() if self.csv_data_path else False
        }
        
        return health

# === 全局单例实例 ===

# 创建全局实例，供现有代码无缝切换使用
_global_fetcher_facade = None

def get_global_fetcher(csv_data_path: Optional[str] = None,
                      enable_new_fetcher: bool = True) -> DataFetcherFacade:
    """获取全局数据获取器实例"""
    global _global_fetcher_facade
    
    if _global_fetcher_facade is None:
        _global_fetcher_facade = DataFetcherFacade(
            enable_new_fetcher=enable_new_fetcher,
            fallback_to_csv=True,
            csv_data_path=csv_data_path
        )
    
    return _global_fetcher_facade

# === 便捷函数 - 直接替换原有的函数调用 ===

def get_ohlcv(symbol: str, 
              start_date: Optional[str] = None,
              end_date: Optional[str] = None,
              **kwargs) -> pd.DataFrame:
    """
    便捷函数：获取OHLCV数据
    
    这个函数可以直接替换原有的CSV读取调用
    """
    fetcher = get_global_fetcher()
    return fetcher.get_ohlcv(symbol, start_date, end_date, **kwargs)

def read_stock_csv(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """
    便捷函数：兼容原有的CSV读取
    
    可以直接替换 pd.read_csv(stock_file) 调用
    """
    fetcher = get_global_fetcher()
    return fetcher.read_csv(file_path, **kwargs)

# === 配置和初始化 ===

def configure_data_backend(csv_data_path: Optional[str] = None,
                          enable_new_fetcher: bool = True,
                          fallback_to_csv: bool = True):
    """
    配置数据后端
    
    在应用启动时调用此函数进行配置
    """
    global _global_fetcher_facade
    
    _global_fetcher_facade = DataFetcherFacade(
        enable_new_fetcher=enable_new_fetcher,
        fallback_to_csv=fallback_to_csv,
        csv_data_path=csv_data_path
    )
    
    logger.info(f"数据后端已配置: new_fetcher={enable_new_fetcher}, fallback={fallback_to_csv}")
    
    return _global_fetcher_facade

if __name__ == "__main__":
    # 测试代码
    import tempfile
    import os
    
    # 创建测试CSV文件
    with tempfile.TemporaryDirectory() as temp_dir:
        test_csv = Path(temp_dir) / "000001.SZ.csv"
        test_data = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=5),
            'open': [10.0, 10.5, 11.0, 10.8, 11.2],
            'high': [10.8, 11.2, 11.5, 11.3, 11.8],
            'low': [9.5, 10.0, 10.5, 10.3, 10.8],
            'close': [10.3, 10.8, 10.9, 11.1, 11.4],
            'volume': [1000000, 1200000, 1100000, 1300000, 1050000]
        })
        test_data.to_csv(test_csv, index=False)
        
        # 配置后端
        configure_data_backend(csv_data_path=temp_dir, enable_new_fetcher=False)
        
        # 测试获取数据
        data = get_ohlcv("000001.SZ")
        print("测试数据获取成功:")
        print(data.head())
        
        # 测试兼容性接口
        data2 = read_stock_csv(test_csv)
        print("\\n兼容性接口测试成功:")
        print(data2.head())
        
        # 获取统计信息
        stats = get_global_fetcher().get_stats()
        print(f"\\n使用统计: {stats}")
        
        # 健康检查
        health = get_global_fetcher().health_check()
        print(f"健康检查: {health}")
        
        print("\\n✅ 数据获取门面测试完成!")