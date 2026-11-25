from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Branch(Base):
    __tablename__ = "branches"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=True)
    seating_capacity = Column(Integer, default=50)

class CanonicalIngredient(Base):
    __tablename__ = "canonical_ingredients"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False) # Produce, Meat & Poultry, Dairy, Dry Goods
    base_unit = Column(String, nullable=False) # g, ml, each
    density_g_per_ml = Column(Float, default=1.0)
    default_pack_desc = Column(String, nullable=True) # e.g. "case of 12 x 500g"
    default_pack_qty_base = Column(Float, default=1000.0) # in base units
    cost_per_base_unit = Column(Float, default=0.01)
    standard_yield_pct = Column(Float, default=100.0)

class IngredientAlias(Base):
    __tablename__ = "ingredient_aliases"
    id = Column(Integer, primary_key=True, autoincrement=True)
    alias_name = Column(String, nullable=False, unique=True)
    canonical_id = Column(String, ForeignKey("canonical_ingredients.id"), nullable=True)
    confidence = Column(Float, default=100.0)
    is_confirmed = Column(Boolean, default=True)
    source = Column(String, default="seed") # seed, auto, manual

class UnitConversion(Base):
    __tablename__ = "unit_conversions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_unit = Column(String, nullable=False)
    to_unit = Column(String, nullable=False)
    factor = Column(Float, nullable=False)
    dimension = Column(String, nullable=False) # mass, volume, count

class MenuItem(Base):
    __tablename__ = "menu_items"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    is_estimable = Column(Boolean, default=True)
    flag_reason = Column(String, nullable=True)

class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    menu_item_id = Column(String, ForeignKey("menu_items.id"), nullable=False)
    canonical_id = Column(String, ForeignKey("canonical_ingredients.id"), nullable=True)
    raw_ingredient_name = Column(String, nullable=False)
    quantity = Column(Float, nullable=True) # None indicates missing quantity
    unit = Column(String, nullable=True)
    yield_pct = Column(Float, default=100.0)
    trim_loss_pct = Column(Float, default=0.0)

class PosOrder(Base):
    __tablename__ = "pos_orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, nullable=False)
    branch_id = Column(String, ForeignKey("branches.id"), nullable=False)
    date = Column(String, nullable=False) # YYYY-MM-DD
    timestamp = Column(String, nullable=False)
    menu_item_id = Column(String, ForeignKey("menu_items.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    sales_amount = Column(Float, nullable=False)

class Purchase(Base):
    __tablename__ = "purchases"
    id = Column(Integer, primary_key=True, autoincrement=True)
    purchase_id = Column(String, nullable=False)
    branch_id = Column(String, ForeignKey("branches.id"), nullable=False)
    date = Column(String, nullable=False) # YYYY-MM-DD
    ingredient_name_raw = Column(String, nullable=False)
    pack_description = Column(String, nullable=False)
    pack_quantity = Column(Float, nullable=False)
    unit_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    canonical_id = Column(String, ForeignKey("canonical_ingredients.id"), nullable=True)
    normalized_qty = Column(Float, nullable=True)
    normalized_unit = Column(String, nullable=True)

class InventoryCount(Base):
    __tablename__ = "inventory_counts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    count_id = Column(String, nullable=False)
    branch_id = Column(String, ForeignKey("branches.id"), nullable=False)
    date = Column(String, nullable=False) # YYYY-MM-DD (typically weekly closing/opening)
    ingredient_name_raw = Column(String, nullable=False)
    count_quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    canonical_id = Column(String, ForeignKey("canonical_ingredients.id"), nullable=True)
    normalized_qty = Column(Float, nullable=True)
    normalized_unit = Column(String, nullable=True)

class WasteLog(Base):
    __tablename__ = "waste_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    waste_id = Column(String, nullable=False)
    branch_id = Column(String, ForeignKey("branches.id"), nullable=False)
    date = Column(String, nullable=False) # YYYY-MM-DD
    ingredient_name_raw = Column(String, nullable=False)
    waste_quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    recorded_by = Column(String, nullable=True)
    canonical_id = Column(String, ForeignKey("canonical_ingredients.id"), nullable=True)
    normalized_qty = Column(Float, nullable=True)
    normalized_unit = Column(String, nullable=True)

class ReviewFlag(Base):
    __tablename__ = "review_flags"
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String, nullable=False) # branch, menu_item, ingredient
    entity_id = Column(String, nullable=False)
    branch_id = Column(String, nullable=True)
    date_period = Column(String, nullable=True)
    flag_type = Column(String, nullable=False) # variance_threshold, z_score_peer, high_waste, recurring, suspicious_count, unmapped_alias, missing_recipe
    severity_score = Column(Float, default=50.0) # 0 - 100
    reason = Column(Text, nullable=False)
    status = Column(String, default="open") # open, investigating, resolved
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemSetting(Base):
    __tablename__ = "system_settings"
    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
