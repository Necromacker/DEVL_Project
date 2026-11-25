import pytest
from backend.app.database import engine, Base, SessionLocal
from backend.app.synthetic_generator import generate_synthetic_dataset
from backend.app.reconciliation import calculate_reconciliation, generate_review_flags
from backend.app.forecasting import generate_procurement_plan

@pytest.fixture(scope="module")
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    generate_synthetic_dataset(db, force=False)
    yield db
    db.close()

def test_reconciliation_formulas(setup_test_db):
    db = setup_test_db
    res = calculate_reconciliation(db, branch_id="B01")
    assert "reconciliation" in res
    assert len(res["reconciliation"]) > 0

    chicken_rows = [r for r in res["reconciliation"] if r["canonical_id"] == "ING-CHICKEN"]
    assert len(chicken_rows) == 1
    chk = chicken_rows[0]

    # Verify reconciliation mathematical invariant:
    # Actual usage = opening + purchases - closing
    expected_actual = max(0.0, chk["opening_stock"] + chk["purchased_qty"] - chk["closing_stock"])
    assert pytest.approx(chk["actual_usage"], 0.1) == expected_actual

    # Unexplained variance = actual_usage - theoretical_usage - logged_waste
    expected_var = chk["actual_usage"] - chk["theoretical_usage"] - chk["logged_waste"]
    assert pytest.approx(chk["unexplained_variance"], 0.1) == expected_var

    # Planted anomaly verification: B01 Chicken over-portioning should yield positive variance
    assert chk["variance_pct"] > 10.0

def test_planted_anomalies_flags(setup_test_db):
    db = setup_test_db
    flags = generate_review_flags(db)
    assert len(flags) >= 3

    # Check B01 Chicken over-portion flag
    b01_chicken = [f for f in flags if f["branch_id"] == "B01" and f["entity_id"] == "ING-CHICKEN"]
    assert len(b01_chicken) >= 1
    assert "over-portioning" in b01_chicken[0]["reason"].lower()

    # Check B03 Dairy waste flag
    b03_dairy = [f for f in flags if f["branch_id"] == "B03" and f["flag_type"] == "high_waste"]
    assert len(b03_dairy) >= 1

    # Check B05 Suspicious inventory count flag
    b05_count = [f for f in flags if f["branch_id"] == "B05" and f["flag_type"] == "suspicious_count"]
    assert len(b05_count) >= 1

def test_procurement_suggestions(setup_test_db):
    db = setup_test_db
    plan = generate_procurement_plan(db, branch_id="B01")
    assert len(plan) > 0
    first = plan[0]
    assert "suggested_packs" in first
    assert "pack_description" in first
    assert "urgency" in first
    # Suggested order qty must be an exact multiple of pack size base
    if first["suggested_packs"] > 0:
        assert pytest.approx(first["suggested_order_qty"], 0.1) == (first["suggested_packs"] * first["pack_size_base"])
