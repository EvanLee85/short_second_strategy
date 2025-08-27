"""
Zipline CSV生成器 - write_zipline_csv()实现
替换原有的直接CSV生成逻辑，使用新的数据源获取数据并生成Zipline格式CSV

设计原则:
1. 保持与原有write_csv接口完全兼容  
2. 内部使用新的数据获取器
3. 支持批量生成和增量更新
4. 提供完整的错误处理和日志记录
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Union, Dict, List, Any, Tuple
from datetime import datetime, timedelta
import logging
import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# 配置日志
logger = logging.getLogger(__name__)

class ZiplineCsvWriter:
    """
    Zipline CSV生成器
    
    负责从新数据源获取数据并生成符合Zipline要求的CSV文件
    完全替换原有的CSV生成逻辑
    """
    
    def __init__(self, 
                 output_dir: Union[str, Path],
                 data_fetcher=None,
                 batch_size: int = 50,
                 max_workers: int = 4):
        """
        初始化Zipline CSV生成器
        
        Args:
            output_dir: CSV输出目录
            data_fetcher: 数据获取器实例，如果为None则使用默认获取器
            batch_size: 批处理大小
            max_workers: 最大并发工作线程数
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.batch_size = batch_size
        self.max_workers = max_workers
        
        # 懒加载数据获取器
        self._data_fetcher = data_fetcher
        
        # Zipline CSV格式要求
        self.zipline_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        self.zipline_dtypes = {
            'date': 'datetime64[ns]',
            'open': 'float64',
            'high': 'float64', 
            'low': 'float64',
            'close': 'float64',
            'volume': 'int64'
        }
        
        # 生成统计
        self.stats = {
            'files_generated': 0,
            'symbols_processed': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    @property
    def data_fetcher(self):
        """懒加载数据获取器"""
        if self._data_fetcher is None:
            try:
                from backend.data_fetcher_facade import get_global_fetcher
                self._data_fetcher = get_global_fetcher()
                logger.info("使用全局数据获取器")
            except ImportError:
                logger.warning("无法导入数据获取器，将使用模拟数据")
                self._data_fetcher = self._create_mock_fetcher()
        
        return self._data_fetcher
    
    def _create_mock_fetcher(self):
        """创建模拟数据获取器"""
        class MockFetcher:
            def get_ohlcv(self, symbol, start_date=None, end_date=None, **kwargs):
                # 生成模拟数据用于测试
                dates = pd.date_range(
                    start=start_date or '2024-01-01',
                    end=end_date or '2024-12-31',
                    freq='D'
                )
                dates = [d for d in dates if d.weekday() < 5]  # 只保留工作日
                
                if len(dates) == 0:
                    return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
                
                np.random.seed(hash(symbol) % 2**32)  # 确保相同symbol的数据一致
                base_price = np.random.uniform(10, 100)
                
                data = []
                for date in dates:
                    close = base_price * (1 + np.random.normal(0, 0.02))
                    open_price = close * (1 + np.random.normal(0, 0.01))
                    high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.01)))
                    low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.01)))
                    volume = int(np.random.uniform(100000, 10000000))
                    
                    data.append({
                        'date': date,
                        'open': round(open_price, 2),
                        'high': round(high, 2),
                        'low': round(low, 2), 
                        'close': round(close, 2),
                        'volume': volume
                    })
                    base_price = close  # 连续性
                
                return pd.DataFrame(data)
        
        return MockFetcher()
    
    def write_zipline_csv(self,
                         symbols: Union[str, List[str]],
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None,
                         overwrite: bool = False,
                         validate: bool = True,
                         **kwargs) -> Dict[str, Any]:
        """
        生成Zipline格式CSV文件 - 主要接口方法
        
        这个方法完全替换原有的CSV生成逻辑
        
        Args:
            symbols: 股票代码或代码列表
            start_date: 开始日期
            end_date: 结束日期  
            overwrite: 是否覆盖已存在的文件
            validate: 是否验证生成的数据
            **kwargs: 额外参数
            
        Returns:
            Dict[str, Any]: 生成结果统计
        """
        # 重置统计
        self.stats = {
            'files_generated': 0,
            'symbols_processed': 0,
            'errors': 0,
            'start_time': datetime.now(),
            'end_time': None,
            'failed_symbols': [],
            'success_symbols': []
        }
        
        # 标准化输入
        if isinstance(symbols, str):
            symbols = [symbols]
        
        logger.info(f"开始生成Zipline CSV: {len(symbols)}个股票代码")
        
        try:
            # 批量处理
            if len(symbols) > self.batch_size and self.max_workers > 1:
                results = self._process_symbols_parallel(
                    symbols, start_date, end_date, overwrite, validate, **kwargs
                )
            else:
                results = self._process_symbols_sequential(
                    symbols, start_date, end_date, overwrite, validate, **kwargs
                )
            
            # 汇总结果
            self.stats['end_time'] = datetime.now()
            self.stats['duration'] = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            
            logger.info(f"CSV生成完成: 成功 {self.stats['files_generated']} / 总计 {len(symbols)}")
            
            return self.stats
            
        except Exception as e:
            logger.error(f"CSV生成过程异常: {e}")
            self.stats['end_time'] = datetime.now()
            self.stats['errors'] += 1
            raise
    
    def _process_symbols_sequential(self,
                                  symbols: List[str],
                                  start_date: Optional[str],
                                  end_date: Optional[str], 
                                  overwrite: bool,
                                  validate: bool,
                                  **kwargs) -> List[Dict]:
        """顺序处理股票代码"""
        results = []
        
        for symbol in symbols:
            try:
                result = self._process_single_symbol(
                    symbol, start_date, end_date, overwrite, validate, **kwargs
                )
                results.append(result)
                
                if result['success']:
                    self.stats['files_generated'] += 1
                    self.stats['success_symbols'].append(symbol)
                else:
                    self.stats['failed_symbols'].append(symbol)
                
                self.stats['symbols_processed'] += 1
                
            except Exception as e:
                logger.error(f"处理 {symbol} 时异常: {e}")
                self.stats['errors'] += 1
                self.stats['failed_symbols'].append(symbol)
                results.append({
                    'symbol': symbol,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def _process_symbols_parallel(self,
                                symbols: List[str],
                                start_date: Optional[str],
                                end_date: Optional[str],
                                overwrite: bool,
                                validate: bool,
                                **kwargs) -> List[Dict]:
        """并行处理股票代码"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_symbol = {
                executor.submit(
                    self._process_single_symbol,
                    symbol, start_date, end_date, overwrite, validate, **kwargs
                ): symbol
                for symbol in symbols
            }
            
            # 收集结果
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result['success']:
                        self.stats['files_generated'] += 1
                        self.stats['success_symbols'].append(symbol)
                    else:
                        self.stats['failed_symbols'].append(symbol)
                    
                    self.stats['symbols_processed'] += 1
                    
                except Exception as e:
                    logger.error(f"并行处理 {symbol} 时异常: {e}")
                    self.stats['errors'] += 1
                    self.stats['failed_symbols'].append(symbol)
                    results.append({
                        'symbol': symbol,
                        'success': False,
                        'error': str(e)
                    })
        
        return results
    
    def _process_single_symbol(self,
                              symbol: str,
                              start_date: Optional[str],
                              end_date: Optional[str],
                              overwrite: bool,
                              validate: bool,
                              **kwargs) -> Dict[str, Any]:
        """处理单个股票代码"""
        try:
            # 生成输出文件路径
            output_file = self._get_output_file_path(symbol)
            
            # 检查文件是否已存在
            if output_file.exists() and not overwrite:
                logger.info(f"文件已存在，跳过: {output_file}")
                return {
                    'symbol': symbol,
                    'success': True,
                    'file_path': str(output_file),
                    'action': 'skipped',
                    'rows': 0
                }
            
            # 获取数据
            logger.debug(f"获取数据: {symbol}")
            data = self.data_fetcher.get_ohlcv(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                **kwargs
            )
            
            if data.empty:
                logger.warning(f"未获取到数据: {symbol}")
                return {
                    'symbol': symbol,
                    'success': False,
                    'error': 'No data available',
                    'rows': 0
                }
            
            # 转换为Zipline格式
            zipline_data = self._convert_to_zipline_format(data, symbol)
            
            # 验证数据
            if validate:
                validation_result = self._validate_zipline_data(zipline_data, symbol)
                if not validation_result['valid']:
                    return {
                        'symbol': symbol,
                        'success': False,
                        'error': f"Data validation failed: {validation_result['errors']}",
                        'rows': len(zipline_data)
                    }
            
            # 写入CSV文件
            self._write_csv_file(zipline_data, output_file)
            
            logger.info(f"CSV文件生成成功: {output_file} ({len(zipline_data)} rows)")
            
            return {
                'symbol': symbol,
                'success': True,
                'file_path': str(output_file),
                'action': 'created' if not output_file.exists() else 'updated',
                'rows': len(zipline_data),
                'date_range': [
                    zipline_data['date'].min().strftime('%Y-%m-%d'),
                    zipline_data['date'].max().strftime('%Y-%m-%d')
                ]
            }
            
        except Exception as e:
            logger.error(f"处理 {symbol} 失败: {e}")
            return {
                'symbol': symbol,
                'success': False,
                'error': str(e),
                'rows': 0
            }
    
    def _get_output_file_path(self, symbol: str) -> Path:
        """生成输出文件路径"""
        # 清理文件名，替换不合法字符
        safe_symbol = symbol.replace('/', '_').replace('\\', '_').replace('.', '_')
        return self.output_dir / f"{safe_symbol}.csv"
    
    def _convert_to_zipline_format(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """转换数据为Zipline格式"""
        # 复制数据避免修改原数据
        result = data.copy()
        
        # 标准化列名
        column_mapping = {
            'datetime': 'date',
            'Date': 'date',
            'DATE': 'date',
            'Open': 'open',
            'High': 'high', 
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
            'vol': 'volume'
        }
        result = result.rename(columns=column_mapping)
        
        # 确保必要列存在
        for col in self.zipline_columns:
            if col not in result.columns:
                if col == 'volume':
                    result[col] = 0
                    logger.warning(f"{symbol}: 缺少volume列，使用默认值0")
                elif col == 'date':
                    if result.index.name == 'date' or 'datetime' in str(result.index.dtype):
                        result = result.reset_index()
                        result = result.rename(columns={'index': 'date'})
                    else:
                        raise ValueError(f"{symbol}: 缺少日期列")
                else:
                    raise ValueError(f"{symbol}: 缺少必要列 {col}")
        
        # 只保留需要的列
        result = result[self.zipline_columns].copy()
        
        # 数据类型转换
        result['date'] = pd.to_datetime(result['date'])
        
        # 数值列转换
        numeric_cols = ['open', 'high', 'low', 'close']
        for col in numeric_cols:
            result[col] = pd.to_numeric(result[col], errors='coerce')
        
        # volume转换为整数
        result['volume'] = pd.to_numeric(result['volume'], errors='coerce').fillna(0).astype('int64')
        
        # 处理缺失值
        result = result.dropna(subset=numeric_cols)
        
        # 按日期排序
        result = result.sort_values('date').reset_index(drop=True)
        
        # 去重（保留最后一条记录）
        result = result.drop_duplicates(subset=['date'], keep='last')
        
        return result
    
    def _validate_zipline_data(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """验证Zipline数据质量"""
        errors = []
        warnings = []
        
        # 检查数据量
        if len(data) == 0:
            errors.append("数据为空")
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        # 检查列完整性
        missing_cols = [col for col in self.zipline_columns if col not in data.columns]
        if missing_cols:
            errors.append(f"缺少必要列: {missing_cols}")
        
        # 检查数据类型
        if 'date' in data.columns:
            if not pd.api.types.is_datetime64_any_dtype(data['date']):
                errors.append("日期列类型不正确")
        
        # 检查价格数据
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            if col in data.columns:
                if not pd.api.types.is_numeric_dtype(data[col]):
                    errors.append(f"{col}列类型不是数值型")
                elif (data[col] <= 0).any():
                    warnings.append(f"{col}列存在非正数值")
        
        # 检查价格关系
        if all(col in data.columns for col in price_cols):
            # high >= low
            if (data['high'] < data['low']).any():
                errors.append("存在 high < low 的异常数据")
            
            # high >= open, close
            if (data['high'] < data['open']).any() or (data['high'] < data['close']).any():
                warnings.append("存在 high 小于 open 或 close 的数据")
            
            # low <= open, close  
            if (data['low'] > data['open']).any() or (data['low'] > data['close']).any():
                warnings.append("存在 low 大于 open 或 close 的数据")
        
        # 检查成交量
        if 'volume' in data.columns:
            if not pd.api.types.is_integer_dtype(data['volume']):
                errors.append("volume列类型不是整数型")
            elif (data['volume'] < 0).any():
                errors.append("存在负数成交量")
        
        # 检查日期连续性和重复
        if 'date' in data.columns:
            # 检查重复日期
            if data['date'].duplicated().any():
                errors.append("存在重复日期")
            
            # 检查日期排序
            if not data['date'].is_monotonic_increasing:
                warnings.append("日期未按升序排列")
        
        # 记录警告
        if warnings:
            logger.warning(f"{symbol} 数据质量警告: {warnings}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'data_points': len(data),
            'date_range': [
                data['date'].min().strftime('%Y-%m-%d') if 'date' in data.columns else None,
                data['date'].max().strftime('%Y-%m-%d') if 'date' in data.columns else None
            ]
        }
    
    def _write_csv_file(self, data: pd.DataFrame, file_path: Path):
        """写入CSV文件"""
        # 确保输出目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入CSV，使用Zipline兼容的格式
        data.to_csv(
            file_path,
            index=False,
            date_format='%Y-%m-%d',
            float_format='%.4f'
        )
        
        logger.debug(f"CSV文件已写入: {file_path}")
    
    # === 批量操作方法 ===
    
    def write_symbol_list_csv(self,
                             symbol_list_file: Union[str, Path],
                             start_date: Optional[str] = None,
                             end_date: Optional[str] = None,
                             **kwargs) -> Dict[str, Any]:
        """
        从股票代码列表文件生成CSV
        
        Args:
            symbol_list_file: 包含股票代码的文件（每行一个代码）
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 生成结果
        """
        symbol_file = Path(symbol_list_file)
        
        if not symbol_file.exists():
            raise FileNotFoundError(f"股票代码文件不存在: {symbol_file}")
        
        # 读取股票代码列表
        with open(symbol_file, 'r', encoding='utf-8') as f:
            symbols = [line.strip() for line in f if line.strip()]
        
        # 过滤空行和注释
        symbols = [s for s in symbols if s and not s.startswith('#')]
        
        logger.info(f"从 {symbol_file} 读取到 {len(symbols)} 个股票代码")
        
        return self.write_zipline_csv(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            **kwargs
        )
    
    def update_existing_csv(self,
                           start_date: Optional[str] = None,
                           max_age_days: int = 7) -> Dict[str, Any]:
        """
        更新已存在的CSV文件
        
        Args:
            start_date: 更新开始日期，如果为None则从文件最后日期开始
            max_age_days: 文件最大天数，超过此天数的文件才会更新
            
        Returns:
            Dict[str, Any]: 更新结果
        """
        csv_files = list(self.output_dir.glob("*.csv"))
        
        if not csv_files:
            logger.info("输出目录中没有找到CSV文件")
            return {'files_updated': 0, 'symbols_processed': 0}
        
        symbols_to_update = []
        
        for csv_file in csv_files:
            # 检查文件年龄
            file_age = (datetime.now() - datetime.fromtimestamp(csv_file.stat().st_mtime)).days
            
            if file_age >= max_age_days:
                # 从文件名提取股票代码
                symbol = csv_file.stem.replace('_', '.')
                symbols_to_update.append(symbol)
        
        if not symbols_to_update:
            logger.info(f"没有需要更新的文件（超过{max_age_days}天）")
            return {'files_updated': 0, 'symbols_processed': 0}
        
        logger.info(f"准备更新 {len(symbols_to_update)} 个文件")
        
        return self.write_zipline_csv(
            symbols=symbols_to_update,
            start_date=start_date,
            overwrite=True
        )
    
    # === 工具方法 ===
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取生成统计信息"""
        stats = self.stats.copy()
        
        # 添加目录信息
        csv_files = list(self.output_dir.glob("*.csv"))
        stats['total_csv_files'] = len(csv_files)
        stats['output_directory'] = str(self.output_dir)
        
        # 计算文件大小
        total_size = sum(f.stat().st_size for f in csv_files)
        stats['total_size_mb'] = round(total_size / (1024 * 1024), 2)
        
        return stats
    
    def validate_output_directory(self) -> Dict[str, Any]:
        """验证输出目录状态"""
        csv_files = list(self.output_dir.glob("*.csv"))
        
        validation_result = {
            'directory_exists': self.output_dir.exists(),
            'directory_writable': os.access(self.output_dir, os.W_OK),
            'csv_file_count': len(csv_files),
            'total_size_mb': 0,
            'oldest_file': None,
            'newest_file': None,
            'corrupted_files': []
        }
        
        if csv_files:
            # 计算总大小
            total_size = sum(f.stat().st_size for f in csv_files if f.exists())
            validation_result['total_size_mb'] = round(total_size / (1024 * 1024), 2)
            
            # 找到最新和最旧的文件
            file_times = [(f, f.stat().st_mtime) for f in csv_files]
            file_times.sort(key=lambda x: x[1])
            
            validation_result['oldest_file'] = {
                'name': file_times[0][0].name,
                'modified': datetime.fromtimestamp(file_times[0][1]).isoformat()
            }
            validation_result['newest_file'] = {
                'name': file_times[-1][0].name,
                'modified': datetime.fromtimestamp(file_times[-1][1]).isoformat()
            }
            
            # 检查文件完整性
            for csv_file in csv_files[:10]:  # 只检查前10个文件
                try:
                    df = pd.read_csv(csv_file, nrows=1)  # 只读第一行
                    if df.empty or 'date' not in df.columns:
                        validation_result['corrupted_files'].append(csv_file.name)
                except Exception:
                    validation_result['corrupted_files'].append(csv_file.name)
        
        return validation_result
    
    def cleanup_output_directory(self, 
                                older_than_days: Optional[int] = None,
                                dry_run: bool = True) -> Dict[str, Any]:
        """
        清理输出目录
        
        Args:
            older_than_days: 删除多少天前的文件，None表示删除所有文件
            dry_run: 是否为试运行模式（不实际删除）
            
        Returns:
            Dict[str, Any]: 清理结果
        """
        csv_files = list(self.output_dir.glob("*.csv"))
        files_to_delete = []
        
        current_time = datetime.now()
        
        for csv_file in csv_files:
            if older_than_days is None:
                files_to_delete.append(csv_file)
            else:
                file_age = (current_time - datetime.fromtimestamp(csv_file.stat().st_mtime)).days
                if file_age > older_than_days:
                    files_to_delete.append(csv_file)
        
        result = {
            'total_files': len(csv_files),
            'files_to_delete': len(files_to_delete),
            'deleted_files': [],
            'dry_run': dry_run
        }
        
        if not dry_run:
            for file_path in files_to_delete:
                try:
                    file_path.unlink()
                    result['deleted_files'].append(file_path.name)
                    logger.info(f"已删除文件: {file_path}")
                except Exception as e:
                    logger.error(f"删除文件失败: {file_path}, {e}")
        else:
            result['files_to_delete_list'] = [f.name for f in files_to_delete]
            logger.info(f"试运行模式：将删除 {len(files_to_delete)} 个文件")
        
        return result

# === 便捷函数 ===

def write_zipline_csv(symbols: Union[str, List[str]],
                     output_dir: Union[str, Path],
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None,
                     **kwargs) -> Dict[str, Any]:
    """
    便捷函数：生成Zipline CSV文件
    
    这个函数可以直接替换原有的CSV生成调用
    """
    writer = ZiplineCsvWriter(output_dir=output_dir)
    return writer.write_zipline_csv(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        **kwargs
    )

def batch_write_zipline_csv(symbol_list_file: Union[str, Path],
                           output_dir: Union[str, Path],
                           **kwargs) -> Dict[str, Any]:
    """
    便捷函数：批量生成Zipline CSV文件
    
    从股票代码列表文件批量生成CSV
    """
    writer = ZiplineCsvWriter(output_dir=output_dir)
    return writer.write_symbol_list_csv(
        symbol_list_file=symbol_list_file,
        **kwargs
    )

if __name__ == "__main__":
    # 测试代码
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试用的CSV生成器
        writer = ZiplineCsvWriter(output_dir=temp_dir)
        
        # 测试生成单个股票CSV
        result = writer.write_zipline_csv(
            symbols="000001.SZ",
            start_date="2024-01-01", 
            end_date="2024-01-31"
        )
        
        print("单个股票CSV生成结果:")
        print(f"  成功: {result['files_generated']}")
        print(f"  耗时: {result.get('duration', 0):.2f}秒")
        
        # 测试批量生成
        test_symbols = ["000001.SZ", "000002.SZ", "600000.SH"]
        result = writer.write_zipline_csv(
            symbols=test_symbols,
            start_date="2024-01-01",
            end_date="2024-01-31", 
            overwrite=True
        )
        
        print("\\n批量CSV生成结果:")
        print(f"  成功: {result['files_generated']}/{len(test_symbols)}")
        print(f"  失败: {len(result['failed_symbols'])}")
        print(f"  耗时: {result.get('duration', 0):.2f}秒")
        
        # 验证输出目录
        validation = writer.validate_output_directory()
        print(f"\\n输出目录验证:")
        print(f"  CSV文件数量: {validation['csv_file_count']}")
        print(f"  总大小: {validation['total_size_mb']} MB")
        print(f"  损坏文件: {len(validation['corrupted_files'])}")
        
        # 测试便捷函数
        result = write_zipline_csv(
            symbols="600036.SH",
            output_dir=temp_dir,
            start_date="2024-01-01",
            end_date="2024-01-31"
        )
        
        print(f"\\n便捷函数测试: {'成功' if result['files_generated'] > 0 else '失败'}")
        
        print("\\n✅ Zipline CSV生成器测试完成!")