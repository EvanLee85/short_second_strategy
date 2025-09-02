# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from backend.core.macro_filter import MacroFilter
from backend.core.sector_rotation import SectorRotation
from backend.core.stock_selector import StockSelector
from backend.core.entry_signals import evaluate_signal, build_trade_plan
from backend.core.risk_manager import RiskManager
from backend.core.sentry import MarketSentry
from backend.data.fetcher import get_ohlcv

api_bp = Blueprint("api", __name__)

@api_bp.get("/health")
def health():
    return {"status": "ok"}

@api_bp.get("/macro/status")
def macro_status():
    mf = MacroFilter.load_from_config()
    return jsonify(mf.evaluate())

@api_bp.get("/sectors/rotation")
def sectors_rotation():
    sector = request.args.get("sector", "AI")
    rot = SectorRotation.load_from_config()
    return jsonify(rot.evaluate(sector))

@api_bp.get("/stocks/leaders")
def stocks_leaders():
    stype = request.args.get("type", "first-line")
    sector = request.args.get("sector", "AI")
    sel = StockSelector.load_from_config()

    if stype == "first-line":
        return jsonify(sel.identify_first_line(sector=sector))
    elif stype == "second-line":
        return jsonify(sel.identify_second_line(sector=sector))
    else:
        return jsonify({"error": "unknown type", "type": stype}), 400

@api_bp.post("/trades/signal")
def trade_signal():
    payload = request.get_json(silent=True) or {}
    symbol = payload.get("symbol")
    if symbol and not payload.get("ohlcv"):
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        df = get_ohlcv(symbol, start, end)
        # 将 DataFrame 转换为传给 evaluate_signal 的格式
        payload["ohlcv"] = {
            "t": df.index.strftime("%Y-%m-%d").tolist(),
            "o": df["open"].tolist(),
            "h": df["high"].tolist(),
            "l": df["low"].tolist(),
            "c": df["close"].tolist(),
            "v": df["volume"].tolist(),
        }
    return jsonify(evaluate_signal(payload))

@api_bp.post("/risk/evaluate")
def risk_evaluate():
    """
    三闸门评估（POST JSON）：
    {
      "symbol": "002415",
      "sector": "AI",
      "price": 11.95   # 可选；不传则由风控模块使用 stub close
    }
    """
    payload = request.get_json(silent=True) or {}
    rm = RiskManager.load_from_config()
    return jsonify(rm.evaluate_trade_gates(payload))

@api_bp.post("/risk/position")
def risk_position():
    """
    仓位建议（POST JSON）：
    {
      "symbol": "002415",
      "sector": "AI",
      "account_size": 200000,   # 账户资金（元）
      "price": 11.95,           # 进场价
      "stop":  11.83            # 可选；不传则按 ATR 推导
    }
    """
    payload = request.get_json(silent=True) or {}
    rm = RiskManager.load_from_config()
    return jsonify(rm.suggest_position(payload))

@api_bp.post("/risk/exit-plan")
def risk_exit_plan():
    """
    撤退/执行剧本（POST JSON）：
    {
      "symbol":"002415",
      "sector":"AI",
      "entry": 11.95,          # 可选；不传则用 ensure_price_atr 的价格
      "stop":  11.83,          # 可选；无则按 ATR 推导
      "target": null
    }
    """
    payload = request.get_json(silent=True) or {}
    rm = RiskManager.load_from_config()
    return jsonify(rm.build_exit_plan(payload))

@api_bp.post("/trades/plan")
def trade_plan():
    """
    交易计划聚合（POST JSON）：
    {
      "symbol": "002415",
      "sector": "AI",
      "mode": "reversal",
      "price": 11.95,
      "account_size": 200000,
      "intraday": {...}, "ohlcv": {...}  # 可选
    }
    返回：统一交易计划（信号+三闸门+仓位+撤退剧本）
    """
    payload = request.get_json(silent=True) or {}
    return jsonify(build_trade_plan(payload))

@api_bp.post("/paper/open")
def paper_open():
    """
    开仓：先生成交易计划；若 decision=ENTER 则建仓
    请求示例：
    {"symbol":"002415","sector":"AI","mode":"breakout","price":12.20,"account_size":200000}
    """
    payload = request.get_json(silent=True) or {}
    plan = build_trade_plan(payload)
    rm = RiskManager.load_from_config()

    if plan.get("decision") == "ENTER":
        pos = plan["position"]        # 来自 suggest_position(...)
        gates = plan["gates"]         # 取 stop/target/atr
        result = rm.paper_open(
            symbol=plan["symbol"],
            qty=int(pos["position"]["shares"]),
            entry=float((payload.get("price") or gates["inputs"]["price"])),
            stop=float(gates["levels"]["stop"]),
            target=float(gates["levels"]["target"]),
            atr=float(gates["inputs"]["atr"]),
        )
    else:
        result = {"ok": False, "error": "decision_hold", "state": rm.paper_state()}

    return jsonify({"plan": plan, "open_result": result})

@api_bp.post("/paper/step")
def paper_step():
    """推进一步：{"price":12.45,"high":12.55,"low":12.30}"""
    j = request.get_json(silent=True) or {}
    rm = RiskManager.load_from_config()
    r = rm.paper_step(price=float(j.get("price")), high=j.get("high"), low=j.get("low"))
    return jsonify(r)

@api_bp.get("/paper/state")
def paper_state():
    """查看纸上状态"""
    rm = RiskManager.load_from_config()
    return jsonify(rm.paper_state())

@api_bp.get("/sentry/status")
def sentry_status():
    """市场哨兵状态查询（硬熔断 + 软情绪）。"""
    ms = MarketSentry.load_from_config()
    return jsonify(ms.evaluate())

@api_bp.post("/sentry/check")
def sentry_check():
    """
    对某个计划进行“是否允许执行”的即席检查。
    - 输入可为空（走 stub）。
    - 输出只返回 allowed / halt，便于前端聚合。
    """
    ms = MarketSentry.load_from_config()
    ev = ms.evaluate()
    return jsonify({
        "allowed": bool(ev["summary"]["allowed"]),
        "halt": bool(ev["summary"]["halt"]),
        "ref": ev  # 方便调试，前端可以忽略
    })