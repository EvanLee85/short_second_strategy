# -*- coding: utf-8 -*-
"""
Zipline CSV导出模块
---------------------------------
用途：
  - 把"统一入口的 DataFrame"写到 data/zipline_csv/，用于 zipline ingest -b sss_csv
  - 列名/日期格式完全匹配 Zipline 的 csvdir_equities 规范
  - 按 XSHG 会话确保长度一致，避免 Missing/Extra sessions 错误

Zipline csvdir_equities 规范：
  - 文件名：{SYMBOL}.csv (如 000001.csv)
  - 必需列：date,open,high,low,close,volume
  - 日期格式：YYYY-MM-DD
  - 数值列：float 类型，不能有 NaN
  - 索引：第一列必须是 date，但不作为 pandas index
  - 排序：按日期升序
  - 会话对齐：必须与交易日历完全一致
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

import pandas as pd
import numpy as np

try:
    from loguru import logger
except ImportError:
    import logging as logger

# 导入依赖模块
from backend.data.fetcher import get_ohlcv
from backend.data.normalize import get_sessions_index


class ZiplineExporter:
    """
    Zipline CSV导出器
    
    职责：
    1. 从统一数据入口获取标准化数据
    2. 转换为 Zipline csvdir_equities 格式
    3. 确保与交易日历完全对齐
    4. 验证数据质量和格式规范
    """
    
    def __init__(
        self,
        output_dir: str = "data/zipline_csv",
        calendar_name: str = "XSHG",
        validate_data: bool = True,
        overwrite_existing: bool = True
    ):
        """
        初始化导出器
        
        参数：
          output_dir        : 输出目录
          calendar_name     : 交易日历名称
          validate_data     : 是否验证数据质量
          overwrite_existing: 是否覆盖已存在的文件
        """
        self.output_dir = Path(output_dir)
        self.calendar_name = calendar_name
        self.validate_data = validate_data
        self.overwrite_existing = overwrite_existing
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ZiplineExporter 初始化: {self.output_dir}")

    def _validate_ohlcv_data(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        验证和清理 OHLCV 数据
        
        参数：
          df     : 原始数据
          symbol : 标的代码
          
        返回：
          清理后的数据
        """
        if df.empty:
            logger.warning(f"数据为空: {symbol}")
            return df
        
        # 1. 基本列检查
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"{symbol}: 缺少必需列 {missing_cols}")
        
        # 2. 数值类型转换
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 3. 检查并处理 NaN 值
        nan_rows = df.isnull().any(axis=1)
        if nan_rows.any():
            logger.warning(f"{symbol}: 发现 {nan_rows.sum()} 行包含 NaN，将被移除")
            df = df.dropna()
        
        if df.empty:
            logger.warning(f"{symbol}: 清理后数据为空")
            return df
        
        # 4. OHLC 关系验证
        if self.validate_data:
            # 验证 high >= max(open, close) 和 low <= min(open, close)
            invalid_high = df['high'] < df[['open', 'close']].max(axis=1)
            invalid_low = df['low'] > df[['open', 'close']].min(axis=1)
            
            if invalid_high.any():
                logger.warning(f"{symbol}: {invalid_high.sum()} 行 high 价格异常")
                # 修正异常值
                df.loc[invalid_high, 'high'] = df.loc[invalid_high, ['open', 'close']].max(axis=1) * 1.001
            
            if invalid_low.any():
                logger.warning(f"{symbol}: {invalid_low.sum()} 行 low 价格异常")
                # 修正异常值
                df.loc[invalid_low, 'low'] = df.loc[invalid_low, ['open', 'close']].min(axis=1) * 0.999
        
        # 5. 成交量验证
        if (df['volume'] < 0).any():
            logger.warning(f"{symbol}: 发现负成交量，将设为0")
            df.loc[df['volume'] < 0, 'volume'] = 0
        
        # 6. 数值精度规范化
        # 价格保留4位小数，成交量取整
        price_cols = ['open', 'high', 'low', 'close']
        df[price_cols] = df[price_cols].round(4)
        df['volume'] = df['volume'].round(0).astype('int64')
        
        return df

    def _align_to_trading_sessions(
        self, 
        df: pd.DataFrame, 
        start_date: str, 
        end_date: str, 
        symbol: str
    ) -> pd.DataFrame:
        """
        对齐到交易日历会话
        
        确保生成的CSV与Zipline期望的交易日历完全一致
        """
        # 获取交易日历
        try:
            sessions = get_sessions_index(start_date, end_date, self.calendar_name)
        except Exception as e:
            logger.warning(f"获取交易日历失败: {e}, 使用工作日近似")
            sessions = pd.bdate_range(start_date, end_date, freq='B')
        
        if sessions.tz is not None:
            sessions = sessions.tz_localize(None)
        
        # 重建索引到完整交易日历
        df_aligned = df.reindex(sessions)
        
        # 处理缺失数据
        missing_sessions = df_aligned['close'].isnull()
        if missing_sessions.any():
            missing_count = missing_sessions.sum()
            logger.info(f"{symbol}: 补齐 {missing_count} 个缺失交易日")
            
            # 使用前向填充补齐价格（停牌日逻辑）
            df_aligned[['open', 'high', 'low', 'close']] = df_aligned[['open', 'high', 'low', 'close']].ffill()
            
            # 缺失日成交量设为0
            df_aligned['volume'] = df_aligned['volume'].fillna(0)
            
            # 如果前向填充仍有NaN（开头缺失），用后向填充
            df_aligned[['open', 'high', 'low', 'close']] = df_aligned[['open', 'high', 'low', 'close']].bfill()
        
        # 最终检查
        if df_aligned.isnull().any().any():
            logger.error(f"{symbol}: 对齐后仍有NaN值，可能是数据质量问题")
            df_aligned = df_aligned.dropna()
        
        return df_aligned

    def _format_for_zipline(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        格式化为 Zipline csvdir_equities 格式
        
        Zipline 要求：
        - 列顺序：date,open,high,low,close,volume
        - date 列格式：YYYY-MM-DD 字符串
        - 不使用 pandas index
        - 按日期升序排列
        """
        if df.empty:
            # 返回空但结构正确的DataFrame
            return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        
        # 重置索引，将日期作为普通列
        zipline_df = df.reset_index()
        
        # 确保日期列名为 'date'
        if 'index' in zipline_df.columns:
            zipline_df = zipline_df.rename(columns={'index': 'date'})
        elif zipline_df.index.name and zipline_df.index.name != 'date':
            zipline_df = zipline_df.reset_index().rename(columns={zipline_df.index.name: 'date'})
        
        # 确保有date列
        if 'date' not in zipline_df.columns:
            logger.error(f"{symbol}: 无法识别日期列")
            raise ValueError(f"{symbol}: DataFrame必须有日期索引或date列")
        
        # 日期格式标准化
        zipline_df['date'] = pd.to_datetime(zipline_df['date']).dt.strftime('%Y-%m-%d')
        
        # 确保列顺序和类型
        zipline_df = zipline_df[['date', 'open', 'high', 'low', 'close', 'volume']].copy()
        
        # 确保数值列类型正确
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            zipline_df[col] = pd.to_numeric(zipline_df[col], errors='coerce')
        
        # 按日期排序
        zipline_df = zipline_df.sort_values('date').reset_index(drop=True)
        
        # 最终验证
        if zipline_df['date'].isnull().any():
            raise ValueError(f"{symbol}: 日期列包含无效值")
        
        if zipline_df[numeric_cols].isnull().any().any():
            logger.warning(f"{symbol}: 数值列包含NaN")
        
        return zipline_df

    def export_single_symbol(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        freq: str = "1d",
        adjust: str = "pre"
    ) -> bool:
        """
        导出单个标的到Zipline CSV
        
        参数：
          symbol     : 标的代码
          start_date : 开始日期 'YYYY-MM-DD'
          end_date   : 结束日期 'YYYY-MM-DD'
          freq       : 数据频率
          adjust     : 复权类型
          
        返回：
          是否成功导出
        """
        try:
            logger.info(f"开始导出 {symbol}: {start_date} ~ {end_date}")
            
            # 1. 从统一入口获取数据
            df = get_ohlcv(symbol, start_date, end_date, freq, adjust)
            
            if df.empty:
                logger.warning(f"获取数据为空: {symbol}")
                return False
            
            # 2. 数据验证和清理
            df = self._validate_ohlcv_data(df, symbol)
            if df.empty:
                logger.warning(f"验证后数据为空: {symbol}")
                return False
            
            # 3. 对齐到交易日历
            df = self._align_to_trading_sessions(df, start_date, end_date, symbol)
            if df.empty:
                logger.warning(f"对齐后数据为空: {symbol}")
                return False
            
            # 4. 格式化为Zipline格式
            zipline_df = self._format_for_zipline(df, symbol)
            if zipline_df.empty:
                logger.warning(f"格式化后数据为空: {symbol}")
                return False
            
            # 5. 生成文件名（使用代码主体，去掉交易所后缀）
            clean_symbol = symbol.split('.')[0].upper()
            output_file = self.output_dir / f"{clean_symbol}.csv"
            
            # 6. 检查是否覆盖
            if output_file.exists() and not self.overwrite_existing:
                logger.info(f"文件已存在，跳过: {output_file}")
                return True
            
            # 7. 写入CSV文件
            zipline_df.to_csv(output_file, index=False, float_format='%.4f')
            
            logger.info(f"导出成功: {output_file} ({len(zipline_df)} 行)")
            return True
            
        except Exception as e:
            logger.error(f"导出 {symbol} 失败: {e}")
            return False

    def export_batch(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        freq: str = "1d",
        adjust: str = "pre",
        max_failures: int = 5
    ) -> Dict[str, bool]:
        """
        批量导出多个标的
        
        参数：
          symbols     : 标的代码列表
          start_date  : 开始日期
          end_date    : 结束日期
          freq        : 数据频率
          adjust      : 复权类型
          max_failures: 最大失败数，超过则停止
          
        返回：
          {symbol: success} 导出结果字典
        """
        results = {}
        failures = 0
        
        logger.info(f"开始批量导出: {len(symbols)} 个标的")
        
        for i, symbol in enumerate(symbols, 1):
            try:
                success = self.export_single_symbol(symbol, start_date, end_date, freq, adjust)
                results[symbol] = success
                
                if not success:
                    failures += 1
                    if failures > max_failures:
                        logger.error(f"失败次数超过限制 ({max_failures})，停止批量导出")
                        break
                
                # 进度提示
                if i % 10 == 0 or i == len(symbols):
                    success_count = sum(results.values())
                    logger.info(f"进度: {i}/{len(symbols)}, 成功: {success_count}, 失败: {i - success_count}")
                    
            except KeyboardInterrupt:
                logger.info("用户中断批量导出")
                break
            except Exception as e:
                logger.error(f"批量导出异常: {symbol}, 错误: {e}")
                results[symbol] = False
                failures += 1
        
        success_count = sum(results.values())
        logger.info(f"批量导出完成: 总计 {len(results)}, 成功 {success_count}, 失败 {len(results) - success_count}")
        
        return results

    def validate_zipline_compatibility(self, check_sample: int = 5) -> bool:
        """
        验证导出文件与Zipline兼容性
        
        参数：
          check_sample: 检查的样本文件数量
          
        返回：
          是否兼容
        """
        csv_files = list(self.output_dir.glob("*.csv"))
        if not csv_files:
            logger.warning("输出目录中没有CSV文件")
            return False
        
        # 随机选择样本文件检查
        import random
        sample_files = random.sample(csv_files, min(check_sample, len(csv_files)))
        
        all_valid = True
        
        for csv_file in sample_files:
            try:
                # 读取文件
                df = pd.read_csv(csv_file)
                
                # 检查必需列
                required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
                if list(df.columns) != required_cols:
                    logger.error(f"文件列名不符合规范: {csv_file}")
                    logger.error(f"期望: {required_cols}")
                    logger.error(f"实际: {list(df.columns)}")
                    all_valid = False
                    continue
                
                # 检查日期格式
                try:
                    pd.to_datetime(df['date'], format='%Y-%m-%d')
                except:
                    logger.error(f"日期格式不正确: {csv_file}")
                    all_valid = False
                    continue
                
                # 检查数据类型
                numeric_cols = ['open', 'high', 'low', 'close', 'volume']
                for col in numeric_cols:
                    if not pd.api.types.is_numeric_dtype(df[col]):
                        logger.error(f"列 {col} 不是数值类型: {csv_file}")
                        all_valid = False
                        break
                
                # 检查NaN值
                if df.isnull().any().any():
                    logger.error(f"文件包含NaN值: {csv_file}")
                    all_valid = False
                    continue
                
                logger.debug(f"文件格式正确: {csv_file}")
                
            except Exception as e:
                logger.error(f"验证文件失败: {csv_file}, 错误: {e}")
                all_valid = False
        
        if all_valid:
            logger.info("Zipline兼容性验证通过")
        else:
            logger.error("Zipline兼容性验证失败")
        
        return all_valid


# 便捷函数
def export_for_zipline(
    symbols: Union[str, List[str]],
    start_date: str,
    end_date: str,
    output_dir: str = "data/zipline_csv",
    freq: str = "1d",
    adjust: str = "pre",
    calendar_name: str = "XSHG",
    validate: bool = True
) -> bool:
    """
    便捷函数：导出数据为Zipline CSV格式
    
    参数：
      symbols      : 标的代码（字符串或列表）
      start_date   : 开始日期
      end_date     : 结束日期  
      output_dir   : 输出目录
      freq         : 数据频率
      adjust       : 复权类型
      calendar_name: 交易日历
      validate     : 是否验证兼容性
      
    返回：
      是否成功
    """
    if isinstance(symbols, str):
        symbols = [symbols]
    
    exporter = ZiplineExporter(
        output_dir=output_dir,
        calendar_name=calendar_name,
        validate_data=True,
        overwrite_existing=True
    )
    
    # 批量导出
    results = exporter.export_batch(symbols, start_date, end_date, freq, adjust)
    
    # 验证兼容性
    if validate and results:
        exporter.validate_zipline_compatibility()
    
    # 返回是否全部成功
    return all(results.values()) if results else False


if __name__ == "__main__":
    # 使用示例
    
    # 1. 导出单只股票
    print("=== 单只股票导出示例 ===")
    exporter = ZiplineExporter()
    success = exporter.export_single_symbol("000001", "2024-01-01", "2024-01-31")
    print(f"导出结果: {success}")
    
    # 2. 批量导出
    print("\n=== 批量导出示例 ===")
    symbols = ["000001", "000002", "002415", "600000"]
    results = exporter.export_batch(symbols, "2024-01-01", "2024-01-31")
    print(f"批量导出结果: {results}")
    
    # 3. 验证兼容性
    print("\n=== 兼容性验证 ===")
    compatibility = exporter.validate_zipline_compatibility()
    print(f"Zipline兼容性: {compatibility}")
    
    # 4. 使用便捷函数
    print("\n=== 便捷函数示例 ===")
    success = export_for_zipline(
        symbols=["002415", "600519"],
        start_date="2024-01-01",
        end_date="2024-01-31"
    )
    print(f"便捷导出结果: {success}")