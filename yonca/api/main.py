# main.py — Yonca AI Planner FastAPI Application
# Run with: uvicorn main:app --reload
from __future__ import annotations

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from engine.engine import *

from datetime import date, timedelta
from typing import Any, Dict, List, Literal, Optional
import re

from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# from engine import get_recommendations, FARM_ENGINES

# ─────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────

app = FastAPI(
    title="Yonca Farm Planner API",
    description="Rule-based agricultural recommendation engine for wheat, vegetable, orchard, mixed and livestock farms.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# DEMO FARM PROFILES (in-memory store)
# ─────────────────────────────────────────────

DEMO_FARMS: Dict[str, Dict[str, Any]] = {
    "farm-001": {
        "farm_id": "farm-001",
        "name": "Aksu Wheat Fields",
        "farm_type": "wheat",
        "location": "Konya, Turkey",
        "area_ha": 120,
        "data": {
            "soil_moisture": 28,
            "rainfall_mm": 2,
            "temp_celsius": 27,
            "growth_stage": "heading",
            "npk": {"N": 18, "P": 12, "K": 25},
            "pest_pressure": "medium",
            "last_irrigation_days": 6,
            "last_fertilization_days": 12,
        },
    },
    "farm-002": {
        "farm_id": "farm-002",
        "name": "Yeşilova Greenhouse",
        "farm_type": "vegetable",
        "location": "Antalya, Turkey",
        "area_ha": 8,
        "data": {
            "soil_moisture": 42,
            "rainfall_mm": 0,
            "temp_celsius": 24,
            "crop_type": "tomato",
            "days_to_harvest": 10,
            "npk": {"N": 22, "P": 15, "K": 18},
            "pest_pressure": "high",
            "humidity_pct": 78,
            "last_irrigation_days": 3,
            "last_fertilization_days": 16,
        },
    },
    "farm-003": {
        "farm_id": "farm-003",
        "name": "Ege Orchard Estate",
        "farm_type": "orchard",
        "location": "İzmir, Turkey",
        "area_ha": 45,
        "data": {
            "soil_moisture": 48,
            "rainfall_mm": 3,
            "temp_celsius": 20,
            "tree_age_years": 4,
            "fruit_stage": "ripening",
            "npk": {"N": 30, "P": 9, "K": 17},
            "pest_pressure": "medium",
            "frost_risk": False,
            "last_irrigation_days": 7,
            "last_fertilization_days": 35,
            "last_pruning_days": 60,
        },
    },
    "farm-004": {
        "farm_id": "farm-004",
        "name": "Dağlı Mixed Farm",
        "farm_type": "mixed",
        "location": "Eskişehir, Turkey",
        "area_ha": 200,
        "data": {
            "soil_moisture": 38,
            "rainfall_mm": 1,
            "temp_celsius": 25,
            "crop_sections": ["wheat", "sunflower", "alfalfa"],
            "npk": {"N": 23, "P": 14, "K": 16},
            "pest_pressure": "medium",
            "animal_count": 40,
            "feed_stock_days": 5,
            "last_irrigation_days": 5,
            "last_fertilization_days": 22,
        },
    },
    "farm-005": {
        "farm_id": "farm-005",
        "name": "Bozkır Livestock Ranch",
        "farm_type": "livestock",
        "location": "Kars, Turkey",
        "area_ha": 350,
        "data": {
            "animal_type": "cattle",
            "animal_count": 80,
            "avg_weight_kg": 350,
            "feed_stock_days": 4,
            "feed_type": "hay+concentrate",
            "water_availability": "low",
            "last_vet_check_days": 75,
            "vaccination_due": True,
            "disease_symptoms": ["coughing", "nasal discharge"],
            "temp_celsius": 32,
            "humidity_pct": 82,
            "mortality_last_7_days": 2,
        },
    },
}

# ─────────────────────────────────────────────
# SCHEDULE TEMPLATES per farm type
# ─────────────────────────────────────────────

SCHEDULE_TEMPLATES: Dict[str, List[Dict[str, str]]] = {
    "wheat": [
        {"time": "06:00", "task": "Field moisture check — walk perimeter and record soil readings"},
        {"time": "07:00", "task": "Irrigation system inspection and runtime adjustment"},
        {"time": "09:00", "task": "Scout for pest activity (aphids, rust lesions) — log observations"},
        {"time": "11:00", "task": "Fertilizer application if scheduled (check NPK log)"},
        {"time": "14:00", "task": "Weather data review — adjust irrigation plan for next 48 h"},
        {"time": "17:00", "task": "Equipment maintenance check (sprayers, irrigation pipes)"},
        {"time": "19:00", "task": "Daily farm log update and next-day task prep"},
    ],
    "vegetable": [
        {"time": "06:00", "task": "Greenhouse / field humidity and temperature check"},
        {"time": "07:00", "task": "Drip irrigation system check — verify emitters and flow rates"},
        {"time": "08:30", "task": "Foliar inspection for pest signs (whitefly, mites, mildew)"},
        {"time": "10:00", "task": "Fertigation cycle — inject nutrients per scheduled NPK plan"},
        {"time": "13:00", "task": "Harvest readiness assessment — record days-to-harvest per bed"},
        {"time": "16:00", "task": "Preventive fungicide spray if humidity >75%"},
        {"time": "18:00", "task": "Daily log and harvest scheduling update"},
    ],
    "orchard": [
        {"time": "06:30", "task": "Frost / temperature alert check — deploy heaters if <4°C"},
        {"time": "07:30", "task": "Soil moisture probe reading — adjust drip irrigation run time"},
        {"time": "09:00", "task": "Tree canopy scouting — look for codling moth, fire blight, mites"},
        {"time": "11:00", "task": "Fertilizer or foliar spray application (avoid open bloom hours)"},
        {"time": "13:00", "task": "Fruit development assessment — measure brix if ripening stage"},
        {"time": "16:00", "task": "Pruning or canopy management if scheduled"},
        {"time": "18:30", "task": "Pheromone trap check and pest count log"},
    ],
    "mixed": [
        {"time": "06:00", "task": "Animal headcount and welfare visual check"},
        {"time": "07:00", "task": "Crop section moisture and temperature readings"},
        {"time": "08:00", "task": "Livestock feeding — morning ration distribution"},
        {"time": "10:00", "task": "Crop irrigation cycle — prioritise highest-need section"},
        {"time": "12:00", "task": "Feed and water stock inventory update"},
        {"time": "14:00", "task": "Crop pest scouting — move livestock away from treated zones"},
        {"time": "17:00", "task": "Livestock evening feeding and water trough check"},
        {"time": "19:00", "task": "Daily integrated log — crops and livestock summary"},
    ],
    "livestock": [
        {"time": "06:00", "task": "Headcount and morning health observation — flag any lethargic animals"},
        {"time": "07:00", "task": "Morning feed distribution — measure and record rations"},
        {"time": "08:30", "task": "Water trough and supply system check"},
        {"time": "10:00", "task": "Manure management and shelter hygiene inspection"},
        {"time": "12:00", "task": "Mid-day health check — check for heat stress if temp >30°C"},
        {"time": "15:00", "task": "Afternoon feed distribution (if twice-daily schedule)"},
        {"time": "17:30", "task": "Mortality and illness log update — report to vet if needed"},
        {"time": "19:00", "task": "Feed stock inventory — trigger resupply if <14 days remaining"},
    ],
}

# ─────────────────────────────────────────────
# PYDANTIC MODELS
# ─────────────────────────────────────────────

class NPK(BaseModel):
    N: float = Field(40, ge=0, description="Nitrogen kg/ha")
    P: float = Field(20, ge=0, description="Phosphorus kg/ha")
    K: float = Field(20, ge=0, description="Potassium kg/ha")


class FarmProfile(BaseModel):
    farm_type: Literal["wheat", "vegetable", "orchard", "mixed", "livestock"]
    # common fields
    soil_moisture: Optional[float] = Field(None, ge=0, le=100)
    rainfall_mm: Optional[float] = Field(None, ge=0)
    temp_celsius: Optional[float] = None
    npk: Optional[NPK] = None
    pest_pressure: Optional[Literal["low", "medium", "high"]] = None
    last_irrigation_days: Optional[int] = Field(None, ge=0)
    last_fertilization_days: Optional[int] = Field(None, ge=0)
    # wheat
    growth_stage: Optional[str] = None
    # vegetable
    crop_type: Optional[str] = None
    days_to_harvest: Optional[int] = Field(None, ge=0)
    humidity_pct: Optional[float] = Field(None, ge=0, le=100)
    # orchard
    tree_age_years: Optional[int] = Field(None, ge=0)
    fruit_stage: Optional[str] = None
    frost_risk: Optional[bool] = None
    last_pruning_days: Optional[int] = Field(None, ge=0)
    # mixed
    crop_sections: Optional[List[str]] = None
    animal_count: Optional[int] = Field(None, ge=0)
    feed_stock_days: Optional[int] = Field(None, ge=0)
    # livestock
    animal_type: Optional[Literal["cattle", "sheep", "poultry", "swine"]] = None
    avg_weight_kg: Optional[float] = Field(None, ge=0)
    feed_type: Optional[str] = None
    water_availability: Optional[Literal["adequate", "low", "critical"]] = None
    last_vet_check_days: Optional[int] = Field(None, ge=0)
    vaccination_due: Optional[bool] = None
    disease_symptoms: Optional[List[str]] = None
    mortality_last_7_days: Optional[int] = Field(None, ge=0)


class Recommendation(BaseModel):
    priority: Literal["high", "medium", "low"]
    message: str


class RecommendResponse(BaseModel):
    farm_type: str
    total: int
    recommendations: List[Recommendation]


class ScheduledTask(BaseModel):
    day: str          # e.g. "2026-02-21"
    day_label: str    # e.g. "Day 1 — Saturday"
    time: str
    task: str
    priority_flag: bool  # True if a high-priority rec exists for this farm


class ScheduleResponse(BaseModel):
    farm_id: str
    farm_name: str
    farm_type: str
    generated_from: str   # today's date
    schedule: List[ScheduledTask]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    farm_id: str


class ChatResponse(BaseModel):
    reply: str
    farm_id: str
    matched_intent: str


class FarmListItem(BaseModel):
    farm_id: str
    name: str
    farm_type: str
    location: str
    area_ha: float


# ─────────────────────────────────────────────
# INTENT MATCHING FOR /chat
# ─────────────────────────────────────────────

_INTENT_RULES: List[tuple] = [
    ("irrigation",    [re.compile(p) for p in [r"\birrigat", r"\bwater\b", r"\bmoisture\b", r"\bdry\b", r"\bdrought\b"]]),
    ("fertilization", [re.compile(p) for p in [r"\bfertili[sz]", r"\bnpk\b", r"\bnitrogen\b", r"\bphosphorus\b", r"\bpotassium\b", r"\bnutrient\b"]]),
    ("pest",          [re.compile(p) for p in [r"\bpest\b", r"\binsect\b", r"\bdisease\b", r"\bfungal\b", r"\bspray\b", r"\btreat\b"]]),
    ("schedule",      [re.compile(p) for p in [r"\bschedule\b", r"\btask\b", r"\bplan\b", r"\btoday\b", r"\bweek\b"]]),
    ("health",        [re.compile(p) for p in [r"\bvet\b", r"\bvaccinat", r"\bmortalit", r"\bdead\b", r"\bsick\b", r"\bsymptom\b"]]),
    ("greeting",      [re.compile(p) for p in [r"\bhello\b", r"\bhi\b", r"\bhey\b", r"\bgreet\b"]]),
]


def detect_intent(message: str) -> str:
    lower = message.lower()
    for intent, patterns in _INTENT_RULES:
        if any(p.search(lower) for p in patterns):
            return intent
    return "general"


def build_chat_reply(intent: str, farm: Dict[str, Any], recs: List[Recommendation]) -> str:
    name = farm["name"]
    ftype = farm["farm_type"]
    high = [r for r in recs if r.priority == "high"]
    medium = [r for r in recs if r.priority == "medium"]

    if intent == "greeting":
        return (
            f"Hello! I'm your Yonca AI assistant for {name}. "
            f"This is a {ftype} farm. I currently see {len(high)} high-priority "
            f"and {len(medium)} medium-priority recommendations. What would you like to know?"
        )

    if intent == "irrigation":
        irr = [r for r in recs if "irrigat" in r.message.lower() or "moisture" in r.message.lower() or "water" in r.message.lower()]
        if irr:
            top = irr[0]
            return f"[{top.priority.upper()}] Irrigation status for {name}: {top.message}"
        return f"No urgent irrigation issues detected for {name} right now."

    if intent == "fertilization":
        fert = [r for r in recs if "fertil" in r.message.lower() or "nitrogen" in r.message.lower()
                or "phosphorus" in r.message.lower() or "potassium" in r.message.lower() or "npk" in r.message.lower()]
        if fert:
            top = fert[0]
            return f"[{top.priority.upper()}] Fertilization note for {name}: {top.message}"
        return f"Nutrient levels appear adequate for {name} at this time."

    if intent == "pest":
        pest = [r for r in recs if "pest" in r.message.lower() or "fungal" in r.message.lower()
                or "disease" in r.message.lower() or "spray" in r.message.lower()]
        if pest:
            top = pest[0]
            return f"[{top.priority.upper()}] Pest/disease alert for {name}: {top.message}"
        return f"Pest risk is currently low for {name}. Keep up regular scouting."

    if intent == "health":
        health = [r for r in recs if "vet" in r.message.lower() or "vaccin" in r.message.lower()
                  or "mortalit" in r.message.lower() or "symptom" in r.message.lower() or "disease" in r.message.lower()]
        if health:
            top = health[0]
            return f"[{top.priority.upper()}] Animal health note for {name}: {top.message}"
        return f"No urgent health concerns detected for {name}. Maintain regular vet schedule."

    if intent == "schedule":
        template = SCHEDULE_TEMPLATES.get(ftype, [])
        if template:
            tasks_preview = "; ".join(t["task"] for t in template[:3])
            return (
                f"Today's top tasks for {name}: {tasks_preview}. "
                f"Use GET /schedule/{farm['farm_id']} for the full 7-day plan."
            )
        return f"Schedule templates are not yet defined for farm type '{ftype}'."

    # general fallback — summarise top recommendations
    if high:
        summary = " | ".join(r.message for r in high[:2])
        return f"Top priorities for {name}: {summary}"
    if medium:
        summary = " | ".join(r.message for r in medium[:2])
        return f"No critical issues. Medium priorities for {name}: {summary}"
    return f"Everything looks stable at {name}. No high or medium priority alerts at this time."


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def farm_data_to_dict(profile: FarmProfile) -> dict:
    """Convert Pydantic model to plain dict, converting nested NPK model."""
    d = profile.model_dump(exclude_none=True)
    if "npk" in d and isinstance(d["npk"], dict):
        pass  # already a plain dict after model_dump
    return d


def recs_to_models(raw: list) -> List[Recommendation]:
    return [Recommendation(priority=p, message=m) for p, m in raw]


def get_farm_or_404(farm_id: str) -> Dict[str, Any]:
    farm = DEMO_FARMS.get(farm_id)
    if not farm:
        raise HTTPException(
            status_code=404,
            detail=f"Farm '{farm_id}' not found. Available IDs: {list(DEMO_FARMS.keys())}",
        )
    return farm


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.get("/health", tags=["Meta"])
def health_check():
    """Liveness probe — returns API status and available farm types."""
    return {
        "status": "ok",
        "service": "Yonca Farm Planner API",
        "version": "1.0.0",
        "supported_farm_types": list(FARM_ENGINES.keys()),
    }


@app.get("/farms", response_model=List[FarmListItem], tags=["Farms"])
def list_farms():
    """Return all 5 demo farm profiles (summary view)."""
    return [
        FarmListItem(
            farm_id=f["farm_id"],
            name=f["name"],
            farm_type=f["farm_type"],
            location=f["location"],
            area_ha=f["area_ha"],
        )
        for f in DEMO_FARMS.values()
    ]


@app.post("/recommend", response_model=RecommendResponse, tags=["Recommendations"])
def recommend(profile: FarmProfile):
    """
    Submit a farm profile JSON and receive a prioritised recommendation list.

    The engine evaluates irrigation, fertilization, pest risk (crop farms)
    or feeding schedule, disease risk, vet check (livestock farms).
    """
    try:
        data = farm_data_to_dict(profile)
        raw = get_recommendations(profile.farm_type, data)
        recs = recs_to_models(raw)
        return RecommendResponse(
            farm_type=profile.farm_type,
            total=len(recs),
            recommendations=recs,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/schedule/{farm_id}", response_model=ScheduleResponse, tags=["Schedule"])
def get_schedule(
    farm_id: str = Path(..., description="Demo farm ID, e.g. farm-001"),
):
    """
    Return a 7-day daily task schedule for the given demo farm.

    Tasks are derived from farm-type templates and annotated with a
    priority flag if the engine detects any high-priority issues.
    """
    farm = get_farm_or_404(farm_id)
    ftype = farm["farm_type"]
    template = SCHEDULE_TEMPLATES.get(ftype, [])

    if not template:
        raise HTTPException(
            status_code=501,
            detail=f"No schedule template for farm type '{ftype}'.",
        )

    # Determine whether this farm has any high-priority recommendations
    raw = get_recommendations(ftype, farm["data"])
    has_high = any(p == "high" for p, _ in raw)

    today = date.today()
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    schedule: List[ScheduledTask] = []
    for day_offset in range(7):
        current_date = today + timedelta(days=day_offset)
        day_label = f"Day {day_offset + 1} — {day_names[current_date.weekday()]}"
        for task_entry in template:
            schedule.append(
                ScheduledTask(
                    day=str(current_date),
                    day_label=day_label,
                    time=task_entry["time"],
                    task=task_entry["task"],
                    priority_flag=has_high,
                )
            )

    return ScheduleResponse(
        farm_id=farm_id,
        farm_name=farm["name"],
        farm_type=ftype,
        generated_from=str(today),
        schedule=schedule,
    )


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat(request: ChatRequest):
    """
    Natural-language chat interface.

    Detects intent from the user's message (irrigation / fertilization /
    pest / schedule / health / general), fetches live recommendations for
    the given farm, and returns a context-aware text reply.
    """
    farm = get_farm_or_404(request.farm_id)
    ftype = farm["farm_type"]

    raw = get_recommendations(ftype, farm["data"])
    recs = recs_to_models(raw)

    intent = detect_intent(request.message)
    reply = build_chat_reply(intent, farm, recs)

    return ChatResponse(reply=reply, farm_id=request.farm_id, matched_intent=intent)


