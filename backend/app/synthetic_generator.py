import os
import random
import csv
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session
from .models import (
    Branch, CanonicalIngredient, IngredientAlias, UnitConversion,
    MenuItem, Recipe, PosOrder, Purchase, InventoryCount, WasteLog,
    ReviewFlag, SystemSetting
)
from .normalizer import (
    parse_pack_or_unit, fuzzy_match_ingredient,
    MASS_CONVERSIONS, VOLUME_CONVERSIONS, COUNT_CONVERSIONS
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 6 Branches
BRANCHES = [
    {"id": "B01", "name": "Downtown Bistro", "location": "Financial District", "seating_capacity": 120},
    {"id": "B02", "name": "Uptown Cafe", "location": "Midtown Avenue", "seating_capacity": 85},
    {"id": "B03", "name": "Westside Grill", "location": "West Marina", "seating_capacity": 140},
    {"id": "B04", "name": "North End Diner", "location": "North Suburbs", "seating_capacity": 95},
    {"id": "B05", "name": "Eastside Kitchen", "location": "Arts District", "seating_capacity": 110},
    {"id": "B06", "name": "Harbor Point Brasserie", "location": "Pier 4", "seating_capacity": 160},
]

# Canonical Ingredients
CANONICAL_INGREDIENTS = [
    {
        "id": "ING-CHICKEN", "name": "Boneless Chicken Breast", "category": "Meat & Poultry",
        "base_unit": "g", "density_g_per_ml": 1.0, "default_pack_desc": "case of 4 x 2.5kg",
        "default_pack_qty_base": 10000.0, "cost_per_base_unit": 0.0075, "standard_yield_pct": 95.0
    },
    {
        "id": "ING-BEEF", "name": "Ground Beef 80/20", "category": "Meat & Poultry",
        "base_unit": "g", "density_g_per_ml": 1.0, "default_pack_desc": "box of 10 x 1kg",
        "default_pack_qty_base": 10000.0, "cost_per_base_unit": 0.0090, "standard_yield_pct": 88.0
    },
    {
        "id": "ING-TOMATO", "name": "Roma Tomato", "category": "Produce",
        "base_unit": "g", "density_g_per_ml": 1.0, "default_pack_desc": "crate of 20 lb",
        "default_pack_qty_base": 9071.85, "cost_per_base_unit": 0.0028, "standard_yield_pct": 90.0
    },
    {
        "id": "ING-ONION", "name": "Yellow Onion", "category": "Produce",
        "base_unit": "g", "density_g_per_ml": 1.0, "default_pack_desc": "bag of 25 kg",
        "default_pack_qty_base": 25000.0, "cost_per_base_unit": 0.0018, "standard_yield_pct": 88.0
    },
    {
        "id": "ING-POTATO", "name": "Russet Potato", "category": "Produce",
        "base_unit": "g", "density_g_per_ml": 1.0, "default_pack_desc": "bag of 50 lb",
        "default_pack_qty_base": 22679.6, "cost_per_base_unit": 0.0015, "standard_yield_pct": 85.0
    },
    {
        "id": "ING-BELLPEPPER", "name": "Green Bell Pepper", "category": "Produce",
        "base_unit": "g", "density_g_per_ml": 1.0, "default_pack_desc": "box of 5 kg",
        "default_pack_qty_base": 5000.0, "cost_per_base_unit": 0.0035, "standard_yield_pct": 85.0
    },
    {
        "id": "ING-CREAM", "name": "Heavy Cream 36%", "category": "Dairy",
        "base_unit": "ml", "density_g_per_ml": 1.01, "default_pack_desc": "tub of 4 l",
        "default_pack_qty_base": 4000.0, "cost_per_base_unit": 0.0055, "standard_yield_pct": 98.0
    },
    {
        "id": "ING-CHEESE", "name": "Mozzarella Cheese", "category": "Dairy",
        "base_unit": "g", "density_g_per_ml": 1.0, "default_pack_desc": "case of 6 x 2kg",
        "default_pack_qty_base": 12000.0, "cost_per_base_unit": 0.0085, "standard_yield_pct": 98.0
    },
    {
        "id": "ING-EGG", "name": "Large Fresh Eggs", "category": "Dairy",
        "base_unit": "each", "density_g_per_ml": 1.0, "default_pack_desc": "pack of 30 each",
        "default_pack_qty_base": 30.0, "cost_per_base_unit": 0.22, "standard_yield_pct": 98.0
    },
    {
        "id": "ING-RICE", "name": "Basmati Rice", "category": "Dry Goods",
        "base_unit": "g", "density_g_per_ml": 1.0, "default_pack_desc": "bag of 20 kg",
        "default_pack_qty_base": 20000.0, "cost_per_base_unit": 0.0025, "standard_yield_pct": 100.0
    },
    {
        "id": "ING-OIL", "name": "Extra Virgin Olive Oil", "category": "Dry Goods",
        "base_unit": "ml", "density_g_per_ml": 0.92, "default_pack_desc": "can of 5 l",
        "default_pack_qty_base": 5000.0, "cost_per_base_unit": 0.0095, "standard_yield_pct": 98.0
    },
    {
        "id": "ING-FLOUR", "name": "All-Purpose Flour", "category": "Dry Goods",
        "base_unit": "g", "density_g_per_ml": 0.60, "default_pack_desc": "bag of 25 kg",
        "default_pack_qty_base": 25000.0, "cost_per_base_unit": 0.0012, "standard_yield_pct": 100.0
    },
]

# Raw Aliases used across messy logs
RAW_ALIASES = [
    # Chicken
    ("chicken breast bnls", "ING-CHICKEN", 100.0, True),
    ("CHICKEN BONELESS", "ING-CHICKEN", 100.0, True),
    ("Murgh Boneless", "ING-CHICKEN", 90.0, True),
    ("Chicken Breast Fillet", "ING-CHICKEN", 100.0, True),
    ("chk breast", "ING-CHICKEN", 85.0, True),
    ("Boneless Chk Brst 5kg", "ING-CHICKEN", 90.0, True),
    # Tomato
    ("Tomato", "ING-TOMATO", 100.0, True),
    ("tomatoes fresh", "ING-TOMATO", 100.0, True),
    ("TOMATO-RED 1kg", "ING-TOMATO", 95.0, True),
    ("tamatar", "ING-TOMATO", 85.0, True),
    ("Roma Tom", "ING-TOMATO", 95.0, True),
    ("Fresh Tomatoes Red", "ING-TOMATO", 100.0, True),
    # Cream
    ("Heavy cream 35%", "ING-CREAM", 100.0, True),
    ("CREAM-HEAVY", "ING-CREAM", 100.0, True),
    ("malai cream", "ING-CREAM", 85.0, True),
    ("Whipping Cream 36%", "ING-CREAM", 95.0, True),
    ("Heavy Whipping Cream", "ING-CREAM", 100.0, True),
    # Cheese
    ("Mozzarella block", "ING-CHEESE", 100.0, True),
    ("SHRED MOZZARELLA", "ING-CHEESE", 100.0, True),
    ("mozz cheese 2kg", "ING-CHEESE", 95.0, True),
    ("paneer mozzarella", "ING-CHEESE", 85.0, True),
    ("Mozzarella Cheese Shredded", "ING-CHEESE", 100.0, True),
    # Onion
    ("Yellow Onions 50lb", "ING-ONION", 100.0, True),
    ("Piyaz", "ING-ONION", 85.0, True),
    ("ONION-YELLOW", "ING-ONION", 100.0, True),
    ("Onions bag", "ING-ONION", 90.0, True),
    ("Fresh Yellow Onion", "ING-ONION", 100.0, True),
    # Beef
    ("Ground Beef 80/20", "ING-BEEF", 100.0, True),
    ("Minced Beef", "ING-BEEF", 95.0, True),
    ("BEEF-GROUND-80", "ING-BEEF", 100.0, True),
    ("Keema beef", "ING-BEEF", 85.0, True),
    ("Beef Minced Prime", "ING-BEEF", 95.0, True),
    # Rice
    ("Basmati Rice 20kg", "ING-RICE", 100.0, True),
    ("Rice Basmati Extra Long", "ING-RICE", 100.0, True),
    ("RICE-BASMATI", "ING-RICE", 100.0, True),
    ("chawal basmati", "ING-RICE", 85.0, True),
    # Olive Oil
    ("Olive Oil EVOO", "ING-OIL", 100.0, True),
    ("OLIVE-OIL-EXTRA-VIRGIN 5L", "ING-OIL", 100.0, True),
    ("EV Olive Oil", "ING-OIL", 95.0, True),
    ("Cooking Olive Oil", "ING-OIL", 95.0, True),
    # Egg
    ("Egg Large White", "ING-EGG", 100.0, True),
    ("EGGS-DOZ", "ING-EGG", 100.0, True),
    ("Farm Fresh Eggs 30ct", "ING-EGG", 100.0, True),
    ("anda large", "ING-EGG", 85.0, True),
    # Potato
    ("Russet Potato 50lb", "ING-POTATO", 100.0, True),
    ("POTATO-RUSSET", "ING-POTATO", 100.0, True),
    ("Aloo Russet", "ING-POTATO", 85.0, True),
    ("Baking Potatoes", "ING-POTATO", 95.0, True),
    # Bell Pepper
    ("Green Peppers", "ING-BELLPEPPER", 95.0, True),
    ("PEPPER-BELL-GREEN", "ING-BELLPEPPER", 100.0, True),
    ("Shimla Mirch Green", "ING-BELLPEPPER", 85.0, True),
    # Flour
    ("All Purpose Flour 25kg", "ING-FLOUR", 100.0, True),
    ("FLOUR-AP", "ING-FLOUR", 100.0, True),
    ("Maida White Flour", "ING-FLOUR", 85.0, True),
    # Low confidence / unmapped aliases for data quality queue!
    ("Special White Powder Condiment", None, 35.0, False),
    ("Imported Artisan Truffle Glaze", None, 40.0, False),
]

# Menu Items & Recipes
MENU_ITEMS = [
    {"id": "ITEM-01", "name": "Grilled Chicken Bowl", "category": "Mains", "price": 16.50, "is_estimable": True, "flag_reason": None},
    {"id": "ITEM-02", "name": "Classic Beef Burger", "category": "Burgers", "price": 15.00, "is_estimable": True, "flag_reason": None},
    {"id": "ITEM-03", "name": "Creamy Chicken Alfredo", "category": "Pasta", "price": 18.00, "is_estimable": True, "flag_reason": None},
    {"id": "ITEM-04", "name": "Margherita Pizza", "category": "Pizza", "price": 14.50, "is_estimable": True, "flag_reason": None},
    {"id": "ITEM-05", "name": "Loaded Potato Fries", "category": "Sides", "price": 9.50, "is_estimable": True, "flag_reason": None},
    {"id": "ITEM-06", "name": "Butter Chicken Curry", "category": "Mains", "price": 17.50, "is_estimable": True, "flag_reason": None},
    {"id": "ITEM-07", "name": "Stuffed Bell Peppers", "category": "Mains", "price": 13.00, "is_estimable": True, "flag_reason": None},
    {"id": "ITEM-08", "name": "Spanish Omelette", "category": "Breakfast", "price": 11.00, "is_estimable": True, "flag_reason": None},
    {"id": "ITEM-09", "name": "Chef Special Risotto", "category": "Mains", "price": 22.00, "is_estimable": False, "flag_reason": "No recipe bill of materials found in database"},
    {"id": "ITEM-10", "name": "House Secret Dip", "category": "Sides", "price": 4.50, "is_estimable": False, "flag_reason": "Missing ingredient portion weights"},
]

RECIPE_BOM = [
    # ITEM-01 Grilled Chicken Bowl
    {"menu_item_id": "ITEM-01", "canonical_id": "ING-CHICKEN", "raw": "Boneless Chicken Breast", "qty": 220.0, "unit": "g", "yield_pct": 95.0, "trim_loss": 5.0},
    {"menu_item_id": "ITEM-01", "canonical_id": "ING-RICE", "raw": "Basmati Rice", "qty": 150.0, "unit": "g", "yield_pct": 100.0, "trim_loss": 0.0},
    {"menu_item_id": "ITEM-01", "canonical_id": "ING-TOMATO", "raw": "Roma Tomato", "qty": 60.0, "unit": "g", "yield_pct": 90.0, "trim_loss": 10.0},
    {"menu_item_id": "ITEM-01", "canonical_id": "ING-ONION", "raw": "Yellow Onion", "qty": 40.0, "unit": "g", "yield_pct": 88.0, "trim_loss": 12.0},
    {"menu_item_id": "ITEM-01", "canonical_id": "ING-OIL", "raw": "Extra Virgin Olive Oil", "qty": 15.0, "unit": "ml", "yield_pct": 98.0, "trim_loss": 2.0},

    # ITEM-02 Classic Beef Burger
    {"menu_item_id": "ITEM-02", "canonical_id": "ING-BEEF", "raw": "Ground Beef 80/20", "qty": 200.0, "unit": "g", "yield_pct": 88.0, "trim_loss": 12.0},
    {"menu_item_id": "ITEM-02", "canonical_id": "ING-CHEESE", "raw": "Mozzarella Cheese", "qty": 40.0, "unit": "g", "yield_pct": 98.0, "trim_loss": 2.0},
    {"menu_item_id": "ITEM-02", "canonical_id": "ING-ONION", "raw": "Yellow Onion", "qty": 30.0, "unit": "g", "yield_pct": 88.0, "trim_loss": 12.0},
    {"menu_item_id": "ITEM-02", "canonical_id": "ING-TOMATO", "raw": "Roma Tomato", "qty": 40.0, "unit": "g", "yield_pct": 90.0, "trim_loss": 10.0},
    {"menu_item_id": "ITEM-02", "canonical_id": "ING-EGG", "raw": "Large Fresh Eggs", "qty": 1.0, "unit": "each", "yield_pct": 100.0, "trim_loss": 0.0},

    # ITEM-03 Creamy Chicken Alfredo
    {"menu_item_id": "ITEM-03", "canonical_id": "ING-CHICKEN", "raw": "Boneless Chicken Breast", "qty": 180.0, "unit": "g", "yield_pct": 95.0, "trim_loss": 5.0},
    {"menu_item_id": "ITEM-03", "canonical_id": "ING-CREAM", "raw": "Heavy Cream 36%", "qty": 120.0, "unit": "ml", "yield_pct": 98.0, "trim_loss": 2.0},
    {"menu_item_id": "ITEM-03", "canonical_id": "ING-CHEESE", "raw": "Mozzarella Cheese", "qty": 50.0, "unit": "g", "yield_pct": 98.0, "trim_loss": 2.0},
    {"menu_item_id": "ITEM-03", "canonical_id": "ING-OIL", "raw": "Extra Virgin Olive Oil", "qty": 10.0, "unit": "ml", "yield_pct": 98.0, "trim_loss": 2.0},

    # ITEM-04 Margherita Pizza
    {"menu_item_id": "ITEM-04", "canonical_id": "ING-FLOUR", "raw": "All-Purpose Flour", "qty": 180.0, "unit": "g", "yield_pct": 100.0, "trim_loss": 0.0},
    {"menu_item_id": "ITEM-04", "canonical_id": "ING-CHEESE", "raw": "Mozzarella Cheese", "qty": 120.0, "unit": "g", "yield_pct": 98.0, "trim_loss": 2.0},
    {"menu_item_id": "ITEM-04", "canonical_id": "ING-TOMATO", "raw": "Roma Tomato", "qty": 100.0, "unit": "g", "yield_pct": 90.0, "trim_loss": 10.0},
    {"menu_item_id": "ITEM-04", "canonical_id": "ING-OIL", "raw": "Extra Virgin Olive Oil", "qty": 15.0, "unit": "ml", "yield_pct": 98.0, "trim_loss": 2.0},

    # ITEM-05 Loaded Potato Fries
    {"menu_item_id": "ITEM-05", "canonical_id": "ING-POTATO", "raw": "Russet Potato", "qty": 300.0, "unit": "g", "yield_pct": 85.0, "trim_loss": 15.0},
    {"menu_item_id": "ITEM-05", "canonical_id": "ING-CHEESE", "raw": "Mozzarella Cheese", "qty": 50.0, "unit": "g", "yield_pct": 98.0, "trim_loss": 2.0},
    {"menu_item_id": "ITEM-05", "canonical_id": "ING-ONION", "raw": "Yellow Onion", "qty": 20.0, "unit": "g", "yield_pct": 88.0, "trim_loss": 12.0},

    # ITEM-06 Butter Chicken Curry
    {"menu_item_id": "ITEM-06", "canonical_id": "ING-CHICKEN", "raw": "Boneless Chicken Breast", "qty": 200.0, "unit": "g", "yield_pct": 95.0, "trim_loss": 5.0},
    {"menu_item_id": "ITEM-06", "canonical_id": "ING-CREAM", "raw": "Heavy Cream 36%", "qty": 100.0, "unit": "ml", "yield_pct": 98.0, "trim_loss": 2.0},
    {"menu_item_id": "ITEM-06", "canonical_id": "ING-ONION", "raw": "Yellow Onion", "qty": 80.0, "unit": "g", "yield_pct": 88.0, "trim_loss": 12.0},
    {"menu_item_id": "ITEM-06", "canonical_id": "ING-TOMATO", "raw": "Roma Tomato", "qty": 120.0, "unit": "g", "yield_pct": 90.0, "trim_loss": 10.0},
    {"menu_item_id": "ITEM-06", "canonical_id": "ING-RICE", "raw": "Basmati Rice", "qty": 150.0, "unit": "g", "yield_pct": 100.0, "trim_loss": 0.0},

    # ITEM-07 Stuffed Bell Peppers
    {"menu_item_id": "ITEM-07", "canonical_id": "ING-BELLPEPPER", "raw": "Green Bell Pepper", "qty": 180.0, "unit": "g", "yield_pct": 85.0, "trim_loss": 15.0},
    {"menu_item_id": "ITEM-07", "canonical_id": "ING-BEEF", "raw": "Ground Beef 80/20", "qty": 100.0, "unit": "g", "yield_pct": 88.0, "trim_loss": 12.0},
    {"menu_item_id": "ITEM-07", "canonical_id": "ING-RICE", "raw": "Basmati Rice", "qty": 80.0, "unit": "g", "yield_pct": 100.0, "trim_loss": 0.0},
    {"menu_item_id": "ITEM-07", "canonical_id": "ING-CHEESE", "raw": "Mozzarella Cheese", "qty": 30.0, "unit": "g", "yield_pct": 98.0, "trim_loss": 2.0},

    # ITEM-08 Spanish Omelette
    {"menu_item_id": "ITEM-08", "canonical_id": "ING-EGG", "raw": "Large Fresh Eggs", "qty": 3.0, "unit": "each", "yield_pct": 100.0, "trim_loss": 0.0},
    {"menu_item_id": "ITEM-08", "canonical_id": "ING-POTATO", "raw": "Russet Potato", "qty": 150.0, "unit": "g", "yield_pct": 85.0, "trim_loss": 15.0},
    {"menu_item_id": "ITEM-08", "canonical_id": "ING-ONION", "raw": "Yellow Onion", "qty": 50.0, "unit": "g", "yield_pct": 88.0, "trim_loss": 12.0},
    {"menu_item_id": "ITEM-08", "canonical_id": "ING-OIL", "raw": "Extra Virgin Olive Oil", "qty": 20.0, "unit": "ml", "yield_pct": 98.0, "trim_loss": 2.0},

    # ITEM-10 House Secret Dip (Missing quantity!)
    {"menu_item_id": "ITEM-10", "canonical_id": "ING-CREAM", "raw": "Heavy Cream", "qty": None, "unit": "ml", "yield_pct": 100.0, "trim_loss": 0.0},
    {"menu_item_id": "ITEM-10", "canonical_id": "ING-CHEESE", "raw": "Mozzarella Cheese", "qty": None, "unit": "g", "yield_pct": 100.0, "trim_loss": 0.0},
]

def generate_synthetic_dataset(db: Session, force: bool = False):
    """
    Generates 90 days of synthetic data across 6 branches with planted anomalies.
    Saves 5 CSV files and commits to SQLite.
    """
    # Check if data already exists
    if not force and db.query(Branch).count() > 0:
        print("Data already populated. Skipping generation.")
        return

    random.seed(42)
    start_date = datetime(2026, 8, 25)
    days_count = 90
    dates = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days_count)]

    # Clean existing data
    db.query(SystemSetting).delete()
    db.query(ReviewFlag).delete()
    db.query(WasteLog).delete()
    db.query(InventoryCount).delete()
    db.query(Purchase).delete()
    db.query(PosOrder).delete()
    db.query(Recipe).delete()
    db.query(MenuItem).delete()
    db.query(IngredientAlias).delete()
    db.query(CanonicalIngredient).delete()
    db.query(Branch).delete()
    db.commit()

    # 1. Insert Branches
    for b in BRANCHES:
        db.add(Branch(**b))

    # 2. Insert Canonical Ingredients
    canon_map = {}
    for c in CANONICAL_INGREDIENTS:
        ci = CanonicalIngredient(**c)
        db.add(ci)
        canon_map[c["id"]] = c

    # 3. Insert Aliases
    alias_dict = {}
    for alias_name, cid, conf, conf_bool in RAW_ALIASES:
        db.add(IngredientAlias(
            alias_name=alias_name,
            canonical_id=cid,
            confidence=conf,
            is_confirmed=conf_bool,
            source="seed"
        ))
        if cid:
            alias_dict[alias_name.lower()] = cid

    # 4. Insert Menu Items & Recipes
    for m in MENU_ITEMS:
        db.add(MenuItem(**m))

    for r in RECIPE_BOM:
        db.add(Recipe(
            menu_item_id=r["menu_item_id"],
            canonical_id=r["canonical_id"],
            raw_ingredient_name=r["raw"],
            quantity=r["qty"],
            unit=r["unit"],
            yield_pct=r["yield_pct"],
            trim_loss_pct=r["trim_loss"]
        ))

    db.commit()

    # Create CSV rows lists
    pos_orders_rows = []
    purchases_rows = []
    inventory_counts_rows = []
    waste_logs_rows = []
    recipes_rows = []

    for r in RECIPE_BOM:
        recipes_rows.append({
            "menu_item_id": r["menu_item_id"],
            "canonical_id": r["canonical_id"],
            "raw_ingredient_name": r["raw"],
            "quantity": r["qty"] if r["qty"] is not None else "",
            "unit": r["unit"] or "",
            "yield_pct": r["yield_pct"],
            "trim_loss_pct": r["trim_loss"]
        })

    # Prepare simulation state per branch x ingredient
    # Stock levels in base units
    stock_levels = {}
    for b in BRANCHES:
        b_id = b["id"]
        stock_levels[b_id] = {}
        for c in CANONICAL_INGREDIENTS:
            # Initialize with ~10 days worth of base stock
            init_stock = c["default_pack_qty_base"] * random.uniform(2.0, 3.5)
            stock_levels[b_id][c["id"]] = init_stock

    order_counter = 100000
    purchase_counter = 50000
    count_counter = 20000
    waste_counter = 80000

    # Weekly count day indices: every 7 days (e.g. days 0, 7, 14, 21, ..., 84, 89)
    count_days = set(range(0, days_count, 7))
    count_days.add(days_count - 1)

    # Alias picker helper
    alias_pool = {}
    for a_name, cid, _, _ in RAW_ALIASES:
        if cid:
            alias_pool.setdefault(cid, []).append(a_name)

    # 90 Days Simulation
    for day_idx, d_str in enumerate(dates):
        current_dt = start_date + timedelta(days=day_idx)
        is_weekend = current_dt.weekday() >= 5
        day_of_week = current_dt.weekday()

        # Day-of-week multiplier (seasonality: Fri, Sat, Sun higher sales)
        dow_mult = 1.35 if is_weekend else (1.15 if day_of_week == 4 else 0.90)

        # 1. POS Orders generation per branch
        for b in BRANCHES:
            b_id = b["id"]
            # Capacity multiplier
            cap_mult = b["seating_capacity"] / 100.0

            # Today's menu orders for this branch
            daily_theoretical_usage = {c["id"]: 0.0 for c in CANONICAL_INGREDIENTS}

            for item in MENU_ITEMS:
                # Base popularity
                base_qty = random.randint(4, 12)
                if item["id"] in ["ITEM-01", "ITEM-02", "ITEM-03", "ITEM-04"]:
                    base_qty += random.randint(6, 14)

                qty = int(base_qty * dow_mult * cap_mult * random.uniform(0.9, 1.1))
                sales_amt = round(qty * item["price"], 2)

                order_counter += 1
                pos_orders_rows.append({
                    "order_id": f"ORD-{order_counter}",
                    "branch_id": b_id,
                    "date": d_str,
                    "timestamp": f"{d_str}T{random.randint(11, 21):02d}:{random.randint(0, 59):02d}:00",
                    "menu_item_id": item["id"],
                    "quantity": qty,
                    "sales_amount": sales_amt
                })

                # Explode theoretical recipe usage
                if item["is_estimable"]:
                    for r in RECIPE_BOM:
                        if r["menu_item_id"] == item["id"] and r["qty"] is not None:
                            # Formula: qty * (bom_qty / (yield_pct / 100))
                            yield_factor = (r["yield_pct"] / 100.0) if r["yield_pct"] > 0 else 1.0
                            ing_needed = qty * (r["qty"] / yield_factor)
                            daily_theoretical_usage[r["canonical_id"]] += ing_needed

            # Deduct theoretical usage or over-portion usage from stock
            for c_id, theo_qty in daily_theoretical_usage.items():
                actual_depletion = theo_qty
                # Planted Anomaly 1: B01 Over-portions Chicken!
                if b_id == "B01" and c_id == "ING-CHICKEN":
                    # Consumes ~32% more chicken than theoretical recipe calls for
                    actual_depletion = theo_qty * 1.32

                stock_levels[b_id][c_id] -= actual_depletion

            # 2. Waste Logs generation
            for c in CANONICAL_INGREDIENTS:
                c_id = c["id"]
                # Normal waste probability ~15% chance per day per ingredient
                waste_prob = 0.15
                waste_pct = random.uniform(0.015, 0.035) # 1.5-3.5%
                reason = "Trimming / Prep loss"

                # Planted Anomaly 2: B03 High Dairy Waste!
                if b_id == "B03" and c_id in ["ING-CREAM", "ING-CHEESE"]:
                    waste_prob = 0.75 # frequent dairy waste
                    waste_pct = random.uniform(0.12, 0.22) # 12-22% high volume waste
                    reason = random.choice([
                        "Spoiled - walk-in temp fluctuation",
                        "Expired batch past use-by date",
                        "Sour smell / Curdled cream",
                        "Mold detected on cheese block"
                    ])
                elif random.random() < 0.2:
                    reason = random.choice(["Overcooked/burnt", "Customer return", "Dropped during prep"])

                if random.random() < waste_prob:
                    waste_raw_name = random.choice(alias_pool.get(c_id, [c["name"]]))
                    base_est = daily_theoretical_usage.get(c_id, 500)
                    waste_base_qty = round(base_est * waste_pct, 2)
                    if waste_base_qty > 0:
                        stock_levels[b_id][c_id] -= waste_base_qty
                        
                        # Express waste in various units
                        unit_choice = c["base_unit"]
                        val_in_unit = waste_base_qty
                        if c["base_unit"] == "g":
                            if waste_base_qty > 1000 and random.random() > 0.4:
                                val_in_unit = round(waste_base_qty / 1000.0, 3)
                                unit_choice = "kg"
                            elif random.random() > 0.6:
                                val_in_unit = round(waste_base_qty / 453.592, 2)
                                unit_choice = "lb"
                        elif c["base_unit"] == "ml":
                            if waste_base_qty > 1000 and random.random() > 0.4:
                                val_in_unit = round(waste_base_qty / 1000.0, 2)
                                unit_choice = "l"
                            elif random.random() > 0.7:
                                val_in_unit = round(waste_base_qty / 240.0, 2)
                                unit_choice = "cup"

                        waste_counter += 1
                        waste_logs_rows.append({
                            "waste_id": f"WST-{waste_counter}",
                            "branch_id": b_id,
                            "date": d_str,
                            "ingredient_name_raw": waste_raw_name,
                            "waste_quantity": val_in_unit,
                            "unit": unit_choice,
                            "reason": reason,
                            "recorded_by": f"Chef {random.choice(['Dave', 'Marcus', 'Elena', 'Chloe', 'Jin'])}",
                            "canonical_id": c_id,
                            "normalized_qty": waste_base_qty,
                            "normalized_unit": c["base_unit"]
                        })

            # 3. Purchases replenishment (triggered when stock drops below 4 days buffer)
            for c in CANONICAL_INGREDIENTS:
                c_id = c["id"]
                current_stock = stock_levels[b_id][c_id]
                pack_base = c["default_pack_qty_base"]
                # Daily expected usage ~ 1-2 packs
                reorder_threshold = pack_base * 2.5
                if current_stock < reorder_threshold:
                    # Order 3 to 6 packs to replenish a week of stock
                    packs_to_order = random.randint(3, 6)
                    pack_desc = c["default_pack_desc"]
                    total_ordered_base = packs_to_order * pack_base
                    stock_levels[b_id][c_id] += total_ordered_base

                    purchase_raw_name = random.choice(alias_pool.get(c_id, [c["name"]]))
                    unit_cost = round(pack_base * c["cost_per_base_unit"], 2)
                    total_cost = round(unit_cost * packs_to_order, 2)

                    purchase_counter += 1
                    purchases_rows.append({
                        "purchase_id": f"PUR-{purchase_counter}",
                        "branch_id": b_id,
                        "date": d_str,
                        "ingredient_name_raw": purchase_raw_name,
                        "pack_description": pack_desc,
                        "pack_quantity": packs_to_order,
                        "unit_cost": unit_cost,
                        "total_cost": total_cost,
                        "canonical_id": c_id,
                        "normalized_qty": total_ordered_base,
                        "normalized_unit": c["base_unit"]
                    })

            # 4. Inventory counts on weekly audit days
            if day_idx in count_days:
                for c in CANONICAL_INGREDIENTS:
                    c_id = c["id"]
                    # Current actual remaining stock on shelves
                    actual_current_stock = max(c["default_pack_qty_base"] * 0.5, stock_levels[b_id][c_id])
                    
                    # Normal random count noise (+/- 1%)
                    counted_base = actual_current_stock * random.uniform(0.99, 1.01)

                    # Planted Anomaly 3: B05 Bad inventory count on day 56 (Week 8)
                    # 8.5x typo on Ground Beef!
                    if b_id == "B05" and day_idx == 56 and c_id == "ING-BEEF":
                        counted_base = actual_current_stock * 8.5

                    # Reset stock to counted level
                    stock_levels[b_id][c_id] = counted_base

                    # Convert counted base to displayed count unit
                    display_unit = c["base_unit"]
                    display_qty = round(counted_base, 2)
                    if c["base_unit"] == "g":
                        display_qty = round(counted_base / 1000.0, 2)
                        display_unit = "kg"
                    elif c["base_unit"] == "ml":
                        display_qty = round(counted_base / 1000.0, 2)
                        display_unit = "l"

                    count_counter += 1
                    count_raw_name = random.choice(alias_pool.get(c_id, [c["name"]]))
                    inventory_counts_rows.append({
                        "count_id": f"CNT-{count_counter}",
                        "branch_id": b_id,
                        "date": d_str,
                        "ingredient_name_raw": count_raw_name,
                        "count_quantity": display_qty,
                        "unit": display_unit,
                        "canonical_id": c_id,
                        "normalized_qty": round(counted_base, 2),
                        "normalized_unit": c["base_unit"]
                    })

    # Save CSV files to DATA_DIR
    csv_configs = [
        ("pos_orders.csv", pos_orders_rows, ["order_id", "branch_id", "date", "timestamp", "menu_item_id", "quantity", "sales_amount"]),
        ("recipes.csv", recipes_rows, ["menu_item_id", "canonical_id", "raw_ingredient_name", "quantity", "unit", "yield_pct", "trim_loss_pct"]),
        ("purchases.csv", purchases_rows, ["purchase_id", "branch_id", "date", "ingredient_name_raw", "pack_description", "pack_quantity", "unit_cost", "total_cost", "canonical_id", "normalized_qty", "normalized_unit"]),
        ("inventory_counts.csv", inventory_counts_rows, ["count_id", "branch_id", "date", "ingredient_name_raw", "count_quantity", "unit", "canonical_id", "normalized_qty", "normalized_unit"]),
        ("waste_logs.csv", waste_logs_rows, ["waste_id", "branch_id", "date", "ingredient_name_raw", "waste_quantity", "unit", "reason", "recorded_by", "canonical_id", "normalized_qty", "normalized_unit"])
    ]

    for filename, rows, fieldnames in csv_configs:
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Generated {filename}: {len(rows)} records.")

    # Insert rows into DB in batches
    print("Writing to SQLite database...")
    batch_size = 5000
    
    # POS Orders
    for i in range(0, len(pos_orders_rows), batch_size):
        chunk = [PosOrder(**r) for r in pos_orders_rows[i:i+batch_size]]
        db.bulk_save_objects(chunk)
        db.commit()

    # Purchases
    for i in range(0, len(purchases_rows), batch_size):
        chunk = [Purchase(**r) for r in purchases_rows[i:i+batch_size]]
        db.bulk_save_objects(chunk)
        db.commit()

    # Inventory Counts
    for i in range(0, len(inventory_counts_rows), batch_size):
        chunk = [InventoryCount(**r) for r in inventory_counts_rows[i:i+batch_size]]
        db.bulk_save_objects(chunk)
        db.commit()

    # Waste Logs
    for i in range(0, len(waste_logs_rows), batch_size):
        chunk = [WasteLog(**r) for r in waste_logs_rows[i:i+batch_size]]
        db.bulk_save_objects(chunk)
        db.commit()

    # Default system settings
    default_settings = [
        ("variance_threshold_pct", "15.0"),
        ("variance_threshold_dollar", "200.0"),
        ("z_score_threshold", "2.0"),
        ("waste_median_multiplier", "1.5"),
        ("safety_stock_days", "3"),
        ("forecast_window_days", "14")
    ]
    for k, v in default_settings:
        db.add(SystemSetting(key=k, value=v))
    db.commit()

    print("Synthetic dataset generation and database seeding complete!")
