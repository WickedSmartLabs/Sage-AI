"""
Sage Tool Router -- pure execution layer.
Receives a resolved tool name and args. Does not make decisions.
"""
import inspect
import time
from sage.tools.registry import TOOL_REGISTRY
from sage.utils.logger import log_tool_call


class ToolRouter:
    async def route(self, tool_name: str, args: dict | None = None) -> dict:
        args = args or {}
        tool_fn = TOOL_REGISTRY.get(tool_name)

        if not tool_fn:
            return {
                "success": False,
                "tool": tool_name,
                "data": None,
                "error": f"Tool '{tool_name}' not found in registry",
            }

        start = time.monotonic()

        try:
            if inspect.iscoroutinefunction(tool_fn):
                result = await tool_fn(**args)
            else:
                result = tool_fn(**args)

            latency_ms = round((time.monotonic() - start) * 1000)
            log_tool_call(tool_name, args, str(result), True, latency_ms)

            return {
                "success": True,
                "tool": tool_name,
                "data": result,
                "error": None,
            }

        except TypeError as e:
            latency_ms = round((time.monotonic() - start) * 1000)
            error = f"Invalid arguments for tool '{tool_name}': {e}"
            log_tool_call(tool_name, args, error, False, latency_ms)
            return {"success": False, "tool": tool_name, "data": None, "error": error}

        except Exception as e:
            latency_ms = round((time.monotonic() - start) * 1000)
            log_tool_call(tool_name, args, str(e), False, latency_ms)
            return {"success": False, "tool": tool_name, "data": None, "error": str(e)}
