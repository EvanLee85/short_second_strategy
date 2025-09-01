#!/usr/bin/env python3
"""
原始数据检查工具
检查和分析原始股票数据的质量和结构

使用方式:
python scripts/inspect_raw_data.py --file data/raw/000001.SZ.csv
python scripts/inspect_raw_data.py --symbol 000001.SZ --source akshare
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
    print(f"\n📋 列信息:")
    for i, (col, dtype) in enumerate(zip(df.columns, df.dtypes)):
        null_count = df[col].isnull().sum()
        null_pct = null_count / len(df) * 100
        print(f"   {i+1:2d}. {col:15s} ({str(dtype):10s}) - 缺失: {null_count:4d} ({null_pct:5.1f}%)")
    
    # 价格关系检查
    price_cols = ['open', 'high', 'low', 'close']
    available_price_cols = [col for col in price_cols if col in df.columns]
    
    if len(available_price_cols) >= 4:
        print(f"\n💰 价格关系检查:")
        
        # high >= low
        high_low_ok = (df['high'] >= df['low']).sum()
        print(f"   high >= low: {high_low_ok:4d}/{len(df)} ({high_low_ok/len(df)*100:5.1f}%)")
        
        # high >= open, close
        high_open_ok = (df['high'] >= df['open']).sum()
        high_close_ok = (df['high'] >= df['close']).sum()
        print(f"   high >= open: {high_open_ok:4d}/{len(df)} ({high_open_ok/len(df)*100:5.1f}%)")
        print(f"   high >= close: {high_close_ok:4d}/{len(df)} ({high_close_ok/len(df)*100:5.1f}%)")
    
    # 数据样例
    print(f"\n📝 数据样例 (前5行):")
    print(df.head().to_string())

def inspect_from_file(file_path):
    """从文件读取数据并检查"""
    try:
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"❌ 文件不存在: {file_path}")
            return False
        
        # 尝试读取文件
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
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
    parser.add_argument('--file', help='数据文件路径')
    parser.add_argument('--symbol', help='股票代码')
    parser.add_argument('--source', help='数据源')
    
    args = parser.parse_args()
    
    print("🔍 原始数据检查工具")
    print("=" * 50)
    
    if args.file:
        success = inspect_from_file(args.file)
    elif args.symbol:
        # 模拟数据检查
        print(f"模拟检查股票: {args.symbol}")
        print("提示: 请先确保数据获取模块正常工作")
        success = True
    else:
        print("❌ 请指定 --file 文件路径或 --symbol 股票代码")
        return 1
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
