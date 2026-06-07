# 🧠 AI Sentiment Analyzer

 

> A smart dashboard that analyzes customer reviews using Artificial Intelligence, classifying feelings and emotions, and extracting positive and negative points from textual comments. Developed as an Academic Project for the **Programação 2026.1** course at **SENAC PE - Systems Analysis and Development**. 

 

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE) 

[![Senac](https://img.shields.io/badge/Institution-Senac%20College-blue)](https://www.senac.br/)

[![LGPD](https://img.shields.io/badge/Compliance-LGPD%20Ready-blueviolet)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm) 

 

--- 

 

## 📋 Project Overview 

 

**AI Sentiment Analyzer** is an intelligent web application designed to analyze customer reviews using Artificial Intelligence. The platform processes textual comments to classify sentiment (positive, negative, neutral) and specific emotions, as well as extract recurring positive and negative points, helping businesses understand customer feedback in real-time. 

 

### Key Features 

* **Intelligent Dashboard:** Displays total reviews, average star rating, and interactive charts.
* **AI Sentiment & Emotion Analysis:** Classifies sentiments and emotions (e.g., joy, anger, sadness) using advanced LLMs via OpenRouter.
* **Automated Highlights:** Extracts recurrent positive and negative points directly from customer comments.
* **Dynamic Filters:** Filter feedback dynamically by source, date, sentiment category, and specific emotions.

 

### Project Architecture & Structure

```
Sentimentos-Analisador/
├── app.py                 # Main Flask server
├── schemas.py             # Pydantic models (validation)
├── ai_service.py          # Communication with OpenRouter API
├── data_service.py        # Data loading and statistics calculation
├── cache_service.py       # SQLite database cache helper
├── avaliacoes.json        # Simulated database of customer reviews
├── .env                   # API keys (ignored by Git)
├── .env.example           # Example configuration file
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html         # Dashboard HTML template
└── static/
    ├── css/style.css      # Dark mode styles
    └── js/dashboard.js    # Charts and frontend filters
```

```
avaliacoes.json ➔ Flask reads ➔ Pydantic validates ➔ AI analyzes comments
➔ Pydantic validates response ➔ Backend calculates statistics ➔ Frontend displays dashboards
```

> **Core Principle:** The AI analyzes text, the Backend processes data, and the Frontend displays the interactive dashboards.

 

--- 

 

## 🔒 LGPD & Data Privacy Compliance (Lei Geral de Proteção de Dados) 

 

Since this application processes customer reviews and potentially personal/sensitive data, ensure compliance with the Brazilian General Data Protection Law (LGPD - Law nº 13.709/2018). Fill in your project's privacy and compliance details below:

### Implemented Privacy Standards:
* **Consent & Minimization:** Explain how user reviews and personal data are collected and stored.
* **Anonymization:** Mention if user identifiers are anonymized.
* **Security & Deletion:** Mention any encryption/hashing applied to user data or API keys, and cache-clearing mechanisms like the `/api/limpar-cache` endpoint that purges stored data.

 

--- 

 

## 🛠️ Tech Stack 

 

* **Frontend:** HTML5, Vanilla CSS3 (Dark Mode), JavaScript, Chart.js (for interactive visualizations) 

* **Backend:** Python, Flask framework 

* **AI Integration:** OpenRouter API (utilizing LLaMA 3.1 8B, deepseek/deepseek-V4 or other configured models) 

* **Data Validation:** Pydantic v2 

* **Testing:** Pytest (Unit and integration testing)

 

--- 

 

## ⚙️ Getting Started (Local Development) 

 

Follow these steps to run the project environment locally. 

 

### 1. Prerequisites 

Ensure you have installed: 

* [Git](https://git-scm.com) 

* [Python](https://www.python.org/) (v3.10 or higher) 

 

### 2. Configuration (`.env`) 

Create a `.env` file in the root directory and configure the environment variables as shown below: 

 

```env 
OPENROUTER_API_KEY="your_openrouter_api_key_here"
``` 

 

### 3. Setup and Execution  

 

```bash 
# 1. Clone the repository 
git clone https://github.com/Richardfcs/sentimentos-analisador.git 
cd Sentimentos-Analisador 

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
``` 

After running, access the dashboard at: **http://localhost:5000**

 

---

 

## 📊 Core API Endpoints 

 

| Method | Endpoint | Description | LGPD / Data Scope |
| :--- | :--- | :--- | :--- |
| **GET** | `/` | Renders the main dashboard page | None (Public UI) |
| **GET** | `/api/dados/<categoria>` | Retrieves all processed reviews and stats for a category | Reads simulated feedback data |
| **POST** | `/api/analisar-avulso` | Analyzes a single ad-hoc comment using AI | Temporary processing, not stored |
| **POST** | `/api/limpar-cache` | Clears local memory cache and SQLite database cache | Permanent deletion of cached data (Right to Erasure / Storage Minimization) |

 

--- 

 

## 📝 Future Improvements (What We'd Do Next) 

 

If we had another semester, we plan to implement: 

* **Real API Integration:** Integrate with official APIs (Google Play Developer API, YouTube Data API, etc.) to extract comments dynamically.
* **Bulk File Import:** Support uploading custom datasets via CSV or Excel files.
* **Sentiment Forecasting:** Implement regression or time-series analysis to predict sentiment trends over time.

 

--- 

 

## 👥 Authors & Project Team 

 

* **Richard Silva** - Backend & AI Integration Specialist - [GitHub](https://github.com/Richardfcs)
* **Luiz Eduardo** - Backend & AI Integration Specialist - [GitHub](https://github.com/luardo05)
* **Cauã Souza** - Frontend Developer & UI Designer - [GitHub](https://github.com/Cauartsz)
* **Morgana Souza** - Frontend Developer & UI Designer - [GitHub](https://github.com/MorganaSouza)

* **Academic Advisor / Professor:** Prof. Rodrigo Rios de Larrazábal
* **Tech English Course Professor:** Prof. Leonardo Trevas 
