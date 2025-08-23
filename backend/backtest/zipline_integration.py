# -*- coding: utf-8 -*-
# backend/backtest/zipline_integration.py
from __future__ import annotations
import os
import pathlib
from typing import Dict, Any

def ensure_zipline_root(root: str | None = None) -> str:
    """
    中文说明：
    - 确保 Zipline 使用“项目内”的数据目录，避免污染用户主目录 ~/.zipline
    - 若未显式传入，则默认使用 ./var/zipline
    - 返回实际使用的 ZIPLINE_ROOT 路径
    """
    if root is None:
        root = os.environ.get("ZIPLINE_ROOT") or os.path.join(os.getcwd(), "var", "zipline")
    p = pathlib.Path(root)
    p.mkdir(parents=True, exist_ok=True)
    os.environ["ZIPLINE_ROOT"] = str(p)
    return str(p)

def get_zipline_env_info() -> Dict[str, Any]:
    """
    中文说明：
    - 尝试导入 zipline 及关键依赖，收集版本信息
    - 若 zipline 未安装，将抛出 ImportError（交给测试脚本判定 FAIL）
    """
    info: Dict[str, Any] = {}

    import zipline as zl
    info["zipline_version"] = getattr(zl, "__version__", "unknown")

    try:
        import exchange_calendars as xc
        info["exchange_calendars_version"] = getattr(xc, "__version__", "unknown")
    except Exception as e:
        info["exchange_calendars_version"] = f"ERROR: {e!r}"

    try:
        import empyrical_reloaded as emp
        info["empyrical_reloaded_version"] = getattr(emp, "__version__", "unknown")
    except Exception as e:
        info["empyrical_reloaded_version"] = f"ERROR: {e!r}"

    info["ZIPLINE_ROOT"] = os.environ.get("ZIPLINE_ROOT", "")
    return info
