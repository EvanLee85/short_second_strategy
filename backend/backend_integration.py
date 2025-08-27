"""
后端集成适配器 - 无痛替换现有后端调用
提供与现有API完全兼容的接口，实现数据源的透明切换

使用方式:
1. 在现有代码开头导入: from backend.backend_integration import *
2. 现有的 pd.read_csv() 调用自动切换到新数据源
3. 现有的 CSV 写入调用自动切换到 write_zipline_csv()
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Union, Dict, List, Any, Callable
import warnings
import logging
import functools
from datetime import datetime

# 配置日志
logger = logging.getLogger(__name__)

class BackendIntegrationAdapter:
    """
    后端集成适配器
    
    通过monkey patching和装饰器模式，实现对现有代码的无痛替换
    """
    
    def __init__(self):
        self.enabled = True
        self.fallback_enabled = True
        self.csv_data_path = None
        
        # 记录原始函数
        self._original_pd_read_csv = pd.read_csv
        self._patched = False
        
        # 统计信息
        self.stats = {
            'read_csv_intercepts': 0,
            'write_csv_intercepts': 0,
            'fallback_calls': 0,
            'errors': 0
        }
    
    def enable_integration(self, 
                          csv_data_path: Optional[str] = None,
                          auto_patch: bool = True):
        """
        启用后端集成
        
        Args:
            csv_data_path: 原始CSV数据路径（用于回退）
            auto_patch: 是否自动patch pandas函数
        """
        self.csv_data_path = csv_data_path
        
        if auto_patch and not self._patched:
            self._patch_pandas_functions()
        
        logger.info("后端集成已启用")
    
    def disable_integration(self):
        """禁用后端集成，恢复原始函数"""
        if self._patched:
            self._restore_pandas_functions()
        
        self.enabled = False
        logger.info("后端集成已禁用")
    
    def _patch_pandas_functions(self):
        """patch pandas函数"""
        if self._patched:
            return
        
        # 保存原始函数
        self._original_pd_read_csv = pd.read_csv
        
        # 替换为适配后的函数
        pd.read_csv = self._adaptive_read_csv
        
        self._patched = True
        logger.info("pandas函数已被patch")
    
    def _restore_pandas_functions(self):
        """恢复pandas原始函数"""
        if not self._patched:
            return
        
        pd.read_csv = self._original_pd_read_csv
        self._patched = False
        logger.info("pandas函数已恢复")
    
    def _adaptive_read_csv(self, filepath_or_buffer, **kwargs) -> pd.DataFrame:
        """
        自适应的read_csv函数
        
        如果是股票数据文件，尝试使用新的数据获取器
        否则回退到原始的pandas.read_csv
        """
        self.stats['read_csv_intercepts'] += 1
        
        try:
            # 检查是否为股票数据文件
            if isinstance(filepath_or_buffer, (str, Path)):
                file_path = Path(filepath_or_buffer)
                
                # 从文件路径判断是否为股票数据
                if self._is_stock_data_file(file_path):
                    return self._read_stock_data_with_new_fetcher(file_path, **kwargs)
            
            # 不是股票数据文件，使用原始函数
            return self._original_pd_read_csv(filepath_or_buffer, **kwargs)
            
        except Exception as e:
            logger.warning(f"自适应read_csv失败，回退到原始函数: {e}")
            self.stats['fallback_calls'] += 1
            return self._original_pd_read_csv(filepath_or_buffer, **kwargs)
    
    def _is_stock_data_file(self, file_path: Path) -> bool:
        """判断是否为股票数据文件"""
        # 基于文件路径和名称的启发式判断
        indicators = [
            # 文件名模式
            file_path.name.lower().endswith(('.csv',)),
            # 路径中包含股票相关关键词
            any(keyword in str(file_path).lower() for keyword in [
                'stock', 'equity', 'data', 'ohlc', 'price', 'zipline'
            ]),
            # 股票代码模式
            self._extract_symbol_from_path(file_path) is not None
        ]
        
        return any(indicators)
    
    def _extract_symbol_from_path(self, file_path: Path) -> Optional[str]:
        """从文件路径提取股票代码"""
        import re
        
        filename = file_path.stem
        
        # 股票代码模式
        patterns = [
            r'^(\d{6}\.(SZ|SH))$',  # 000001.SZ
            r'^(\d{6})_(SZ|SH)$',   # 000001_SZ
            r'^([A-Z]{1,5})$',      # AAPL
            r'^(\d{6})$'            # 000001
        ]
        
        for pattern in patterns:
            match = re.match(pattern, filename.upper())
            if match:
                symbol = match.group(1)
                # 标准化格式
                if len(symbol) == 6 and symbol.isdigit():
                    # 根据代码判断市场
                    if symbol.startswith(('000', '002', '300')):
                        return f"{symbol}.SZ"
                    elif symbol.startswith(('600', '601', '603', '688')):
                        return f"{symbol}.SH"
                return symbol
        
        return None
    
    def _read_stock_data_with_new_fetcher(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """使用新数据获取器读取股票数据"""
        try:
            # 提取股票代码
            symbol = self._extract_symbol_from_path(file_path)
            
            if not symbol:
                raise ValueError("无法从文件路径提取股票代码")
            
            # 使用新的数据获取器
            from backend.data_fetcher_facade import get_global_fetcher
            
            fetcher = get_global_fetcher(csv_data_path=self.csv_data_path)
            
            # 尝试从kwargs中获取日期范围
            start_date = kwargs.pop('start_date', None)
            end_date = kwargs.pop('end_date', None)
            
            data = fetcher.get_ohlcv(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            logger.info(f"使用新数据获取器成功读取: {symbol}")
            return data
            
        except Exception as e:
            logger.warning(f"新数据获取器失败，回退到CSV: {e}")
            self.stats['fallback_calls'] += 1
            
            # 回退到原始CSV读取
            return self._original_pd_read_csv(file_path, **kwargs)

# 全局适配器实例
_global_adapter = BackendIntegrationAdapter()

# === 公开接口函数 ===

def enable_backend_integration(csv_data_path: Optional[str] = None,
                              auto_patch: bool = True):
    """
    启用后端集成
    
    在应用启动时调用此函数来启用无痛替换
    
    Args:
        csv_data_path: 原始CSV数据路径
        auto_patch: 是否自动patch pandas函数
    
    Example:
        # 在main函数或应用启动时调用
        enable_backend_integration(csv_data_path="./data/stocks/")
        
        # 之后所有的 pd.read_csv() 调用都会自动使用新数据源
        data = pd.read_csv("data/000001.SZ.csv")  # 自动切换到新获取器
    """
    global _global_adapter
    _global_adapter.enable_integration(csv_data_path=csv_data_path, auto_patch=auto_patch)

def disable_backend_integration():
    """禁用后端集成"""
    global _global_adapter
    _global_adapter.disable_integration()

def get_integration_stats() -> Dict[str, Any]:
    """获取集成统计信息"""
    global _global_adapter
    return _global_adapter.stats.copy()

# === 兼容性函数 - 直接替换现有调用 ===

def read_stock_data(file_path: Union[str, Path], 
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   **kwargs) -> pd.DataFrame:
    """
    读取股票数据 - 兼容性函数
    
    可以直接替换现有的 pd.read_csv() 调用
    
    Example:
        # 原来的代码:
        # data = pd.read_csv("data/000001.SZ.csv")
        
        # 替换为:
        data = read_stock_data("data/000001.SZ.csv")
    """
    try:
        from backend.data_fetcher_facade import get_global_fetcher
        
        file_path = Path(file_path)
        symbol = _global_adapter._extract_symbol_from_path(file_path)
        
        if symbol:
            fetcher = get_global_fetcher(csv_data_path=_global_adapter.csv_data_path)
            return fetcher.get_ohlcv(symbol=symbol, start_date=start_date, end_date=end_date)
        else:
            # 如果无法提取股票代码，回退到普通CSV读取
            return pd.read_csv(file_path, **kwargs)
            
    except Exception as e:
        logger.warning(f"read_stock_data失败，回退到CSV: {e}")
        return pd.read_csv(file_path, **kwargs)

def write_stock_csv(data: pd.DataFrame, 
                   file_path: Union[str, Path],
                   symbol: Optional[str] = None,
                   **kwargs):
    """
    写入股票CSV - 兼容性函数
    
    自动使用Zipline格式，可以直接替换现有的 DataFrame.to_csv() 调用
    
    Example:
        # 原来的代码:
        # data.to_csv("output/000001.SZ.csv", index=False)
        
        # 替换为:
        write_stock_csv(data, "output/000001.SZ.csv")
    """
    try:
        from backend.zipline_csv_writer import ZiplineCsvWriter
        
        file_path = Path(file_path)
        output_dir = file_path.parent
        
        # 如果没有提供symbol，从文件路径提取
        if not symbol:
            symbol = _global_adapter._extract_symbol_from_path(file_path)
        
        if symbol:
            # 使用Zipline CSV写入器
            writer = ZiplineCsvWriter(output_dir=output_dir)
            
            # 临时将数据保存到获取器中（这里简化处理）
            # 实际应用中可能需要更复杂的数据管理
            zipline_data = writer._convert_to_zipline_format(data, symbol)
            writer._write_csv_file(zipline_data, file_path)
            
            logger.info(f"使用Zipline格式写入: {file_path}")
        else:
            # 回退到普通CSV写入
            data.to_csv(file_path, index=False, **kwargs)
            logger.info(f"使用普通格式写入: {file_path}")
            
    except Exception as e:
        logger.warning(f"write_stock_csv失败，回退到普通CSV: {e}")
        data.to_csv(file_path, index=False, **kwargs)

# === 装饰器 - 用于逐步迁移现有函数 ===

def use_new_data_source(csv_data_path: Optional[str] = None):
    """
    装饰器：将函数中的CSV读取切换到新数据源
    
    用于逐步迁移现有函数，不需要修改函数内部代码
    
    Example:
        @use_new_data_source(csv_data_path="./data/stocks/")
        def analyze_stock(symbol):
            # 这里的 pd.read_csv 会自动使用新数据源
            data = pd.read_csv(f"data/{symbol}.csv")
            return data.mean()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 临时启用集成
            original_enabled = _global_adapter.enabled
            original_path = _global_adapter.csv_data_path
            
            try:
                _global_adapter.csv_data_path = csv_data_path or original_path
                _global_adapter.enabled = True
                
                if not _global_adapter._patched:
                    _global_adapter._patch_pandas_functions()
                
                result = func(*args, **kwargs)
                return result
                
            finally:
                # 恢复原始状态
                _global_adapter.enabled = original_enabled
                _global_adapter.csv_data_path = original_path
        
        return wrapper
    return decorator

def migrate_csv_operations(output_dir: Union[str, Path]):
    """
    装饰器：迁移函数中的CSV操作到新后端
    
    自动处理函数中的CSV读写操作
    
    Example:
        @migrate_csv_operations(output_dir="./output/")
        def process_stocks(symbol_list):
            results = []
            for symbol in symbol_list:
                data = pd.read_csv(f"data/{symbol}.csv")  # 自动使用新数据源
                processed = process_data(data)
                processed.to_csv(f"output/{symbol}.csv")  # 自动使用新写入器
                results.append(processed)
            return results
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 启用后端集成
            enable_backend_integration()
            
            # 临时替换DataFrame.to_csv方法
            original_to_csv = pd.DataFrame.to_csv
            
            def adaptive_to_csv(self, path_or_buf=None, **csv_kwargs):
                if isinstance(path_or_buf, (str, Path)):
                    path = Path(path_or_buf)
                    if path.suffix.lower() == '.csv':
                        symbol = _global_adapter._extract_symbol_from_path(path)
                        if symbol:
                            write_stock_csv(self, path_or_buf, symbol=symbol, **csv_kwargs)
                            return
                
                # 回退到原始方法
                return original_to_csv(self, path_or_buf, **csv_kwargs)
            
            pd.DataFrame.to_csv = adaptive_to_csv
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # 恢复原始方法
                pd.DataFrame.to_csv = original_to_csv
        
        return wrapper
    return decorator

# === 批量迁移工具 ===

class BatchMigrationTool:
    """批量迁移工具"""
    
    def __init__(self, 
                 csv_input_dir: Union[str, Path],
                 csv_output_dir: Union[str, Path]):
        self.csv_input_dir = Path(csv_input_dir)
        self.csv_output_dir = Path(csv_output_dir) 
        self.csv_output_dir.mkdir(parents=True, exist_ok=True)
        
        self.migration_stats = {
            'files_processed': 0,
            'files_migrated': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    def migrate_all_csv_files(self, 
                             overwrite: bool = False,
                             validate: bool = True) -> Dict[str, Any]:
        """
        批量迁移所有CSV文件到新格式
        
        Args:
            overwrite: 是否覆盖已存在的文件
            validate: 是否验证迁移后的数据
            
        Returns:
            Dict[str, Any]: 迁移结果统计
        """
        from backend.zipline_csv_writer import ZiplineCsvWriter
        
        self.migration_stats['start_time'] = datetime.now()
        
        # 找到所有CSV文件
        csv_files = list(self.csv_input_dir.glob("*.csv"))
        logger.info(f"发现 {len(csv_files)} 个CSV文件")
        
        if not csv_files:
            return self.migration_stats
        
        # 提取股票代码列表
        symbols = []
        for csv_file in csv_files:
            symbol = _global_adapter._extract_symbol_from_path(csv_file)
            if symbol:
                symbols.append(symbol)
        
        logger.info(f"提取到 {len(symbols)} 个有效股票代码")
        
        # 使用Zipline写入器批量处理
        writer = ZiplineCsvWriter(output_dir=self.csv_output_dir)
        
        # 配置数据获取器使用原始CSV作为数据源
        enable_backend_integration(csv_data_path=str(self.csv_input_dir))
        
        try:
            result = writer.write_zipline_csv(
                symbols=symbols,
                overwrite=overwrite,
                validate=validate
            )
            
            self.migration_stats.update({
                'files_processed': len(csv_files),
                'files_migrated': result['files_generated'],
                'errors': result['failed_symbols'] and len(result['failed_symbols']) or 0,
                'end_time': datetime.now(),
                'duration': result.get('duration', 0)
            })
            
            logger.info(f"批量迁移完成: {self.migration_stats['files_migrated']}/{len(csv_files)}")
            
            return self.migration_stats
            
        except Exception as e:
            logger.error(f"批量迁移失败: {e}")
            self.migration_stats['errors'] += 1
            self.migration_stats['end_time'] = datetime.now()
            raise
    
    def validate_migration(self) -> Dict[str, Any]:
        """验证迁移结果"""
        original_files = list(self.csv_input_dir.glob("*.csv"))
        migrated_files = list(self.csv_output_dir.glob("*.csv"))
        
        validation_result = {
            'original_count': len(original_files),
            'migrated_count': len(migrated_files),
            'missing_files': [],
            'data_consistency_check': []
        }
        
        # 检查文件完整性
        for original_file in original_files:
            symbol = _global_adapter._extract_symbol_from_path(original_file)
            if symbol:
                migrated_file = self.csv_output_dir / f"{symbol.replace('.', '_')}.csv"
                if not migrated_file.exists():
                    validation_result['missing_files'].append(symbol)
        
        # 抽样检查数据一致性（检查前5个文件）
        for original_file in original_files[:5]:
            symbol = _global_adapter._extract_symbol_from_path(original_file)
            if symbol:
                try:
                    original_data = pd.read_csv(original_file)
                    migrated_file = self.csv_output_dir / f"{symbol.replace('.', '_')}.csv"
                    
                    if migrated_file.exists():
                        migrated_data = pd.read_csv(migrated_file)
                        
                        # 简单的数据量对比
                        consistency_check = {
                            'symbol': symbol,
                            'original_rows': len(original_data),
                            'migrated_rows': len(migrated_data),
                            'row_diff': len(migrated_data) - len(original_data)
                        }
                        validation_result['data_consistency_check'].append(consistency_check)
                        
                except Exception as e:
                    logger.warning(f"验证 {symbol} 时异常: {e}")
        
        return validation_result

# === 便捷函数 ===

def quick_migration(csv_input_dir: Union[str, Path],
                   csv_output_dir: Union[str, Path],
                   **kwargs) -> Dict[str, Any]:
    """
    快速迁移工具
    
    一键迁移整个目录的CSV文件到新格式
    
    Example:
        result = quick_migration(
            csv_input_dir="./data/old_csvs/",
            csv_output_dir="./data/zipline_csvs/"
        )
        print(f"迁移完成: {result['files_migrated']} 个文件")
    """
    tool = BatchMigrationTool(csv_input_dir, csv_output_dir)
    return tool.migrate_all_csv_files(**kwargs)

def create_migration_script(csv_input_dir: Union[str, Path],
                           csv_output_dir: Union[str, Path],
                           script_path: Union[str, Path] = "migrate_data.py"):
    """
    创建迁移脚本
    
    生成一个独立的Python脚本来执行数据迁移
    """
    script_content = f'''#!/usr/bin/env python3
"""
自动生成的数据迁移脚本
从 {csv_input_dir} 迁移CSV文件到 {csv_output_dir}
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.backend_integration import quick_migration

def main():
    print("开始数据迁移...")
    
    try:
        result = quick_migration(
            csv_input_dir="{csv_input_dir}",
            csv_output_dir="{csv_output_dir}",
            overwrite=True,
            validate=True
        )
        
        print(f"迁移完成!")
        print(f"  处理文件: {{result['files_processed']}}")
        print(f"  成功迁移: {{result['files_migrated']}}")
        print(f"  错误数量: {{result['errors']}}")
        print(f"  耗时: {{result.get('duration', 0):.2f}} 秒")
        
        if result['errors'] == 0:
            print("✅ 所有文件迁移成功!")
            return 0
        else:
            print("⚠️ 部分文件迁移失败，请检查日志")
            return 1
            
    except Exception as e:
        print(f"❌ 迁移过程异常: {{e}}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
    
    script_file = Path(script_path)
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # 设置执行权限（Linux/Mac）
    try:
        import stat
        script_file.chmod(script_file.stat().st_mode | stat.S_IEXEC)
    except:
        pass
    
    logger.info(f"迁移脚本已创建: {script_file}")
    return script_file

if __name__ == "__main__":
    # 测试代码
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试CSV文件
        input_dir = Path(temp_dir) / "input"
        output_dir = Path(temp_dir) / "output"
        input_dir.mkdir()
        
        # 生成测试数据
        test_symbols = ["000001.SZ", "600000.SH", "AAPL"]
        
        for symbol in test_symbols:
            test_data = pd.DataFrame({
                'date': pd.date_range('2024-01-01', periods=10),
                'open': np.random.uniform(10, 20, 10),
                'high': np.random.uniform(20, 30, 10),
                'low': np.random.uniform(5, 15, 10),
                'close': np.random.uniform(10, 25, 10),
                'volume': np.random.randint(1000000, 10000000, 10)
            })
            
            # 确保价格关系正确
            for i in range(len(test_data)):
                test_data.loc[i, 'high'] = max(test_data.loc[i, ['open', 'close', 'high']])
                test_data.loc[i, 'low'] = min(test_data.loc[i, ['open', 'close', 'low']])
            
            csv_file = input_dir / f"{symbol.replace('.', '_')}.csv"
            test_data.to_csv(csv_file, index=False)
        
        print(f"创建了 {len(test_symbols)} 个测试CSV文件")
        
        # 测试快速迁移
        result = quick_migration(
            csv_input_dir=input_dir,
            csv_output_dir=output_dir
        )
        
        print("\\n快速迁移结果:")
        print(f"  处理: {result['files_processed']}")
        print(f"  成功: {result['files_migrated']}")
        print(f"  错误: {result['errors']}")
        
        # 测试后端集成
        enable_backend_integration(csv_data_path=str(input_dir))
        
        # 测试自动读取
        test_data = read_stock_data(input_dir / "000001_SZ.csv")
        print(f"\\n自动读取测试: {len(test_data)} 行数据")
        
        # 测试统计信息
        stats = get_integration_stats()
        print(f"集成统计: {stats}")
        
        print("\\n✅ 后端集成测试完成!")
        
        # 清理
        disable_backend_integration()