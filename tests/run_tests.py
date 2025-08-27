#!/usr/bin/env python3
"""
数据源替换测试套件
目的: 保证"替换数据源"不会破坏上层功能
运行: python run_tests.py
"""

import sys
import traceback
from pathlib import Path
import importlib.util
from typing import Dict, List, Tuple, Any
from datetime import datetime
import json

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class TestResult:
    """测试结果封装"""
    def __init__(self, name: str, passed: bool, message: str = "", duration: float = 0.0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration
        self.timestamp = datetime.now()

class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.unit_tests = [
            "normalize_sessions_ok",
            "adjust_pre_ok", 
            "symbol_map_ok",
            "cache_hit_ok"
        ]
        self.integration_tests = [
            "akshare_fetch_ok",
            "tushare_fetch_ok",
            "merge_fallback_ok",
            "zipline_ingest_ok",
            "algo_smoke_ok"
        ]
    
    def run_test(self, test_name: str, test_func) -> TestResult:
        """运行单个测试"""
        start_time = datetime.now()
        try:
            test_func()
            duration = (datetime.now() - start_time).total_seconds()
            return TestResult(test_name, True, "PASSED", duration)
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"FAILED: {str(e)}"
            return TestResult(test_name, False, error_msg, duration)
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("数据源替换测试套件")
        print("=" * 60)
        
        # 导入测试模块
        try:
            from tests.unit_tests import UnitTests
            from tests.integration_tests import IntegrationTests
        except ImportError as e:
            print(f"❌ 导入测试模块失败: {e}")
            return False
        
        unit_test_obj = UnitTests()
        integration_test_obj = IntegrationTests()
        
        # 运行单元测试
        print("\n🔧 单元测试:")
        print("-" * 40)
        
        for test_name in self.unit_tests:
            test_func = getattr(unit_test_obj, test_name, None)
            if test_func:
                result = self.run_test(test_name, test_func)
                self.results.append(result)
                status = "✅" if result.passed else "❌"
                print(f"{status} {test_name}: {result.message} ({result.duration:.3f}s)")
            else:
                result = TestResult(test_name, False, "测试方法不存在")
                self.results.append(result)
                print(f"❌ {test_name}: 测试方法不存在")
        
        # 运行集成测试
        print("\n🔗 集成测试:")
        print("-" * 40)
        
        for test_name in self.integration_tests:
            test_func = getattr(integration_test_obj, test_name, None)
            if test_func:
                result = self.run_test(test_name, test_func)
                self.results.append(result)
                status = "✅" if result.passed else "❌"
                print(f"{status} {test_name}: {result.message} ({result.duration:.3f}s)")
            else:
                result = TestResult(test_name, False, "测试方法不存在")
                self.results.append(result)
                print(f"❌ {test_name}: 测试方法不存在")
        
        # 生成测试报告
        self.generate_report()
        
        # 返回总体结果
        failed_tests = [r for r in self.results if not r.passed]
        return len(failed_tests) == 0
    
    def generate_report(self):
        """生成测试报告"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.passed])
        failed_tests = total_tests - passed_tests
        total_duration = sum(r.duration for r in self.results)
        
        print("\n" + "=" * 60)
        print("📊 测试结果汇总")
        print("=" * 60)
        
        if failed_tests == 0:
            print(f"🎉 所有测试通过! ({passed_tests}/{total_tests})")
            print(f"⏱️  总耗时: {total_duration:.3f}s")
        else:
            print(f"❌ 测试失败! 通过: {passed_tests}/{total_tests}")
            print(f"⏱️  总耗时: {total_duration:.3f}s")
            
            print("\n❌ 失败的测试:")
            for result in self.results:
                if not result.passed:
                    print(f"   • {result.name}: {result.message}")
        
        # 保存详细报告到文件
        self.save_detailed_report()
    
    def save_detailed_report(self):
        """保存详细报告到文件"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": len(self.results),
                "passed": len([r for r in self.results if r.passed]),
                "failed": len([r for r in self.results if not r.passed]),
                "duration": sum(r.duration for r in self.results)
            },
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "duration": r.duration,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in self.results
            ]
        }
        
        report_file = PROJECT_ROOT / "tests" / "test_report.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存: {report_file}")

def main():
    """主函数"""
    runner = TestRunner()
    
    try:
        success = runner.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n💥 测试运行器异常: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()