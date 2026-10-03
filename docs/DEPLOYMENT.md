# Deployment Guide

## Streamlit Community Cloud

FactoryZero AI is configured for Python 3.12 and uses a single `requirements.txt` dependency file at the repository root.

### 1. Push the repository

Push the complete repository to GitHub with this structure:

```text
factoryzero-ai/
├── app.py
├── requirements.txt
├── runtime.txt
└── .streamlit/config.toml
```

### 2. Deploy

In Streamlit Community Cloud, select:

- Repository: your FactoryZero AI repository
- Branch: your deployment branch
- Main file: `app.py`
- Python: **3.12**

The repository also contains `runtime.txt` with `3.12` as a deployment hint. If the Cloud deployment UI asks you to choose the Python version, explicitly select Python 3.12.

### 3. Add the Groq secret

Open the app's **Settings / Secrets** and add:

```toml
GROQ_API_KEY = "your_real_groq_api_key"
```

Never commit the real key to GitHub.

### 4. If you previously deployed a failed build

After changing `requirements.txt`, Streamlit Community Cloud normally detects the dependency change and rebuilds the environment. If the app was originally created with a different Python version and you need to change Python, Streamlit requires deleting and redeploying the app, then selecting Python 3.12 in Advanced settings.

### 5. Demo mode

The application can run in Demo Mode without a Groq API key. Demo data is synthetic and clearly labeled as simulated.

## Dependency compatibility note

The repository pins CrewAI 1.15.23. That release requires Python 3.10–3.13 and Pydantic `<2.13`; the repository pins Pydantic 2.12.0. CrewAI also requires `python-dotenv>=1.2.2`; the repository therefore pins `python-dotenv==1.2.4`.

The previous dependency set used `python-dotenv==1.1.1`, which is incompatible with the current CrewAI dependency requirement and can cause the Community Cloud dependency resolver to fail.
