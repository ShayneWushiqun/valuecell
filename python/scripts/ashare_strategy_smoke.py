import json
import time
import urllib.parse
import urllib.request


BASE_URL = "http://localhost:8000/api/v1"


def post(path: str, payload: dict) -> dict:
    request = urllib.request.Request(
        BASE_URL + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.loads(response.read().decode())


def get(path: str) -> dict:
    with urllib.request.urlopen(BASE_URL + path, timeout=180) as response:
        return json.loads(response.read().decode())


def stop_strategy(strategy_id: str) -> dict:
    request = urllib.request.Request(
        BASE_URL + "/strategies/stop?id=" + urllib.parse.quote(strategy_id),
        data=b"",
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.loads(response.read().decode())


def main() -> None:
    payload = {
        "llm_model_config": {
            "provider": "openai-compatible",
            "model_id": "doubao-seed-2.0-pro",
            "api_key": "c94841e2-730d-41e0-b6a5-b1dc6ad5b0e2",
        },
        "exchange_config": {
            "trading_mode": "virtual",
            "exchange_id": "ashare",
            "market_type": "spot",
            "fee_bps": 10.0,
        },
        "trading_config": {
            "strategy_name": f"AShare-Smoke-Test-{int(time.time())}",
            "strategy_type": "PromptBasedStrategy",
            "initial_capital": 100000,
            "initial_free_cash": 100000,
            "max_leverage": 1,
            "symbols": ["000001.SZ"],
            "decide_interval": 3,
            "prompt_text": "你是A股模拟交易策略。只交易输入股票，保守决策；若信号不明确则 noop；遵守A股不做空和整手交易约束。",
        },
    }

    created = post("/strategies/create", payload)
    print("CREATE", created)
    strategy_id = (created.get("data") or {}).get("strategy_id")
    if not strategy_id:
        raise SystemExit("Strategy creation failed")

    summary_result = None
    detail_result = None
    for _ in range(8):
        time.sleep(3)
        summary_result = get(
            "/strategies/portfolio_summary?id="
            + urllib.parse.quote(str(strategy_id))
        )
        detail_result = get(
            "/strategies/detail?id=" + urllib.parse.quote(str(strategy_id))
        )
        print("SUMMARY", summary_result)
        print("DETAIL_COUNT", len(detail_result.get("data") or []))
        if summary_result.get("code") == 0 and (detail_result.get("data") or []):
            break

    stopped = stop_strategy(str(strategy_id))
    print("STOP", stopped)


if __name__ == "__main__":
    main()
