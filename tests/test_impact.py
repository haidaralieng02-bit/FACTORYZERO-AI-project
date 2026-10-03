from tools.impact import calculate_production_impact

def test_impact():
    r=calculate_production_impact(100,2); assert r["estimated_production_impact_units"]==200
