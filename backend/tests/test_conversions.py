import pytest
from backend.app.normalizer import (
    parse_pack_or_unit, convert_to_dim_base,
    apply_density_conversion, fuzzy_match_ingredient
)

def test_convert_to_dim_base_mass():
    val, dim = convert_to_dim_base(2.5, "kg")
    assert val == 2500.0
    assert dim == "g"

    val_lb, dim_lb = convert_to_dim_base(10, "lb")
    assert pytest.approx(val_lb, 0.1) == 4535.92
    assert dim_lb == "g"

def test_convert_to_dim_base_volume():
    val, dim = convert_to_dim_base(3.5, "l")
    assert val == 3500.0
    assert dim == "ml"

    val_cup, dim_cup = convert_to_dim_base(2, "cups")
    assert val_cup == 480.0
    assert dim_cup == "ml"

def test_pack_composite_parsing():
    # Case of 12 x 500g = 6,000g
    val, unit = parse_pack_or_unit("case of 12 x 500g", quantity=1.0)
    assert val == 6000.0
    assert unit == "g"

    # Box of 6 x 1kg, 2 boxes = 12,000g
    val2, unit2 = parse_pack_or_unit("box of 6 x 1kg", quantity=2.0)
    assert val2 == 12000.0
    assert unit2 == "g"

def test_density_conversions():
    # Olive oil: 500 ml -> g with density 0.92 = 460g
    val, unit = parse_pack_or_unit("500 ml", quantity=1.0, density_g_per_ml=0.92, target_base_unit="g")
    assert pytest.approx(val, 0.1) == 460.0
    assert unit == "g"

    # Heavy Cream: 1000 ml with density 1.01 = 1010g
    val2, unit2 = parse_pack_or_unit("1 l", quantity=1.0, density_g_per_ml=1.01, target_base_unit="g")
    assert pytest.approx(val2, 0.1) == 1010.0
    assert unit2 == "g"

def test_fuzzy_alias_matching():
    known_aliases = {
        "tomatoes fresh": "ING-TOMATO",
        "chicken breast bnls": "ING-CHICKEN",
        "malai cream": "ING-CREAM"
    }
    catalog = {
        "ING-TOMATO": "Roma Tomato",
        "ING-CHICKEN": "Boneless Chicken Breast",
        "ING-CREAM": "Heavy Cream 36%"
    }

    # Exact match
    cid, conf, _ = fuzzy_match_ingredient("tomatoes fresh", known_aliases, catalog)
    assert cid == "ING-TOMATO"
    assert conf == 100.0

    # Fuzzy match with rearranged or partial words
    cid_fuzzy, conf_fuzzy, _ = fuzzy_match_ingredient("fresh tomatoes", known_aliases, catalog)
    assert cid_fuzzy == "ING-TOMATO"
    assert conf_fuzzy >= 80.0

    # Chk breast -> chicken
    cid_chk, conf_chk, _ = fuzzy_match_ingredient("chk breast fillet", known_aliases, catalog)
    assert cid_chk == "ING-CHICKEN"
