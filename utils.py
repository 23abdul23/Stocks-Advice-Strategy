from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

import requests, random, json
import finnhub


from classes import *
from stocks import NIFTY50

load_dotenv()
NIFTY50 = list(NIFTY50)

MODEL = "llama-3.1-8b-instant"

llm = ChatGroq(
    temperature=0,
    model_name=MODEL,
    api_key=os.environ.get("GROQ_API_KEY"),
)

#Node adivce or strategy extracter
def usage_extractor(state: UsageClassfier) -> UsageClassfier:
    print('\n',"Determining whether the user wants advice, strategy, or neither.")

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
    # new_state["usage"] = extraction.usage
    # new_state['stocks'] = extraction.stocks

    state.usage = extraction.usage
    state.stocks = extraction.stocks
    return state

#Node Portfolio Builder from the user Input
def portfolio_builder(state: UsageClassfier) -> UsageClassfier:
    print('\n',"Building the portfolio from user query")

    prompt = """
    Extract the following portfolio fields from the user's query.

    If a field is missing:
    - For string fields, set value to "" (empty string)
    - For int/float fields, set value to null / None

    Fields:
    - age (int): User's age, or infer average from phrases like "young", "middle-aged", "retired", etc.
    - job_type (str): Classify as "private", "government", "semi private", "non profit", or "business". Else "".
    - job (str): Job title or "".
    - monthly_income (float): Monthly primary income. If not stated, return null.
    - side_income (float): Side income or null.
    - investment_goal (str): E.g., "retirement", "wealth building", etc. Else "".
    - investment_duration (str): E.g., "10 years", "long term", etc. Else "".
    - risk_preference (float): From 0 to 1. Estimate from phrases like:
        - "risk-averse", "low risk" → ~0.2
        - "moderate" → ~0.5
        - "aggressive", "high risk" → ~0.8+
        Else null.
    - investing_years (int): Years of experience investing, or null.
    - retirement_age (int): Desired retirement age if mentioned, or Appropriate age for retirement ->60.
    - martial_status (str): "married", "single", etc. Else "".
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
    print('\n',"Summarizing the overall portfolio from user inputs")

    prompt = f"""
    Analyze the following investor profile and provide a summary including the finalncial outlook, retirement strategy, risk assessment:

    Personal Information:
    - Age: {state.age}
    - Job Type: {state.job_type}
    - Job Role: {state.job}
    - Marital Status: {state.martial_status}
    - Number of Children: {state.children}
    - Years of Investing Experience: {state.investing_years}
    - Planned Retirement Age: {state.retirement_age}

    Financial Situation:
    - Monthly Income: ₹{state.monthly_income:.2f}
    - Side Income: ₹{state.side_income:.2f}
    - Total Monthly Income: ₹{(state.monthly_income or 0) + (state.side_income or 0):.2f}

    Investment Objectives:
    - Investment Goal: {state.investment_goal}
    - Investment Duration: {state.investment_duration}
    - Risk Preference (0–1 scale): {state.risk_preference}
    """

    response = llm.invoke([HumanMessage(prompt)])

    new_state = AppState()
    new_state["usage"] = state.usage
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
# def news_extractor(state: AppState) -> AppState:
def news_extractor():
    
    return None
    
#news_extractor()


def macro_economic(state: AppState) -> AppState:
    return None

def market_trends(state: AppState) -> AppState:
    return None 

def advice(state: AppState) -> AppState:
    return None

def strategy(state: AppState) -> AppState:
    return None

def final_proposal(state: AppState) -> AppState:
    return None
