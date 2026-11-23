import pytest
from backend.app.services.vitals import compute_bmi

def test_compute_bmi_normal():
    # 170 cm, 65 kg -> 65 / (1.7^2) = 65 / 2.89 = 22.49 -> 22.5 (Normal in Indian guidelines <= 22.9)
    bmi, category = compute_bmi(170, 65)
    assert bmi == 22.5
    assert category == "Normal"

def test_compute_bmi_underweight():
    # 175 cm, 50 kg -> 50 / (1.75^2) = 16.3 (Underweight < 18.5)
    bmi, category = compute_bmi(175, 50)
    assert bmi == 16.3
    assert category == "Underweight"

def test_compute_bmi_overweight_and_obese():
    # 165 cm, 65 kg -> 65 / (1.65^2) = 23.87 -> 23.9 (Overweight in Indian guidelines: 23.0 - 24.9)
    bmi, category = compute_bmi(165, 65)
    assert bmi == 23.9
    assert category == "Overweight"

    # 160 cm, 75 kg -> 75 / (1.6^2) = 29.3 (Obese >= 25.0)
    bmi, category = compute_bmi(160, 75)
    assert bmi == 29.3
    assert category == "Obese"

def test_invalid_vitals():
    with pytest.raises(ValueError):
        compute_bmi(-170, 70)
    with pytest.raises(ValueError):
        compute_bmi(170, 0)
