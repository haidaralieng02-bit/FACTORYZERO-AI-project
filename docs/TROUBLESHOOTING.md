# Troubleshooting

## Error: Error installing requirements

If Streamlit shows:

> Error installing requirements. Click "Manage App" and consult the terminal for more details.

check the deployment terminal first. For the current repository, use the supplied `requirements.txt` and Python 3.12.

### Correct dependency versions

```text
streamlit==1.65.0
crewai==1.15.23
groq==1.7.0
pandas==2.3.3
numpy==2.3.3
scikit-learn==1.7.2
pypdf==6.1.3
pydantic==2.12.0
python-dotenv==1.2.4
pytest==8.4.2
```

### Most important compatibility fix

CrewAI 1.15.23 requires `python-dotenv>=1.2.2`. Do not restore `python-dotenv==1.1.1`.

### If the Cloud environment is still stuck

1. Commit and push the updated `requirements.txt` and `runtime.txt`.
2. Open the failed Streamlit app and check the terminal/build log.
3. If Python must be changed, delete the failed app and redeploy it.
4. In Advanced settings, select **Python 3.12**.
5. Re-enter the `GROQ_API_KEY` secret after redeployment.

### If installation succeeds but the app cannot call Groq

- Confirm the secret name is exactly `GROQ_API_KEY`.
- Do not put the key in `app.py`, `config.py`, or GitHub.
- Start in Demo Mode to verify the application without an API call.
- Check the app's warnings panel for recoverable agent/LLM errors.

### If Demo Mode works but Live Mode fails

The deterministic telemetry, RAG, maintenance planning, impact calculation, and verification layers can run with demo fallbacks. Live mode additionally requires a valid Groq API key and access to `openai/gpt-oss-120b`.
