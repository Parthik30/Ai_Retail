from backend.services import inventory_service as inv


def test_recommendations_include_projected_cover():
    info = inv.predict_stock_series(20, 60, months=6, demand_level='MEDIUM', lead_time_days=14, safety_stock_pct=0.2, target_cover_months=3)
    assert isinstance(info, dict)
    assert "recommended_reorders" in info
    recs = info["recommended_reorders"]
    assert isinstance(recs, list)
    if recs:
        for r in recs:
            assert r.get("projected_cover_months") == 3


def test_return_structure_keys():
    info = inv.predict_stock_series(50, 30, months=3)
    expected_keys = {"series", "stockout_months", "min_stock", "pending_deliveries", "recommended_reorders"}
    assert expected_keys.issubset(set(info.keys()))
