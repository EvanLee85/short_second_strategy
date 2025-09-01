#!/usr/bin/env python3
"""
实用工具脚本创建器
创建项目所需的所有实用工具脚本文件
"""

import os
import sys
from pathlib import Path

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def create_script_file(filename, content):
    """创建单个脚本文件"""
    scripts_dir = PROJECT_ROOT / 'scripts'
    scripts_dir.mkdir(exist_ok=True)
    
    file_path = scripts_dir / filename
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 设置执行权限 (Unix系统)
        try:
            import stat
            file_path.chmod(file_path.stat().st_mode | stat.S_IEXEC)
        except:
            pass
        
        print(f"✅ 创建脚本: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ 创建脚本失败 {filename}: {e}")
        return False

def create_verify_token_script():
    """创建 verify_token.py"""
    content = '''#!/usr/bin/env python3
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
    print("\\n📊 验证结果汇总:")
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
        print(f"\\n成功率: {success_count}/{total_count}")
        return 0 if success_count == total_count else 1
    else:
        print("\\n没有可验证的数据源")
        return 0

if __name__ == "__main__":
    sys.exit(main())
'''
    return create_script_file('verify_token.py', content)

def create_clear_cache_script():
    """创建 clear_cache.py"""
    content = '''#!/usr/bin/env python3
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
    
    print(f"\\n📊 清理完成:")
    print(f"   清理项目: {total_cleared}")
    print(f"   释放空间: {total_size/1024/1024:.1f} MB")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''
    return create_script_file('clear_cache.py', content)

def create_inspect_raw_data_script():
    """创建 inspect_raw_data.py"""
    content = '''#!/usr/bin/env python3
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
    print(f"\\n📋 列信息:")
    for i, (col, dtype) in enumerate(zip(df.columns, df.dtypes)):
        null_count = df[col].isnull().sum()
        null_pct = null_count / len(df) * 100
        print(f"   {i+1:2d}. {col:15s} ({str(dtype):10s}) - 缺失: {null_count:4d} ({null_pct:5.1f}%)")
    
    # 价格关系检查
    price_cols = ['open', 'high', 'low', 'close']
    available_price_cols = [col for col in price_cols if col in df.columns]
    
    if len(available_price_cols) >= 4:
        print(f"\\n💰 价格关系检查:")
        
        # high >= low
        high_low_ok = (df['high'] >= df['low']).sum()
        print(f"   high >= low: {high_low_ok:4d}/{len(df)} ({high_low_ok/len(df)*100:5.1f}%)")
        
        # high >= open, close
        high_open_ok = (df['high'] >= df['open']).sum()
        high_close_ok = (df['high'] >= df['close']).sum()
        print(f"   high >= open: {high_open_ok:4d}/{len(df)} ({high_open_ok/len(df)*100:5.1f}%)")
        print(f"   high >= close: {high_close_ok:4d}/{len(df)} ({high_close_ok/len(df)*100:5.1f}%)")
    
    # 数据样例
    print(f"\\n📝 数据样例 (前5行):")
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
'''
    return create_script_file('inspect_raw_data.py', content)

def create_system_diagnosis_script():
    """创建 system_diagnosis.py"""
    content = '''#!/usr/bin/env python3
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
        print("\\n🐍 Python环境检查")
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
        print("\\n📦 依赖包检查")
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
        print("\\n📁 文件权限检查")
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
        print("\\n" + "=" * 60)
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
        print("\\n\\n⚠️  诊断被用户中断")
        return 130
    except Exception as e:
        print(f"\\n💥 诊断过程异常: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
    return create_script_file('system_diagnosis.py', content)

def main():
    """主函数：创建所有脚本"""
    print("🛠️  实用工具脚本创建器")
    print("=" * 50)
    
    # 创建脚本列表
    scripts = [
        ('verify_token.py', create_verify_token_script),
        ('clear_cache.py', create_clear_cache_script),
        ('inspect_raw_data.py', create_inspect_raw_data_script),
        ('system_diagnosis.py', create_system_diagnosis_script),
    ]
    
    created_count = 0
    total_count = len(scripts)
    
    for script_name, create_func in scripts:
        print(f"\\n创建 {script_name}...")
        if create_func():
            created_count += 1
        else:
            print(f"❌ {script_name} 创建失败")
    
    print(f"\\n📊 创建完成:")
    print(f"   成功: {created_count}/{total_count}")
    
    if created_count > 0:
        print(f"\\n🎉 脚本创建成功！")
        print(f"\\n使用方法:")
        print(f"   python scripts/verify_token.py --all")
        print(f"   python scripts/clear_cache.py --type all")
        print(f"   python scripts/inspect_raw_data.py --file data/sample.csv")
        print(f"   python scripts/system_diagnosis.py")
        
        # 创建 README
        readme_content = """# 实用工具脚本

## 可用脚本

1. **verify_token.py** - 验证API token有效性
   ```bash
   python scripts/verify_token.py --all
   python scripts/verify_token.py --source akshare
   ```

2. **clear_cache.py** - 清理各种缓存
   ```bash
   python scripts/clear_cache.py --type all
   python scripts/clear_cache.py --type data
   ```

3. **inspect_raw_data.py** - 检查原始数据
   ```bash
   python scripts/inspect_raw_data.py --file data/sample.csv
   python scripts/inspect_raw_data.py --symbol 000001.SZ
   ```

4. **system_diagnosis.py** - 系统诊断
   ```bash
   python scripts/system_diagnosis.py
   python scripts/system_diagnosis.py --verbose
   ```

## 注意事项

- 所有脚本都支持 `--help` 参数查看详细使用说明
- 建议在虚拟环境中运行脚本
- 确保项目根目录在 Python 路径中
"""
        
        readme_path = PROJECT_ROOT / 'scripts' / 'README.md'
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"   📖 查看详细说明: scripts/README.md")
    
    return created_count

if __name__ == "__main__":
    main()