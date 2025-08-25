# backend/data/normalize.py
# -*- coding: utf-8 -*-

"""
代码规范映射（normalize.symbol）
--------------------------------
目标：
  - 统一内部证券代码形态为：<6位代码>.<交易所>，如：
      - 上交所：600519.XSHG
      - 深交所：000063.XSHE
  - 屏蔽外部平台（TuShare、AkShare、CSV、用户输入等）不同代码风格：
      - "600519.SH" / "000063.SZ" / "sh600519" / "sz000063" / "600519" 等
  - 与 Zipline 的 symbol 对齐：Zipline 的 CSV bundle 可直接使用内部标准作为 symbol

提供两个主要函数：
  - to_internal(symbol, *, default_exchange=None) -> str
      把任意风格的 symbol 转为统一内部形态。
  - from_internal(internal, *, style="tushare") -> str
      将内部形态映射回目标平台风格（默认 tushare：XSHG->SH, XSHE->SZ）。

注意：
  - 仅覆盖 A 股上/深常见证券代码规则，指数、北交所等可按需扩展。
  - 如果无法从纯数字代码可靠地推断交易所，可通过 default_exchange 指定兜底。

--------------------------------
统一代码规范 + 交易日历对齐与复权
================================
本模块在第3步的基础上，新增第4步能力：
  - 使用 exchange_calendars 生成上交所(XSHG)交易日历 sessions
  - 对任意来源的 OHLCV 日线数据执行“对齐 + 停牌日补行 + 复权”流水线
  - 默认“前复权”（若无复权因子则原样返回）

核心函数：
  1) to_internal() / from_internal()      —— 第3步，代码格式规范化（已实现）
  2) get_sessions_index()                 —— 生成 XSHG 指定起止的“交易日”索引（日期粒度）
  3) align_and_adjust_ohlcv()             —— 对齐 + 停牌补行 + 复权 的一条龙处理

注意：
  - 输入 DataFrame 需包含列：open, high, low, close, volume（大小写不限会自动统一）
  - 索引若含时区/时间，会被归一化为“本地日历日期”（亚洲/上海）粒度
  - 停牌日补行：OHLC=前收、volume=0
  - 复权：优先读取列 adj_factor（若不存在或 method='none' 则不做价格调整）
      * 前复权(pre)：price_adj = price_raw * (factor_i / factor_last)
      * 后复权(post)：price_adj = price_raw * (factor_i / factor_first)
"""

from __future__ import annotations
import re
from typing import Optional, Tuple
import pandas as pd
import exchange_calendars as xcals

# 交易所后缀标准化映射：
#   外部常见写法 -> 内部标准写法
_EX_SUFFIX_MAP = {
    "SH": "XSHG",
    "SSE": "XSHG",
    "SHSE": "XSHG",
    "SS": "XSHG",

    "SZ": "XSHE",
    "SZSE": "XSHE",
}

# 从内部标准到各平台风格的映射（目前提供 tushare / simple 两种）
# - tushare: XSHG->SH, XSHE->SZ
# - simple : 保留内部标准，直接返回（可用于 Zipline、内部统一展示）
_STYLE_EX_MAP = {
    "tushare": {
        "XSHG": "SH",
        "XSHE": "SZ",
    },
    "simple": {
        "XSHG": "XSHG",
        "XSHE": "XSHE",
    },
}


def _cleanup(s: str) -> str:
    """将输入进行基础清洗：
    - 去除首尾空格
    - 转大写
    - 去掉常见分隔符（下划线/短横线）
    """
    return s.strip().upper().replace("_", "").replace("-", "")


def _split_by_dot(s: str) -> Tuple[str, Optional[str]]:
    """按点号拆分：返回 (主体, 后缀或None)
    仅按第一个点分割，后续逻辑自行判断后缀是否为交易所标识。
    """
    if "." in s:
        left, right = s.split(".", 1)
        return left, right
    return s, None


def _normalize_exchange_suffix(suffix: Optional[str]) -> Optional[str]:
    """将外部多种交易所后缀写法规范化为内部标准：XSHG / XSHE。
    - 若 suffix 本就为标准写法，原样返回
    - 若无法识别，返回 None
    """
    if not suffix:
        return None
    suf = suffix.upper()
    if suf in ("XSHG", "XSHE"):
        return suf
    return _EX_SUFFIX_MAP.get(suf)


def _guess_exchange_by_digits(code: str) -> Optional[str]:
    """根据 6 位数字代码的前缀规则**猜测**所属交易所。
    仅作为启发式规则（适用大多数 A 股股票/ETF）：
      - 上交所（XSHG）：60*, 68*（科创板）, 50*/51*/52*/56*/58*/59*（常见ETF/债）
      - 深交所（XSHE）：00*, 30*（创业板）
    若无法可靠判断，返回 None。

    警告：
      - 指数、基金、转债等可能存在特例；如需严谨，请从数据源携带交易所信息。
    """
    if not re.fullmatch(r"\d{6}", code):
        return None

    if code.startswith(("60", "68", "50", "51", "52", "56", "58", "59")):
        return "XSHG"
    if code.startswith(("00", "30")):
        return "XSHE"

    # 其他前缀（如 20/39/15 等）视业务需要自行扩展
    return None


def to_internal(symbol: str, *, default_exchange: Optional[str] = None) -> str:
    """将任意风格的证券代码转为内部统一形态：<6位代码>.<交易所>

    参数：
      symbol            : 外部输入代码（如 "600519.SH" / "sh600519" / "600519"）
      default_exchange  : 当无法从 symbol 推断交易所时，使用该兜底值（"XSHG"/"XSHE"）

    返回：
      内部标准代码，如 "600519.XSHG"、"000063.XSHE"

    规则说明：
      1) 若包含点号后缀（.SH/.SZ/XSHG/XSHE 等），直接规范化该后缀。
      2) 若以字母前缀开头（sh600519/sz000063），通过前缀判断交易所。
      3) 若仅 6 位数字，通过启发式规则猜测交易所，否则用 default_exchange。
      4) 最终代码统一为 6 位数字 + "." + 交易所（XSHG/XSHE）。

    异常：
      若无法得到 6 位数字主体，或无法确定交易所（且未提供 default_exchange），
      会抛出 ValueError 以便上层处理。
    """
    raw = _cleanup(symbol)
    body, suf = _split_by_dot(raw)

    exchange = _normalize_exchange_suffix(suf)  # 若提供了后缀，先尝试规范化

    # 情形 A：有标准/可映射后缀
    if exchange:
        # body 既可能是 "sh600519" 也可能是 "600519"；要把字母前缀剥掉
        m = re.fullmatch(r"([A-Z]+)?(\d{6})", body)
        if not m:
            raise ValueError(f"无法解析代码主体：{symbol}")
        code = m.group(2)
        return f"{code}.{exchange}"

    # 情形 B：无点号后缀，可能是 "sh600519"/"sz000063" 这类
    m = re.fullmatch(r"(SH|SZ|SSE|SZSE)?(\d{6})", raw)
    if m and m.group(1):
        code = m.group(2)
        exchange = _normalize_exchange_suffix(m.group(1))
        if not exchange:
            raise ValueError(f"无法识别交易所后缀：{symbol}")
        return f"{code}.{exchange}"

    # 情形 C：纯 6 位数字，尝试按规则猜交易所
    if re.fullmatch(r"\d{6}", raw):
        code = raw
        exchange = _guess_exchange_by_digits(code) or (default_exchange.upper() if default_exchange else None)
        if not exchange:
            raise ValueError(f"无法从代码推断交易所且未提供 default_exchange：{symbol}")
        return f"{code}.{exchange}"

    # 情形 D：诸如 "600519SH" 这类不带点的尾缀（不常见），做一次扫描尝试
    m = re.fullmatch(r"(\d{6})(SH|SZ|XSHG|XSHE)", raw)
    if m:
        code = m.group(1)
        exchange = _normalize_exchange_suffix(m.group(2))
        if exchange:
            return f"{code}.{exchange}"

    raise ValueError(f"不支持的代码格式：{symbol}")


def from_internal(internal: str, *, style: str = "tushare") -> str:
    """将内部标准代码（如 600519.XSHG）转换为指定平台风格。

    参数：
      internal : 内部标准代码，形如 "600519.XSHG" / "000063.XSHE"
      style    : 输出风格：
                 - "tushare": 600519.SH / 000063.SZ
                 - "simple" : 原样返回（或与内部一致，用于 Zipline/内部展示）

    返回：
      目标平台风格代码字符串。

    异常：
      若内部代码格式不正确、或 style 未配置相应映射，抛出 ValueError。
    """
    s = _cleanup(internal)
    code, suf = _split_by_dot(s)
    if not (re.fullmatch(r"\d{6}", code) and suf):
        raise ValueError(f"内部代码格式不正确：{internal}")

    exch = _normalize_exchange_suffix(suf)
    if not exch:
        raise ValueError(f"未知交易所后缀：{internal}")

    style = style.lower()
    if style not in _STYLE_EX_MAP:
        raise ValueError(f"未知输出风格：{style}")

    ex_map = _STYLE_EX_MAP[style]
    if exch not in ex_map:
        raise ValueError(f"风格 {style} 不支持交易所：{exch}")

    # tushare：600519.SH
    return f"{code}.{ex_map[exch]}"


# ---------- 第4步：交易日历对齐 + 停牌补行 + 复权 ----------

def get_sessions_index(start: str | pd.Timestamp,
                       end: str | pd.Timestamp,
                       calendar_name: str = "XSHG") -> pd.DatetimeIndex:
    """
    生成【交易日】日期索引（无时区、按“日”粒度），用于对齐日线数据。

    参数：
      start / end   : 起止日期（字符串或 Timestamp），建议为“YYYY-MM-DD”
      calendar_name : 交易日历名称，默认 XSHG（上交所）

    返回：
      DatetimeIndex（无时区、形如 2024-01-02, 2024-01-03, ...），已剔除节假日/周末。
    注意：
      exchange_calendars 的 sessions_in_range 要求传入“无时区（tz-naive）”的日期；
      因此这里显式去掉任何可能携带的时区信息，并只保留“日期”。
    """
    cal = xcals.get_calendar(calendar_name)

    # —— 将输入统一为“无时区 + 日期”的 Timestamp ——
    def _to_naive_day(x) -> pd.Timestamp:
        ts = pd.Timestamp(x)
        # 若带时区则去时区；随后归一化为当天 00:00
        if ts.tzinfo is not None:
            ts = ts.tz_localize(None)
        return ts.normalize()

    start_naive = _to_naive_day(start)
    end_naive   = _to_naive_day(end)

    # —— 生成交易日会话区间（传入必须为 tz-naive）——
    sessions = cal.sessions_in_range(start_naive, end_naive)

    # 返回也统一为“无时区 + 日期索引”
    if getattr(sessions, "tz", None) is not None:
        sessions = sessions.tz_localize(None)

    return sessions.normalize()


def _unify_ohlcv_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    将各种大小写/别名列统一到 open/high/low/close/volume/adj_factor 命名。
    不存在的列将报错（除 adj_factor 可缺省）。
    """
    col_map = {c.lower(): c for c in df.columns}
    need = ["open", "high", "low", "close", "volume"]
    missing = [c for c in need if c not in col_map]
    if missing:
        raise ValueError(f"缺少必要列：{missing}，现有列：{list(df.columns)}")

    # 构造统一后的 DataFrame（深拷贝避免副作用）
    out = pd.DataFrame({
        "open":   df[col_map["open"]].astype("float64"),
        "high":   df[col_map["high"]].astype("float64"),
        "low":    df[col_map["low"]].astype("float64"),
        "close":  df[col_map["close"]].astype("float64"),
        "volume": df[col_map["volume"]].astype("float64"),
    }, index=pd.to_datetime(df.index))

    # 可选列：adj_factor
    if "adj_factor" in col_map:
        out["adj_factor"] = pd.to_numeric(df[col_map["adj_factor"]], errors="coerce")

    # 归一化索引到“日期粒度、无时区”
    out.index = out.index.tz_localize(None).normalize()
    # 去重：同一天多条（若上层曾给到更高频），聚合为日线（O=首，H=max，L=min，C=末，V=sum）
    if out.index.has_duplicates:
        agg = {
            "open": "first",
            "high": "max",
            "low":  "min",
            "close":"last",
            "volume":"sum",
        }
        if "adj_factor" in out.columns:
            # 复权因子：按“最后一个”为当日有效（多数数据源为收盘时的因子）
            agg["adj_factor"] = "last"
        out = out.groupby(out.index).agg(agg)
    return out.sort_index()


def _apply_adjustment(df: pd.DataFrame, method: str = "pre", factor_col: str = "adj_factor") -> pd.DataFrame:
    """
    对价格列应用复权。支持：
      - 'pre'  : 前复权（历史价格 * factor_i / factor_last）
      - 'post' : 后复权（历史价格 * factor_i / factor_first）
      - 'none' : 不复权或无复权因子时等同于不处理
    """
    method = (method or "pre").lower()
    if method == "none" or factor_col not in df.columns:
        return df

    fac = df[factor_col].astype("float64")
    if fac.isna().all():
        # 没有可用的复权因子，直接返回
        return df

    # 用最近可得的因子填充缺失（常见于个别日期缺口）
    fac = fac.ffill().bfill()

    if method == "pre":
        anchor = fac.iloc[-1]  # 以最后一个交易日因子为基准
    elif method == "post":
        anchor = fac.iloc[0]   # 以后复权基准（首日因子）
    else:
        raise ValueError(f"未知复权方法：{method}")

    # 计算倍率
    mult = fac / anchor
    out = df.copy()
    for col in ("open", "high", "low", "close"):
        out[col] = (out[col] * mult).astype("float64")

    return out


def align_and_adjust_ohlcv(df: pd.DataFrame,
                           start: str | pd.Timestamp,
                           end: str | pd.Timestamp,
                           *,
                           calendar_name: str = "XSHG",
                           adjust: str = "pre",
                           fill_leading: bool = False) -> pd.DataFrame:
    """
    对任意来源的日线 OHLCV 数据执行“交易日日历对齐 + 停牌日补行 + 复权”处理。

    参数：
      df             : 输入 DataFrame，需含 open/high/low/close/volume（大小写不敏感）
      start, end     : 期望的对齐区间（含端点）；建议使用 YYYY-MM-DD
      calendar_name  : 交易日历（默认 XSHG）
      adjust         : 复权口径：'pre'（默认）/'post'/'none'
      fill_leading   : 若起始若干交易日无数据，是否也用“首个可得前收”补齐；
                       - False（默认）：丢弃起始这段缺数据的交易日
                       - True ：以首个可得 close 作为“前收”向前填充，强制齐头

    返回：
      已按交易日对齐、补行、完成复权处理的 DataFrame（列：open,high,low,close,volume 以及可选 adj_factor）
    """
    if df is None or len(df) == 0:
        raise ValueError("输入 df 为空，无法对齐与复权")

    # 1) 列名 & 索引标准化
    base = _unify_ohlcv_columns(df)

    # 2) 构建目标交易日索引
    ses = get_sessions_index(start, end, calendar_name=calendar_name)

    # 3) 先与交易日做并集对齐，再决定如何处理起始缺口
    aligned = base.reindex(ses)

    # 4) 停牌日补行：
    #    规则：如果该日无交易数据，则 OHLC = 前收、volume = 0。
    #    实现方式：先前向填充 close_ffill，再将 open/high/low/close 用 close_ffill 填缺，volume 缺失置 0。
    close_ffill = aligned["close"].ffill()

    if not fill_leading:
        # 丢弃“前部完全缺失”的交易日（避免用错误的“前收”凭空造价）
        # 判定标准：在出现第一条有效 close 之前的日期，一律丢弃
        first_valid = close_ffill.first_valid_index()
        if first_valid is None:
            # 整段都没有有效数据，直接返回空
            return aligned.iloc[0:0]
        aligned = aligned.loc[first_valid:]  # 从首个有效开始
        ses = aligned.index  # 更新对齐索引
        close_ffill = aligned["close"].ffill()

    # 用“前收”补 open/high/low/close 的缺失
    for col in ("open", "high", "low", "close"):
        aligned[col] = aligned[col].where(aligned[col].notna(), close_ffill)

    # 成交量缺失补 0（停牌日）
    aligned["volume"] = aligned["volume"].fillna(0.0)

    # 5) 复权处理（若有 adj_factor 且选择 pre/post）
    adjusted = _apply_adjustment(aligned, method=adjust, factor_col="adj_factor" if "adj_factor" in aligned.columns else "adj_factor")

    # 6) 收尾：确保类型，并排序索引（保险）
    for c in ("open", "high", "low", "close", "volume"):
        adjusted[c] = pd.to_numeric(adjusted[c], errors="coerce").astype("float64")
    adjusted = adjusted.sort_index()

    return adjusted


# -----------------------------
# 一些快速示例（作为文档注释/开发期自测）：
# -----------------------------
if __name__ == "__main__":
    samples = [
        "600519.SH",
        "000063.SZ",
        "sh600519",
        "sz000063",
        "600519",
        "000063",
        "600519.XSHG",
        "000063.XSHE",
        "600519SH",
        "000063SZ",
    ]
    for s in samples:
        try:
            i = to_internal(s, default_exchange="XSHG")
            print(s, "=>", i, "=>", from_internal(i, style="tushare"))
        except Exception as e:
            print(s, "=> ERROR:", e)