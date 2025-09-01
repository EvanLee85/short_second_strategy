# 实用工具脚本

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
