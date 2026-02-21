"""
Yonca Farm Assistant - Intent Matching & Response Generation
Azerbaijani language chatbot logic using keyword-based intent matching.
"""

import re
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Intent keyword map  (intent_name -> list of Azerbaijani keywords/phrases)
# ---------------------------------------------------------------------------
INTENT_KEYWORDS: dict[str, list[str]] = {
    "irrigation":           ["suvarma", "suvarmaq", "su", "damcı", "nəmlik", "quraqlıq", "sulanmaq", "şırıltı"],
    "fertilization":        ["gübrə", "gübrələmə", "azot", "fosfor", "kalium", "npk", "üzvi", "mineral", "kompost", "torpaq qidalanması"],
    "pest_alert":           ["zərərverici var", "zərərverici", "böcək", "mənənə", "kəpənək", "həşərat", "ziyan", "bit", "gəmirici", "əkin zərərvericisi"],
    "harvest_timing":       ["yığım", "biçin", "məhsul", "hasat", "yetişmə", "dərmə", "toplama", "yetişib", "nə vaxt yığmaq"],
    "subsidy_deadline":     ["subsidiya", "müavinət", "dövlət dəstəyi", "qrant", "son tarix", "müraciət", "kompensasiya"],
    "weather_advice":       ["hava proqnozu", "hava necədir", "hava bu həftə", "hava", "yağış", "külək", "temperatur", "don", "dolu", "istilik", "soyuq", "proqnoz", "iqlim"],
    "livestock_feeding":    ["heyvan", "mal-qara", "inək", "qoyun", "yem", "qidalanma", "otlaq", "saman", "yemləmə"],
    "disease_risk":         ["xəstəlik", "virus", "göbələk", "bakteriya", "solma", "sarılma", "çürümə", "pas", "yanıq", "infeksiya"],
    "weekly_schedule":      ["həftəlik plan", "iş planı", "həftəlik cədvəl", "cədvəl", "plan", "həftəlik", "iş siyahısı", "bu həftə nə", "tapşırıqlar", "planlaşdırma"],
    "general_help":         ["kömək", "nə edim", "necə", "sual", "başlamaq", "yardım", "öyrən", "məlumat"],
    "soil_analysis":        ["torpaq", "analiz", "ph", "turşuluq", "münbitlik", "humus", "qum", "gil", "torpaq növü"],
    "market_price":         ["qiymət", "bazar", "satış", "gəlir", "mənfəət", "ixrac", "ticarət", "bazarlıq"],
    "equipment_maintenance":["texnika", "traktor", "nasaz", "təmir", "texniki xidmət", "motor", "avadanlıq"],
    "seed_selection":       ["toxum", "sort", "növ", "əkin materialı", "hibrid", "yerli sort", "sertifikat"],
    "crop_rotation":        ["növbəli əkin", "rotasiya", "torpaq dincəlməsi", "sələf", "növbə", "dinclik"],
}

# Words considered high-specificity agricultural terms that should outweigh
# generic helper words even when both are single-word matches.
_HIGH_SPECIFICITY: frozenset[str] = frozenset([
    "suvarma", "gübrə", "zərərverici", "yığım", "subsidiya", "hava",
    "yemləmə", "xəstəlik", "torpaq", "toxum", "traktor", "rotasiya",
    "suvarmaq", "gübrələmə", "hasat", "biçin",
])

# Weights: longer keyword phrases score quadratically higher to prevent short
# common words (e.g. "su", "nə") from outweighing specific domain terms.
def _keyword_score(keyword: str) -> float:
    word_count = len(keyword.split())
    base = word_count ** 2
    # Boost single-word high-specificity agricultural terms
    if word_count == 1 and keyword in _HIGH_SPECIFICITY:
        base += 2.0
    return base


def _normalize(text: str) -> str:
    """Lowercase and remove punctuation."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return text


def match_intent(user_message: str) -> str:
    """
    Match user message to the best intent using keyword scoring.

    Args:
        user_message: Raw user input in Azerbaijani.

    Returns:
        intent_name string (e.g. 'irrigation'). Falls back to 'general_help'.
    """
    normalized = _normalize(user_message)
    scores: dict[str, float] = {intent: 0.0 for intent in INTENT_KEYWORDS}

    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in normalized:
                scores[intent] += _keyword_score(kw)

    best_intent = max(scores, key=lambda k: scores[k])

    # If no keyword matched at all, default to general help
    if scores[best_intent] == 0.0:
        return "general_help"

    return best_intent


# ---------------------------------------------------------------------------
# Response generation
# ---------------------------------------------------------------------------

_RESPONSE_TEMPLATES: dict[str, str] = {
    "irrigation": (
        "🚿 Suvarma Məlumatı\n"
        "Sahə: {field_name}\n"
        "Suvarma cədvəli: {irrigation_schedule}\n"
        "Torpaq nəmliyi: {soil_moisture}%\n"
        "Növbəti suvarma: {next_irrigation_date}\n"
        "Tövsiyə: {irrigation_tip}"
    ),
    "fertilization": (
        "🌱 Gübrələmə Tövsiyəsi\n"
        "Bitki: {crop_name}\n"
        "Gübrə növü: {fertilizer_type}\n"
        "Norma: {fertilizer_dose} kq/ha\n"
        "Müddət: {fertilization_period}\n"
        "Qeyd: Gübrəni yağışdan əvvəl tətbiq edin."
    ),
    "pest_alert": (
        "⚠️ ZƏRƏRVERİCİ XƏBƏRDARLIĞI\n"
        "Zərərverici: {pest_name}\n"
        "Risk səviyyəsi: {risk_level}\n"
        "Təsirə məruz qala biləcək sahə: {affected_area} ha\n"
        "Tövsiyə olunan mübarizə: {pest_recommendation}\n"
        "Dərhal tədbirə başlayın!"
    ),
    "harvest_timing": (
        "🌾 Yığım Məlumatı\n"
        "Bitki: {crop_name}\n"
        "Yığım tarixi: {harvest_date}\n"
        "Yetişmə əlaməti: {maturity_sign}\n"
        "Gözlənilən məhsuldarlıq: {expected_yield} ton/ha\n"
        "İqlim şəraiti: {weather_condition}"
    ),
    "subsidy_deadline": (
        "📋 Subsidiya Məlumatı\n"
        "Subsidiya adı: {subsidy_name}\n"
        "Son müraciət tarixi: {deadline}\n"
        "Tələb olunan sənədlər: {required_docs}\n"
        "Müraciət qaydası: {application_method}\n"
        "Diqqət: Bu tarixdən sonra müraciət qəbul edilmir!"
    ),
    "weather_advice": (
        "🌤️ Hava Proqnozu & Məsləhət\n"
        "Ərazi: {location}\n"
        "Proqnoz: {weather_forecast}\n"
        "Temperatur: {temperature}°C\n"
        "Kənd təsərrüfatı məsləhəti: {weather_advice}\n"
        "Xəbərdarlıq: {weather_warning}"
    ),
    "livestock_feeding": (
        "🐄 Yemləmə Tövsiyəsi\n"
        "Heyvan növü: {livestock_type}\n"
        "Baş sayı: {livestock_count}\n"
        "Gündəlik yem norması: {feed_amount} kq/baş\n"
        "Yem növü: {feed_type}\n"
        "Suvarma rejimi: {water_schedule}"
    ),
    "disease_risk": (
        "🔴 XƏSTƏLİK RİSKİ\n"
        "Xəstəlik: {disease_name}\n"
        "Risk səviyyəsi: {risk_level}\n"
        "Əsas simptomlar: {symptoms}\n"
        "Profilaktik tədbirlər: {prevention_measures}\n"
        "Müraciət: Aqronom ilə əlaqə saxlayın."
    ),
    "weekly_schedule": (
        "📅 Həftəlik İş Planı — {farm_name}\n"
        "Dövr: {week_range}\n"
        "Bazar ertəsi: {monday_tasks}\n"
        "Çərşənbə axşamı: {tuesday_tasks}\n"
        "Çərşənbə: {wednesday_tasks}\n"
        "Cümə axşamı: {thursday_tasks}\n"
        "Cümə: {friday_tasks}"
    ),
    "general_help": (
        "👋 Salam! Mən Yonca Ferma Köməkçisiyəm.\n"
        "Ferma: {farm_name}\n\n"
        "Sizə bu mövzularda kömək edə bilərəm:\n"
        "• Suvarma cədvəli\n"
        "• Gübrələmə tövsiyəsi\n"
        "• Zərərverici xəbərdarlığı\n"
        "• Məhsul yığım vaxtı\n"
        "• Subsidiya son tarixləri\n"
        "• Hava proqnozu məsləhəti\n"
        "• Mal-qara qidalanması\n"
        "• Xəstəlik riski\n"
        "• Həftəlik planlaşdırma\n\n"
        "Sualınızı yazın, kömək etməyə hazıram!"
    ),
    "soil_analysis": (
        "🔬 Torpaq Analizi — {field_name}\n"
        "pH: {soil_ph}\n"
        "Humus: {humus_percent}%\n"
        "Azot: {nitrogen_level} mg/kq\n"
        "Fosfor: {phosphorus_level} mg/kq\n"
        "Tövsiyə: {soil_recommendation}"
    ),
    "market_price": (
        "💰 Bazar Qiymətləri\n"
        "Məhsul: {crop_name}\n"
        "Cari qiymət: {market_price} AZN/ton\n"
        "Ən yaxın bazar: {nearest_market}\n"
        "Keçən həftəyə nisbət: {price_change}\n"
        "Satış məsləhəti: {market_tip}"
    ),
    "equipment_maintenance": (
        "🔧 Avadanlıq Texniki Xidməti\n"
        "Avadanlıq: {equipment_name}\n"
        "Növbəti texniki baxış: {next_service_date}\n"
        "Xəbərdarlıqlar: {maintenance_warnings}\n"
        "Servis mərkəzi: {service_center}\n"
        "Ehtiyat hissə sifariş: {parts_order}"
    ),
    "seed_selection": (
        "🌾 Toxum Seçimi\n"
        "Bitki: {crop_name}\n"
        "Tövsiyə olunan sortlar: {recommended_varieties}\n"
        "Optimal əkin müddəti: {planting_period}\n"
        "Toxum norması: {seed_rate} kq/ha\n"
        "Sertifikat statusu: {seed_certification}"
    ),
    "crop_rotation": (
        "🔄 Növbəli Əkin Planı\n"
        "Sahə: {field_name}\n"
        "Bu il: {current_crop}\n"
        "Növbəti il: {next_crop}\n"
        "Tövsiyənin səbəbi: {rotation_reason}\n"
        "Gözlənilən fayda: {expected_benefit}"
    ),
}

# Default placeholder values shown when farm_data doesn't supply a key
_DEFAULTS: dict[str, str] = {
    "field_name": "Əsas sahə",
    "farm_name": "Ferma",
    "crop_name": "Məhsul",
    "irrigation_schedule": "Hər 3 gündən bir",
    "soil_moisture": "45",
    "next_irrigation_date": (datetime.now() + timedelta(days=2)).strftime("%d.%m.%Y"),
    "irrigation_tip": "Sübh erkən saatlarda sulayın.",
    "fertilizer_type": "NPK 16-16-16",
    "fertilizer_dose": "150",
    "fertilization_period": "Cücərmədən 20 gün sonra",
    "pest_name": "Kəpənək sürfəsi",
    "risk_level": "Orta",
    "affected_area": "5",
    "pest_recommendation": "Biopestisid tətbiq edin",
    "harvest_date": (datetime.now() + timedelta(days=30)).strftime("%d.%m.%Y"),
    "maturity_sign": "Dən bərkimişdir",
    "expected_yield": "3.5",
    "weather_condition": "Günəşli",
    "subsidy_name": "Kənd Təsərrüfatı Subsidiyası",
    "deadline": (datetime.now() + timedelta(days=14)).strftime("%d.%m.%Y"),
    "required_docs": "Şəxsiyyət vəsiqəsi, torpaq sənədi, ərizə",
    "application_method": "ASAN xidmət mərkəzinə müraciət",
    "location": "Bakı ətrafı",
    "weather_forecast": "Növbəti 3 gün: az buludlu, yağıntısız",
    "temperature": "22",
    "weather_advice": "Gübrələmə üçün əlverişli vaxtdır",
    "weather_warning": "Axşam saatlarında şeh düşə bilər",
    "livestock_type": "İnək",
    "livestock_count": "20",
    "feed_amount": "12",
    "feed_type": "Qarışıq yem + saman",
    "water_schedule": "Gündə 2 dəfə, 50 litr/baş",
    "disease_name": "Kök çürüməsi",
    "symptoms": "Yarpaqların saralması, bitkinin solması",
    "prevention_measures": "Drenaj sistemini yoxlayın, funqisid tətbiq edin",
    "week_range": f"{datetime.now().strftime('%d.%m')} - {(datetime.now() + timedelta(days=6)).strftime('%d.%m.%Y')}",
    "monday_tasks": "Suvarma sistemi yoxlanışı",
    "tuesday_tasks": "Gübrələmə",
    "wednesday_tasks": "Zərərverici müşahidəsi",
    "thursday_tasks": "Avadanlıq texniki baxışı",
    "friday_tasks": "Həftəlik hesabat",
    "soil_ph": "6.8",
    "humus_percent": "3.2",
    "nitrogen_level": "85",
    "phosphorus_level": "60",
    "soil_recommendation": "Əhəngləmə tövsiyə olunur",
    "market_price": "245",
    "nearest_market": "Qəbələ Kənd Bazarı",
    "price_change": "+5% artım",
    "market_tip": "Həftə sonuna saxlamaq qiymətini artıra bilər",
    "equipment_name": "Traktor MTZ-82",
    "next_service_date": (datetime.now() + timedelta(days=7)).strftime("%d.%m.%Y"),
    "maintenance_warnings": "Yağ dəyişilməsi lazımdır",
    "service_center": "AqroTexnika ASC, Gəncə",
    "parts_order": "Filtrlər sifariş edilib",
    "recommended_varieties": "Azəri-1, Şirvan-2",
    "planting_period": "Mart–Aprel",
    "seed_rate": "180",
    "seed_certification": "Sertifikatlıdır ✓",
    "current_crop": "Buğda",
    "next_crop": "Günəbaxan",
    "rotation_reason": "Torpaq azotunu bərpa etmək üçün",
    "expected_benefit": "Məhsuldarlıq 15% artır",
}


def get_response(intent_name: str, farm_data: dict) -> str:
    """
    Generate an Azerbaijani response for the given intent using farm_data.

    Args:
        intent_name: One of the recognized intent strings.
        farm_data:   Dict with farm-specific values (e.g. field_name, crop_name).
                     Missing keys fall back to sensible Azerbaijani defaults.

    Returns:
        Formatted Azerbaijani response string.
    """
    template = _RESPONSE_TEMPLATES.get(intent_name, _RESPONSE_TEMPLATES["general_help"])

    # Build context: defaults overridden by provided farm_data
    context = {**_DEFAULTS, **{k: str(v) for k, v in farm_data.items()}}

    try:
        return template.format_map(context)
    except KeyError as missing:
        # Fallback: insert placeholder for any truly unknown key
        context[str(missing).strip("'")] = f"[{missing}]"
        return template.format_map(context)


# ---------------------------------------------------------------------------
# Quick smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample_farm = {
        "farm_name": "Yonca Ferması №3",
        "field_name": "Cənub sahəsi (12 ha)",
        "crop_name": "Buğda",
        "soil_moisture": "38",
        "next_irrigation_date": "23.02.2026",
    }

    test_messages = [
        "Sabah suvarma lazımdırmı?",
        "Gübrə nə vaxt verim?",
        "Zərərverici var, nə edim?",
        "Məhsulu nə vaxt yığmaq olar?",
        "Subsidiya üçün son tarix nədir?",
        "Hava bu həftə necədir?",
        "İnəkləri nə ilə yemləyim?",
        "Bitkilərdə xəstəlik var",
        "Bu həftə nə etməliyəm?",
        "Kömək et",
    ]

    print("=" * 60)
    print("YONCA FERMA KÖMƏKÇİSİ — Test")
    print("=" * 60)
    for msg in test_messages:
        intent = match_intent(msg)
        response = get_response(intent, sample_farm)
        print(f"\n🧑 İstifadəçi: {msg}")
        print(f"🤖 Intent: {intent}")
        print(f"💬 Cavab:\n{response}")
        print("-" * 60)


