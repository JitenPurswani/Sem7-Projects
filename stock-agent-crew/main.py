import os
from dotenv import load_dotenv
import yfinance as yf
from crewai import Agent, Task, Crew, Process, LLM # <-- Import LLM class
from crewai.tools import tool 
from duckduckgo_search import DDGS 
import json
from typing import List, Dict, Any

# --- 1. Load Environment Variables and LLM Configuration ---
load_dotenv()
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY") # Ensure this is set in .env
# We don't need to set TAVILY_API_KEY anymore since we're using DDGS

# --- Initialize the Gemini LLM ---
# This step forces Crew.ai/LiteLLM to use Gemini and its key for all agents.
try:
    gemini_llm = LLM(
        model='gemini/gemini-2.5-flash', # Use the LiteLLM format: provider/model-name
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.1 # Lower temp for more consistent analysis
    )
except Exception as e:
    print(f"🔴 FATAL ERROR: Failed to initialize Gemini LLM. Ensure GEMINI_API_KEY is correct and valid. Error: {e}")
    exit()

# --- Define Custom Tools ---
# (The custom tools are stable and do not need changes)

# Tool 1: Custom Stock Data Tool (YFinance)
@tool("YFinance Stock Data Tool")
def get_stock_data(ticker: str) -> str:
    """
    Fetches the latest real-time stock price, P/E ratio, and the last 5 days of closing 
    prices for a given stock ticker. This information is crucial for technical analysis.
    
    Args:
        ticker (str): The stock ticker symbol (e.g., 'NVDA', 'TSLA').

    Returns:
        str: A JSON string containing the current price, P/E ratio, and a list of 
             recent closing prices for trend analysis.
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Get current price data
        latest_info = stock.info
        current_price = latest_info.get('currentPrice', 'N/A')
        pe_ratio = latest_info.get('trailingPE', 'N/A')
        
        # Get recent history for trend analysis
        hist = stock.history(period='5d')
        price_trend = hist['Close'].tolist()

        data = {
            "ticker": ticker,
            "current_price": current_price,
            "P/E_ratio": pe_ratio,
            "last_5_day_close_prices": price_trend,
        }
        return json.dumps(data)
    except Exception as e:
        return f"Error fetching stock data for {ticker}: {e}"


# Tool 2: DuckDuckGo Search Tool (Free News/Context)
@tool("DuckDuckGo News Search")
def custom_ddg_search(query: str) -> str:
    """
    Performs a web search using DuckDuckGo to find real-time news articles, press releases, 
    and general market sentiment for a specific stock query. This is used for sentiment analysis.
    
    Args:
        query (str): The search string for news (e.g., 'NVDA stock news today').

    Returns:
        str: A formatted string of the top 5 relevant news results (Title, Snippet, Source).
    """
    with DDGS() as ddgs:
        # Searches for news and returns a maximum of 5 highly relevant results
        results = ddgs.text(f"{query} stock news today", max_results=5)
    
    formatted_results = []
    for i, r in enumerate(results):
        formatted_results.append(f"Result {i+1}:\nTitle: {r.get('title')}\nSnippet: {r.get('snippet')}\nSource: {r.get('href')}\n---")
    
    return "\n".join(formatted_results)


# --- 2. Define the Specialized AI Agents (Assigning the Gemini LLM) ---

STOCK_TICKER = "NVDA" 
financial_tool = get_stock_data
tavily_tool = custom_ddg_search

# Agent 1: Real-Time Data and Technicals
data_analyst = Agent(
    role='Real-Time Stock Data Analyst',
    goal=f'Fetch and analyze the latest stock data for {STOCK_TICKER} using the YFinance Stock Data Tool.',
    backstory=("You are an expert financial data scientist..."),
    tools=[financial_tool],
    verbose=True,
    llm=gemini_llm # <-- Explicitly set the Gemini LLM
)

# Agent 2: Market Context and News Sentiment
news_analyst = Agent(
    role='Market News and Sentiment Analyst',
    goal='Use the DuckDuckGo News Search tool to find and analyze the latest sentiment for the stock.',
    backstory=("You are a seasoned Wall Street journalist..."),
    tools=[tavily_tool],
    verbose=True,
    llm=gemini_llm # <-- Explicitly set the Gemini LLM
)

# Agent 3: Final Synthesis and Recommendation
investment_strategist = Agent(
    role='Senior Investment Strategist',
    goal='Synthesize data from the analysts to provide a final, actionable investment recommendation.',
    backstory=("You are a hedge fund portfolio manager..."),
    verbose=True,
    llm=gemini_llm # <-- Explicitly set the Gemini LLM
)

# --- 3. Define Tasks for the Crew ---
# (Tasks remain the same)
task_data = Task(
    description=f"Use the YFinance Stock Data Tool to fetch all metrics for {STOCK_TICKER}. Summarize the current price, P/E ratio, and analyze the last 5-day price trend.",
    agent=data_analyst,
    expected_output=f"A short summary of {STOCK_TICKER}'s current technical status and recent price movement."
)

task_news = Task(
    description=f"Use the DuckDuckGo News Search tool to find and analyze the latest 24-hour news headlines, press releases, and general market sentiment for {STOCK_TICKER}. Provide a sentiment score (0-10) and a brief summary of the key bullish and bearish news drivers.",
    agent=news_analyst,
    expected_output=f"A sentiment analysis report for {STOCK_TICKER} based on recent news, including a clear sentiment score and key drivers."
)

task_recommendation = Task(
    description=(
        f"Using the technical and news analysis provided by the other agents, create a final, comprehensive "
        f"**Investment Recommendation Report for {STOCK_TICKER}**."
        f"The report MUST include a clear BUY/SELL/HOLD decision and a detailed justification "
        f"based on both the technical and news data."
    ),
    agent=investment_strategist,
    context=[task_data, task_news],
    expected_output="A final markdown-formatted report with a clear investment decision (BUY/SELL/HOLD) and detailed justification."
)


# --- 4. Create and Run the Crew ---

stock_analysis_crew = Crew(
    agents=[data_analyst, news_analyst, investment_strategist],
    tasks=[task_data, task_news, task_recommendation],
    process=Process.sequential, 
    verbose=True # Fix applied in last step: using boolean True
)

print(f"--- Starting Crew for {STOCK_TICKER} Analysis ---")
result = stock_analysis_crew.kickoff()
print("--------------------------------------------------")
print("✅ FINAL INVESTMENT RECOMMENDATION REPORT:")
print("--------------------------------------------------")
print(result)