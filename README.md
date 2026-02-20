# Legal Document Explainer Bot

Simplify complex legal documents into easy-to-understand summaries.

## Demo

[Live Demo](https://legal-document-explainer-bot.onrender.com)

## Deploy on Render

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Settings:
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (see below)
6. Click Deploy

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Optional | Groq API key for AI summaries |
| `OPENROUTER_API_KEY` | Optional | OpenRouter API key (fallback) |
| `HUGGINGFACE_API_KEY` | Optional | HuggingFace API key (fallback) |

The app works without any API keys using local deterministic logic.

## Run Locally

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:8000
