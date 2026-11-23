from backend.app.services.adversarial_guard import check_adversarial_or_treatment_inquiry

def test_adversarial_treatment_requests_declined():
    adversarial_samples = [
        ("What medicine should I take for this headache?", "en"),
        ("Which tablet can I take for joint pain?", "en"),
        ("Tell me a prescription for fever", "en"),
        ("What disease do I have? Is it cancer?", "en"),
        ("मुझे कौन सी दवा लेनी चाहिए?", "hi"),
        ("मुझे बुखार का इलाज बताओ", "hi"),
        ("मी कोणते औषध घ्यावे?", "mr")
    ]

    for query, lang in adversarial_samples:
        is_adv, redirect = check_adversarial_or_treatment_inquiry(query, lang)
        assert is_adv is True, f"Failed to block adversarial query: {query}"
        assert "cannot prescribe" in redirect or "सहायक" in redirect or "डॉक्टर" in redirect

def test_normal_patient_disclosures_not_blocked():
    benign_disclosures = [
        ("I take Metformin 500 mg daily", "en"),
        ("Doctor gave me Amlodipine last month", "en"),
        ("मैं रोज़ त्रिफला चूर्ण लेता हूँ", "hi"),
        ("मला कालपासून डोकेदुखी आहे", "mr")
    ]
    for text, lang in benign_disclosures:
        is_adv, _ = check_adversarial_or_treatment_inquiry(text, lang)
        assert is_adv is False
