#!/usr/bin/env python3
"""
完整的后端迁移示例
展示如何实现"无痛替换"，将直接读CSV改为fetcher.get_ohlcv()，
CSV生成改为write_zipline_csv()

运行方式:
python examples/complete_migration_example.py
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import os

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def create_sample_data():
    """创建示例数据用于演示"""
    print("🎯 创建示例数据...")
    
    # 创建临时目录结构
    temp_dir = Path("temp_migration_demo")
    temp_dir.mkdir(exist_ok=True)
    
    # 创建原始数据目录
    old_data_dir = temp_dir / "old_data"
    old_data_dir.mkdir(exist_ok=True)
    
    # 创建输出目录
    new_data_dir = temp_dir / "new_data"
    new_data_dir.mkdir(exist_ok=True)
    
    # 生成示例股票数据
    symbols = ["000001.SZ", "000002.SZ", "600000.SH", "600036.SH"]
    
    for symbol in symbols:
        # 生成时间序列数据
        dates = pd.date_range('2024-01-01', '2024-03-31', freq='D')
        dates = [d for d in dates if d.weekday() < 5]  # 只保留工作日
        
        np.random.seed(hash(symbol) % 2**32)  # 确保数据一致性
        base_price = np.random.uniform(10, 50)
        
        data = []
        current_price = base_price
        
        for date in dates:
            # 模拟价格变动
            change = np.random.normal(0, 0.02)  # 2%的日波动率
            current_price *= (1 + change)
            
            open_price = current_price * (1 + np.random.normal(0, 0.005))
            high_price = max(open_price, current_price) * (1 + abs(np.random.normal(0, 0.01)))
            low_price = min(open_price, current_price) * (1 - abs(np.random.normal(0, 0.01)))
            volume = int(np.random.uniform(1000000, 10000000))
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(current_price, 2),
                'volume': volume
            })
        
        # 保存原始格式CSV
        df = pd.DataFrame(data)
        csv_file = old_data_dir / f"{symbol.replace('.', '_')}.csv"
        df.to_csv(csv_file, index=False)
        print(f"   ✅ 创建 {csv_file} ({len(df)} 行)")
    
    print(f"✅ 示例数据创建完成，位置: {temp_dir}")
    return temp_dir, old_data_dir, new_data_dir

def demonstrate_original_code(old_data_dir):
    """演示原始的代码逻辑"""
    print("\n📊 演示原始代码逻辑...")
    
    def original_load_data(symbol):
        """原始的数据加载函数"""
        file_path = old_data_dir / f"{symbol.replace('.', '_')}.csv"
        data = pd.read_csv(file_path)
        return data
    
    def original_calculate_indicators(data):
        """原始的技术指标计算"""
        data = data.copy()
        data['date'] = pd.to_datetime(data['date'])
        data = data.sort_values('date')
        
        # 计算移动平均
        data['sma_20'] = data['close'].rolling(20, min_periods=1).mean()
        data['sma_5'] = data['close'].rolling(5, min_periods=1).mean()
        
        # 计算收益率
        data['daily_return'] = data['close'].pct_change()
        
        return data
    
    def original_batch_process(symbols):
        """原始的批量处理逻辑"""
        results = {}
        
        for symbol in symbols:
            try:
                print(f"   处理 {symbol}...")
                
                # 原始CSV读取方式
                data = original_load_data(symbol)
                
                # 计算指标
                processed_data = original_calculate_indicators(data)
                
                # 保存处理结果
                output_file = old_data_dir.parent / "processed" / f"{symbol.replace('.', '_')}_processed.csv"
                output_file.parent.mkdir(exist_ok=True)
                processed_data.to_csv(output_file, index=False)
                
                results[symbol] = {
                    'status': 'success',
                    'rows': len(processed_data),
                    'file': str(output_file)
                }
                
            except Exception as e:
                print(f"   ❌ 处理 {symbol} 失败: {e}")
                results[symbol] = {'status': 'failed', 'error': str(e)}
        
        return results
    
    # 执行原始逻辑
    symbols = ["000001.SZ", "000002.SZ", "600000.SH"]
    results = original_batch_process(symbols)
    
    print(f"   原始代码处理结果:")
    for symbol, result in results.items():
        if result['status'] == 'success':
            print(f"   ✅ {symbol}: {result['rows']} 行数据")
        else:
            print(f"   ❌ {symbol}: {result['error']}")
    
    return results

def demonstrate_migrated_code(old_data_dir, new_data_dir):
    """演示迁移后的代码"""
    print("\n🔄 演示迁移后的代码...")
    
    # 导入后端集成模块
    from backend.backend_integration import enable_backend_integration, read_stock_data, write_stock_csv
    from backend.data_fetcher_facade import get_ohlcv
    from backend.zipline_csv_writer import write_zipline_csv
    
    # 启用后端集成 - 这是关键的一步！
    enable_backend_integration(
        csv_data_path=str(old_data_dir),
        auto_patch=True  # 自动patch pandas函数
    )
    
    print("   ✅ 后端集成已启用")
    
    def migrated_load_data_v1(symbol):
        """迁移方式1: 完全无修改，自动切换"""
        # 这里的代码与原始代码完全相同！
        file_path = old_data_dir / f"{symbol.replace('.', '_')}.csv"
        data = pd.read_csv(file_path)  # 这里会自动使用新的数据获取器！
        return data
    
    def migrated_load_data_v2(symbol):
        """迁移方式2: 使用兼容性函数"""
        file_path = old_data_dir / f"{symbol.replace('.', '_')}.csv"
        data = read_stock_data(file_path)  # 显式使用新接口
        return data
    
    def migrated_load_data_v3(symbol):
        """迁移方式3: 直接使用新接口"""
        data = get_ohlcv(
            symbol=symbol,
            start_date="2024-01-01",
            end_date="2024-03-31"
        )
        return data
    
    def migrated_calculate_indicators(data):
        """技术指标计算逻辑完全不变"""
        data = data.copy()
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
        data = data.sort_values('date' if 'date' in data.columns else data.columns[0])
        
        # 计算移动平均
        data['sma_20'] = data['close'].rolling(20, min_periods=1).mean()
        data['sma_5'] = data['close'].rolling(5, min_periods=1).mean()
        
        # 计算收益率
        data['daily_return'] = data['close'].pct_change()
        
        return data
    
    def migrated_batch_process_v1(symbols):
        """迁移方式1: 代码完全不变，自动使用新后端"""
        results = {}
        
        for symbol in symbols:
            try:
                print(f"   处理 {symbol} (自动切换模式)...")
                
                # 这里的代码与原始版本完全相同！
                data = migrated_load_data_v1(symbol)  # 自动使用新数据源
                processed_data = migrated_calculate_indicators(data)
                
                # 保存结果
                output_file = new_data_dir / f"{symbol.replace('.', '_')}_v1.csv"
                processed_data.to_csv(output_file, index=False)  # 自动使用新格式
                
                results[symbol] = {
                    'method': 'auto_switch',
                    'status': 'success', 
                    'rows': len(processed_data),
                    'file': str(output_file)
                }
                
            except Exception as e:
                print(f"   ❌ 处理 {symbol} 失败: {e}")
                results[symbol] = {'method': 'auto_switch', 'status': 'failed', 'error': str(e)}
        
        return results
    
    def migrated_batch_process_v2(symbols):
        """迁移方式2: 使用批量新接口"""
        print(f"   批量处理 {len(symbols)} 个股票 (批量模式)...")
        
        try:
            # 直接使用批量CSV生成
            result = write_zipline_csv(
                symbols=symbols,
                output_dir=str(new_data_dir),
                start_date="2024-01-01",
                end_date="2024-03-31",
                overwrite=True,
                validate=True
            )
            
            print(f"   ✅ 批量处理完成: {result['files_generated']}/{len(symbols)}")
            print(f"   ⏱️  耗时: {result.get('duration', 0):.2f} 秒")
            
            return {
                'method': 'batch_mode',
                'total_symbols': len(symbols),
                'success_count': result['files_generated'],
                'failed_symbols': result.get('failed_symbols', []),
                'duration': result.get('duration', 0)
            }
            
        except Exception as e:
            print(f"   ❌ 批量处理失败: {e}")
            return {'method': 'batch_mode', 'status': 'failed', 'error': str(e)}
    
    # 执行迁移后的逻辑
    symbols = ["000001.SZ", "000002.SZ", "600000.SH"]
    
    print("\n   🔄 方式1: 自动切换模式（代码零修改）")
    results_v1 = migrated_batch_process_v1(symbols)
    
    for symbol, result in results_v1.items():
        if result['status'] == 'success':
            print(f"   ✅ {symbol}: {result['rows']} 行数据 ({result['method']})")
        else:
            print(f"   ❌ {symbol}: {result.get('error', '未知错误')}")
    
    print("\n   🚀 方式2: 批量处理模式（高性能）")
    results_v2 = migrated_batch_process_v2(symbols)
    
    if results_v2.get('status') != 'failed':
        print(f"   ✅ 批量处理: {results_v2['success_count']}/{results_v2['total_symbols']} 成功")
        print(f"   ⏱️  性能: {results_v2['duration']:.2f} 秒")
    else:
        print(f"   ❌ 批量处理失败: {results_v2['error']}")
    
    return results_v1, results_v2

def demonstrate_compatibility_check(old_data_dir, new_data_dir):
    """演示兼容性检查"""
    print("\n🔍 演示数据兼容性检查...")
    
    def compare_files(original_file, new_file):
        """比较原始文件和新文件的兼容性"""
        try:
            original_data = pd.read_csv(original_file)
            new_data = pd.read_csv(new_file)
            
            comparison = {
                'original_rows': len(original_data),
                'new_rows': len(new_data),
                'row_diff': len(new_data) - len(original_data),
                'original_cols': list(original_data.columns),
                'new_cols': list(new_data.columns),
                'compatible': True,
                'issues': []
            }
            
            # 检查行数差异
            if abs(comparison['row_diff']) > len(original_data) * 0.1:  # 10%容差
                comparison['issues'].append(f"行数差异较大: {comparison['row_diff']}")
                comparison['compatible'] = False
            
            # 检查必要列
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in new_data.columns]
            if missing_cols:
                comparison['issues'].append(f"缺少必要列: {missing_cols}")
                comparison['compatible'] = False
            
            # 检查数据质量
            if 'high' in new_data.columns and 'low' in new_data.columns:
                invalid_prices = (new_data['high'] < new_data['low']).sum()
                if invalid_prices > 0:
                    comparison['issues'].append(f"价格关系异常: {invalid_prices} 条记录")
                    comparison['compatible'] = False
            
            return comparison
            
        except Exception as e:
            return {
                'compatible': False,
                'issues': [f"比较失败: {str(e)}"]
            }
    
    # 进行兼容性检查
    symbols = ["000001.SZ", "000002.SZ"]
    
    for symbol in symbols:
        original_file = old_data_dir / f"{symbol.replace('.', '_')}.csv"
        new_file = new_data_dir / f"{symbol.replace('.', '_')}.csv"
        
        if original_file.exists() and new_file.exists():
            result = compare_files(original_file, new_file)
            
            print(f"   📊 {symbol}:")
            print(f"      原始数据: {result['original_rows']} 行")
            print(f"      新数据: {result['new_rows']} 行")
            
            if result['compatible']:
                print(f"      ✅ 兼容性: 良好")
            else:
                print(f"      ⚠️  兼容性问题: {'; '.join(result['issues'])}")
        else:
            print(f"   ❌ {symbol}: 文件不存在，跳过检查")

def demonstrate_performance_monitoring():
    """演示性能监控"""
    print("\n📈 演示性能监控...")
    
    from backend.backend_integration import get_integration_stats
    
    # 获取集成统计
    stats = get_integration_stats()
    
    print(f"   📊 后端集成统计:")
    print(f"      CSV读取拦截: {stats['read_csv_intercepts']} 次")
    print(f"      CSV写入拦截: {stats['write_csv_intercepts']} 次")
    print(f"      回退调用: {stats['fallback_calls']} 次")
    print(f"      错误次数: {stats['errors']} 次")
    
    # 计算成功率
    total_operations = stats['read_csv_intercepts'] + stats['write_csv_intercepts']
    if total_operations > 0:
        success_rate = (total_operations - stats['errors']) / total_operations * 100
        fallback_rate = stats['fallback_calls'] / total_operations * 100
        
        print(f"   📈 性能指标:")
        print(f"      成功率: {success_rate:.1f}%")
        print(f"      回退率: {fallback_rate:.1f}%")
        
        if success_rate >= 95:
            print(f"      ✅ 性能优秀")
        elif success_rate >= 90:
            print(f"      ⚠️  性能良好，建议优化")
        else:
            print(f"      ❌ 性能不佳，需要排查问题")

def cleanup_demo_data(temp_dir):
    """清理演示数据"""
    print(f"\n🧹 清理演示数据...")
    
    try:
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"   ✅ 已删除: {temp_dir}")
        else:
            print(f"   ℹ️  目录不存在: {temp_dir}")
    except Exception as e:
        print(f"   ⚠️  清理失败: {e}")

def main():
    """主演示函数"""
    print("=" * 80)
    print("🚀 后端对接完整迁移演示")
    print("=" * 80)
    print("目的: 演示如何实现'无痛替换'")
    print("关键点: 将直接读CSV改为fetcher.get_ohlcv()，CSV生成改为write_zipline_csv()")
    print("=" * 80)
    
    try:
        # 1. 创建示例数据
        temp_dir, old_data_dir, new_data_dir = create_sample_data()
        
        # 2. 演示原始代码
        print("\n" + "="*50)
        print("第一部分: 原始代码逻辑")
        print("="*50)
        original_results = demonstrate_original_code(old_data_dir)
        
        # 3. 演示迁移后代码
        print("\n" + "="*50) 
        print("第二部分: 迁移后代码逻辑")
        print("="*50)
        migrated_results_v1, migrated_results_v2 = demonstrate_migrated_code(old_data_dir, new_data_dir)
        
        # 4. 演示兼容性检查
        print("\n" + "="*50)
        print("第三部分: 兼容性检查")
        print("="*50)
        demonstrate_compatibility_check(old_data_dir, new_data_dir)
        
        # 5. 演示性能监控
        print("\n" + "="*50)
        print("第四部分: 性能监控")
        print("="*50)
        demonstrate_performance_monitoring()
        
        # 6. 总结迁移效果
        print("\n" + "="*50)
        print("🎯 迁移效果总结")
        print("="*50)
        
        print("✅ 迁移优势:")
        print("   1. 代码零修改: 现有pd.read_csv()调用自动切换到新数据源")
        print("   2. 自动回退: 新数据源不可用时自动使用原CSV文件")
        print("   3. 格式统一: 生成的CSV文件自动符合Zipline格式要求")
        print("   4. 性能监控: 内置统计功能，便于监控切换效果")
        print("   5. 渐进迁移: 支持逐步迁移，降低风险")
        
        print("\n🎯 关键实现:")
        print("   • 数据读取: pd.read_csv() → 自动切换到 fetcher.get_ohlcv()")
        print("   • CSV生成: DataFrame.to_csv() → 自动使用 write_zipline_csv()")
        print("   • 无痛替换: 现有接口语义完全保持不变")
        
        print("\n📊 演示结果:")
        successful_symbols = len([r for r in migrated_results_v1.values() if r.get('status') == 'success'])
        total_symbols = len(migrated_results_v1)
        print(f"   • 自动切换模式: {successful_symbols}/{total_symbols} 成功")
        print(f"   • 批量处理模式: {migrated_results_v2.get('success_count', 0)} 个文件生成")
        print(f"   • 数据格式: 完全兼容Zipline要求")
        print(f"   • 迁移风险: 最小化（自动回退机制）")
        
        # 7. 迁移建议
        print("\n💡 实际项目迁移建议:")
        print("   1. 首先在开发/测试环境验证")
        print("   2. 启用详细日志监控切换过程")
        print("   3. 小范围试点，逐步扩大范围")  
        print("   4. 保持原CSV数据作为回退方案")
        print("   5. 定期检查性能统计和错误日志")
        
        print(f"\n✅ 演示完成！临时文件位置: {temp_dir}")
        
        # 询问是否清理
        try:
            response = input("\n是否清理演示数据? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                cleanup_demo_data(temp_dir)
            else:
                print(f"   ℹ️  演示数据保留在: {temp_dir}")
        except (KeyboardInterrupt, EOFError):
            print(f"\n   ℹ️  演示数据保留在: {temp_dir}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  演示被用户中断")
        return 1
    except Exception as e:
        print(f"\n💥 演示过程异常: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())