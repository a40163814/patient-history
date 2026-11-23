from backend.app.services.question_engine import question_engine

def test_question_engine_sequence_and_language():
    # Initial question should be chief_complaint in symptoms section
    q1 = question_engine.get_next_question(
        current_section="symptoms",
        answered_fields=[],
        preferred_language="en"
    )
    assert q1 is not None
    assert q1.section_id == "symptoms"
    assert q1.field_key == "chief_complaint"
    assert "main health problem" in q1.prompt.lower()

    # Hindi prompt
    q1_hi = question_engine.get_next_question(
        current_section="symptoms",
        answered_fields=[],
        preferred_language="hi"
    )
    assert q1_hi is not None
    assert "मुख्य कारण" in q1_hi.prompt

    # Marathi prompt
    q1_mr = question_engine.get_next_question(
        current_section="symptoms",
        answered_fields=[],
        preferred_language="mr"
    )
    assert q1_mr is not None
    assert "मुख्य कारण" in q1_mr.prompt

def test_speech_failure_fallback_trigger():
    # If consecutive failures < 2, no tap fallback
    q_normal = question_engine.get_next_question(
        current_section="pre_existing_conditions",
        answered_fields=[],
        consecutive_speech_failures=1
    )
    assert q_normal.show_tap_fallback is False

    # If consecutive failures >= 2, offer tap fallback
    q_fallback = question_engine.get_next_question(
        current_section="pre_existing_conditions",
        answered_fields=[],
        consecutive_speech_failures=2
    )
    assert q_fallback.show_tap_fallback is True

def test_symptom_cap_at_13():
    # When symptom cap of 13 is reached, symptoms section is bypassed to pre_existing_conditions
    q = question_engine.get_next_question(
        current_section="symptoms",
        answered_fields=["chief_complaint"],
        symptom_questions_asked=13
    )
    assert q is not None
    assert q.section_id == "pre_existing_conditions"

def test_dynamic_follow_up_questions():
    # When patient reports Diabetes, engine asks diabetes_history follow-up
    q_fu = question_engine.get_next_question(
        current_section="pre_existing_conditions",
        answered_fields=["known_chronic_conditions"],
        answered_data={"known_chronic_conditions": "I have Type 2 Diabetes for some years"}
    )
    assert q_fu is not None
    assert q_fu.field_key == "diabetes_history"
    assert "blood sugar" in q_fu.prompt.lower()

    # When patient reports no chronic illness, engine skips follow-ups and moves to current_medicines
    q_no_fu = question_engine.get_next_question(
        current_section="pre_existing_conditions",
        answered_fields=["known_chronic_conditions"],
        answered_data={"known_chronic_conditions": "None, no known chronic illness"}
    )
    assert q_no_fu is not None
    assert q_no_fu.section_id == "current_medicines"
    assert q_no_fu.field_key == "active_medications"
