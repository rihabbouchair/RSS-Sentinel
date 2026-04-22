NewsPulse (RSS Sentinel)
NewsPulse is an AI-powered news analysis ecosystem that fetches RSS feeds, performs sentiment analysis using local Large Language Models (LLMs), and visualizes insights through an interactive dashboard.

Key Features:
RSS Aggregation: Automatically pulls the latest headlines from customizable news sources.

Local AI Analysis: Leverages Ollama for privacy-focused sentiment analysis (no external API costs).

Real-time Insights: Classifies news as Positive, Neutral, or Negative to track global trends.

Interactive UI: A sleek dashboard built with Streamlit for data exploration.

Privacy-First: All data processing stays on your local machine.

Tech Stack:

LLM Orchestration: Ollama (Gemma3:4b)
Frontend: React js+Tillwind CSS
Backend: Python(fast API)
Data Store: SQLite
Data collection : FeedParser
Environment:Windows/ Linux 

Installation & Setup
1. Prerequisites
Ensure you have Ollama installed and running on your system.
# Pull the preferred model
ollama run gemma3:4b
2. Install Dependencies
pip install -r requirements.txt
3. Run the application:

# Backend
cd backend
uvicorn main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev

# in a new terminal
cd backend
python -c "from pipeline import run_pipeline; run_pipeline()"
(to manualy rerun pipeline)
