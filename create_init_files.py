# -*- coding: utf-8 -*-
"""
创建项目中缺失的__init__.py文件
"""

from pathlib import Path

def create_init_files():
    """在项目的Python包目录中创建__init__.py文件"""
    
    project_root = Path(__file__).resolve().parents[1]
    
    # 需要创建__init__.py的目录列表
    init_dirs = [
        project_root / "backend",
        project_root / "backend" / "data",
        project_root / "backend" / "data" / "providers",
        project_root / "tests",
    ]
    
    created_files = []
    existing_files = []
    
    for directory in init_dirs:
        init_file = directory / "__init__.py"
        
        if init_file.exists():
            existing_files.append(init_file)
        else:
            # 确保目录存在
            directory.mkdir(parents=True, exist_ok=True)
            
            # 创建__init__.py文件
            init_content = '# -*- coding: utf-8 -*-\n'
            
            # 根据不同目录添加特定内容
            if directory.name == "providers":
                init_content += '''"""
数据提供器包
"""

from .base import BaseMarketDataProvider, DataProvider

__all__ = [
    "BaseMarketDataProvider",
    "DataProvider",
]
'''
            elif directory.name == "data":
                init_content += '''"""
数据处理模块
"""
'''
            elif directory.name == "backend":
                init_content += '''"""
后端核心模块
"""
'''
            elif directory.name == "tests":
                init_content += '''"""
测试模块
"""
'''
            
            try:
                init_file.write_text(init_content, encoding='utf-8')
                created_files.append(init_file)
            except Exception as e:
                print(f"创建 {init_file} 失败: {e}")
    
    print("__init__.py 文件创建情况:")
    print("=" * 50)
    
    if created_files:
        print("新创建的文件:")
        for f in created_files:
            print(f"  ✓ {f}")
    
    if existing_files:
        print("\n已存在的文件:")
        for f in existing_files:
            print(f"  - {f}")
    
    if not created_files and not existing_files:
        print("  没有找到需要处理的目录")
    
    print(f"\n总计: 创建 {len(created_files)} 个, 已存在 {len(existing_files)} 个")

if __name__ == "__main__":
    create_init_files()