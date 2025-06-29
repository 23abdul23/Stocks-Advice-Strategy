from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

import requests, random, json
import finnhub

import yfinance as yf
import numpy as np
import pandas as pd
import pandas_ta as ta

from classes import *
from stocks import *
from macro import *

load_dotenv()
NIFTY50 = list(NIFTY50)
NASDAQ = list(NASDAQ)

testo = AppState(
    user_query= """Need advice on these particular stocks of Amazon, Netflix and NVIDIA
    What is currently going on in these comapnies?
    """,
    stocks=["AAPL", "NVDA"]
    )

test2 = AppState(
    user_query= "I'm 32, married with 2 kids, earning ₹1.2L/month as a software engineer. My side income is ₹20K/month. I've been investing for 4 years, mostly in mutual funds. I'm planning for early retirement by 50, prefer moderate risk, and want a proper investing strategy.",
    portfolio= """
    Investor Profile Summary

    Personal Information:

    Age: 32
    Job Type: Private
    Job Role: Software Engineer
    Marital Status: Married
    Number of Children: 2
    Years of Investing Experience: 4
    Planned Retirement Age: 50
    Financial Situation:

    Monthly Income: ₹120,000.00
    Side Income: ₹20,000.00
    Total Monthly Income: ₹140,000.00
    Investment Objectives:

    Investment Goal: Early Retirement
    Investment Duration: Long Term
    Risk Preference (0-1 scale): 0.5 (Moderate Risk)
    Summary:

    The investor is a 32-year-old software engineer with a moderate risk preference, aiming for early retirement at 50. With a total monthly income of ₹140,000.00, they have a stable financial foundation. Their investment experience is 4 years, which is a good starting point for long-term investing.

    Financial Outlook:

    Based on the provided information, the investor's financial outlook appears promising. With a stable income and a moderate risk preference, they can potentially achieve their investment goals. However, to accelerate their early retirement plan, they may need to consider increasing their savings rate, investing in tax-efficient instruments, and optimizing their investment portfolio.

    Retirement Strategy:

    To achieve early retirement at 50, the investor should focus on the following strategies:

    Maximize Savings: Increase their savings rate to at least 30-40% of their total monthly income.
    Invest in Tax-Efficient Instruments: Utilize tax-saving instruments like Public Provident Fund (PPF), National Pension System (NPS), or tax-efficient mutual funds to minimize tax liabilities.
    Optimize Investment Portfolio: Allocate their investments across a mix of low-risk instruments (e.g., fixed deposits, bonds) and moderate-risk instruments (e.g., equity mutual funds, stocks).
    Consider Alternative Income Streams: Explore alternative income streams, such as real estate or peer-to-peer lending, to diversify their income sources.
    Risk Assessment:

    The investor's risk preference is moderate (0.5 on a 0-1 scale), indicating a willingness to take calculated risks to achieve their investment goals. However, to mitigate potential risks, they should:

    Diversify Investments: Spread their investments across various asset classes to minimize exposure to any one particular market or sector.
    Regularly Review and Adjust: Periodically review their investment portfolio and adjust it as needed to ensure it remains aligned with their investment objectives and risk tolerance.
    Consider Professional Advice: Consult with a financial advisor to get personalized investment advice and guidance.
    By following these strategies and regularly reviewing their progress, the investor can increase their chances of achieving their early retirement goal.
    """,
    stocks= random.choices(NASDAQ, k = 3)
    )


test = test2

MODEL = "llama-3.1-8b-instant"

llm = ChatGroq(
    temperature=0,
    model_name=MODEL,
    api_key=os.environ.get("GROQ_API_KEY"),
)
FIN_CLIENT = finnhub.Client(api_key=os.environ.get("FINNHUB_API"))



#Node adivce or strategy extracter
def usage_extractor(state: UsageClassfier) -> UsageClassfier:
    print('\n',"Determining whether the user wants advice, strategy, or neither.\n")

    prompt = """
    Classify the user's query into one of the following intents and also reterieve the symbols of any stocks mentioned in the query as a list else the list is empty:

    1. "advice" — if the user is asking:
       - whether to buy/sell/hold a stock
       - about the future of a specific company
       - for stock recommendations
       - about price movements

    2. "strategy" — if the user is asking:
       - direct mention of strategy or roadmap
       - how to start investing
       - about investment plans, timeframes, or long-term goals
       - about portfolio structuring, risk allocation, or retirement planning

    3. "invalid" — if the query is unrelated to investing or not understandable

    Return fields `usage` with value: "advice", "strategy", or "invalid" and `stocks` as a list with  STOCKS SYMBOLS like 'TATASTEEL' for Tata Steel or Tata, as it's elements.
    """

    usage_llm = llm.with_structured_output(UsageClassfier)
    extraction = usage_llm.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=state.user_query.strip())
    ])

    new_state = AppState()
    print("Extracted usage:", extraction.usage, '\n')
    print("Stocks:", extraction.stocks, '\n')
    state.usage = extraction.usage
    state.stocks = extraction.stocks
    return state

#Node Portfolio Builder from the user Input
def portfolio_builder(state: UsageClassfier) -> UsageClassfier:
    print('\n',"Building the portfolio from user query\n")

    prompt = f"""
    Extract the following portfolio fields from the user's query.

    If a field is missing:
    - For string fields, set value to "" (empty string)
    - For int/float fields, set value to null / None

    Fields:
    - age (int): User's age, or infer average from phrases like "young", "middle-aged", "retired" or take a guess, from {state.user_query}. Else 30.
    - job_type (str): Classify as "private", "government", "semi private", "non profit", or "business". Else "private".
    - job (str): Job title or "Corporate Job".
    - monthly_income (float): Monthly primary income. If not stated, Find the average monthly salary of a decent corporate working individual.
    - side_income (float): Side income. Else 0
    - investment_goal (str): E.g., "retirement", "wealth building", etc. Else "wealth building".
    - investment_duration (str): E.g., "short term","12 years", "long term", etc. Else 10.
    - risk_preference (float): From 0 to 1. Estimate from phrases like:
        - "risk-averse", "low risk" → ~0.2
        - "moderate" → ~0.5
        - "aggressive", "high risk" → ~0.8+
        Else 0.5.
    - investing_years (int): Years of experience investing, or 0.
    - retirement_age (int): Desired retirement age if mentioned, or Appropriate age for retirement ->55.
    - martial_status (str): "married", "single", "bachelor", etc. Else "single".
    - children (int): Number of children, or 0.
    - stocks (list): Add STOCKS SYMBOLS like 'TATASTEEL' for Tata Steel or Tata, if any interested stocks mentioned by user to existing stocks list.
    
    Return only structured output with these exact fields.
    """

    # Change structured model to AppState (not UsageClassfier) to receive all fields
    usage_llm = llm.with_structured_output(UsageClassfier)
    
    extraction = usage_llm.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=state.user_query)
    ])

    # Fill in fields explicitly into state
    state.age = extraction.age
    state.job_type = extraction.job_type or ""
    state.job = extraction.job or ""
    state.monthly_income = extraction.monthly_income
    state.side_income = extraction.side_income
    state.investment_goal = extraction.investment_goal or ""
    state.investment_duration = extraction.investment_duration or ""
    state.risk_preference = extraction.risk_preference
    state.investing_years = extraction.investing_years
    state.retirement_age = extraction.retirement_age
    state.martial_status = extraction.martial_status or ""
    state.children = extraction.children
    state.stocks = extraction.stocks or []

    #print(state)
    return state


#Node Portfolio Builder from the user Input
def portfolio_summariser(state: UsageClassfier) -> AppState:
    print('\n',"Summarizing the overall portfolio from user inputs\n")

    prompt = f"""Analyze the following investor profile and provide a summary including the finalncial outlook, retirement strategy, risk assessment:

    Personal Information:
    - Age: {state.age}
    - Job Type: {state.job_type}
    - Job Role: {state.job}
    - Marital Status: {state.martial_status}
    - Number of Children: {state.children or 0}
    - Years of Investing Experience: {state.investing_years or 0}
    - Planned Retirement Age: {state.retirement_age or 55}

    Financial Situation:
    - Monthly Income: ₹{(state.monthly_income or 0.0):.2f}
    - Side Income: ₹{(state.side_income or 0.0):.2f}
    - Total Monthly Income: ₹{((state.monthly_income or 0.0) + (state.side_income or 0.0)):.2f}
    Investment Objectives:
    - Investment Goal: {state.investment_goal}
    - Investment Duration: {state.investment_duration}
    - Risk Preference (0–1 scale): {state.risk_preference}
    """

    response = llm.invoke([HumanMessage(prompt)])

    new_state = AppState()
    new_state["usage"] = state.usage
    new_state["user_query"] = state.user_query
    new_state['portfolio'] = response.content
    new_state['stocks'] = state.stocks

    #print(new_state['portfolio'])
    return new_state


def usage_check(state: AppState):
    if (state['usage'] == 'advice'):
        return "advice"
    elif (state['usage'] == 'strategy'):
        return "strategy"
    else:
        return "invalid"

#Node News Extractor for every stock present in the users query
def news_extractor(state: AppState, limit = 10) -> AppState:
    print('\n',"Extracting News on User's stocks\n")

    stocks = state['stocks']
    news_dict = {}
    DF = pd.DataFrame(columns=["stock", "summary"])

    for stock in stocks:
        data = FIN_CLIENT.company_news(stock, _from="2025-04-01", to="2025-05-10")
        final = []
        for i in data[:limit]:
            final.append({'stock': stock, 'summary': i['summary']})

        temp = pd.DataFrame(final)
    
        DF = pd.concat([DF, temp], ignore_index=True)

    news_text = ""
    for stock, row in list(DF.iterrows()):
        if row['stock'] not in news_dict:
            news_dict[row['stock']] = [row['summary']]
        else:
            news_dict[row['stock']].append(row['summary'])

        news_text += f"{row['stock']}\n{row['summary']}\n---\n"

    state['news'] = news_text
    state['news_dict'] = news_dict
    return state

def news_report(state: AppState) -> AppState:
    print('\n',"Generating News Report with sentiments based on the extracted News.\n")

    prompt = f"""

Choose a combined sentiment that best represents these news articles:

    ```
    {state['news']}
    ```

    Each article is separated by `---`.

    Go through each news summary for that particular stock and give a sentiment vlaue between -1 to 1 where sentiment_score_definition: 
    x <= -0.35: Bearish; 
    -0.35 < x <= -0.15: Somewhat-Bearish; 
    -0.15 < x < 0.15: Neutral; 
    0.15 <= x < 0.35: Somewhat_Bullish; 
    x >= 0.35: Bullish

    Reply only with the sentiment and a short explanation (1-2 sentences) of why. 
    Format your answer for each stock in {state['stocks']} like this:
    
    ------
    STOCK (Companies Full Name) : SENTIMENT (with value x)

    `your responce from next line`
    ------

    When creating your answer, focus on answering the user query:
    {state["user_query"]}
    """

    response = llm.invoke([HumanMessage(prompt)])
    state["market_news"] = response.content

    #print(response.content)

    return state





def macro_economic(state: AppState) -> AppState:
    print('\n',"Gathering the market data and other economics for stocks.\n")

    stocks = state["stocks"]
    macro_economic_dict = {}
    
    for stock in stocks:
        info = FIN_CLIENT.company_basic_financials(stock, 'all')
        economic = {
            category: {
                fields[field]: info["metric"].get(field, None)  
                for field in fields
            }
            for category, fields in macro_terms.items()
        }

            
        df = yf.download(stock, period="12mo", interval="1d")
        df.dropna(inplace=True)

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)


        # Now apply RSI
        df["RSI"] = ta.rsi(df["Close"], length=14)

        macd = ta.macd(df["Close"])
        df["MACD_Line"] = macd["MACD_12_26_9"]
        df["MACD_Signal"] = macd["MACDs_12_26_9"]
        df["SMA_20"] = ta.sma(df["Close"], length=20)
        df["EMA_20"] = ta.ema(df["Close"], length=20)


        bbands = ta.bbands(df["Close"], length=20)
        df["BB_upper"]  = bbands["BBU_20_2.0"]
        df["BB_middle"] = bbands["BBM_20_2.0"]
        df["BB_lower"]  = bbands["BBL_20_2.0"]
        df["BB_bandwidth"] = bbands["BBB_20_2.0"]
        df["BB_percent"]   = bbands["BBP_20_2.0"]

        today = {}
        for idx, row in df.tail(1).iterrows():
            for col, val in row.items():
                today[col] = val
        economic['Today'] = today

        macro_economic_dict[stock] = economic
        
    state['macro_economics_dict'] = macro_economic_dict
    
    return state 

    
def market_trends(state: AppState) -> AppState:
    print('\n',"Generating a detailed report based on Economics and News Sentiment.\n")

    stocks = state['stocks']
    economic_analysis = ""
    
    for stock in stocks:
        economic = state['macro_economics_dict'][stock]
        economic_analysis += "----------------------\n"
        economic_analysis += (f"{stock}\n\n")

        for main_key in economic:
            curr = ""
            curr += (f"{main_key} :\n")
            for k, v in economic[main_key].items():
                curr += (f"\t{k} : {v}\n")
            curr += "\n"

            economic_analysis += curr
        
        economic_analysis += "----------------------\n"
    
    #print(economic_analysis)
    state['macro_economics'] = economic_analysis

    prompt = f"""



    You are a leading financial strategist with deep domain expertise in equity markets, valuation modeling, macroeconomic forecasting, and technical analysis. You are tasked with delivering a thorough investment analysis of the stocks {state['stocks']} based on the full set of financial data, technical indicators, and recent performance.
    The investor has asked the following:

    "{state['user_query']}"

    Economic Data for each Stock:
    ```
    {economic_analysis}
    ```

    You are also provided with overall Market News for each Stock seprated by "------":
    ```
    {state['market_news']}
    ```


    Generate a well detailed report for each stock in {state['stocks']} using the provided information to evaluate across multiple dimensions — fundamentals, momentum, volatility, and sentiment — and provide a data-backed, forward-looking report so that the
    investers gets an idea how the market is Behaving and how the given stocks are performing in the market.

    - Start each stock report with a clear heading with the stock name(underlined) (e.g., APPLE INC (AAPL))
    - Fundamentals: Discuss valuation, profitability, efficiency, financial health, and return ratios
    - Momentum: Analyze technical indicators such as price returns, RSI, MACD, and moving averages
    - Volatility: Mention beta and any indicators of price variability or risk
    - Sentiment: Reflect market news and tone, if it suggests optimism or caution
    - Avoid giving recommendations. Just deliver a rich, data-backed analysis so the investor can understand the stock's behavior and positioning in the market.

    """

    response = llm.invoke([HumanMessage(prompt)])
    state['market_trends'] = response.content

    return state




def advice(state: AppState) -> AppState:
    print('\n',"Generating the Advice the user is looking for.\n")

    prompt = f"""



    You are a leading financial strategist with deep domain expertise in equity markets, valuation modeling, macroeconomic forecasting, and technical analysis. You are tasked with delivering a thorough investment analysis of the stocks {state['stocks']} based on the full set of financial data, technical indicators, and recent performance.

    Economic Data for each Stock:
    ```
    {state['macro_economics']}
    ```

    You are also provided with overall Market News for each Stock seprated by "------":
    ```
    {state['market_news']}
    ```

    Create appropriate advice for user for the coming Day, coming 3 Days and for the coming Week to {state['user_query']} with proper reasoning.
    """

    responce = llm.invoke([HumanMessage(prompt)])
    state['advice']  = responce.content

    return state


def strategy(state: AppState) -> AppState:
    print('\n',"Generating the Strategy the user is looking for.\n")

    prompt = f"""



    You are a leading financial strategist with deep domain expertise in equity markets, valuation modeling, macroeconomic forecasting, and technical analysis. You are tasked with delivering a thorough investment analysis of the stocks {state['stocks']} based on the full set of financial data, technical indicators, and recent performance.
    The investor has asked the following:

    "{state['user_query']}"

    Economic Data for each Stock:
    ```
    {state['macro_economics']}
    ```

    You are also provided with overall Market News for each Stock seprated by "------":
    ```
    {state['market_news']}
    ```

    Now focusing on User's Portfolio:
    ```
    {state['portfolio']}
    ```

    Give strategy specific to user of how to distribute his portfolio into these {state['stocks']} stocks appropriately to gain maximum returns, with minimal risks 
    with proper reasoning.
    """

    responce = llm.invoke([HumanMessage(prompt)])
    state['strategy']  = responce.content
    return state

# print(test['stocks'])
# test = news_extractor(test, 5)
# test = news_report(test)
# test = macro_economic(test)
# test = market_trends(test)
# test = strategy(test)


