import math
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from .models import (
    Branch, CanonicalIngredient, MenuItem, Recipe,
    PosOrder, InventoryCount, WasteLog, Purchase, SystemSetting
)
from .reconciliation import get_settings_map

def generate_procurement_plan(
    db: Session,
    branch_id: Optional[str] = None,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Generates procurement suggestions:
    1. Forecast sales for next 7 days using 14-day day-of-week moving average.
    2. Explode forecast menu sales into ingredient demand via recipe BOM.
    3. Subtract current stock from latest inventory counts.
    4. Add waste-adjusted safety buffer.
    5. Output recommended order quantity rounded to nearest commercial pack size.
    """
    settings = get_settings_map(db)
    lead_time_days = 2
    safety_stock_days = settings.get("safety_stock_days", 3.0)

    # 1. Fetch branches and ingredients
    branches_q = db.query(Branch)
    if branch_id and branch_id != "All":
        branches_q = branches_q.filter(Branch.id == branch_id)
    branches = branches_q.all()

    canon_q = db.query(CanonicalIngredient)
    if category and category != "All":
        canon_q = canon_q.filter(CanonicalIngredient.category == category)
    canonical_list = canon_q.all()
    canonical_map = {c.id: c for c in canonical_list}

    # 2. Get recipe BOM
    recipes = db.query(Recipe, MenuItem).join(MenuItem, Recipe.menu_item_id == MenuItem.id).all()
    recipe_bom = {} # (menu_item_id, canonical_id) -> effective_qty
    for r, m in recipes:
        if m.is_estimable and r.quantity is not None and r.quantity > 0:
            yield_pct = (r.yield_pct / 100.0) if r.yield_pct and r.yield_pct > 0 else 1.0
            recipe_bom[(m.id, r.canonical_id)] = r.quantity / yield_pct

    # 3. Get recent 14-21 days of POS orders to calculate day-of-week sales
    latest_date_str = db.query(func.max(PosOrder.date)).scalar() or "2026-11-23"
    latest_dt = datetime.strptime(latest_date_str, "%Y-%m-%d")
    window_start_dt = latest_dt - timedelta(days=21)
    window_start_str = window_start_dt.strftime("%Y-%m-%d")

    pos_rows = db.query(
        PosOrder.branch_id,
        PosOrder.date,
        PosOrder.menu_item_id,
        func.sum(PosOrder.quantity).label("sold_qty")
    ).filter(
        PosOrder.date >= window_start_str,
        PosOrder.date <= latest_date_str
    ).group_by(PosOrder.branch_id, PosOrder.date, PosOrder.menu_item_id).all()

    # Calculate average daily sales per (branch_id, menu_item_id, day_of_week)
    dow_sales = {} # (branch_id, menu_item_id, dow) -> list of daily sales
    for b_id, d_str, item_id, sold in pos_rows:
        dt = datetime.strptime(d_str, "%Y-%m-%d")
        dow = dt.weekday()
        dow_sales.setdefault((b_id, item_id, dow), []).append(sold or 0)

    dow_avg_sales = {k: (sum(v) / len(v)) if v else 0.0 for k, v in dow_sales.items()}

    # 4. Forecast next 7 days sales per (branch_id, menu_item_id)
    # Next 7 days starting from latest_dt + 1
    next_7_dows = [(latest_dt + timedelta(days=i)).weekday() for i in range(1, 8)]

    forecast_item_sales = {} # (branch_id, menu_item_id) -> 7-day projected units
    for b in branches:
        for item_id, _ in db.query(MenuItem.id, MenuItem.is_estimable).all():
            proj_total = 0.0
            for dow in next_7_dows:
                avg_for_dow = dow_avg_sales.get((b.id, item_id, dow), 0.0)
                # Fallback if specific dow missing
                if avg_for_dow == 0.0:
                    any_dows = [dow_avg_sales.get((b.id, item_id, d), 0.0) for d in range(7)]
                    avg_for_dow = max(10.0, sum(any_dows) / 7.0 if sum(any_dows) > 0 else 15.0)
                proj_total += avg_for_dow
            forecast_item_sales[(b.id, item_id)] = proj_total

    # 5. Explode into 7-day projected demand per (branch_id, canonical_id)
    proj_ingredient_demand = {} # (branch_id, canonical_id) -> float
    for (b_id, item_id), units_projected in forecast_item_sales.items():
        for (m_id, c_id), eff_qty in recipe_bom.items():
            if m_id == item_id and c_id in canonical_map:
                key = (b_id, c_id)
                proj_ingredient_demand[key] = proj_ingredient_demand.get(key, 0.0) + (units_projected * eff_qty)

    # 6. Get latest inventory count for each (branch_id, canonical_id)
    # Subquery for max date per branch and ingredient
    subq = db.query(
        InventoryCount.branch_id,
        InventoryCount.canonical_id,
        func.max(InventoryCount.date).label("max_date")
    ).group_by(InventoryCount.branch_id, InventoryCount.canonical_id).subquery()

    latest_counts = db.query(
        InventoryCount.branch_id,
        InventoryCount.canonical_id,
        InventoryCount.normalized_qty
    ).join(
        subq,
        (InventoryCount.branch_id == subq.c.branch_id) &
        (InventoryCount.canonical_id == subq.c.canonical_id) &
        (InventoryCount.date == subq.c.max_date)
    ).all()

    current_stock_map = {(b_id, c_id): qty for b_id, c_id, qty in latest_counts}

    # 7. Calculate historical waste percentage per branch x ingredient
    waste_stats_q = db.query(
        WasteLog.branch_id,
        WasteLog.canonical_id,
        func.sum(WasteLog.normalized_qty).label("total_waste")
    ).group_by(WasteLog.branch_id, WasteLog.canonical_id).all()
    waste_totals = {(b_id, c_id): tw for b_id, c_id, tw in waste_stats_q}

    procurement_list = []

    for b in branches:
        b_id = b.id
        b_name = b.name

        for c_id, c in canonical_map.items():
            key = (b_id, c_id)
            projected_7d = proj_ingredient_demand.get(key, c.default_pack_qty_base * 1.5)
            curr_stock = current_stock_map.get(key, c.default_pack_qty_base * 0.8)

            daily_burn = projected_7d / 7.0
            
            # Waste rate buffer (typically 3% - 15%)
            hist_waste = waste_totals.get(key, 0.0)
            waste_rate = min(0.20, max(0.02, (hist_waste / max(1.0, projected_7d * 12.0))))
            
            # Safety stock = safety_stock_days * daily_burn * (1 + waste_buffer)
            safety_stock = daily_burn * safety_stock_days * (1.0 + waste_rate)

            # Net required demand
            net_demand = (projected_7d + safety_stock) - curr_stock

            pack_base = c.default_pack_qty_base or 1000.0
            pack_desc = c.default_pack_desc or f"Pack of 1 {c.base_unit}"
            pack_unit_cost = round(pack_base * c.cost_per_base_unit, 2)

            if net_demand <= 0:
                suggested_packs = 0
            else:
                suggested_packs = math.ceil(net_demand / pack_base)

            suggested_qty_base = suggested_packs * pack_base
            total_cost = round(suggested_packs * pack_unit_cost, 2)

            # Stock status urgency
            days_of_supply = round(curr_stock / daily_burn, 1) if daily_burn > 0 else 99.0
            if days_of_supply < 2.0:
                urgency = "Critical Low"
                urgency_color = "#FF4D4D"
            elif days_of_supply < 4.0:
                urgency = "Reorder Soon"
                urgency_color = "#FFE57F"
            else:
                urgency = "Adequate"
                urgency_color = "#CCFF00"

            procurement_list.append({
                "branch_id": b_id,
                "branch_name": b_name,
                "canonical_id": c_id,
                "ingredient_name": c.name,
                "category": c.category,
                "base_unit": c.base_unit,
                "current_stock": round(curr_stock, 1),
                "daily_run_rate": round(daily_burn, 1),
                "days_of_supply": days_of_supply,
                "projected_7day_demand": round(projected_7d, 1),
                "safety_stock_buffer": round(safety_stock, 1),
                "net_demand": round(max(0.0, net_demand), 1),
                "pack_description": pack_desc,
                "pack_size_base": pack_base,
                "pack_unit_cost": pack_unit_cost,
                "suggested_packs": suggested_packs,
                "suggested_order_qty": round(suggested_qty_base, 1),
                "estimated_order_cost": total_cost,
                "urgency": urgency,
                "urgency_color": urgency_color
            })

    # Sort critical low first, then by estimated order cost descending
    urgency_order = {"Critical Low": 0, "Reorder Soon": 1, "Adequate": 2}
    procurement_list.sort(key=lambda x: (urgency_order.get(x["urgency"], 3), -x["estimated_order_cost"]))

    return procurement_list
