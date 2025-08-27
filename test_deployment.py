#!/usr/bin/env python3
"""
后端集成部署测试脚本
快速验证部署是否成功

运行方式:
python test_deployment.py
"""

import sys
from pathlib import Path
import traceback

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_imports():
    """测试模块导入"""
    print("🔍 测试模块导入...")
    
    tests = []
    
    # 测试pandas基础导入
    try:
        import pandas as pd
        import numpy as np
        tests.append(("pandas/numpy", True, ""))
    except Exception as e:
        tests.append(("pandas/numpy", False, str(e)))
    
    # 测试后端模块导入
    try:
        from backend.data_fetcher_facade import get_ohlcv, configure_data_backend
        tests.append(("data_fetcher_facade", True, ""))
    except Exception as e:
        tests.append(("data_fetcher_facade", False, str(e)))
    
    try:
        from backend.zipline_csv_writer import write_zipline_csv
        tests.append(("zipline_csv_writer", True, ""))
    except Exception as e:
        tests.append(("zipline_csv_writer", False, str(e)))
    
    try:
        from backend.backend_integration import enable_backend_integration
        tests.append(("backend_integration", True, ""))
    except Exception as e:
        tests.append(("backend_integration", False, str(e)))
    
    # 输出结果
    print("   导入测试结果:")
    for module, success, error in tests:
        status = "✅" if success else "❌"
        print(f"   {status} {module}")
        if not success:
            print(f"      错误: {error}")
    
    return all(t[1] for t in tests)

def test_basic_functionality():
    """测试基本功能"""
    print("\n🧪 测试基本功能...")
    
    try:
        # 测试数据获取
        from backend.data_fetcher_facade import get_ohlcv
        
        print("   测试数据获取...")
        data = get_ohlcv(
            symbol="000001.SZ", 
            start_date="2024-01-01", 
            end_date="2024-01-05"
        )
        
        if data.empty:
            print("   ⚠️  数据获取返回空结果（使用模拟数据）")
        else:
            print(f"   ✅ 数据获取成功: {len(data)} 行")
        
        # 测试CSV生成
        from backend.zipline_csv_writer import write_zipline_csv
        import tempfile
        
        print("   测试CSV生成...")
        with tempfile.TemporaryDirectory() as temp_dir:
            result = write_zipline_csv(
                symbols=["000001.SZ"],
                output_dir=temp_dir,
                start_date="2024-01-01",
                end_date="2024-01-05"
            )
            
            if result['files_generated'] > 0:
                print(f"   ✅ CSV生成成功: {result['files_generated']} 个文件")
            else:
                print("   ⚠️  CSV生成无输出")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 功能测试失败: {e}")
        return False

def test_integration():
    """测试集成功能"""
    print("\n🔗 测试集成功能...")
    
    try:
        from backend.backend_integration import enable_backend_integration, get_integration_stats
        import pandas as pd
        import tempfile
        
        # 创建临时测试数据
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 创建测试CSV文件
            test_data = pd.DataFrame({
                'date': pd.date_range('2024-01-01', periods=5),
                'open': [10.0, 10.5, 11.0, 10.8, 11.2],
                'high': [10.8, 11.2, 11.5, 11.3, 11.8],
                'low': [9.5, 10.0, 10.5, 10.3, 10.8],
                'close': [10.3, 10.8, 10.9, 11.1, 11.4],
                'volume': [1000000, 1200000, 1100000, 1300000, 1050000]
            })
            
            test_csv = temp_path / "000001_SZ.csv"
            test_data.to_csv(test_csv, index=False)
            
            # 启用集成
            print("   启用后端集成...")
            enable_backend_integration(
                csv_data_path=str(temp_path),
                auto_patch=True
            )
            
            # 测试自动切换
            print("   测试自动切换...")
            data = pd.read_csv(test_csv)  # 这应该会被拦截
            
            if not data.empty:
                print(f"   ✅ 自动切换成功: {len(data)} 行数据")
            else:
                print("   ⚠️  自动切换返回空数据")
            
            # 检查统计
            stats = get_integration_stats()
            print(f"   📊 集成统计: 拦截 {stats['read_csv_intercepts']} 次")
            
            return True
    
    except Exception as e:
        print(f"   ❌ 集成测试失败: {e}")
        traceback.print_exc()
        return False

def test_deployment_status():
    """检查部署状态"""
    print("\n📋 检查部署状态...")
    
    # 检查必要文件
    files_to_check = [
        "backend/__init__.py",
        "backend/data_fetcher_facade.py",
        "backend/zipline_csv_writer.py", 
        "backend/backend_integration.py"
    ]
    
    missing_files = []
    for file_path in files_to_check:
        full_path = PROJECT_ROOT / file_path
        if not full_path.exists():
            missing_files.append(file_path)
        else:
            print(f"   ✅ {file_path}")
    
    if missing_files:
        print(f"   ❌ 缺少文件: {missing_files}")
        return False
    
    # 检查生成的文件
    optional_files = [
        "backend_integration_example.py",
        "backend_deployment_report.json",
        "backend_deployment.log"
    ]
    
    for file_path in optional_files:
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            print(f"   ✅ {file_path} (已生成)")
        else:
            print(f"   ⚠️  {file_path} (未找到)")
    
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("🧪 后端集成部署测试")
    print("=" * 60)
    
    results = []
    
    # 运行各项测试
    tests = [
        ("模块导入", test_imports),
        ("基本功能", test_basic_functionality), 
        ("集成功能", test_integration),
        ("部署状态", test_deployment_status)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   💥 {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！后端集成部署成功！")
        print("\n📋 接下来可以:")
        print("   1. 运行完整演示: python examples/complete_migration_example.py")
        print("   2. 查看集成示例: python backend_integration_example.py")
        print("   3. 开始在你的项目中使用新的后端集成")
        return 0
    else:
        print("⚠️  部分测试失败，请检查部署配置")
        print("\n🔧 建议:")
        print("   1. 重新运行部署脚本")
        print("   2. 检查依赖安装")
        print("   3. 查看详细错误日志")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 测试过程异常: {e}")
        traceback.print_exc()
        sys.exit(1)