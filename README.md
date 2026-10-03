# FactoryZero AI
## Multi-Agent Factory Maintenance & Production Impact Engineer

**Detect the fault. Challenge the hypothesis. Plan the maintenance.**

FactoryZero AI is a hackathon-ready decision-support demonstration that combines deterministic telemetry analysis, six CrewAI agents, local TF-IDF RAG, evidence review, maintenance planning, production-impact arithmetic, and a deterministic verification layer. It is **not** a replacement for a qualified industrial engineer or a safety system.

### Architecture
`Streamlit → validation → Sensor → Electrical + Mechanical → Evidence/RAG → Maintenance Planner → Plant Manager → Verifier → Report`

The engineering principle is: **AI = reasoning, Python = calculation, RAG = evidence, CrewAI = collaboration, Verifier = trust layer, Streamlit = human interface.**

### Agents
1. Sensor Agent — interprets deterministic telemetry findings.
2. Electrical Engineer Agent — proposes electrical hypotheses.
3. Mechanical Engineer Agent — proposes mechanical hypotheses.
4. Evidence Agent — audits local document evidence.
5. Maintenance Planner Agent — builds an inspection-first plan.
6. Plant Manager Agent — explains operational impact from deterministic values.

### Stack
- Python 3.12
- Streamlit 1.65.0
- CrewAI 1.15.23
- Groq Python SDK 1.7.0
- `openai/gpt-oss-120b`
- pandas / NumPy
- scikit-learn TF-IDF
- pypdf
- Pydantic

The pinned versions were selected against the current package releases checked on 2026-10-03. Streamlit Community Cloud currently supports selecting Python versions and uses `requirements.txt` for dependencies. citeturn4search0turn3search1turn3search0

### Run locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env  # Windows
# or: cp .env.example .env
streamlit run app.py
```

Demo Mode works without `GROQ_API_KEY`. For Live Mode set `GROQ_API_KEY` in `.env` locally or Streamlit Secrets in the cloud.

### Streamlit Community Cloud
1. Create a GitHub repository.
2. Upload the contents of this ZIP.
3. Open Streamlit Community Cloud and create an app from the GitHub repository.
4. Select `app.py` as the entrypoint.
5. Choose Python 3.12 in Advanced settings if needed.
6. Add the secret:
```toml
GROQ_API_KEY = "YOUR_GROQ_KEY"
```
7. Deploy.
8. Run Demo Mode first, then test Live Mode.

Community Cloud expects the dependency file in the repository and runs the app from the repository root. citeturn0search0turn0search5turn0search2

### Demo
Use **Demo Mode** and click **Run Investigation**. The included synthetic MOTOR-017 scenario is intentionally fictional and marked as simulated.

### Live mode
Live mode uses the hardcoded model `openai/gpt-oss-120b` through the official Groq SDK. The model is documented by Groq with JSON-schema/JSON-object capabilities and a large context window. citeturn0search6turn0search12

### Inputs
Supported: CSV telemetry and PDF/TXT/CSV/JSON maintenance documents. The telemetry minimum is `timestamp`; other numeric columns are detected dynamically.

### Testing
```bash
pytest -q
```
Tests use deterministic fixtures and do not require a live Groq API.

### Safety
The app must never be treated as authorization to operate machinery. Follow site lockout/tagout procedures and qualified-personnel requirements. It must never recommend defeating emergency stops, bypassing interlocks, disabling protection, or unsafe energized work.

### Limitations
This is a hackathon demonstration. Synthetic documents are fictional, RAG is lightweight lexical retrieval, production impact is unit-based, and live LLM outputs remain subject to model/API availability.


## Live telemetry CSV compatibility

FactoryZero normalizes common industrial CSV header variants before deterministic
analysis. For example:

| Input header | Canonical field |
|---|---|
| `temperature_c`, `temp_c` | `temperature` |
| `vibration_mm_s`, `vibration_rms` | `vibration` |
| `current_a`, `motor_current_a` | `current` |
| `voltage_v`, `line_voltage_v` | `voltage` |
| `speed_rpm`, `motor_rpm` | `rpm` |
| `power_kw`, `motor_power_kw` | `power` |
| `datetime`, `date_time`, `event_time` | `timestamp` |

Health status and threshold breaches are calculated deterministically in Python.
Maintenance documents/RAG are used for evidence, hypotheses, and maintenance
guidance; they do not decide whether telemetry is normal or abnormal.
