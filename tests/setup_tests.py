#!/usr/bin/env python3
"""
测试环境设置脚本
自动检查和安装测试所需的环境和依赖
运行: python tests/setup_tests.py
"""

import sys
import os
import subprocess
from pathlib import Path
import importlib.util
from typing import List, Tuple

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
TESTS_ROOT = Path(__file__).parent

class TestEnvironmentSetup:
    """测试环境设置类"""
    
    def __init__(self):
        self.required_packages = [
            ("pandas", ">=1.5.0"),
            ("numpy", ">=1.21.0"),
            ("python-dateutil", ">=2.8.0")
        ]
        
        self.optional_packages = [
            ("akshare", ">=1.10.0", "Akshare数据源测试"),
            ("tushare", ">=1.2.80", "Tushare数据源测试"),
            ("psutil", ">=5.9.0", "性能监控"),
            ("pytest", ">=7.0.0", "高级测试功能"),
            ("colorama", ">=0.4.6", "彩色输出")
        ]
        
        self.test_directories = [
            "tests/temp",
            "tests/fixtures", 
            "tests/outputs",
            "data/test_cache",
            "logs/tests"
        ]
    
    def check_python_version(self) -> bool:
        """检查Python版本"""
        print("🐍 检查Python版本...")
        
        current_version = sys.version_info
        required_version = (3, 8)
        
        if current_version >= required_version:
            print(f"✅ Python版本: {current_version.major}.{current_version.minor}.{current_version.micro}")
            return True
        else:
            print(f"❌ Python版本过低: {current_version.major}.{current_version.minor}")
            print(f"   需要版本 >= {required_version[0]}.{required_version[1]}")
            return False
    
    def check_package_installed(self, package_name: str) -> bool:
        """检查包是否已安装"""
        try:
            importlib.import_module(package_name)
            return True
        except ImportError:
            return False
    
    def install_package(self, package_name: str, version_spec: str = "") -> bool:
        """安装包"""
        try:
            if version_spec:
                package_spec = f"{package_name}{version_spec}"
            else:
                package_spec = package_name
            
            print(f"   正在安装 {package_spec}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package_spec
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"   ✅ {package_name} 安装成功")
                return True
            else:
                print(f"   ❌ {package_name} 安装失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ {package_name} 安装超时")
            return False
        except Exception as e:
            print(f"   💥 {package_name} 安装异常: {e}")
            return False
    
    def setup_required_packages(self) -> bool:
        """设置必需包"""
        print("\n📦 检查必需依赖包...")
        
        all_installed = True
        for package_name, version_spec in self.required_packages:
            if self.check_package_installed(package_name):
                print(f"✅ {package_name}: 已安装")
            else:
                print(f"❌ {package_name}: 未安装")
                if not self.install_package(package_name, version_spec):
                    all_installed = False
        
        return all_installed
    
    def setup_optional_packages(self) -> List[str]:
        """设置可选包"""
        print("\n📦 检查可选依赖包...")
        
        installed_optional = []
        for package_info in self.optional_packages:
            package_name = package_info[0]
            version_spec = package_info[1] if len(package_info) > 1 else ""
            description = package_info[2] if len(package_info) > 2 else ""
            
            if self.check_package_installed(package_name):
                print(f"✅ {package_name}: 已安装 - {description}")
                installed_optional.append(package_name)
            else:
                print(f"⚠️  {package_name}: 未安装 - {description}")
                print(f"   提示: pip install {package_name}{version_spec}")
        
        return installed_optional
    
    def create_directories(self) -> bool:
        """创建必要目录"""
        print("\n📁 创建测试目录...")
        
        try:
            for dir_path in self.test_directories:
                full_path = PROJECT_ROOT / dir_path
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ 目录已创建: {dir_path}")
            return True
        except Exception as e:
            print(f"❌ 目录创建失败: {e}")
            return False
    
    def create_sample_fixtures(self):
        """创建示例测试数据"""
        print("\n📊 创建示例测试数据...")
        
        try:
            # 创建示例股票数据
            import pandas as pd
            import numpy as np
            from datetime import datetime, timedelta
            
            # 生成示例数据
            dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='D')
            dates = [d for d in dates if d.weekday() < 5]  # 只保留工作日
            
            sample_data = {
                'symbol': ['000001.SZ'] * len(dates),
                'date': dates,
                'open': np.random.uniform(12, 15, len(dates)),
                'high': np.random.uniform(15, 18, len(dates)),
                'low': np.random.uniform(10, 12, len(dates)),
                'close': np.random.uniform(12, 16, len(dates)),
                'volume': np.random.randint(1000000, 10000000, len(dates))
            }
            
            df = pd.DataFrame(sample_data)
            
            # 确保价格关系合理
            df['high'] = np.maximum.reduce([df['open'], df['close'], df['high']])
            df['low'] = np.minimum.reduce([df['open'], df['close'], df['low']])
            
            # 保存到fixtures目录
            fixtures_path = TESTS_ROOT / "fixtures"
            sample_file = fixtures_path / "sample_stock_data.csv"
            df.to_csv(sample_file, index=False)
            
            print(f"✅ 示例数据已创建: {sample_file}")
            
            # 创建错误数据示例
            corrupted_data = df.copy()
            corrupted_data.loc[0, 'high'] = corrupted_data.loc[0, 'low'] - 1  # 错误的价格关系
            corrupted_data.loc[1, 'volume'] = -1000000  # 负成交量
            
            corrupted_file = fixtures_path / "corrupted_stock_data.csv"
            corrupted_data.to_csv(corrupted_file, index=False)
            
            print(f"✅ 错误数据示例已创建: {corrupted_file}")
            
        except Exception as e:
            print(f"⚠️  示例数据创建失败: {e}")
    
    def check_environment_variables(self) -> dict:
        """检查环境变量"""
        print("\n🔧 检查环境变量...")
        
        env_vars = {
            'TUSHARE_TOKEN': os.getenv('TUSHARE_TOKEN'),
            'TEST_MODE': os.getenv('TEST_MODE', 'unit'),
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO')
        }
        
        for var_name, var_value in env_vars.items():
            if var_value:
                if var_name == 'TUSHARE_TOKEN':
                    # 隐藏token的完整值
                    display_value = f"{var_value[:8]}..." if len(var_value) > 8 else "已设置"
                else:
                    display_value = var_value
                print(f"✅ {var_name}: {display_value}")
            else:
                print(f"⚠️  {var_name}: 未设置")
        
        return env_vars
    
    def create_env_template(self):
        """创建环境变量模板文件"""
        print("\n📝 创建环境变量模板...")
        
        env_template = """# 测试环境变量配置文件
# 复制此文件为 .env 并填入实际值

# Tushare API令牌 (可选，用于真实数据测试)
TUSHARE_TOKEN=your_tushare_token_here

# 测试模式: unit, integration, full
TEST_MODE=unit

# 日志级别: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# 是否启用并行测试
PARALLEL_TESTS=false

# Akshare请求超时时间(秒)
AKSHARE_TIMEOUT=30

# 使用说明:
# 1. 将此文件复制为 .env
# 2. 根据需要修改配置值
# 3. 运行: source .env (Linux/Mac) 或使用python-dotenv加载
"""
        
        try:
            env_file = PROJECT_ROOT / ".env.template"
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_template)
            print(f"✅ 环境变量模板已创建: {env_file}")
        except Exception as e:
            print(f"⚠️  模板创建失败: {e}")
    
    def run_quick_test(self) -> bool:
        """运行快速测试验证环境"""
        print("\n🧪 运行环境验证测试...")
        
        try:
            # 导入并测试核心功能
            sys.path.insert(0, str(TESTS_ROOT))
            
            from mock_modules import MockModuleFactory
            
            # 测试模拟模块
            factory = MockModuleFactory()
            
            # 测试数据生成
            akshare_mock = factory.create_akshare_source()
            test_data = akshare_mock.fetch_stock_data("000001.SZ", "2024-01-01", "2024-01-05")
            assert not test_data.empty, "模拟数据生成失败"
            
            # 测试数据处理
            normalizer = factory.create_session_normalizer()
            normalized = normalizer.normalize(test_data)
            assert len(normalized) > 0, "数据标准化失败"
            
            # 测试缓存
            cache = factory.create_data_cache()
            cache.set("test_key", "test_value")
            assert cache.get("test_key") == "test_value", "缓存功能失败"
            
            print("✅ 环境验证测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 环境验证测试失败: {e}")
            return False
    
    def generate_setup_report(self, results: dict):
        """生成设置报告"""
        print("\n" + "="*60)
        print("🎯 测试环境设置完成")
        print("="*60)
        
        print(f"Python版本: {'✅' if results['python_ok'] else '❌'}")
        print(f"必需依赖: {'✅' if results['required_ok'] else '❌'}")
        print(f"目录创建: {'✅' if results['directories_ok'] else '❌'}")
        print(f"环境验证: {'✅' if results['test_ok'] else '❌'}")
        
        print(f"\n可选依赖安装: {len(results['optional_installed'])}/{len(self.optional_packages)}")
        for pkg in results['optional_installed']:
            print(f"  ✅ {pkg}")
        
        print(f"\n环境变量配置:")
        for var, value in results['env_vars'].items():
            status = "✅" if value else "⚠️ "
            print(f"  {status} {var}")
        
        if all([results['python_ok'], results['required_ok'], results['test_ok']]):
            print(f"\n🎉 环境设置成功！可以运行测试了:")
            print(f"   python tests/run_tests.py")
        else:
            print(f"\n❌ 环境设置不完整，请解决上述问题后重试")
            
        # 保存设置报告
        try:
            import json
            from datetime import datetime
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "setup_results": results,
                "next_steps": [
                    "运行测试: python tests/run_tests.py",
                    "查看文档: tests/README.md", 
                    "配置环境变量: .env.template"
                ]
            }
            
            report_file = TESTS_ROOT / "setup_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"\n📄 设置报告已保存: {report_file}")
            
        except Exception as e:
            print(f"⚠️  报告保存失败: {e}")
    
    def run_setup(self):
        """运行完整设置流程"""
        print("🚀 开始测试环境设置...")
        print(f"项目目录: {PROJECT_ROOT}")
        print(f"测试目录: {TESTS_ROOT}")
        
        # 执行设置步骤
        results = {
            'python_ok': self.check_python_version(),
            'required_ok': self.setup_required_packages(),
            'optional_installed': self.setup_optional_packages(),
            'directories_ok': self.create_directories(),
            'env_vars': self.check_environment_variables(),
            'test_ok': False
        }
        
        # 创建辅助文件
        self.create_sample_fixtures()
        self.create_env_template()
        
        # 最终测试
        if results['python_ok'] and results['required_ok']:
            results['test_ok'] = self.run_quick_test()
        
        # 生成报告
        self.generate_setup_report(results)
        
        return results

def main():
    """主函数"""
    try:
        setup = TestEnvironmentSetup()
        results = setup.run_setup()
        
        # 返回适当的退出码
        if results['python_ok'] and results['required_ok'] and results['test_ok']:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  设置被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n💥 设置过程异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()