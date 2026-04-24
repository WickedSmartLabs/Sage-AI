"""
Sage Market Interpreter -- hybrid interpretation layer.

Known clean setups -> deterministic rules.
Ambiguous/partial setups -> LLM fallback with enforced JSON output.

Input:  normalized scanner payload (dict)
Output: structured interpretation (dict)
"""
import json
import logging
from openai import AsyncOpenAI
from config.settings import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)
logger = logging.getLogger(__name__)


# ── Deterministic rules ───────────────────────────────────────────────────────

def _rule_based_interpret(signal: dict) -> dict | None:
    bias = signal.get("bias")
    structure = signal.get("structure_state")
    pullback = signal.get("pullback_quality")
    impulse = signal.get("impulse_strength")
    volume = signal.get("volume_confirmed")
    range_expansion = signal.get("range_expansion", "unknown")
    body_strength = signal.get("body_strength")
    candles_confirming = signal.get("candles_confirming", {})
    confirming_label = candles_confirming.get("label", "unknown") if candles_confirming else "unknown"
    vwap = signal.get("vwap_relationship", "unknown")
    options_fit = signal.get("options_fit", "unknown")
    confidence = signal.get("confidence", 0.0)

    # ── Clean bearish continuation ────────────────────────────────────────────
    if (
        bias == "bearish"
        and structure == "continuation"
        and pullback == "weak"
        and impulse in ("strong", "moderate")
    ):
        candle_note = _candle_read(body_strength, range_expansion, confirming_label, "bearish")
        return {
            "market_read": "Bearish continuation structure remains intact.",
            "candle_interpretation": candle_note,
            "vwap_context": _vwap_context(vwap, bias),
            "recommendation": {
                "stance": "bearish_bias",
                "aggressive": "Look for continuation confirmation before entering short.",
                "conservative": "Wait for a clean breakdown below structure before acting.",
                "invalidation": "A stronger reclaim above recent structure weakens the bearish case.",
            },
            "options_fit": options_fit,
            "options_note": _options_note(options_fit, bias),
            "risk": signal.get("risk_note") or "No confirmed reversal yet.",
            "confidence": confidence,
            "mode": "rule_based",
        }

    # ── Clean bullish continuation ────────────────────────────────────────────
    if (
        bias == "bullish"
        and structure == "continuation"
        and pullback == "weak"
        and impulse in ("strong", "moderate")
    ):
        candle_note = _candle_read(body_strength, range_expansion, confirming_label, "bullish")
        return {
            "market_read": "Bullish continuation structure remains intact.",
            "candle_interpretation": candle_note,
            "vwap_context": _vwap_context(vwap, bias),
            "recommendation": {
                "stance": "bullish_bias",
                "aggressive": "Look for continuation confirmation before entering long.",
                "conservative": "Wait for a clean breakout or higher-quality pullback entry.",
                "invalidation": "A decisive break below recent structure weakens the bullish case.",
            },
            "options_fit": options_fit,
            "options_note": _options_note(options_fit, bias),
            "risk": signal.get("risk_note") or "No confirmed reversal yet.",
            "confidence": confidence,
            "mode": "rule_based",
        }

    # ── Consolidation ─────────────────────────────────────────────────────────
    if structure == "consolidation" or range_expansion == "contracting":
        return {
            "market_read": "Market is compressing. No directional edge present.",
            "candle_interpretation": "Range contracting with no clean impulse — indecision.",
            "vwap_context": _vwap_context(vwap, bias),
            "recommendation": {
                "stance": "wait",
                "aggressive": "Avoid forcing an entry in a ranging market.",
                "conservative": "Stand aside until a directional breakout is confirmed.",
                "invalidation": "N/A — wait for structure to resolve.",
            },
            "options_fit": "poor",
            "options_note": "Contracting range is poor conditions for premium buying.",
            "risk": "Low-quality setup. Range-bound conditions increase false signal risk.",
            "confidence": confidence,
            "mode": "rule_based",
        }

    # ── Reversal with volume ──────────────────────────────────────────────────
    if structure == "reversal" and volume:
        direction = "upside" if bias == "bullish" else "downside"
        return {
            "market_read": f"Potential reversal forming with volume support toward {direction}.",
            "candle_interpretation": (
                signal.get("candle_read")
                or f"Structure shifting with volume confirmation toward {direction}."
            ),
            "vwap_context": _vwap_context(vwap, bias),
            "recommendation": {
                "stance": f"cautious_{bias}_bias" if bias else "wait",
                "aggressive": "Aggressive traders may look for early entry with tight risk.",
                "conservative": "Wait for confirmation before treating this as a confirmed reversal.",
                "invalidation": "Failure to follow through on volume would invalidate the reversal thesis.",
            },
            "options_fit": options_fit,
            "options_note": _options_note(options_fit, bias),
            "risk": signal.get("risk_note") or "Early reversal signals carry higher failure rate.",
            "confidence": confidence,
            "mode": "rule_based",
        }

    return None


# ── Helper functions ──────────────────────────────────────────────────────────

def _candle_read(body_strength, range_expansion, confirming_label, bias) -> str:
    parts = []

    if body_strength is not None:
        if body_strength > 0.6:
            parts.append("strong conviction candles")
        elif body_strength > 0.35:
            parts.append("moderate body strength")
        else:
            parts.append("weak candle bodies — low conviction")

    if range_expansion == "expanding":
        parts.append("range expanding")
    elif range_expansion == "contracting":
        parts.append("range contracting — momentum fading")
    else:
        parts.append("range normal")

    if confirming_label == "strong_confirmation":
        parts.append(f"candles confirming {bias} direction cleanly")
    elif confirming_label == "moderate_confirmation":
        parts.append("mixed candle confirmation")
    else:
        parts.append("candles not confirming direction well")

    return ", ".join(parts) if parts else "Candle data unavailable."


def _vwap_context(vwap, bias) -> str:
    if vwap == "above":
        return "Price is above VWAP — bullish intraday positioning." if bias == "bullish" \
            else "Price above VWAP but bias is bearish — watch for VWAP rejection."
    if vwap == "below":
        return "Price is below VWAP — bearish intraday positioning." if bias == "bearish" \
            else "Price below VWAP but bias is bullish — needs reclaim to confirm."
    if vwap == "at":
        return "Price is at VWAP — decision point. Direction of next move matters."
    return "VWAP relationship unknown."


def _options_note(options_fit, bias) -> str:
    direction = "calls" if bias == "bullish" else "puts" if bias == "bearish" else "options"
    if options_fit == "good":
        return f"Structure suits {direction} — expanding range with strong candles."
    if options_fit == "mediocre":
        return f"Direction exists but structure is not ideal for {direction}."
    if options_fit == "poor":
        return f"Poor conditions for {direction} — avoid buying premium here."
    return "Options fit unclear."


# ── LLM fallback ─────────────────────────────────────────────────────────────

_INTERPRETER_PROMPT = """
You are a disciplined market analyst. You receive structured market scanner data
and produce a structured interpretation. You do not predict or guarantee outcomes.
You describe what the structure shows and offer scenario-based guidance.

Respond ONLY with a valid JSON object matching this exact schema:
{
    "market_read": "one sentence describing current market structure",
    "candle_interpretation": "one sentence describing candle behavior and conviction",
    "vwap_context": "one sentence on price relationship to VWAP",
    "recommendation": {
        "stance": "one of: bullish_bias, bearish_bias, wait, neutral",
        "aggressive": "guidance for aggressive traders",
        "conservative": "guidance for conservative traders",
        "invalidation": "what would invalidate this read"
    },
    "options_fit": "one of: good, mediocre, poor, unknown",
    "options_note": "one sentence on whether conditions suit options trading",
    "risk": "one sentence on primary risk to this view",
    "confidence": 0.0
}

Do not include any text outside the JSON object. No markdown, no preamble.
""".strip()


async def _llm_interpret(signal: dict) -> dict:
    signal_text = json.dumps(signal, indent=2, default=str)

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": _INTERPRETER_PROMPT},
                {"role": "user", "content": f"Scanner data:\n{signal_text}"},
            ],
            temperature=0.2,
            max_tokens=600,
        )

        raw = response.choices[0].message.content or ""
        result = json.loads(raw)
        result["mode"] = "llm_fallback"
        result.setdefault("confidence", signal.get("confidence", 0.0))
        return result

    except Exception:
        logger.exception("LLM interpretation failed")
        return {
            "market_read": "Structure is unclear from available data.",
            "candle_interpretation": signal.get("candle_read") or "Insufficient data.",
            "vwap_context": "VWAP relationship unknown.",
            "recommendation": {
                "stance": "wait",
                "aggressive": "Avoid forcing an entry without a clear setup.",
                "conservative": "Stand aside until structure improves.",
                "invalidation": "N/A",
            },
            "options_fit": "poor",
            "options_note": "Cannot assess options fit without clean structure.",
            "risk": "Low-confidence read. Default to caution.",
            "confidence": 0.0,
            "mode": "llm_fallback",
        }


# ── Public interface ──────────────────────────────────────────────────────────

async def interpret_market_signal(signal: dict) -> dict:
    result = _rule_based_interpret(signal)
    if result:
        return result
    return await _llm_interpret(signal)