#!/usr/bin/env python3
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

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def verify_tushare_token():
    """验证Tushare token"""
    try:
        import tushare as ts
        
        # 尝试从环境变量获取token
        import os
        token = os.environ.get('TUSHARE_TOKEN')
        
        if not token:
            try:
                from config.settings import DATA_SOURCES
                token = DATA_SOURCES.get('tushare', {}).get('token')
            except ImportError:
                pass
        
        if not token:
            print("❌ Tushare token未配置")
            return False
        
        # 设置token并测试
        ts.set_token(token)
        pro = ts.pro_api()
        
        # 测试API调用
        df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name', limit=10)
        
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
    print("\n📊 验证结果汇总:")
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
        print(f"\n成功率: {success_count}/{total_count}")
        return 0 if success_count == total_count else 1
    else:
        print("\n没有可验证的数据源")
        return 0

if __name__ == "__main__":
    sys.exit(main())
