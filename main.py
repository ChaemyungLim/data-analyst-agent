"""
LangGraph Agent for Causal Analysis using DoWhy and TabPFN
"""

from causal_agent import CausalAnalysisAgent
from database.connection import DatabaseConnection
import asyncio


async def main():
    """Main entry point for the causal analysis agent"""
    db_config = {
        'host': 'localhost',
        'database': 'causal_db',
        'user': 'postgres',
        'password': 'password',
        'port': 5432
    }
    
    agent = CausalAnalysisAgent(db_config)
    
    # Example usage
    question = "What is the causal effect of education on income?"
    result = await agent.answer_causal_question(question)
    print(f"Answer: {result}")


if __name__ == "__main__":
    asyncio.run(main())