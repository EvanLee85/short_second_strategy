#!/usr/bin/env python3
"""
系统诊断工具
快速检测系统配置、依赖和功能状态

使用方式:
python scripts/system_diagnosis.py
python scripts/system_diagnosis.py --component data_sources
python scripts/system_diagnosis.py --verbose
"""

import sys
import os
import argparse
import traceback
from pathlib import Path
from datetime import datetime

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class SystemDiagnosis:
    """系统诊断工具"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': [],
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }
    
    def _add_result(self, component, check_name, status, message, details=None):
        """添加检查结果"""
        result = {
            'component': component,
            'check': check_name,
            'status': status,  # 'pass', 'fail', 'warning'
            'message': message,
            'details': details or {}
        }
        
        self.results['checks'].append(result)
        self.results['summary']['total'] += 1
        
        if status == 'pass':
            self.results['summary']['passed'] += 1
        elif status == 'fail':
            self.results['summary']['failed'] += 1
        elif status == 'warning':
            self.results['summary']['warnings'] += 1
        
        # 输出到控制台
        status_icon = {'pass': '✅', 'fail': '❌', 'warning': '⚠️'}
        print(f"{status_icon[status]} {component}.{check_name}: {message}")
        
        if self.verbose and details:
            for key, value in details.items():
                print(f"   {key}: {value}")
    
    def check_python_environment(self):
        """检查Python环境"""
        print("\n🐍 Python环境检查")
        print("-" * 40)
        
        # Python版本检查
        py_version = sys.version_info
        if py_version >= (3, 8):
            self._add_result('python', 'version', 'pass', 
                           f"Python版本合适: {py_version.major}.{py_version.minor}")
        elif py_version >= (3, 6):
            self._add_result('python', 'version', 'warning',
                           f"Python版本偏低: {py_version.major}.{py_version.minor}")
        else:
            self._add_result('python', 'version', 'fail',
                           f"Python版本过低: {py_version.major}.{py_version.minor}")
        
        # pip检查
        try:
            import subprocess
            result = subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                pip_version = result.stdout.strip()
                self._add_result('python', 'pip', 'pass',
                               "pip可用", {'version': pip_version})
            else:
                self._add_result('python', 'pip', 'fail', "pip不可用")
        except Exception as e:
            self._add_result('python', 'pip', 'fail', f"pip检查失败: {e}")
    
    def check_dependencies(self):
        """检查依赖包"""
        print("\n📦 依赖包检查")
        print("-" * 40)
        
        required_packages = [
            ('pandas', '>=1.5.0'),
            ('numpy', '>=1.21.0'),
        ]
        
        optional_packages = [
            ('akshare', '>=1.10.0'),
            ('tushare', '>=1.2.80'),
            ('zipline-reloaded', '>=3.0.0'),
        ]
        
        # 检查必需包
        for package_name, version_spec in required_packages:
            self._check_package(package_name, version_spec, required=True)
        
        # 检查可选包
        for package_name, version_spec in optional_packages:
            self._check_package(package_name, version_spec, required=False)
    
    def _check_package(self, package_name, version_spec, required=True):
        """检查单个包"""
        try:
            import importlib
            module = importlib.import_module(package_name.replace('-', '_'))
            
            # 尝试获取版本号
            version = None
            for attr in ['__version__', 'version', 'VERSION']:
                if hasattr(module, attr):
                    version = getattr(module, attr)
                    break
            
            if version:
                status = 'pass'
                message = f"{package_name} 已安装"
                details = {'version': str(version)}
            else:
                status = 'warning' if not required else 'pass'
                message = f"{package_name} 已安装但无法获取版本号"
                details = {}
            
            self._add_result('dependencies', package_name, status, message, details)
            
        except ImportError:
            status = 'fail' if required else 'warning'
            message = f"{package_name} 未安装"
            self._add_result('dependencies', package_name, status, message)
    
    def check_file_permissions(self):
        """检查文件权限"""
        print("\n📁 文件权限检查")
        print("-" * 40)
        
        # 检查关键目录的读写权限
        directories_to_check = [
            ('project_root', PROJECT_ROOT),
            ('data_dir', PROJECT_ROOT / 'data'),
            ('scripts_dir', PROJECT_ROOT / 'scripts'),
        ]
        
        for dir_name, dir_path in directories_to_check:
            if dir_path.exists():
                if os.access(dir_path, os.R_OK) and os.access(dir_path, os.W_OK):
                    self._add_result('permissions', f'{dir_name}', 'pass',
                                   f"{dir_path.name}: 可读写")
                else:
                    self._add_result('permissions', f'{dir_name}', 'fail',
                                   f"{dir_path.name}: 权限不足")
            else:
                self._add_result('permissions', f'{dir_name}', 'warning',
                               f"目录不存在: {dir_path}")
    
    def run_diagnosis(self, components=None):
        """运行诊断"""
        print("=" * 60)
        print("🔍 系统诊断开始")
        print("=" * 60)
        
        all_components = {
            'python': self.check_python_environment,
            'dependencies': self.check_dependencies,
            'permissions': self.check_file_permissions,
        }
        
        if components:
            components_to_run = {k: v for k, v in all_components.items() if k in components}
        else:
            components_to_run = all_components
        
        # 运行检查
        for component_name, check_func in components_to_run.items():
            try:
                check_func()
            except Exception as e:
                self._add_result(component_name, 'execution', 'fail',
                               f"组件检查执行失败: {e}")
                if self.verbose:
                    traceback.print_exc()
        
        # 输出总结
        self._print_summary()
        
        return self.results
    
    def _print_summary(self):
        """打印诊断总结"""
        print("\n" + "=" * 60)
        print("📊 诊断结果总结")
        print("=" * 60)
        
        summary = self.results['summary']
        total = summary['total']
        passed = summary['passed']
        failed = summary['failed']
        warnings = summary['warnings']
        
        print(f"总检查项: {total}")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"⚠️  警告: {warnings}")
        
        if total > 0:
            success_rate = passed / total * 100
            print(f"成功率: {success_rate:.1f}%")
            
            if success_rate >= 90:
                print("🎉 系统状态优秀！")
            elif success_rate >= 70:
                print("👍 系统状态良好")
            else:
                print("⚠️  系统存在问题，建议修复")

def main():
    parser = argparse.ArgumentParser(description='系统诊断工具')
    parser.add_argument('--component', '-c', action='append',
                       help='指定要检查的组件')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出模式')
    
    args = parser.parse_args()
    
    try:
        diagnosis = SystemDiagnosis(verbose=args.verbose)
        results = diagnosis.run_diagnosis(components=args.component)
        
        summary = results['summary']
        if summary['failed'] == 0:
            return 0
        else:
            return 1
    
    except KeyboardInterrupt:
        print("\n\n⚠️  诊断被用户中断")
        return 130
    except Exception as e:
        print(f"\n💥 诊断过程异常: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
