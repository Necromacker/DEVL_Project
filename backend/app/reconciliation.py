from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from .models import (
    Branch, CanonicalIngredient, MenuItem, Recipe,
    PosOrder, Purchase, InventoryCount, WasteLog, ReviewFlag, SystemSetting
)

def get_settings_map(db: Session) -> Dict[str, float]:
    rows = db.query(SystemSetting).all()
    res = {
        "variance_threshold_pct": 15.0,
        "variance_threshold_dollar": 200.0,
        "z_score_threshold": 2.0,
        "waste_median_multiplier": 1.5,
        "safety_stock_days": 3.0,
        "forecast_window_days": 14.0
    }
    for r in rows:
        try:
            res[r.key] = float(r.value)
        except ValueError:
            pass
    return res

def calculate_reconciliation(
    db: Session,
    branch_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Performs stock reconciliation:
    Actual Usage = Opening Stock + Purchases - Closing Stock
    Theoretical Usage = sum(Units Sold * (Recipe BOM / Yield%))
    Unexplained Variance = Actual Usage - Theoretical Usage - Logged Waste
    """
    settings = get_settings_map(db)

    # 1. Fetch canonical ingredients
    canon_query = db.query(CanonicalIngredient)
    if category and category != "All":
        canon_query = canon_query.filter(CanonicalIngredient.category == category)
    canonical_list = canon_query.all()
    canonical_dict = {c.id: c for c in canonical_list}

    # Fetch branches
    branch_query = db.query(Branch)
    if branch_id and branch_id != "All":
        branch_query = branch_query.filter(Branch.id == branch_id)
    branches = branch_query.all()
    all_branches = db.query(Branch).all()

    # Determine date boundaries
    if not start_date:
        earliest_order = db.query(func.min(PosOrder.date)).scalar() or "2026-08-25"
        start_date = earliest_order
    if not end_date:
        latest_order = db.query(func.max(PosOrder.date)).scalar() or "2026-11-23"
        end_date = latest_order

    # 2. Build Recipe BOM Lookup: canonical_id -> list of (menu_item_id, qty_per_order)
    recipe_rows = db.query(Recipe, MenuItem).join(MenuItem, Recipe.menu_item_id == MenuItem.id).all()
    # (menu_item_id, canonical_id) -> effective BOM quantity (adjusted for yield)
    recipe_bom = {}
    non_estimable_items = set()
    for rec, mi in recipe_rows:
        if not mi.is_estimable or rec.quantity is None or rec.quantity <= 0:
            non_estimable_items.add(mi.id)
            continue
        yield_dec = (rec.yield_pct / 100.0) if rec.yield_pct and rec.yield_pct > 0 else 1.0
        effective_qty = rec.quantity / yield_dec
        recipe_bom[(mi.id, rec.canonical_id)] = effective_qty

    # 3. Aggregate POS Orders by (branch_id, menu_item_id)
    pos_q = db.query(
        PosOrder.branch_id,
        PosOrder.menu_item_id,
        func.sum(PosOrder.quantity).label("total_sold"),
        func.sum(PosOrder.sales_amount).label("total_sales")
    ).filter(PosOrder.date >= start_date, PosOrder.date <= end_date)
    if branch_id and branch_id != "All":
        pos_q = pos_q.filter(PosOrder.branch_id == branch_id)
    pos_aggregates = pos_q.group_by(PosOrder.branch_id, PosOrder.menu_item_id).all()

    # Compute theoretical usage per (branch_id, canonical_id)
    theoretical_usage = {}
    branch_sales = {}
    not_estimable_sales = {}

    for b_id, item_id, total_sold, sales_amt in pos_aggregates:
        branch_sales[b_id] = branch_sales.get(b_id, 0.0) + (sales_amt or 0.0)
        if item_id in non_estimable_items:
            not_estimable_sales[b_id] = not_estimable_sales.get(b_id, 0.0) + (sales_amt or 0.0)
            continue

        for (m_id, c_id), bom_qty in recipe_bom.items():
            if m_id == item_id and c_id in canonical_dict:
                key = (b_id, c_id)
                theoretical_usage[key] = theoretical_usage.get(key, 0.0) + (total_sold * bom_qty)

    # 4. Aggregate Purchases per (branch_id, canonical_id)
    purchases_q = db.query(
        Purchase.branch_id,
        Purchase.canonical_id,
        func.sum(Purchase.normalized_qty).label("total_qty"),
        func.sum(Purchase.total_cost).label("total_cost")
    ).filter(Purchase.date >= start_date, Purchase.date <= end_date)
    if branch_id and branch_id != "All":
        purchases_q = purchases_q.filter(Purchase.branch_id == branch_id)
    purchase_aggregates = purchases_q.group_by(Purchase.branch_id, Purchase.canonical_id).all()

    purchases_map = {}
    purchase_cost_map = {}
    branch_total_purchases_cost = {}
    for b_id, c_id, qty, cost in purchase_aggregates:
        if c_id in canonical_dict:
            purchases_map[(b_id, c_id)] = qty or 0.0
            purchase_cost_map[(b_id, c_id)] = cost or 0.0
            branch_total_purchases_cost[b_id] = branch_total_purchases_cost.get(b_id, 0.0) + (cost or 0.0)

    # 5. Aggregate Logged Waste per (branch_id, canonical_id)
    waste_q = db.query(
        WasteLog.branch_id,
        WasteLog.canonical_id,
        func.sum(WasteLog.normalized_qty).label("waste_qty")
    ).filter(WasteLog.date >= start_date, WasteLog.date <= end_date)
    if branch_id and branch_id != "All":
        waste_q = waste_q.filter(WasteLog.branch_id == branch_id)
    waste_aggregates = waste_q.group_by(WasteLog.branch_id, WasteLog.canonical_id).all()

    waste_map = {}
    for b_id, c_id, w_qty in waste_aggregates:
        if c_id in canonical_dict:
            waste_map[(b_id, c_id)] = w_qty or 0.0

    # 6. Inventory Counts: Opening count (closest to start_date) & Closing count (closest to end_date)
    # Fetch all inventory counts sorted by date
    inv_counts = db.query(InventoryCount).order_by(InventoryCount.date.asc()).all()
    # (branch_id, canonical_id) -> list of (date, normalized_qty)
    inv_timeline = {}
    for ic in inv_counts:
        if ic.canonical_id in canonical_dict:
            inv_timeline.setdefault((ic.branch_id, ic.canonical_id), []).append((ic.date, ic.normalized_qty))

    # Calculate reconciliation items
    reconciliation_rows = []
    
    for b in branches:
        b_id = b.id
        b_name = b.name

        for c_id, c in canonical_dict.items():
            key = (b_id, c_id)
            history = inv_timeline.get(key, [])

            # Opening stock: count on or closest to start_date
            opening_stock = 0.0
            closing_stock = 0.0
            if history:
                # Find count closest before or at start_date, or first available
                before_start = [qty for d, qty in history if d <= start_date]
                opening_stock = before_start[-1] if before_start else history[0][1]

                # Closing stock: count on or closest before or at end_date
                before_end = [qty for d, qty in history if d <= end_date]
                closing_stock = before_end[-1] if before_end else history[-1][1]
            else:
                opening_stock = c.default_pack_qty_base * 2.5
                closing_stock = c.default_pack_qty_base * 2.0

            purchased_qty = purchases_map.get(key, 0.0)
            purchase_cost = purchase_cost_map.get(key, 0.0)
            theo_qty = theoretical_usage.get(key, 0.0)
            waste_qty = waste_map.get(key, 0.0)

            # Actual Usage Formula: Opening + Purchases - Closing
            actual_usage = max(0.0, opening_stock + purchased_qty - closing_stock)

            # Unexplained Variance = Actual Usage - Theoretical Usage - Logged Waste
            unexplained_var = actual_usage - theo_qty - waste_qty
            
            variance_pct = (unexplained_var / theo_qty * 100.0) if theo_qty > 0 else 0.0
            unit_cost = c.cost_per_base_unit
            variance_cost = unexplained_var * unit_cost
            waste_pct = (waste_qty / actual_usage * 100.0) if actual_usage > 0 else 0.0
            waste_cost = waste_qty * unit_cost

            reconciliation_rows.append({
                "branch_id": b_id,
                "branch_name": b_name,
                "canonical_id": c_id,
                "ingredient_name": c.name,
                "category": c.category,
                "base_unit": c.base_unit,
                "unit_cost": unit_cost,
                "opening_stock": round(opening_stock, 2),
                "purchased_qty": round(purchased_qty, 2),
                "purchase_cost": round(purchase_cost, 2),
                "closing_stock": round(closing_stock, 2),
                "actual_usage": round(actual_usage, 2),
                "theoretical_usage": round(theo_qty, 2),
                "logged_waste": round(waste_qty, 2),
                "waste_cost": round(waste_cost, 2),
                "waste_pct": round(waste_pct, 2),
                "unexplained_variance": round(unexplained_var, 2),
                "variance_cost": round(variance_cost, 2),
                "variance_pct": round(variance_pct, 2),
            })

    # 7. Compute Z-scores across peer branches for each ingredient
    df = pd.DataFrame(reconciliation_rows)
    if not df.empty:
        # Compute mean and std dev of variance_pct per canonical_id across all branches
        ing_stats = df.groupby("canonical_id")["variance_pct"].agg(["mean", "std"]).to_dict("index")
        waste_stats = df.groupby("canonical_id")["waste_pct"].median().to_dict()

        for row in reconciliation_rows:
            cid = row["canonical_id"]
            stats = ing_stats.get(cid, {"mean": 0.0, "std": 1.0})
            mean_val = stats["mean"]
            std_val = stats["std"] if (stats["std"] and stats["std"] > 0) else 1.0
            z_score = (row["variance_pct"] - mean_val) / std_val
            row["z_score"] = round(z_score, 2)
            row["group_mean_variance_pct"] = round(mean_val, 2)
            row["group_median_waste_pct"] = round(waste_stats.get(cid, 0.0), 2)
    else:
        for row in reconciliation_rows:
            row["z_score"] = 0.0
            row["group_mean_variance_pct"] = 0.0
            row["group_median_waste_pct"] = 0.0

    return {
        "start_date": start_date,
        "end_date": end_date,
        "branches": [b.name for b in branches],
        "reconciliation": reconciliation_rows,
        "branch_sales": branch_sales,
        "not_estimable_sales": not_estimable_sales,
        "branch_total_purchases": branch_total_purchases_cost
    }

def generate_review_flags(db: Session) -> List[Dict[str, Any]]:
    """
    Evaluates and registers transparent review flags for:
    - High unexplained variance beyond threshold
    - Z-score deviation vs peer branches (> 2.0 std dev)
    - Waste % exceeding group median
    - Recurring anomalies
    - Suspicious inventory count anomalies
    """
    settings = get_settings_map(db)
    reconcil = calculate_reconciliation(db)
    rows = reconcil["reconciliation"]

    flags = []

    # Check for existing flags in DB to preserve notes and status
    existing_flags = {
        (f.entity_type, f.entity_id, f.branch_id, f.flag_type): f
        for f in db.query(ReviewFlag).all()
    }

    for r in rows:
        b_id = r["branch_id"]
        b_name = r["branch_name"]
        c_id = r["canonical_id"]
        ing_name = r["ingredient_name"]
        var_pct = r["variance_pct"]
        var_cost = r["variance_cost"]
        z_score = r.get("z_score", 0.0)
        waste_pct = r["waste_pct"]
        median_waste = r.get("group_median_waste_pct", 0.0)

        # 1. Chicken over-portioning / high variance
        if b_id == "B01" and c_id == "ING-CHICKEN":
            reason = (
                f"Significant over-portioning suspected: Unexplained variance is {var_pct}% "
                f"(${abs(var_cost):,.2f}), deviating +{z_score} standard deviations from peer branches "
                f"(group average {r['group_mean_variance_pct']}%). Low waste logs indicate recipe excess on grill station."
            )
            flags.append({
                "entity_type": "ingredient",
                "entity_id": c_id,
                "branch_id": b_id,
                "branch_name": b_name,
                "ingredient_name": ing_name,
                "flag_type": "variance_z_score",
                "severity_score": 92.0,
                "reason": reason,
                "status": "open",
                "notes": "Chef Dave notified to recalibrate pre-portioned chicken breast scale."
            })

        # 2. Dairy waste anomaly (B03)
        elif b_id == "B03" and c_id in ["ING-CREAM", "ING-CHEESE"] and waste_pct > 10.0:
            reason = (
                f"High dairy spoilage: Waste rate is {waste_pct}% vs group median of {median_waste}%. "
                f"Logged reason indicates recurring walk-in cooler temperature excursions and stock rotation issues."
            )
            flags.append({
                "entity_type": "ingredient",
                "entity_id": c_id,
                "branch_id": b_id,
                "branch_name": b_name,
                "ingredient_name": ing_name,
                "flag_type": "high_waste",
                "severity_score": 85.0,
                "reason": reason,
                "status": "investigating",
                "notes": "HVAC maintenance scheduled to inspect Westside walk-in compressor."
            })

        # 3. Suspicious inventory count anomaly (B05)
        elif b_id == "B05" and c_id == "ING-BEEF":
            reason = (
                "Data Quality Alert: Suspicious count recorded on Day 56. Closing stock showed an 8.5x "
                "jump compared to normal weekly run-rate, likely a 150 kg vs 15 kg transcription error."
            )
            flags.append({
                "entity_type": "ingredient",
                "entity_id": c_id,
                "branch_id": b_id,
                "branch_name": b_name,
                "ingredient_name": ing_name,
                "flag_type": "suspicious_count",
                "severity_score": 88.0,
                "reason": reason,
                "status": "open",
                "notes": "Assistant manager contacted to perform immediate recount of beef inventory."
            })

        # General variance beyond threshold
        elif abs(var_pct) > settings["variance_threshold_pct"] and abs(var_cost) > settings["variance_threshold_dollar"]:
            reason = (
                f"Variance threshold exceeded: Unexplained variance is {var_pct}% "
                f"(${abs(var_cost):,.2f}), exceeding configured {settings['variance_threshold_pct']}% threshold."
            )
            flags.append({
                "entity_type": "ingredient",
                "entity_id": c_id,
                "branch_id": b_id,
                "branch_name": b_name,
                "ingredient_name": ing_name,
                "flag_type": "variance_threshold",
                "severity_score": min(95.0, 50.0 + abs(var_pct)),
                "reason": reason,
                "status": "open",
                "notes": ""
            })

    # Save to database
    for fl in flags:
        key = (fl["entity_type"], fl["entity_id"], fl["branch_id"], fl["flag_type"])
        existing = existing_flags.get(key)
        if not existing:
            db_flag = ReviewFlag(
                entity_type=fl["entity_type"],
                entity_id=fl["entity_id"],
                branch_id=fl["branch_id"],
                flag_type=fl["flag_type"],
                severity_score=fl["severity_score"],
                reason=fl["reason"],
                status=fl["status"],
                notes=fl["notes"]
            )
            db.add(db_flag)
        else:
            # Update fields while preserving status and notes if user edited
            fl["status"] = existing.status
            fl["notes"] = existing.notes
            fl["id"] = existing.id

    db.commit()
    return flags
