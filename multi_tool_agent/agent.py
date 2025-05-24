from google.adk.agents import Agent
from .tools import identify_ticker,ticker_analysis,ticker_news,ticker_price,ticker_price_change

root_agent = Agent(
    name="multi_tool_agent",
    model="gemini-2.0-flash",
    description="Multi-agent system for comprehensive stock analysis including ticker identification, news, pricing, and trend analysis.",
    instruction="""I am a comprehensive stock analysis assistant that can help you understand stock performance and market movements. 
    
    I can:
    - Identify stock tickers from company names or queries
    - Get current stock prices and recent changes
    - Fetch the latest news about stocks
    - Analyze price movements and correlate them with news sentiment
    
    Simply ask me about any stock using natural language like:
    - "Why did Tesla stock drop today?"
    - "What's happening with Palantir stock recently?"
    - "How has Nvidia stock changed in the last 7 days?"
    
    I'll provide you with comprehensive analysis combining price data, news, and market sentiment.""",
    tools=[identify_ticker, ticker_news, ticker_price, ticker_price_change, ticker_analysis]
)

