import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
import re
import os
from dotenv import load_dotenv , find_dotenv
# load_dotenv()
load_dotenv(find_dotenv()) 
print(find_dotenv())

ALPHA_VANTAGE_API_KEY=os.getenv("ALPHA_VANTAGE_API_KEY")
ALPHA_VANTAGE_BASE_URL=os.getenv("ALPHA_VANTAGE_BASE_URL")


if not ALPHA_VANTAGE_API_KEY:
    print("Warning: ALPHA_VANTAGE_API_KEY not found in environment variables")
    # ALPHA_VANTAGE_API_KEY = "YOUR_API_KEY_HERE" 


# Common stock ticker mappings for natural language processing
TICKER_MAPPINGS = {
    "tesla": "TSLA",
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "nvidia": "NVDA",
    "palantir": "PLTR",
    "meta": "META",
    "facebook": "META",
    "netflix": "NFLX",
    "spotify": "SPOT",
    "uber": "UBER",
    "airbnb": "ABNB",
    "twitter": "TWTR",
    "x": "TWTR"
}

def identify_ticker(query: str) -> dict:
    """
    Parses the user query and identifies the stock ticker.
    
    Args:
        query (str): User's natural language query about a stock
        
    Returns:
        dict: Contains status, ticker symbol, and company name if found
    """
    query_lower = query.lower()
    
    # First, try to find explicit ticker symbols (3-5 uppercase letters)
    ticker_pattern = r'\b[A-Z]{2,5}\b'
    explicit_tickers = re.findall(ticker_pattern, query)
    
    if explicit_tickers:
        ticker = explicit_tickers[0]
        return {
            "status": "success",
            "ticker": ticker,
            "company": f"Company with ticker {ticker}",
            "confidence": "high"
        }
    
    # Search for company names in our mapping
    for company, ticker in TICKER_MAPPINGS.items():
        if company in query_lower:
            return {
                "status": "success",
                "ticker": ticker,
                "company": company.title(),
                "confidence": "medium"
            }
    
    return {
        "status": "error",
        "error_message": "Could not identify a stock ticker from the query. Please specify a company name or ticker symbol."
    }

def ticker_news(ticker: str) -> dict:
    """
    Retrieves the most recent news about the identified stock.
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: Contains status and news articles if successful
    """
    try:
        url = f"{ALPHA_VANTAGE_BASE_URL}"
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": ticker,
            "apikey": ALPHA_VANTAGE_API_KEY,
            "limit": 5
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if "Error Message" in data or "Note" in data:
            return {
                "status": "error",
                "error_message": f"API error retrieving news for {ticker}. Please check if the ticker is valid."
            }
        
        if "feed" in data and len(data["feed"]) > 0:
            news_items = []
            for item in data["feed"][:3]:  # Get top 3 news items
                news_items.append({
                    "title": item.get("title", "No title"),
                    "summary": item.get("summary", "No summary available")[:200] + "...",
                    "source": item.get("source", "Unknown"),
                    "time_published": item.get("time_published", "Unknown"),
                    "sentiment": item.get("overall_sentiment_label", "Neutral")
                })
            
            return {
                "status": "success",
                "ticker": ticker,
                "news_count": len(news_items),
                "articles": news_items
            }
        else:
            return {
                "status": "error",
                "error_message": f"No recent news found for {ticker}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error fetching news for {ticker}: {str(e)}"
        }

def ticker_price(ticker: str) -> dict:
    """
    Fetches the current price of the stock.
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: Contains status and current price information
    """
    try:
        url = f"{ALPHA_VANTAGE_BASE_URL}"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": ticker,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if "Error Message" in data or "Note" in data:
            return {
                "status": "error",
                "error_message": f"API error retrieving price for {ticker}. Please check if the ticker is valid."
            }
        
        if "Global Quote" in data:
            quote = data["Global Quote"]
            return {
                "status": "success",
                "ticker": ticker,
                "current_price": float(quote.get("05. price", 0)),
                "previous_close": float(quote.get("08. previous close", 0)),
                "change": float(quote.get("09. change", 0)),
                "change_percent": quote.get("10. change percent", "0%"),
                "last_updated": quote.get("07. latest trading day", "Unknown")
            }
        else:
            return {
                "status": "error",
                "error_message": f"No price data found for {ticker}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error fetching price for {ticker}: {str(e)}"
        }

def ticker_price_change(ticker: str, timeframe: str = "1day") -> dict:
    """
    Calculates how the stock's price has changed in a given timeframe.
    
    Args:
        ticker (str): Stock ticker symbol
        timeframe (str): Time period ("1day", "1week", "1month")
        
    Returns:
        dict: Contains status and price change analysis
    """
    try:
        url = f"{ALPHA_VANTAGE_BASE_URL}"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if "Error Message" in data or "Note" in data:
            return {
                "status": "error",
                "error_message": f"API error retrieving price history for {ticker}."
            }
        
        if "Time Series (Daily)" not in data:
            return {
                "status": "error",
                "error_message": f"No historical data found for {ticker}"
            }
        
        time_series = data["Time Series (Daily)"]
        dates = sorted(time_series.keys(), reverse=True)
        
        if len(dates) < 2:
            return {
                "status": "error",
                "error_message": f"Insufficient data to calculate price change for {ticker}"
            }
        
        # Determine comparison period
        if timeframe.lower() in ["today", "1day", "daily"]:
            compare_days = 1
        elif timeframe.lower() in ["week", "1week", "7days"]:
            compare_days = 7
        elif timeframe.lower() in ["month", "1month", "30days"]:
            compare_days = 30
        else:
            compare_days = 1
        
        current_date = dates[0]
        current_price = float(time_series[current_date]["4. close"])
        
        # Find comparison date
        comparison_date = dates[min(compare_days, len(dates) - 1)]
        comparison_price = float(time_series[comparison_date]["4. close"])
        
        price_change = current_price - comparison_price
        percent_change = (price_change / comparison_price) * 100
        
        return {
            "status": "success",
            "ticker": ticker,
            "timeframe": timeframe,
            "current_price": current_price,
            "comparison_price": comparison_price,
            "price_change": round(price_change, 2),
            "percent_change": round(percent_change, 2),
            "current_date": current_date,
            "comparison_date": comparison_date,
            "trend": "up" if price_change > 0 else "down" if price_change < 0 else "flat"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error calculating price change for {ticker}: {str(e)}"
        }

def ticker_analysis(ticker: str) -> dict:
    """
    Analyzes and summarizes the reason behind recent price movements using news and price data.
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: Contains comprehensive analysis combining news and price data
    """
    try:
        # Get price data
        price_data = ticker_price(ticker)
        if price_data["status"] != "success":
            return price_data
        
        # Get price change data
        change_data = ticker_price_change(ticker, "1week")
        if change_data["status"] != "success":
            change_data = ticker_price_change(ticker, "1day")
        
        # Get news data
        news_data = ticker_news(ticker)
        
        # Analyze sentiment from news
        sentiment_analysis = "Mixed"
        if news_data["status"] == "success":
            sentiments = [article.get("sentiment", "Neutral") for article in news_data["articles"]]
            positive_count = sentiments.count("Positive")
            negative_count = sentiments.count("Negative")
            
            if positive_count > negative_count:
                sentiment_analysis = "Positive"
            elif negative_count > positive_count:
                sentiment_analysis = "Negative"
            else:
                sentiment_analysis = "Neutral"
        
        # Generate analysis summary
        analysis_summary = f"""
        Stock Analysis for {ticker}:
        
        Current Price: ${price_data['current_price']:.2f}
        Change: ${price_data['change']:.2f} ({price_data['change_percent']})
        
        """
        
        if change_data["status"] == "success":
            analysis_summary += f"""
        {change_data['timeframe'].title()} Performance:
        Price moved from ${change_data['comparison_price']:.2f} to ${change_data['current_price']:.2f}
        Change: ${change_data['price_change']:.2f} ({change_data['percent_change']:.2f}%)
        Trend: {change_data['trend'].upper()}
        
        """
        
        analysis_summary += f"News Sentiment: {sentiment_analysis}\n"
        
        if news_data["status"] == "success":
            analysis_summary += "\nRecent News Headlines:\n"
            for i, article in enumerate(news_data["articles"][:3], 1):
                analysis_summary += f"{i}. {article['title']} (Sentiment: {article['sentiment']})\n"
        
        return {
            "status": "success",
            "ticker": ticker,
            "analysis": analysis_summary,
            "price_data": price_data,
            "change_data": change_data if change_data["status"] == "success" else None,
            "news_data": news_data if news_data["status"] == "success" else None,
            "overall_sentiment": sentiment_analysis
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error generating analysis for {ticker}: {str(e)}"
        }
#tools testing 
# test=ticker_news("TSLA")
# print(test)