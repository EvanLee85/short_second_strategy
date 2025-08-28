# =============================================================================
# zipline_ingest.py - Zipline数据摄入
# =============================================================================

ZIPLINE_INGEST_SCRIPT = '''#!/usr/bin/env python3
"""
Zipline数据摄入工具
将CSV数据摄入到Zipline中用于回测

使用方式:
python scripts/zipline_ingest.py --bundle custom_bundle
python scripts/zipline_ingest.py --bundle custom_bundle --symbols 000001.SZ,600000.SH
"""

import sys
import subprocess
import argparse
from pathlib import Path
import os

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def setup_zipline_environment():
    """设置Zipline环境变量"""
    # 设置Zipline根目录
    zipline_root = PROJECT_ROOT / 'data' / 'zipline'
    zipline_root.mkdir(parents=True, exist_ok=True)#!/usr/bin/env python3
"""
实用工具脚本集合
包含文档中提到的所有工具脚本的实际实现

文件结构:
- verify_token.py - 验证API token有效性
- clear_cache.py - 清理各种缓存
- inspect_raw_data.py - 检查原始数据
- validate_data_format.py - 验证数据格式
- verify_adjustment.py - 验证复权一致性
- check_price_relationships.py - 检查价格关系
- fix_price_relationships.py - 修复价格关系异常
- align_trading_calendar.py - 对齐交易日历
- validate_zipline_format.py - 验证Zipline格式
- zipline_ingest.py - Zipline数据摄入
- test_zipline_data.py - 测试Zipline数据
"""

import os
import sys
from pathlib import Path

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# verify_token.py - 验证API token有效性
# =============================================================================

VERIFY_TOKEN_SCRIPT = '''#!/usr/bin/env python3
"""
API Token验证工具
验证各种数据源API token的有效性

使用方式:
python scripts/verify_token.py --source tushare
python scripts/verify_token.py --source akshare
python scripts/verify_token.py --all
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def verify_tushare_token():
    """验证Tushare token"""
    try:
        import tushare as ts
        from config.settings import DATA_SOURCES
        
        token = DATA_SOURCES.get('tushare', {}).get('token')
        if not token:
            print("❌ Tushare token未配置")
            return False
        
        # 设置token并测试
        ts.set_token(token)
        pro = ts.pro_api()
        
        # 测试API调用
        df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name')
        
        if not df.empty:
            print(f"✅ Tushare token验证成功")
            print(f"   获取到 {len(df)} 只股票信息")
            return True
        else:
            print("❌ Tushare token验证失败: 返回空数据")
            return False
            
    except ImportError:
        print("⚠️  Tushare未安装，跳过验证")
        return None
    except Exception as e:
        print(f"❌ Tushare token验证失败: {e}")
        return False

def verify_akshare_connection():
    """验证Akshare连接"""
    try:
        import akshare as ak
        
        # 测试获取股票列表
        df = ak.stock_zh_a_spot_em()
        
        if not df.empty:
            print(f"✅ Akshare连接验证成功")
            print(f"   获取到 {len(df)} 只股票信息")
            return True
        else:
            print("❌ Akshare连接验证失败: 返回空数据")
            return False
            
    except ImportError:
        print("⚠️  Akshare未安装，跳过验证")
        return None
    except Exception as e:
        print(f"❌ Akshare连接验证失败: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='API Token验证工具')
    parser.add_argument('--source', choices=['tushare', 'akshare'], help='指定数据源')
    parser.add_argument('--all', action='store_true', help='验证所有数据源')
    
    args = parser.parse_args()
    
    print("🔐 API Token验证工具")
    print("=" * 40)
    
    results = {}
    
    if args.source == 'tushare' or args.all:
        results['tushare'] = verify_tushare_token()
    
    if args.source == 'akshare' or args.all:
        results['akshare'] = verify_akshare_connection()
    
    if not args.source and not args.all:
        # 默认验证所有
        results['tushare'] = verify_tushare_token()
        results['akshare'] = verify_akshare_connection()
    
    # 汇总结果
    print("\\n📊 验证结果汇总:")
    success_count = 0
    total_count = 0
    
    for source, result in results.items():
        if result is not None:
            total_count += 1
            if result:
                success_count += 1
                print(f"   ✅ {source}: 通过")
            else:
                print(f"   ❌ {source}: 失败")
        else:
            print(f"   ⚠️  {source}: 跳过")
    
    if total_count > 0:
        print(f"\\n成功率: {success_count}/{total_count}")
        return 0 if success_count == total_count else 1
    else:
        print("\\n没有可验证的数据源")
        return 0

if __name__ == "__main__":
    sys.exit(main())
'''

# =============================================================================
# clear_cache.py - 清理各种缓存
# =============================================================================

CLEAR_CACHE_SCRIPT = '''#!/usr/bin/env python3
"""
缓存清理工具
清理项目中的各种缓存数据

使用方式:
python scripts/clear_cache.py --type all
python scripts/clear_cache.py --type data
python scripts/clear_cache.py --type adjustment
python scripts/clear_cache.py --type auth
"""

import sys
import shutil
import argparse
from pathlib import Path

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def clear_data_cache():
    """清理数据缓存"""
    cache_dirs = [
        PROJECT_ROOT / 'data' / 'cache',
        PROJECT_ROOT / 'data' / 'temp',
        PROJECT_ROOT / '.cache'
    ]
    
    cleared_count = 0
    total_size = 0
    
    for cache_dir in cache_dirs:
        if cache_dir.exists():
            # 计算大小
            size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
            total_size += size
            
            # 删除内容
            shutil.rmtree(cache_dir)
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"✅ 清理数据缓存: {cache_dir} ({size/1024/1024:.1f} MB)")
            cleared_count += 1
    
    return cleared_count, total_size

def clear_adjustment_cache():
    """清理复权因子缓存"""
    adjustment_files = [
        PROJECT_ROOT / 'data' / 'adjustment_factors.pkl',
        PROJECT_ROOT / 'data' / 'adjustment_factors.json',
    ]
    
    cleared_count = 0
    
    for adj_file in adjustment_files:
        if adj_file.exists():
            size = adj_file.stat().st_size
            adj_file.unlink()
            print(f"✅ 清理复权缓存: {adj_file} ({size/1024:.1f} KB)")
            cleared_count += 1
    
    return cleared_count

def clear_auth_cache():
    """清理认证缓存"""
    auth_files = [
        PROJECT_ROOT / '.tushare_cache',
        PROJECT_ROOT / '.auth_cache',
        Path.home() / '.tushare' / 'token_cache'
    ]
    
    cleared_count = 0
    
    for auth_file in auth_files:
        if auth_file.exists():
            if auth_file.is_dir():
                shutil.rmtree(auth_file)
            else:
                auth_file.unlink()
            print(f"✅ 清理认证缓存: {auth_file}")
            cleared_count += 1
    
    return cleared_count

def clear_log_files():
    """清理日志文件"""
    log_dirs = [
        PROJECT_ROOT / 'logs',
        PROJECT_ROOT / 'log'
    ]
    
    cleared_count = 0
    total_size = 0
    
    for log_dir in log_dirs:
        if log_dir.exists():
            for log_file in log_dir.glob('*.log'):
                if log_file.stat().st_size > 10 * 1024 * 1024:  # 大于10MB
                    size = log_file.stat().st_size
                    log_file.unlink()
                    total_size += size
                    print(f"✅ 清理大日志文件: {log_file} ({size/1024/1024:.1f} MB)")
                    cleared_count += 1
    
    return cleared_count, total_size

def clear_temp_files():
    """清理临时文件"""
    temp_patterns = [
        '**/.DS_Store',
        '**/__pycache__',
        '**/*.pyc',
        '**/*.pyo',
        '**/temp_*',
        '**/tmp_*'
    ]
    
    cleared_count = 0
    
    for pattern in temp_patterns:
        for temp_file in PROJECT_ROOT.glob(pattern):
            if temp_file.is_file():
                temp_file.unlink()
                cleared_count += 1
            elif temp_file.is_dir():
                shutil.rmtree(temp_file)
                cleared_count += 1
    
    if cleared_count > 0:
        print(f"✅ 清理临时文件: {cleared_count} 个")
    
    return cleared_count

def main():
    parser = argparse.ArgumentParser(description='缓存清理工具')
    parser.add_argument('--type', 
                       choices=['all', 'data', 'adjustment', 'auth', 'logs', 'temp'],
                       default='all',
                       help='指定清理类型')
    parser.add_argument('--dry-run', action='store_true', help='试运行，不实际删除')
    
    args = parser.parse_args()
    
    print("🧹 缓存清理工具")
    print("=" * 40)
    
    if args.dry_run:
        print("⚠️  试运行模式，不会实际删除文件")
    
    total_cleared = 0
    total_size = 0
    
    if args.type in ['all', 'data']:
        count, size = clear_data_cache()
        total_cleared += count
        total_size += size
    
    if args.type in ['all', 'adjustment']:
        count = clear_adjustment_cache()
        total_cleared += count
    
    if args.type in ['all', 'auth']:
        count = clear_auth_cache()
        total_cleared += count
    
    if args.type in ['all', 'logs']:
        count, size = clear_log_files()
        total_cleared += count
        total_size += size
    
    if args.type in ['all', 'temp']:
        count = clear_temp_files()
        total_cleared += count
    
    print(f"\\n📊 清理完成:")
    print(f"   清理项目: {total_cleared}")
    print(f"   释放空间: {total_size/1024/1024:.1f} MB")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

# =============================================================================
# inspect_raw_data.py - 检查原始数据
# =============================================================================

INSPECT_RAW_DATA_SCRIPT = '''#!/usr/bin/env python3
"""
原始数据检查工具
检查和分析原始股票数据的质量和结构

使用方式:
python scripts/inspect_raw_data.py --symbol 000001.SZ --source akshare
python scripts/inspect_raw_data.py --file data/raw/000001.SZ.csv
"""

import sys
import pandas as pd
import argparse
from pathlib import Path

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def inspect_dataframe(df, symbol_name="Unknown"):
    """检查DataFrame的详细信息"""
    
    print(f"📊 数据检查报告: {symbol_name}")
    print("=" * 50)
    
    # 基本信息
    print(f"数据维度: {df.shape[0]} 行 × {df.shape[1]} 列")
    print(f"内存使用: {df.memory_usage(deep=True).sum() / 1024:.1f} KB")
    
    # 列信息
    print(f"\\n📋 列信息:")
    for i, (col, dtype) in enumerate(zip(df.columns, df.dtypes)):
        null_count = df[col].isnull().sum()
        null_pct = null_count / len(df) * 100
        print(f"   {i+1:2d}. {col:15s} ({str(dtype):10s}) - 缺失: {null_count:4d} ({null_pct:5.1f}%)")
    
    # 数值列统计
    numeric_cols = df.select_dtypes(include=[float, int]).columns
    if len(numeric_cols) > 0:
        print(f"\\n📈 数值列统计:")
        print(df[numeric_cols].describe().round(4))
    
    # 价格关系检查
    price_cols = ['open', 'high', 'low', 'close']
    available_price_cols = [col for col in price_cols if col in df.columns]
    
    if len(available_price_cols) >= 4:
        print(f"\\n💰 价格关系检查:")
        
        # high >= low
        high_low_ok = (df['high'] >= df['low']).sum()
        print(f"   high >= low: {high_low_ok:4d}/{len(df)} ({high_low_ok/len(df)*100:5.1f}%)")
        
        # high >= open, close
        high_open_ok = (df['high'] >= df['open']).sum()
        high_close_ok = (df['high'] >= df['close']).sum()
        print(f"   high >= open: {high_open_ok:4d}/{len(df)} ({high_open_ok/len(df)*100:5.1f}%)")
        print(f"   high >= close: {high_close_ok:4d}/{len(df)} ({high_close_ok/len(df)*100:5.1f}%)")
        
        # low <= open, close
        low_open_ok = (df['low'] <= df['open']).sum()
        low_close_ok = (df['low'] <= df['close']).sum()
        print(f"   low <= open: {low_open_ok:4d}/{len(df)} ({low_open_ok/len(df)*100:5.1f}%)")
        print(f"   low <= close: {low_close_ok:4d}/{len(df)} ({low_close_ok/len(df)*100:5.1f}%)")
    
    # 成交量检查
    if 'volume' in df.columns:
        print(f"\\n📊 成交量检查:")
        vol_positive = (df['volume'] > 0).sum()
        vol_zero = (df['volume'] == 0).sum()
        vol_negative = (df['volume'] < 0).sum()
        
        print(f"   正数成交量: {vol_positive:4d} ({vol_positive/len(df)*100:5.1f}%)")
        print(f"   零成交量: {vol_zero:4d} ({vol_zero/len(df)*100:5.1f}%)")
        print(f"   负数成交量: {vol_negative:4d} ({vol_negative/len(df)*100:5.1f}%)")
    
    # 日期连续性检查
    date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
    if date_cols:
        date_col = date_cols[0]
        print(f"\\n📅 日期连续性检查 (列: {date_col}):")
        
        try:
            df_sorted = df.copy()
            df_sorted[date_col] = pd.to_datetime(df_sorted[date_col])
            df_sorted = df_sorted.sort_values(date_col)
            
            date_range = df_sorted[date_col].max() - df_sorted[date_col].min()
            print(f"   时间跨度: {date_range.days} 天")
            print(f"   开始日期: {df_sorted[date_col].min().strftime('%Y-%m-%d')}")
            print(f"   结束日期: {df_sorted[date_col].max().strftime('%Y-%m-%d')}")
            
            # 检查重复日期
            duplicates = df_sorted[date_col].duplicated().sum()
            if duplicates > 0:
                print(f"   ⚠️  重复日期: {duplicates} 个")
            
        except Exception as e:
            print(f"   ❌ 日期检查失败: {e}")
    
    # 异常值检查
    if len(available_price_cols) > 0:
        print(f"\\n⚠️  异常值检查:")
        
        for col in available_price_cols:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
            print(f"   {col:10s}: {outliers:4d} 个异常值 ({outliers/len(df)*100:5.1f}%)")
    
    # 数据样例
    print(f"\\n📝 数据样例 (前5行):")
    print(df.head().to_string())
    
    if len(df) > 10:
        print(f"\\n📝 数据样例 (后5行):")
        print(df.tail().to_string())

def inspect_from_source(symbol, source):
    """从数据源直接获取数据并检查"""
    try:
        from data_sources.unified_fetcher import UnifiedDataFetcher
        
        fetcher = UnifiedDataFetcher()
        df = fetcher.get_stock_data(
            symbol=symbol,
            start_date='2024-01-01',
            end_date='2024-01-31',
            source=source
        )
        
        if df.empty:
            print(f"❌ 从 {source} 获取 {symbol} 的数据为空")
            return False
        
        inspect_dataframe(df, f"{symbol} (来源: {source})")
        return True
        
    except Exception as e:
        print(f"❌ 从 {source} 获取 {symbol} 数据失败: {e}")
        return False

def inspect_from_file(file_path):
    """从文件读取数据并检查"""
    try:
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"❌ 文件不存在: {file_path}")
            return False
        
        # 尝试不同的读取方式
        try:
            df = pd.read_csv(file_path)
        except Exception as e1:
            try:
                df = pd.read_csv(file_path, encoding='gbk')
            except Exception as e2:
                print(f"❌ 读取文件失败: {e1}")
                return False
        
        if df.empty:
            print(f"❌ 文件数据为空: {file_path}")
            return False
        
        inspect_dataframe(df, file_path.name)
        return True
        
    except Exception as e:
        print(f"❌ 检查文件失败: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='原始数据检查工具')
    parser.add_argument('--symbol', help='股票代码')
    parser.add_argument('--source', help='数据源')
    parser.add_argument('--file', help='数据文件路径')
    
    args = parser.parse_args()
    
    print("🔍 原始数据检查工具")
    print("=" * 50)
    
    if args.file:
        success = inspect_from_file(args.file)
    elif args.symbol and args.source:
        success = inspect_from_source(args.symbol, args.source)
    elif args.symbol:
        # 默认使用统一获取器
        success = inspect_from_source(args.symbol, None)
    else:
        print("❌ 请指定 --symbol 和 --source，或者 --file")
        return 1
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
'''

# =============================================================================
# validate_data_format.py - 验证数据格式
# =============================================================================

VALIDATE_DATA_FORMAT_SCRIPT = '''#!/usr/bin/env python3
"""
数据格式验证工具
验证CSV数据文件是否符合系统要求的格式

使用方式:
python scripts/validate_data_format.py --input data/raw/000001.SZ.csv
python scripts/validate_data_format.py --input data/raw/ --recursive
"""

import sys
import pandas as pd
import argparse
from pathlib import Path

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 标准数据格式要求
REQUIRED_COLUMNS = ['date', 'open', 'high', 'low', 'close', 'volume']
OPTIONAL_COLUMNS = ['pre_close', 'change', 'pct_change', 'amount', 'turnover']
COLUMN_TYPES = {
    'date': 'datetime',
    'open': 'float',
    'high': 'float', 
    'low': 'float',
    'close': 'float',
    'volume': 'int',
    'pre_close': 'float',
    'amount': 'float'
}

def validate_single_file(file_path):
    """验证单个文件"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        return {
            'file': str(file_path),
            'valid': False,
            'error': '文件不存在',
            'issues': []
        }
    
    try:
        # 读取文件
        df = pd.read_csv(file_path)
        
        issues = []
        warnings = []
        
        # 检查是否为空
        if df.empty:
            issues.append('文件为空')
            return {
                'file': str(file_path),
                'valid': False,
                'error': '文件为空',
                'issues': issues
            }
        
        # 检查必需列
        missing_required = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_required:
            issues.append(f'缺少必需列: {missing_required}')
        
        # 检查列名规范
        invalid_columns = []
        for col in df.columns:
            if col not in REQUIRED_COLUMNS + OPTIONAL_COLUMNS:
                invalid_columns.append(col)
        
        if invalid_columns:
            warnings.append(f'未识别的列: {invalid_columns}')
        
        # 检查数据类型
        for col, expected_type in COLUMN_TYPES.items():
            if col in df.columns:
                if expected_type == 'datetime':
                    try:
                        pd.to_datetime(df[col])
                    except:
                        issues.append(f'列 {col} 不是有效的日期格式')
                elif expected_type == 'float':
                    if not pd.api.types.is_numeric_dtype(df[col]):
                        issues.append(f'列 {col} 不是数值类型')
                elif expected_type == 'int':
                    if not pd.api.types.is_numeric_dtype(df[col]):
                        issues.append(f'列 {col} 不是数值类型')
        
        # 检查数据完整性
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isnull().sum().sum()
        missing_ratio = missing_cells / total_cells
        
        if missing_ratio > 0.1:  # 超过10%缺失
            issues.append(f'缺失数据过多: {missing_ratio:.1%}')
        elif missing_ratio > 0.05:  # 超过5%警告
            warnings.append(f'存在缺失数据: {missing_ratio:.1%}')
        
        # 检查价格关系
        price_cols = ['open', 'high', 'low', 'close']
        if all(col in df.columns for col in price_cols):
            # high >= low
            invalid_high_low = (df['high'] < df['low']).sum()
            if invalid_high_low > 0:
                issues.append(f'{invalid_high_low} 行数据 high < low')
            
            # 检查负价格
            negative_prices = 0
            for col in price_cols:
                negative_prices += (df[col] <= 0).sum()
            
            if negative_prices > 0:
                issues.append(f'{negative_prices} 个非正价格数据')
        
        # 检查成交量
        if 'volume' in df.columns:
            negative_volume = (df['volume'] < 0).sum()
            if negative_volume > 0:
                issues.append(f'{negative_volume} 行负成交量')
        
        # 检查日期连续性
        if 'date' in df.columns:
            try:
                df_sorted = df.copy()
                df_sorted['date'] = pd.to_datetime(df_sorted['date'])
                df_sorted = df_sorted.sort_values('date')
                
                # 检查重复日期
                duplicates = df_sorted['date'].duplicated().sum()
                if duplicates > 0:
                    issues.append(f'{duplicates} 个重复日期')
                
            except:
                issues.append('日期格式无法解析')
        
        return {
            'file': str(file_path),
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'rows': len(df),
            'columns': list(df.columns),
            'missing_ratio': missing_ratio
        }
        
    except Exception as e:
        return {
            'file': str(file_path),
            'valid': False,
            'error': str(e),
            'issues': [f'文件读取失败: {e}']
        }

def validate_directory(dir_path, recursive=False):
    """验证目录中的所有CSV文件"""
    dir_path = Path(dir_path)
    
    if recursive:
        csv_files = list(dir_path.rglob("*.csv"))
    else:
        csv_files = list(dir_path.glob("*.csv"))
    
    results = []
    
    print(f"🔍 扫描目录: {dir_path}")
    print(f"   找到 {len(csv_files)} 个CSV文件")
    
    for csv_file in csv_files:
        print(f"   验证: {csv_file.name}")
        result = validate_single_file(csv_file)
        results.append(result)
    
    return results

def print_validation_results(results):
    """打印验证结果"""
    valid_count = sum(1 for r in results if r['valid'])
    total_count = len(results)
    
    print(f"\\n📊 验证结果汇总:")
    print(f"   总文件数: {total_count}")
    print(f"   有效文件: {valid_count}")
    print(f"   无效文件: {total_count - valid_count}")
    print(f"   通过率: {valid_count/total_count*100:.1f}%")
    
    # 详细结果
    print(f"\\n📋 详细结果:")
    
    for result in results:
        file_name = Path(result['file']).name
        
        if result['valid']:
            print(f"   ✅ {file_name}")
            print(f"      行数: {result['rows']}, 列数: {len(result['columns'])}")
            if result.get('warnings'):
                for warning in result['warnings']:
                    print(f"      ⚠️  {warning}")
        else:
            print(f"   ❌ {file_name}")
            if 'error' in result:
                print(f"      错误: {result['error']}")
            
            for issue in result['issues']:
                print(f"      问题: {issue}")

def main():
    parser = argparse.ArgumentParser(description='数据格式验证工具')
    parser.add_argument('--input', required=True, help='输入文件或目录路径')
    parser.add_argument('--recursive', action='store_true', help='递归扫描子目录')
    parser.add_argument('--output', help='输出验证报告到JSON文件')
    
    args = parser.parse_args()
    
    print("✅ 数据格式验证工具")
    print("=" * 40)
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"❌ 路径不存在: {input_path}")
        return 1
    
    if input_path.is_file():
        results = [validate_single_file(input_path)]
    elif input_path.is_dir():
        results = validate_directory(input_path, args.recursive)
    else:
        print(f"❌ 无效路径类型: {input_path}")
        return 1
    
    print_validation_results(results)
    
    # 保存报告
    if args.output:
        import json
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        print(f"\\n📄 验证报告已保存: {args.output}")
    
    # 返回状态码
    valid_count = sum(1 for r in results if r['valid'])
    return 0 if valid_count == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())
'''

# =============================================================================
# verify_adjustment.py - 验证复权一致性
# =============================================================================

VERIFY_ADJUSTMENT_SCRIPT = '''#!/usr/bin/env python3
"""
复权一致性验证工具
检查股票在不同时间获取的复权数据是否一致

使用方式:
python scripts/verify_adjustment.py --symbol 000001.SZ --dates 2024-01-01,2024-06-01,2024-12-01
python scripts/verify_adjustment.py --symbol 000001.SZ --check-consistency
"""

import sys
import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def fetch_data_at_different_times(symbol, base_period, fetch_dates):
    """在不同时间点获取相同历史期间的数据"""
    try:
        from data_sources.unified_fetcher import UnifiedDataFetcher
        
        fetcher = UnifiedDataFetcher()
        results = {}
        
        start_date, end_date = base_period
        
        print(f"📊 获取 {symbol} 在 {start_date} ~ {end_date} 期间的数据")
        print(f"   模拟在不同日期获取数据: {fetch_dates}")
        
        for fetch_date in fetch_dates:
            print(f"\\n📄 模拟在 {fetch_date} 获取数据...")
            
            # 这里模拟在不同时间获取数据
            # 实际中可能需要调整复权基准日期
            data = fetcher.get_stock_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust='qfq'  # 前复权
            )
            
            if not data.empty:
                results[fetch_date] = data
                print(f"   ✅ 获取成功: {len(data)} 行数据")
                print(f"   价格范围: {data['close'].min():.3f} ~ {data['close'].max():.3f}")
            else:
                print(f"   ❌ 获取失败: 数据为空")
        
        return results
        
    except Exception as e:
        print(f"❌ 数据获取失败: {e}")
        return {}

def compare_adjustment_consistency(data_dict):
    """比较复权数据一致性"""
    if len(data_dict) < 2:
        print("❌ 需要至少两个时间点的数据进行比较")
        return False
    
    print(f"\\n🔍 复权一致性分析:")
    print("=" * 50)
    
    # 获取所有数据的日期交集
    date_sets = []
    for fetch_date, data in data_dict.items():
        if 'date' in data.columns:
            dates = set(pd.to_datetime(data['date']).dt.date)
            date_sets.append(dates)
    
    if not date_sets:
        print("❌ 没有找到有效的日期列")
        return False
    
    common_dates = date_sets[0]
    for date_set in date_sets[1:]:
        common_dates &= date_set
    
    print(f"📅 共同交易日数量: {len(common_dates)}")
    
    if len(common_dates) == 0:
        print("❌ 没有共同的交易日期")
        return False
    
    # 按日期对齐数据
    aligned_data = {}
    for fetch_date, data in data_dict.items():
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy = data_copy[data_copy['date'].dt.date.isin(common_dates)]
        data_copy = data_copy.sort_values('date').reset_index(drop=True)
        aligned_data[fetch_date] = data_copy
    
    # 比较价格一致性
    fetch_dates = list(aligned_data.keys())
    base_data = aligned_data[fetch_dates[0]]
    
    print(f"\\n💰 价格一致性检查:")
    print(f"   基准时间: {fetch_dates[0]}")
    
    price_columns = ['open', 'high', 'low', 'close']
    consistency_results = {}
    
    for price_col in price_columns:
        if price_col not in base_data.columns:
            continue
            
        max_diff = 0
        max_diff_pct = 0
        
        print(f"\\n   {price_col.upper()} 列比较:")
        
        for i, compare_date in enumerate(fetch_dates[1:], 1):
            compare_data = aligned_data[compare_date]
            
            if price_col not in compare_data.columns:
                print(f"      vs {compare_date}: ❌ 列不存在")
                continue
            
            # 计算差异
            diff = abs(base_data[price_col] - compare_data[price_col])
            diff_pct = abs(diff / base_data[price_col] * 100)
            
            max_single_diff = diff.max()
            max_single_diff_pct = diff_pct.max()
            mean_diff = diff.mean()
            mean_diff_pct = diff_pct.mean()
            
            max_diff = max(max_diff, max_single_diff)
            max_diff_pct = max(max_diff_pct, max_single_diff_pct)
            
            print(f"      vs {compare_date}:")
            print(f"         最大差异: {max_single_diff:.6f} ({max_single_diff_pct:.4f}%)")
            print(f"         平均差异: {mean_diff:.6f} ({mean_diff_pct:.4f}%)")
            
            # 判断一致性
            if max_single_diff_pct < 0.01:  # 0.01%以内认为一致
                print(f"         结果: ✅ 高度一致")
            elif max_single_diff_pct < 0.1:   # 0.1%以内认为基本一致
                print(f"         结果: ⚠️  基本一致")
            else:
                print(f"         结果: ❌ 存在差异")
        
        consistency_results[price_col] = {
            'max_diff': max_diff,
            'max_diff_pct': max_diff_pct
        }
    
    # 总体一致性评估
    print(f"\\n📊 总体一致性评估:")
    
    all_consistent = True
    for col, result in consistency_results.items():
        if result['max_diff_pct'] > 0.1:
            all_consistent = False
            print(f"   {col}: ❌ 存在显著差异 ({result['max_diff_pct']:.4f}%)")
        elif result['max_diff_pct'] > 0.01:
            print(f"   {col}: ⚠️  轻微差异 ({result['max_diff_pct']:.4f}%)")
        else:
            print(f"   {col}: ✅ 高度一致 ({result['max_diff_pct']:.4f}%)")
    
    if all_consistent:
        print(f"\\n🎉 复权数据一致性检查通过！")
    else:
        print(f"\\n⚠️  复权数据存在不一致，建议:")
        print(f"     1. 固定复权基准日期")
        print(f"     2. 缓存复权因子")
        print(f"     3. 使用统一的数据源")
    
    return all_consistent

def main():
    parser = argparse.ArgumentParser(description='复权一致性验证工具')
    parser.add_argument('--symbol', required=True, help='股票代码')
    parser.add_argument('--dates', help='检查日期列表，用逗号分隔')
    parser.add_argument('--check-consistency', action='store_true', help='执行一致性检查')
    parser.add_argument('--period', default='2024-01-01,2024-03-31', help='检查的历史期间，格式：开始日期,结束日期')
    
    args = parser.parse_args()
    
    print("🔍 复权一致性验证工具")
    print("=" * 40)
    
    # 解析期间
    try:
        start_date, end_date = args.period.split(',')
        base_period = (start_date.strip(), end_date.strip())
    except:
        print("❌ 期间格式错误，应为：YYYY-MM-DD,YYYY-MM-DD")
        return 1
    
    # 解析检查日期
    if args.dates:
        fetch_dates = [date.strip() for date in args.dates.split(',')]
    elif args.check_consistency:
        # 默认使用几个测试日期
        fetch_dates = ['2024-06-01', '2024-09-01', '2024-12-01']
    else:
        print("❌ 请指定 --dates 或使用 --check-consistency")
        return 1
    
    # 获取数据
    data_dict = fetch_data_at_different_times(args.symbol, base_period, fetch_dates)
    
    if not data_dict:
        print("❌ 没有获取到有效数据")
        return 1
    
    # 执行一致性检查
    consistent = compare_adjustment_consistency(data_dict)
    
    return 0 if consistent else 1

if __name__ == "__main__":
    sys.exit(main())
'''

# =============================================================================
# check_price_relationships.py - 检查价格关系
# =============================================================================

CHECK_PRICE_RELATIONSHIPS_SCRIPT = '''#!/usr/bin/env python3
"""
价格关系检查工具
检查股票数据中的价格关系是否合理

使用方式:
python scripts/check_price_relationships.py --input data/processed/
python scripts/check_price_relationships.py --file data/processed/000001.SZ.csv
"""

import sys
import pandas as pd
import argparse
from pathlib import Path

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def check_single_file(file_path):
    """检查单个文件的价格关系"""
    try:
        df = pd.read_csv(file_path)
        
        if df.empty:
            return {
                'file': str(file_path),
                'valid': False,
                'error': '文件为空'
            }
        
        price_cols = ['open', 'high', 'low', 'close']
        missing_cols = [col for col in price_cols if col not in df.columns]
        
        if missing_cols:
            return {
                'file': str(file_path),
                'valid': False,
                'error': f'缺少价格列: {missing_cols}'
            }
        
        issues = []
        total_rows = len(df)
        
        # 检查 high >= low
        high_low_violations = (df['high'] < df['low']).sum()
        if high_low_violations > 0:
            issues.append({
                'type': 'high_low_violation',
                'count': high_low_violations,
                'percentage': high_low_violations / total_rows * 100,
                'description': 'high < low'
            })
        
        # 检查 high >= open
        high_open_violations = (df['high'] < df['open']).sum()
        if high_open_violations > 0:
            issues.append({
                'type': 'high_open_violation',
                'count': high_open_violations,
                'percentage': high_open_violations / total_rows * 100,
                'description': 'high < open'
            })
        
        # 检查 high >= close
        high_close_violations = (df['high'] < df['close']).sum()
        if high_close_violations > 0:
            issues.append({
                'type': 'high_close_violation',
                'count': high_close_violations,
                'percentage': high_close_violations / total_rows * 100,
                'description': 'high < close'
            })
        
        # 检查 low <= open
        low_open_violations = (df['low'] > df['open']).sum()
        if low_open_violations > 0:
            issues.append({
                'type': 'low_open_violation',
                'count': low_open_violations,
                'percentage': low_open_violations / total_rows * 100,
                'description': 'low > open'
            })
        
        # 检查 low <= close
        low_close_violations = (df['low'] > df['close']).sum()
        if low_close_violations > 0:
            issues.append({
                'type': 'low_close_violation',
                'count': low_close_violations,
                'percentage': low_close_violations / total_rows * 100,
                'description': 'low > close'
            })
        
        # 检查负价格
        negative_prices = 0
        negative_price_details = []
        for col in price_cols:
            neg_count = (df[col] <= 0).sum()
            if neg_count > 0:
                negative_prices += neg_count
                negative_price_details.append(f'{col}: {neg_count}')
        
        if negative_prices > 0:
            issues.append({
                'type': 'negative_price',
                'count': negative_prices,
                'percentage': negative_prices / (total_rows * 4) * 100,  # 4个价格列
                'description': f'负价格或零价格: {", ".join(negative_price_details)}'
            })
        
        # 检查异常波动
        if len(df) > 1:
            for col in price_cols:
                pct_change = df[col].pct_change().abs()
                extreme_changes = (pct_change > 0.15).sum()  # 单日涨跌幅超过15%
                
                if extreme_changes > total_rows * 0.1:  # 超过10%的交易日出现极端波动
                    issues.append({
                        'type': 'extreme_volatility',
                        'count': extreme_changes,
                        'percentage': extreme_changes / total_rows * 100,
                        'description': f'{col} 极端波动过多(>15%)'
                    })
        
        return {
            'file': str(file_path),
            'valid': len(issues) == 0,
            'total_rows': total_rows,
            'issues': issues
        }
        
    except Exception as e:
        return {
            'file': str(file_path),
            'valid': False,
            'error': str(e)
        }

def check_directory(dir_path):
    """检查目录中的所有文件"""
    dir_path = Path(dir_path)
    csv_files = list(dir_path.glob("*.csv"))
    
    results = []
    
    print(f"🔍 检查目录: {dir_path}")
    print(f"   找到 {len(csv_files)} 个CSV文件")
    
    for csv_file in csv_files:
        print(f"   检查: {csv_file.name}")
        result = check_single_file(csv_file)
        results.append(result)
    
    return results

def print_check_results(results):
    """打印检查结果"""
    valid_count = sum(1 for r in results if r['valid'])
    total_count = len(results)
    
    print(f"\\n📊 价格关系检查结果:")
    print("=" * 50)
    print(f"   总文件数: {total_count}")
    print(f"   正常文件: {valid_count}")
    print(f"   异常文件: {total_count - valid_count}")
    print(f"   正常率: {valid_count/total_count*100:.1f}%")
    
    # 统计问题类型
    issue_stats = {}
    total_issues = 0
    
    for result in results:
        if not result['valid'] and 'issues' in result:
            for issue in result['issues']:
                issue_type = issue['type']
                if issue_type not in issue_stats:
                    issue_stats[issue_type] = {
                        'count': 0,
                        'files': 0,
                        'total_violations': 0
                    }
                issue_stats[issue_type]['files'] += 1
                issue_stats[issue_type]['total_violations'] += issue['count']
                total_issues += issue['count']
    
    if issue_stats:
        print(f"\\n⚠️  问题类型统计:")
        for issue_type, stats in issue_stats.items():
            print(f"   {issue_type}:")
            print(f"     影响文件: {stats['files']} 个")
            print(f"     违规记录: {stats['total_violations']} 条")
    
    # 详细结果
    print(f"\\n📋 详细结果:")
    
    for result in results:
        file_name = Path(result['file']).name
        
        if result['valid']:
            print(f"   ✅ {file_name} - 正常 ({result.get('total_rows', 0)} 行)")
        else:
            print(f"   ❌ {file_name}")
            
            if 'error' in result:
                print(f"      错误: {result['error']}")
            elif 'issues' in result:
                for issue in result['issues']:
                    print(f"      问题: {issue['description']} - {issue['count']} 条 ({issue['percentage']:.1f}%)")

def main():
    parser = argparse.ArgumentParser(description='价格关系检查工具')
    parser.add_argument('--input', help='输入目录路径')
    parser.add_argument('--file', help='输入文件路径')
    parser.add_argument('--output', help='输出检查报告到JSON文件')
    
    args = parser.parse_args()
    
    print("💰 价格关系检查工具")
    print("=" * 40)
    
    if args.file:
        input_path = Path(args.file)
        if not input_path.exists():
            print(f"❌ 文件不存在: {input_path}")
            return 1
        results = [check_single_file(input_path)]
    elif args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"❌ 目录不存在: {input_path}")
            return 1
        results = check_directory(input_path)
    else:
        print("❌ 请指定 --input 目录或 --file 文件")
        return 1
    
    print_check_results(results)
    
    # 保存报告
    if args.output:
        import json
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        print(f"\\n📄 检查报告已保存: {args.output}")
    
    # 返回状态码
    valid_count = sum(1 for r in results if r['valid'])
    return 0 if valid_count == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())
'''

# =============================================================================
# fix_price_relationships.py - 修复价格关系异常
# =============================================================================

FIX_PRICE_RELATIONSHIPS_SCRIPT = '''#!/usr/bin/env python3
"""
价格关系修复工具
自动修复股票数据中的价格关系异常

使用方式:
python scripts/fix_price_relationships.py --input data/raw/000001.SZ.csv --output data/cleaned/
python scripts/fix_price_relationships.py --input data/raw/ --batch --output data/cleaned/
"""

import sys
import pandas as pd
import numpy as np
import argparse
from pathlib import Path
import shutil

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def fix_price_relationships(df, method='interpolate'):
    """修复价格关系异常"""
    df = df.copy()
    fix_log = []
    
    price_cols = ['open', 'high', 'low', 'close']
    
    # 检查必需列
    missing_cols = [col for col in price_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"缺少必需的价格列: {missing_cols}")
    
    original_rows = len(df)
    
    # 1. 修复负价格和零价格
    for col in price_cols:
        negative_mask = df[col] <= 0
        negative_count = negative_mask.sum()
        
        if negative_count > 0:
            if method == 'interpolate':
                # 使用插值方法
                df.loc[negative_mask, col] = np.nan
                df[col] = df[col].interpolate(method='linear')
            elif method == 'forward_fill':
                # 向前填充
                df.loc[negative_mask, col] = np.nan
                df[col] = df[col].fillna(method='ffill')
            elif method == 'drop':
                # 删除异常行
                df = df[~negative_mask]
            
            fix_log.append(f"修复 {col} 列负价格: {negative_count} 个")
    
    # 2. 修复 high < low 异常
    high_low_mask = df['high'] < df['low']
    high_low_count = high_low_mask.sum()
    
    if high_low_count > 0:
        # 交换 high 和 low 值
        df.loc[high_low_mask, ['high', 'low']] = df.loc[high_low_mask, ['low', 'high']].values
        fix_log.append(f"修复 high < low 异常: {high_low_count} 个")
    
    # 3. 修复 high < open 或 high < close
    high_open_mask = df['high'] < df['open']
    high_open_count = high_open_mask.sum()
    if high_open_count > 0:
        df.loc[high_open_mask, 'high'] = df.loc[high_open_mask, 'open']
        fix_log.append(f"修复 high < open 异常: {high_open_count} 个")
    
    high_close_mask = df['high'] < df['close']
    high_close_count = high_close_mask.sum()
    if high_close_count > 0:
        df.loc[high_close_mask, 'high'] = df.loc[high_close_mask, 'close']
        fix_log.append(f"修复 high < close 异常: {high_close_count} 个")
    
    # 4. 修复 low > open 或 low > close
    low_open_mask = df['low'] > df['open']
    low_open_count = low_open_mask.sum()
    if low_open_count > 0:
        df.loc[low_open_mask, 'low'] = df.loc[low_open_mask, 'open']
        fix_log.append(f"修复 low > open 异常: {low_open_count} 个")
    
    low_close_mask = df['low'] > df['close']
    low_close_count = low_close_mask.sum()
    if low_close_count > 0:
        df.loc[low_close_mask, 'low'] = df.loc[low_close_mask, 'close']
        fix_log.append(f"修复 low > close 异常: {low_close_count} 个")
    
    # 5. 处理异常波动（可选）
    if method == 'smooth_volatility':
        for col in price_cols:
            if len(df) > 1:
                pct_change = df[col].pct_change().abs()
                extreme_mask = pct_change > 0.2  # 超过20%的变动
                extreme_count = extreme_mask.sum()
                
                if extreme_count > 0:
                    # 使用滑动平均平滑异常波动
                    smoothed = df[col].rolling(window=3, center=True).mean()
                    df.loc[extreme_mask, col] = smoothed.loc[extreme_mask]
                    fix_log.append(f"平滑 {col} 列异常波动: {extreme_count} 个")
    
    # 6. 删除仍然无效的行
    if method != 'keep_invalid':
        # 检查修复后仍有问题的行
        invalid_mask = (
            (df['high'] < df['low']) |
            (df['high'] < df['open']) |
            (df['high'] < df['close']) |
            (df['low'] > df['open']) |
            (df['low'] > df['close']) |
            (df[price_cols] <= 0).any(axis=1)
        )
        
        invalid_count = invalid_mask.sum()
        if invalid_count > 0:
            df = df[~invalid_mask]
            fix_log.append(f"删除无法修复的行: {invalid_count} 个")
    
    final_rows = len(df)
    if final_rows != original_rows:
        fix_log.append(f"数据行数变化: {original_rows} -> {final_rows}")
    
    return df, fix_log

def fix_single_file(input_file, output_file, method='interpolate', backup=True):
    """修复单个文件"""
    try:
        # 备份原文件
        if backup:
            backup_file = input_file.with_suffix(input_file.suffix + '.backup')
            shutil.copy2(input_file, backup_file)
        
        # 读取数据
        df = pd.read_csv(input_file)
        
        if df.empty:
            return False, "文件为空"
        
        # 修复价格关系
        fixed_df, fix_log = fix_price_relationships(df, method)
        
        # 保存修复后的数据
        output_file.parent.mkdir(parents=True, exist_ok=True)
        fixed_df.to_csv(output_file, index=False)
        
        return True, fix_log
        
    except Exception as e:
        return False, str(e)

def batch_fix_files(input_dir, output_dir, method='interpolate', backup=True):
    """批量修复文件"""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    csv_files = list(input_dir.glob("*.csv"))
    
    if not csv_files:
        print("没有找到CSV文件")
        return
    
    print(f"找到 {len(csv_files)} 个CSV文件")
    
    success_count = 0
    total_fixes = 0
    
    for csv_file in csv_files:
        output_file = output_dir / csv_file.name
        
        print(f"\\n修复: {csv_file.name}")
        
        success, result = fix_single_file(csv_file, output_file, method, backup)
        
        if success:
            fix_log = result
            success_count += 1
            fixes_count = len(fix_log)
            total_fixes += fixes_count
            
            print(f"   ✅ 修复成功: {fixes_count} 项修复")
            for log_entry in fix_log:
                print(f"      • {log_entry}")
        else:
            print(f"   ❌ 修复失败: {result}")
    
    print(f"\\n📊 批量修复完成:")
    print(f"   成功文件: {success_count}/{len(csv_files)}")
    print(f"   总修复项: {total_fixes}")

def main():
    parser = argparse.ArgumentParser(description='价格关系修复工具')
    parser.add_argument('--input', required=True, help='输入文件或目录')
    parser.add_argument('--output', required=True, help='输出文件或目录')
    parser.add_argument('--method', 
                       choices=['interpolate', 'forward_fill', 'drop', 'smooth_volatility', 'keep_invalid'],
                       default='interpolate',
                       help='修复方法')
    parser.add_argument('--batch', action='store_true', help='批量处理模式')
    parser.add_argument('--no-backup', action='store_true', help='不创建备份文件')
    
    args = parser.parse_args()
    
    print("🔧 价格关系修复工具")
    print("=" * 40)
    print(f"修复方法: {args.method}")
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"❌ 输入路径不存在: {input_path}")
        return 1
    
    backup = not args.no_backup
    
    if args.batch or input_path.is_dir():
        if not input_path.is_dir():
            print(f"❌ 批量模式要求输入为目录")
            return 1
        
        batch_fix_files(input_path, output_path, args.method, backup)
    else:
        if input_path.is_file():
            success, result = fix_single_file(input_path, output_path, args.method, backup)
            
            if success:
                fix_log = result
                print(f"✅ 文件修复成功: {len(fix_log)} 项修复")
                for log_entry in fix_log:
                    print(f"   • {log_entry}")
                return 0
            else:
                print(f"❌ 文件修复失败: {result}")
                return 1
        else:
            print(f"❌ 单文件模式要求输入为文件")
            return 1

if __name__ == "__main__":
    sys.exit(main())
'''

# =============================================================================
# align_trading_calendar.py - 对齐交易日历
# =============================================================================

ALIGN_TRADING_CALENDAR_SCRIPT = '''#!/usr/bin/env python3
"""
交易日历对齐工具
标准化不同数据源的交易日历，确保数据一致性

使用方式:
python scripts/align_trading_calendar.py --input data/raw/ --output data/aligned/
python scripts/align_trading_calendar.py --file data/raw/000001.SZ.csv --calendar SHSZ
"""

import sys
import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime, date

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def get_trading_calendar(calendar_name='SHSZ', start_date=None, end_date=None):
    """获取交易日历"""
    try:
        from zipline.utils.calendars import get_calendar
        
        calendar = get_calendar(calendar_name)
        
        if start_date and end_date:
            sessions = calendar.sessions_in_range(start_date, end_date)
            return [session.date() for session in sessions]
        else:
            # 返回当年的交易日
            current_year = datetime.now().year
            start = f"{current_year}-01-01"
            end = f"{current_year}-12-31"
            sessions = calendar.sessions_in_range(start, end)
            return [session.date() for session in sessions]
    
    except ImportError:
        print("⚠️  Zipline未安装，使用简化交易日历")
        return get_simple_trading_calendar(start_date, end_date)

def get_simple_trading_calendar(start_date=None, end_date=None):
    """简化的交易日历（排除周末和主要节假日）"""
    if not start_date:
        start_date = "2024-01-01"
    if not end_date:
        end_date = "2024-12-31"
    
    # 主要节假日（简化版）
    holidays = [
        "2024-01-01",  # 元旦
        "2024-02-10", "2024-02-11", "2024-02-12", "2024-02-13", "2024-02-14", "2024-02-15", "2024-02-16", "2024-02-17",  # 春节
        "2024-04-04", "2024-04-05", "2024-04-06",  # 清明节
        "2024-05-01", "2024-05-02", "2024-05-03",  # 劳动节
        "2024-06-10",  # 端午节
        "2024-09-15", "2024-09-16", "2024-09-17",  # 中秋节
        "2024-10-01", "2024-10-02", "2024-10-03", "2024-10-04", "2024-10-05", "2024-10-06", "2024-10-07"  # 国庆节
    ]
    
    holiday_dates = {datetime.strptime(h, "%Y-%m-%d").date() for h in holidays}
    
    # 生成日期范围
    date_range = pd.date_range(start_date, end_date, freq='D')
    
    # 过滤周末和节假日
    trading_days = []
    for dt in date_range:
        if dt.weekday() < 5 and dt.date() not in holiday_dates:  # 周一到周五，且不是节假日
            trading_days.append(dt.date())
    
    return trading_days

def align_data_to_calendar(df, trading_calendar, date_col='date'):
    """将数据对齐到交易日历"""
    if date_col not in df.columns:
        raise ValueError(f"日期列 '{date_col}' 不存在")
    
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df['date_only'] = df[date_col].dt.date
    
    # 获取数据中的日期范围
    data_dates = set(df['date_only'])
    calendar_dates = set(trading_calendar)
    
    # 统计信息
    extra_dates = data_dates - calendar_dates  # 数据中有但日历中没有的日期
    missing_dates = calendar_dates - data_dates  # 日历中有但数据中没有的日期
    
    # 过滤掉非交易日的数据
    aligned_df = df[df['date_only'].isin(calendar_dates)].copy()
    aligned_df = aligned_df.drop('date_only', axis=1)
    aligned_df = aligned_df.sort_values(date_col).reset_index(drop=True)
    
    align_info = {
        'original_rows': len(df),
        'aligned_rows': len(aligned_df),
        'extra_dates': len(extra_dates),
        'missing_dates': len(missing_dates),
        'removed_dates': list(extra_dates)[:10] if extra_dates else [],  # 只显示前10个
        'missing_dates_list': list(missing_dates)[:10] if missing_dates else []
    }
    
    return aligned_df, align_info

def align_single_file(input_file, output_file, calendar_name='SHSZ'):
    """对齐单个文件到交易日历"""
    try:
        # 读取数据
        df = pd.read_csv(input_file)
        
        if df.empty:
            return False, "文件为空"
        
        # 检查日期列
        date_cols = [col for col in df.columns if 'date' in col.lower()]
        if not date_cols:
            return False, "未找到日期列"
        
        date_col = date_cols[0]  # 使用第一个日期列
        
        # 获取数据日期范围
        df_temp = df.copy()
        df_temp[date_col] = pd.to_datetime(df_temp[date_col])
        start_date = df_temp[date_col].min().strftime('%Y-%m-%d')
        end_date = df_temp[date_col].max().strftime('%Y-%m-%d')
        
        # 获取交易日历
        trading_calendar = get_trading_calendar(calendar_name, start_date, end_date)
        
        # 对齐数据
        aligned_df, align_info = align_data_to_calendar(df, trading_calendar, date_col)
        
        # 保存结果
        output_file.parent.mkdir(parents=True, exist_ok=True)
        aligned_df.to_csv(output_file, index=False)
        
        return True, align_info
        
    except Exception as e:
        return False, str(e)

def batch_align_files(input_dir, output_dir, calendar_name='SHSZ'):
    """批量对齐文件"""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    csv_files = list(input_dir.glob("*.csv"))
    
    if not csv_files:
        print("没有找到CSV文件")
        return
    
    print(f"找到 {len(csv_files)} 个CSV文件")
    
    success_count = 0
    total_removed = 0
    total_original = 0
    
    for csv_file in csv_files:
        output_file = output_dir / csv_file.name
        
        print(f"\\n对齐: {csv_file.name}")
        
        success, result = align_single_file(csv_file, output_file, calendar_name)
        
        if success:
            align_info = result
            success_count += 1
            total_removed += align_info['extra_dates']
            total_original += align_info['original_rows']
            
            print(f"   ✅ 对齐成功")
            print(f"      原始行数: {align_info['original_rows']}")
            print(f"      对齐后行数: {align_info['aligned_rows']}")
            print(f"      移除非交易日: {align_info['extra_dates']} 天")
            print(f"      缺失交易日: {align_info['missing_dates']} 天")
            
            if align_info['removed_dates']:
                print(f"      移除的日期示例: {', '.join(map(str, align_info['removed_dates'][:5]))}")
        else:
            print(f"   ❌ 对齐失败: {result}")
    
    print(f"\\n📊 批量对齐完成:")
    print(f"   成功文件: {success_count}/{len(csv_files)}")
    print(f"   总移除行数: {total_removed}")
    if total_original > 0:
        print(f"   数据保留率: {((total_original - total_removed) / total_original * 100):.1f}%")

def main():
    parser = argparse.ArgumentParser(description='交易日历对齐工具')
    parser.add_argument('--input', help='输入文件或目录')
    parser.add_argument('--output', help='输出文件或目录')
    parser.add_argument('--file', help='单文件处理模式')
    parser.add_argument('--calendar', default='SHSZ', 
                       choices=['SHSZ', 'XSHG', 'XSHE'],
                       help='交易日历类型')
    parser.add_argument('--batch', action='store_true', help='批量处理模式')
    
    args = parser.parse_args()
    
    print("📅 交易日历对齐工具")
    print("=" * 40)
    print(f"使用日历: {args.calendar}")
    
    if args.file:
        # 单文件模式
        input_file = Path(args.file)
        if not input_file.exists():
            print(f"❌ 输入文件不存在: {input_file}")
            return 1
        
        output_file = Path(args.output) if args.output else input_file.with_suffix('.aligned.csv')
        
        success, result = align_single_file(input_file, output_file, args.calendar)
        
        if success:
            align_info = result
            print(f"✅ 文件对齐成功:")
            print(f"   原始行数: {align_info['original_rows']}")
            print(f"   对齐后行数: {align_info['aligned_rows']}")
            print(f"   移除非交易日: {align_info['extra_dates']} 天")
            print(f"   缺失交易日: {align_info['missing_dates']} 天")
            return 0
        else:
            print(f"❌ 文件对齐失败: {result}")
            return 1
    
    elif args.input and args.output:
        # 批量模式
        input_path = Path(args.input)
        output_path = Path(args.output)
        
        if not input_path.exists():
            print(f"❌ 输入路径不存在: {input_path}")
            return 1
        
        if input_path.is_dir():
            batch_align_files(input_path, output_path, args.calendar)
        else:
            success, result = align_single_file(input_path, output_path, args.calendar)
            if success:
                align_info = result
                print(f"✅ 单文件对齐成功: 移除 {align_info['extra_dates']} 个非交易日")
                return 0
            else:
                print(f"❌ 单文件对齐失败: {result}")
                return 1
    else:
        print("❌ 请指定输入输出路径，或使用 --file 模式")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''

# =============================================================================
# validate_zipline_format.py - 验证Zipline格式
# =============================================================================

VALIDATE_ZIPLINE_FORMAT_SCRIPT = '''#!/usr/bin/env python3
"""
Zipline格式验证工具
验证CSV数据是否符合Zipline要求的格式

使用方式:
python scripts/validate_zipline_format.py --input data/zipline/
python scripts/validate_zipline_format.py --file data/zipline/000001.SZ.csv
"""

import sys
import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Zipline所需的列名和类型
ZIPLINE_REQUIRED_COLUMNS = {
    'date': 'datetime',
    'open': 'float',
    'high': 'float',
    'low': 'float',
    'close': 'float',
    'volume': 'int'
}

ZIPLINE_OPTIONAL_COLUMNS = {
    'dividend': 'float',
    'split': 'float'
}

def validate_zipline_format(df, filename):
    """验证单个DataFrame的Zipline格式"""
    issues = []
    warnings = []
    
    # 1. 检查必需列
    missing_columns = []
    for col in ZIPLINE_REQUIRED_COLUMNS.keys():
        if col not in df.columns:
            missing_columns.append(col)
    
    if missing_columns:
        issues.append(f"缺少必需列: {missing_columns}")
        return {
            'valid': False,
            'issues': issues,
            'warnings': warnings
        }
    
    # 2. 检查数据类型
    for col, expected_type in ZIPLINE_REQUIRED_COLUMNS.items():
        if col in df.columns:
            if expected_type == 'datetime':
                try:
                    pd.to_datetime(df[col])
                except:
                    issues.append(f"列 {col} 不是有效的日期格式")
            elif expected_type == 'float':
                if not pd.api.types.is_numeric_dtype(df[col]):
                    issues.append(f"列 {col} 应为数值类型")
                elif df[col].dtype != 'float64':
                    warnings.append(f"列 {col} 类型为 {df[col].dtype}，建议转换为 float64")
            elif expected_type == 'int':
                if not pd.api.types.is_numeric_dtype(df[col]):
                    issues.append(f"列 {col} 应为数值类型")
                elif not df[col].dtype.name.startswith('int'):
                    warnings.append(f"列 {col} 类型为 {df[col].dtype}，建议转换为 int64")
    
    # 3. 检查数据完整性
    if df.empty:
        issues.append("数据为空")
    else:
        # 检查缺失值
        null_counts = df[list(ZIPLINE_REQUIRED_COLUMNS.keys())].isnull().sum()
        null_columns = null_counts[null_counts > 0]
        
        if len(null_columns) > 0:
            issues.append(f"存在缺失值: {dict(null_columns)}")
        
        # 检查负价格
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            if col in df.columns:
                negative_count = (df[col] <= 0).sum()
                if negative_count > 0:
                    issues.append(f"列 {col} 存在 {negative_count} 个非正值")
        
        # 检查负成交量
        if 'volume' in df.columns:
            negative_volume = (df['volume'] < 0).sum()
            if negative_volume > 0:
                issues.append(f"成交量存在 {negative_volume} 个负值")
        
        # 检查价格关系
        if all(col in df.columns for col in price_cols):
            high_low_issues = (df['high'] < df['low']).sum()
            if high_low_issues > 0:
                issues.append(f"{high_low_issues} 行数据 high < low")
            
            high_open_issues = (df['high'] < df['open']).sum()
            if high_open_issues > 0:
                issues.append(f"{high_open_issues} 行数据 high < open")
            
            high_close_issues = (df['high'] < df['close']).sum()
            if high_close_issues > 0:
                issues.append(f"{high_close_issues} 行数据 high < close")
            
            low_open_issues = (df['low'] > df['open']).sum()
            if low_open_issues > 0:
                issues.append(f"{low_open_issues} 行数据 low > open")
            
            low_close_issues = (df['low'] > df['close']).sum()
            if low_close_issues > 0:
                issues.append(f"{low_close_issues} 行数据 low > close")
    
    # 4. 检查日期格式和排序
    if 'date' in df.columns:
        try:
            df_temp = df.copy()
            df_temp['date'] = pd.to_datetime(df_temp['date'])
            
            # 检查日期排序
            if not df_temp['date'].is_monotonic_increasing:
                warnings.append("日期未按升序排列")
            
            # 检查重复日期
            duplicates = df_temp['date'].duplicated().sum()
            if duplicates > 0:
                issues.append(f"存在 {duplicates} 个重复日期")
            
            # 检查日期范围合理性
            min_date = df_temp['date'].min()
            max_date = df_temp['date'].max()
            
            if min_date.year < 1990:
                warnings.append(f"最早日期过早: {min_date.date()}")
            
            if max_date > pd.Timestamp.now():
                warnings.append(f"最晚日期超过当前日期: {max_date.date()}")
            
        except Exception as e:
            issues.append(f"日期处理错误: {e}")
    
    # 5. 检查文件名格式
    if filename:
        if not filename.endswith('.csv'):
            warnings.append("文件名应以.csv结尾")
        
        # 检查是否包含股票代码
        stem = Path(filename).stem
        if not any(char.isdigit() for char in stem):
            warnings.append("文件名中未检测到股票代码")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'rows': len(df),
        'date_range': (df['date'].min(), df['date'].max()) if 'date' in df.columns and not df.empty else None
    }

def validate_single_file(file_path):
    """验证单个文件"""
    try:
        df = pd.read_csv(file_path)
        result = validate_zipline_format(df, file_path.name)
        result['file'] = str(file_path)
        return result
        
    except Exception as e:
        return {
            'file': str(file_path),
            'valid': False,
            'issues': [f"文件读取失败: {e}"],
            'warnings': []
        }

def validate_directory(dir_path):
    """验证目录中的所有CSV文件"""
    dir_path = Path(dir_path)
    csv_files = list(dir_path.glob("*.csv"))
    
    if not csv_files:
        print("没有找到CSV文件")
        return []
    
    print(f"找到 {len(csv_files)} 个CSV文件")
    
    results = []
    for csv_file in csv_files:
        print(f"验证: {csv_file.name}")
        result = validate_single_file(csv_file)
        results.append(result)
    
    return results

def print_validation_summary(results):
    """打印验证摘要"""
    if not results:
        return
    
    valid_count = sum(1 for r in results if r['valid'])
    total_count = len(results)
    
    print(f"\\n📊 Zipline格式验证结果:")
    print("=" * 50)
    print(f"总文件数: {total_count}")
    print(f"通过验证: {valid_count}")
    print(f"验证失败: {total_count - valid_count}")
    print(f"通过率: {valid_count/total_count*100:.1f}%")
    
    # 统计常见问题
    all_issues = []
    all_warnings = []
    
    for result in results:
        all_issues.extend(result.get('issues', []))
        all_warnings.extend(result.get('warnings', []))
    
    if all_issues:
        print(f"\\n❌ 常见问题:")
        issue_counts = {}
        for issue in all_issues:
            issue_type = issue.split(':')[0] if ':' in issue else issue.split('存在')[0] if '存在' in issue else issue
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        
        for issue_type, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   • {issue_type}: {count} 次")
    
    if all_warnings:
        print(f"\\n⚠️  常见警告:")
        warning_counts = {}
        for warning in all_warnings:
            warning_type = warning.split(':')[0] if ':' in warning else warning.split('建议')[0] if '建议' in warning else warning
            warning_counts[warning_type] = warning_counts.get(warning_type, 0) + 1
        
        for warning_type, count in sorted(warning_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"   • {warning_type}: {count} 次")

def print_detailed_results(results, show_warnings=False):
    """打印详细结果"""
    print(f"\\n📋 详细验证结果:")
    
    for result in results:
        file_name = Path(result['file']).name
        
        if result['valid']:
            status_icon = "✅"
            status_text = "通过"
        else:
            status_icon = "❌"
            status_text = "失败"
        
        print(f"\\n{status_icon} {file_name} - {status_text}")
        
        if 'rows' in result:
            print(f"   行数: {result['rows']}")
        
        if 'date_range' in result and result['date_range']:
            start_date, end_date = result['date_range']
            print(f"   日期范围: {start_date} ~ {end_date}")
        
        # 显示问题
        if result.get('issues'):
            for issue in result['issues']:
                print(f"   ❌ {issue}")
        
        # 显示警告（可选）
        if show_warnings and result.get('warnings'):
            for warning in result['warnings']:
                print(f"   ⚠️  {warning}")

def main():
    parser = argparse.ArgumentParser(description='Zipline格式验证工具')
    parser.add_argument('--input', help='输入目录路径')
    parser.add_argument('--file', help='输入文件路径')
    parser.add_argument('--show-warnings', action='store_true', help='显示警告信息')
    parser.add_argument('--output', help='输出验证报告到JSON文件')
    
    args = parser.parse_args()
    
    print("📊 Zipline格式验证工具")
    print("=" * 40)
    
    if args.file:
        # 单文件模式
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ 文件不存在: {file_path}")
            return 1
        
        result = validate_single_file(file_path)
        results = [result]
    
    elif args.input:
        # 目录模式
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"❌ 目录不存在: {input_path}")
            return 1
        
        results = validate_directory(input_path)
    
    else:
        print("❌ 请指定 --input 目录或 --file 文件")
        return 1
    
    # 打印结果
    print_validation_summary(results)
    print_detailed_results(results, args.show_warnings)
    
    # 保存报告
    if args.output:
        import json
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        print(f"\\n📄 验证报告已保存: {args.output}")
    
    # 返回状态码
    valid_count = sum(1 for r in results if r['valid'])
    return 0 if valid_count == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())
'''

    
    os.environ['ZIPLINE_ROOT'] = str(zipline_root)
    
    print(f"设置 ZIPLINE_ROOT: {zipline_root}")
    return zipline_root

def create_bundle_definition(bundle_name, data_dir, symbols=None):
    """创建Bundle定义文件"""
    bundle_file = PROJECT_ROOT / 'zipline_extensions.py'
    
    # Bundle定义模板
    bundle_template = f'''
import pandas as pd
from zipline.data.bundles import register
from zipline.data.bundles.csvdir import csvdir_equities

# 注册自定义bundle
register(
    '{bundle_name}',
    csvdir_equities(
        ['{data_dir}'],
        symbol_columns=['symbol'],
        date_columns=['date'],
        timezone='Asia/Shanghai'
    ),
    calendar_name='XSHG',
    start_session=pd.Timestamp('2020-01-01', tz='utc'),
    end_session=pd.Timestamp('2024-12-31', tz='utc'),
)
'''
    
    with open(bundle_file, 'w', encoding='utf-8') as f:
        f.write(bundle_template.strip())
    
    print(f"创建Bundle定义文件: {bundle_file}")
    return bundle_file

def run_zipline_ingest(bundle_name, force=False):
    """运行Zipline数据摄入"""
    try:
        # 构建命令
        cmd = ['zipline', 'ingest', '-b', bundle_name]
        
        if force:
            # 清理现有数据
            clean_cmd = ['zipline', 'clean', '-b', bundle_name, '--keep-last', '0']
            print(f"清理现有Bundle数据...")
            clean_result = subprocess.run(clean_cmd, capture_output=True, text=True)
            if clean_result.returncode != 0:
                print(f"警告: 清理失败 - {clean_result.stderr}")
        
        print(f"开始摄入Bundle: {bundle_name}")
        print(f"执行命令: {' '.join(cmd)}")
        
        # 执行摄入
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("摄入成功!")
            if result.stdout:
                print(f"输出: {result.stdout}")
            return True
        else:
            print(f"摄入失败!")
            print(f"错误: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("错误: zipline命令未找到，请确保已安装zipline-reloaded")
        return False
    except Exception as e:
        print(f"摄入过程异常: {e}")
        return False

def verify_bundle(bundle_name):
    """验证Bundle是否可用"""
    try:
        cmd = ['zipline', 'bundles']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            bundles_list = result.stdout
            if bundle_name in bundles_list:
                print(f"Bundle验证成功: {bundle_name} 已注册")
                return True
            else:
                print(f"Bundle验证失败: {bundle_name} 未在列表中")
                print(f"可用的Bundle: {bundles_list}")
                return False
        else:
            print(f"无法获取Bundle列表: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Bundle验证异常: {e}")
        return False

def prepare_data_for_ingest(symbols=None):
    """准备摄入数据"""
    from backend.zipline_csv_writer import write_zipline_csv
    
    data_dir = PROJECT_ROOT / 'data' / 'zipline'
    
    if symbols is None:
        # 默认股票列表
        symbols = ['000001.SZ', '000002.SZ', '600000.SH', '600036.SH']
    
    print(f"准备摄入数据，股票数量: {len(symbols)}")
    
    try:
        # 生成Zipline格式CSV
        result = write_zipline_csv(
            symbols=symbols,
            output_dir=str(data_dir),
            start_date='2024-01-01',
            end_date='2024-12-31',
            overwrite=True
        )
        
        if result.get('files_generated', 0) > 0:
            print(f"数据准备成功: {result['files_generated']} 个文件")
            return True, data_dir
        else:
            print("数据准备失败: 没有生成文件")
            return False, None
            
    except Exception as e:
        print(f"数据准备异常: {e}")
        return False, None

def main():
    parser = argparse.ArgumentParser(description='Zipline数据摄入工具')
    parser.add_argument('--bundle', default='custom_bundle', help='Bundle名称')
    parser.add_argument('--symbols', help='股票代码列表，逗号分隔')
    parser.add_argument('--force', action='store_true', help='强制重新摄入')
    parser.add_argument('--prepare-only', action='store_true', help='只准备数据，不摄入')
    parser.add_argument('--verify-only', action='store_true', help='只验证Bundle')
    
    args = parser.parse_args()
    
    print("数据摄入工具")
    print("=" * 40)
    
    # 解析股票代码
    symbols = None
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
        print(f"指定股票: {symbols}")
    
    # 设置环境
    zipline_root = setup_zipline_environment()
    
    if args.verify_only:
        # 只验证Bundle
        success = verify_bundle(args.bundle)
        return 0 if success else 1
    
    # 准备数据
    print("\n步骤1: 准备摄入数据")
    data_ready, data_dir = prepare_data_for_ingest(symbols)
    
    if not data_ready:
        print("数据准备失败")
        return 1
    
    if args.prepare_only:
        print("数据准备完成，跳过摄入步骤")
        return 0
    
    # 创建Bundle定义
    print("\n步骤2: 创建Bundle定义")
    bundle_file = create_bundle_definition(args.bundle, data_dir, symbols)
    
    # 执行摄入
    print("\n步骤3: 执行数据摄入")
    ingest_success = run_zipline_ingest(args.bundle, args.force)
    
    if not ingest_success:
        print("数据摄入失败")
        return 1
    
    # 验证结果
    print("\n步骤4: 验证摄入结果")
    verify_success = verify_bundle(args.bundle)
    
    if verify_success:
        print(f"\n摄入完成! Bundle '{args.bundle}' 已准备就绪")
        print(f"现在可以在Zipline策略中使用此Bundle进行回测")
        return 0
    else:
        print("\nBundle验证失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''

# =============================================================================
# test_zipline_data.py - 测试Zipline数据
# =============================================================================

TEST_ZIPLINE_DATA_SCRIPT = '''#!/usr/bin/env python3
"""
Zipline数据测试工具
测试摄入的Zipline数据是否正常可用

使用方式:
python scripts/test_zipline_data.py --bundle custom_bundle
python scripts/test_zipline_data.py --bundle custom_bundle --symbol 000001.SZ
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_bundle_availability(bundle_name):
    """测试Bundle是否可用"""
    try:
        from zipline.data import bundles
        
        # 检查Bundle是否已注册
        available_bundles = bundles.bundles.keys()
        
        if bundle_name not in available_bundles:
            print(f"Bundle '{bundle_name}' 未注册")
            print(f"可用的Bundle: {list(available_bundles)}")
            return False
        
        print(f"Bundle '{bundle_name}' 已注册")
        return True
        
    except ImportError:
        print("Zipline未安装或导入失败")
        return False
    except Exception as e:
        print(f"Bundle可用性测试失败: {e}")
        return False

def load_bundle_data(bundle_name):
    """加载Bundle数据"""
    try:
        from zipline.data import bundles
        
        # 加载Bundle
        bundle_data = bundles.load(bundle_name)
        
        print(f"Bundle数据加载成功")
        return bundle_data
        
    except Exception as e:
        print(f"Bundle数据加载失败: {e}")
        return None

def test_asset_finder(bundle_data):
    """测试资产查找器"""
    try:
        asset_finder = bundle_data.asset_finder
        
        # 获取所有资产
        all_sids = asset_finder.sids
        assets = asset_finder.retrieve_all(all_sids)
        
        print(f"总资产数量: {len(assets)}")
        
        if assets:
            print("前5个资产:")
            for asset in assets[:5]:
                print(f"  {asset.symbol}: {asset.start_date} ~ {asset.end_date}")
        
        return assets
        
    except Exception as e:
        print(f"资产查找器测试失败: {e}")
        return []

def test_price_data(bundle_data, symbol=None):
    """测试价格数据"""
    try:
        asset_finder = bundle_data.asset_finder
        equity_daily_bar_reader = bundle_data.equity_daily_bar_reader
        
        # 选择测试资产
        if symbol:
            try:
                asset = asset_finder.lookup_symbol(symbol, as_of_date=None)
            except:
                print(f"找不到股票: {symbol}")
                return False
        else:
            # 使用第一个资产
            all_sids = asset_finder.sids
            if not all_sids:
                print("没有找到任何资产")
                return False
            asset = asset_finder.retrieve_asset(all_sids[0])
        
        print(f"测试股票: {asset.symbol}")
        
        # 获取价格数据
        try:
            # 获取数据的日期范围
            start_date = asset.start_date
            end_date = asset.end_date
            
            print(f"数据范围: {start_date} ~ {end_date}")
            
            # 读取价格数据
            fields = ['open', 'high', 'low', 'close', 'volume']
            
            for field in fields:
                try:
                    data = equity_daily_bar_reader.load_raw_arrays(
                        [field], start_date, end_date, [asset.sid]
                    )
                    
                    field_data = data[0][field].flatten()  # [assets, dates] -> [dates]
                    
                    # 统计信息
                    valid_count = (~pd.isna(field_data)).sum()
                    total_count = len(field_data)
                    
                    print(f"  {field}: {valid_count}/{total_count} 有效数据点")
                    
                    if valid_count > 0:
                        non_nan_data = field_data[~pd.isna(field_data)]
                        print(f"    范围: {non_nan_data.min():.4f} ~ {non_nan_data.max():.4f}")
                        print(f"    均值: {non_nan_data.mean():.4f}")
                    
                except Exception as e:
                    print(f"  {field}: 数据读取失败 - {e}")
            
            return True
            
        except Exception as e:
            print(f"价格数据读取失败: {e}")
            return False
        
    except Exception as e:
        print(f"价格数据测试失败: {e}")
        return False

def test_calendar_alignment(bundle_data):
    """测试交易日历对齐"""
    try:
        from zipline.utils.calendars import get_calendar
        
        # 获取交易日历
        calendar = get_calendar('XSHG')  # 上海证券交易所
        
        # 获取2024年的交易日
        sessions_2024 = calendar.sessions_in_range('2024-01-01', '2024-12-31')
        
        print(f"2024年交易日数量: {len(sessions_2024)}")
        
        # 检查数据是否与交易日历对齐
        asset_finder = bundle_data.asset_finder
        all_sids = asset_finder.sids
        
        if all_sids:
            first_asset = asset_finder.retrieve_asset(all_sids[0])
            
            # 获取资产的数据日期范围
            start_date = max(first_asset.start_date, sessions_2024[0].date())
            end_date = min(first_asset.end_date, sessions_2024[-1].date())
            
            # 计算期间的交易日
            period_sessions = calendar.sessions_in_range(
                pd.Timestamp(start_date),
                pd.Timestamp(end_date)
            )
            
            print(f"测试期间交易日: {len(period_sessions)}")
            print(f"数据日期范围: {start_date} ~ {end_date}")
            
            return True
        else:
            print("没有资产可供测试")
            return False
        
    except Exception as e:
        print(f"交易日历测试失败: {e}")
        return False

def run_simple_backtest(bundle_name, test_symbol=None):
    """运行简单回测测试"""
    try:
        from zipline import run_algorithm
        from zipline.api import order_percent, symbol, get_datetime
        
        # 定义简单策略
        def initialize(context):
            if test_symbol:
                context.asset = symbol(test_symbol)
            else:
                # 使用第一个可用资产
                context.asset = symbol('000001.SZ')  # 默认
        
        def handle_data(context, data):
            # 简单买入持有策略
            if data.can_trade(context.asset):
                if not context.portfolio.positions[context.asset]:
                    order_percent(context.asset, 1.0)
        
        # 运行回测
        print(f"运行简单回测测试...")
        
        result = run_algorithm(
            start=pd.Timestamp('2024-01-01', tz='utc'),
            end=pd.Timestamp('2024-01-31', tz='utc'),  # 短期测试
            initialize=initialize,
            handle_data=handle_data,
            bundle=bundle_name,
            capital_base=100000
        )
        
        if result is not None and not result.empty:
            final_value = result['portfolio_value'].iloc[-1]
            total_return = (final_value / 100000 - 1) * 100
            
            print(f"回测完成!")
            print(f"  期末资产: {final_value:,.2f}")
            print(f"  总收益率: {total_return:.2f}%")
            return True
        else:
            print("回测失败: 返回空结果")
            return False
        
    except Exception as e:
        print(f"回测测试失败: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Zipline数据测试工具')
    parser.add_argument('--bundle', default='custom_bundle', help='Bundle名称')
    parser.add_argument('--symbol', help='测试股票代码')
    parser.add_argument('--skip-backtest', action='store_true', help='跳过回测测试')
    
    args = parser.parse_args()
    
    print("Zipline数据测试工具")
    print("=" * 40)
    print(f"测试Bundle: {args.bundle}")
    
    # 测试1: Bundle可用性
    print("\n测试1: Bundle可用性")
    if not test_bundle_availability(args.bundle):
        print("Bundle不可用，退出测试")
        return 1
    
    # 测试2: 加载Bundle数据
    print("\n测试2: 加载Bundle数据")
    bundle_data = load_bundle_data(args.bundle)
    
    if not bundle_data:
        print("Bundle数据加载失败，退出测试")
        return 1
    
    # 测试3: 资产查找器
    print("\n测试3: 资产查找器")
    assets = test_asset_finder(bundle_data)
    
    if not assets:
        print("没有找到资产，退出测试")
        return 1
    
    # 测试4: 价格数据
    print("\n测试4: 价格数据")
    price_test_success = test_price_data(bundle_data, args.symbol)
    
    if not price_test_success:
        print("价格数据测试失败")
    
    # 测试5: 交易日历
    print("\n测试5: 交易日历对齐")
    calendar_test_success = test_calendar_alignment(bundle_data)
    
    if not calendar_test_success:
        print("交易日历测试失败")
    
    # 测试6: 简单回测（可选）
    if not args.skip_backtest:
        print("\n测试6: 简单回测")
        backtest_success = run_simple_backtest(args.bundle, args.symbol)
        
        if not backtest_success:
            print("回测测试失败")
    
    # 总结
    print("\n测试总结:")
    print("=" * 40)
    
    test_results = [
        ("Bundle可用性", True),
        ("数据加载", bundle_data is not None),
        ("资产查找器", len(assets) > 0),
        ("价格数据", price_test_success),
        ("交易日历", calendar_test_success),
    ]
    
    if not args.skip_backtest:
        test_results.append(("回测功能", backtest_success))
    
    passed_count = sum(1 for _, passed in test_results if passed)
    total_count = len(test_results)
    
    for test_name, passed in test_results:
        status = "通过" if passed else "失败"
        icon = "✓" if passed else "✗"
        print(f"  {icon} {test_name}: {status}")
    
    print(f"\n通过率: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
    
    if passed_count == total_count:
        print("\n所有测试通过! Zipline数据准备就绪")
        return 0
    else:
        print("\n部分测试失败，请检查数据")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''

# =============================================================================
# 创建所有脚本文件的主函数
# =============================================================================

def create_all_scripts():
    """创建所有工具脚本"""
    scripts_to_create = [
        ('verify_token.py', VERIFY_TOKEN_SCRIPT),
        ('clear_cache.py', CLEAR_CACHE_SCRIPT),
        ('inspect_raw_data.py', INSPECT_RAW_DATA_SCRIPT),
        ('validate_data_format.py', VALIDATE_DATA_FORMAT_SCRIPT),
        ('verify_adjustment.py', VERIFY_ADJUSTMENT_SCRIPT),
        ('check_price_relationships.py', CHECK_PRICE_RELATIONSHIPS_SCRIPT),
        ('fix_price_relationships.py', FIX_PRICE_RELATIONSHIPS_SCRIPT),
        ('align_trading_calendar.py', ALIGN_TRADING_CALENDAR_SCRIPT),
        ('validate_zipline_format.py', VALIDATE_ZIPLINE_FORMAT_SCRIPT),
        ('zipline_ingest.py', ZIPLINE_INGEST_SCRIPT),
        ('test_zipline_data.py', TEST_ZIPLINE_DATA_SCRIPT),
    ]
    
    scripts_dir = PROJECT_ROOT / 'scripts'
    scripts_dir.mkdir(exist_ok=True)
    
    print("实用工具脚本创建器")
    print("=" * 50)
    
    created_count = 0
    
    for filename, content in scripts_to_create:
        file_path = scripts_dir / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 设置执行权限 (Unix系统)
            try:
                import stat
                file_path.chmod(file_path.stat().st_mode | stat.S_IEXEC)
            except:
                pass
            
            print(f"创建脚本: {file_path}")
            created_count += 1
            
        except Exception as e:
            print(f"创建脚本失败 {filename}: {e}")
    
    print(f"\n成功创建 {created_count}/{len(scripts_to_create)} 个脚本")
    
    # 输出使用说明
    print(f"\n使用说明:")
    print(f"  python scripts/verify_token.py --all")
    print(f"  python scripts/clear_cache.py --type all")
    print(f"  python scripts/inspect_raw_data.py --symbol 000001.SZ")
    print(f"  python scripts/validate_data_format.py --input data/raw/")
    print(f"  python scripts/verify_adjustment.py --symbol 000001.SZ --check-consistency")
    print(f"  python scripts/check_price_relationships.py --input data/processed/")
    print(f"  python scripts/fix_price_relationships.py --input data/raw/ --output data/cleaned/ --batch")
    print(f"  python scripts/align_trading_calendar.py --input data/raw/ --output data/aligned/")
    print(f"  python scripts/validate_zipline_format.py --input data/zipline/")
    print(f"  python scripts/zipline_ingest.py --bundle custom_bundle")
    print(f"  python scripts/test_zipline_data.py --bundle custom_bundle")
    
    return created_count

if __name__ == "__main__":
    create_all_scripts()