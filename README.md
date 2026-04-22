#  NewsPulse (RSS Sentinel)

**NewsPulse** is an AI-powered news analysis ecosystem that fetches RSS feeds, performs sentiment analysis using local Large Language Models (LLMs), and visualizes insights through a modern interactive dashboard.

---

##  Key Features

* **RSS Aggregation:** Automatically pulls the latest headlines from customizable news sources using `FeedParser`.
* **Local AI Analysis:** Leverages **Ollama (Gemma 3:4b)** for privacy-focused sentiment analysis with zero API costs.
* **Real-time Insights:** Classifies news as **Positive**, **Neutral**, or **Negative** to track global trends.
* **Interactive UI:** A sleek, responsive dashboard built with **React.js** and **Tailwind CSS**.
* **Privacy-First:** All data processing and storage (**SQLite**) stay entirely on your local machine.

---

##  Tech Stack

| Component          | Technology                          |
|--------------------|-------------------------------------|
| **Frontend** | React.js + Tailwind CSS            |
| **Backend** | Python (FastAPI)                   |
| **LLM Engine** | Ollama (Gemma 3:4b)                |
| **Database** | SQLite                             |
| **Data Collection**| FeedParser                         |
| **Environment** | Windows / Linux                    |

---

##  Installation & Setup

### 1. Prerequisites
Ensure you have **Ollama** installed and running, then pull the model:
```bash
ollama run gemma3:4b
