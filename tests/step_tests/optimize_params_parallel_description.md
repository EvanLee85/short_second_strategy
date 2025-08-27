📚 使用说明
1. 串行优化脚本 (optimize_params.py)
适合细致分析，提供详细输出：
bash# 快速测试（约32种组合）
python optimize_params.py --quick

# 完整优化（数百种组合）
python optimize_params.py --full
2. 并行优化脚本 (optimize_parallel.py)
利用多核CPU加速，更快完成：
bash# 快速并行优化（默认使用CPU核心数-1）
python optimize_parallel.py --mode quick

# 完整并行优化
python optimize_parallel.py --mode full

# 指定进程数
python optimize_parallel.py --mode quick --workers 2
🎯 主要功能
优化的参数包括：

信号参数: lookback窗口、突破阈值
仓位管理: 仓位大小、最大持仓天数
风控参数: 止盈止损比例、MA离场条件

输出结果：

TOP 5 收益率 - 最赚钱的参数组合
TOP 5 夏普比率 - 风险调整后收益最好的
综合最佳 - 平衡收益、风险和回撤的最优解
自动生成优化策略文件 - algo_sss_optimized.py

🚀 快速开始
bash# 1. 保存脚本
# 将并行优化脚本保存为: optimize_parallel.py

# 2. 运行快速优化（推荐先试这个）
python optimize_parallel.py --mode quick

# 3. 查看结果
# 结果保存在: var/optimization_results/
# - optimization_results_*.csv (所有结果)
# - best_params_*.json (最佳参数)
# - backend/zipline/algo_sss_optimized.py (优化后的策略)
📊 预期输出示例
🚀 策略参数优化工具
模式: 快速优化
总组合数: 162

使用 4 个进程进行并行优化
开始并行回测...

✓ [1/162] 收益: 5.3%, 夏普: 1.25, 回撤: -2.1%
✓ [2/162] 收益: 3.8%, 夏普: 0.98, 回撤: -3.5%
...

📊 优化结果分析
🏆 收益率 TOP 5:
1. 收益率: 7.52%, 夏普: 1.45, 回撤: -2.3%, 交易: 8次
   参数: lookback=15, position_size=0.25, ...

💎 综合评分最佳:
综合评分: 8.25
收益率: 6.85%
夏普比率: 1.52
最大回撤: -2.1%

🎯 最佳参数配置:
  lookback: 15
  position_size: 0.20
  max_hold_days: 8
  take_profit: 5.0
  stop_loss: 2.0
  breakout_threshold: 0.99
⚙️ 高级用法
自定义参数范围
编辑脚本中的 QUICK_PARAM_GRID 或 FULL_PARAM_GRID：
pythonQUICK_PARAM_GRID = {
    "lookback": [你想测试的值],
    "position_size": [你想测试的值],
    # ...
}
调整评分权重
修改综合评分计算：
pythondf['score'] = (
    df['total_return'] * 0.5 +      # 提高收益权重到50%
    df['sharpe_ratio'] * 10 * 0.3 + # 降低夏普权重到30%
    (-df['max_drawdown']) * 0.2     # 降低回撤权重到20%
)
这些工具能帮你快速找到最佳参数组合，提高策略表现！


---------------------------------------------------------


🚀 使用步骤

保存脚本文件：

bash# 保存第一个脚本
vim tests/optimize_params.py
# 粘贴串行优化脚本内容

# 保存第二个脚本  
vim tests/optimize_parallel.py
# 粘贴并行优化脚本内容

给脚本添加执行权限：

bashchmod +x tests/optimize_params.py
chmod +x tests/optimize_parallel.py

运行优化：

bash# 在项目根目录下运行
cd ~/short_second_strategy

# 激活环境
conda activate sss_py311

# 运行并行优化（推荐，更快）
python tests/optimize_parallel.py --mode quick

# 或运行串行优化（更详细的输出）
python tests/optimize_params.py --quick
💡 选择建议

开发测试阶段：使用并行优化的 --mode quick，快速找到较好的参数
最终优化阶段：使用并行优化的 --mode full，全面搜索最佳参数
调试问题时：使用串行优化，因为输出更详细，容易定位问题

📊 查看结果
优化完成后，结果会保存在：
bashvar/
├── optimization_results/
│   ├── optimization_results_20250823_xxxxx.csv  # 所有测试结果
│   ├── best_params_20250823_xxxxx.json         # 最佳参数
│   └── intermediate_results.csv                # 中间结果（串行版本）

backend/
├── zipline/
│   └── algo_sss_optimized.py                   # 自动生成的最优策略
运行示例：
bash# 快速测试一下
python tests/optimize_parallel.py --mode quick --workers 2
这样就能快速找到最佳参数组合了！