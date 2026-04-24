"""
Sage Market Scanner tool -- live implementation.
Queries the real Market Scanner API running on Fedora.
"""
import httpx
from config.settings import settings


async def get_scanner_latest() -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        headers = {}
        if settings.scanner_api_key:
            headers["Authorization"] = f"Bearer {settings.scanner_api_key}"

        response = await client.get(
            f"{settings.scanner_base_url}/scanner/latest",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

    signals = data.get("signals", [])
    if not signals:
        return {"signals": [], "count": 0, "top_signal": None}

    top_signal = max(signals, key=lambda s: s.get("confidence", 0))

    return {
        "signals": signals,
        "count": len(signals),
        "top_signal": top_signal,
    }


async def get_scanner_history(limit: int = 10) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        headers = {}
        if settings.scanner_api_key:
            headers["Authorization"] = f"Bearer {settings.scanner_api_key}"

        response = await client.get(
            f"{settings.scanner_base_url}/scanner/history",
            params={"limit": limit},
            headers=headers,
        )
        response.raise_for_status()
        return response.json()


async def get_scanner_for_symbol(symbol: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        headers = {}
        if settings.scanner_api_key:
            headers["Authorization"] = f"Bearer {settings.scanner_api_key}"

        response = await client.get(
            f"{settings.scanner_base_url}/scanner/latest/{symbol.upper()}",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

    if data.get("status") == "no_data":
        return {"error": f"No data available for {symbol}"}

    return data