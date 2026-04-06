import asyncio

from valuecell.core.agent import create_wrapped_agent

from .core import TradingAgents

if __name__ == "__main__":
    agent = create_wrapped_agent(TradingAgents)
    asyncio.run(agent.serve())
