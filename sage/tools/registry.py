"""
Tool registry -- maps tool names to handler functions and OpenAI schemas.
Add new tools here. Router picks them up automatically.
"""
from sage.tools.scanner import (
    get_scanner_latest,
    get_scanner_history,
    get_scanner_for_symbol,
)


TOOL_REGISTRY: dict = {
    "scanner_latest": get_scanner_latest,
    "scanner_history": get_scanner_history,
    "scanner_symbol": get_scanner_for_symbol,
    # Phase 7: "docker_status": get_docker_status,
    # Phase 10: "ha_query": query_home_assistant,
}


def get_tool_schemas() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": "scanner_latest",
                "description": (
                    "Fetch the latest signal from the Market Scanner. "
                    "Use when the user asks about the market, current signals, "
                    "or what the scanner shows."
                ),
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "scanner_history",
                "description": (
                    "Fetch recent historical signals from the Market Scanner. "
                    "Use when the user asks about past signals, recent outcomes, "
                    "or scanner history."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of recent signals to retrieve (default 10).",
                        }
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "scanner_symbol",
                "description": (
                    "Get the latest scanner reading for a specific symbol. "
                    "Use when the user asks about a specific asset such as BTC, ETH, SPY, AAPL, NVDA, SOL, or MSFT."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The symbol to query, e.g. BTC/USD, SPY, AAPL.",
                        }
                    },
                    "required": ["symbol"],
                },
            },
        },
    ]