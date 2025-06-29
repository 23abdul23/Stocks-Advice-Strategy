# Stock & Financial Advice Agent

This project is an AI-powered financial and stock advice assistant. It uses LLMs (Large Language Models) to classify user queries, extract portfolio information, summarize financial profiles, and provide tailored investment advice or strategies. The system is built using Python, Streamlit for the web UI, and LangChain/LangGraph for LLM orchestration.

## Features
- **User Query Classification**: Detects if the user wants stock advice, investment strategy, or if the query is invalid.
- **Portfolio Extraction**: Extracts structured financial and personal data from user input.
- **Portfolio Summarization**: Summarizes the user's financial situation and investment goals.
- **Stock News & Trends**: Integrates with Yahoo Finance and other APIs to fetch news and trends for mentioned stocks.
- **Macro-Economic Analysis**: (Planned) Summarizes macro-economic context.
- **Advice & Strategy Generation**: Provides actionable advice or investment strategies based on user profile.

## Project Structure
```
Financial-advice-agent/
  classes.py
  consts.py
  flask_app.py
  graph.png
  main.py
  README.md
  requirements.txt
  utils.py
  ...
```

## Requirements
- Python 3.11+
- API keys for Groq (LLM), Finnhub (for news/trends)

## Installation
1. **Clone the repository**
   ```sh
   git clone <your-repo-url>
   cd <Stock-advice-agent>
   ```
2. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```
3. **Set up environment variables**
   - Create a `.env` file in the project root with your API keys:
     ```env
     GROQ_API_KEY=your_groq_api_key
     FINNHUB_API_KEY=your_finnhub_api_key
     ```

## Running the App
1. **Start the Streamlit app**
   ```sh
   streamlit run main.py
   ```
2. **Open your browser** to the URL shown in the terminal (usually http://localhost:8501)
3. **Enter your query** in the UI and follow the prompts for advice or strategy.

## Notes
- Make sure your API keys are valid and have sufficient quota.
- The app uses LLMs, so internet access is required.
- For best results, use clear and specific queries (e.g., "Should I buy TATASTEEL?" or "I want a retirement strategy ---> I'm a 35-year-old with 2 kids and ₹1L income").

