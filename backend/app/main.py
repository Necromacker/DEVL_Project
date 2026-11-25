import os
import io
import csv
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import engine, Base, SessionLocal, get_db
from .models import (
    Branch, CanonicalIngredient, IngredientAlias, UnitConversion,
    MenuItem, Recipe, PosOrder, Purchase, InventoryCount, WasteLog,
    ReviewFlag, SystemSetting
)
from .synthetic_generator import generate_synthetic_dataset, DATA_DIR
from .reconciliation import calculate_reconciliation, generate_review_flags, get_settings_map
from .forecasting import generate_procurement_plan
from .normalizer import parse_pack_or_unit, fuzzy_match_ingredient

# Initialize database
Base.metadata.create_all(bind=engine)

# Seed if empty
with SessionLocal() as db:
    if db.query(Branch).count() == 0:
        generate_synthetic_dataset(db, force=True)

app = FastAPI(title="Branch Food Waste & Procurement Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/branches")
def list_branches(db: Session = Depends(get_db)):
    branches = db.query(Branch).all()
    return [{"id": b.id, "name": b.name, "location": b.location, "seating_capacity": b.seating_capacity} for b in branches]

@app.get("/api/categories")
def list_categories(db: Session = Depends(get_db)):
    cats = db.query(CanonicalIngredient.category).distinct().all()
    return ["All"] + [c[0] for c in cats if c[0]]

@app.get("/api/overview")
def get_overview(
    branch_id: Optional[str] = Query("All"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    category: Optional[str] = Query("All"),
    db: Session = Depends(get_db)
):
    # Perform reconciliation
    rec_res = calculate_reconciliation(db, branch_id=branch_id, start_date=start_date, end_date=end_date, category=category)
    rows = rec_res["reconciliation"]

    # Overall KPIs
    total_purchases = sum(r["purchase_cost"] for r in rows)
    total_waste_cost = sum(r["waste_cost"] for r in rows)
    total_variance_cost = sum(r["variance_cost"] for r in rows)
    
    total_sales = sum(rec_res["branch_sales"].values())
    if branch_id and branch_id != "All":
        total_sales = rec_res["branch_sales"].get(branch_id, 1.0)
    total_sales = max(total_sales, 1.0)

    food_cost_pct = round((total_purchases / total_sales) * 100.0, 1)
    waste_pct = round((total_waste_cost / max(1.0, total_purchases)) * 100.0, 1)
    variance_pct = round((total_variance_cost / max(1.0, total_purchases)) * 100.0, 1)

    # Branch rankings
    branch_summary = {}
    for r in rows:
        b_id = r["branch_id"]
        b_name = r["branch_name"]
        if b_id not in branch_summary:
            branch_summary[b_id] = {
                "branch_id": b_id,
                "branch_name": b_name,
                "total_purchases": 0.0,
                "total_waste_cost": 0.0,
                "total_variance_cost": 0.0,
                "actual_usage_cost": 0.0,
                "theoretical_cost": 0.0,
                "sales": rec_res["branch_sales"].get(b_id, 0.0),
                "items_flagged": 0
            }
        b_sum = branch_summary[b_id]
        b_sum["total_purchases"] += r["purchase_cost"]
        b_sum["total_waste_cost"] += r["waste_cost"]
        b_sum["total_variance_cost"] += r["variance_cost"]
        b_sum["actual_usage_cost"] += r["actual_usage"] * r["unit_cost"]
        b_sum["theoretical_cost"] += r["theoretical_usage"] * r["unit_cost"]
        if abs(r.get("z_score", 0)) > 1.8 or r.get("waste_pct", 0) > 8.0:
            b_sum["items_flagged"] += 1

    rankings = []
    for b_id, b_data in branch_summary.items():
        p = max(1.0, b_data["total_purchases"])
        rankings.append({
            "branch_id": b_id,
            "branch_name": b_data["branch_name"],
            "sales": round(b_data["sales"], 2),
            "purchases": round(b_data["total_purchases"], 2),
            "waste_cost": round(b_data["total_waste_cost"], 2),
            "waste_pct": round((b_data["total_waste_cost"] / p) * 100.0, 1),
            "variance_cost": round(b_data["total_variance_cost"], 2),
            "variance_pct": round((b_data["total_variance_cost"] / p) * 100.0, 1),
            "food_cost_pct": round((b_data["total_purchases"] / max(1.0, b_data["sales"])) * 100.0, 1),
            "items_flagged": b_data["items_flagged"]
        })
    rankings.sort(key=lambda x: x["variance_cost"], reverse=True)

    # Daily / Weekly trend for Segmented Pill Charts (matching the reference UI)
    # Group orders by day of week
    dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    dow_stats = {d: {"day": d, "sales": 0.0, "waste": 0.0, "purchases": 0.0, "pills": 3} for d in dow_names}
    
    # Query sample day-of-week breakdown
    pos_q = db.query(PosOrder.date, func.sum(PosOrder.sales_amount)).group_by(PosOrder.date).all()
    for d_str, amt in pos_q:
        import datetime as dt_mod
        d_obj = dt_mod.datetime.strptime(d_str, "%Y-%m-%d")
        day_name = dow_names[d_obj.weekday()]
        dow_stats[day_name]["sales"] += amt or 0.0

    # Build segmented bar pills (height in blocks 1 to 8, matching reference image!)
    max_sales = max([v["sales"] for v in dow_stats.values()]) or 1.0
    trend_bars = []
    for d in dow_names:
        item = dow_stats[d]
        total_pills = max(2, min(9, int((item["sales"] / max_sales) * 9)))
        yellow_pills = max(1, int(total_pills * 0.35))
        purple_pills = max(0, total_pills - yellow_pills)
        trend_bars.append({
            "day": d,
            "sales": round(item["sales"], 0),
            "total_blocks": total_pills,
            "yellow_blocks": yellow_pills,
            "purple_blocks": purple_pills,
            "highlight": (d == "Thu" or d == "Sat")
        })

    # Top Recent Food Items (styled like recent order items in reference image)
    top_items = [
        {"name": "Grilled Chicken Bowl", "category": "Mains", "sales": 44346, "orders": 2680, "icon": "🍗", "color": "#FFE57F"},
        {"name": "Classic Beef Burger", "category": "Burgers", "sales": 32900, "orders": 2193, "icon": "🍔", "color": "#D8B4FE"},
        {"name": "Margherita Pizza", "category": "Pizza", "sales": 28450, "orders": 1962, "icon": "🍕", "color": "#CCFF00"},
        {"name": "Loaded Potato Fries", "category": "Sides", "sales": 15800, "orders": 1663, "icon": "🍟", "color": "#FFE57F"},
        {"name": "Creamy Chicken Alfredo", "category": "Pasta", "sales": 26100, "orders": 1450, "icon": "🍝", "color": "#D8B4FE"},
    ]

    return {
        "kpis": {
            "total_purchases": round(total_purchases, 2),
            "total_waste": round(total_waste_cost, 2),
            "waste_pct": waste_pct,
            "unexplained_variance": round(total_variance_cost, 2),
            "variance_pct": variance_pct,
            "total_sales": round(total_sales, 2),
            "food_cost_pct": food_cost_pct,
            "active_branches": len(rankings)
        },
        "branch_rankings": rankings,
        "trend_bars": trend_bars,
        "top_items": top_items,
        "date_range": {
            "start": rec_res["start_date"],
            "end": rec_res["end_date"]
        }
    }

@app.get("/api/branch-view")
def get_branch_view(
    branch_id: str = Query("B01"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    category: Optional[str] = Query("All"),
    db: Session = Depends(get_db)
):
    rec_res = calculate_reconciliation(db, branch_id=branch_id, start_date=start_date, end_date=end_date, category=category)
    rows = rec_res["reconciliation"]

    # Weekly timeline for selected branch
    # Aggregate purchases, waste, and theoretical use by week
    branch = db.query(Branch).filter(Branch.id == branch_id).first()

    return {
        "branch": {
            "id": branch.id if branch else branch_id,
            "name": branch.name if branch else "Selected Branch",
            "location": branch.location if branch else "",
            "capacity": branch.seating_capacity if branch else 100
        },
        "ingredients": rows,
        "total_ingredients_monitored": len(rows),
        "total_spend": round(sum(r["purchase_cost"] for r in rows), 2),
        "total_waste_cost": round(sum(r["waste_cost"] for r in rows), 2),
        "total_variance_cost": round(sum(r["variance_cost"] for r in rows), 2),
    }

@app.get("/api/menu-items")
def get_menu_items(db: Session = Depends(get_db)):
    # Calculate recipe variance contribution & sales
    items = db.query(MenuItem).all()
    recipes = db.query(Recipe).all()

    # Sales volume
    sales_q = db.query(
        PosOrder.menu_item_id,
        func.sum(PosOrder.quantity).label("units_sold"),
        func.sum(PosOrder.sales_amount).label("sales_val")
    ).group_by(PosOrder.menu_item_id).all()
    sales_map = {m_id: (u, s) for m_id, u, s in sales_q}

    result = []
    for item in items:
        units_sold, total_sales = sales_map.get(item.id, (0, 0.0))
        item_recipes = [r for r in recipes if r.menu_item_id == item.id]

        bom_list = []
        est_cost_per_serving = 0.0
        for r in item_recipes:
            canon = db.query(CanonicalIngredient).filter(CanonicalIngredient.id == r.canonical_id).first()
            cost_unit = canon.cost_per_base_unit if canon else 0.01
            qty_needed = (r.quantity or 0.0) / ((r.yield_pct or 100.0) / 100.0)
            ing_cost = qty_needed * cost_unit
            est_cost_per_serving += ing_cost

            bom_list.append({
                "id": r.id,
                "canonical_id": r.canonical_id,
                "ingredient_name": r.raw_ingredient_name,
                "quantity": r.quantity,
                "unit": r.unit,
                "yield_pct": r.yield_pct,
                "trim_loss_pct": r.trim_loss_pct,
                "cost_contribution": round(ing_cost, 3)
            })

        margin_pct = round(((item.price - est_cost_per_serving) / max(0.01, item.price)) * 100.0, 1) if item.is_estimable else 0.0

        result.append({
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "price": item.price,
            "is_estimable": item.is_estimable,
            "flag_reason": item.flag_reason,
            "units_sold": units_sold,
            "total_sales": round(total_sales, 2),
            "cost_per_serving": round(est_cost_per_serving, 2),
            "margin_pct": margin_pct,
            "ingredients_count": len(bom_list),
            "bom": bom_list
        })

    result.sort(key=lambda x: x["total_sales"], reverse=True)
    return result

@app.get("/api/procurement")
def get_procurement(
    branch_id: Optional[str] = Query("All"),
    category: Optional[str] = Query("All"),
    db: Session = Depends(get_db)
):
    plan = generate_procurement_plan(db, branch_id=branch_id, category=category)
    return plan

@app.get("/api/review-queue")
def get_review_queue(
    status: Optional[str] = Query("All"),
    db: Session = Depends(get_db)
):
    # Ensure flags are up to date
    generate_review_flags(db)
    
    query = db.query(ReviewFlag)
    if status and status != "All":
        query = query.filter(ReviewFlag.status == status)
    
    flags = query.order_by(ReviewFlag.severity_score.desc()).all()
    
    # Enrich branch name
    branches = {b.id: b.name for b in db.query(Branch).all()}
    res = []
    for f in flags:
        res.append({
            "id": f.id,
            "entity_type": f.entity_type,
            "entity_id": f.entity_id,
            "branch_id": f.branch_id,
            "branch_name": branches.get(f.branch_id, f.branch_id),
            "flag_type": f.flag_type,
            "severity_score": f.severity_score,
            "reason": f.reason,
            "status": f.status,
            "notes": f.notes,
            "created_at": f.created_at.strftime("%Y-%m-%d %H:%M") if f.created_at else ""
        })
    return res

@app.post("/api/review-queue/{flag_id}")
def update_review_flag(
    flag_id: int,
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    flag = db.query(ReviewFlag).filter(ReviewFlag.id == flag_id).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    
    if "status" in payload:
        flag.status = payload["status"]
    if "notes" in payload:
        flag.notes = payload["notes"]
        
    db.commit()
    return {"status": "success", "id": flag_id}

@app.get("/api/data-quality")
def get_data_quality(db: Session = Depends(get_db)):
    # 1. Unmapped or low confidence aliases
    aliases = db.query(IngredientAlias).all()
    canon_map = {c.id: c.name for c in db.query(CanonicalIngredient).all()}
    
    unmapped = []
    for a in aliases:
        if not a.is_confirmed or not a.canonical_id or a.confidence < 80:
            # Run fuzzy match
            matched_id, score, matched_term = fuzzy_match_ingredient(a.alias_name, {}, canon_map)
            unmapped.append({
                "id": a.id,
                "alias_name": a.alias_name,
                "canonical_id": a.canonical_id or matched_id,
                "suggested_name": canon_map.get(matched_id, "Unknown"),
                "confidence": a.confidence if a.canonical_id else score,
                "is_confirmed": a.is_confirmed,
                "source": a.source
            })

    # 2. Recipes missing or not estimable
    missing_recipes = []
    items = db.query(MenuItem).filter(MenuItem.is_estimable == False).all()
    for it in items:
        missing_recipes.append({
            "menu_item_id": it.id,
            "menu_item_name": it.name,
            "category": it.category,
            "issue": it.flag_reason or "Missing recipe BOM"
        })

    # 3. Suspicious inventory counts (negative stock or 5x jump)
    suspicious_counts = []
    flags = db.query(ReviewFlag).filter(ReviewFlag.flag_type == "suspicious_count").all()
    branches = {b.id: b.name for b in db.query(Branch).all()}
    for f in flags:
        suspicious_counts.append({
            "id": f.id,
            "branch_id": f.branch_id,
            "branch_name": branches.get(f.branch_id, f.branch_id),
            "ingredient_id": f.entity_id,
            "reason": f.reason,
            "status": f.status
        })

    return {
        "unmapped_aliases": unmapped,
        "missing_recipes": missing_recipes,
        "suspicious_counts": suspicious_counts,
        "canonical_ingredients": [{"id": c.id, "name": c.name} for c in db.query(CanonicalIngredient).all()]
    }

@app.post("/api/data-quality/alias/confirm")
def confirm_alias(payload: Dict[str, Any], db: Session = Depends(get_db)):
    alias_id = payload.get("alias_id")
    canonical_id = payload.get("canonical_id")
    
    alias = db.query(IngredientAlias).filter(IngredientAlias.id == alias_id).first()
    if not alias:
        raise HTTPException(status_code=404, detail="Alias not found")
    
    alias.canonical_id = canonical_id
    alias.confidence = 100.0
    alias.is_confirmed = True
    alias.source = "manual"
    db.commit()
    return {"status": "success", "alias_name": alias.alias_name}

@app.get("/api/settings")
def get_settings(db: Session = Depends(get_db)):
    settings = get_settings_map(db)
    aliases = db.query(IngredientAlias).all()
    canon_map = {c.id: c.name for c in db.query(CanonicalIngredient).all()}
    
    alias_list = [{
        "id": a.id,
        "alias_name": a.alias_name,
        "canonical_id": a.canonical_id,
        "canonical_name": canon_map.get(a.canonical_id, "Unmapped"),
        "confidence": a.confidence,
        "is_confirmed": a.is_confirmed
    } for a in aliases]

    return {
        "settings": settings,
        "aliases": alias_list,
        "canonical_catalog": [{"id": c.id, "name": c.name, "category": c.category, "base_unit": c.base_unit} for c in db.query(CanonicalIngredient).all()]
    }

@app.post("/api/settings")
def update_settings(payload: Dict[str, Any], db: Session = Depends(get_db)):
    for k, v in payload.items():
        st = db.query(SystemSetting).filter(SystemSetting.key == k).first()
        if st:
            st.value = str(v)
        else:
            db.add(SystemSetting(key=k, value=str(v)))
    db.commit()
    return {"status": "success"}

@app.post("/api/reset-data")
def reset_synthetic_data(db: Session = Depends(get_db)):
    generate_synthetic_dataset(db, force=True)
    return {"status": "success", "message": "Synthetic dataset re-generated with 6 branches and 90 days."}

@app.get("/api/export/{table_name}")
def export_csv(table_name: str, db: Session = Depends(get_db)):
    file_map = {
        "pos_orders": ("pos_orders.csv", PosOrder),
        "recipes": ("recipes.csv", Recipe),
        "purchases": ("purchases.csv", Purchase),
        "inventory_counts": ("inventory_counts.csv", InventoryCount),
        "waste_logs": ("waste_logs.csv", WasteLog)
    }
    if table_name not in file_map:
        raise HTTPException(status_code=400, detail="Invalid table name")

    fname, model = file_map[table_name]
    filepath = os.path.join(DATA_DIR, fname)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return StreamingResponse(
            io.StringIO(content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={fname}"}
        )
    else:
        raise HTTPException(status_code=404, detail="File not found")

# Serve frontend build if available
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
