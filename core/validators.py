from __future__ import annotations
from typing import Any
from pathlib import Path
from core.schemas import IncidentState, VerificationResult

def validate_incident(state: IncidentState) -> VerificationResult:
    errors=[]; warnings=[]; checks={}
    try: state.model_validate(state.model_dump()); checks["schema"]=True
    except Exception as e: checks["schema"]=False; errors.append(f"Schema validation failed: {e}")
    valid_docs={Path(x).name for x in state.source_files}
    citation_ok=True
    for item in state.evidence:
        if valid_docs and item.document not in valid_docs: citation_ok=False
        if not item.relevant_passage.strip(): citation_ok=False
    checks["citation"]=citation_ok
    if not citation_ok: errors.append("One or more evidence citations do not map to supplied documents or have empty passages.")
    evidence_ok=all(bool(h.supporting_observations) or not h.evidence_needed for h in state.electrical_hypotheses+state.mechanical_hypotheses)
    checks["evidence"]=evidence_ok
    if not evidence_ok: warnings.append("Some hypotheses have limited direct observation support.")
    arithmetic_ok=True
    if state.production_impact:
        p=state.production_impact
        expected=round(p.production_rate_units_per_hour*p.downtime_hours,2)
        arithmetic_ok=abs(expected-p.estimated_production_impact_units)<0.01
        if not arithmetic_ok: errors.append("Production impact arithmetic mismatch.")
    checks["arithmetic"]=arithmetic_ok
    safety_ok=True
    if state.maintenance_plan:
        blob=" ".join(state.maintenance_plan.immediate_actions+state.maintenance_plan.repair_actions).lower()
        unsafe_terms=["bypass safety", "defeat emergency", "disable protection", "work energized"]
        safety_ok=not any(x in blob for x in unsafe_terms)
        if not safety_ok: errors.append("Unsafe instruction detected in maintenance plan.")
    checks["safety"]=safety_ok
    confidence_ok=all(0<=h.confidence<=1 for h in state.electrical_hypotheses+state.mechanical_hypotheses)
    checks["confidence"]=confidence_ok
    if not confidence_ok: errors.append("Confidence values must be between 0 and 1.")
    status="PASS" if not errors else ("REVISE" if not any(not v for v in checks.values()) else "FAIL")
    return VerificationResult(status=status,errors=errors,warnings=warnings,checks=checks)
