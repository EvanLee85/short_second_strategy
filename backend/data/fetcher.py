# -*- coding: utf-8 -*-
"""
统一数据入口（fetcher）
---------------------------------
用途：
  - 上层只用一个入口，不直接依赖具体 Provider
  - 读取配置→按优先级逐源拉数→规范化→合并→缓存→返回
  - 面向后端与回测的公共 API

核心接口：
  - get_ohlcv(symbol, start, end, freq="1d", adjust="pre") -> DataFrame
  - write_zipline_csv(symbols, start, end, out_dir) -> None

依赖：
  - providers (akshare/tushare/csv)
  - merge (多源合并)
  - cache (本地缓存)
  - normalize (数据规范化)
"""

from __future__ import annotations

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field

import pandas as pd

try:
    from loguru import logger
except ImportError:
    import logging as logger

# 导入各数据模块
from backend.data.providers.akshare_provider import AkshareProvider
from backend.data.providers.tushare_provider import TuShareProvider
from backend.data.providers.csv_provider import CsvProvider
from backend.data.merge import merge_ohlcv
from backend.data.cache import cache_ohlcv_get, cache_ohlcv_put
from backend.data.normalize import to_internal


@dataclass
class FetchConfig:
    """数据获取配置"""
    # 提供商优先级配置
    provider_priority: List[str] = field(default_factory=lambda: ["akshare", "tushare", "csv"])
    
    # 提供商特定配置
    provider_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # 缓存配置
    enable_cache: bool = True
    cache_ttl_hours: Dict[str, int] = field(default_factory=lambda: {"1d": 1, "1h": 0.25, "1m": 0.1})
    
    # 合并配置
    conflict_threshold: float = 0.02  # 2%差异视为冲突
    freshness_tolerance_days: int = 3
    
    # 默认参数
    default_calendar: str = "XSHG"
    default_exchange: str = "XSHE"
    
    @classmethod
    def from_yaml(cls, config_path: str) -> 'FetchConfig':
        """从YAML配置文件加载"""
        if not os.path.exists(config_path):
            logger.warning(f"配置文件不存在: {config_path}, 使用默认配置")
            return cls()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            return cls(
                provider_priority=data.get('provider_priority', cls().provider_priority),
                provider_configs=data.get('provider_configs', {}),
                enable_cache=data.get('enable_cache', True),
                cache_ttl_hours=data.get('cache_ttl_hours', cls().cache_ttl_hours),
                conflict_threshold=data.get('conflict_threshold', 0.02),
                freshness_tolerance_days=data.get('freshness_tolerance_days', 3),
                default_calendar=data.get('default_calendar', 'XSHG'),
                default_exchange=data.get('default_exchange', 'XSHE')
            )
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}, 使用默认配置")
            return cls()


class DataFetcher:
    """
    统一数据获取器
    
    职责：
    1. 管理多个数据提供商
    2. 按优先级获取数据并合并
    3. 处理缓存读写
    4. 提供统一接口
    """
    
    def __init__(self, config: Optional[FetchConfig] = None):
        """
        初始化数据获取器
        
        参数：
          config: 数据获取配置，None则使用默认配置
        """
        self.config = config or FetchConfig()
        self.providers = self._init_providers()
        
    def _init_providers(self) -> Dict[str, Any]:
        """初始化数据提供商"""
        providers = {}
        
        # 初始化各提供商
        for provider_name in self.config.provider_priority:
            try:
                provider_config = self.config.provider_configs.get(provider_name, {})
                
                if provider_name == "akshare":
                    providers[provider_name] = AkshareProvider(
                        calendar_name=self.config.default_calendar,
                        default_exchange=self.config.default_exchange,
                        **provider_config
                    )
                
                elif provider_name == "tushare":
                    providers[provider_name] = TuShareProvider(
                        calendar_name=self.config.default_calendar,
                        **provider_config
                    )
                
                elif provider_name == "csv":
                    providers[provider_name] = CsvProvider(
                        calendar_name=self.config.default_calendar,
                        **provider_config
                    )
                
                else:
                    logger.warning(f"未知的提供商: {provider_name}")
                    
            except Exception as e:
                logger.warning(f"初始化提供商 {provider_name} 失败: {e}")
        
        logger.info(f"已初始化提供商: {list(providers.keys())}")
        return providers
    
    def _fetch_from_provider(
        self, 
        provider_name: str, 
        symbol: str, 
        start: str, 
        end: str, 
        freq: str, 
        adjust: str
    ) -> Optional[pd.DataFrame]:
        """从指定提供商获取数据"""
        if provider_name not in self.providers:
            return None
        
        try:
            provider = self.providers[provider_name]
            df = provider.fetch_ohlcv(symbol, start, end, freq, adjust)
            
            if df is not None and not df.empty:
                logger.debug(f"从 {provider_name} 获取到 {len(df)} 条数据: {symbol}")
                return df
            else:
                logger.debug(f"{provider_name} 返回空数据: {symbol}")
                return None
                
        except Exception as e:
            logger.warning(f"从 {provider_name} 获取数据失败: {symbol}, 错误: {e}")
            return None
    
    def _get_cache_ttl(self, freq: str) -> int:
        """获取缓存TTL（小时）"""
        return self.config.cache_ttl_hours.get(freq, 1)
    
    def get_ohlcv(
        self,
        symbol: str,
        start: str,
        end: str,
        freq: str = "1d",
        adjust: str = "pre"
    ) -> pd.DataFrame:
        """
        获取OHLCV数据（统一入口）
        
        参数：
          symbol : 标的代码（支持多种格式，内部会统一化）
          start  : 开始日期 'YYYY-MM-DD'
          end    : 结束日期 'YYYY-MM-DD'
          freq   : 频率 ('1d', '1h', '1m')
          adjust : 复权类型 ('pre', 'post', 'none')
        
        返回：
          标准化的OHLCV DataFrame
          - 索引: DatetimeIndex (tz-naive)
          - 列: ['open', 'high', 'low', 'close', 'volume']
        
        流程：
          1. 标准化symbol
          2. 尝试从缓存读取
          3. 缓存未命中时，按优先级从各提供商获取
          4. 多源合并处理冲突
          5. 写入缓存
          6. 返回最终数据
        """
        # 1. 标准化symbol
        internal_symbol = to_internal(symbol, default_exchange=self.config.default_exchange)
        
        # 2. 尝试从缓存读取
        if self.config.enable_cache:
            ttl_hours = self._get_cache_ttl(freq)
            
            # 尝试从各提供商的缓存读取
            for provider_name in self.config.provider_priority:
                cached_df = cache_ohlcv_get(
                    internal_symbol, start, end, freq, provider_name, ttl_hours
                )
                if cached_df is not None:
                    logger.debug(f"缓存命中: {provider_name}/{internal_symbol}")
                    return cached_df
        
        # 3. 缓存未命中，从各提供商获取原始数据
        provider_data = {}
        for provider_name in self.config.provider_priority:
            df = self._fetch_from_provider(provider_name, internal_symbol, start, end, freq, adjust)
            if df is not None:
                provider_data[provider_name] = df
        
        if not provider_data:
            logger.warning(f"所有提供商都无法获取数据: {internal_symbol}")
            # 返回空但结构正确的DataFrame
            empty_index = pd.date_range(start, end, freq='D')[:0]  # 空的日期索引
            return pd.DataFrame(
                columns=['open', 'high', 'low', 'close', 'volume'],
                index=pd.DatetimeIndex([], name=None),
                dtype=float
            )
        
        # 4. 多源合并
        if len(provider_data) == 1:
            # 只有一个数据源，直接使用
            merged_df = list(provider_data.values())[0]
            primary_provider = list(provider_data.keys())[0]
        else:
            # 多个数据源，执行合并
            merged_df, merge_logs = merge_ohlcv(
                provider_data,
                start=start,
                end=end,
                calendar_name=self.config.default_calendar,
                prefer_order=self.config.provider_priority,
                conflict_close_pct=self.config.conflict_threshold,
                freshness_tolerance_days=self.config.freshness_tolerance_days
            )
            primary_provider = merge_logs.get('primary', self.config.provider_priority[0])
            
            # 记录合并日志
            if merge_logs.get('conflicts'):
                logger.info(f"数据合并发现 {len(merge_logs['conflicts'])} 个冲突: {internal_symbol}")
            if merge_logs.get('fallback_used', 0) > 0:
                logger.info(f"数据合并使用 {merge_logs['fallback_used']} 次回填: {internal_symbol}")
        
        # 5. 写入缓存
        if self.config.enable_cache and not merged_df.empty:
            try:
                cache_ohlcv_put(merged_df, internal_symbol, start, end, freq, primary_provider)
                logger.debug(f"数据已缓存: {primary_provider}/{internal_symbol}")
            except Exception as e:
                logger.warning(f"缓存写入失败: {e}")
        
        # 6. 返回最终数据
        logger.info(f"成功获取数据: {internal_symbol} ({len(merged_df)} 行, 主源: {primary_provider})")
        return merged_df
    
    def write_zipline_csv(
        self,
        symbols: Union[str, List[str]],
        start: str,
        end: str,
        out_dir: str,
        freq: str = "1d",
        adjust: str = "pre"
    ) -> None:
        """
        批量获取数据并写入Zipline CSV格式
        
        参数：
          symbols : 标的代码列表或单个代码
          start   : 开始日期
          end     : 结束日期  
          out_dir : 输出目录
          freq    : 频率
          adjust  : 复权类型
        
        输出格式：
          out_dir/SYMBOL.csv
          列: date,open,high,low,close,volume
        """
        if isinstance(symbols, str):
            symbols = [symbols]
        
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"开始生成Zipline CSV: {len(symbols)} 只股票 -> {out_dir}")
        
        for symbol in symbols:
            try:
                # 获取数据
                df = self.get_ohlcv(symbol, start, end, freq, adjust)
                
                if df.empty:
                    logger.warning(f"跳过空数据: {symbol}")
                    continue
                
                # 转换为Zipline格式
                # Zipline期望: 索引重置为列，列名为标准英文
                zipline_df = df.copy()
                zipline_df = zipline_df.reset_index()
                zipline_df = zipline_df.rename(columns={'index': 'date'})
                
                # 确保日期格式正确
                zipline_df['date'] = pd.to_datetime(zipline_df['date']).dt.strftime('%Y-%m-%d')
                
                # 保证列顺序
                zipline_df = zipline_df[['date', 'open', 'high', 'low', 'close', 'volume']]
                
                # 写入文件
                internal_symbol = to_internal(symbol, default_exchange=self.config.default_exchange)
                # 使用原始代码作为文件名（去掉交易所后缀）
                clean_symbol = internal_symbol.split('.')[0]
                output_file = out_path / f"{clean_symbol}.csv"
                
                zipline_df.to_csv(output_file, index=False)
                logger.info(f"已写入: {output_file} ({len(zipline_df)} 行)")
                
            except Exception as e:
                logger.error(f"处理 {symbol} 时出错: {e}")
        
        logger.info(f"Zipline CSV生成完成: {out_dir}")


# 全局默认实例
_default_fetcher: Optional[DataFetcher] = None


def get_default_fetcher(config_path: Optional[str] = None) -> DataFetcher:
    """获取默认的数据获取器实例（单例模式）"""
    global _default_fetcher
    
    if _default_fetcher is None:
        if config_path and os.path.exists(config_path):
            config = FetchConfig.from_yaml(config_path)
        else:
            # 尝试从默认位置加载配置
            default_config_path = "config/data_providers.yaml"
            if os.path.exists(default_config_path):
                config = FetchConfig.from_yaml(default_config_path)
            else:
                config = FetchConfig()  # 使用默认配置
        
        _default_fetcher = DataFetcher(config)
    
    return _default_fetcher


# 便捷函数（使用默认实例）
def get_ohlcv(
    symbol: str,
    start: str,
    end: str,
    freq: str = "1d",
    adjust: str = "pre"
) -> pd.DataFrame:
    """便捷函数：获取OHLCV数据"""
    return get_default_fetcher().get_ohlcv(symbol, start, end, freq, adjust)


def write_zipline_csv(
    symbols: Union[str, List[str]],
    start: str,
    end: str,
    out_dir: str,
    freq: str = "1d",
    adjust: str = "pre"
) -> None:
    """便捷函数：生成Zipline CSV文件"""
    get_default_fetcher().write_zipline_csv(symbols, start, end, out_dir, freq, adjust)


# 示例配置文件模板
EXAMPLE_CONFIG_YAML = """
# 数据提供商配置示例
# 保存为: config/data_providers.yaml

# 提供商优先级（越靠前优先级越高）
provider_priority:
  - akshare
  - tushare  
  - csv

# 各提供商特定配置
provider_configs:
  akshare:
    timeout: 15.0
    retries: 3
    volume_unit: hands  # 'hands' 或 'shares'
  
  tushare:
    # token 从环境变量 TUSHARE_TOKEN 读取
    timeout: 10.0
    max_retries: 2
  
  csv:
    csv_dir: "data/zipline_csv"
    allow_stub: true

# 缓存配置
enable_cache: true
cache_ttl_hours:
  1d: 1    # 日线缓存1小时
  1h: 0.25 # 小时线缓存15分钟
  1m: 0.1  # 分钟线缓存6分钟

# 合并配置
conflict_threshold: 0.02  # 2%差异视为冲突
freshness_tolerance_days: 3

# 默认设置
default_calendar: "XSHG"
default_exchange: "XSHE"
"""


if __name__ == "__main__":
    # 使用示例
    
    # 1. 基本使用
    print("=== 基本使用示例 ===")
    df = get_ohlcv("002415", "2024-01-01", "2024-01-10")
    print(f"获取到数据: {len(df)} 行")
    print(df.head())
    
    # 2. 批量生成Zipline CSV
    print("\n=== Zipline CSV生成示例 ===")
    symbols = ["002415", "600000", "000001"]
    write_zipline_csv(symbols, "2024-01-01", "2024-01-10", "data/zipline_csv")
    
    # 3. 显示配置模板
    print("\n=== 配置文件模板 ===")
    print(EXAMPLE_CONFIG_YAML)