from __future__ import annotations
import json, io
from pathlib import Path
import pandas as pd
import streamlit as st
from config import DEMO_DIR, DOCUMENTS_DIR, get_groq_api_key, MODEL_NAME
from core.orchestrator import run_investigation
from tools.telemetry import normalize_telemetry_columns
from core.schemas import IncidentState

st.set_page_config(page_title="FactoryZero AI",page_icon="🏭",layout="wide",initial_sidebar_state="expanded")

st.markdown("""<style>
.main{background:linear-gradient(180deg,#07111f 0%,#0b1626 45%,#0f1d2d 100%)}
.block-container{padding-top:1.2rem;max-width:1400px}
.hero{padding:1.3rem 1.5rem;border:1px solid rgba(255,255,255,.12);border-radius:18px;background:linear-gradient(135deg,rgba(16,34,54,.95),rgba(12,24,39,.9));box-shadow:0 12px 35px rgba(0,0,0,.18)}
.hero h1{margin:0;font-size:2.2rem}.hero p{margin:.35rem 0 0;color:#b7c7d8}.status{display:inline-block;padding:.3rem .7rem;border-radius:999px;background:rgba(31,203,137,.13);color:#61e6b0;font-weight:700;font-size:.82rem}
.card{padding:1rem;border:1px solid rgba(255,255,255,.1);border-radius:14px;background:rgba(255,255,255,.035);min-height:110px}.muted{color:#9eb0c3;font-size:.85rem}.agent{padding:.85rem;border-left:4px solid #4f9cff;border-radius:10px;background:rgba(255,255,255,.035);margin:.5rem 0}.pill{display:inline-block;padding:.2rem .5rem;border-radius:999px;background:rgba(79,156,255,.13);font-size:.78rem}
</style>""",unsafe_allow_html=True)

st.markdown('<div class="hero"><span class="status">● AI SYSTEM READY</span><h1>FactoryZero AI</h1><p>Multi-Agent Factory Maintenance Intelligence</p><p><b>Detect the fault. Challenge the hypothesis. Plan the maintenance.</b></p></div>',unsafe_allow_html=True)

if "state" not in st.session_state: st.session_state.state=None
if "telemetry_df" not in st.session_state: st.session_state.telemetry_df=None

with st.sidebar:
    st.markdown("## 🏭 FactoryZero AI")
    demo=st.toggle("Demo Mode",value=True,help="Runs with synthetic data and no Groq API call.")
    st.divider(); st.markdown("### Incident Upload")
    telemetry_file=st.file_uploader("Telemetry CSV",type=["csv"])
    docs=st.file_uploader("Maintenance Documents",type=["pdf","txt","csv","json"],accept_multiple_files=True)
    st.markdown("### Machine Information")
    machine_id=st.text_input("Machine ID",value="MOTOR-017")
    machine_name=st.text_input("Machine Name",value="Demo Motor 017")
    incident_id=st.text_input("Incident ID",value="INC-017-DEMO")
    run=st.button("🔎 Run Investigation",type="primary",use_container_width=True)
    st.divider(); st.markdown("### System Status")
    if get_groq_api_key(): st.success("Live Groq mode available")
    else: st.info("Demo mode available • Groq key not configured")
    st.caption(f"Model: {MODEL_NAME}")


def load_demo():
    return pd.read_csv(DEMO_DIR/"DEMO_MOTOR_017.csv"), [DOCUMENTS_DIR/x for x in ["motor_manual.txt","maintenance_manual.txt","alarm_codes.txt","maintenance_history.csv","spare_parts.csv"]]

def save_uploads(files):
    temp=Path(".factoryzero_uploads"); temp.mkdir(exist_ok=True); paths=[]
    for f in files:
        p=temp/f.name; p.write_bytes(f.getvalue()); paths.append(p)
    return paths

if run:
    try:
        if demo or telemetry_file is None:
            df,paths=load_demo(); mode_live=False
        else:
            df=pd.read_csv(telemetry_file); paths=save_uploads(docs); mode_live=True
            if not paths: paths=[DOCUMENTS_DIR/x for x in ["motor_manual.txt","maintenance_manual.txt","alarm_codes.txt","maintenance_history.csv","spare_parts.csv"]]
        # Normalize common live CSV headers before both analysis and UI rendering.
        # This keeps charts/reporting consistent with the deterministic telemetry engine.
        df=normalize_telemetry_columns(df)
        st.session_state.telemetry_df=df
        progress=st.progress(0,text="Starting investigation...")
        statuses=["Sensor Agent","Electrical Engineer Agent","Mechanical Engineer Agent","Evidence Agent","Maintenance Planner Agent","Plant Manager Agent","Verification Layer"]
        def cb(agent,status,msg):
            idx=statuses.index(agent) if agent in statuses else 0; progress.progress(min(1,(idx+0.5)/len(statuses)),text=f"{agent}: {msg}")
        state=run_investigation(df,incident_id,machine_id,machine_name,paths,live=mode_live,progress_callback=cb)
        progress.progress(1.0,text="Investigation complete")
        st.session_state.state=state
    except Exception as e:
        st.error(f"We could not analyze this incident. Reason: {e}")

state: IncidentState|None=st.session_state.state
if state is None:
    st.info("Start with Demo Mode to see the complete FactoryZero AI workflow without an API key.")
    st.markdown("### Workflow")
    cols=st.columns(7)
    for c,label in zip(cols,["Sensor","Electrical","Mechanical","Evidence","Maintenance","Plant Manager","Verifier"]): c.markdown(f"**{label}**")
    st.stop()

st.caption(f"Mode: {'🟢 LIVE' if state.mode=='LIVE' else '🟡 DEMO / SIMULATED RESULT'}  •  Incident: {state.incident_id}")
if state.errors:
    with st.expander("Warnings / recoverable errors",expanded=False):
        for e in state.errors: st.warning(e)

tabs=st.tabs(["Overview","Telemetry","Agent Investigation","Evidence","Maintenance Plan","Production Impact","Verification","Final Report"])
with tabs[0]:
    sr=state.sensor_result; p=state.maintenance_plan; impact=state.production_impact; ver=state.verification
    vals=[("Machine Status",sr.status if sr else "—"),("Severity",sr.severity if sr else "—"),("Primary Hypothesis",(state.electrical_hypotheses+state.mechanical_hypotheses)[0].hypothesis if state.electrical_hypotheses+state.mechanical_hypotheses else "—"),("Confidence",f"{(state.electrical_hypotheses+state.mechanical_hypotheses)[0].confidence:.0%}" if state.electrical_hypotheses+state.mechanical_hypotheses else "—"),("Evidence Score",f"{sum(e.score for e in state.evidence)/len(state.evidence):.2f}" if state.evidence else "0.00"),("Estimated Downtime",f"{p.estimated_downtime_hours:.1f} h" if p else "—"),("Production Impact",f"{impact.estimated_production_impact_units:g} units" if impact else "—"),("Verification",ver.status if ver else "—")]
    cols=st.columns(4)
    for i,(k,v) in enumerate(vals): cols[i%4].metric(k,v)
    st.markdown("### What happened?"); st.write(sr.trend_summary if sr else "No telemetry result.")
    if sr: st.write(sr.observations)
with tabs[1]:
    df=st.session_state.telemetry_df
    st.dataframe(df.head(25),use_container_width=True)
    numeric=[c for c in df.columns if c.lower()!="timestamp" and pd.api.types.is_numeric_dtype(df[c])]
    for c in numeric: st.line_chart(df.set_index("timestamp")[c],height=220)
    if state.sensor_result and state.sensor_result.threshold_breaches: st.dataframe(pd.DataFrame(state.sensor_result.threshold_breaches),use_container_width=True)
with tabs[2]:
    st.markdown("### Multi-Agent Investigation")
    for ev in state.agent_events:
        # Defensive rendering: older/partially serialized states may contain dict events.
        if isinstance(ev, dict):
            agent = ev.get("agent", "Unknown Agent")
            status = ev.get("status", "UNKNOWN")
            output_summary = ev.get("output_summary", "")
        else:
            agent = getattr(ev, "agent", "Unknown Agent")
            status = getattr(ev, "status", "UNKNOWN")
            output_summary = getattr(ev, "output_summary", "")
        st.markdown(f'<div class="agent"><b>{agent}</b> <span class="pill">{status}</span><br><span class="muted">{output_summary}</span></div>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        st.markdown("### ⚡ Electrical Agent")
        for h in state.electrical_hypotheses: st.write(f"**{h.hypothesis}** — {h.confidence:.0%}"); st.caption(h.reasoning)
    with c2:
        st.markdown("### ⚙️ Mechanical Agent")
        for h in state.mechanical_hypotheses: st.write(f"**{h.hypothesis}** — {h.confidence:.0%}"); st.caption(h.reasoning)
with tabs[3]:
    if not state.evidence: st.warning("No retrievable evidence was found.")
    for e in state.evidence:
        st.markdown(f"**{e.document}** • Page: {e.page if e.page is not None else 'Page not available'} • {e.support_level} • score {e.score:.2f}")
        st.info(e.relevant_passage)
        st.caption(f"Supports: {e.supported_hypothesis}")
with tabs[4]:
    p=state.maintenance_plan
    if p:
        st.subheader("Recommended Inspection")
        for i,x in enumerate(p.inspection_sequence,1): st.write(f"{i}. {x}")
        c1,c2,c3=st.columns(3); c1.metric("Priority",p.priority); c2.metric("Downtime",f"{p.estimated_downtime_hours:.1f} h"); c3.metric("Tools",len(p.required_tools))
        st.markdown("**Required Tools**"); st.write(p.required_tools); st.markdown("**Spare Parts**"); st.write(p.required_parts); st.markdown("**Safety**"); st.write(p.safety_notes)
with tabs[5]:
    i=state.production_impact
    if i:
        c1,c2,c3=st.columns(3); c1.metric("Production Rate",f"{i.production_rate_units_per_hour:g} units/h"); c2.metric("Downtime",f"{i.downtime_hours:g} h"); c3.metric("Estimated Impact",f"{i.estimated_production_impact_units:g} units")
        st.progress(min(1.0,i.downtime_hours/8),text="Relative maintenance window")
        st.info("Production impact is calculated by Python from supplied production rate × downtime. It is not a financial-loss estimate.")
with tabs[6]:
    v=state.verification
    if v:
        st.metric("Verification Result",v.status)
        for k,val in v.checks.items(): st.write(("✓" if val else "✗")+" "+k.title())
        if v.errors:
            st.error("\n".join(v.errors))
        if v.warnings:
            for x in v.warnings: st.warning(x)
with tabs[7]:
    # Human-readable engineering report. Keep raw JSON only as an optional download.
    report=state.to_report_dict()
    sr=state.sensor_result
    hyps=state.electrical_hypotheses + state.mechanical_hypotheses
    p=state.maintenance_plan
    impact=state.production_impact
    ver=state.verification

    st.markdown("## 📋 FactoryZero AI Investigation Report")
    st.caption(f"Incident {state.incident_id} • Machine {state.machine_id} • {state.machine_name}")

    # Executive status
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Investigation Status", state.final_status or "—")
    c2.metric("Machine Condition", sr.status if sr else "—")
    c3.metric("Severity", sr.severity if sr else "—")
    c4.metric("Verification", ver.status if ver else "—")

    st.markdown("### 1. Executive Summary")
    if sr:
        st.info(sr.trend_summary)
        if sr.observations:
            for observation in sr.observations:
                st.write(f"• {observation}")
    else:
        st.write("No telemetry summary is available.")

    st.markdown("### 2. Key Telemetry Findings")
    if state.telemetry_summary:
        rows=[]
        for parameter,stats in state.telemetry_summary.items():
            rows.append({
                "Parameter": parameter.title(),
                "Minimum": round(stats.get("min",0),3),
                "Maximum": round(stats.get("max",0),3),
                "Average": round(stats.get("average",0),3),
                "Trend / Slope": round(stats.get("slope",0),4),
                "Change %": round(stats.get("percentage_change",0),2),
            })
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

    if sr and sr.threshold_breaches:
        st.markdown("**Threshold breaches**")
        breach_rows=[]
        for b in sr.threshold_breaches:
            breach_rows.append({
                "Parameter": b.get("parameter","—").title(),
                "Threshold": b.get("threshold","—"),
                "Breach Count": b.get("breach_count","—"),
                "Maximum": b.get("max","—"),
            })
        st.dataframe(pd.DataFrame(breach_rows),use_container_width=True,hide_index=True)

    st.markdown("### 3. Engineering Hypotheses")
    if hyps:
        for idx,h in enumerate(hyps,1):
            domain="Electrical" if h in state.electrical_hypotheses else "Mechanical"
            with st.expander(f"{idx}. {h.hypothesis} — {h.confidence:.0%} confidence",expanded=idx==1):
                st.markdown(f"**Engineering domain:** {domain}")
                st.markdown(f"**Reasoning:** {h.reasoning}")
                if h.supporting_observations:
                    st.markdown("**Supporting observations**")
                    for x in h.supporting_observations: st.write(f"• {x}")
                if h.evidence_needed:
                    st.markdown("**Evidence still needed**")
                    for x in h.evidence_needed: st.write(f"• {x}")
    else:
        st.write("No engineering hypotheses were generated.")

    st.markdown("### 4. Evidence & Traceability")
    if state.evidence:
        for e in state.evidence:
            page=f"Page {e.page}" if e.page is not None else "Page not available"
            with st.expander(f"{e.document} • {page} • {e.support_level} support",expanded=False):
                st.markdown(f"**Supports:** {e.supported_hypothesis}")
                st.markdown(f"**Retrieval score:** {e.score:.2f}")
                st.markdown("**Relevant evidence:**")
                st.info(e.relevant_passage)
    else:
        st.warning("No supporting evidence was retrieved.")

    st.markdown("### 5. Maintenance Plan")
    if p:
        st.markdown("**Immediate actions**")
        for x in p.immediate_actions: st.write(f"• {x}")
        st.markdown("**Inspection sequence**")
        for n,x in enumerate(p.inspection_sequence,1): st.write(f"{n}. {x}")
        c1,c2,c3=st.columns(3)
        c1.metric("Priority",p.priority)
        c2.metric("Estimated Downtime",f"{p.estimated_downtime_hours:.1f} h")
        c3.metric("Required Tools",len(p.required_tools))
        with st.expander("Parts and tools",expanded=False):
            st.markdown("**Required parts**")
            for x in p.required_parts: st.write(f"• {x}")
            st.markdown("**Required tools**")
            for x in p.required_tools: st.write(f"• {x}")
        st.markdown("**Repair guidance**")
        for x in p.repair_actions: st.write(f"• {x}")
        st.markdown("**Safety controls**")
        for x in p.safety_notes: st.warning(x)

    st.markdown("### 6. Production Impact")
    if impact:
        c1,c2,c3=st.columns(3)
        c1.metric("Production Rate",f"{impact.production_rate_units_per_hour:g} units/hour")
        c2.metric("Downtime",f"{impact.downtime_hours:g} hours")
        c3.metric("Estimated Production Impact",f"{impact.estimated_production_impact_units:g} units")
        st.info(impact.operational_notes[0] if impact.operational_notes else "Impact is a deterministic unit estimate.")
        st.write(f"**Maintenance window:** {impact.maintenance_window}")

    st.markdown("### 7. Verification")
    if ver:
        if ver.status == "PASS": st.success("Verification PASSED — schema, evidence, arithmetic, safety and confidence checks passed.")
        elif ver.status == "REVISE": st.warning("Verification requires revision before treating the report as complete.")
        else: st.error("Verification FAILED. Review the errors below.")
        check_cols=st.columns(len(ver.checks) or 1)
        for col,(k,val) in zip(check_cols,ver.checks.items()):
            col.metric(k.title(),"PASS" if val else "FAIL")
        for x in ver.errors: st.error(x)
        for x in ver.warnings: st.warning(x)

    st.markdown("### 8. Report Metadata")
    st.write(f"**Mode:** {'Live' if state.mode=='LIVE' else 'Demo / Simulated'}")
    st.write(f"**Incident ID:** {state.incident_id}")
    st.write(f"**Machine ID:** {state.machine_id}")

    st.divider()
    st.markdown("### Downloads")
    d1,d2=st.columns(2)
    with d1:
        st.download_button("⬇ Download technical JSON",json.dumps(report,indent=2).encode(),file_name="factoryzero_report.json",mime="application/json",use_container_width=True)
    with d2:
        # Generate a readable plain-text version rather than exposing internal Python/JSON formatting.
        lines=[
            "FACTORYZERO AI — INVESTIGATION REPORT",
            f"Incident: {state.incident_id}",
            f"Machine: {state.machine_id} — {state.machine_name}",
            f"Status: {state.final_status}",
            f"Severity: {sr.severity if sr else '—'}",
            "",
            "EXECUTIVE SUMMARY",
            sr.trend_summary if sr else "No telemetry result.",
            "",
            "KEY OBSERVATIONS",
            *[f"- {x}" for x in (sr.observations if sr else [])],
            "",
            "ENGINEERING HYPOTHESES",
            *[f"- {h.hypothesis} ({h.confidence:.0%} confidence): {h.reasoning}" for h in hyps],
            "",
            "MAINTENANCE PLAN",
            *( [f"{i}. {x}" for i,x in enumerate(p.inspection_sequence,1)] if p else [] ),
            "",
            "PRODUCTION IMPACT",
            f"{impact.estimated_production_impact_units:g} units" if impact else "Not available",
            "",
            "VERIFICATION",
            ver.status if ver else "Not available",
        ]
        st.download_button("⬇ Download readable report", "\n".join(lines), file_name="factoryzero_report.txt", mime="text/plain", use_container_width=True)

    st.warning("Decision-support demonstration only. Never use this application as authorization to operate machinery or bypass safety systems.")
