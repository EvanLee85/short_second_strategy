#!/usr/bin/env python3
"""
后端集成快速部署脚本 (修复版)
一键完成后端对接，实现"无痛替换"

运行方式:
python deploy_backend_integration_fixed.py --csv-path ./data/stocks/ --mode auto

功能:
1. 自动检测项目结构
2. 配置后端集成
3. 验证迁移效果
4. 生成部署报告
"""

import sys
import argparse
from pathlib import Path
import json
from datetime import datetime
import logging
import traceback

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

class BackendDeploymentTool:
    """后端集成部署工具"""
    
    def __init__(self):
        self.deployment_config = {}
        self.deployment_results = {
            'start_time': datetime.now(),
            'steps_completed': [],
            'steps_failed': [],
            'warnings': [],
            'recommendations': []
        }
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('backend_deployment.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def detect_project_structure(self) -> dict:
        """检测项目结构"""
        self.logger.info("🔍 检测项目结构...")
        
        structure = {
            'project_root': PROJECT_ROOT,
            'has_data_dir': False,
            'has_backend_modules': False,
            'csv_files_found': [],
            'python_files': [],
            'requirements_file': None
        }
        
        # 检查数据目录
        common_data_dirs = ['data', 'datasets', 'stock_data', 'csv_data']
        for dir_name in common_data_dirs:
            data_dir = PROJECT_ROOT / dir_name
            if data_dir.exists():
                structure['has_data_dir'] = True
                structure['data_dir'] = data_dir
                
                # 查找CSV文件
                csv_files = list(data_dir.glob("*.csv"))
                structure['csv_files_found'].extend(csv_files)
                break
        
        # 检查后端模块
        backend_dir = PROJECT_ROOT / 'backend'
        if backend_dir.exists():
            structure['has_backend_modules'] = True
            structure['backend_dir'] = backend_dir
        
        # 查找Python文件
        py_files = list(PROJECT_ROOT.glob("*.py"))
        py_files.extend(PROJECT_ROOT.glob("**/*.py"))
        structure['python_files'] = py_files[:20]  # 限制数量
        
        # 查找requirements文件
        for req_file in ['requirements.txt', 'requirements-dev.txt', 'pyproject.toml']:
            req_path = PROJECT_ROOT / req_file
            if req_path.exists():
                structure['requirements_file'] = req_path
                break
        
        self.logger.info(f"   ✅ 项目根目录: {structure['project_root']}")
        self.logger.info(f"   📁 数据目录: {'存在' if structure['has_data_dir'] else '未找到'}")
        self.logger.info(f"   📂 后端模块: {'存在' if structure['has_backend_modules'] else '未找到'}")
        self.logger.info(f"   📄 CSV文件: 发现 {len(structure['csv_files_found'])} 个")
        
        return structure
    
    def install_dependencies(self) -> bool:
        """安装必要依赖"""
        self.logger.info("📦 检查并安装依赖...")
        
        required_packages = [
            'pandas>=1.5.0',
            'numpy>=1.21.0', 
            'python-dateutil>=2.8.0'
        ]
        
        try:
            import subprocess
            
            for package in required_packages:
                try:
                    pkg_name = package.split('>=')[0]
                    __import__(pkg_name)
                    self.logger.info(f"   ✅ {pkg_name}: 已安装")
                except ImportError:
                    self.logger.info(f"   📥 安装 {package}...")
                    result = subprocess.run([
                        sys.executable, '-m', 'pip', 'install', package
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        self.logger.info(f"   ✅ {package}: 安装成功")
                    else:
                        self.logger.error(f"   ❌ {package}: 安装失败")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"依赖安装异常: {e}")
            return False
    
    def create_backend_modules(self) -> bool:
        """创建后端模块文件"""
        self.logger.info("🔧 创建后端模块...")
        
        backend_dir = PROJECT_ROOT / 'backend'
        backend_dir.mkdir(exist_ok=True)
        
        # 创建__init__.py
        init_file = backend_dir / '__init__.py'
        if not init_file.exists():
            init_content = '''"""
后端数据集成模块
提供无痛替换的数据源集成功能
"""

from .data_fetcher_facade import get_ohlcv, configure_data_backend
from .zipline_csv_writer import write_zipline_csv
from .backend_integration import enable_backend_integration, disable_backend_integration

__version__ = "1.0.0"
__all__ = [
    'get_ohlcv', 
    'configure_data_backend',
    'write_zipline_csv',
    'enable_backend_integration',
    'disable_backend_integration'
]
'''
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write(init_content)
            
            self.logger.info(f"   ✅ 创建: {init_file}")
        
        # 检查必要模块文件
        required_modules = [
            'data_fetcher_facade.py',
            'zipline_csv_writer.py', 
            'backend_integration.py'
        ]
        
        missing_modules = []
        for module in required_modules:
            module_file = backend_dir / module
            if not module_file.exists():
                missing_modules.append(module)
        
        if missing_modules:
            self.logger.warning(f"   ⚠️  缺少模块: {missing_modules}")
            self.deployment_results['warnings'].append(f"缺少后端模块: {missing_modules}")
            return False
        
        self.logger.info("   ✅ 后端模块检查完成")
        return True
    
    def configure_integration(self, csv_data_path: str, mode: str = 'gradual') -> bool:
        """配置后端集成"""
        self.logger.info(f"⚙️  配置后端集成 (模式: {mode})...")
        
        try:
            # 导入必要模块
            from backend.data_fetcher_facade import configure_data_backend
            from backend.backend_integration import enable_backend_integration
            
            # 配置数据后端
            configure_data_backend(
                csv_data_path=csv_data_path,
                enable_new_fetcher=True,
                fallback_to_csv=True
            )
            
            # 根据模式启用集成
            auto_patch = mode in ['auto', 'aggressive']
            
            enable_backend_integration(
                csv_data_path=csv_data_path,
                auto_patch=auto_patch
            )
            
            self.deployment_config = {
                'csv_data_path': csv_data_path,
                'mode': mode,
                'auto_patch': auto_patch,
                'fallback_enabled': True,
                'deployment_time': datetime.now().isoformat()
            }
            
            self.logger.info("   ✅ 后端集成配置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"   ❌ 配置失败: {e}")
            return False
    
    def run_verification_tests(self) -> dict:
        """运行验证测试"""
        self.logger.info("🧪 运行验证测试...")
        
        test_results = {
            'data_read_test': False,
            'csv_write_test': False,
            'integration_stats': {},
            'performance_ok': True,
            'errors': []
        }
        
        try:
            # 测试1: 数据读取
            self.logger.info("   🔍 测试数据读取...")
            from backend.data_fetcher_facade import get_ohlcv
            
            test_data = get_ohlcv(
                symbol="000001.SZ",
                start_date="2024-01-01",
                end_date="2024-01-10"
            )
            
            if not test_data.empty:
                test_results['data_read_test'] = True
                self.logger.info(f"   ✅ 数据读取成功: {len(test_data)} 行")
            else:
                self.logger.warning("   ⚠️  数据读取返回空结果")
            
            # 测试2: CSV生成
            self.logger.info("   📝 测试CSV生成...")
            from backend.zipline_csv_writer import write_zipline_csv
            import tempfile
            
            with tempfile.TemporaryDirectory() as temp_dir:
                result = write_zipline_csv(
                    symbols=["000001.SZ"],
                    output_dir=temp_dir,
                    start_date="2024-01-01",
                    end_date="2024-01-10"
                )
                
                if result['files_generated'] > 0:
                    test_results['csv_write_test'] = True
                    self.logger.info("   ✅ CSV生成成功")
                else:
                    self.logger.warning("   ⚠️  CSV生成无输出")
            
            # 测试3: 集成统计
            self.logger.info("   📊 检查集成统计...")
            from backend.backend_integration import get_integration_stats
            
            stats = get_integration_stats()
            test_results['integration_stats'] = stats
            
            # 简单的性能检查
            if stats['errors'] > stats.get('read_csv_intercepts', 1) * 0.1:
                test_results['performance_ok'] = False
                test_results['errors'].append("错误率过高")
            
            self.logger.info("   ✅ 验证测试完成")
            
        except Exception as e:
            self.logger.error(f"   ❌ 验证测试异常: {e}")
            test_results['errors'].append(str(e))
        
        return test_results
    
    def generate_integration_example(self, csv_data_path: str) -> bool:
        """生成集成示例代码"""
        self.logger.info("📝 生成集成示例代码...")
        
        example_code = f'''#!/usr/bin/env python3
"""
后端集成示例代码
自动生成于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import sys
from pathlib import Path
import pandas as pd

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def setup_backend_integration():
    """设置后端集成"""
    from backend.backend_integration import enable_backend_integration
    
    # 启用后端集成
    enable_backend_integration(
        csv_data_path="{csv_data_path}",
        auto_patch=True  # 自动patch pandas函数
    )
    
    print("✅ 后端集成已启用")

def example_data_reading():
    """示例: 数据读取"""
    # 原有代码完全不变，自动使用新数据源！
    data = pd.read_csv("data/000001_SZ.csv")
    print(f"读取数据: {{len(data)}} 行")
    return data

def example_batch_csv_generation():
    """示例: 批量CSV生成"""
    from backend.zipline_csv_writer import write_zipline_csv
    
    symbols = ["000001.SZ", "600000.SH", "000002.SZ"]
    
    result = write_zipline_csv(
        symbols=symbols,
        output_dir="./output/",
        start_date="2024-01-01",
        end_date="2024-03-31",
        overwrite=True
    )
    
    print(f"批量生成完成: {{result['files_generated']}}/{{len(symbols)}}")
    return result

def example_performance_monitoring():
    """示例: 性能监控"""
    from backend.backend_integration import get_integration_stats
    
    stats = get_integration_stats()
    print("性能统计:")
    print(f"  CSV读取拦截: {{stats['read_csv_intercepts']}} 次")
    print(f"  回退调用: {{stats['fallback_calls']}} 次") 
    print(f"  错误次数: {{stats['errors']}} 次")

def main():
    """主函数"""
    print("🚀 后端集成示例")
    
    # 1. 设置集成
    setup_backend_integration()
    
    # 2. 示例数据读取
    print("\\n📊 数据读取示例:")
    try:
        data = example_data_reading()
        print("✅ 数据读取成功")
    except Exception as e:
        print(f"❌ 数据读取失败: {{e}}")
    
    # 3. 示例CSV生成
    print("\\n📝 CSV生成示例:")
    try:
        result = example_batch_csv_generation()
        print("✅ CSV生成成功")
    except Exception as e:
        print(f"❌ CSV生成失败: {{e}}")
    
    # 4. 性能监控
    print("\\n📈 性能监控:")
    example_performance_monitoring()

if __name__ == "__main__":
    main()
'''
        
        try:
            example_file = PROJECT_ROOT / "backend_integration_example.py"
            with open(example_file, 'w', encoding='utf-8') as f:
                f.write(example_code)
            
            self.logger.info(f"   ✅ 示例代码生成: {example_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"   ❌ 示例代码生成失败: {e}")
            return False
    
    def generate_deployment_report(self, verification_results: dict) -> dict:
        """生成部署报告"""
        self.logger.info("📋 生成部署报告...")
        
        self.deployment_results['end_time'] = datetime.now()
        self.deployment_results['duration'] = (
            self.deployment_results['end_time'] - self.deployment_results['start_time']
        ).total_seconds()
        
        report = {
            'deployment_info': {
                'timestamp': self.deployment_results['end_time'].isoformat(),
                'duration_seconds': self.deployment_results['duration'],
                'configuration': self.deployment_config
            },
            'verification_results': verification_results,
            'deployment_status': 'success' if all([
                verification_results['data_read_test'],
                verification_results['csv_write_test'],
                len(verification_results['errors']) == 0
            ]) else 'partial_success',
            'next_steps': [
                "运行示例代码验证功能: python backend_integration_example.py",
                "在现有代码中添加后端集成初始化",
                "监控集成统计和性能指标",
                "逐步迁移更多功能到新后端"
            ],
            'recommendations': []
        }
        
        # 生成建议
        if not verification_results['data_read_test']:
            report['recommendations'].append("数据读取测试失败，检查数据源配置")
        
        if not verification_results['csv_write_test']:
            report['recommendations'].append("CSV生成测试失败，检查输出权限")
        
        if verification_results['errors']:
            report['recommendations'].append(f"解决验证错误: {verification_results['errors']}")
        
        if verification_results.get('integration_stats', {}).get('fallback_calls', 0) > 0:
            report['recommendations'].append("存在回退调用，建议优化数据源配置")
        
        # 保存报告
        report_file = PROJECT_ROOT / "backend_deployment_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"   ✅ 部署报告保存: {report_file}")
        return report
    
    def deploy(self, csv_data_path: str, mode: str = 'gradual') -> bool:
        """执行完整部署流程"""
        self.logger.info("🚀 开始后端集成部署...")
        
        try:
            # 步骤1: 检测项目结构
            structure = self.detect_project_structure()
            self.deployment_results['steps_completed'].append('detect_structure')
            
            # 步骤2: 安装依赖
            if self.install_dependencies():
                self.deployment_results['steps_completed'].append('install_dependencies')
            else:
                self.deployment_results['steps_failed'].append('install_dependencies')
                return False
            
            # 步骤3: 创建后端模块
            if self.create_backend_modules():
                self.deployment_results['steps_completed'].append('create_modules')
            else:
                self.deployment_results['steps_failed'].append('create_modules')
                return False
            
            # 步骤4: 配置集成
            if self.configure_integration(csv_data_path, mode):
                self.deployment_results['steps_completed'].append('configure_integration')
            else:
                self.deployment_results['steps_failed'].append('configure_integration')
                return False
            
            # 步骤5: 验证测试
            verification_results = self.run_verification_tests()
            self.deployment_results['steps_completed'].append('verification_tests')
            
            # 步骤6: 生成示例
            if self.generate_integration_example(csv_data_path):
                self.deployment_results['steps_completed'].append('generate_examples')
            
            # 步骤7: 生成报告
            report = self.generate_deployment_report(verification_results)
            self.deployment_results['steps_completed'].append('generate_report')
            
            # 输出最终结果
            self.logger.info("\n" + "="*60)
            self.logger.info("🎉 后端集成部署完成!")
            self.logger.info("="*60)
            
            self.logger.info(f"部署状态: {report['deployment_status']}")
            self.logger.info(f"完成步骤: {len(self.deployment_results['steps_completed'])}")
            self.logger.info(f"失败步骤: {len(self.deployment_results['steps_failed'])}")
            self.logger.info(f"部署耗时: {self.deployment_results['duration']:.2f} 秒")
            
            if verification_results['data_read_test']:
                self.logger.info("✅ 数据读取: 正常")
            else:
                self.logger.info("❌ 数据读取: 异常")
            
            if verification_results['csv_write_test']:
                self.logger.info("✅ CSV生成: 正常")
            else:
                self.logger.info("❌ CSV生成: 异常")
            
            if report['recommendations']:
                self.logger.info("\n💡 建议:")
                for rec in report['recommendations']:
                    self.logger.info(f"   • {rec}")
            
            self.logger.info("\n📋 后续步骤:")
            for step in report['next_steps']:
                self.logger.info(f"   • {step}")
            
            return report['deployment_status'] == 'success'
            
        except Exception as e:
            self.logger.error(f"部署过程异常: {e}")
            traceback.print_exc()
            return False

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='后端集成快速部署工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python deploy_backend_integration_fixed.py --csv-path ./data/stocks/ --mode auto
  python deploy_backend_integration_fixed.py --csv-path ./data/ --mode gradual --verify-only
  python deploy_backend_integration_fixed.py --detect-only

模式说明:
  gradual  : 渐进模式，不自动patch pandas函数，适合大型项目
  auto     : 自动模式，全面启用集成，适合新项目
  aggressive: 激进模式，禁用回退机制，仅用于测试
        """
    )
    
    parser.add_argument(
        '--csv-path',
        type=str,
        help='CSV数据文件路径，用于回退机制'
    )
    
    parser.add_argument(
        '--mode',
        choices=['gradual', 'auto', 'aggressive'],
        default='gradual',
        help='部署模式 (默认: gradual)'
    )
    
    parser.add_argument(
        '--detect-only',
        action='store_true',
        help='仅检测项目结构，不执行部署'
    )
    
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='仅运行验证测试'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制执行，忽略警告'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别 (默认: INFO)'
    )
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_arguments()
    
    # 设置日志级别
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    print("=" * 80)
    print("🚀 后端集成快速部署工具")
    print("=" * 80)
    
    tool = BackendDeploymentTool()
    
    try:
        if args.detect_only:
            # 仅检测项目结构
            print("🔍 项目结构检测模式")
            structure = tool.detect_project_structure()
            
            print("\n📊 检测结果:")
            print(f"   项目根目录: {structure['project_root']}")
            print(f"   数据目录: {'存在' if structure['has_data_dir'] else '未找到'}")
            print(f"   后端模块: {'存在' if structure['has_backend_modules'] else '未找到'}")
            print(f"   CSV文件: {len(structure['csv_files_found'])} 个")
            print(f"   Python文件: {len(structure['python_files'])} 个")
            
            if not structure['has_data_dir'] and not args.csv_path:
                print("\n⚠️  建议: 未检测到数据目录，请使用 --csv-path 指定")
            
            if not structure['has_backend_modules']:
                print("\n⚠️  建议: 缺少后端模块，需要完整部署")
            
            return 0
        
        if args.verify_only:
            # 仅运行验证测试
            if not args.csv_path:
                print("❌ 验证模式需要指定 --csv-path")
                return 1
            
            print("🧪 验证测试模式")
            
            # 先配置集成
            if not tool.configure_integration(args.csv_path, args.mode):
                print("❌ 配置失败，无法进行验证")
                return 1
            
            # 运行验证
            results = tool.run_verification_tests()
            
            print("\n📊 验证结果:")
            print(f"   数据读取: {'✅' if results['data_read_test'] else '❌'}")
            print(f"   CSV生成: {'✅' if results['csv_write_test'] else '❌'}")
            print(f"   错误数量: {len(results['errors'])}")
            
            if results['errors']:
                print(f"   错误详情: {'; '.join(results['errors'])}")
            
            return 0 if len(results['errors']) == 0 else 1
        
        # 完整部署流程
        if not args.csv_path:
            # 尝试自动检测CSV路径
            structure = tool.detect_project_structure()
            if structure['has_data_dir']:
                args.csv_path = str(structure.get('data_dir', './data/'))
                print(f"🔍 自动检测到CSV路径: {args.csv_path}")
            else:
                print("❌ 未指定CSV路径且无法自动检测，请使用 --csv-path 指定")
                return 1
        
        print(f"🎯 开始部署 (模式: {args.mode}, CSV路径: {args.csv_path})")
        
        # 安全检查
        if not args.force:
            csv_path = Path(args.csv_path)
            if not csv_path.exists():
                print(f"⚠️  警告: CSV路径不存在: {csv_path}")
                response = input("继续部署? (y/N): ").strip().lower()
                if response not in ['y', 'yes']:
                    print("部署已取消")
                    return 0
        
        # 执行部署
        success = tool.deploy(args.csv_path, args.mode)
        
        if success:
            print("\n🎉 部署成功完成!")
            print("\n📋 接下来可以:")
            print("   1. 运行示例: python backend_integration_example.py")
            print("   2. 查看报告: backend_deployment_report.json")
            print("   3. 检查日志: backend_deployment.log")
            return 0
        else:
            print("\n❌ 部署未完全成功，请检查日志")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n⚠️  部署被用户中断")
        return 130
    except Exception as e:
        print(f"\n💥 部署过程异常: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())