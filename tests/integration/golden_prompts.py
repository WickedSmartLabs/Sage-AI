"""
Golden prompt set -- Phase 4 eval dataset.

These are the test cases that prove Sage works.
Run against the live API to catch regressions.

Usage:
    python tests/integration/run_evals.py

Add more prompts as you build new capabilities.
Each entry is a contract: input -> expected routing -> expected output shape.
"""
import asyncio
import json
import time
from datetime import datetime

# Base URL for the running Sage API
SAGE_URL = "http://localhost:8000/api/v1"

GOLDEN_PROMPTS = [
    # ── Scanner tool ──────────────────────────────────────────────────────────
    {
        "id": "scanner_latest_001",
        "phase": 3,
        "input": "Sage, what's the market doing?",
        "expected_tool": "scanner_latest",
        "must_contain": ["sir"],
        "must_not_contain": ["I don't know", "cannot access", "I'm unable"],
        "notes": "Flagship interaction. Must route to scanner and respond in character.",
    },
    {
        "id": "scanner_latest_002",
        "phase": 3,
        "input": "What does the scanner show right now?",
        "expected_tool": "scanner_latest",
        "must_contain": ["sir"],
        "must_not_contain": [],
        "notes": "Alternative phrasing -- should still route to scanner_latest.",
    },
    {
        "id": "scanner_history_001",
        "phase": 3,
        "input": "Sage, review the last 10 scanner signals.",
        "expected_tool": "scanner_history",
        "must_contain": ["sir"],
        "must_not_contain": [],
        "notes": "History query. Must route to scanner_history.",
    },
    {
        "id": "scanner_history_002",
        "phase": 3,
        "input": "How have recent scanner signals been performing?",
        "expected_tool": "scanner_history",
        "must_contain": ["sir"],
        "must_not_contain": [],
        "notes": "Implicit history query -- should infer scanner_history.",
    },

    # ── No tool needed ────────────────────────────────────────────────────────
    {
        "id": "no_tool_001",
        "phase": 1,
        "input": "Sage, are you there?",
        "expected_tool": None,
        "must_contain": ["sir"],
        "must_not_contain": [],
        "notes": "Simple greeting. No tool should fire.",
    },
    {
        "id": "no_tool_002",
        "phase": 1,
        "input": "What are your capabilities?",
        "expected_tool": None,
        "must_contain": ["sir"],
        "must_not_contain": [],
        "notes": "Capability question. Pure assistant response.",
    },
    {
        "id": "no_tool_003",
        "phase": 1,
        "input": "Sage, remind me what you can help with.",
        "expected_tool": None,
        "must_contain": ["sir"],
        "must_not_contain": [],
        "notes": "Meta question about Sage's role.",
    },

    # ── Character / tone checks ───────────────────────────────────────────────
    {
        "id": "tone_001",
        "phase": 1,
        "input": "Good morning, Sage.",
        "expected_tool": None,
        "must_contain": ["sir"],
        "must_not_contain": ["Hello!", "Hi there", "Sure!", "Absolutely!"],
        "notes": "Tone check. Sage should not sound like a generic chatbot.",
    },
]


async def run_eval(prompt: dict, session_id: str = "eval") -> dict:
    """Run a single golden prompt against the live API."""
    import httpx

    start = time.monotonic()
    result = {
        "id": prompt["id"],
        "input": prompt["input"],
        "expected_tool": prompt["expected_tool"],
        "passed": False,
        "failures": [],
        "response": None,
        "tool_used": None,
        "latency_ms": None,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{SAGE_URL}/chat",
                json={"message": prompt["input"], "session_id": session_id},
            )
            resp.raise_for_status()
            data = resp.json()

        result["response"] = data.get("response", "")
        result["tool_used"] = data.get("tool_used")
        result["latency_ms"] = round((time.monotonic() - start) * 1000)

        # Check tool routing
        if prompt["expected_tool"] is not None:
            if result["tool_used"] != prompt["expected_tool"]:
                result["failures"].append(
                    f"Expected tool '{prompt['expected_tool']}', "
                    f"got '{result['tool_used']}'"
                )

        if prompt["expected_tool"] is None and result["tool_used"] is not None:
            result["failures"].append(
                f"Expected no tool, but '{result['tool_used']}' was called"
            )

        # Check response content
        for phrase in prompt.get("must_contain", []):
            if phrase.lower() not in result["response"].lower():
                result["failures"].append(f"Response missing required phrase: '{phrase}'")

        for phrase in prompt.get("must_not_contain", []):
            if phrase.lower() in result["response"].lower():
                result["failures"].append(f"Response contains forbidden phrase: '{phrase}'")

        result["passed"] = len(result["failures"]) == 0

    except Exception as e:
        result["failures"].append(f"Request failed: {e}")

    return result


async def main():
    print(f"\nSage Golden Prompt Eval -- {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print(f"Running {len(GOLDEN_PROMPTS)} prompts against {SAGE_URL}\n")
    print("-" * 60)

    results = []
    for i, prompt in enumerate(GOLDEN_PROMPTS):
        # Use unique session per prompt to avoid cross-contamination
        session_id = f"eval_{prompt['id']}"
        result = await run_eval(prompt, session_id=session_id)
        results.append(result)

        status = "PASS" if result["passed"] else "FAIL"
        latency = f"{result['latency_ms']}ms" if result["latency_ms"] else "err"
        tool = result["tool_used"] or "none"

        print(f"[{status}] {prompt['id']} | tool={tool} | {latency}")
        if not result["passed"]:
            for f in result["failures"]:
                print(f"       -> {f}")
        if result["response"]:
            preview = result["response"][:80].replace("\n", " ")
            print(f"       Sage: \"{preview}...\"")
        print()

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print("-" * 60)
    print(f"Results: {passed}/{total} passed")

    # Write results to logs/
    log_path = f"logs/eval_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jsonl"
    with open(log_path, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"Full results written to {log_path}\n")


if __name__ == "__main__":
    asyncio.run(main())
