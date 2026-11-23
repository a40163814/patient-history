import pytest
from backend.app.services.red_flag_scanner import red_flag_scanner

def test_cardiac_red_flag_multilingual():
    # English
    res_en = red_flag_scanner.scan_text("I have sharp chest pain radiating to arm", language="en")
    assert res_en.is_red_flag is True
    assert res_en.category == "cardiac_chest_pain"
    assert res_en.staff_priority == "CRITICAL"
    assert res_en.crisis_helpline == "14416"

    # Hindi
    res_hi = red_flag_scanner.scan_text("अचानक सीने में दर्द और भारीपन हो रहा है", language="hi")
    assert res_hi.is_red_flag is True
    assert res_hi.category == "cardiac_chest_pain"
    assert "बैठ जाएं" in res_hi.patient_message

    # Marathi
    res_mr = red_flag_scanner.scan_text("माझ्या छातीत तीव्र वेदना होत आहेत", language="mr")
    assert res_mr.is_red_flag is True
    assert res_mr.category == "cardiac_chest_pain"

def test_breathlessness_red_flag():
    res = red_flag_scanner.scan_text("I cannot breathe and I am gasping for air")
    assert res.is_red_flag is True
    assert res.category == "respiratory_distress"

    res_hi = red_flag_scanner.scan_text("मेरी सांस नहीं आ रही है, दम घुट रहा है", language="hi")
    assert res_hi.is_red_flag is True
    assert res_hi.category == "respiratory_distress"

def test_severe_bleeding_red_flag():
    res = red_flag_scanner.scan_text("I started coughing blood this morning")
    assert res.is_red_flag is True
    assert res.category == "severe_hemorrhage"

    res_mr = red_flag_scanner.scan_text("खोकल्यातून रक्त येत आहे खूप", language="mr")
    assert res_mr.is_red_flag is True
    assert res_mr.category == "severe_hemorrhage"

def test_altered_consciousness_red_flag():
    res = red_flag_scanner.scan_text("The patient fainted and blacked out in the corridor")
    assert res.is_red_flag is True
    assert res.category == "altered_consciousness"

    res_hi = red_flag_scanner.scan_text("यह अचानक चक्कर खाकर गिर गया और बेहोश हो गया", language="hi")
    assert res_hi.is_red_flag is True
    assert res_hi.category == "altered_consciousness"

def test_stroke_signs_red_flag():
    res = red_flag_scanner.scan_text("Sudden slurred speech and face drooping on the left")
    assert res.is_red_flag is True
    assert res.category == "stroke_neurological"

    res_hi = red_flag_scanner.scan_text("इनका मुंह टेढ़ा हो गया और बोली लड़खड़ा रही है", language="hi")
    assert res_hi.is_red_flag is True
    assert res_hi.category == "stroke_neurological"

def test_pregnancy_danger_red_flag():
    res = red_flag_scanner.scan_text("I am 7 months pregnant and bleeding heavily")
    assert res.is_red_flag is True
    assert res.category == "pregnancy_danger"

def test_acute_pain_red_flag():
    res = red_flag_scanner.scan_text("This is the worst headache of my life, like a thunderclap")
    assert res.is_red_flag is True
    assert res.category == "acute_severe_pain"

def test_self_harm_crisis_red_flag():
    res = red_flag_scanner.scan_text("I just want to end my life and kill myself")
    assert res.is_red_flag is True
    assert res.category == "self_harm_crisis"
    assert res.crisis_helpline == "14416"
    assert res.ambulance_service == "108"

def test_benign_utterances_do_not_trigger():
    benign_samples = [
        "I have a mild knee pain since two months",
        "मुझे थोड़ी गैस और अपच की समस्या है",
        "माझ्या डोक्यात थोडी कळ आहे कालपासून",
        "I take Ayurvedic Ashwagandha churna daily",
        "No major chronic diseases, just seasonal cold"
    ]
    for text in benign_samples:
        res = red_flag_scanner.scan_text(text)
        assert res.is_red_flag is False, f"False positive triggered on: {text}"
