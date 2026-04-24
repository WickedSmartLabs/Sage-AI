"""
Sage core assistant logic.
Owns intent classification. Delegates execution to ToolRouter.
"""
import json
import time
import logging
from openai import AsyncOpenAI
from config.settings import settings
from config.prompts import SAGE_SYSTEM_PROMPT
from sage.tools.router import ToolRouter
from sage.tools.registry import get_tool_schemas
from sage.utils.logger import log_interaction

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=settings.openai_api_key)
router = ToolRouter()


async def _classify_intent(user_message: str) -> dict | None:
    schemas = get_tool_schemas()
    if not schemas:
        return None

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a tool router for Sage, a market intelligence assistant. "
                    "You have access to a Market Scanner that provides real-time market data. "
                    "Call scanner_latest when the user asks about: the market, current conditions, "
                    "what is happening, price action, trend, signals, BTC, crypto, stocks, "
                    "or anything related to current market state. "
                    "Call scanner_symbol when the user asks about a specific asset, ticker, or symbol "
                    "such as SPY, AAPL, ETH, SOL, NVDA, or MSFT. "
                    "Call scanner_history when the user asks about past signals, recent history, "
                    "or how the scanner has been performing. "
                    "If the request is clearly unrelated to markets or systems, do not call any function."
                ),
            },
            {"role": "user", "content": user_message},
        ],
        tools=schemas,
        tool_choice="auto",
        max_tokens=128,
    )

    message = response.choices[0].message
    if not message.tool_calls:
        return None

    call = message.tool_calls[0]
    try:
        args = json.loads(call.function.arguments or "{}")
    except json.JSONDecodeError:
        args = {}

    return {
        "tool_name": call.function.name,
        "args": args,
        "raw_tool_call_id": getattr(call, "id", None),
    }


async def chat(
    user_message: str,
    conversation_history: list[dict],
) -> dict:
    start = time.monotonic()

    messages = [
        {"role": "system", "content": SAGE_SYSTEM_PROMPT},
        *conversation_history,
        {"role": "user", "content": user_message},
    ]

    tool_result = None
    tool_name = None
    tool_success = None

    try:
        intent = await _classify_intent(user_message)
    except Exception:
        logger.exception("Intent classification failed")
        intent = None

    if intent:
        tool_result = await router.route(intent["tool_name"], intent.get("args", {}))
        tool_name = tool_result["tool"]
        tool_success = tool_result["success"]

    if tool_result:
        if tool_success:
            tool_data = tool_result["data"]

            if tool_name in ("scanner_latest", "scanner_symbol"):
                try:
                    from sage.tools.scanner_adapter import normalize_scanner_payload
                    from sage.core.market_interpreter import interpret_market_signal

                    top_signal = tool_data.get("top_signal") or tool_data
                    all_signals = tool_data.get("signals", [])

                    normalized = normalize_scanner_payload(top_signal) if top_signal else {}
                    interpretation = await interpret_market_signal(normalized) if normalized else {}

                    tool_payload = json.dumps(
                        {
                            "top_signal": normalized,
                            "interpretation": interpretation,
                            "all_signals": [
                                {
                                    "symbol": s.get("symbol"),
                                    "timeframe": s.get("timeframe"),
                                    "bias": s.get("bias"),
                                    "confidence": s.get("confidence"),
                                    "status_label": s.get("status_label"),
                                    "price": s.get("price"),
                                }
                                for s in all_signals
                            ],
                        },
                        indent=2,
                        default=str,
                    )

                    messages.append({
                        "role": "system",
                        "content": (
                            f"Market scanner data for '{tool_name}':\n"
                            f"{tool_payload}\n\n"
                            "The top_signal is the highest confidence reading. "
                            "all_signals gives you the full market picture across assets. "
                            "Use both to give a complete market read in Sage voice. "
                            "Lead with the most interesting signal, then give brief context on the others if relevant. "
                            "Do not list every symbol mechanically. Speak like an operator giving a situation report."
                        ),
                    })

                except Exception:
                    logger.exception("Scanner interpretation failed")
                    raise

            else:
                tool_payload = json.dumps(tool_data, indent=2, default=str)
                messages.append({
                    "role": "system",
                    "content": (
                        f"Tool result for '{tool_name}':\n{tool_payload}\n\n"
                        "Use this as the primary source for your answer. "
                        "Prioritize it over general model knowledge. "
                        "Do not mention the tool unless the user asks."
                    ),
                })

        else:
            messages.append({
                "role": "system",
                "content": (
                    f"Tool '{tool_name}' failed with error: {tool_result['error']}\n"
                    "Respond gracefully, in character. Do not invent tool results."
                ),
            })

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        temperature=0.7,
        max_tokens=512,
    )

    assistant_message = response.choices[0].message.content or ""
    latency_ms = round((time.monotonic() - start) * 1000)

    log_interaction(
        user_message=user_message,
        tool_name=tool_name,
        tool_success=tool_success,
        assistant_response=assistant_message,
        latency_ms=latency_ms,
    )

    return {
        "response": assistant_message,
        "history": conversation_history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message},
        ],
        "tool_used": tool_name,
        "latency_ms": latency_ms,
    }