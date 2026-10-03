from __future__ import annotations

def calculate_production_impact(production_rate_units_per_hour: float, downtime_hours: float, maintenance_window: str = "") -> dict:
    rate=max(0.0,float(production_rate_units_per_hour)); downtime=max(0.0,float(downtime_hours))
    return {"production_rate_units_per_hour":rate,"downtime_hours":downtime,"estimated_production_impact_units":round(rate*downtime,2),"maintenance_window":maintenance_window or "Not specified","operational_notes":["Impact is a deterministic unit estimate, not a financial-loss estimate."]}
