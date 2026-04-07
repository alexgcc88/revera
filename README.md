# Revera — Forecast Intelligence
**Siemens Advanta · AI Agent · Business Case NOVA 2026**

Chat interface for MinT hierarchical Revenue forecasts across 4 BUs, 16 segments and 108 subsegments.

---

## Setup (5 minutes)

### 1. Get a free Groq API key
Go to **console.groq.com** → sign up → API Keys → Create key  
No credit card needed. Free tier is more than enough.

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run locally
```bash
streamlit run app.py
```
The app opens at **http://localhost:8501**

Paste your Groq API key in the sidebar and start asking questions.

---

## Deploy online (optional, also free)

1. Push this folder to a GitHub repo
2. Go to **share.streamlit.io** → New app → select your repo
3. Add your Groq API key as a secret:
   - Settings → Secrets → add: `GROQ_API_KEY = "gsk_..."`
4. Update `nlu.py` to read from `st.secrets["GROQ_API_KEY"]` if you want it pre-filled

---

## Example questions
- "Show revenue by BU"
- "What are the top 5 subsegments by revenue?"
- "Compare the best and the poorest segment"
- "Which segment has the highest growth?"
- "What is the difference between period 39 and 38?"
- "Executive summary"
- "Show model performance metrics"

---

## Updating with test set forecasts (periods 43–48)
When the MinT test set predictions are ready, replace the arrays in `data.py` with the new values.  
Everything else stays the same.

---

## Stack
- **Frontend**: Streamlit
- **NLU**: Groq API (Llama 3.3 70B) — free
- **Charts**: Plotly
- **Data**: MinT shrink reconciled forecasts (in-sample P.37–42)
