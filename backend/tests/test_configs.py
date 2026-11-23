import json
from pathlib import Path
from backend.app.core.config import settings

def test_question_bank_config():
    path = settings.CONFIG_DIR / "question_bank.json"
    assert path.exists(), f"Missing {path}"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "_metadata" in data
    assert "sections" in data
    section_ids = [s["id"] for s in data["sections"]]
    assert section_ids[0] == "symptoms"
    assert "pre_existing_conditions" in section_ids
    assert "allergies" in section_ids
    assert "current_medicines" in section_ids
    assert "family_history" in section_ids
    assert "symptoms" in section_ids
    assert "lifestyle" in section_ids
    assert data["_metadata"]["max_symptom_questions"] == 13

def test_red_flags_config():
    path = settings.CONFIG_DIR / "red_flags.json"
    assert path.exists(), f"Missing {path}"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "_metadata" in data
    assert "crisis_helpline" in data["_metadata"]
    assert "categories" in data
    cat_ids = [c["id"] for c in data["categories"]]
    for required in ["cardiac_chest_pain", "respiratory_distress", "severe_hemorrhage", 
                     "altered_consciousness", "stroke_neurological", "pregnancy_danger", 
                     "acute_severe_pain", "self_harm_crisis"]:
        assert required in cat_ids

def test_lab_thresholds_config():
    path = settings.CONFIG_DIR / "lab_thresholds.json"
    assert path.exists(), f"Missing {path}"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "biomarkers" in data
    assert "fasting_blood_glucose" in data["biomarkers"]
    assert "hba1c" in data["biomarkers"]
    assert "systolic_bp" in data["biomarkers"]

def test_ayush_systems_config():
    path = settings.CONFIG_DIR / "ayush_systems.json"
    assert path.exists(), f"Missing {path}"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "systems" in data
    assert "ayurveda" in data["systems"]
    assert "homeopathy" in data["systems"]
    assert "unani" in data["systems"]
    assert "siddha" in data["systems"]
    assert "yoga_naturopathy" in data["systems"]
