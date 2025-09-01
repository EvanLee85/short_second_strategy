#!/usr/bin/env python3
"""
缓存清理工具
清理项目中的各种缓存数据

使用方式:
python scripts/clear_cache.py --type all
python scripts/clear_cache.py --type data
python scripts/clear_cache.py --type adjustment
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
                       choices=['all', 'data', 'adjustment', 'temp'],
                       default='all',
                       help='指定清理类型')
    
    args = parser.parse_args()
    
    print("🧹 缓存清理工具")
    print("=" * 40)
    
    total_cleared = 0
    total_size = 0
    
    if args.type in ['all', 'data']:
        count, size = clear_data_cache()
        total_cleared += count
        total_size += size
    
    if args.type in ['all', 'adjustment']:
        count = clear_adjustment_cache()
        total_cleared += count
    
    if args.type in ['all', 'temp']:
        count = clear_temp_files()
        total_cleared += count
    
    print(f"\n📊 清理完成:")
    print(f"   清理项目: {total_cleared}")
    print(f"   释放空间: {total_size/1024/1024:.1f} MB")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
