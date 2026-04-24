"""
Scanner adapter -- normalizes raw scanner output into a stable Sage payload.
"""
from datetime import datetime, timezone


def normalize_scanner_payload(raw: dict) -> dict:
    return {
        "symbol":             raw.get("symbol", "UNKNOWN"),
        "timeframe":          raw.get("timeframe", "unknown"),
        "bias":               _normalize_bias(raw),
        "confidence":         _normalize_confidence(raw),
        "price":              raw.get("price", raw.get("close", None)),
        "trend_state":        _normalize_trend(raw),
        "structure_state":    raw.get("structure_state", raw.get("pattern", "unknown")),
        "impulse_strength":   raw.get("impulse_strength", "unknown"),
        "pullback_quality":   raw.get("pullback_quality", "unknown"),
        "volatility_state":   raw.get("volatility_state", raw.get("volatility_regime", "unknown")),
        "volume_state":       raw.get("volume_state", raw.get("volume_context", "unknown")),
        "volume_confirmed":   (raw.get("details") or {}).get("volume_confirmed", False),
        "atr":                raw.get("atr", None) or (raw.get("details") or {}).get("atr", None),
        "candle_read":        raw.get("candle_read", raw.get("summary", "")),
        "risk_note":          raw.get("risk_note", ""),
        "status_label":       raw.get("status_label", raw.get("status", "")),
        "scanner_note":       raw.get("scanner_note", raw.get("notes", "")),
        "scanned_at":         raw.get("scanned_at", raw.get("timestamp",
                                  datetime.now(timezone.utc).isoformat())),
        "source":             raw.get("source", "scanner"),
        "upper_wick_ratio":   (raw.get("details") or {}).get("upper_wick_ratio", None),
        "lower_wick_ratio":   (raw.get("details") or {}).get("lower_wick_ratio", None),
        "body_strength":      (raw.get("details") or {}).get("body_strength", None),
        "candles_confirming": (raw.get("details") or {}).get("candles_confirming", {}),
        "range_expansion":    (raw.get("details") or {}).get("range_expansion", "unknown"),
        "vwap_relationship":  (raw.get("details") or {}).get("vwap_relationship", "unknown"),
        "options_fit":        (raw.get("details") or {}).get("options_fit", "unknown"),
    }


def _normalize_bias(raw: dict) -> str:
    bias = raw.get("bias") or raw.get("direction") or raw.get("trend_direction", "")
    if not bias:
        return "neutral"
    bias = str(bias).lower()
    if bias in ("bearish", "down", "short", "downtrend", "sell", "bear"):
        return "bearish"
    if bias in ("bullish", "up", "long", "uptrend", "buy", "bull"):
        return "bullish"
    return "neutral"


def _normalize_trend(raw: dict) -> str:
    trend = raw.get("trend_state") or raw.get("trend") or raw.get("trend_direction", "")
    return str(trend).lower() if trend else "unknown"


def _normalize_confidence(raw: dict) -> float:
    raw_conf = raw.get("confidence", raw.get("confidence_score", None))
    if raw_conf is None:
        return 0.0
    try:
        val = float(raw_conf)
        if val > 1.0:
            val = val / 10.0
        return round(min(max(val, 0.0), 1.0), 2)
    except (TypeError, ValueError):
        return 0.0