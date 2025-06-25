from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from typing import TypedDict, Literal
from dotenv import load_dotenv
from google import genai
from google.genai import types
import os

import warnings
import streamlit as st

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

# test_input = UsageClassfier(user_query="""
# I'm 32 years old, working as a full-time software engineer in Bangalore. 
# I make around ₹1.2 lakh per month with a side freelance income of ₹20,000. 
# My investment goal is to build long-term wealth for early retirement, ideally by the age of 50. 
# I’ve been investing for about 4 years, mostly in mutual funds, but I want to be more active now. 
# Given that I have moderate risk tolerance and two young children, I want a strategy that balances growth and stability.
# What investment duration and asset mix would you recommend?
# """)

# test_input1 = usage_extractor(test_input)

# test_input2 = portfolio_builder(test_input)

# test_input3 = portfolio_summariser(test_input2)

graph = StateGraph(UsageClassfier)
graph.support_multiple_edges = True


graph.add_node("User Usage", usage_extractor)
#graph.add_node("Portfolio Builder", portfolio_builder)
graph.add_node("News Analysis", news_extractor)
graph.add_node("Economy Analysis", macro_economic)
graph.add_node("Market Trends", market_trends)
graph.add_node("Advice Generation", advice)
graph.add_node("Strategy Generation", strategy)
graph.add_node("Final Proposal", final_proposal)

graph.add_conditional_edges("Market Trends", usage_check, {"advice": "Advice Generation", "strategy" : "Strategy Generation", "invalid" : "Final Proposal"})

#graph.add_edge("User Usage", "Portfolio Builder")
graph.add_edge("User Usage", "News Analysis")
graph.add_edge("User Usage", "Economy Analysis")
graph.add_edge("News Analysis", "Market Trends")
graph.add_edge("Economy Analysis", "Market Trends")
graph.add_edge("Advice Generation", "Final Proposal")
graph.add_edge("Strategy Generation", "Final Proposal")

graph.set_entry_point("User Usage")
graph.set_finish_point("Final Proposal")
app = graph.compile()

# png_graph = app.get_graph().draw_mermaid_png()

# with open("Pipeline.png", "wb") as f:
#     f.write(png_graph)


# temp = UsageClassfier(user_query= "I'm 32, married with 2 kids, earning ₹1.2L/month as a software engineer. My side income is ₹20K/month. I've been investing for 4 years, mostly in mutual funds. I'm planning for early retirement by 50, prefer moderate risk, and want a proper investing strategy.")
# temp = portfolio_summariser(portfolio_builder(temp))


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
            st.write(state['stocks'])

elif "usage" in st.session_state and st.session_state.usage == "advice":
    st.write("Giving You Advice, Shortly")
    st.write(state.stocks)

elif "usage" in st.session_state and st.session_state.usage == "invalid":
    st.write("Query is Invlaid")

                   

       
        