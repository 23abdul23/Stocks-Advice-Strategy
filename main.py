from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from typing import TypedDict, Literal
from dotenv import load_dotenv
from google import genai
from google.genai import types
import os

import warnings
import random
import streamlit as st

from stocks import *
from classes import *
from utils import *

warnings.filterwarnings("ignore")

load_dotenv()
MODEL = "llama-3.1-8b-instant"

llm = ChatGroq(
    temperature=0,
    model_name=MODEL,
    api_key=os.environ.get("GROQ_API_KEY"),
)



graph = StateGraph(UsageClassfier)
graph.support_multiple_edges = True


graph.add_node("User Usage", usage_extractor)
graph.add_node("News Analysis", news_extractor)
graph.add_node("Economy Analysis", macro_economic)
graph.add_node("Market Trends", market_trends)
graph.add_node("Advice Generation", advice)
graph.add_node("Strategy Generation", strategy)

graph.add_conditional_edges("Market Trends", usage_check, {
    "advice": "Advice Generation",
    "strategy": "Strategy Generation"
})

graph.add_edge("User Usage", "News Analysis")
graph.add_edge("User Usage", "Economy Analysis")
graph.add_edge("News Analysis", "Market Trends")
graph.add_edge("Economy Analysis", "Market Trends")

graph.set_entry_point("User Usage")
graph.set_finish_point("Advice Generation")  

app = graph.compile()


# png_graph = app.get_graph().draw_mermaid_png()

# with open("Pipeline.png", "wb") as f:
#     f.write(png_graph)


#App Title
st.title("Stock Adivce/Strategy")

# User Input Section
st.subheader("Enter Your Query")
user_query = st.text_input("Ask your financial question (e.g., 'Advice related to NVIDIA Stocks', 'Give me trading strategy based on my portfolio')")

if st.button("Get Solution"):
    if user_query:
        state = UsageClassfier(user_query=user_query)
        state = usage_extractor(state)
        st.session_state.usage = state.usage
        st.session_state.state = state  # store whole object if needed

# Now handle strategy branch
if "usage" in st.session_state and st.session_state.usage == "strategy":
    st.subheader("Enter Your Portfolio Details")
    portfolio_query = st.text_input("Provide Portfolio Information")

    if st.button("Strategize"):
        if portfolio_query:
            state = UsageClassfier(user_query=portfolio_query)
            state = portfolio_summariser(portfolio_builder(state))
            st.write(state['portfolio'])
            
            stocks = random.choices(list(NASDAQ), k = 4)
            print(stocks)
            state['stocks'] = stocks
            st.write(state['stocks'])
            state = news_extractor(state, 3)
            state = news_report(state)

            st.write(state['market_news'])
            state = macro_economic(state)
            state = market_trends(state)
            st.write(state['market_trends'])
            state = strategy(state)
            st.write(state['strategy'])

elif "usage" in st.session_state and st.session_state.usage == "advice":
    state = UsageClassfier(user_query=user_query)
    state = usage_extractor(state)
    state = AppState(user_query= state.user_query, stocks= state.stocks)
    st.write(state['stocks'])
    state = news_extractor(state, 3)
    state = news_report(state)

    st.write(state['market_news'])
    state = macro_economic(state)
    state = market_trends(state)
    st.write(state['market_trends'])
    state = advice(state)
    st.write(state['advice'])

elif "usage" in st.session_state and st.session_state.usage == "invalid":
    st.write("Query is Invlaid")

                   

       
        