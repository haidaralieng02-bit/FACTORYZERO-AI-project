from core.schemas import IncidentState, ProductionImpact, MaintenancePlan, Hypothesis, EvidenceItem
from core.validators import validate_incident

def test_validator_pass():
    s=IncidentState(incident_id="i",machine_id="m",machine_name="n",mode="DEMO",source_files=["manual.txt"],electrical_hypotheses=[Hypothesis(hypothesis="h",confidence=.5,reasoning="r",supporting_observations=["o"])],production_impact=ProductionImpact(production_rate_units_per_hour=100,downtime_hours=2,estimated_production_impact_units=200),maintenance_plan=MaintenancePlan(immediate_actions=["Follow site lockout/tagout procedures."],inspection_sequence=["inspect"],estimated_downtime_hours=2))
    s.evidence=[EvidenceItem(source="x",document="manual.txt",page=1,relevant_passage="evidence",supported_hypothesis="h",support_level="HIGH",score=.8)]
    v=validate_incident(s); assert v.status=="PASS"

def test_validator_arithmetic_mismatch():
    s=IncidentState(incident_id="i",machine_id="m",machine_name="n",production_impact=ProductionImpact(production_rate_units_per_hour=100,downtime_hours=2,estimated_production_impact_units=10))
    v=validate_incident(s); assert v.status in {"REVISE","FAIL"}
