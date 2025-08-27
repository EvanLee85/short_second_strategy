# -*- coding: utf-8 -*-
"""
依赖扫描脚本 - 输出当前Python环境的依赖信息
"""

import subprocess
import sys
from pathlib import Path

def get_installed_packages():
    """获取已安装的包列表"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                              capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error getting pip list: {e}"

def get_pip_freeze():
    """获取pip freeze输出"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], 
                              capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error getting pip freeze: {e}"

def scan_imports_in_backend():
    """扫描backend目录中的import语句"""
    project_root = Path(__file__).resolve().parents[1]
    backend_dir = project_root / "backend"
    
    imports = set()
    
    if not backend_dir.exists():
        return ["Backend directory not found"]
    
    # 扫描所有.py文件
    for py_file in backend_dir.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                for line_no, line in enumerate(f, 1):
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('from '):
                        # 提取包名
                        if line.startswith('import '):
                            pkg = line[7:].split()[0].split('.')[0]
                        elif line.startswith('from '):
                            pkg = line[5:].split()[0].split('.')[0]
                        
                        # 过滤掉内置模块和相对导入
                        if not pkg.startswith('.') and pkg not in ['sys', 'os', 'time', 'logging', 'pathlib', 'typing', 'dataclasses', 'abc', 'threading', 'functools']:
                            imports.add(f"{pkg} (from {py_file.name}:{line_no})")
        except Exception as e:
            imports.add(f"Error reading {py_file}: {e}")
    
    return sorted(imports)

def main():
    print("=" * 60)
    print("Python环境依赖信息扫描")
    print("=" * 60)
    
    print(f"\nPython版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    
    print("\n" + "="*40)
    print("已安装包列表 (pip list)")
    print("="*40)
    print(get_installed_packages())
    
    print("\n" + "="*40)
    print("项目依赖扫描 (从backend代码中提取)")
    print("="*40)
    backend_imports = scan_imports_in_backend()
    for imp in backend_imports:
        print(imp)
    
    print("\n" + "="*40)
    print("Pip freeze输出 (便于生成requirements.txt)")
    print("="*40)
    freeze_output = get_pip_freeze()
    print(freeze_output)
    
    # 生成requirements.txt
    project_root = Path(__file__).resolve().parents[1]
    req_file = project_root / "requirements.txt"
    try:
        with open(req_file, 'w', encoding='utf-8') as f:
            f.write(freeze_output)
        print(f"\nrequirements.txt 已生成: {req_file}")
    except Exception as e:
        print(f"\n生成requirements.txt失败: {e}")

if __name__ == "__main__":
    main()