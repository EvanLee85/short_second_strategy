# -*- coding: utf-8 -*-
"""
项目结构扫描脚本 - 生成详细的项目文档
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class ProjectScanner:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.ignore_dirs = {
            '.git', '.vscode', '.idea', '__pycache__', '.pytest_cache',
            'node_modules', '.env', 'venv', 'env', '.mypy_cache',
            'dist', 'build', '*.egg-info', 'logs'
        }
        self.ignore_files = {
            '.gitignore', '.pyc', '.pyo', '.pyd', '.DS_Store',
            'Thumbs.db', '.coverage', '*.log'
        }
    
    def should_ignore(self, path: Path) -> bool:
        """判断是否应该忽略某个路径"""
        name = path.name
        
        # 检查目录
        if path.is_dir() and name in self.ignore_dirs:
            return True
        
        # 检查文件扩展名和名称
        if path.is_file():
            if name in self.ignore_files:
                return True
            if any(name.endswith(ext) for ext in ['.pyc', '.pyo', '.pyd', '.log']):
                return True
        
        return False
    
    def get_file_info(self, file_path: Path) -> Dict:
        """获取文件详细信息"""
        try:
            stat = file_path.stat()
            info = {
                'name': file_path.name,
                'size': stat.st_size,
                'size_human': self.format_size(stat.st_size),
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'extension': file_path.suffix,
                'is_python': file_path.suffix == '.py'
            }
            
            # 如果是Python文件，尝试获取更多信息
            if info['is_python']:
                py_info = self.analyze_python_file(file_path)
                info.update(py_info)
            
            return info
        except Exception as e:
            return {'name': file_path.name, 'error': str(e)}
    
    def analyze_python_file(self, py_file: Path) -> Dict:
        """分析Python文件内容"""
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            info = {
                'lines': len(lines),
                'imports': [],
                'classes': [],
                'functions': [],
                'docstring': None
            }
            
            # 分析导入、类、函数
            in_docstring = False
            docstring_quotes = None
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                
                # 文档字符串检测
                if i < 10 and not info['docstring']:  # 只检查前10行
                    if stripped.startswith('"""') or stripped.startswith("'''"):
                        quote_type = stripped[:3]
                        if stripped.count(quote_type) >= 2:
                            # 单行文档字符串
                            info['docstring'] = stripped.strip(quote_type).strip()
                        elif not in_docstring:
                            in_docstring = True
                            docstring_quotes = quote_type
                            info['docstring'] = stripped[3:]
                    elif in_docstring and docstring_quotes and docstring_quotes in stripped:
                        info['docstring'] = (info['docstring'] or '') + ' ' + stripped.split(docstring_quotes)[0]
                        in_docstring = False
                    elif in_docstring:
                        info['docstring'] = (info['docstring'] or '') + ' ' + stripped
                
                # 导入语句
                if stripped.startswith('import ') or stripped.startswith('from '):
                    info['imports'].append(stripped)
                
                # 类定义
                if stripped.startswith('class '):
                    class_name = stripped.split('class ')[1].split('(')[0].split(':')[0].strip()
                    info['classes'].append(class_name)
                
                # 函数定义
                if stripped.startswith('def '):
                    func_name = stripped.split('def ')[1].split('(')[0].strip()
                    info['functions'].append(func_name)
            
            return info
        except Exception as e:
            return {'analysis_error': str(e)}
    
    def format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def scan_directory(self, dir_path: Path, max_depth: int = 10, current_depth: int = 0) -> Dict:
        """递归扫描目录"""
        if current_depth > max_depth or self.should_ignore(dir_path):
            return None
        
        dir_info = {
            'name': dir_path.name,
            'path': str(dir_path.relative_to(self.root_path)),
            'type': 'directory',
            'children': [],
            'files': [],
            'summary': {
                'total_files': 0,
                'total_size': 0,
                'python_files': 0,
                'config_files': 0,
                'subdirs': 0
            }
        }
        
        try:
            for item in sorted(dir_path.iterdir()):
                if self.should_ignore(item):
                    continue
                
                if item.is_dir():
                    subdir_info = self.scan_directory(item, max_depth, current_depth + 1)
                    if subdir_info:
                        dir_info['children'].append(subdir_info)
                        dir_info['summary']['subdirs'] += 1
                        # 累加子目录统计
                        for key in ['total_files', 'total_size', 'python_files', 'config_files']:
                            dir_info['summary'][key] += subdir_info['summary'][key]
                
                elif item.is_file():
                    file_info = self.get_file_info(item)
                    dir_info['files'].append(file_info)
                    
                    # 更新统计
                    dir_info['summary']['total_files'] += 1
                    if 'size' in file_info:
                        dir_info['summary']['total_size'] += file_info['size']
                    if file_info.get('is_python'):
                        dir_info['summary']['python_files'] += 1
                    if item.suffix in ['.yaml', '.yml', '.json', '.toml', '.ini', '.cfg']:
                        dir_info['summary']['config_files'] += 1
        
        except PermissionError:
            dir_info['error'] = 'Permission denied'
        
        # 格式化总大小
        dir_info['summary']['total_size_human'] = self.format_size(dir_info['summary']['total_size'])
        
        return dir_info
    
    def generate_markdown(self, structure: Dict) -> str:
        """生成Markdown文档"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        md_content = f"""# 项目结构文档

**生成时间:** {timestamp}
**项目根目录:** `{self.root_path}`

## 项目概览

"""
        
        # 项目统计概览
        total_stats = structure['summary']
        md_content += f"""### 整体统计

- **总文件数:** {total_stats['total_files']}
- **Python文件:** {total_stats['python_files']}
- **配置文件:** {total_stats['config_files']}
- **子目录数:** {total_stats['subdirs']}
- **总大小:** {total_stats['total_size_human']}

"""
        
        # 目录结构树
        md_content += "## 目录结构\n\n```\n"
        md_content += self.generate_tree_text(structure)
        md_content += "```\n\n"
        
        # 详细文件列表
        md_content += "## 详细文件信息\n\n"
        md_content += self.generate_detailed_info(structure)
        
        # Python文件分析
        python_files = self.collect_python_files(structure)
        if python_files:
            md_content += "\n## Python文件分析\n\n"
            md_content += self.generate_python_analysis(python_files)
        
        return md_content
    
    def generate_tree_text(self, node: Dict, prefix: str = "", is_last: bool = True) -> str:
        """生成树状结构文本"""
        result = ""
        
        # 当前节点
        connector = "└── " if is_last else "├── "
        result += f"{prefix}{connector}{node['name']}"
        
        # 添加统计信息
        if node['type'] == 'directory':
            stats = node['summary']
            result += f" ({stats['total_files']} files, {stats['total_size_human']})\n"
        else:
            result += "\n"
        
        # 子节点
        if node['type'] == 'directory':
            # 扩展前缀
            extension = "    " if is_last else "│   "
            new_prefix = prefix + extension
            
            # 处理文件
            all_items = node.get('files', []) + node.get('children', [])
            for i, item in enumerate(all_items):
                is_last_item = (i == len(all_items) - 1)
                
                if 'type' in item:  # 是目录
                    result += self.generate_tree_text(item, new_prefix, is_last_item)
                else:  # 是文件
                    connector = "└── " if is_last_item else "├── "
                    file_info = f"{item['name']}"
                    if 'size_human' in item:
                        file_info += f" ({item['size_human']})"
                    result += f"{new_prefix}{connector}{file_info}\n"
        
        return result
    
    def generate_detailed_info(self, node: Dict, current_path: str = "") -> str:
        """生成详细信息"""
        result = ""
        
        if node['type'] == 'directory':
            path = f"{current_path}/{node['name']}" if current_path else node['name']
            
            # 目录信息
            if node['files'] or current_path:  # 不为根目录或有文件时才显示
                result += f"### {path}\n\n"
                
                if node['files']:
                    result += "| 文件名 | 大小 | 修改时间 | 类型 |\n"
                    result += "|--------|------|----------|------|\n"
                    
                    for file in node['files']:
                        name = file.get('name', 'unknown')
                        size = file.get('size_human', '-')
                        modified = file.get('modified', '-')
                        ext = file.get('extension', '-')
                        result += f"| {name} | {size} | {modified} | {ext} |\n"
                    
                    result += "\n"
            
            # 递归处理子目录
            for child in node.get('children', []):
                result += self.generate_detailed_info(child, path)
        
        return result
    
    def collect_python_files(self, node: Dict, files: Optional[List] = None) -> List:
        """收集所有Python文件信息"""
        if files is None:
            files = []
        
        if node['type'] == 'directory':
            # 收集当前目录的Python文件
            for file in node.get('files', []):
                if file.get('is_python'):
                    files.append({
                        'path': f"{node.get('path', '')}/{file['name']}",
                        **file
                    })
            
            # 递归处理子目录
            for child in node.get('children', []):
                self.collect_python_files(child, files)
        
        return files
    
    def generate_python_analysis(self, python_files: List) -> str:
        """生成Python文件分析报告"""
        result = "| 文件路径 | 行数 | 类 | 函数 | 主要功能 |\n"
        result += "|----------|------|----|----- |---------|\n"
        
        for file in python_files:
            path = file.get('path', '')
            lines = file.get('lines', 0)
            classes = len(file.get('classes', []))
            functions = len(file.get('functions', []))
            docstring = (file.get('docstring') or '').strip()
            
            # 截取文档字符串前50个字符
            if docstring:
                docstring = docstring[:50] + "..." if len(docstring) > 50 else docstring
                docstring = docstring.replace('\n', ' ').replace('|', '\\|')
            else:
                docstring = '-'
            
            result += f"| {path} | {lines} | {classes} | {functions} | {docstring} |\n"
        
        # 添加导入分析
        result += "\n### 主要依赖分析\n\n"
        all_imports = []
        for file in python_files:
            all_imports.extend(file.get('imports', []))
        
        # 统计导入频率
        import_count = {}
        for imp in all_imports:
            # 提取包名
            if imp.startswith('import '):
                pkg = imp[7:].split()[0].split('.')[0]
            elif imp.startswith('from '):
                pkg = imp[5:].split()[0].split('.')[0]
            else:
                continue
            
            if pkg not in ['os', 'sys', 'time', 'logging', 'pathlib', 'typing', 'dataclasses']:
                import_count[pkg] = import_count.get(pkg, 0) + 1
        
        if import_count:
            result += "| 包名 | 使用次数 |\n|------|----------|\n"
            for pkg, count in sorted(import_count.items(), key=lambda x: x[1], reverse=True)[:10]:
                result += f"| {pkg} | {count} |\n"
        
        return result
    
    def scan_and_generate(self, output_file: str = "project_structure.md") -> str:
        """扫描项目并生成Markdown文档"""
        print(f"开始扫描项目: {self.root_path}")
        
        # 扫描目录结构
        structure = self.scan_directory(self.root_path)
        
        # 生成Markdown
        markdown_content = self.generate_markdown(structure)
        
        # 保存到文件
        output_path = self.root_path / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"项目结构文档已生成: {output_path}")
        
        # 同时保存JSON格式的原始数据
        json_file = output_path.with_suffix('.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(structure, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"原始数据已保存: {json_file}")
        
        return markdown_content

def main():
    scanner = ProjectScanner()
    content = scanner.scan_and_generate()
    
    # 输出基本统计到控制台
    lines = content.split('\n')
    for line in lines:
        if '**总文件数:**' in line or '**Python文件:**' in line or '**总大小:**' in line:
            print(line.strip())

if __name__ == "__main__":
    main()