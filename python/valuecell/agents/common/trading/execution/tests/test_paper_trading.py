import pytest

from valuecell.agents.common.trading.constants import (
    FEATURE_GROUP_BY_KEY,
    FEATURE_GROUP_BY_MARKET_SNAPSHOT,
)
from valuecell.agents.common.trading.execution.paper_trading import (
    PaperExecutionGateway,
)
from valuecell.agents.common.trading.models import (
    FeatureVector,
    InstrumentRef,
    PriceMode,
    TradeDecisionAction,
    TradeInstruction,
    TradeSide,
    TxStatus,
)


def _build_instruction(
    symbol: str,
    quantity: float,
    action: TradeDecisionAction = TradeDecisionAction.OPEN_LONG,
) -> TradeInstruction:
    side = TradeSide.BUY if action == TradeDecisionAction.OPEN_LONG else TradeSide.SELL
    return TradeInstruction(
        instruction_id=f"inst-{symbol}",
        compose_id="compose-1",
        instrument=InstrumentRef(symbol=symbol, exchange_id="paper"),
        action=action,
        side=side,
        quantity=quantity,
        price_mode=PriceMode.MARKET,
    )


def _build_feature(symbol: str, close_price: float) -> FeatureVector:
    return FeatureVector(
        ts=1,
        instrument=InstrumentRef(symbol=symbol, exchange_id="ashare"),
        values={"price.close": close_price, "price.last": close_price},
        meta={FEATURE_GROUP_BY_KEY: FEATURE_GROUP_BY_MARKET_SNAPSHOT},
    )


@pytest.mark.asyncio
async def test_paper_trading_rounds_ashare_quantity_to_lot() -> None:
    gateway = PaperExecutionGateway()
    instruction = _build_instruction("SZSE:000001", 250)
    feature = _build_feature("SZSE:000001", 11.0)

    results = await gateway.execute([instruction], [feature])

    assert results[0].status == TxStatus.FILLED
    assert results[0].filled_qty == 200.0


@pytest.mark.asyncio
async def test_paper_trading_rejects_ashare_short() -> None:
    gateway = PaperExecutionGateway()
    instruction = _build_instruction(
        "SZSE:000001",
        200,
        action=TradeDecisionAction.OPEN_SHORT,
    )
    feature = _build_feature("SZSE:000001", 11.0)

    results = await gateway.execute([instruction], [feature])

    assert results[0].status == TxStatus.REJECTED
    assert "short" in (results[0].reason or "").lower()
