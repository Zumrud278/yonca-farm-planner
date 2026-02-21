# engine.py — Yonca AI Planner: Rule-Based Recommendation Engine
# Each function accepts a farm_data dict and returns a list of
# (priority, recommendation) tuples sorted high → medium → low.

from datetime import datetime

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _sort(recs):
    """Sort recommendations by priority level."""
    return sorted(recs, key=lambda x: PRIORITY_ORDER.get(x[0], 3))


# ─────────────────────────────────────────────
# WHEAT FARM
# ─────────────────────────────────────────────
def wheat_recommendations(farm_data: dict) -> list:
    """
    Recommendations for wheat farms.
    Expected schema fields:
      soil_moisture (float, %), rainfall_mm (float), temp_celsius (float),
      growth_stage (str), npk (dict: N/P/K float), pest_pressure (str: low/medium/high),
      last_irrigation_days (int), last_fertilization_days (int)
    """
    recs = []
    soil_moisture    = farm_data.get("soil_moisture", 50)
    rainfall_mm      = farm_data.get("rainfall_mm", 0)
    temp_c           = farm_data.get("temp_celsius", 20)
    growth_stage     = farm_data.get("growth_stage", "vegetative")
    npk              = farm_data.get("npk", {"N": 40, "P": 20, "K": 20})
    pest_pressure    = farm_data.get("pest_pressure", "low")
    last_irrig_days  = farm_data.get("last_irrigation_days", 3)
    last_fert_days   = farm_data.get("last_fertilization_days", 14)

    # ── IRRIGATION ──────────────────────────────
    # Critical dryness: moisture below 30% and no significant rain
    if soil_moisture < 30 and rainfall_mm < 5:
        recs.append(("high", "Irrigate immediately — soil moisture critically low (<30%) with negligible rainfall."))
    # Moderate dryness at sensitive tillering/heading stages
    elif soil_moisture < 45 and growth_stage in ("tillering", "heading"):
        recs.append(("high", f"Irrigate soon — moisture at {soil_moisture}% during sensitive {growth_stage} stage."))
    # General low moisture reminder
    elif soil_moisture < 50 and last_irrig_days > 4:
        recs.append(("medium", "Schedule irrigation — moisture below 50% and >4 days since last watering."))
    # Soil is sufficiently moist
    else:
        recs.append(("low", "Soil moisture adequate; monitor and irrigate if it drops below 50%."))

    # ── FERTILIZATION ────────────────────────────
    # Nitrogen is the primary driver for wheat yield
    if npk.get("N", 40) < 20:
        recs.append(("high", "Apply nitrogen fertilizer urgently — N levels critically low (<20 kg/ha)."))
    elif npk.get("N", 40) < 35 and last_fert_days > 10:
        recs.append(("medium", "Top-dress with nitrogen — levels moderate and >10 days since last application."))
    # Phosphorus matters most at early growth
    if npk.get("P", 20) < 10 and growth_stage == "germination":
        recs.append(("high", "Apply phosphorus starter — P very low during germination stage."))
    elif npk.get("P", 20) < 15:
        recs.append(("medium", "Phosphorus slightly low; consider balanced NPK application."))
    if npk.get("K", 20) < 15:
        recs.append(("medium", "Potassium below threshold; apply potash to improve stress tolerance."))

    # ── PEST RISK ────────────────────────────────
    # High temperature + humidity creates aphid/rust risk
    if pest_pressure == "high":
        recs.append(("high", "High pest pressure detected — apply appropriate pesticide/fungicide immediately."))
    elif pest_pressure == "medium" and temp_c > 25:
        recs.append(("medium", "Moderate pest pressure with warm temperatures — scout fields and prepare treatment."))
    elif temp_c > 28 and rainfall_mm > 20:
        # Warm + wet = fungal disease risk even without detected pressure
        recs.append(("medium", "Conditions favour fungal diseases (rust/blight) — consider preventive fungicide."))
    else:
        recs.append(("low", "Pest risk currently low; maintain regular scouting every 7 days."))

    return _sort(recs)


# ─────────────────────────────────────────────
# VEGETABLE FARM
# ─────────────────────────────────────────────
def vegetable_recommendations(farm_data: dict) -> list:
    """
    Recommendations for vegetable farms.
    Expected schema fields:
      soil_moisture (float, %), rainfall_mm (float), temp_celsius (float),
      crop_type (str), days_to_harvest (int), npk (dict),
      pest_pressure (str), humidity_pct (float), last_irrigation_days (int),
      last_fertilization_days (int)
    """
    recs = []
    soil_moisture   = farm_data.get("soil_moisture", 55)
    rainfall_mm     = farm_data.get("rainfall_mm", 0)
    temp_c          = farm_data.get("temp_celsius", 22)
    crop_type       = farm_data.get("crop_type", "tomato")
    days_to_harvest = farm_data.get("days_to_harvest", 30)
    npk             = farm_data.get("npk", {"N": 40, "P": 20, "K": 30})
    pest_pressure   = farm_data.get("pest_pressure", "low")
    humidity        = farm_data.get("humidity_pct", 60)
    last_irrig_days = farm_data.get("last_irrigation_days", 2)
    last_fert_days  = farm_data.get("last_fertilization_days", 7)

    # ── IRRIGATION ──────────────────────────────
    # Vegetables need consistent moisture; very sensitive to drought
    if soil_moisture < 35:
        recs.append(("high", "Irrigate immediately — soil moisture critically low for vegetables (<35%)."))
    elif soil_moisture < 50 and last_irrig_days >= 2:
        recs.append(("medium", "Irrigate within 24 hours — moisture dropping and 2+ days since last irrigation."))
    elif days_to_harvest <= 14 and soil_moisture < 60:
        # Pre-harvest consistent moisture prevents cracking / quality issues
        recs.append(("medium", "Maintain consistent irrigation near harvest — prevents blossom end rot and cracking."))
    else:
        recs.append(("low", "Moisture adequate; use drip irrigation to maintain 55–70% soil moisture."))

    # ── FERTILIZATION ────────────────────────────
    if npk.get("N", 40) < 25:
        recs.append(("high", "Nitrogen deficiency likely — apply foliar or granular N fertilizer."))
    elif npk.get("K", 30) < 20 and days_to_harvest <= 21:
        # Potassium critical for fruit quality near harvest
        recs.append(("high", "Boost potassium before harvest — essential for fruit quality and shelf life."))
    elif last_fert_days > 14:
        recs.append(("medium", "Fertilization overdue (>14 days) — apply balanced NPK for continued growth."))
    else:
        recs.append(("low", "Nutrient levels acceptable; next fertilization due in ~7 days."))

    # ── PEST RISK ────────────────────────────────
    # High humidity + warm temps = whitefly, mildew, botrytis risk
    if pest_pressure == "high":
        recs.append(("high", "Severe pest pressure — immediately apply targeted treatment and remove affected plants."))
    elif humidity > 75 and temp_c > 22:
        recs.append(("medium", f"High humidity ({humidity}%) and warm temps favour mildew/botrytis — apply preventive fungicide."))
    elif pest_pressure == "medium":
        recs.append(("medium", "Moderate pest activity — deploy sticky traps and scout undersides of leaves."))
    else:
        recs.append(("low", "Pest risk low; inspect plants twice weekly and maintain good air circulation."))

    return _sort(recs)


# ─────────────────────────────────────────────
# ORCHARD FARM
# ─────────────────────────────────────────────
def orchard_recommendations(farm_data: dict) -> list:
    """
    Recommendations for orchard farms (fruit trees).
    Expected schema fields:
      soil_moisture (float, %), rainfall_mm (float), temp_celsius (float),
      tree_age_years (int), fruit_stage (str: dormant/flowering/fruit_set/ripening),
      npk (dict), pest_pressure (str), frost_risk (bool),
      last_irrigation_days (int), last_fertilization_days (int), last_pruning_days (int)
    """
    recs = []
    soil_moisture   = farm_data.get("soil_moisture", 55)
    rainfall_mm     = farm_data.get("rainfall_mm", 0)
    temp_c          = farm_data.get("temp_celsius", 18)
    tree_age        = farm_data.get("tree_age_years", 5)
    fruit_stage     = farm_data.get("fruit_stage", "fruit_set")
    npk             = farm_data.get("npk", {"N": 35, "P": 15, "K": 25})
    pest_pressure   = farm_data.get("pest_pressure", "low")
    frost_risk      = farm_data.get("frost_risk", False)
    last_irrig_days = farm_data.get("last_irrigation_days", 5)
    last_fert_days  = farm_data.get("last_fertilization_days", 21)

    # ── IRRIGATION ──────────────────────────────
    # Frost + irrigation is dangerous — do not irrigate before a freeze
    if frost_risk and temp_c < 4:
        recs.append(("high", "Frost risk detected — avoid irrigation now; consider wind machines or heaters to protect blossoms."))
    elif fruit_stage == "fruit_set" and soil_moisture < 45:
        # Fruit set is the most critical moisture stage for yield
        recs.append(("high", "Critical: irrigate during fruit set — moisture deficit now causes fruit drop."))
    elif soil_moisture < 40 and rainfall_mm < 5:
        recs.append(("high", "Soil moisture very low — irrigate orchard to prevent tree stress."))
    elif soil_moisture < 55 and last_irrig_days > 6:
        recs.append(("medium", "Moisture declining and >6 days since last irrigation — schedule watering."))
    else:
        recs.append(("low", "Moisture adequate for current stage; deep irrigate every 7–10 days."))

    # ── FERTILIZATION ────────────────────────────
    # Young trees need more N for establishment
    if tree_age < 3 and npk.get("N", 35) < 30:
        recs.append(("high", "Young tree N deficiency — apply nitrogen to support establishment and canopy growth."))
    elif fruit_stage == "ripening" and npk.get("K", 25) < 20:
        # K drives sugar accumulation and colour in ripening fruit
        recs.append(("high", "Potassium low during ripening — apply K fertilizer to improve fruit quality and colour."))
    elif last_fert_days > 30 and fruit_stage not in ("dormant",):
        recs.append(("medium", "Fertilization gap >30 days — apply balanced NPK to sustain active growth stage."))
    elif npk.get("P", 15) < 10:
        recs.append(("medium", "Phosphorus low — apply to support root health and disease resistance."))
    else:
        recs.append(("low", "Nutrient status adequate; next fertilization in 3–4 weeks."))

    # ── PEST RISK ────────────────────────────────
    if pest_pressure == "high":
        recs.append(("high", "High pest pressure — apply appropriate insecticide/fungicide; check for codling moth or fire blight."))
    elif fruit_stage == "flowering" and pest_pressure != "low":
        # Avoid broad-spectrum sprays during flowering to protect pollinators
        recs.append(("medium", "Pest activity during flowering — use bee-safe treatments only; do not spray open blossoms."))
    elif temp_c > 25 and pest_pressure == "medium":
        recs.append(("medium", "Warm conditions elevating pest risk — monitor for mites and apply targeted miticide if needed."))
    else:
        recs.append(("low", "Pest risk manageable; scout weekly and maintain pheromone traps."))

    return _sort(recs)


# ─────────────────────────────────────────────
# MIXED FARM
# ─────────────────────────────────────────────
def mixed_recommendations(farm_data: dict) -> list:
    """
    Recommendations for mixed (crop + livestock) farms.
    Expected schema fields:
      crop_sections (list of str), soil_moisture (float, %),
      rainfall_mm (float), temp_celsius (float), npk (dict),
      pest_pressure (str), animal_count (int), feed_stock_days (int),
      last_irrigation_days (int), last_fertilization_days (int)
    """
    recs = []
    soil_moisture   = farm_data.get("soil_moisture", 50)
    rainfall_mm     = farm_data.get("rainfall_mm", 0)
    temp_c          = farm_data.get("temp_celsius", 20)
    npk             = farm_data.get("npk", {"N": 35, "P": 18, "K": 22})
    pest_pressure   = farm_data.get("pest_pressure", "low")
    crop_sections   = farm_data.get("crop_sections", [])
    animal_count    = farm_data.get("animal_count", 0)
    feed_stock_days = farm_data.get("feed_stock_days", 10)
    last_irrig_days = farm_data.get("last_irrigation_days", 4)
    last_fert_days  = farm_data.get("last_fertilization_days", 14)

    # ── IRRIGATION ──────────────────────────────
    if soil_moisture < 35:
        recs.append(("high", "Soil moisture critically low across crop sections — initiate irrigation immediately."))
    elif soil_moisture < 50 and last_irrig_days > 3:
        recs.append(("medium", "Moisture declining and >3 days since irrigation — schedule field-by-field watering."))
    else:
        recs.append(("low", "Soil moisture adequate; adjust schedule based on dominant crop type in each section."))

    # ── FERTILIZATION ────────────────────────────
    # Mixed farms often have uneven nutrient draw from diverse crops
    if npk.get("N", 35) < 25:
        recs.append(("high", "Nitrogen critically low — apply N fertilizer prioritising highest-yield crop sections."))
    elif last_fert_days > 21:
        recs.append(("medium", "21+ days since fertilization — conduct soil test and apply balanced fertilizer."))
    elif len(crop_sections) > 2 and npk.get("K", 22) < 18:
        # Multiple crop types deplete K faster
        recs.append(("medium", "Potassium declining in multi-crop scenario — apply potash across all sections."))
    else:
        recs.append(("low", "Nutrient levels stable; schedule soil analysis every 4–6 weeks."))

    # ── PEST RISK ────────────────────────────────
    if pest_pressure == "high":
        recs.append(("high", "High pest pressure — treat affected sections; ensure livestock are moved away from treated areas."))
    elif pest_pressure == "medium" and temp_c > 24:
        recs.append(("medium", "Warm conditions with moderate pest pressure — scout all crop sections and apply targeted control."))
    else:
        recs.append(("low", "Pest risk low; cross-check that livestock grazing rotation doesn't concentrate pests."))

    # Mixed-farm specific: feed stock warning for animals
    if animal_count > 0 and feed_stock_days < 7:
        recs.append(("high", f"Feed stock critically low (<7 days) for {animal_count} animals — reorder feed immediately."))
    elif animal_count > 0 and feed_stock_days < 14:
        recs.append(("medium", f"Feed stock at ~{feed_stock_days} days — plan resupply for livestock within the week."))

    return _sort(recs)


# ─────────────────────────────────────────────
# LIVESTOCK FARM
# ─────────────────────────────────────────────
def livestock_recommendations(farm_data: dict) -> list:
    """
    Recommendations for livestock-only farms.
    Expected schema fields:
      animal_type (str: cattle/sheep/poultry/swine),
      animal_count (int), avg_weight_kg (float),
      feed_stock_days (int), feed_type (str),
      water_availability (str: adequate/low/critical),
      last_vet_check_days (int), vaccination_due (bool),
      disease_symptoms (list of str), temp_celsius (float),
      humidity_pct (float), mortality_last_7_days (int)
    """
    recs = []
    animal_type        = farm_data.get("animal_type", "cattle")
    animal_count       = farm_data.get("animal_count", 50)
    avg_weight         = farm_data.get("avg_weight_kg", 200)
    feed_stock_days    = farm_data.get("feed_stock_days", 14)
    feed_type          = farm_data.get("feed_type", "mixed")
    water_avail        = farm_data.get("water_availability", "adequate")
    last_vet_days      = farm_data.get("last_vet_check_days", 30)
    vaccination_due    = farm_data.get("vaccination_due", False)
    disease_symptoms   = farm_data.get("disease_symptoms", [])
    temp_c             = farm_data.get("temp_celsius", 22)
    humidity           = farm_data.get("humidity_pct", 55)
    mortality_7d       = farm_data.get("mortality_last_7_days", 0)

    # ── FEEDING SCHEDULE ─────────────────────────
    # Water is the first nutrition concern
    if water_avail == "critical":
        recs.append(("high", "Water supply critical — restore water access immediately; dehydration kills within 24–48 h."))
    elif water_avail == "low":
        recs.append(("medium", "Water supply low — increase water delivery or repair supply; monitor for dehydration signs."))

    # Feed stock runway
    if feed_stock_days < 3:
        recs.append(("high", f"Feed stock below 3-day threshold for {animal_count} {animal_type} — emergency resupply required."))
    elif feed_stock_days < 7:
        recs.append(("high", f"Feed stock at {feed_stock_days} days — order feed immediately to avoid rationing."))
    elif feed_stock_days < 14:
        recs.append(("medium", "Feed supply at ~2 weeks — initiate resupply order to maintain buffer stock."))
    else:
        recs.append(("low", f"Feed stock adequate ({feed_stock_days} days); ensure feed quality and check for spoilage."))

    # Heat stress affects feed intake
    if temp_c > 30 and animal_type in ("cattle", "swine"):
        recs.append(("medium", f"Heat stress risk at {temp_c}°C — shift feeding to cooler morning/evening hours and increase water."))

    # ── DISEASE RISK ─────────────────────────────
    # Mortality is the strongest disease signal
    if mortality_7d > 0:
        rate = round(mortality_7d / animal_count * 100, 1)
        if rate >= 2:
            recs.append(("high", f"Elevated mortality: {mortality_7d} deaths ({rate}%) in 7 days — isolate herd and contact vet urgently."))
        else:
            recs.append(("medium", f"Unusual mortality ({mortality_7d} animal(s)) this week — monitor closely and report to vet."))

    # Observable symptoms
    if disease_symptoms:
        symptom_str = ", ".join(disease_symptoms)
        recs.append(("high", f"Disease symptoms reported ({symptom_str}) — isolate affected animals and call vet immediately."))

    # Environmental disease triggers
    if humidity > 80 and temp_c > 25:
        recs.append(("medium", "Hot and humid conditions increase respiratory disease risk — improve ventilation in shelters."))
    elif humidity > 80 and animal_type == "poultry":
        recs.append(("medium", "High humidity in poultry house — risk of Newcastle/respiratory disease; improve airflow."))

    # ── VET CHECK ────────────────────────────────
    if vaccination_due:
        recs.append(("high", "Vaccinations are overdue — schedule vet visit immediately to prevent outbreak."))

    if last_vet_days > 90:
        recs.append(("high", f"No vet check in {last_vet_days} days — schedule comprehensive health inspection."))
    elif last_vet_days > 60:
        recs.append(("medium", f"Last vet check was {last_vet_days} days ago — book routine inspection within 2 weeks."))
    elif last_vet_days > 30 and animal_type == "poultry":
        # Poultry deteriorates faster; more frequent checks recommended
        recs.append(("medium", "Poultry vet check recommended every 30 days — book appointment soon."))
    else:
        recs.append(("low", f"Vet check recent ({last_vet_days} days ago); next routine check due at 60-day mark."))

    return _sort(recs)


# ─────────────────────────────────────────────
# DISPATCHER
# ─────────────────────────────────────────────
FARM_ENGINES = {
    "wheat":      wheat_recommendations,
    "vegetable":  vegetable_recommendations,
    "orchard":    orchard_recommendations,
    "mixed":      mixed_recommendations,
    "livestock":  livestock_recommendations,
}

def get_recommendations(farm_type: str, farm_data: dict) -> list:
    """
    Public entry point.
    Returns list of (priority, recommendation) tuples for the given farm_type.
    Raises ValueError for unknown farm types.
    """
    engine = FARM_ENGINES.get(farm_type.lower())
    if not engine:
        raise ValueError(f"Unknown farm type '{farm_type}'. Choose from: {list(FARM_ENGINES.keys())}")
    return engine(farm_data)


# ─────────────────────────────────────────────
# QUICK DEMO
# ─────────────────────────────────────────────
if __name__ == "__main__":
    samples = {
        "wheat": {
            "soil_moisture": 28, "rainfall_mm": 2, "temp_celsius": 27,
            "growth_stage": "heading", "npk": {"N": 18, "P": 12, "K": 25},
            "pest_pressure": "medium", "last_irrigation_days": 6, "last_fertilization_days": 12
        },
        "vegetable": {
            "soil_moisture": 42, "rainfall_mm": 0, "temp_celsius": 24,
            "crop_type": "tomato", "days_to_harvest": 10, "npk": {"N": 22, "P": 15, "K": 18},
            "pest_pressure": "high", "humidity_pct": 78, "last_irrigation_days": 3, "last_fertilization_days": 16
        },
        "orchard": {
            "soil_moisture": 48, "rainfall_mm": 3, "temp_celsius": 20,
            "tree_age_years": 4, "fruit_stage": "ripening", "npk": {"N": 30, "P": 9, "K": 17},
            "pest_pressure": "medium", "frost_risk": False,
            "last_irrigation_days": 7, "last_fertilization_days": 35, "last_pruning_days": 60
        },
        "mixed": {
            "soil_moisture": 38, "rainfall_mm": 1, "temp_celsius": 25,
            "crop_sections": ["wheat", "sunflower", "alfalfa"],
            "npk": {"N": 23, "P": 14, "K": 16}, "pest_pressure": "medium",
            "animal_count": 40, "feed_stock_days": 5,
            "last_irrigation_days": 5, "last_fertilization_days": 22
        },
        "livestock": {
            "animal_type": "cattle", "animal_count": 80, "avg_weight_kg": 350,
            "feed_stock_days": 4, "feed_type": "hay+concentrate",
            "water_availability": "low", "last_vet_check_days": 75,
            "vaccination_due": True, "disease_symptoms": ["coughing", "nasal discharge"],
            "temp_celsius": 32, "humidity_pct": 82, "mortality_last_7_days": 2
        },
    }

    for farm_type, data in samples.items():
        print(f"\n{'='*55}")
        print(f"  {farm_type.upper()} FARM RECOMMENDATIONS")
        print(f"{'='*55}")
        for priority, msg in get_recommendations(farm_type, data):
            tag = f"[{priority.upper()}]"
            print(f"  {tag:<10} {msg}")

