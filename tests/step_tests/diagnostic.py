# -*- coding: utf-8 -*-
"""
问题诊断脚本 - 逐步排查 fetcher 测试失败的原因
"""

import os
import sys
from pathlib import Path
import traceback

# 项目根目录
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def check_step(step_name, func):
    """执行检查步骤并记录结果"""
    print(f"\n=== {step_name} ===")
    try:
        result = func()
        if result:
            print(f"✓ {step_name} - PASS")
            return True
        else:
            print(f"✗ {step_name} - FAIL")
            return False
    except Exception as e:
        print(f"✗ {step_name} - ERROR: {e}")
        traceback.print_exc()
        return False

def check_dependencies():
    """检查依赖包"""
    try:
        import pandas as pd
        print(f"pandas version: {pd.__version__}")
        
        import exchange_calendars as xcals
        print(f"exchange_calendars imported successfully")
        
        # 测试XSHG日历
        cal = xcals.get_calendar("XSHG")
        print(f"XSHG calendar loaded: {type(cal)}")
        
        # 测试生成交易日
        sessions = cal.sessions_in_range("2024-01-02", "2024-01-10")
        print(f"Generated {len(sessions)} trading sessions for 2024-01-02 to 2024-01-10")
        print(f"Sample sessions: {sessions[:3].strftime('%Y-%m-%d').tolist()}")
        
        return True
    except Exception as e:
        print(f"Dependency check failed: {e}")
        return False

def check_file_structure():
    """检查文件结构"""
    required_dirs = [
        ROOT / "backend",
        ROOT / "backend" / "data", 
        ROOT / "backend" / "data" / "providers",
        ROOT / "config",
        ROOT / "data" / "zipline_csv"
    ]
    
    for d in required_dirs:
        if not d.exists():
            print(f"Missing directory: {d}")
            return False
        print(f"Directory exists: {d}")
    
    required_files = [
        ROOT / "backend" / "__init__.py",
        ROOT / "backend" / "data" / "__init__.py",
        ROOT / "backend" / "data" / "providers" / "__init__.py",
        ROOT / "backend" / "data" / "providers" / "base.py",
        ROOT / "backend" / "data" / "providers" / "csv_provider.py",
        ROOT / "backend" / "data" / "normalize.py",
        ROOT / "backend" / "data" / "cache.py",
        ROOT / "backend" / "data" / "merge.py",
        ROOT / "backend" / "data" / "exceptions.py",
        ROOT / "backend" / "data" / "fetcher.py"
    ]
    
    for f in required_files:
        if not f.exists():
            print(f"Missing file: {f}")
            return False
        print(f"File exists: {f}")
    
    return True

def check_imports():
    """检查模块导入"""
    try:
        print("Testing imports step by step...")
        
        print("1. Importing normalize...")
        from backend.data.normalize import get_sessions_index, to_internal
        print("   ✓ normalize imported")
        
        print("2. Testing get_sessions_index...")
        sessions = get_sessions_index("2024-01-02", "2024-01-10", "XSHG")
        print(f"   ✓ got {len(sessions)} sessions")
        
        print("3. Testing to_internal...")
        internal = to_internal("002415", default_exchange="XSHE")
        print(f"   ✓ normalized to: {internal}")
        
        print("4. Importing base provider...")
        from backend.data.providers.base import BaseMarketDataProvider
        print("   ✓ base provider imported")
        
        print("5. Importing csv provider...")
        from backend.data.providers.csv_provider import CsvProvider
        print("   ✓ csv provider imported")
        
        print("6. Importing cache...")
        from backend.data.cache import cache_ohlcv_get, cache_ohlcv_put
        print("   ✓ cache imported")
        
        print("7. Importing merge...")
        from backend.data.merge import merge_ohlcv
        print("   ✓ merge imported")
        
        print("8. Importing exceptions...")
        from backend.data.exceptions import DataSourceError
        print("   ✓ exceptions imported")
        
        print("9. Importing fetcher...")
        from backend.data.fetcher import get_default_fetcher
        print("   ✓ fetcher imported")
        
        return True
    except Exception as e:
        print(f"Import failed: {e}")
        return False

def create_test_config():
    """创建测试配置"""
    try:
        config_dir = ROOT / "config"
        config_dir.mkdir(exist_ok=True)
        
        config_content = f'''provider_priority:
  - csv

provider_configs:
  csv:
    csv_dir: "{(ROOT / 'data' / 'zipline_csv').as_posix()}"
    allow_stub: true

enable_cache: true
cache_ttl_hours:
  1d: 24

default_calendar: "XSHG"
default_exchange: "XSHE"
'''
        config_file = config_dir / "data_providers.yaml"
        config_file.write_text(config_content)
        print(f"Config created: {config_file}")
        return True
    except Exception as e:
        print(f"Config creation failed: {e}")
        return False

def create_test_csv():
    """创建测试CSV文件"""
    try:
        import pandas as pd
        from backend.data.normalize import get_sessions_index
        
        # 生成测试数据
        sessions = get_sessions_index("2024-01-02", "2024-01-10", "XSHG")
        print(f"Generated {len(sessions)} trading sessions")
        
        if len(sessions) == 0:
            print("No trading sessions generated!")
            return False
            
        # 创建样例数据
        data = []
        base_price = 10.0
        for i, date in enumerate(sessions):
            open_price = base_price + i * 0.1
            high_price = open_price + 0.2
            low_price = open_price - 0.15
            close_price = open_price + 0.05
            volume = 1000000 + i * 10000
            
            data.append([
                date.strftime('%Y-%m-%d'),
                round(open_price, 4),
                round(high_price, 4), 
                round(low_price, 4),
                round(close_price, 4),
                int(volume)
            ])
        
        df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        
        # 保存CSV
        csv_dir = ROOT / "data" / "zipline_csv"
        csv_dir.mkdir(parents=True, exist_ok=True)
        csv_file = csv_dir / "002415.csv"
        df.to_csv(csv_file, index=False)
        
        print(f"CSV created: {csv_file}")
        print(f"CSV shape: {df.shape}")
        print(f"CSV columns: {list(df.columns)}")
        print("CSV preview:")
        print(df.head(3))
        
        return True
    except Exception as e:
        print(f"CSV creation failed: {e}")
        return False

def test_csv_provider_directly():
    """直接测试CsvProvider"""
    try:
        from backend.data.providers.csv_provider import CsvProvider
        
        csv_dir = ROOT / "data" / "zipline_csv"
        provider = CsvProvider(csv_dir=str(csv_dir), allow_stub=True)
        
        print(f"CsvProvider created with csv_dir: {csv_dir}")
        
        # 测试文件查找
        csv_path = provider._resolve_csv_path("002415.XSHE")
        print(f"Resolved CSV path: {csv_path}")
        
        if not csv_path or not Path(csv_path).exists():
            print("CSV file not found by provider!")
            return False
            
        # 直接读取CSV
        raw_df = provider._read_csv(csv_path)
        print(f"Raw CSV shape: {raw_df.shape}")
        print(f"Raw CSV columns: {list(raw_df.columns)}")
        
        # 测试列规范化
        normalized_df, has_factor = provider._normalize_columns(raw_df)
        print(f"Normalized shape: {normalized_df.shape}")
        print(f"Has factor: {has_factor}")
        print(f"Normalized columns: {list(normalized_df.columns)}")
        
        # 测试完整的fetch流程
        result_df = provider.fetch_ohlcv("002415", "2024-01-02", "2024-01-10")
        print(f"Final result shape: {result_df.shape}")
        print(f"Final result columns: {list(result_df.columns)}")
        print("Final result preview:")
        print(result_df.head(3))
        
        return not result_df.empty
    except Exception as e:
        print(f"CsvProvider test failed: {e}")
        traceback.print_exc()
        return False

def test_fetcher_integration():
    """测试完整的fetcher流程"""
    try:
        from backend.data.fetcher import get_default_fetcher
        
        fetcher = get_default_fetcher()
        print("Fetcher created successfully")
        
        result = fetcher.get_ohlcv("002415", "2024-01-02", "2024-01-10")
        print(f"Fetcher result shape: {result.shape if result is not None else 'None'}")
        
        if result is not None and not result.empty:
            print(f"Fetcher result columns: {list(result.columns)}")
            print("Fetcher result preview:")
            print(result.head(3))
            return True
        else:
            print("Fetcher returned empty result")
            return False
            
    except Exception as e:
        print(f"Fetcher integration test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """主诊断流程"""
    print("开始诊断 fetcher 测试失败的原因...\n")
    
    # 创建必要的__init__.py文件
    init_files = [
        ROOT / "backend" / "__init__.py",
        ROOT / "backend" / "data" / "__init__.py", 
        ROOT / "backend" / "data" / "providers" / "__init__.py",
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.parent.mkdir(parents=True, exist_ok=True)
            init_file.write_text("# -*- coding: utf-8 -*-\n")
    
    # 执行诊断步骤
    steps = [
        ("检查依赖包", check_dependencies),
        ("检查文件结构", check_file_structure), 
        ("检查模块导入", check_imports),
        ("创建测试配置", create_test_config),
        ("创建测试CSV", create_test_csv),
        ("直接测试CsvProvider", test_csv_provider_directly),
        ("测试Fetcher集成", test_fetcher_integration)
    ]
    
    results = []
    for step_name, step_func in steps:
        result = check_step(step_name, step_func)
        results.append((step_name, result))
        if not result:
            print(f"\n❌ 在步骤 '{step_name}' 处发现问题，后续测试可能受影响")
    
    print("\n" + "="*60)
    print("诊断结果摘要:")
    print("="*60)
    
    for step_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {step_name}")
    
    failed_steps = [name for name, result in results if not result]
    if failed_steps:
        print(f"\n❌ 发现问题的步骤: {', '.join(failed_steps)}")
        print("请根据上述错误信息进行修复")
    else:
        print(f"\n✅ 所有诊断步骤都通过了！")

if __name__ == "__main__":
    main()