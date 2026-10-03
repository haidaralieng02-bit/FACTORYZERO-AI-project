from __future__ import annotations
from datetime import datetime, timezone
import json
from pathlib import Path
from core.schemas import IncidentState, TelemetryResult, Hypothesis, EvidenceItem, MaintenancePlan, ProductionImpact, AgentEvent
from core.llm_client import LLMClient
from core.crew_adapter import run_crew_agent
from core.validators import validate_incident
from rag.ingest import build_chunks
from rag.retriever import LocalRetriever
from tools.telemetry import analyze_telemetry
from tools.impact import calculate_production_impact
from config import PROMPTS_DIR, TOP_K, DEMO_DIR, DOCUMENTS_DIR

def _prompt(name): return (PROMPTS_DIR/f"{name}_prompt.txt").read_text(encoding="utf-8")

def _event(state, agent, status, input_summary="", output_summary="", confidence=None):
    state.agent_events.append(AgentEvent(agent=agent,status=status,timestamp=datetime.now(timezone.utc).isoformat(),input_summary=input_summary,output_summary=output_summary,confidence=confidence))

def _demo_hypotheses(state):
    return [Hypothesis(hypothesis="Possible motor overload/current imbalance",confidence=0.72,reasoning="Current rises alongside temperature and the deterministic telemetry analysis flags a current threshold breach.",supporting_observations=["Current increases during the abnormal event.","Temperature also rises."],evidence_needed=["Verify phase balance and load condition."])]

def run_investigation(df, incident_id, machine_id, machine_name, document_paths=None, parts_df=None, live=False, progress_callback=None):
    client=LLMClient(); mode="LIVE" if live and client.available else "DEMO"
    state=IncidentState(incident_id=incident_id,machine_id=machine_id,machine_name=machine_name,mode=mode,source_files=[str(x) for x in (document_paths or [])])
    def step(agent,status,msg="",conf=None):
        _event(state,agent,status,msg,msg,conf)
        if progress_callback: progress_callback(agent,status,msg)
    try:
        step("Sensor Agent","RUNNING","Analyzing telemetry")
        telemetry=analyze_telemetry(df); state.sensor_result=TelemetryResult.model_validate(telemetry); state.telemetry_summary=telemetry["statistics"]
        step("Sensor Agent","COMPLETED",telemetry["trend_summary"])
        sensor_json=json.dumps(telemetry,indent=2)
        if mode=="LIVE":
            try:
                raw=run_crew_agent(client,"Telemetry anomaly analyst","Explain deterministic telemetry findings without recalculating them.","You explain Python-calculated industrial telemetry findings carefully.",_prompt("sensor").format(sensor_json=sensor_json),"JSON object matching the telemetry result schema.")
                parsed=client.parse_json(raw); parsed.update(telemetry); state.sensor_result=TelemetryResult.model_validate(parsed)
            except Exception as e: state.errors.append(f"Sensor LLM explanation unavailable: {e}")
        # parallel domains are represented sequentially for deterministic auditability
        for label, prompt_name, target in [("Electrical Engineer Agent","electrical", "electrical_hypotheses"),("Mechanical Engineer Agent","mechanical","mechanical_hypotheses")]:
            step(label,"RUNNING","Generating evidence-aware hypotheses")
            if mode=="LIVE":
                try:
                    raw=run_crew_agent(client,label,"Generate cautious hypotheses from supplied observations.","You must distinguish observations, hypotheses, evidence needed and uncertainty.",_prompt(prompt_name).format(sensor_json=sensor_json),"JSON array of hypothesis objects.")
                    arr=client.parse_json(raw); hyps=[Hypothesis.model_validate(x) for x in (arr if isinstance(arr,list) else arr.get("hypotheses",[]))]
                except Exception as e:
                    state.errors.append(f"{label} live call failed: {e}"); hyps=[]
            else: hyps=[]
            if not hyps:
                if label.startswith("Electrical"): hyps=_demo_hypotheses(state)
                else: hyps=[Hypothesis(hypothesis="Possible bearing degradation or misalignment",confidence=0.68,reasoning="Vibration and temperature rise together during the abnormal event, which warrants mechanical inspection.",supporting_observations=["Vibration increases.","Temperature increases."],evidence_needed=["Inspect bearing condition, coupling alignment and lubrication."])]
            setattr(state,target,hyps); step(label,"COMPLETED",hyps[0].hypothesis,hyps[0].confidence)
        # RAG
        step("Evidence Agent","RUNNING","Searching maintenance evidence")
        paths=[Path(p) for p in (document_paths or []) if Path(p).exists()]
        if not paths: paths=[p for p in DOCUMENTS_DIR.iterdir() if p.suffix.lower() in {".txt",".csv",".pdf",".json"}]
        chunks=build_chunks(paths); retriever=LocalRetriever(chunks)
        query=" ".join([state.electrical_hypotheses[0].hypothesis,state.mechanical_hypotheses[0].hypothesis,"maintenance troubleshooting bearing overload current vibration temperature"])
        retrieved=retriever.search(query,TOP_K)
        if mode=="LIVE" and retrieved:
            try:
                raw=run_crew_agent(client,"Evidence Agent","Audit supplied passages against hypotheses.","You are an evidence auditor. Never invent document text or page numbers.",_prompt("evidence").format(hypotheses=json.dumps([h.model_dump() for h in state.electrical_hypotheses+state.mechanical_hypotheses]),retrieved=json.dumps(retrieved)),"JSON array of evidence objects.")
                arr=client.parse_json(raw); evidence=[EvidenceItem.model_validate(x) for x in (arr if isinstance(arr,list) else arr.get("evidence",[]))]
            except Exception as e: state.errors.append(f"Evidence live call failed: {e}"); evidence=[]
        else: evidence=[]
        if not evidence:
            for r in retrieved:
                text=r["text"]; lower=text.lower()
                support="HIGH" if r["score"]>=0.35 else ("MEDIUM" if r["score"]>=0.15 else "LOW")
                hypothesis="Possible bearing degradation or misalignment" if any(k in lower for k in ["bearing","vibration","alignment"]) else "Possible motor overload/current imbalance"
                evidence.append(EvidenceItem(source="Local RAG",document=r["document"],page=r.get("page"),relevant_passage=text,supported_hypothesis=hypothesis,support_level=support,score=max(0.0,min(1.0,r["score"]))))
        state.evidence=evidence; step("Evidence Agent","COMPLETED",f"Retrieved {len(evidence)} evidence item(s)")
        # Maintenance
        step("Maintenance Planner Agent","RUNNING","Building maintenance plan")
        plan=None
        if mode=="LIVE":
            try:
                raw=run_crew_agent(client,"Maintenance Planner Agent","Build a safe evidence-grounded inspection plan.","Plan inspection before repair and include safety controls.",_prompt("maintenance").format(hypotheses=json.dumps([h.model_dump() for h in state.electrical_hypotheses+state.mechanical_hypotheses]),evidence=json.dumps([e.model_dump() for e in evidence])),"JSON object matching the maintenance plan schema.")
                plan=MaintenancePlan.model_validate(client.parse_json(raw))
            except Exception as e: state.errors.append(f"Maintenance live call failed: {e}")
        if plan is None:
            plan=MaintenancePlan(immediate_actions=["Follow site lockout/tagout procedures before intervention.","Verify motor current and phase balance using approved procedures."],inspection_sequence=["Review telemetry and alarm history.","Check motor current and phase balance.","Inspect bearing temperature and vibration.","Inspect coupling alignment.","Verify lubrication condition."],repair_actions=["Repair or replace confirmed defective components only after qualified inspection."],required_parts=["Bearing kit if inspection confirms bearing damage.","Approved coupling components if alignment inspection identifies damage."],required_tools=["Clamp meter","Vibration meter","Temperature measurement device","Alignment tools"],estimated_downtime_hours=2.0,priority="High",safety_notes=["Follow site lockout/tagout procedures.","Consult qualified personnel before intervention."])
        state.maintenance_plan=plan; step("Maintenance Planner Agent","COMPLETED",f"Priority {plan.priority}")
        # Manager / deterministic impact
        step("Plant Manager Agent","RUNNING","Calculating production impact")
        production_rate=100.0
        if parts_df is not None and "production_rate_units_per_hour" in parts_df.columns:
            try: production_rate=float(parts_df["production_rate_units_per_hour"].iloc[0])
            except Exception: pass
        impact=calculate_production_impact(production_rate,plan.estimated_downtime_hours,"Planned maintenance window")
        state.production_impact=ProductionImpact.model_validate(impact)
        if mode=="LIVE":
            try: run_crew_agent(client,"Plant Manager Agent","Explain deterministic production impact and scheduling considerations.","Never invent production or financial values; explain only supplied numbers.",_prompt("manager").format(impact=json.dumps(impact),plan=json.dumps(plan.model_dump())),"A concise operational explanation.")
            except Exception as e: state.errors.append(f"Manager live call failed: {e}")
        step("Plant Manager Agent","COMPLETED",f"Estimated impact {impact['estimated_production_impact_units']} units")
        step("Verification Layer","RUNNING","Checking schema, evidence, arithmetic, safety and confidence")
        state.verification=validate_incident(state); state.final_status=state.verification.status; step("Verification Layer","COMPLETED",state.verification.status)
        return state
    except Exception as e:
        state.errors.append(str(e)); state.final_status="FAIL"; state.verification=validate_incident(state); return state
