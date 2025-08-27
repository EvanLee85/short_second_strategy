import json
import pandas as pd
from backend.data.providers.akshare_provider import AkshareProvider

if __name__ == "__main__":
    prov = AkshareProvider(calendar_name="XSHG", retries=2, retry_sleep=0.5)
    df = prov.fetch_ohlcv("002415.XSHE", "2024-01-02", "2024-03-29", freq="1d", adjust="pre")
    
    # 方案1：将索引转换为字符串
    head_dict = df.head(3).round(4).copy()
    head_dict.index = head_dict.index.strftime('%Y-%m-%d')
    
    tail_dict = df.tail(3).round(4).copy()
    tail_dict.index = tail_dict.index.strftime('%Y-%m-%d')
    
    print(json.dumps({
        "rows": len(df),
        "start": str(df.index.min()),
        "end": str(df.index.max()),
        "cols": list(df.columns),
        "head": head_dict.to_dict(orient="index"),
        "tail": tail_dict.to_dict(orient="index"),
    }, ensure_ascii=False, indent=2))