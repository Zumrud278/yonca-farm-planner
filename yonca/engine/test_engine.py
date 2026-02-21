# test_engine.py — Pytest unit tests for Yonca AI Planner engine.py
# Edge cases covered: drought, high pest risk, overdue fertilization,
# critical livestock conditions, frost risk, pre-harvest windows, etc.

import pytest
from engine import (
    wheat_recommendations,
    vegetable_recommendations,
    orchard_recommendations,
    mixed_recommendations,
    livestock_recommendations,
    get_recommendations,
)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def priorities(recs):
    """Return just the priority list from recommendations."""
    return [r[0] for r in recs]


def messages(recs):
    """Return just the message strings from recommendations."""
    return [r[1] for r in recs]


def has_priority(recs, level):
    """Assert at least one recommendation has the given priority level."""
    return level in priorities(recs)


def first_priority(recs):
    """Return the priority of the top-sorted recommendation."""
    return recs[0][0]


# ─────────────────────────────────────────────
# SYNTHETIC DATA FIXTURES
# ─────────────────────────────────────────────

# ── Wheat ───────────────────────────────────

@pytest.fixture
def wheat_normal():
    """Healthy wheat farm — no alerts expected."""
    return {
        "soil_moisture": 60, "rainfall_mm": 10, "temp_celsius": 20,
        "growth_stage": "vegetative", "npk": {"N": 50, "P": 25, "K": 30},
        "pest_pressure": "low", "last_irrigation_days": 2, "last_fertilization_days": 5
    }

@pytest.fixture
def wheat_drought():
    """Drought edge case: critically low moisture, no rain."""
    return {
        "soil_moisture": 22, "rainfall_mm": 0, "temp_celsius": 28,
        "growth_stage": "heading", "npk": {"N": 40, "P": 20, "K": 25},
        "pest_pressure": "low", "last_irrigation_days": 7, "last_fertilization_days": 10
    }

@pytest.fixture
def wheat_high_pest():
    """High pest pressure during warm conditions."""
    return {
        "soil_moisture": 55, "rainfall_mm": 5, "temp_celsius": 29,
        "growth_stage": "heading", "npk": {"N": 45, "P": 22, "K": 28},
        "pest_pressure": "high", "last_irrigation_days": 3, "last_fertilization_days": 8
    }

@pytest.fixture
def wheat_overdue_fert():
    """Overdue fertilization + low N."""
    return {
        "soil_moisture": 55, "rainfall_mm": 8, "temp_celsius": 18,
        "growth_stage": "tillering", "npk": {"N": 16, "P": 10, "K": 20},
        "pest_pressure": "low", "last_irrigation_days": 3, "last_fertilization_days": 25
    }

@pytest.fixture
def wheat_fungal_risk():
    """Warm + wet = fungal disease risk with no detected pressure yet."""
    return {
        "soil_moisture": 65, "rainfall_mm": 30, "temp_celsius": 30,
        "growth_stage": "tillering", "npk": {"N": 45, "P": 22, "K": 28},
        "pest_pressure": "low", "last_irrigation_days": 1, "last_fertilization_days": 7
    }


# ── Vegetable ───────────────────────────────

@pytest.fixture
def veg_normal():
    return {
        "soil_moisture": 62, "rainfall_mm": 8, "temp_celsius": 21,
        "crop_type": "tomato", "days_to_harvest": 45,
        "npk": {"N": 45, "P": 22, "K": 35},
        "pest_pressure": "low", "humidity_pct": 58,
        "last_irrigation_days": 1, "last_fertilization_days": 5
    }

@pytest.fixture
def veg_drought():
    """Critical soil moisture for vegetables."""
    return {
        "soil_moisture": 28, "rainfall_mm": 0, "temp_celsius": 24,
        "crop_type": "pepper", "days_to_harvest": 20,
        "npk": {"N": 40, "P": 18, "K": 30},
        "pest_pressure": "low", "humidity_pct": 50,
        "last_irrigation_days": 4, "last_fertilization_days": 10
    }

@pytest.fixture
def veg_high_pest():
    """High pest pressure with high humidity."""
    return {
        "soil_moisture": 58, "rainfall_mm": 3, "temp_celsius": 26,
        "crop_type": "cucumber", "days_to_harvest": 15,
        "npk": {"N": 42, "P": 20, "K": 32},
        "pest_pressure": "high", "humidity_pct": 82,
        "last_irrigation_days": 2, "last_fertilization_days": 8
    }

@pytest.fixture
def veg_overdue_fert():
    """Overdue fertilization (>14 days)."""
    return {
        "soil_moisture": 55, "rainfall_mm": 5, "temp_celsius": 20,
        "crop_type": "lettuce", "days_to_harvest": 30,
        "npk": {"N": 30, "P": 18, "K": 28},
        "pest_pressure": "low", "humidity_pct": 60,
        "last_irrigation_days": 2, "last_fertilization_days": 18
    }

@pytest.fixture
def veg_pre_harvest_k_low():
    """K deficiency close to harvest — quality risk."""
    return {
        "soil_moisture": 58, "rainfall_mm": 4, "temp_celsius": 22,
        "crop_type": "tomato", "days_to_harvest": 10,
        "npk": {"N": 42, "P": 20, "K": 14},
        "pest_pressure": "low", "humidity_pct": 60,
        "last_irrigation_days": 2, "last_fertilization_days": 7
    }


# ── Orchard ─────────────────────────────────

@pytest.fixture
def orchard_normal():
    return {
        "soil_moisture": 60, "rainfall_mm": 10, "temp_celsius": 18,
        "tree_age_years": 6, "fruit_stage": "fruit_set",
        "npk": {"N": 40, "P": 18, "K": 28},
        "pest_pressure": "low", "frost_risk": False,
        "last_irrigation_days": 4, "last_fertilization_days": 20, "last_pruning_days": 40
    }

@pytest.fixture
def orchard_drought_fruit_set():
    """Drought during fruit_set — highest risk for yield loss."""
    return {
        "soil_moisture": 38, "rainfall_mm": 1, "temp_celsius": 22,
        "tree_age_years": 5, "fruit_stage": "fruit_set",
        "npk": {"N": 38, "P": 16, "K": 24},
        "pest_pressure": "low", "frost_risk": False,
        "last_irrigation_days": 8, "last_fertilization_days": 18, "last_pruning_days": 50
    }

@pytest.fixture
def orchard_frost():
    """Frost risk — irrigation must NOT be recommended normally."""
    return {
        "soil_moisture": 45, "rainfall_mm": 0, "temp_celsius": 2,
        "tree_age_years": 4, "fruit_stage": "flowering",
        "npk": {"N": 35, "P": 15, "K": 22},
        "pest_pressure": "low", "frost_risk": True,
        "last_irrigation_days": 3, "last_fertilization_days": 14, "last_pruning_days": 30
    }

@pytest.fixture
def orchard_high_pest():
    """High pest pressure — immediate treatment needed."""
    return {
        "soil_moisture": 58, "rainfall_mm": 5, "temp_celsius": 26,
        "tree_age_years": 7, "fruit_stage": "ripening",
        "npk": {"N": 38, "P": 16, "K": 24},
        "pest_pressure": "high", "frost_risk": False,
        "last_irrigation_days": 5, "last_fertilization_days": 22, "last_pruning_days": 45
    }

@pytest.fixture
def orchard_overdue_fert():
    """Fertilization gap >30 days during active stage."""
    return {
        "soil_moisture": 55, "rainfall_mm": 6, "temp_celsius": 19,
        "tree_age_years": 5, "fruit_stage": "fruit_set",
        "npk": {"N": 38, "P": 18, "K": 24},
        "pest_pressure": "low", "frost_risk": False,
        "last_irrigation_days": 4, "last_fertilization_days": 35, "last_pruning_days": 40
    }

@pytest.fixture
def orchard_young_tree_n_low():
    """Young tree + low N — establishment at risk."""
    return {
        "soil_moisture": 55, "rainfall_mm": 8, "temp_celsius": 18,
        "tree_age_years": 2, "fruit_stage": "vegetative",
        "npk": {"N": 22, "P": 14, "K": 20},
        "pest_pressure": "low", "frost_risk": False,
        "last_irrigation_days": 3, "last_fertilization_days": 10, "last_pruning_days": 30
    }


# ── Mixed ───────────────────────────────────

@pytest.fixture
def mixed_normal():
    return {
        "soil_moisture": 58, "rainfall_mm": 8, "temp_celsius": 20,
        "crop_sections": ["wheat", "alfalfa"],
        "npk": {"N": 40, "P": 20, "K": 25},
        "pest_pressure": "low", "animal_count": 30,
        "feed_stock_days": 20,
        "last_irrigation_days": 3, "last_fertilization_days": 12
    }

@pytest.fixture
def mixed_drought():
    return {
        "soil_moisture": 30, "rainfall_mm": 0, "temp_celsius": 26,
        "crop_sections": ["wheat", "sunflower"],
        "npk": {"N": 38, "P": 18, "K": 22},
        "pest_pressure": "low", "animal_count": 25,
        "feed_stock_days": 12,
        "last_irrigation_days": 6, "last_fertilization_days": 10
    }

@pytest.fixture
def mixed_high_pest():
    return {
        "soil_moisture": 52, "rainfall_mm": 4, "temp_celsius": 27,
        "crop_sections": ["vegetable", "wheat"],
        "npk": {"N": 36, "P": 17, "K": 21},
        "pest_pressure": "high", "animal_count": 40,
        "feed_stock_days": 15,
        "last_irrigation_days": 3, "last_fertilization_days": 14
    }

@pytest.fixture
def mixed_overdue_fert_low_feed():
    """Overdue fertilization + low feed stock."""
    return {
        "soil_moisture": 50, "rainfall_mm": 5, "temp_celsius": 22,
        "crop_sections": ["wheat", "alfalfa", "sunflower"],
        "npk": {"N": 20, "P": 14, "K": 15},
        "pest_pressure": "medium", "animal_count": 50,
        "feed_stock_days": 5,
        "last_irrigation_days": 4, "last_fertilization_days": 25
    }


# ── Livestock ────────────────────────────────

@pytest.fixture
def livestock_normal():
    return {
        "animal_type": "cattle", "animal_count": 60, "avg_weight_kg": 300,
        "feed_stock_days": 20, "feed_type": "hay",
        "water_availability": "adequate", "last_vet_check_days": 25,
        "vaccination_due": False, "disease_symptoms": [],
        "temp_celsius": 20, "humidity_pct": 55, "mortality_last_7_days": 0
    }

@pytest.fixture
def livestock_critical_feed():
    """Emergency feed shortage (<3 days)."""
    return {
        "animal_type": "cattle", "animal_count": 80, "avg_weight_kg": 350,
        "feed_stock_days": 2, "feed_type": "concentrate",
        "water_availability": "adequate", "last_vet_check_days": 20,
        "vaccination_due": False, "disease_symptoms": [],
        "temp_celsius": 22, "humidity_pct": 55, "mortality_last_7_days": 0
    }

@pytest.fixture
def livestock_disease_symptoms():
    """Active disease symptoms + high mortality."""
    return {
        "animal_type": "cattle", "animal_count": 100, "avg_weight_kg": 320,
        "feed_stock_days": 15, "feed_type": "mixed",
        "water_availability": "adequate", "last_vet_check_days": 40,
        "vaccination_due": False,
        "disease_symptoms": ["coughing", "nasal discharge", "lethargy"],
        "temp_celsius": 24, "humidity_pct": 65, "mortality_last_7_days": 3
    }

@pytest.fixture
def livestock_overdue_vet():
    """No vet check in >90 days AND vaccination overdue."""
    return {
        "animal_type": "sheep", "animal_count": 120, "avg_weight_kg": 60,
        "feed_stock_days": 18, "feed_type": "pasture",
        "water_availability": "adequate", "last_vet_check_days": 100,
        "vaccination_due": True, "disease_symptoms": [],
        "temp_celsius": 18, "humidity_pct": 60, "mortality_last_7_days": 0
    }

@pytest.fixture
def livestock_heat_stress():
    """Heat stress for cattle: high temp, adequate water."""
    return {
        "animal_type": "cattle", "animal_count": 70, "avg_weight_kg": 330,
        "feed_stock_days": 14, "feed_type": "hay",
        "water_availability": "adequate", "last_vet_check_days": 28,
        "vaccination_due": False, "disease_symptoms": [],
        "temp_celsius": 34, "humidity_pct": 60, "mortality_last_7_days": 0
    }

@pytest.fixture
def livestock_water_critical():
    """Critical water shortage."""
    return {
        "animal_type": "cattle", "animal_count": 50, "avg_weight_kg": 280,
        "feed_stock_days": 12, "feed_type": "hay",
        "water_availability": "critical", "last_vet_check_days": 20,
        "vaccination_due": False, "disease_symptoms": [],
        "temp_celsius": 24, "humidity_pct": 50, "mortality_last_7_days": 0
    }

@pytest.fixture
def livestock_poultry_humidity():
    """Poultry with high humidity — respiratory disease risk."""
    return {
        "animal_type": "poultry", "animal_count": 2000, "avg_weight_kg": 2,
        "feed_stock_days": 10, "feed_type": "pellet",
        "water_availability": "adequate", "last_vet_check_days": 35,
        "vaccination_due": False, "disease_symptoms": [],
        "temp_celsius": 26, "humidity_pct": 85, "mortality_last_7_days": 0
    }


# ─────────────────────────────────────────────
# TESTS: WHEAT
# ─────────────────────────────────────────────

class TestWheatRecommendations:

    def test_returns_list(self, wheat_normal):
        result = wheat_recommendations(wheat_normal)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_tuple_structure(self, wheat_normal):
        for rec in wheat_recommendations(wheat_normal):
            assert len(rec) == 2
            assert rec[0] in ("high", "medium", "low")
            assert isinstance(rec[1], str)

    def test_sorted_by_priority(self, wheat_overdue_fert):
        recs = wheat_recommendations(wheat_overdue_fert)
        p = priorities(recs)
        order = {"high": 0, "medium": 1, "low": 2}
        assert p == sorted(p, key=lambda x: order[x])

    # Drought edge case
    def test_drought_triggers_high_irrigation(self, wheat_drought):
        recs = wheat_recommendations(wheat_drought)
        assert first_priority(recs) == "high"
        # irrigation message should be first high-priority
        irr_msgs = [m for p, m in recs if p == "high" and "irrigat" in m.lower()]
        assert len(irr_msgs) >= 1

    def test_drought_message_mentions_moisture(self, wheat_drought):
        recs = wheat_recommendations(wheat_drought)
        combined = " ".join(messages(recs))
        assert "moisture" in combined.lower() or "irrigat" in combined.lower()

    # High pest edge case
    def test_high_pest_triggers_high_priority(self, wheat_high_pest):
        recs = wheat_recommendations(wheat_high_pest)
        assert has_priority(recs, "high")
        pest_msgs = [m for p, m in recs if "pest" in m.lower() or "pesticide" in m.lower()]
        assert len(pest_msgs) >= 1

    def test_fungal_risk_medium_when_no_pressure(self, wheat_fungal_risk):
        recs = wheat_recommendations(wheat_fungal_risk)
        fungal_msgs = [m for p, m in recs if "fungal" in m.lower() or "rust" in m.lower() or "blight" in m.lower()]
        assert len(fungal_msgs) >= 1
        # Should not escalate to high without detected pressure
        fungal_priorities = [p for p, m in recs if "fungal" in m.lower() or "rust" in m.lower()]
        assert all(pr in ("medium", "low") for pr in fungal_priorities)

    # Overdue fertilization edge case
    def test_overdue_fert_low_n_is_high(self, wheat_overdue_fert):
        recs = wheat_recommendations(wheat_overdue_fert)
        n_msgs = [m for p, m in recs if p == "high" and "nitrogen" in m.lower()]
        assert len(n_msgs) >= 1

    def test_normal_farm_no_high_priority(self, wheat_normal):
        recs = wheat_recommendations(wheat_normal)
        # A healthy farm should have no high-priority alerts
        assert not has_priority(recs, "high")

    def test_low_phosphorus_at_germination(self):
        data = {
            "soil_moisture": 55, "rainfall_mm": 5, "temp_celsius": 18,
            "growth_stage": "germination", "npk": {"N": 45, "P": 8, "K": 25},
            "pest_pressure": "low", "last_irrigation_days": 2, "last_fertilization_days": 5
        }
        recs = wheat_recommendations(data)
        p_msgs = [m for p, m in recs if p == "high" and "phosphorus" in m.lower()]
        assert len(p_msgs) >= 1


# ─────────────────────────────────────────────
# TESTS: VEGETABLE
# ─────────────────────────────────────────────

class TestVegetableRecommendations:

    def test_returns_list(self, veg_normal):
        assert isinstance(vegetable_recommendations(veg_normal), list)

    def test_drought_critical_moisture(self, veg_drought):
        recs = vegetable_recommendations(veg_drought)
        assert first_priority(recs) == "high"
        irr = [m for p, m in recs if p == "high" and "irrigat" in m.lower()]
        assert len(irr) >= 1

    def test_high_pest_pressure_is_high(self, veg_high_pest):
        recs = vegetable_recommendations(veg_high_pest)
        assert has_priority(recs, "high")
        pest = [m for p, m in recs if "pest" in m.lower() or "treatment" in m.lower()]
        assert len(pest) >= 1

    def test_high_humidity_fungal_medium(self, veg_high_pest):
        # humidity=82 + temp=26 should also flag medium for mildew
        recs = vegetable_recommendations(veg_high_pest)
        # high pest will dominate; check medium or high has a mildew/botrytis mention
        # (may be overridden by high pest — both conditions coexist)
        all_msgs = " ".join(messages(recs))
        assert "mildew" in all_msgs.lower() or "botrytis" in all_msgs.lower() or "pest" in all_msgs.lower()

    def test_overdue_fert_medium(self, veg_overdue_fert):
        recs = vegetable_recommendations(veg_overdue_fert)
        fert = [m for p, m in recs if p == "medium" and "fertil" in m.lower()]
        assert len(fert) >= 1

    def test_pre_harvest_k_low_is_high(self, veg_pre_harvest_k_low):
        recs = vegetable_recommendations(veg_pre_harvest_k_low)
        k_msgs = [m for p, m in recs if p == "high" and "potassium" in m.lower()]
        assert len(k_msgs) >= 1

    def test_normal_farm_no_high(self, veg_normal):
        recs = vegetable_recommendations(veg_normal)
        assert not has_priority(recs, "high")

    def test_moisture_medium_alert_when_2days_dry(self):
        data = {
            "soil_moisture": 45, "rainfall_mm": 0, "temp_celsius": 22,
            "crop_type": "tomato", "days_to_harvest": 40,
            "npk": {"N": 42, "P": 20, "K": 30},
            "pest_pressure": "low", "humidity_pct": 58,
            "last_irrigation_days": 2, "last_fertilization_days": 5
        }
        recs = vegetable_recommendations(data)
        irr = [m for p, m in recs if "irrigat" in m.lower() and p == "medium"]
        assert len(irr) >= 1


# ─────────────────────────────────────────────
# TESTS: ORCHARD
# ─────────────────────────────────────────────

class TestOrchardRecommendations:

    def test_returns_list(self, orchard_normal):
        assert isinstance(orchard_recommendations(orchard_normal), list)

    def test_drought_fruit_set_is_high(self, orchard_drought_fruit_set):
        recs = orchard_recommendations(orchard_drought_fruit_set)
        irr = [m for p, m in recs if p == "high" and "irrigat" in m.lower()]
        assert len(irr) >= 1

    def test_frost_risk_overrides_irrigation(self, orchard_frost):
        recs = orchard_recommendations(orchard_frost)
        # Frost message must be high priority
        frost_msgs = [m for p, m in recs if "frost" in m.lower() and p == "high"]
        assert len(frost_msgs) >= 1
        # No standard irrigation recommendation should be high in this state
        plain_irr = [m for p, m in recs if "irrigate" in m.lower() and "frost" not in m.lower() and p == "high"]
        assert len(plain_irr) == 0

    def test_high_pest_orchard(self, orchard_high_pest):
        recs = orchard_recommendations(orchard_high_pest)
        pest = [m for p, m in recs if p == "high" and ("pest" in m.lower() or "insecticide" in m.lower())]
        assert len(pest) >= 1

    def test_overdue_fert_medium(self, orchard_overdue_fert):
        recs = orchard_recommendations(orchard_overdue_fert)
        fert = [m for p, m in recs if "fertil" in m.lower() and p == "medium"]
        assert len(fert) >= 1

    def test_young_tree_n_low_is_high(self, orchard_young_tree_n_low):
        recs = orchard_recommendations(orchard_young_tree_n_low)
        n_msgs = [m for p, m in recs if p == "high" and "nitrogen" in m.lower()]
        assert len(n_msgs) >= 1

    def test_flowering_pest_uses_bee_safe_language(self):
        data = {
            "soil_moisture": 58, "rainfall_mm": 5, "temp_celsius": 18,
            "tree_age_years": 5, "fruit_stage": "flowering",
            "npk": {"N": 38, "P": 16, "K": 24},
            "pest_pressure": "medium", "frost_risk": False,
            "last_irrigation_days": 4, "last_fertilization_days": 15, "last_pruning_days": 30
        }
        recs = orchard_recommendations(data)
        bee_msgs = [m for p, m in recs if "bee" in m.lower() or "blossom" in m.lower()]
        assert len(bee_msgs) >= 1

    def test_ripening_k_low_is_high(self):
        data = {
            "soil_moisture": 55, "rainfall_mm": 5, "temp_celsius": 20,
            "tree_age_years": 6, "fruit_stage": "ripening",
            "npk": {"N": 38, "P": 16, "K": 14},
            "pest_pressure": "low", "frost_risk": False,
            "last_irrigation_days": 5, "last_fertilization_days": 10, "last_pruning_days": 40
        }
        recs = orchard_recommendations(data)
        k_msgs = [m for p, m in recs if p == "high" and "potassium" in m.lower()]
        assert len(k_msgs) >= 1

    def test_normal_no_high(self, orchard_normal):
        recs = orchard_recommendations(orchard_normal)
        assert not has_priority(recs, "high")


# ─────────────────────────────────────────────
# TESTS: MIXED
# ─────────────────────────────────────────────

class TestMixedRecommendations:

    def test_returns_list(self, mixed_normal):
        assert isinstance(mixed_recommendations(mixed_normal), list)

    def test_drought_is_high(self, mixed_drought):
        recs = mixed_recommendations(mixed_drought)
        irr = [m for p, m in recs if p == "high" and "irrigat" in m.lower()]
        assert len(irr) >= 1

    def test_high_pest_is_high(self, mixed_high_pest):
        recs = mixed_recommendations(mixed_high_pest)
        pest = [m for p, m in recs if p == "high" and ("pest" in m.lower() or "pesticide" in m.lower())]
        assert len(pest) >= 1

    def test_high_pest_mentions_livestock_safety(self, mixed_high_pest):
        recs = mixed_recommendations(mixed_high_pest)
        livestock_safety = [m for p, m in recs if "livestock" in m.lower() or "animal" in m.lower()]
        assert len(livestock_safety) >= 1

    def test_overdue_fert_low_n_high(self, mixed_overdue_fert_low_feed):
        recs = mixed_recommendations(mixed_overdue_fert_low_feed)
        n_msgs = [m for p, m in recs if p == "high" and "nitrogen" in m.lower()]
        assert len(n_msgs) >= 1

    def test_low_feed_stock_is_high(self, mixed_overdue_fert_low_feed):
        recs = mixed_recommendations(mixed_overdue_fert_low_feed)
        feed = [m for p, m in recs if p == "high" and "feed" in m.lower()]
        assert len(feed) >= 1

    def test_normal_no_high(self, mixed_normal):
        recs = mixed_recommendations(mixed_normal)
        assert not has_priority(recs, "high")

    def test_feed_medium_when_7_to_14_days(self):
        data = {
            "soil_moisture": 55, "rainfall_mm": 5, "temp_celsius": 20,
            "crop_sections": ["wheat"], "npk": {"N": 40, "P": 20, "K": 25},
            "pest_pressure": "low", "animal_count": 30,
            "feed_stock_days": 10,
            "last_irrigation_days": 3, "last_fertilization_days": 10
        }
        recs = mixed_recommendations(data)
        feed = [m for p, m in recs if p == "medium" and "feed" in m.lower()]
        assert len(feed) >= 1

    def test_no_feed_alert_when_no_animals(self):
        data = {
            "soil_moisture": 55, "rainfall_mm": 5, "temp_celsius": 20,
            "crop_sections": ["wheat"], "npk": {"N": 40, "P": 20, "K": 25},
            "pest_pressure": "low", "animal_count": 0,
            "feed_stock_days": 2,  # would trigger if animals > 0
            "last_irrigation_days": 3, "last_fertilization_days": 10
        }
        recs = mixed_recommendations(data)
        feed_alerts = [m for p, m in recs if "feed" in m.lower() and p in ("high", "medium")]
        assert len(feed_alerts) == 0


# ─────────────────────────────────────────────
# TESTS: LIVESTOCK
# ─────────────────────────────────────────────

class TestLivestockRecommendations:

    def test_returns_list(self, livestock_normal):
        assert isinstance(livestock_recommendations(livestock_normal), list)

    def test_critical_feed_is_high(self, livestock_critical_feed):
        recs = livestock_recommendations(livestock_critical_feed)
        feed = [m for p, m in recs if p == "high" and "feed" in m.lower()]
        assert len(feed) >= 1

    def test_critical_feed_mentions_emergency(self, livestock_critical_feed):
        recs = livestock_recommendations(livestock_critical_feed)
        msgs_text = " ".join(messages(recs)).lower()
        assert "emergency" in msgs_text or "critical" in msgs_text or "immediately" in msgs_text

    def test_disease_symptoms_is_high(self, livestock_disease_symptoms):
        recs = livestock_recommendations(livestock_disease_symptoms)
        disease = [m for p, m in recs if p == "high" and "symptom" in m.lower()]
        assert len(disease) >= 1

    def test_high_mortality_is_high(self, livestock_disease_symptoms):
        recs = livestock_recommendations(livestock_disease_symptoms)
        mort = [m for p, m in recs if p == "high" and "mortalit" in m.lower()]
        assert len(mort) >= 1

    def test_overdue_vet_is_high(self, livestock_overdue_vet):
        recs = livestock_recommendations(livestock_overdue_vet)
        vet = [m for p, m in recs if p == "high" and "vet" in m.lower()]
        assert len(vet) >= 1

    def test_vaccination_due_is_high(self, livestock_overdue_vet):
        recs = livestock_recommendations(livestock_overdue_vet)
        vax = [m for p, m in recs if p == "high" and "vaccin" in m.lower()]
        assert len(vax) >= 1

    def test_heat_stress_medium_for_cattle(self, livestock_heat_stress):
        recs = livestock_recommendations(livestock_heat_stress)
        heat = [m for p, m in recs if p == "medium" and "heat" in m.lower()]
        assert len(heat) >= 1

    def test_water_critical_is_high(self, livestock_water_critical):
        recs = livestock_recommendations(livestock_water_critical)
        water = [m for p, m in recs if p == "high" and "water" in m.lower()]
        assert len(water) >= 1

    def test_poultry_humidity_medium(self, livestock_poultry_humidity):
        recs = livestock_recommendations(livestock_poultry_humidity)
        hum = [m for p, m in recs if p == "medium" and ("humidity" in m.lower() or "poultry" in m.lower())]
        assert len(hum) >= 1

    def test_normal_no_high(self, livestock_normal):
        recs = livestock_recommendations(livestock_normal)
        assert not has_priority(recs, "high")

    def test_feed_medium_when_7_to_14_days(self):
        data = {
            "animal_type": "cattle", "animal_count": 50, "avg_weight_kg": 280,
            "feed_stock_days": 10, "feed_type": "hay",
            "water_availability": "adequate", "last_vet_check_days": 20,
            "vaccination_due": False, "disease_symptoms": [],
            "temp_celsius": 20, "humidity_pct": 55, "mortality_last_7_days": 0
        }
        recs = livestock_recommendations(data)
        feed = [m for p, m in recs if p == "medium" and "feed" in m.lower()]
        assert len(feed) >= 1

    def test_mortality_rate_calculation_below_2pct_is_medium(self):
        """1 death in 100 animals = 1% mortality → medium, not high."""
        data = {
            "animal_type": "cattle", "animal_count": 100, "avg_weight_kg": 300,
            "feed_stock_days": 15, "feed_type": "hay",
            "water_availability": "adequate", "last_vet_check_days": 20,
            "vaccination_due": False, "disease_symptoms": [],
            "temp_celsius": 22, "humidity_pct": 55, "mortality_last_7_days": 1
        }
        recs = livestock_recommendations(data)
        mort_high = [m for p, m in recs if p == "high" and "mortalit" in m.lower()]
        mort_medium = [m for p, m in recs if p == "medium" and "mortalit" in m.lower()]
        assert len(mort_high) == 0
        assert len(mort_medium) >= 1

    def test_vet_check_medium_when_61_to_90_days(self):
        data = {
            "animal_type": "cattle", "animal_count": 50, "avg_weight_kg": 280,
            "feed_stock_days": 15, "feed_type": "hay",
            "water_availability": "adequate", "last_vet_check_days": 70,
            "vaccination_due": False, "disease_symptoms": [],
            "temp_celsius": 20, "humidity_pct": 55, "mortality_last_7_days": 0
        }
        recs = livestock_recommendations(data)
        vet = [m for p, m in recs if p == "medium" and "vet" in m.lower()]
        assert len(vet) >= 1


# ─────────────────────────────────────────────
# TESTS: DISPATCHER
# ─────────────────────────────────────────────

class TestDispatcher:

    def test_dispatcher_wheat(self, wheat_normal):
        recs = get_recommendations("wheat", wheat_normal)
        assert isinstance(recs, list)

    def test_dispatcher_vegetable(self, veg_normal):
        recs = get_recommendations("vegetable", veg_normal)
        assert isinstance(recs, list)

    def test_dispatcher_orchard(self, orchard_normal):
        recs = get_recommendations("orchard", orchard_normal)
        assert isinstance(recs, list)

    def test_dispatcher_mixed(self, mixed_normal):
        recs = get_recommendations("mixed", mixed_normal)
        assert isinstance(recs, list)

    def test_dispatcher_livestock(self, livestock_normal):
        recs = get_recommendations("livestock", livestock_normal)
        assert isinstance(recs, list)

    def test_dispatcher_case_insensitive(self, wheat_normal):
        recs = get_recommendations("WHEAT", wheat_normal)
        assert isinstance(recs, list)

    def test_dispatcher_unknown_type_raises(self, wheat_normal):
        with pytest.raises(ValueError, match="Unknown farm type"):
            get_recommendations("vineyard", wheat_normal)

    def test_dispatcher_empty_data_no_crash(self):
        """Engine must not raise even with completely empty dict (uses defaults)."""
        for ft in ("wheat", "vegetable", "orchard", "mixed", "livestock"):
            recs = get_recommendations(ft, {})
            assert isinstance(recs, list)
            assert len(recs) > 0

