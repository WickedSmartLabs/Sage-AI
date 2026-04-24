"""
Unit tests -- scanner tool adapter.
Mocks the HTTP client so tests run without a live scanner.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sage.tools.scanner import get_scanner_latest, get_scanner_history, _format_signal, _format_history


MOCK_SIGNAL = {
    "signal": "bearish_continuation",
    "direction": "short",
    "confidence": "moderate",
    "structure": "lower_highs",
    "timestamp": "2025-01-01T12:00:00Z",
    "notes": "Wait for confirmation.",
}

MOCK_HISTORY = [
    {"timestamp": "2025-01-01T10:00:00Z", "direction": "short", "confidence": "high"},
    {"timestamp": "2025-01-01T08:00:00Z", "direction": "long", "confidence": "low"},
]


# ── Format helpers (pure functions, no mocking needed) ────────────────────────

def test_format_signal_contains_key_fields():
    result = _format_signal(MOCK_SIGNAL)
    assert "bearish_continuation" in result
    assert "moderate" in result
    assert "lower_highs" in result
    assert "Wait for confirmation" in result


def test_format_signal_handles_missing_fields():
    result = _format_signal({})
    assert "N/A" in result
    assert "Signal" in result


def test_format_history_formats_list():
    result = _format_history(MOCK_HISTORY)
    assert "short" in result
    assert "long" in result
    assert "high" in result


def test_format_history_handles_dict_wrapper():
    result = _format_history({"signals": MOCK_HISTORY})
    assert "short" in result


def test_format_history_empty():
    result = _format_history([])
    assert "No recent signals" in result


# ── HTTP adapter tests (mock httpx) ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_scanner_latest_success():
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_SIGNAL
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("sage.tools.scanner.httpx.AsyncClient", return_value=mock_client):
        result = await get_scanner_latest()

    assert "bearish_continuation" in result
    assert "moderate" in result


@pytest.mark.asyncio
async def test_get_scanner_latest_http_error():
    import httpx

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=httpx.HTTPError("connection refused"))

    with patch("sage.tools.scanner.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(Exception):
            await get_scanner_latest()


@pytest.mark.asyncio
async def test_get_scanner_history_default_limit():
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_HISTORY
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("sage.tools.scanner.httpx.AsyncClient", return_value=mock_client):
        result = await get_scanner_history()

    assert "short" in result
    assert "long" in result
    # Verify default limit was passed
    call_kwargs = mock_client.get.call_args
    assert call_kwargs.kwargs["params"]["limit"] == 10
