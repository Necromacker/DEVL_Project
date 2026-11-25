import re
from typing import Tuple, Optional, Dict
from rapidfuzz import fuzz, process

# Standard conversion factors to base units (g for mass, ml for volume, each for count)
MASS_CONVERSIONS = {
    "g": 1.0,
    "gram": 1.0,
    "grams": 1.0,
    "kg": 1000.0,
    "kilogram": 1000.0,
    "kilograms": 1000.0,
    "lb": 453.59237,
    "lbs": 453.59237,
    "pound": 453.59237,
    "pounds": 453.59237,
    "oz": 28.34952,
    "ounce": 28.34952,
    "ounces": 28.34952,
}

VOLUME_CONVERSIONS = {
    "ml": 1.0,
    "milliliter": 1.0,
    "milliliters": 1.0,
    "l": 1000.0,
    "liter": 1000.0,
    "liters": 1000.0,
    "litre": 1000.0,
    "litres": 1000.0,
    "cup": 240.0,
    "cups": 240.0,
    "tbsp": 15.0,
    "tablespoon": 15.0,
    "tablespoons": 15.0,
    "tsp": 5.0,
    "teaspoon": 5.0,
    "teaspoons": 5.0,
    "gal": 3785.41,
    "gallon": 3785.41,
    "gallons": 3785.41,
    "fl oz": 29.5735,
    "floz": 29.5735,
}

COUNT_CONVERSIONS = {
    "each": 1.0,
    "ea": 1.0,
    "pc": 1.0,
    "piece": 1.0,
    "pieces": 1.0,
    "unit": 1.0,
    "units": 1.0,
    "item": 1.0,
    "items": 1.0,
    "dozen": 12.0,
    "doz": 12.0,
}

# Regex to match pack sizes such as:
# "case of 12 x 500g", "box of 6 x 1kg", "pack of 24 each", "crate of 20 lb", "bag of 5 kg", "tub of 4 l"
PACK_COMPOSITE_REGEX = re.compile(
    r'(?:case|box|pack|crate|bag|tub|can|jug|carton)?\s*(?:of)?\s*(\d+(?:\.\d+)?)\s*(?:x|X|\*)\s*(\d+(?:\.\d+)?)\s*([a-zA-Z\s]+)',
    re.IGNORECASE
)
PACK_SIMPLE_REGEX = re.compile(
    r'(?:case|box|pack|crate|bag|tub|can|jug|carton)?\s*(?:of)?\s*(\d+(?:\.\d+)?)\s*([a-zA-Z\s]+)',
    re.IGNORECASE
)

def clean_unit_string(unit: str) -> str:
    if not unit:
        return ""
    u = unit.strip().lower()
    u = re.sub(r'[^a-z0-9\s]', '', u)
    return u.strip()

def parse_pack_or_unit(
    pack_or_unit_desc: str,
    quantity: float = 1.0,
    density_g_per_ml: float = 1.0,
    target_base_unit: Optional[str] = None
) -> Tuple[float, str]:
    """
    Parses a unit or pack description and converts the total quantity to base unit:
    - Mass -> 'g'
    - Volume -> 'ml'
    - Count -> 'each'
    If target_base_unit is supplied and dimension differs (e.g. recipe needs 'g' but pack is 'ml'),
    it converts via density (mass = volume * density).
    """
    if not pack_or_unit_desc:
        return (quantity, target_base_unit or "each")

    desc = pack_or_unit_desc.strip()

    # Try composite pack format first: e.g. "case of 12 x 500g"
    m_comp = PACK_COMPOSITE_REGEX.search(desc)
    if m_comp:
        n_items = float(m_comp.group(1))
        item_size = float(m_comp.group(2))
        inner_unit = clean_unit_string(m_comp.group(3))
        single_pack_base, dim = convert_to_dim_base(item_size * n_items, inner_unit)
        total_base = single_pack_base * quantity
        final_val, final_unit = apply_density_conversion(total_base, dim, density_g_per_ml, target_base_unit)
        return (round(final_val, 4), final_unit)

    # Try simple pack format: e.g. "crate of 20 lb" or "bag of 5 kg" or "pack of 24 each"
    m_simp = PACK_SIMPLE_REGEX.search(desc)
    if m_simp:
        size = float(m_simp.group(1))
        unit_str = clean_unit_string(m_simp.group(2))
        single_base, dim = convert_to_dim_base(size, unit_str)
        total_base = single_base * quantity
        final_val, final_unit = apply_density_conversion(total_base, dim, density_g_per_ml, target_base_unit)
        return (round(final_val, 4), final_unit)

    # Plain unit string without numbers: e.g. "kg", "lb", "ml", "each"
    unit_str = clean_unit_string(desc)
    single_base, dim = convert_to_dim_base(quantity, unit_str)
    final_val, final_unit = apply_density_conversion(single_base, dim, density_g_per_ml, target_base_unit)
    return (round(final_val, 4), final_unit)

def convert_to_dim_base(value: float, unit_str: str) -> Tuple[float, str]:
    """Converts a value and unit into (base_value, dimension_unit) where dimension_unit is g, ml, or each"""
    u = unit_str.strip().lower()
    
    # Check mass
    for key, factor in MASS_CONVERSIONS.items():
        if u == key or u.startswith(key + " "):
            return (value * factor, "g")

    # Check volume
    for key, factor in VOLUME_CONVERSIONS.items():
        if u == key or u.startswith(key + " "):
            return (value * factor, "ml")

    # Check count
    for key, factor in COUNT_CONVERSIONS.items():
        if u == key or u.startswith(key + " "):
            return (value * factor, "each")

    # Fallback default: assume 1.0 of whatever is passed, treat as each
    return (value, "each")

def apply_density_conversion(
    base_val: float,
    current_dim: str,
    density_g_per_ml: float,
    target_base_unit: Optional[str]
) -> Tuple[float, str]:
    """Converts between mass and volume if target requires it using density."""
    if not target_base_unit or current_dim == target_base_unit:
        return (base_val, current_dim)

    # Volume to Mass (ml -> g)
    if current_dim == "ml" and target_base_unit == "g":
        # mass = volume * density
        return (base_val * density_g_per_ml, "g")

    # Mass to Volume (g -> ml)
    if current_dim == "g" and target_base_unit == "ml":
        # volume = mass / density
        return (base_val / (density_g_per_ml or 1.0), "ml")

    return (base_val, current_dim)

def fuzzy_match_ingredient(
    raw_name: str,
    known_aliases: Dict[str, str], # alias_lower -> canonical_id
    canonical_catalog: Dict[str, str] # canonical_id -> canonical_name
) -> Tuple[Optional[str], float, str]:
    """
    Fuzzy match raw_name to canonical ingredients.
    Returns: (canonical_id, confidence_score, matched_term)
    """
    if not raw_name:
        return (None, 0.0, "")

    clean_raw = raw_name.strip().lower()

    # 1. Exact match in alias table
    if clean_raw in known_aliases:
        return (known_aliases[clean_raw], 100.0, clean_raw)

    # 2. Check canonical names directly
    for cid, cname in canonical_catalog.items():
        if clean_raw == cname.lower():
            return (cid, 100.0, cname)

    # 3. Fuzzy search against all known aliases and canonical names
    candidates = {}
    for alias, cid in known_aliases.items():
        candidates[f"alias:{alias}"] = (cid, alias)
    for cid, cname in canonical_catalog.items():
        candidates[f"canon:{cname.lower()}"] = (cid, cname)

    best_score = 0.0
    best_cid = None
    best_term = ""

    # Token sort ratio handles reordered words like "tomatoes fresh" vs "fresh tomatoes"
    for cand_key, (cid, term) in candidates.items():
        score_sort = fuzz.token_sort_ratio(clean_raw, term.lower())
        score_set = fuzz.token_set_ratio(clean_raw, term.lower())
        score = max(score_sort, score_set)

        # Bonus if canonical name token is a full substring
        if term.lower() in clean_raw or clean_raw in term.lower():
            score = min(100.0, score + 10.0)

        if score > best_score:
            best_score = score
            best_cid = cid
            best_term = term

    return (best_cid, round(best_score, 1), best_term)
