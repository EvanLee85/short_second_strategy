# -*- coding: utf-8 -*-
# 自动生成：注册 CSV Bundle (中国A股市场)
from zipline.data.bundles import register
from zipline.data.bundles.csvdir import csvdir_equities

# 将 /home/evan/short_second_strategy/data/zipline_csv 目录作为数据源
# 使用 XSHG（上海证券交易所）交易日历
register(
    "sss_csv", 
    csvdir_equities(["/home/evan/short_second_strategy/data/zipline_csv"]),  # csvdir_equities 只接受目录列表
    calendar_name='XSHG'  # 只在 register 函数中指定 calendar_name
)
